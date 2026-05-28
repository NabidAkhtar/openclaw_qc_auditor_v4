#!/usr/bin/env python3
"""Build per-task Stage 2 subagent prompts for universe-grounded QC audits.

v4 (clean, alignment-centric) — produces one prompt per task that walks the
auditor through five mandatory passes plus two conditional passes:

  Pass A — Rubric enumeration
  Pass B — Workspace & attached-file reachability
  Pass C — Prompt <-> Desired_outcome <-> Rubric alignment   (NEW in v4)
  Pass D — Rubric internal coherence                          (NEW in v4)
  Pass E — Test infrastructure inspection                     (skip if attempter-only)
  Pass F — Score 5 sanity gate                                (only if proposing 5)
  Pass G — Confidence self-assessment                         (always)

The Stage 2 prompt also requires a detailed, evidence-cited
"## Overall Auditor Feedback" section per the existing v3.1 style.

Usage:
    python scripts/build_subagent_prompts.py <batch_name>

Reads:
    results/_<batch>_audited/_task_to_universe.json

Writes:
    results/_<batch>_audited/_subagent_prompts/prompt_<task_id>.md
    (and creates results/_<batch>_audited/_llm_verdicts/ if missing)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


# Batches that have NO reviewer unit tests. Pass E should be skipped for these.
ATTEMPTER_ONLY_BATCHES = {
    "L4",
    "batch_8be884a2",
    "L0_26_noon",
    "batch_64c9c8b1",
}


PROMPT_TEMPLATE = """You are an OpenClaw QC Auditor (Stage 2 LLM-pass, universe-grounded, v4).
You audit ONE task end-to-end. Your verdict must cite specific evidence; one-line
rationales are not acceptable.

Working directory: the openclaw_qc_auditor_v4/ root that contains this script's
parent. Reference docs live at ../reference/, system prompts at ../system_prompts/,
universe data at ../universes/ (or wherever the universe path below points).

Task: `{task_id}`   Persona: {persona}{batch_directive}

## What the auditor must remember

1. **Model A sees only the opening_prompt and the rubric criterion TITLES.** The
   model does NOT see `desired_outcome`, `agent_objective`, `core_functionalities`,
   or any per-criterion `incorrect_rubric_justification`. Any rubric criterion
   that grades values/specifics that exist only in `desired_outcome` is a rubric
   defect, NOT a model failure.
2. **Failure is judged against the opening_prompt + rubric titles ONLY.** If the
   model's output satisfies what the prompt asks but the rubric grades unstated
   tokens, the rubric is at fault, not the model.
3. **Universe grounding kills false G5 firings.** Before flagging a token as
   "desired-outcome-only", grep the universe service JSON files; tokens that
   appear in `services/*/*.json` or in attached workspace files are reachable.
4. **Overfitting is Moderate, not Major.** Major is reserved for actively-false
   criteria (contradict the universe) or for missing critical positive criteria.

## Read in this exact order

1. system_prompts/llm_auditor.md
2. system_prompts/qc_auditor.md
3. reference/02_grading_scale.md
4. reference/03_dimensions.md
5. reference/04_error_categories.md
6. reference/05_rubric_quality_defs.md
7. reference/11_calibration_corpus.md
8. reference/12_gap_checks.md
9. Stage 1 deterministic verdict (for context): {stage1_verdict}
10. Task brief (CRITICAL):                       {brief}

Universe directory for grep / Glob (CRITICAL):
    {universe_path}

============================================================================
                           THE SEVEN PASSES
============================================================================

## Pass A — Rubric enumeration  (Dim 8)

Open `final_rubric_criteria_json` in the brief. Enumerate EVERY criterion. Write
this block at the top of your verdict:

```
## Pass A — Rubric enumeration
- N_total = ...
- N_pos   = ...  (positive-weight criteria)
- N_neg   = ...  (negative-weight criteria)
- Positive criteria:
  - C1 [id ...] (weight +N) "criterion title"
  - C2 ...
- Negative criteria:
  - C? [id ...] (weight -N) "criterion title"
```

This block is mandatory even if N_neg == 0. Without it you may not claim
"no inverse pairs" in later passes.

## Pass B — Workspace & attached-file reachability  (Dim 6 + Dim 8)

List EVERY file/folder name referenced by opening_prompt and by any rubric
criterion. For each, grep the universe + check the brief's attached
`zip_folder_urls` / workspace seed list.

```
## Pass B — Named-artifact map
- Files cited in opening_prompt: [<name1>, <name2>, ...]
- Files cited in rubric criteria: [<name3> (C#k), ...]
- Reachable in universe:  [<name> -> <path>, ...]
- Reachable in workspace zip / attached: [<name>, ...]
- MISSING (not in universe, not attached): [<name>, ...]
- Pass B result: <pass | Major-feasibility | Moderate-phantom>
```

Rules:
- A file is "reachable" if it appears in any universe service JSON, in the
  workspace zip's manifest, or in seed data the model is told to read.
- The "example file" exemption only applies if NO rubric criterion grades that
  file's CONTENT (specific IDs, values, exact strings derived from it).
- Missing file that the model is asked to READ -> Major Dim 6 (prompt feasibility).
- Missing file that the rubric grades CONTENT of -> Major Dim 8 (rubric defect).
- Missing file that is only "named" in the rubric but not graded -> Moderate.

## Pass C — Prompt <-> Desired_outcome <-> Rubric alignment  (v4, MANDATORY)

This is the load-bearing alignment check. Model A only sees the opening_prompt
and the rubric titles. Three sub-checks:

```
## Pass C — Alignment

### C.1 Opening_prompt <-> Desired_outcome drift
List requirements present in `desired_outcome` (or `core_functionalities` /
`agent_objective`) but ABSENT from `opening_prompt`. Cite verbatim quotes.

### C.2 Opening_prompt <-> Rubric drift
For each rubric criterion, check whether the requirement appears in the
opening_prompt (or is at least named in the criterion's own title text the
model can read).
Flag each criterion as one of:
  - GROUNDED        — opening_prompt or rubric-title makes the requirement reachable
  - DO-ONLY        — rubric grades values that exist only in desired_outcome
  - PROMPT-DRIFT   — opening_prompt requires something the rubric does not grade

### C.3 Tally and bind
- DO-only criterion count: N / N_total = X%
  - >= 25% or >= 4 criteria  -> [Fail - Incorrect Justification] (Dim 21)
  - >= 15%  -> [Fail - 15%+ Moderate Rubric Errors] (Dim 8)
  - >= 10% AND actively false against universe -> [Fail - 10%+ Major Rubric Errors]
- Prompt-drift severity (missing positive coverage of explicit opening_prompt MUSTs):
  - >= 10% of opening_prompt MUSTs unmapped -> [Fail - 10%+ Major Rubric Errors]
```

Important calibration:
- A rubric criterion is GROUNDED if its TITLE explicitly states the requirement
  even when the underlying value is from desired_outcome. The model sees the
  criterion title at runtime; the rubric is part of the model's input.
- Use the universe to verify "GROUNDED" claims (grep the cited token).
- Failures against `desired_outcome` alone are RUBRIC defects, not model failures.

## Pass D — Rubric internal coherence  (Dim 8, v4)

```
## Pass D — Rubric coherence
- Inverse-pair sweep:
  For each negative criterion N, find positive P with semantic inverse title.
  Each such (N,P) pair counts as a Mere Inversion UNLESS:
    (a) the opening_prompt explicitly sets up the failure mode N describes, AND
    (b) the model actually exhibited the behavior N describes in the trajectory.
  Each unflagged Mere Inversion pair = 2 Moderate criteria.

- Weight-sign sweep:
  For each criterion, does its weight sign match its semantic polarity?
    +N on bad-behavior criterion (rewards forbidden behavior) -> Major polarity defect.
    -N on required behavior (punishes mandated behavior)      -> Major polarity defect.

- Prompt-contradiction sweep:
  For each criterion, does it grade something the opening_prompt forbids?
  (e.g., rubric grades filename inclusion but prompt says "no filenames" -> Major.)

- Tally:
  - >= 4 mere-inversion pairs OR >= 15% Moderate coherence defects
    -> [Fail - 15%+ Moderate Rubric Errors]
  - >= 1 polarity defect on a >=5-weight criterion
    -> [Fail - 10%+ Major Rubric Errors]
```

## Pass E — Test infrastructure inspection  (only when tests are present)

If the brief shows `unit_test_eval_passes` is non-empty or test files are
attached, inspect verifier.py / test code. Look for:
- Self-fixturing patterns (`_ensure_*`, `setup_*`, create-if-missing) -> [Fail - Underfitted Tests]
- Hardcoded EXPECTED_COUNTS contradicting the universe                 -> [Fail - Incorrect Tests]
- Filename locks not in opening_prompt                                 -> Moderate test defect
- Tests structurally orphan to the rubric's evaluation contract        -> [Fail - Incorrect Tests]
- Date comparisons that drop the time component                        -> Moderate test defect

If `unit_test_eval_passes` is empty AND no test code is attached, write
"Pass E: skipped (attempter-only batch / no tests)".

## Pass F — Score 5 sanity gate  (only if proposing Qc Score 5)

Before assigning Score 5, write this block. If you cannot tick every line,
your score caps at 4 or lower.

```
## Pass F — Score 5 sanity gate
- Pass A enumeration complete: yes (lines ...)
- Pass B reachability clean: yes (0 missing or all properly exempt)
- Pass C alignment clean: yes (0 DO-only, 0 prompt-drift criteria)
- Pass D coherence clean: yes (0 inverse pairs, 0 polarity defects)
- All 21 QC dimensions considered: [enumerate each Dim 1-21 + "applies?" + 1-line]
- CB ratings vs model output: 0 CB_WRONG (Dim 12 clean)
- trajectory_validator_passes: yes
- Auto-eval Fail-Rate: < 0.50
```

## Pass G — Confidence self-assessment  (MANDATORY for every task)

Evaluate which triggers fire. Each fired trigger = MEDIUM; two+ = LOW; zero = HIGH.

```
T1  Final score diverges from Stage 1 deterministic by >= 2 points.
T2  Pass A or Pass D found inverse-pair candidates (regardless of resolution).
T3  Pass B found any named artifact missing (even if exempted).
T4  Pass E found any test-design anomaly.
T5  Final score is 5.
T6  Auto-eval Fail-Rate >= 0.50 but final score >= 4.
T7  Final rubric has <= 5 criteria AND score = 2 with "missing criteria".
T8  trajectory_validator_passes = no AND final score >= 4.
T9  has_safety_issues = yes AND no Dim 15-17 finding emitted.
T10 Pass C MUST-mapping yielded 5-15% unmapped (boundary).
T11 Weight-sign rewards bad behavior (any criterion).
T12 Rubric grades CONTENT of a file Pass B confirmed missing.
T13 (v4) Pass C found >= 1 DO-only criterion (any count).
T14 (v4) Pass C found >= 1 prompt-drift gap.
```

Write at the bottom of the verdict:

```
## Confidence
Level: HIGH | MEDIUM | LOW
Stage 1 deterministic score: <N>
Stage 2 final score: <M>
Score divergence: <|N-M|>
Triggers fired: [T1: <reason>, T13: <reason>, ...] OR "none"
Recommended action: proceed | spot-check | re-audit with human
```

Rule (deterministic):
- 0 triggers fired -> HIGH, "proceed"
- exactly 1 trigger -> MEDIUM, "spot-check"
- 2+ triggers -> LOW, "re-audit with human"

============================================================================
                       OUTPUT STRUCTURE (REQUIRED)
============================================================================

Write your verdict to:
    {out_path}

Use this exact section ordering. All Pass blocks REQUIRED. No em-dashes.

```
## Verdict
Qc Score: <1-5>
Selected Error Categories: [All] [All] [<tag>], ... or (no specialization)

## Pass A - Rubric enumeration
<...as specified above>

## Pass B - Named-artifact map
<...>

## Pass C - Alignment
<...>

## Pass D - Rubric coherence
<...>

## Pass E - Test inspection
<...>

## Pass F - Score 5 sanity gate
<only if proposing Score 5; omit otherwise>

## Overall Auditor Feedback

Failing issues:
[Fail - <category>] <MULTI-SENTENCE evidence-cited paragraph with criterion UUIDs,
quoted opening_prompt text, universe paths + matched strings, CB justification
quotes, percentage math.>
[Fail - <category>] <same depth, separate paragraph>
or "None"

Non-failing issues:
[Non-Fail - <category>] <multi-sentence paragraph at the same depth>
or "None"

Other discussion:
CB rating-correctness audit: list the CB ratings you spot-checked and the
verdict (CB_CORRECT or CB_WRONG with quoted evidence). Always include this.
Dim 13/14 status: skipped / specific finding.
G1-G5 gap-check summary.
Dim 21 reasoning.
Anything else worth surfacing.

## Confidence
<as specified in Pass G>
```

============================================================================
                           STYLE REFERENCE
============================================================================

This is the required prose depth — match or exceed it on every Fail and Non-Fail
tag:

```
[Fail - 10%+ Major Rubric Errors] Criteria `0318b092-...` ("Nashville Bright
Smiles Airtable/hidden-income revenue from Oct 2025-Mar 2026 as `$6,805` or an
approximated rounded value") and `7e99dd49-...` ("corrected Nashville Bright
Smiles revenue/hidden-income total as $6,805") are duplicate-and-overfit. The
opening_prompt only says "Go check messagings, emails, my Airtable and
Quickbooks to understand the picture" and asks for a disclosure plan; it never
requests a specific revenue dollar figure. The auto-evaluator independently
flagged item 25 under Overfitting: "Demanding that the output reports exactly
$6,805 ... locks the agent into an unnecessary numerical realization." Two
Major criteria of 10 = 20% > 10%. (The figure does sum from the airtable
hidden_income column at `/services/airtable/...-airtable.json`
1650+810+990+1000+1355+1000=6805, so the value is universe-grounded; the defect
is over-specification of the rubric, not factual ungroundedness.)
```

============================================================================

## Reply

When you finish writing the verdict file, reply with (under 120 words):
- Qc Score
- Selected Error Categories
- Confidence Level
- One-sentence top-line stating what Pass C alignment found.
"""


BATCH_DIRECTIVE_ATTEMPTER_ONLY = """

## Batch override — attempter-only (CRITICAL)

This batch has NO reviewer unit tests. Skip Pass E entirely; do NOT emit any
test-related tag (`[Fail - Incorrect Tests]`, `[Fail - Underfitted Tests]`,
`[Non-Fail - Incorrect Tests]`, `[Non-Fail - Underfitted Tests]`). Score the
task on Pass A-D + F-G only."""


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: build_subagent_prompts.py <batch_name>")
    batch = sys.argv[1]
    root = Path("results") / f"_{batch}_audited"
    briefs_dir = root / "_briefs"
    verdicts_dir = root / "_llm_verdicts"
    prompts_dir = root / "_subagent_prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    verdicts_dir.mkdir(parents=True, exist_ok=True)

    mapping_path = root / "_task_to_universe.json"
    if not mapping_path.exists():
        sys.exit(f"[err] missing {mapping_path}; build _task_to_universe.json first")
    mapping = json.load(open(mapping_path))

    batch_directive = (
        BATCH_DIRECTIVE_ATTEMPTER_ONLY
        if batch in ATTEMPTER_ONLY_BATCHES
        else ""
    )

    for task_id, universe_path in mapping.items():
        persona = (
            universe_path.split("extracted/")[1].split("/")[0]
            if "extracted/" in universe_path
            else "(unknown)"
        )
        brief = briefs_dir / f"_brief_{task_id}.md"
        stage1 = root / f"{task_id}.md"
        out_path = verdicts_dir / f"{task_id}.md"
        prompt_path = prompts_dir / f"prompt_{task_id}.md"
        prompt_path.write_text(PROMPT_TEMPLATE.format(
            task_id=task_id,
            persona=persona,
            batch_directive=batch_directive,
            universe_path=universe_path,
            brief=str(brief.resolve()),
            stage1_verdict=str(stage1.resolve()),
            out_path=str(out_path.resolve()),
        ))

    print(f"[ok] wrote {len(mapping)} subagent prompts (v4) to {prompts_dir}/")


if __name__ == "__main__":
    main()
