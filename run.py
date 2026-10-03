"""Run one grading experiment against a local Ollama model.

The ONLY thing that changes between modes is how structure is requested:
  prompt : schema is described in the prompt, nothing enforced
  json   : Ollama JSON mode (output parses, fields not guaranteed)
  schema : Ollama constrained decoding with the JSON schema (structure guaranteed)

Examples:
  python run.py --model mock-oracle --mode schema          # sanity-check the harness, no GPU
  python run.py --model qwen3:4b --mode prompt
  python run.py --model qwen3:4b --mode json
  python run.py --model qwen3:4b --mode schema --order mark_first
  python run.py --model qwen3:4b --mode schema --with-scheme --repeats 3
"""
import argparse
import datetime as dt
import json
import pathlib
import subprocess
import time

import requests
from pydantic import ValidationError

from schema import SCHEMAS, semantic_issues

OLLAMA_URL = "http://localhost:11434/api/chat"
ROOT = pathlib.Path(__file__).parent

SYSTEM = (
    "You are an experienced Cambridge IGCSE Physics (0625) examiner marking one student answer. "
    "Mark the way Cambridge does: one mark per marking point; for calculations award method marks "
    "and allow error carried forward; be strict about units. "
    "Reply with a single JSON object that follows the given schema and nothing else."
)


def build_user_prompt(item: dict, schema_json: str, with_scheme: bool) -> str:
    if with_scheme:
        points = "\n".join(f"{i}. {p}" for i, p in enumerate(item["mark_scheme"], 1))
        scheme = f"Marking points (judge exactly these, in this order, one entry each):\n{points}"
    else:
        scheme = (
            f"No mark scheme is given. Decide the {item['max_mark']} distinct marking points yourself "
            f"(one mark each) and judge each one."
        )
    return (
        f"Syllabus reference: {item['syllabus_ref']}\nLevel: {item['level']}\n"
        f"Question ({item['max_mark']} marks): {item['question']}\n\n{scheme}\n\n"
        f'Student answer:\n"""{item["student_answer"]}"""\n\nJSON schema:\n{schema_json}'
    )


def extract_json(text: str) -> dict:
    """Parse JSON; tolerate code fences / chatter around the object (needed in prompt mode)."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def call_ollama(model, messages, fmt, seed):
    body = {"model": model, "messages": messages, "stream": False,
            "options": {"temperature": 0, "seed": seed}}
    if fmt is not None:
        body["format"] = fmt
    t0 = time.time()
    r = requests.post(OLLAMA_URL, json=body, timeout=900)
    r.raise_for_status()
    d = r.json()
    meta = {"latency_s": round(time.time() - t0, 3),
            "prompt_tokens": d.get("prompt_eval_count"), "output_tokens": d.get("eval_count")}
    return d["message"]["content"], meta


def call_mock(model, item, with_scheme, order):
    """Fake models to test the pipeline. 'mock-oracle' copies the teacher; 'mock-noisy' is sometimes wrong."""
    n = len(item["mark_scheme"]) if with_scheme else item["max_mark"]
    pts = list(item["teacher_points"]) + [False] * n
    pts = pts[:n]
    total = sum(pts)
    if model == "mock-noisy" and item["id"].endswith(("a3", "b3", "d2")):
        total += 1  # internal contradiction: total != sum of points
    points = [{"point": f"point {i+1}", "awarded": a,
               "evidence": item["student_answer"][:25] if a else ""} for i, a in enumerate(pts)]
    obj = {"marking_points": points, "total_mark": total, "error_type": "none" if total == item["max_mark"] else "concept",
           "misconception": "", "feedback": "mock feedback"}
    if order == "mark_first":
        obj = {"total_mark": obj.pop("total_mark"), **obj}
    return json.dumps(obj), {"latency_s": 0.0, "prompt_tokens": None, "output_tokens": None}


def grade(item, args, seed):
    Model = SCHEMAS[args.order]
    schema = Model.model_json_schema()
    schema_json = json.dumps(schema, indent=1)
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": build_user_prompt(item, schema_json, args.with_scheme)}]
    fmt = {"prompt": None, "json": "json", "schema": schema}[args.mode]

    parsed, error, raw, attempts = None, None, "", 0
    latency, out_tokens = 0.0, 0
    for attempts in range(1, args.max_attempts + 1):
        if args.model.startswith("mock-"):
            raw, meta = call_mock(args.model, item, args.with_scheme, args.order)
        else:
            raw, meta = call_ollama(args.model, messages, fmt, seed)
        latency += meta["latency_s"]
        out_tokens += meta["output_tokens"] or 0
        try:
            parsed = Model.model_validate(extract_json(raw))
            error = None
            break
        except (ValueError, ValidationError) as e:  # JSON errors and schema errors (both ValueError)
            error = str(e)[:400]
            messages += [{"role": "assistant", "content": raw},
                         {"role": "user", "content": f"Your reply was invalid: {error}\n"
                                                     "Reply again with ONLY the corrected JSON object."}]
    return parsed, error, raw, attempts, latency, out_tokens


def git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="Ollama model tag (see `ollama list`) or mock-oracle / mock-noisy")
    ap.add_argument("--mode", choices=["prompt", "json", "schema"], default="schema")
    ap.add_argument("--order", choices=list(SCHEMAS), default="reason_first")
    ap.add_argument("--with-scheme", action="store_true", help="give the model the mark scheme (Session 2 preview)")
    ap.add_argument("--data", default=str(ROOT / "data" / "dev.jsonl"))
    ap.add_argument("--repeats", type=int, default=1, help="repeat with different seeds to see run-to-run variation")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-attempts", type=int, default=2, help="1 = no retry; 2 = one retry with the error message")
    args = ap.parse_args()

    items = [json.loads(l) for l in open(args.data, encoding="utf-8") if l.strip()]
    config = {"model": args.model, "mode": args.mode, "order": args.order, "with_scheme": args.with_scheme,
              "max_attempts": args.max_attempts, "temperature": 0, "git_commit": git_commit(), "data": pathlib.Path(args.data).name}
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"{args.model.replace(':', '-').replace('/', '-')}_{args.mode}_{args.order}_{'scheme' if args.with_scheme else 'noscheme'}_{stamp}"
    out_path = ROOT / "results" / f"{name}.jsonl"
    out_path.parent.mkdir(exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as out:
        for rep in range(args.repeats):
            seed = args.seed + rep
            for item in items:
                parsed, error, raw, attempts, latency, out_tokens = grade(item, args, seed)
                issues = None
                if parsed is not None:
                    n_scheme = len(item["mark_scheme"]) if args.with_scheme else None
                    issues = semantic_issues(parsed, item["max_mark"], item["student_answer"], n_scheme)
                rec = {"config": {**config, "seed": seed}, "id": item["id"], "kind": item["kind"],
                       "valid": parsed is not None, "error": error, "attempts": attempts, "issues": issues,
                       "pred_total": parsed.total_mark if parsed else None,
                       "pred_points": [p.awarded for p in parsed.marking_points] if parsed else None,
                       "teacher_total": item["teacher_total"], "teacher_points": item["teacher_points"],
                       "max_mark": item["max_mark"], "latency_s": round(latency, 3), "output_tokens": out_tokens,
                       "raw": raw}
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                flag = "ok " if parsed and not issues else ("BAD" if not parsed else "iss")
                print(f"[{flag}] {item['id']:<18} pred={rec['pred_total']} teacher={item['teacher_total']} "
                      f"attempts={attempts} {issues or ''}")
    print(f"\nsaved -> {out_path}\nnow run: python evaluate.py")


if __name__ == "__main__":
    main()
