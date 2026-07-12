# Verification Loops for Reliable Enterprise AI Agents — Artifact Release

Run-level evaluation record and audit scripts accompanying the paper
*"Where Does Agent Reliability Come From? A Cross-Benchmark Decomposition of
Verification Loops, Specialist Models, and Scaffolding in a Production
Enterprise Agent"* (Leni Inc., 2026).

Everything reported in the paper is computable from the files in this
repository. The record deliberately includes unfavorable and superseded runs
(development configurations, degraded runs, a superseded GAIA campaign) as
evidence against post-hoc selection.

## Layout

```
paper.pdf                        current preprint draft
experiments_protocol.md          pre-registered designs for planned
                                 follow-up experiments (frozen before runs)
LICENSE.md                       MIT (scripts) / CC BY 4.0 (data)
data/
  benchmarks.csv                 benchmark registry (GAIA, SpreadsheetBench,
                                 BullshitBench, DRACO)
  eval_runs_spreadsheet.csv      1,299 runs / 400 tasks / 4 configurations
  eval_runs_bullshit.csv         500 runs / 100 items; 200 with per-judge
                                 scores (GPT, Gemini, Claude), panel means,
                                 bucket assignments
  eval_runs_gaia.csv             803 validation runs / 165 tasks / 7 campaigns,
                                 full trajectories and final answers per run
  eval_runs_draco.csv            DRACO valid-premise control: rubric-graded
                                 runs over 100 legitimate expert-level tasks
  eval_runs.csv                  early development runs (all benchmarks)
  bullshitbench_tasks.csv        task metadata
  gaia_tasks.csv                 task metadata + validation gold answers
  draco_tasks.csv                task metadata + rubrics
scripts/
  regrade_gaia.py                re-grades every stored GAIA trajectory with
                                 the official scorer; validates 218/218 against
                                 database-resident grades; reports pass@1
                                 (124/165 = 75.2%) and best-of-k (137/165)
  audit_gaia_retrieval.py        scripted answer-page-retrieval audit over all
                                 803 trajectories; produces the 25-flag list
                                 and the conservative 70.9% lower bound
  audit_training_exclusion.py    n-gram containment audit of evaluation items
                                 against (private) specialist training corpora;
                                 publishes summary counts only
reports/
  regrade_report.txt             output of regrade_gaia.py
  gaia_regraded_runs.csv         per-run re-grades, all 803 runs
  gaia_retrieval_flags.csv       per-run retrieval-audit flags
  exclusion_audit_report.txt     question-corpus scan: 4/30,104 flags, all
                                 internal test traffic; 0 eval items in the
                                 training-signal corpus
  exclusion_audit_flags.csv      per-pair flags with session/account IDs
```

## Reproducing the paper's numbers

Requires Python 3.10+ and pandas (`pip install -r requirements.txt`).
The scripts read the CSVs from the current directory, so run them from
`data/`:

```
pip install -r requirements.txt
cd data
python3 ../scripts/regrade_gaia.py           # GAIA pass@1 and best-of-k
python3 ../scripts/audit_gaia_retrieval.py   # retrieval flags + lower bound
```

SpreadsheetBench and BullshitBench headline numbers are direct aggregations of
the CSVs (see the paper's Methodology section for the selection rules; the
`v3-final` configuration and the 2026-03-24 judged batches are the reported
runs).

## What is not in this repository

Specialist model weights, the production training corpora, and production
prompts are proprietary. The training-corpus exclusion audit runs privately
via `scripts/audit_training_exclusion.py`; its summary counts are published in
`reports/exclusion_audit_report.txt` when available.

## License / contact

See `LICENSE.md` (MIT for scripts, CC BY 4.0 for data). Questions and audit
requests: Arunabh Dastidar, Leni Inc.
