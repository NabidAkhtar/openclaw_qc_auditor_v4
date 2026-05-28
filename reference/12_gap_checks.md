# Gap-Checks Reference (v2 — post-c09 post-mortem)

Source: post-mortem analysis of task `post_mortem_task` (May 20, 2026), which scored Score 5 from the v1 calibrated auditor but Score 3 from the real human auditor. The post-mortem identified four framework-coverage blind spots; this file documents the four gap-checks that close them.

> **These are checks layered on top of the 21 official QC dimensions.** They do not replace any dimension. They surface signals that the existing dimensions cannot see because of (a) the 05/04 removal of Desired Outcome Coverage as a graded dimension, and (b) the absence of a graded dimension that consumes `trajectory_validator_feedback`.

Implementation: `audits_v2/scripts/audit_v2.py` → `check_*` functions.

---

## G1 — Prompt-coverage gap

### What it catches

Tasks where `trajectory_validator_passes == "no"` AND the validator's feedback explicitly cites missing core functionalities or a low specification-coverage score (e.g., `Score: 3/5` with named missing deliverables).

### Why it exists

The QC dimension matrix has no dimension that consumes the trajectory validator's score. Dim 4 (Feasibility With Tools) is about tools, not coverage. Dim 7 (Trajectory: Guidance) was REMOVED on 05/04. So the trajectory validator's "3/5 — prompt does not engage core functionalities" feedback was orphaned with nowhere to land.

### Tags

- `[Non-Fail - Prompt Coverage Gap]` — validator gave 3/5, or failed without explicit score but feedback flags missing/incomplete coverage.
- `[Fail - Major Prompt Coverage]` — validator gave ≤2/5 with named missing Desired-Outcome deliverables.

### Trigger logic (summary)

```text
if trajectory_validator_passes != "no":           skip
parse "Score: X/5" from trajectory_validator_feedback
if X <= 2:                                        Fail
elif X == 3:                                      Non-Fail
elif score-not-found AND feedback cites missing:  Non-Fail
else:                                             skip
```

---

## G2 — Rubric pruning

### What it catches

Tasks where `rubric_criteria_builder_v2_json` had N criteria but `final_rubric_criteria_json` has fewer — AND the dropped criteria include explicit Desired-Outcome deliverables (anchor table, findings log, traceability table, timezone note, parsing libraries note, flaky scenarios section, coverage gaps section, named test cases, etc.).

### Why it exists

When Desired Outcome Coverage was removed as a graded dimension on 05/04, the framework lost its primary mechanism for catching rubric trimming that strips out Desired-Outcome deliverables. The auto-evaluator's "missing criterion" flags don't catch this case because the missing items were already pruned out before the auto-eval ran. The original c09 task lost ~half of its 34 candidate criteria in this exact way; the final 18-criterion rubric no longer graded most of the Desired-Outcome deliverables.

### Tags

- `[Non-Fail - Rubric Pruning]` — drop ratio ≥25% and at least one dropped item references a Desired-Outcome deliverable; OR drop ratio ≥35%.
- `[Fail - Rubric Pruning]` — drop ratio ≥45% AND at least one dropped item references a Desired-Outcome deliverable.

### Trigger logic (summary)

```text
n_b = len(rubric_criteria_builder_v2_json)
n_f = len(final_rubric_criteria_json)
if n_b == 0 or n_b <= n_f: skip
drop_ratio = (n_b - n_f) / n_b
dropped_ids = {builder ids} - {final ids}
deliverable_drops = dropped items whose title matches anchor table / findings log / etc.
if drop_ratio >= 0.45 and deliverable_drops:                          Fail
elif drop_ratio >= 0.25 and (deliverable_drops or drop_ratio >= 0.35): Non-Fail
```

The regex used to identify Desired-Outcome deliverables in dropped titles:

```text
anchor table | traceability table | findings log | timezone (assumptions? )?note |
parsing libraries note | flaky scenarios section | coverage gaps section |
named test cases | input scenario | expected output | actual behavior | fix recommendation
```

---

## G3 — Model skipped required artifact

### What it catches

Tasks whose `desired_outcome` text implies a file artifact deliverable (`.md`, `.csv`, `.json`, `workspace`, `save`, `report`, etc.), but the Model A trajectory contains zero file-writing tool calls AND `workspace_verification_passed` is not `{yes, true, 1, passed, pass}`.

### Why it exists

The Tests Coverage dimension (Dim 15) only applies when `verifiers.py` exists. For experimental tasks (verifiers absent or empty `unit_test_*` fields), the existing framework has no way to flag "model didn't produce the required artifact." Yet "skipped the workspace artifact" is the largest single failure mode in real deliveries (≈27% of failed-rubric weight in `18_delivery`).

### Tag

- `[Non-Fail - Model Skipped Artifact]` — applies only when all of:
  - `desired_outcome` contains an artifact hint
  - trajectory has no write / edit_file / create_file / shell `> file` / `python …open(…,'w')…` write
  - `workspace_verification_passed` is not affirmative

### Tool detection (summary)

The check considers both formal tool calls and shell-based writes:

```text
formal tool name in:  write, edit_file, str_replace, create_file, save_file,
                      edit_notebook, patch_file, fs_write, edit, update_file,
                      put_file
shell pattern:        > FILENAME.ext,  cat <<EOF … EOF,
                      open(... , 'w'),  .write_text(,
                      echo … > FILENAME.ext,  tee FILENAME.ext
```

If any of these patterns are found anywhere in `model_trajectories_json`, the artifact-skipped check returns no flag.

---

## G5 — Desired-Outcome Leak detector *(added 2026-05-23)*

### What it catches

Rubric criteria that grade tokens (filenames, column names, enum values, section names, status tags) which appear in `desired_outcome` but NOT in `opening_prompt`. Per the QC spec, `desired_outcome` is not visible to the model, so a criterion that grades a deliverable named only in `desired_outcome` penalises the model for something it could not have known.

### Why it exists

The May-2026 `Untitledspreadsheet.xlsx` calibration round had 2 of 4 tasks under-flagged with the same root cause: the rubric leaked desired_outcome-only requirements (specific column names, enum values, section headings). Both were flagged by the human as `[Fail - Incorrect Justification]` on Dim 21. The previous calibrator could not catch this pattern because Dim 21 was only emittable by the LLM in the interactive workflow.

### Tags

- `[Non-Fail - Weak Justification]` — leak_ratio ≥ 0.10 AND ≥ 2 leaked criteria.
- `[Fail - Incorrect Justification]` — leak_ratio ≥ 0.25 AND ≥ 4 leaked criteria.

### Trigger logic (summary)

```text
leak_tokens = {tokens in desired_outcome} - {tokens in opening_prompt}
              (normalised: lowercase + _/-./ collapsed to spaces)
leak_criteria = number of final_rubric_criteria_json items whose title
                contains >= 1 leak token
leak_ratio = leak_criteria / total_criteria

leak_ratio >= 0.25 AND leak_criteria >= 4 -> Fail
leak_ratio >= 0.10 AND leak_criteria >= 2 -> Non-Fail
```

### Token regexes (extracted from `desired_outcome`)

| Pattern | Example |
|---|---|
| Filenames | `categories_manuel.json` |
| Backtick-quoted identifiers | `` `column_name` `` |
| snake_case identifiers ≥5 chars | `content_summary` |
| Quoted enum-style values | `"completed_moment"` |
| Bracketed status tags | `[MATCHED]`, `[STALE]` |
| Markdown section headings | `### Matched` |
| Title Case multi-word phrases (2-5 words) | `Reconciliation View`, `Section A: Preferences` |

Trivial tokens (`memory.md`, `verifier.py`, `snapshots.json`, generic phrases) are excluded.

---

## G4 — Model A failure rate (informational)

### What it surfaces

The actual fraction of weighted rubric that Model A failed, computed from `rubric_justifications_breakdown_json`. A criterion is treated as failed when `model_mistake_justification` is populated **AND** does not contain a pass marker (`"No mistake"`, `"correctly avoided"`, `"correctly did not"`, etc.). For negative-weight criteria, the check requires active language (`"the model exposed/included/invented/…"`) to count the negative as triggered.

### Why it exists

Even when no Fail or Non-Fail tag fires from G1–G3 or the official dimensions, knowing that Model A failed 100% of weighted rubric is a useful audit-trail signal. It does not lower the score. It documents that the task fulfilled the design constraint and gives the reviewer a sanity-check anchor when a clean Score 5 doesn't intuitively match the underlying performance.

### Tag

None. G4 is informational only — it appears in the audit MD as:

```text
Informational:
- Model A failure rate: 100% (X of Y rubrics failed)
```

### Scoring formula

```text
passed_w = Σ(weights of passed criteria)
abs_w    = Σ(|weights|)
score%   = passed_w / abs_w * 100             (clamped to [0, 100])
failure% = 100 - score%                       (clamped to [0, 100])
```

This matches the Ratings Validity formula in `reference/02_grading_scale.md`.

---

## Order of operations inside `audit_v2.py`

```text
1. Run v1 checks (Dim 11, Dim 8 fail rate, Action Tier)
2. Run G1 prompt coverage          → maybe add tag
3. Run G2 rubric pruning           → maybe add tag
4. Run G3 model skipped artifact   → maybe add tag
5. Run G5 desired-outcome leak     → maybe add tag  (added 2026-05-23)
6. Run G4 model A failure rate     → always add informational
7. Score:
     any [Fail] → 2
     ≥3 [Non-Fail] → 3
     ≥1 [Non-Fail] → 4
     else → 5
```

The G4 informational note never participates in scoring.

---

## How to verify this layer

Run the LLM-pass auditor (Stage 2 in `README.md`) on the same batch and cross-check tasks where the deterministic audit emitted Score 5 but the LLM-pass downgrades the score. Those divergences are the gap-check signal — if the same pattern repeats across batches, the deterministic G1-G5 thresholds need tightening (raise G2 / expand G3 regex / etc.).
