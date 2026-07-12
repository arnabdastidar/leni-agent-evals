# Pre-Registered Protocol: Outstanding Experiments

Committed in advance of execution. Purpose: the three experiments reviewers
have identified as the remaining gaps between this paper and a definitive
result. Selection rules, sample sizes, and analysis are fixed here, before
any run, so results cannot be selected after the fact.

---

## Experiment 1 — Matched-budget scaffold baselines (SpreadsheetBench)

**Question.** Does the verification-loop architecture beat standard open
scaffolds at equal inference compute, or is the uplift purchasable by
brute-force sampling?

**Design.**
- Task set: fixed random subsample of 100 tasks from SpreadsheetBench
  Verified, drawn with seed 42 from the 400-task list (subsample IDs to be
  committed to this repo before any run).
- Conditions (all using Claude Opus 4.6, identical tool access, identical
  sandbox, production file I/O):
  1. **ReAct-style**: standard reason-act loop, no external oracle, no
     specialist; canonical prompt from Yao et al. adapted minimally for
     spreadsheet editing.
  2. **Best-of-n**: n independent single-pass attempts; final answer chosen
     by majority vote over recalculated answer-region values; n set so
     total token spend matches condition 4 (report n and spend).
  3. **CRITIC-style**: generate, then tool-based critique (recalculation
     output shown back to the same model), one revision round.
  4. **Leni production** (reference): full loop with Leni-Cell-S.
- Budget matching: record total input+output tokens per task per condition;
  conditions 1–3 tuned to within ±10% of condition 4's median spend.
- Runs: 3 seeds per condition (temperature as production default).

**Analysis (fixed).** Per-condition mean pass rate over seeds with Wilson
95% CIs; pairwise McNemar tests on per-task outcomes (condition 4 vs.
each), majority outcome across seeds per task. With n=100, detectable gap
at 80% power is roughly 12–14pp for typical discordance; smaller observed
gaps are reported as unresolved, not as wins.

**Cost estimate.** ~100 tasks x 4 conditions x 3 seeds = 1,200 task-runs;
at observed per-task spend this is bounded and schedulable in one week.

---

## Experiment 2 — Three-condition specialist-swap ablation

**Question.** Is the loop's value due to the observer's *independence*
(any model that didn't generate the artifact), its *specialization*
(training on the verification task), or both?

**Design.** Hold the SpreadsheetBench loop fixed; vary only the
observe/compare stage:
  - **A. Specialist** (production): Leni-Cell-S.
  - **B. Self-verification**: the generating frontier model (Claude Opus
    4.6) verifies its own artifact.
  - **C. Independent generalist**: a frontier model from a different
    provider (Gemini class), same verification prompt as B, no fine-tuning.
- Same 400-task set; 3 seeds per condition (9 full runs).
- Record per task: flags raised, rescues, regressions (pass->fail after
  "fix"), verifier confusion counts (extends Table 4 of the paper to all
  three conditions).

**Predictions (falsifiable, stated in advance).**
- If independence is what matters: C ≈ A > B on catch rate.
- If specialization is what matters: A > C ≈ B.
- If both: A > C > B.

**Analysis (fixed).** Catch rate c, fix rate r, false-alarm rate f per
condition with binomial CIs; rescue counts with paired comparison across
conditions on identical tasks; report per-seed variance. This is the
paper's central hypothesis; whatever the ordering, it gets reported.

**Also run (cheap, same harness):** BullshitBench triage swap A/B/C,
n=100, judged under the benchmark's standard panel.

---

## Experiment 3 — Adversarially matched valid-premise control (BullshitBench)

**Question.** Does the epistemic firewall stay calibrated when a *valid*
premise is styled to look like a fabrication?

**Design.**
- Construct 100 questions mirroring the benchmark's structure: same five
  domains in the same proportions (SE 40; Finance/Legal/Medical/Physics 15
  each), same 13 surface techniques — but every premise is real and
  verifiable (obscure-but-real frameworks, correctly applied mechanisms,
  real standards with precise parameters). Each item carries a citation
  establishing premise validity.
- Authoring: drafted per technique template, then validated by two domain
  reviewers per item; items failing validation are replaced before any
  model sees the set. The full set + citations are committed to this repo
  before evaluation.
- Conditions: Leni on Sonnet 4.6 and Opus 4.6 (production harness), plus
  the bare base models for reference.
- Metric: acceptance rate (system answers substantively within the valid
  frame). A rejection of a valid premise counts as a false positive.

**Analysis (fixed).** False-positive rate with Wilson 95% CI per
configuration; report alongside the benchmark's sensitivity numbers as a
2x2 (sensitivity vs. specificity). Pre-declared success criterion: none —
whatever the rate is, it gets published in reports/.

---

## Reporting

Each experiment's raw per-task outcomes land in `data/`, analysis output
in `reports/`, and the paper is updated with whatever the numbers say.
Deviations from this protocol, if any become necessary, are documented in
this file with dates rather than silently applied.
