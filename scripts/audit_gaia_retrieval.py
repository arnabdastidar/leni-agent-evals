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

WHAT THE FLAGS REPRESENT (interpretation)
-----------------------------------------
The flags are NOT verification-loop failures, and they are NOT
infrastructure artifacts. Infrastructure faults (API failures, budget
limits, load-balancer errors encountered during the campaigns) manifest in
this dataset as *unanswered runs* (model_final_answer empty), which are
reported separately; they never produce URL matches inside a trajectory.

The flags are a data-exposure side effect of evaluating a *public*
validation set with a web-searching agent: GAIA validation questions exist
verbatim on the public web (mirrors, course materials, derived datasets),
so the agent's ordinary keyword searches sometimes surface those mirror
pages among candidate results.

Manual classification of all 25 flags by trajectory context:
  - 16 search-listing-only: the mirror URL appeared inside a web-search
    result list and was neither fetched nor cited;
  - 9 cited-in-sources: a mirror URL appears among the answer's cited
    sources (higher risk; the agent surfaced the page as a reference);
  - 0 fetched: no trajectory shows a fetch/browse action targeting a
    mirror page.
Of the 7 flagged runs in the pass@1 selection: 5 listing-only, 2 cited.
Tiered sensitivity bounds implied: excluding cited-in-sources runs only,
122/165 = 73.9%; excluding all flagged runs, 117/165 = 70.9% (the
conservative bound reported in the paper). Anyone can re-adjudicate the
"URL seen" vs "answer used" boundary from the raw trajectories in
data/eval_runs_gaia.csv.
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
