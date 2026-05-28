# OpenClaw QC Auditor — v4

A two-stage QC auditor for OpenClaw RL tasks. Stage 1 is a deterministic
signal-extraction + gap-check pass. Stage 2 dispatches an LLM subagent per task
that does universe-grounded alignment-checking. The framework produces a single
xlsx review sheet with a calibrated confidence score and human-review queue.

This is the **clean, shareable v4** — consolidated passes, alignment-centric,
no redundant or conflicting instructions.

---

## What v4 changes versus v1.1 / v3.1

| Change | Why |
|---|---|
| **Pass C — Prompt ↔ Desired_outcome ↔ Rubric alignment** (new explicit pass) | Calling a model "failure" for tokens that exist only in `desired_outcome` is the most common calibration miss. The model sees only the opening_prompt and rubric titles — so a rubric grading content from desired_outcome is a rubric defect, not a model failure. |
| **Pass D — Rubric internal coherence** (separate pass, was merged before) | Inverse-pair sweep + weight-sign sweep + prompt-contradiction sweep, all in one place. |
| **Pass B — Reachability** now combines workspace+attached-file checks | Catches the "prompt names a CSV that doesn't exist" failure mode (Dim 6). |
| **Pass G — Confidence** triggers extended to T13/T14 | DO-only criteria and prompt-drift gaps now flag for human review. |
| **Pass A enumeration is mandatory** before any "no inverse pairs" claim | Stops agents from shortcutting to "vacuous" without listing criteria. |
| **All Pass blocks consolidated**, output structure unchanged | One source of truth; no instructions repeated in multiple sections. |

---

## Folder layout

```
openclaw_qc_auditor_v4/
├── README.md                       ← you are here
├── requirements.txt
├── scripts/
│   ├── prepare_input.py            ← xlsx -> CSV (if needed)
│   ├── run_stage1.py               ← Stage 1 wrapper
│   ├── extract_signals.py          ← per-task signal JSON
│   ├── audit_v2.py                 ← deterministic per-task verdict
│   ├── build_audit_brief.py        ← per-task brief for Stage 2 input
│   ├── build_universe_map.py       ← task_id -> universe snapshot
│   ├── build_subagent_prompts.py   ← Stage 2 prompt builder (v4)
│   ├── build_audit_xlsx.py         ← per-task aggregator (legacy)
│   └── build_review_sheet.py       ← single-tab review xlsx (recommended)
├── reference/                      ← QC spec docs (read by every Stage 2 agent)
├── system_prompts/                 ← LLM auditor instructions
├── universes/                      ← 30 persona snapshots (~21MB) — see below
├── examples/
│   └── sample_verdict.md           ← what a v4 verdict looks like
└── results/                        ← per-batch outputs land here
```

### Universes bundled

`universes/<persona>/snapshot-openclaw-<persona>-multi-...` — 30 personas
included as of 2026-05-27 / 2026-05-28 refresh. Universes are grep-checked by
Stage 2 agents for Pass B reachability and Pass C alignment.

Personas included:

```
adriana_ortiz   adriana_reyes   amanda_allen   amanda_evans   ana_salazar
andrew_mitchell andrew_robinson ashley_jones   bella_notte    daniel_guo
daniel_park     daniel_taylor   destiny_lewis  eric_harris    francisco_hernandez
hotel           isabella_ramos  isaiah_harris  jennifer_perez john_choi
kai_allen       kenneth_liu     lucia_gutierrez manuel_romero marcus_davis
matthew_smith   matthew_thompson melissa_jackson meriton       rachel_wilson
```

If a new persona shows up in a delivery CSV, drop its snapshot zip into
`universes/<persona>/snapshot-openclaw-<persona>-multi-<id>-<hash>/` (extracted),
then re-run `build_universe_map.py`.

`build_universe_map.py` looks for `universes/` first (relative to the v4 folder).
If it's empty it falls back to the legacy `/Users/vishal.kushwaha/Documents/Openclaw_RL copy/L12_universes/extracted/`
path for backward compatibility.

---

## End-to-end workflow

You have a delivery CSV. You have universe data extracted at
`L12_universes/extracted/<persona>/snapshot-openclaw-<persona>-multi-...`.
Run, in order:

```bash
cd openclaw_qc_auditor_v4

# 1. Stage 1 — deterministic signals, briefs, deterministic verdicts
python scripts/run_stage1.py /path/to/delivery.csv <batch_name>

# 2. Build task -> universe snapshot map
python scripts/build_universe_map.py /path/to/delivery.csv <batch_name>
#    Reports any missing personas. Provide their snapshots, then re-run.

# 3. Build the v4 Stage 2 prompts (one .md per task)
python scripts/build_subagent_prompts.py <batch_name>

# 4. Dispatch one LLM subagent per task in parallel waves of ~12.
#    Each subagent reads its prompt file under
#    results/_<batch>_audited/_subagent_prompts/prompt_<task_id>.md
#    and writes its verdict to
#    results/_<batch>_audited/_llm_verdicts/<task_id>.md

# 5. Build the single-tab review xlsx
python scripts/build_review_sheet.py /path/to/delivery.csv \\
    results/_<batch>_audited_review.xlsx \\
    --results-dir results/_<batch>_audited/_llm_verdicts \\
    [--email-csv /path/to/email.csv]
```

The review xlsx has 12 columns including a calibrated **Confidence %**, a
**Why Human Review** column listing exactly which triggers fired, and a
**Sharp Focus Areas** column with task-specific reviewer instructions. The
**Overall Auditor Feedback** column carries the full multi-paragraph verdict
prose (no truncation).

### Attempter-only batches

If the batch has no reviewer tests (`unit_test_eval_passes` blank everywhere),
add the batch name to `ATTEMPTER_ONLY_BATCHES` in
`scripts/build_subagent_prompts.py`. The Stage 2 prompt then skips Pass E and
will not emit test-related Fail tags.

---

## The seven passes the auditor runs

| Pass | Purpose | Mandatory? |
|---|---|---|
| **A** | Enumerate every rubric criterion with weight + title | Always |
| **B** | Workspace & attached-file reachability (catches phantom files) | Always |
| **C** | Prompt ↔ Desired_outcome ↔ Rubric alignment | Always |
| **D** | Rubric internal coherence (inverse pairs, weight signs, contradictions) | Always |
| **E** | Test infrastructure inspection (self-fixturing, hardcoded counts) | When tests present |
| **F** | Score-5 sanity gate | Only when proposing Score 5 |
| **G** | Confidence self-assessment (14 triggers, HIGH/MEDIUM/LOW band) | Always |

Each pass writes its own structured block to the verdict. After the passes, the
auditor writes the rich **Overall Auditor Feedback** narrative.

---

## What "alignment" means here

**Model A only sees the opening_prompt and the rubric criterion titles.** It
never sees `desired_outcome`, `agent_objective`, or `core_functionalities`. The
auditor must judge model performance against what the model could reasonably
know. v4 codifies this with Pass C:

- **GROUNDED** criterion — opening_prompt or the rubric title itself states
  the requirement. Fair to grade against.
- **DO-ONLY** criterion — rubric grades a token that exists only in
  desired_outcome. Calling this a "model failure" is incorrect; it's a
  rubric drift defect. Counts toward Dim 21 (Incorrect Justification).
- **PROMPT-DRIFT** gap — opening_prompt requires something the rubric does
  not grade at all. Counts toward Dim 8 (Major Rubric Errors) if it covers
  more than 10% of opening_prompt MUSTs.

The Pass C tally drives the binding Fail tag selection.

---

## Confidence scoring (the human-review queue)

Each Stage 2 verdict ends with a `## Confidence` block. The aggregator parses
it and computes a 0-100% Confidence score using weighted penalties:

| Trigger | Penalty | What it catches |
|---|---|---|
| T1 — Stage 1↔2 score divergence ≥2 | −25% | Strongest disagreement signal |
| T7 — Small rubric flagged underfit | −20% | Calibration boundary zone |
| T12 — Rubric grades phantom file content | −20% | Catastrophic prompt-feasibility miss |
| T3 — Named artifact missing | −15% | Phantom file signal |
| T5 — Score 5 | −15% | Score-5 spot-check default |
| T6 / T8 / T9 | −15% each | Auto-eval high but score 4-5 / validator-failed-but-passed / safety-task-not-graded |
| T2 / T4 / T10 / T11 / T13 / T14 | −10% each | Less critical signals |

**Bands**: HIGH ≥75% (auto-publish), MEDIUM 50-74% (light spot-check), LOW <50% (deep re-audit).
**Needs Human Review = Yes** if confidence <75 OR any high-stakes trigger
(T1, T5, T7, T12) fired.

---

## File contents per Stage 2 verdict

Each `results/_<batch>_audited/_llm_verdicts/<task_id>.md` contains:

1. `## Verdict` — score + selected error categories
2. `## Pass A` — rubric enumeration
3. `## Pass B` — named-artifact reachability map
4. `## Pass C` — alignment (the three sub-checks)
5. `## Pass D` — rubric coherence
6. `## Pass E` — test inspection (or "skipped")
7. `## Pass F` — Score 5 sanity gate (only if Score 5)
8. `## Overall Auditor Feedback` — multi-paragraph prose with criterion UUIDs,
   universe paths, quoted opening_prompt text, CB justification quotes,
   percentage math
9. `## Confidence` — Pass G block parsed by the aggregator

The xlsx pulls (1), (8), and (9) into reviewer-facing columns. The remainder
stays in the verdict file as audit trail.

---

## Common pitfalls (and what v4 fixes)

| Pitfall | v4 fix |
|---|---|
| Auditor calls model "failure" for desired-outcome-only tokens | Pass C explicitly tallies DO-ONLY criteria and binds them as rubric defects |
| Phantom files in the prompt go undetected | Pass B enumerates every named artifact and grep-checks reachability |
| Rubric has +5 weight on bad-behavior criterion | Pass D weight-sign sweep flags polarity defects |
| Inverse-pair redundancies inflate the rubric | Pass D inverse-pair sweep with both (prompt-setup) AND (model-exhibited) conditions |
| Self-fixturing verifier.py passes vacuously | Pass E inspection catches `_ensure_*` / `setup_*` patterns |
| Auditor over-grades Score 5 | Pass F gate requires explicit Dim-by-Dim attestation before allowing Score 5 |
| Auditor wrong but doesn't know | Pass G confidence triggers route the task to human review |

---

## Reference docs (do not modify lightly)

`reference/` carries the QC spec snapshot every Stage 2 agent reads:

- `02_grading_scale.md` — Score 1-5 definitions
- `03_dimensions.md` — 21 QC dimensions
- `04_error_categories.md` — every valid Fail / Non-Fail tag
- `05_rubric_quality_defs.md` — atomicity / overfitting / underfitting rules
- `11_calibration_corpus.md` — 33 calibration audits
- `12_gap_checks.md` — G1-G5 definitions

If you update these, all in-flight audits should be re-run.

---

## Reproducing a session

Each batch produces a self-contained tree:

```
results/_<batch>_audited/
├── <task_id>.md                       ← Stage 1 verdict
├── _summary.md                        ← batch-level rollup
├── _briefs/_brief_<task_id>.md        ← Stage 2 input
├── _signals_<batch>/<task_id>.json    ← raw signals from Stage 1
├── _subagent_prompts/prompt_<task_id>.md   ← what each LLM agent sees
├── _task_to_universe.json             ← persona mapping
└── _llm_verdicts/<task_id>.md         ← canonical per-task verdict
```

This is everything a reviewer needs to re-audit or appeal a specific task.
