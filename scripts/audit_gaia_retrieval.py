#!/usr/bin/env python3
"""Scripted answer-page-retrieval audit for GAIA validation trajectories.

Scans every stored trajectory (intermediate_steps) for URLs of known
GAIA-derived sources whose pages contain or mirror validation answers:
the HF dataset/leaderboard pages, the GAIA paper, WebVoyager's
GAIA_web.jsonl, and agents-course metadata.jsonl.

A match means the URL appeared in the trajectory (e.g., in a search-result
list); it does not by itself prove the page was fetched or used. The audit
therefore reports (a) match counts with context, and (b) a conservative
sensitivity bound on pass@1 that treats every flagged, correct,
final-selection run as a failure.

Findings on the 2026-07 export: 25/803 trajectories (12 distinct tasks)
contain such URLs; 7 runs in the final pass@1 selection are flagged, all
scored correct; conservative pass@1 lower bound 117/165 = 70.9% against the
124/165 = 75.2% headline.
"""
import csv
import re
import sys

import pandas as pd

from regrade_gaia import question_scorer, FINAL_CAMPAIGNS

csv.field_size_limit(sys.maxsize)

PATTERN = re.compile(
    r"huggingface\.co/(?:datasets/)?gaia-benchmark"
    r"|gaia-benchmark/leaderboard"
    r"|metadata\.jsonl"
    r"|2311\.12983"
    r"|GAIA_web\.jsonl",
    re.I,
)


def main():
    runs = pd.read_csv(
        "eval_runs_gaia.csv",
        engine="python",
        usecols=["id", "created_at", "bench_task_id", "intermediate_steps", "model_final_answer"],
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
    df["ok"] = [question_scorer(m, g) for m, g in zip(df.model_final_answer, df.final_answer)]
    df["flagged"] = df.intermediate_steps.fillna("").str.contains(PATTERN)

    print(f"flagged trajectories: {int(df.flagged.sum())}/{len(df)} "
          f"({df[df.flagged].bench_task_id.nunique()} distinct tasks)")

    sel = pd.concat(
        df[(df.level == lvl) & (df.date == day) & df.answered]
        .sort_values("ts").groupby("bench_task_id").tail(1)
        for lvl, day in FINAL_CAMPAIGNS.items()
    )
    fl = sel[sel.flagged]
    n_tasks = df.bench_task_id.nunique()
    correct = int(sel.ok.sum())
    lower = correct - int(fl.ok.sum())
    print(f"pass@1 selection: {correct}/{n_tasks} = {100*correct/n_tasks:.1f}%")
    print(f"flagged in selection: {len(fl)} (correct: {int(fl.ok.sum())})")
    print(f"conservative lower bound (flagged-correct -> fail): "
          f"{lower}/{n_tasks} = {100*lower/n_tasks:.1f}%")
    fl[["bench_task_id", "level", "date", "ok"]].to_csv("gaia_retrieval_flags.csv", index=False)


if __name__ == "__main__":
    main()
