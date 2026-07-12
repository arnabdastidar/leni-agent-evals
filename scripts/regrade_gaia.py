#!/usr/bin/env python3
"""Re-grade every stored GAIA trajectory with the official GAIA scorer.

Reads eval_runs_gaia.csv and gaia_tasks.csv (CSV export of the production
evaluation database) and recomputes correctness for every run from the stored
model_final_answer against the validation gold answers.

Validation: the re-grader agrees with all 218 runs that carried an
is_correct grade at export time (218/218).

Outputs:
  - regrade_report.txt        per-campaign, per-level results
  - gaia_regraded_runs.csv    one row per run with the recomputed grade

Selection rules reported:
  pass@1  = last completed (answered) attempt per task within the
            final-configuration campaigns (L1: 2026-04-10; L2/L3: 2026-04-20)
  best-of = max over all stored runs per task (pass@k, k varies by tier)
"""
import csv
import re
import string
import sys

import pandas as pd

csv.field_size_limit(sys.maxsize)

FINAL_CAMPAIGNS = {1: "2026-04-10", 2: "2026-04-20", 3: "2026-04-20"}


# --- official GAIA question scorer (gaia-benchmark/GAIA scorer.py) ---
def _is_float(x):
    try:
        float(x)
        return True
    except (ValueError, TypeError):
        return False


def _norm_num(s):
    for c in ["$", "%", ","]:
        s = s.replace(c, "")
    try:
        return float(s)
    except ValueError:
        return float("inf")


def _norm_str(s, remove_punct=True):
    s = re.sub(r"\s", "", str(s))
    if remove_punct:
        s = s.translate(str.maketrans("", "", string.punctuation))
    return s.lower()


def question_scorer(model_answer, ground_truth):
    if model_answer is None or (isinstance(model_answer, float) and pd.isna(model_answer)):
        return False
    ma, gt = str(model_answer).strip(), str(ground_truth).strip()
    if _is_float(gt):
        return _norm_num(ma) == float(gt)
    if any(c in gt for c in [",", ";"]):
        g, m = re.split(r"[,;]", gt), re.split(r"[,;]", ma)
        if len(g) != len(m):
            return False
        return all(
            _norm_num(a) == float(b) if _is_float(b) else _norm_str(a, False) == _norm_str(b, False)
            for a, b in zip(m, g)
        )
    return _norm_str(ma) == _norm_str(gt)


def main():
    runs = pd.read_csv(
        "eval_runs_gaia.csv",
        engine="python",
        usecols=["id", "created_at", "bench_task_id", "is_correct", "model_final_answer"],
    )
    tasks = pd.read_csv(
        "gaia_tasks.csv",
        engine="python",
        usecols=["bench_task_id", "level", "split", "final_answer"],
    )
    df = runs.merge(tasks, on="bench_task_id").query("split=='validation'").copy()
    df["ts"] = pd.to_datetime(df.created_at, format="mixed")
    df["date"] = df.ts.dt.date.astype(str)
    df["answered"] = df.model_final_answer.notna()
    df["regraded"] = [
        question_scorer(m, g) for m, g in zip(df.model_final_answer, df.final_answer)
    ]

    lines = []
    graded = df[df.is_correct.notna()]
    agree = (graded.is_correct.astype(bool) == graded.regraded).sum()
    lines.append(f"Validation: {agree}/{len(graded)} agreement with database-resident grades\n")

    lines.append("Per-campaign, per-level (answered runs / correct):")
    per = (
        df.groupby(["date", "level"])
        .agg(runs=("id", "size"), answered=("answered", "sum"), correct=("regraded", "sum"))
        .reset_index()
    )
    lines.append(per.to_string(index=False))

    p1 = []
    for lvl, day in FINAL_CAMPAIGNS.items():
        f = df[(df.level == lvl) & (df.date == day) & df.answered]
        last = f.sort_values("ts").groupby("bench_task_id").tail(1)
        n_tasks = df[df.level == lvl].bench_task_id.nunique()
        p1.append((lvl, int(last.regraded.sum()), n_tasks))
    total_c = sum(c for _, c, _ in p1)
    total_n = sum(n for _, _, n in p1)
    lines.append("\npass@1 (last answered attempt, final campaigns): "
                 + ", ".join(f"L{l}: {c}/{n}" for l, c, n in p1)
                 + f"  overall {total_c}/{total_n} = {100*total_c/total_n:.1f}%")

    best = df.groupby(["bench_task_id", "level"]).regraded.max().reset_index()
    bl = best.groupby("level").regraded.agg(["count", "sum"])
    lines.append("best-of-all-runs: "
                 + ", ".join(f"L{l}: {int(r['sum'])}/{int(r['count'])}" for l, r in bl.iterrows())
                 + f"  overall {int(best.regraded.sum())}/{len(best)} = {100*best.regraded.mean():.1f}%")

    report = "\n".join(lines)
    print(report)
    with open("regrade_report.txt", "w") as fh:
        fh.write(report + "\n")
    df[["id", "created_at", "bench_task_id", "level", "answered", "is_correct", "regraded"]].to_csv(
        "gaia_regraded_runs.csv", index=False
    )


if __name__ == "__main__":
    main()
