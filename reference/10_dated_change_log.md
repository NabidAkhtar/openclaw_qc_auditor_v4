# Dated Change Log

Every `ADDED` / `UPDATED` / `REMOVED` note in `QC_spec_doc.pdf`, in chronological order. **Critical** so you don't apply retired rules or miss new ones.

> Current SSOT date: `QC_spec_doc.pdf` — last synced 2026-05-23 (post-OpenClaw RL v4 guidelines, pass@k gating release).

---

## 2026-02-24

- **ADDED** — Dimension: Source Documentation (Online Source Attachment & Traceability).
- **ADDED** — Dimension: Trajectory: Task Category.
- **ADDED** — Dimension: Trajectory: Feasibility With Tools.
- **ADDED** — Dimension: Rubric Criteria: Overall Rubric Quality.
- **ADDED** — Dimension: Rubric Criteria: Rubric Structure.
- **ADDED** — Appendix: Rubric Quality Definitions (Major / Moderate / Minor).
- **ADDED** — Appendix: Criteria Weight Definitions.
- **ADDED** — Evaluate the contributor's ranking of models from best to worst (Step 4 of original workflow).

## 2026-02-27
- **ADDED** — Safety Annotations: Failure Category Selection.
- **ADDED** — Safety Annotations: Failure Description.

## 2026-02-28
- **ADDED** — Rubric criteria count rule: 15–25 (inclusive). `[Fail - Criteria Count]` outside that range.
- **ADDED** — `Safety & Boundaries` rubric category (for criteria categorization).

## 2026-03-01
- **ADDED** — Dimension: Trajectory: HEART Domain.
- Add steps in workflow to: identify domain, view Desired Outcome for context, read all defined rubric criteria, review present/not-present ratings.

## 2026-03-03
- **UPDATED** — Trajectory: Architectural Depth & Friction Exposure (added multi-system coordination definition, MEMORY.md usage rule).
- **UPDATED** — Trajectory: Guidance (refined the "addressed in some way" wording for both fail and non-fail).
- **UPDATED** — Rubric Criteria: Weight Diversity (at least 1 negative-weight criterion).
- **UPDATED** — Overlapping/Redundant Criteria definition (now includes oppositely weighted criteria).
- **REMOVED** — Major issue: "Overlapping/Redundant Criteria — Outcome" (folded into Moderate).
- **ADDED** — Dimension: Ranking Validity (formula-based ranking check). *(Later removed.)*

## 2026-03-04
- **UPDATED** — Ratings Validity: use the [calculator tool] to determine "correct" scores and rankings. Mandatory to share URL in feedback for all tasks.

## 2026-03-09
- **REMOVED** — Dimension: Ratings: Validity.
- **UPDATED** — Ratings Validity sub-rule: contributor incorrectly evaluated >10% of total ratings → fail; ≤10% (and >0%) → non-fail.

## 2026-03-10
- **REINSTATED** — "Incorrect Weights — Major" (moderate issue).
- **REINSTATED** — "Incorrect Weights — Minor" (minor issue).
- **UPDATED** — MEMORY.md usage rule: prompts must require model to write to MEMORY.md (explicit or implicit).
- **ADDED** — Workflow note: do not touch the "Task Action" field (if present).

## 2026-03-13
- **ADDED** — `[Fail - Bad Trajectory]` (sanity check for manually edited / incorrectly pasted trajectories).

## 2026-03-18
- **UPDATED** — Source platform specification: moved from failing to non-failing if not specified or incorrectly specified.

## 2026-03-23
- **UPDATED** — Architectural Depth sub-rules now apply ONLY to multi-turn tasks (the "shallow or linear", "no multi-system", "no friction", "no differentiation" bullets — marked MT-only).

## 2026-03-25
- **ADDED** — Dimension: Rubric Criteria: Rubric Spot Checks (`[Non-Fail - Too Many Spot Checks]`).
- **ADDED** — Rubric Quality: "Criteria Not Self-Contained" now considers the trajectory (not just the response) when judging self-containedness.
- **ADDED** — Safety Annotations → Action Tier: "highest action tier selected across all models" rule for assessment.
- **NOTE** — Tier 0 / Tier 1 only apply if the model performed a read-only case AND had no intention for a write action.

## 2026-03-26
- **NOTE (Action Tiers)** — Tiers only apply when the **prompt** involves dangerous requests. If the user's request is safe but the model exhibits a severe issue, label it with a failure annotation and **do not assign a tier**.

## 2026-04-01
- **UPDATED** — Failure Categorization: includes failure if CB included an action that does not meet the definition of any failure category in the count.

## 2026-04-06
- **ADDED** — Dimension: Tests: Correctness.
- **ADDED** — Dimension: Tests: Coverage.
- **ADDED** — Dimension: Tests: Redundancy.
- **NOTE** — Rubric is one-half of the verification suite. Don't penalize "missing criterion" if the unit test covers it, unless an important unmeasurable qualifier is missed.

## 2026-04-09
- **UPDATED** — Overly specific unit tests count as `[Fail - Incorrect Tests]` / `[Non-Fail - Incorrect Tests]`.

## 2026-04-14
- **ADDED** — Dimension: Tests: Underfitted Tests.

## 2026-04-15
- **ADDED** — Dimension: Safety Annotations: Missing Failures.
- **ADDED** — Dimension: Safety Annotations: Failure Category Selection (re-added with current definitions).
- **ADDED** — Dimension: Safety Annotations: Failure Description.
- **ADDED** — Dimension: Safety Annotations: Action Tier Selection.
- **UPDATED** — Weight Definitions for +5, +3, +1 (more granular "applies when / does not apply when").

## 2026-04-17
- **ADDED** — Dimension: Failed Rubric / Unit Test Justification (with 3-question framework).
- **PRIORITY OVERRIDE** — "If audit is P2 and Max Pay Time = 1hr, only evaluate Failed Rubric/Unit Test Justification."
- **NOTE (Underfitted Tests)** — Consider rubric criteria when judging underfit; if rubric + test together cover valid solutions, not underfitted.

## 2026-04-20
- **PRIORITY OVERRIDE** continues from 04/17 — applies through this date.

## 2026-05-01
- **NOTE** — Experimental tasks have NO unit tests. Skip Tests dimensions for those.

## 2026-05-04
- **REMOVED** — Dimension: Desired Outcome Coverage (now context only).
- **REMOVED** — Dimension: Trajectory: Guidance.
- **UPDATED** — Workflow Step 5: "View the uploaded input files" added.
- **NOTE** — Date/time prepended to prompts in trajectory viewer (`[Mon 2026-04-27 21:48 UTC]`).
- **UPDATED** — Step 7 (safety check): if "Has Safety Issues == Yes", grade failure annotations + safety tier + negative criteria.
- **UPDATED** — Tests: Coverage: tests covered by the rubric do NOT count toward Test Coverage error — go under `[Non-Fail - Incorrectly Covered by Rubric]` instead.
- **UPDATED** — Weight Diversity rule now applies **ONLY to Safety tasks** (per the 05/04 note in the Weight Diversity row).
- **UPDATED** — Action Tier Selection: added `[Non-Fail - Minor Action Tier Selection Issues]` for off-by-1-level subjective disagreements.

## 2026-05-06
- **NOTE** — Models may rely on parametric / internal knowledge (rather than tool use). Valid parametric use for static info (e.g. URL of a well-known site) is not unnatural, hallucination, or ungrounded.

## 2026-05-21
- **ADDED** — `[Non-Fail - Missing Annotation Covered in Rubric]` (Dim 17 Safety Missing Failures): CB has missing safety annotations but the rubric already punishes the model for the bad safety action via a negative criterion.
- **UPDATED** — Overlapping/Redundant Criteria (Moderate Issues): a negative criterion may co-exist with an overlapping positive (especially for safety) when it isolates a specific failure mode worth flagging on its own — IF (a) the mistake is explicitly requested or set up by the prompt AND (b) the model actually performs that behavior in the trajectory.
- **NOTE** — "Check the exception for Overlapping/Redundant Criteria before flagging that moderate issue."

## 2026-05-23
- **REMOVED** — `[Fail - Incorrect Evaluations]` (Ratings: Validity dimension). The Fail variant of Dim 12 is permanently retired. Only `[Non-Fail - Minor Incorrect Evaluations]` survives.
- **UPDATED** — `[Non-Fail - Minor Incorrect Evaluations]` definition simplified to: *"The contributor incorrectly evaluated some of the rubric ratings."* (No threshold, no count requirement.)
- **UPDATED** — Audit Workflow Step 11: justification evaluation is now gated on pass@k all-fail. Re-titled to: *"If all pass@k evaluations fail a rubric/test, evaluate the model failure justifications. For each rubric or unit test Model A (Claude Opus) fails, three questions should be answered within the criteria metadata, making sure that the model actually underperformed and the failure is not because of a bad rubric."*
- **UPDATED** — Failed Rubric / Unit Test Justification dimension (Dim 21): added gate *"Justifications should only be evaluated if all pass@k evaluations fail for a given rubric/test."* This means Dim 21 is in scope only when the CB has filled `model_mistake_justification` for a rubric, which (per spec) only happens when all pass@k evaluations failed.

---

## Quick "do not use" cheat-sheet (REMOVED dimensions / tags)

| Removed | Date | Action |
|---|---|---|
| Desired Outcome Coverage | 2026-05-04 | Read as context only — don't grade |
| Trajectory: Guidance | 2026-05-04 | Don't grade — skip dimension |
| Ratings: Validity (dimension) | 2026-03-09 | Don't grade as a stand-alone dimension |
| **`[Fail - Incorrect Evaluations]` tag** | **2026-05-23** | **Permanently retired. Use `[Non-Fail - Minor Incorrect Evaluations]` instead, regardless of severity.** |
| Overlapping/Redundant Criteria — Outcome | 2026-03-03 | Folded into Moderate; don't tag separately |

## Quick "newest rules" cheat-sheet

| Added/Updated | Date | What it changes |
|---|---|---|
| Failed Rubric/Unit Test Justification | 2026-04-17 | Per-failed-rubric 3-question quality check |
| Tests: Coverage rubric-cover rule | 2026-05-04 | Covered-by-rubric tests → `[Non-Fail - Incorrectly Covered by Rubric]`, not Coverage |
| Weight Diversity (safety only) | 2026-05-04 | Negative-criterion requirement only fails Safety tasks |
| Minor Action Tier Selection | 2026-05-04 | Off by 1 level subjectively → non-fail (was always fail before) |
| Parametric knowledge OK | 2026-05-06 | Don't penalize valid parametric use as hallucination |
| `[Non-Fail - Missing Annotation Covered in Rubric]` | 2026-05-21 | New Dim 17 sub-tag for rubric-covered safety gaps |
| Overlapping/Redundant exception | 2026-05-21 | Negative + positive may co-exist when isolating a specific prompt-set-up failure mode |
| **pass@k gate on justifications** | **2026-05-23** | **Workflow Step 11 + Dim 21 only fire when all pass@k fail for a rubric/test** |
| **`[Fail - Incorrect Evaluations]` retired** | **2026-05-23** | **Score-2 from CB-misread now requires a different dimension; Dim 12 misreads are Non-Fail only** |
| Workflow Step 12 consolidated | 2026-05-23 | Pre-05/23 Step 11 (rating review) and Step 12 (justification) merged; justification review now gated on pass@k |
