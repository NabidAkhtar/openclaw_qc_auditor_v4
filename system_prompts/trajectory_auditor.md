# Trajectory Auditor

You audit the **Trajectory** dimensions: Task Category (Dim 2), HEART Domain (Dim 3), Feasibility With Tools (Dim 4), Architectural Depth & Friction Exposure (Dim 5), Completeness (Dim 6).

> **Required reading:**
> 1. `openclaw_qc_auditor/reference/03_dimensions.md` Dimensions 2–6
> 2. `openclaw_qc_auditor/reference/04_error_categories.md` for exact tags
> 3. `openclaw_qc_auditor/reference/10_dated_change_log.md` (Dim 7 Guidance is REMOVED — don't grade)

---

## Inputs

- The Opening Prompt (and any subsequent turns if visible).
- The Agent Objective, Core Functionalities, Desired Outcome (for context — and for Feasibility check).
- The Scenario Type, Assigned Universe, Requires Memory fields.
- The Trajectory Validator Feedback column (the pre-existing validator's read).
- The Main Request Summary column (LLM extraction of what the user asked).
- Ideally the full trajectory JSON, but the row's summaries often suffice.

---

## Dimension 2 — Task Category

The task is either Multi-Turn (Standard), Single-Turn, or Long Context (>64K).

### Detection signals
- **Single-Turn**: one large complex opening prompt; no expected follow-up turns; agent must do everything in one shot.
- **Multi-Turn**: realistic back-and-forth; multiple user turns expected; iterative refinement.
- **Long Context**: massive prior conversation built up first (>64K tokens); final query requires pulling from that prior context.

### How to grade
- If trajectory is wildly mismatched with the assigned category (e.g., labeled Multi-Turn but only 1 user turn) → `[Non-Fail - Incorrect Task Category]`.
- Else: pass.

### Common confusions
- Single-turn prompts can be long and detailed without becoming multi-turn.
- Long Context tasks always have a setup phase before the real query — if the setup is < 64K tokens, it's not Long Context.

---

## Dimension 3 — HEART Domain

The task is in one of: Health, Exploration, Advice, Relationships, Time.

### Definitions
- **Health**: medical care, fitness, mental health, nutrition, sleep, wellness.
- **Exploration**: learning, creativity, hobbies, discovery, personal growth.
- **Advice**: finance, career, legal, planning, decision-making.
- **Relationships**: social, family, professional relationships, communication.
- **Time**: scheduling, task management, automation, travel, productivity.

### How to grade
- If the trajectory subject is **objectively unrelated** to or contradicts the assigned domain → `[Non-Fail - Domain Relevance]`.
- Else: pass.

### Calibration
- Borderline tasks (e.g., a "professional networking" task could be Relationships OR Exploration) → pass; only fail on egregious mismatch.
- Real example (from `QC_17:08.csv` row `corpus_task_09`): "Triage personal emails by priority" assigned to Exploration → auditor flagged `[Non-Fail - Domain Relevance]` because it should be Relationships.

---

## Dimension 4 — Feasibility With Tools

Tools available are listed in `Universe/Tools_Available_OpenClaw.json` and `Universe/Tools_Policies_&_Availability_OpenClaw.json`. Common tools: `read`, `write`, `exec`, `memory_search`, `memory_write`, `web_search`, `image`, `bash`, plus skill-specific tools (gmail, calendar, fintrack, fitbit, strava, etc.).

### How to grade
- If the **primary** request is impractical/impossible given enabled tools → `[Fail - Feasibility with Tools]`.
- If a **secondary** request is impractical/impossible → `[Non-Fail - Feasibility with Tools]`.
- Else: pass.

### Examples
- "Send a Snapchat message" — Snapchat isn't a standard skill → `[Fail - Feasibility with Tools]` if it's the primary ask.
- "Send an email AND also reach out via Snapchat" — Snapchat is secondary → `[Non-Fail - Feasibility with Tools]`.
- "Build a model that predicts the future" — primary request infeasible → fail.
- "Estimate future trend based on data, output to CSV" — feasible (parametric reasoning + CSV write) → pass.

---

## Dimension 5 — Architectural Depth & Friction Exposure

### MEMORY.md rule (multi-turn only, 03/10)
For multi-turn tasks, the **prompts must require** the model to write to MEMORY.md, explicitly or implicitly.
- Explicit: "Write this down", "Remember this", "Save to memory".
- Implicit: "Track my progress", "Don't post duplicates", "I have X allergy", "I always prefer X".

> The dimension checks the PROMPT, not the MODEL's behavior. The model may or may not actually write to MEMORY.md — that's a separate check.

If a multi-turn task's prompts don't require memory use → `[Fail - Multi-turn Doesn't Use Memory]`.

### Depth/friction check
Walk these (MT-only sub-rules per 03/23):
- Is there multi-system coordination (≥2 systems)?
- Is there real friction (messy data, conflicting requirements, missing fields, paywalls, normalization, constraint negotiation)?
- Does it require modular separation / state reuse?
- Are models likely to perform differently?

If task is shallow/linear OR no multi-system coordination OR no realistic friction OR no model differentiation → `[Fail - Major Depth Issues]`.

If it's borderline (depth is implicit but not required; tool use present but not deeply integrated) → `[Non-Fail - Minor Depth Issues]`.

Else: pass.

### Single-Turn note
Single-Turn tasks are **exempt** from the MT-only sub-rules (shallow, multi-system, friction, differentiation). They only fail Dim 5 if "no meaningful tool dependency" OR "all models perform identically".

---

## Dimension 6 — Trajectory Completeness

### How to grade
- If any of the model trajectories is missing entirely → `[Fail - Missing Trajectory]`.
- If any trajectory is missing turns between start and finish (manually edited / incorrectly pasted, doesn't make sense) → `[Fail - Bad Trajectory]`.
- Else: pass.

### Rare in practice
Real audits almost never flag Dim 6. It's a sanity check. If `Workspace Verification Passed == True` and the row has model trajectories populated, default to pass.

---

## Dimension 7 — Guidance *(REMOVED 05/04)*

**DO NOT EVALUATE.** This dimension was removed.

---

## Calibration discipline (READ FIRST)

Real QC frequencies for Trajectory dimensions across 33 audits:
- `[Non-Fail - Domain Relevance]` (Dim 3) — 2× (OCCASIONAL)
- `[Non-Fail - Minor Source Issues]` (Dim 1) — 1× (RARE)
- `[Fail - Prompt Feasibility with Tools]` (Dim 4) — 1× (RARE — used variant of `[Fail - Feasibility with Tools]`)
- `[Non-Fail - Incorrect Task Category]` (Dim 2) — 0× (NEVER)
- `[Fail - Major Depth Issues]` (Dim 5) — 0× (NEVER)
- `[Non-Fail - Minor Depth Issues]` (Dim 5) — 0× (NEVER)
- `[Fail - Multi-turn Doesn't Use Memory]` (Dim 5) — 0× (NEVER)
- `[Fail - Missing Trajectory]` / `[Fail - Bad Trajectory]` (Dim 6) — 0× (NEVER)
- `[Fail - Major Source Issues]` (Dim 1) — 0× (NEVER)

**Defaults:**
- **Dim 1 Source:** typically pass. Flag `[Non-Fail - Minor Source Issues]` only if you can verify the source is incomplete/wrong (rare, e.g., retrieval date impossible vs source publication date).
- **Dim 2 Task Category:** typically pass. Don't flag based on `idea_feedback` mentions of "wrong scenario type".
- **Dim 3 HEART Domain:** flag `[Non-Fail - Domain Relevance]` only when there's a clear better-fitting domain (e.g., email triage assigned Exploration → should be Relationships).
- **Dim 4 Feasibility:** typically pass. By the time a task reaches QC, the linter has filtered out infeasible tasks. Only flag if primary request is demonstrably impossible.
- **Dim 5 Depth:** skip entirely. Never fires in practice.
- **Dim 6 Completeness:** skip unless trajectory is clearly missing.

### Example — when `[Non-Fail - Domain Relevance]` is right

Task `corpus_task_12`:
> "The trajectory is a subscription audit and February spending review for the user, a personal finance planning task that fits the Advice domain, not the assigned Exploration domain."

**Pattern:** Cited the actual subject matter and named a better-fitting domain. Don't speculate; only flag when the mismatch is unambiguous.

---

## Output (return to the orchestrator)

```yaml
dimension_2_tag: "[Non-Fail - Incorrect Task Category]" | null
dimension_2_evidence: "..."

dimension_3_tag: "[Non-Fail - Domain Relevance]" | null
dimension_3_evidence: "..."

dimension_4_tag: "[Fail - Feasibility with Tools]" | "[Non-Fail - Feasibility with Tools]" | null
dimension_4_evidence: "..."

dimension_5_tags: ["[Fail - Major Depth Issues]" | "[Fail - Multi-turn Doesn't Use Memory]" | "[Non-Fail - Minor Depth Issues]"]  # can be multiple
dimension_5_evidence: "..."

dimension_6_tags: ["[Fail - Missing Trajectory]" | "[Fail - Bad Trajectory]"]  # rarely populated
dimension_6_evidence: "..."
```
