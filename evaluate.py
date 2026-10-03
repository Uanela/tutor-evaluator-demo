"""Score every results/*.jsonl file and print a small leaderboard.

Key habits built in:
  - failed outputs count as DISAGREEMENT in the headline numbers (never silently dropped)
  - every agreement figure has a bootstrap confidence interval, so you see how little 10 answers can prove
  - kappa is reported next to raw agreement (guessing is already right some of the time)
"""
import collections
import glob
import json
import pathlib
import random
import statistics

ROOT = pathlib.Path(__file__).parent


def cohen_kappa(a, b):
    """Unweighted Cohen's kappa for two equal-length label lists. None if undefined."""
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = collections.Counter(a), collections.Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def bootstrap_ci(flags, n_boot=2000, seed=0):
    """95% bootstrap interval for the mean of a list of 0/1 flags."""
    if not flags:
        return None
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(flags, k=len(flags))) for _ in range(n_boot))
    return means[int(0.025 * n_boot)], means[int(0.975 * n_boot) - 1]


def pct(x):
    return "  -  " if x is None else f"{100 * x:4.0f}%"


def fmt_ci(flags):
    ci = bootstrap_ci(flags)
    return "" if ci is None else f"[{100 * ci[0]:.0f}-{100 * ci[1]:.0f}]"


def load():
    groups = collections.defaultdict(list)
    for path in sorted(glob.glob(str(ROOT / "results" / "*.jsonl"))):
        for line in open(path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                c = r["config"]
                groups[(c["model"], c["mode"], c["order"], "scheme" if c["with_scheme"] else "noscheme")].append(r)
    return groups


def main():
    groups = load()
    if not groups:
        print("No results yet. Run run.py first.")
        return
    for key, rows in sorted(groups.items()):
        model, mode, order, scheme = key
        n = len(rows)
        valid = [r for r in rows if r["valid"]]
        clean = [r for r in valid if not r["issues"]]
        exact_all = [int(r["valid"] and r["pred_total"] == r["teacher_total"]) for r in rows]
        within_all = [int(r["valid"] and abs(r["pred_total"] - r["teacher_total"]) <= 1) for r in rows]
        exact_valid = [int(r["pred_total"] == r["teacher_total"]) for r in valid]
        kappa = cohen_kappa([r["pred_total"] for r in valid], [r["teacher_total"] for r in valid])

        pp = [(p, t) for r in valid if r["pred_points"] is not None and len(r["pred_points"]) == len(r["teacher_points"])
              for p, t in zip(r["pred_points"], r["teacher_points"])]
        point_agree = [int(p == t) for p, t in pp] if scheme == "scheme" else []

        issues = collections.Counter(i for r in valid for i in (r["issues"] or []))
        lat = [r["latency_s"] for r in rows if r["latency_s"]]
        toks = [r["output_tokens"] for r in rows if r["output_tokens"]]

        print(f"\n=== {model} | mode={mode} | order={order} | {scheme} | n={n} "
              f"({len({r['config']['seed'] for r in rows})} seed(s)) ===")
        print(f"  syntactic valid        {pct(len(valid) / n)}   retried: {sum(r['attempts'] > 1 for r in rows)}")
        print(f"  semantic valid         {pct(len(clean) / n)}   (parsed AND no issue codes)")
        print(f"  total exact (all)      {pct(statistics.fmean(exact_all))} {fmt_ci(exact_all)}   failures count as wrong")
        print(f"  total exact (valid)    {pct(statistics.fmean(exact_valid) if exact_valid else None)}   <- flatters the model: failures dropped")
        print(f"  total within 1 (all)   {pct(statistics.fmean(within_all))} {fmt_ci(within_all)}")
        print(f"  kappa (valid, totals)  {'  -  ' if kappa is None else f'{kappa:5.2f}'}")
        if point_agree:
            print(f"  per-point agreement    {pct(statistics.fmean(point_agree))} {fmt_ci(point_agree)}   ({len(point_agree)} points)")
        if issues:
            print("  issues                 " + ", ".join(f"{k} x{v}" for k, v in issues.most_common()))
        if lat:
            print(f"  latency/answer         {statistics.fmean(lat):.1f}s   output tokens/answer {statistics.fmean(toks) if toks else 0:.0f}")


if __name__ == "__main__":
    main()
