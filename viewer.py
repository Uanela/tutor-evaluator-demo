"""Local read-only UI for the dev data and grading results.

Run:  python viewer.py            then open http://127.0.0.1:8000

Standard library only. Reads data/*.jsonl and results/*.jsonl on every request,
so new runs show up on refresh. Statistics come from evaluate.py.
"""
import argparse
import collections
import glob
import json
import pathlib
import re
import statistics
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import evaluate

ROOT = pathlib.Path(__file__).parent
UI_FILE = ROOT / "ui" / "index.html"
STAMP = re.compile(r"_(\d{8}-\d{6})$")
ITEM_FIELDS = ("question_id", "question", "syllabus_ref", "level", "student_answer", "mark_scheme", "teacher_note")


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_dataset():
    items = []
    for path in sorted(glob.glob(str(ROOT / "data" / "*.jsonl"))):
        items += read_jsonl(path)
    return items


def stat(flags):
    if not flags:
        return None
    lo, hi = evaluate.bootstrap_ci(flags)
    return {"value": statistics.fmean(flags), "lo": lo, "hi": hi}


def summarize(rows):
    n = len(rows)
    valid = [r for r in rows if r["valid"]]
    clean = [r for r in valid if not r["issues"]]
    with_scheme = rows[0]["config"]["with_scheme"]
    point_pairs = [
        (p, t)
        for r in valid
        if r["pred_points"] is not None and len(r["pred_points"]) == len(r["teacher_points"])
        for p, t in zip(r["pred_points"], r["teacher_points"])
    ]
    point_flags = [int(p == t) for p, t in point_pairs] if with_scheme else []
    exact_valid = [int(r["pred_total"] == r["teacher_total"]) for r in valid]
    latency = [r["latency_s"] for r in rows if r["latency_s"]]
    tokens = [r["output_tokens"] for r in rows if r["output_tokens"]]
    issues = collections.Counter(i for r in valid for i in (r["issues"] or []))
    return {
        "n": n,
        "seeds": len({r["config"]["seed"] for r in rows}),
        "syntactic_valid": len(valid) / n,
        "semantic_valid": len(clean) / n,
        "retried": sum(r["attempts"] > 1 for r in rows),
        "exact_all": stat([int(r["valid"] and r["pred_total"] == r["teacher_total"]) for r in rows]),
        "exact_valid": statistics.fmean(exact_valid) if exact_valid else None,
        "within1_all": stat([int(r["valid"] and abs(r["pred_total"] - r["teacher_total"]) <= 1) for r in rows]),
        "kappa": evaluate.cohen_kappa([r["pred_total"] for r in valid], [r["teacher_total"] for r in valid]),
        "point_agree": stat(point_flags),
        "point_count": len(point_flags),
        "issues": dict(issues.most_common()),
        "latency": statistics.fmean(latency) if latency else None,
        "tokens": statistics.fmean(tokens) if tokens else None,
    }


def join_row(row, by_id):
    item = by_id.get(row["id"], {})
    return {**row, "item": {k: item.get(k) for k in ITEM_FIELDS}}


def build_runs():
    by_id = {it["id"]: it for it in load_dataset()}
    runs = []
    for path in sorted(glob.glob(str(ROOT / "results" / "*.jsonl"))):
        rows = read_jsonl(path)
        if not rows:
            continue
        p = pathlib.Path(path)
        c = rows[0]["config"]
        stamp = STAMP.search(p.stem)
        runs.append({
            "name": p.stem,
            "file": p.name,
            "created": stamp.group(1) if stamp else None,
            "model": c["model"],
            "mode": c["mode"],
            "order": c["order"],
            "scheme": "scheme" if c["with_scheme"] else "noscheme",
            "data": c.get("data"),
            "git_commit": c.get("git_commit"),
            "summary": summarize(rows),
            "rows": [join_row(r, by_id) for r in rows],
        })
    return runs


def build_dataset():
    questions = collections.OrderedDict()
    for it in load_dataset():
        q = questions.setdefault(it["question_id"], {
            "question_id": it["question_id"],
            "question": it["question"],
            "syllabus_ref": it["syllabus_ref"],
            "level": it["level"],
            "kind": it["kind"],
            "max_mark": it["max_mark"],
            "mark_scheme": it["mark_scheme"],
            "answers": [],
        })
        q["answers"].append({k: it[k] for k in ("id", "student_answer", "teacher_points", "teacher_total", "teacher_note")})
    return {"questions": list(questions.values())}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            return self._send(200, UI_FILE.read_bytes(), "text/html; charset=utf-8")
        if url.path == "/api/dataset":
            return self._json(build_dataset())
        if url.path == "/api/runs":
            return self._json([{k: v for k, v in run.items() if k != "rows"} for run in build_runs()])
        if url.path == "/api/run":
            name = parse_qs(url.query).get("name", [""])[0]
            run = next((r for r in build_runs() if r["name"] == name), None)
            if run is None:
                return self._json({"error": "run not found"}, status=404)
            return self._json(run)
        self._send(404, b"not found", "text/plain; charset=utf-8")

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _send(self, status, body, ctype):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Viewer running at http://{args.host}:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
