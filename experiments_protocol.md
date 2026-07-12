# Pre-Registered Protocol: Planned Follow-Up Experiments

We pre-register follow-up experiments as standard practice: designs, sample
sizes, selection rules, and analysis plans are fixed and published *before*
any run, so that future results cannot be selected or reframed after the
fact. The experiments below extend the paper's evidence along directions we
consider natural next steps; they are planned, without commitment to a
particular timeline, and whatever the numbers turn out to be, they will be
reported here and folded into the paper.

Protocol frozen: 2026-07-12.

---

## Experiment 1 — Matched-budget scaffold comparison (SpreadsheetBench)

**Question.** How does the verification-loop architecture compare to generic
scaffolds at equal inference compute — in particular, does the loop beat
brute-force sampling when token spend is held constant?

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
each), majority outcome across seeds per task. With n=100, the detectable
gap at 80% power is roughly 12–14pp for typical discordance; smaller
observed gaps are reported as unresolved, not as wins.

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
    provider, same verification prompt as B, no fine-tuning.
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
conditions on identical tasks; report per-seed variance. Whatever the
ordering, it gets reported.

**Also planned (cheap, same harness):** BullshitBench triage swap A/B/C,
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
configuration; reported alongside the benchmark's sensitivity numbers as a
2x2 (sensitivity vs. specificity). Pre-declared success criterion: none —
whatever the rate is, it gets published in reports/.

---

## Reporting

Each experiment's raw per-task outcomes land in `data/`, analysis output
in `reports/`, and the paper is updated with whatever the numbers say.
Deviations from this protocol, if any become necessary, are documented in
this file with dates rather than silently applied.
