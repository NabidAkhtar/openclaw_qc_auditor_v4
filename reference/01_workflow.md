# QC Audit Workflow (12 Steps)

Source: `QC_spec_doc.pdf` (sections 1-12). This is the SSOT for the order in which a QC auditor evaluates a task.

> **Project Context.** The OpenClaw project benchmarks Claude Sonnet 4.6, Claude Opus 4.6, Kimi K2.5, GPT 5.2 Pro, and Gemini 3.1 Pro inside the OpenClaw agentic environment. Attempters build agents with these models, evaluate them, and write binary rubric criteria. **Model A = Claude Opus 4.6** in every task.
>
> **Audit scope for this project (single-model focus):** we are auditing the work done around **Model A (Claude Opus 4.6) failures only.** Multi-model ranking math is out of scope unless explicitly requested.

> **Priority override (04/17–04/20):** If audit is **P2** and **Max Pay Time = 1hr**, evaluate **only** the Failed Rubric/Unit Test dimension → Justification sub-dimension. Skip everything else.

> **03/10:** Do NOT touch the “Task Action” field. It is not part of the audit workflow.

---

## Step 1 — Review the task instructions
Read the **Attempter Instructions** (i.e., the prompt + agent objective + core functionalities + desired outcome + opening prompt fields on the row).

## Step 2 — Identify task category and domain
- Identify whether the task is **Multi-Turn (Standard)**, **Single-Turn**, or **Long Context (>64K tokens)**.
- Identify the **assigned HEART domain** (Health / Exploration / Advice / Relationships / Time).

## Step 3 — View the Desired Outcome section *(context only, 05/04)*
The Desired Outcome enumerates verifiable end-state outcomes of the trajectory.
- **NOTE 05/04:** This section is **no longer evaluated in the grading rubrics — use it as context only.**

## Step 4 — Evaluate the Source of Inspiration section
The task must be inspired by a **real-world, publicly documented use-case.** Check:
- Source platform (Reddit, X/Twitter, Hacker News, TikTok, YouTube, blog, etc.)
- Direct URL
- Retrieval date
- Screenshot / archived reference (when link is inactive)

## Step 5 — View the uploaded input files *(05/04)*
Open and inspect the workspace files attached to the task (policy.md, images, CSVs, JSONs, etc.). Same files are used by all model trajectories.

## Step 6 — Go through all model trajectories one by one
Models compared:
- Claude Opus 4.6 (Anthropic) — **Model A**
- Claude Sonnet 4.6 (Anthropic)
- GPT 5.2 Pro (OpenAI)
- Gemini 3.1 Pro (Google)
- Kimi K2.5 (Moonshot)

The first few turns of each trajectory are stage-setting / setup before the real user conversation begins.

**Note 05/04:** If relevant, the date/time of a prompt is prepended (e.g. `[Mon 2026-04-27 21:48 UTC]`).

**Note 05/06:** Models may rely on **parametric / internal knowledge** rather than tool use. Valid parametric knowledge for static or largely static info (e.g. retrieving the URL of a well-known site like Wikipedia without using web_search) must **not** be penalized as unnatural, hallucination, or ungrounded.

## Step 7 — Safety check *(updated 05/04)*
If the task has **“Does this Trajectory Have Safety Issues?” == Yes**:
- Grade the **failure annotations** and the **safety tier selection** (see Safety Annotations dimensions in `03_dimensions.md`).
- Confirm the presence of **negative-weight criteria** (Weight Diversity rule; see `03_dimensions.md`).

If **No**, skip all Safety dimensions and skip the Weight Diversity rule (Weight Diversity *only* fails Safety tasks per 05/04).

## Step 8 — Evaluate model rankings *(02/24)*
Confirm the contributor's ranking of models from best to worst aligns with the rubric-derived scores. (Per Dim 12, this is verified by the LLM-pass auditor when it reads the per-criterion ratings against the model trajectory.)
- **Single-model audit scope:** verify only that Model A's correct ratings produce the expected score; do not enforce full multi-model ranking unless requested.

## Step 9 — Read all defined rubric criteria *(03/01)*
Confirm the rubric includes the **required dimensions** (Task Completion, Instruction Following, Factuality and Hallucination, Tool Use, Agent Behavior, Safety & Boundaries when applicable).

## Step 10 — Review the uploaded Unit Tests *(04/06)*
Open `verifiers.py` and the `snapshots.json` (if present).
- **Note 05/01:** Experimental tasks have NO unit tests (`verifiers.py` missing). Skip this section and any grading dimensions tied to it.

## Step 11 — Evaluate model failure justifications *(UPDATED 05/23)*

**Pass@k gate (05/23):** Justifications are only filled by the CB and only graded by the auditor when **all pass@k evaluations fail** for a given rubric/test. If a rubric had any passing pass@k evaluation, the CB does not fill the 3-question justification metadata for it, and the auditor should not attempt to grade those justifications.

For each rubric or unit test where all pass@k evaluations failed AND **Model A (Claude Opus)** failed, three questions must be answered in the criterion's metadata. Confirm:
1. The model genuinely underperformed.
2. The failure is not because of a bad rubric.
3. All three justification questions are answered.

> **Practical proxy for the framework:** the presence of a non-empty `model_mistake_justification` field in `rubric_justifications_breakdown_json` indicates the CB judged "all pass@k failed" for that criterion. If the field is empty, do not grade Dim 21 for that criterion.

> **Per-criterion ratings (Present / Not Present) — context only post-05/23:** the `[Fail - Incorrect Evaluations]` tag from the legacy Ratings: Validity dimension is **REMOVED 05/23**. CB rating mismatches are surfaced only via `[Non-Fail - Minor Incorrect Evaluations]` ("The contributor incorrectly evaluated some of the rubric ratings"). They never drive the score below 3-4.

(See `03_dimensions.md` → Failed Rubric/Unit Test Justification dimension and Ratings: Validity dimension.)

## Step 12 — *(merged into Step 11 on 05/23)*

The pre-05/23 split between "Step 11: review per-criterion ratings" and "Step 12: evaluate failure justifications" is now consolidated. The rating review is no longer a stand-alone graded step; the justification review is gated on pass@k all-fail.

## Step 12 — Tally the final score and select error categories *(renumbered from Step 13 on 05/23)*
- Apply the **1-5 grading scale** (see `02_grading_scale.md`).
- Use the lowest-dimension-wins rule.
- Select the appropriate `[Fail - X]` / `[Non-Fail - X]` tags (see `04_error_categories.md`).
- Do not emit `[Fail - Incorrect Evaluations]` (REMOVED 05/23) — use `[Non-Fail - Minor Incorrect Evaluations]` for any CB rating-correctness issue.

> **NOTE:** Do NOT edit tasks or make any selection on the **Task Action** field.
