# Grading Dimensions — Full Reference

Source: `QC_spec_doc.pdf` grading rubrics table. Each dimension below shows:
- **When it applies** (some are scoped: multi-turn only, safety only, has-unit-tests only, etc.)
- **The 1-2 (Fail) criteria** → exact tag names
- **The 3-4 (Non-Fail) criteria** → exact tag names
- **The 5 (Pass) criterion**
- **Auditor notes** (calculation rules, edge cases)

Tags are listed verbatim — use them in the `Selected Error Categories` output.

> ## **READ `11_calibration_corpus.md` FIRST**
>
> The spec rules below are correct. **How strictly to apply them is the calibration question.** Real QC auditors apply many rules loosely; the corpus doc shows the actual frequencies in a 33-audit sample.
>
> **Defaults from the corpus:**
> - Most tasks pass (Score 5 = 33%, Score 4 = 33%, Score 2-3 = 33%).
> - Score 5 has 0 tags. Score 4 averages 2.2 tags. Score 2 averages 3.2 tags.
> - **Some Fail tags are NEVER used in practice** even when the spec arithmetic says they should fire (see Dim 9, 11 below).
> - **Auto-evaluator outputs over-flag by 2-3×.** Treat as advisory only.

---

## Dimension 1 — Source Documentation: Online Source Attachment & Traceability *(ADDED 02/24)*

**Applies to:** All tasks.

Evaluates whether the task was properly sourced from real online content and documented transparently. URLs may expire; live availability is not required.

### [1-2 / Fail]
- `[Fail - Major Source Issues]`
  - No source URL provided.
  - Clearly fabricated or unverifiable source.
  - No documentation of the retrieval date AND insufficient information to trace original inspiration.

### [3-4 / Non-Fail]
- `[Non-Fail - Minor Source Issues]`
  - Source link provided but documentation incomplete.
  - Source platform not specified or incorrectly specified (e.g. Reddit, X, Hacker News). *(03/18 — moved from failing to non-failing.)*
  - Minor formatting issues.
  - No archived reference or screenshot when link appears inactive.

### [5 / Pass]
- Source clearly documented.
- Platform specified.
- Original URL included.
- Retrieval date included.
- Screenshot or archived reference included when possible.
- Provides sufficient traceability even if link expires.

---

## Dimension 2 — Trajectory: Task Category *(ADDED 02/24)*

**Applies to:** All tasks.

Task category must match what the contributor selected (Multi-Turn Standard / Single-Turn / Long Context >64K).

### [1-2 / Fail]
- *N/A* — task category mismatch alone never fails the task.

### [3-4 / Non-Fail]
- `[Non-Fail - Incorrect Task Category]`
  - The trajectory contains egregious category misalignment.

### [5 / Pass]
- The trajectory is clearly related to the assigned category.

### Auditor notes
- **Multi-Turn (Standard):** realistic back-and-forth, natural pacing, skill discovery/tool coordination/memory/friction happen organically across multiple turns.
- **Single-Turn:** one large, complex, natural prompt; no follow-up turns; tests planning/coordination in one shot.
- **Long Context (>64K Tokens):** massive prior context built up (fake but realistic prior convo) before the real agent task; final query must require the model to pull info from that prior context.

---

## Dimension 3 — Trajectory: HEART Domain *(ADDED 03/01)*

**Applies to:** All tasks.

Trajectory must be related to the assigned HEART domain.

### [1-2 / Fail]
- *N/A*

### [3-4 / Non-Fail]
- `[Non-Fail - Domain Relevance]`
  - The trajectory is objectively unrelated to, or contradicts the definition of, the assigned domain.

### [5 / Pass]
- The trajectory is clearly related to the assigned domain.

### Auditor notes — domain definitions
- **Health:** Medical care, fitness, mental health, nutrition, sleep, wellness.
- **Exploration:** Learning, creativity, hobbies, discovery, personal growth.
- **Advice:** Finance, career, legal, planning, decision-making.
- **Relationships:** Social, family, professional relationships, communication.
- **Time:** Scheduling, task management, automation, travel, productivity.

---

## Dimension 4 — Trajectory: Feasibility With Tools *(ADDED 02/24)*

**Applies to:** All tasks.

### [1-2 / Fail]
- `[Fail - Feasibility with Tools]`
  - The **primary** request is impractical or impossible and can't be answered by the tools available or enabled for the task.

### [3-4 / Non-Fail]
- `[Non-Fail - Feasibility with Tools]`
  - One or more **secondary** requests are impractical or impossible and can't be answered by the tools available.

### [5 / Pass]
- The requests are completely actionable by the tool framework.

---

## Dimension 5 — Trajectory: Architectural Depth & Friction Exposure *(UPDATED 03/03)*

**Applies to:** All tasks. Several sub-rules apply **only** to multi-turn tasks (marked `MT-only` below).

> **CALIBRATION:** `[Fail - Major Depth Issues]` and `[Fail - Multi-turn Doesn't Use Memory]` have NEVER fired in 33 audits. `[Non-Fail - Minor Depth Issues]` is also unobserved. By the time a task reaches QC, depth is presumed adequate (it passed CB → reviewer first). **Default: pass this dimension unless the task is laughably trivial.**

Evaluates whether the task meaningfully tests agent-building capability and exposes differences across models. Must require multi-stage coordination, real tool use, cross-step dependencies, and at least one realistic friction point.

**Multi-system coordination** = the agent must retrieve, reconcile, or act upon information across two or more distinct systems, where outputs from one system meaningfully influence decisions or actions in another.

**MEMORY.md usage (UPDATED 03/10):** prompts in multi-turn tasks have to **require** the model — explicitly or implicitly — to write details to `MEMORY.md` (long-term context for future conversations). Examples:
- Explicit: "Write this down to your memory", "Remember this"
- Implicit: "Track my progress", "Make sure you don't post duplicates", "I have a bad knee", "I always prefer the subway over a cab"

> This dimension checks whether the **prompts require** memory use, NOT whether the model actually writes to MEMORY.md in the trajectory.

### [1-2 / Fail]
- `[Fail - Major Depth Issues]`
  - No meaningful tool dependency.
  - All models perform nearly identically due to low complexity.
  - **MT-only (03/23):**
    - Task is shallow or linear (solvable in a few turns without architectural evolution) unless required by the assigned category.
    - No multi-system coordination required.
    - No realistic friction (no messy data, no ambiguity, no constraint conflict, no backtracking opportunity).
    - Task does not meaningfully expose differences in reasoning, modularization, or state management.
- `[Fail - Multi-turn Doesn't Use Memory]` *(03/03)*
  - **MT-only.** At least one trajectory does not **require** the model to write to MEMORY.md.

### [3-4 / Non-Fail]
- `[Non-Fail - Minor Depth Issues]`
  - Architectural evolution is possible but not clearly required.
  - Tool use is present but not deeply integrated into reasoning.
  - Task meets minimum requirements but lacks strong differentiation power.

### [5 / Pass]
- Task clearly forces architectural reasoning.
- Requires modular separation or structured multi-stage planning.
- Includes real friction (conflicting data, missing fields, paywalls, normalization issues, constraint negotiation).
- Requires state reuse or refactoring.
- Meaningfully differentiates model capability.

---

## Dimension 6 — Trajectory: Completeness

**Applies to:** All tasks.

### [1-2 / Fail]
- `[Fail - Missing Trajectory]`
  - At least one of the agent trajectories is missing.
- `[Fail - Bad Trajectory]` *(03/13)*
  - At least one agent trajectory is missing parts between start and finish, so the conversation does not make sense. (Often = manually edited or incorrectly pasted. Rare; sanity check only.)

### [3-4 / Non-Fail]
- *N/A*

### [5 / Pass]
- All trajectories are present and complete.

---

## Dimension 7 — Trajectory: Guidance *(REMOVED 05/04)*

> **DO NOT EVALUATE THIS DIMENSION.** It was removed on 05/04 and is no longer part of the QC audit workflow.

(Historical: This dimension checked whether the CB guided the agent toward the components of the Desired Outcome.)

---

## Dimension 8 — Rubric Criteria: Overall Rubric Quality *(ADDED 02/24)*

**Applies to:** All tasks with a rubric (i.e., basically all of them).

> **CALIBRATION:** the auto-evaluator's "Defective Criteria Count" is **NOT** the Major Issues count. Auditor judgment trumps arithmetic — re-evaluate each flagged criterion against the actual prompt before counting it as Major. Real QC typically counts 2-3 Major issues per task, not the 10-15 the auto-eval flags. Use the discount rules in `05_rubric_quality_defs.md`. Fail tags fire ~6/33 audits; Non-Fail variants fire ~4/33; the rest pass this dimension.

See `05_rubric_quality_defs.md` for category definitions (Major / Moderate / Minor). Tally errors using the **number of criteria CB wrote as the denominator.** Do NOT double-count a criterion even if it has multiple issues. The numerator counts unique flagged criteria.

### [1-2 / Fail]
- `[Fail - 10%+ Major Rubric Errors]`
  - More than 10% (>10%) of criteria contain Major issues.
- `[Fail - 15%+ Moderate Rubric Errors]`
  - More than 15% (>15%) of criteria contain Moderate OR Major issues.
- `[Fail - 20%+ Minor Rubric Errors]`
  - More than 20% (>20%) of criteria contain Minor OR Moderate OR Major issues.

### [3-4 / Non-Fail]
- `[Non-Fail - Up to 10% Major Errors]`
  - Up to 10% (<=10%) of criteria contain Major issues.
- `[Non-Fail - Up to 15% Moderate Errors]`
  - Up to 15% (<=15%) of criteria contain Moderate or Major issues (with Major contributing <5%).
- `[Non-Fail - 5-20% Minor Errors]`
  - Between 5% and 20% (>=5% and <=20%) of criteria contain Minor / Moderate / Major issues (Major <5%, Moderate <15%).

### [5 / Pass]
- Less than 5% (<5%) of rubrics have minor issues.
- No major or moderate issues.

---

## Dimension 9 — Rubric Criteria: Rubric Structure *(ADDED 02/24)*

**Applies to:** All tasks with a rubric. These errors reflect structural problems and are failing if present.

> **CALIBRATION: DO NOT FLAG `[Fail - Criteria Count]`.** Real QC NEVER flagged this in 33 audits, even with rubrics that the JSON suggested were 1, 3, 4, 10, or 56 criteria. The `final_rubric_criteria_json.length` is unreliable; the true rubric structure likely includes spot-check rollups, sub-criteria, and other elements not in the JSON. The "15-25 inclusive" rule is enforced upstream by the linter — by the time a task reaches QC, the count is presumed within range. **Default: skip Dim 9 entirely unless weights are clearly invalid.**
>
> `[Fail - Invalid Weights]` has also never been observed in practice — the {-5,-3,-1,+1,+3,+5} restriction is also linter-enforced upstream.

### [1-2 / Fail]
- `[Fail - Invalid Weights]`
  - One or more criteria use weights outside the allowed set `{-5, -3, -1, +1, +3, +5}`.
- `[Fail - Criteria Count]` *(02/28)*
  - Rubric includes fewer than 15 criteria OR more than 25 criteria.

### [3-4 / Non-Fail]
- *N/A*

### [5 / Pass]
- Rubric has between 15 and 25 total criteria (inclusive).
- All rubric criteria have weights within `{-5, -3, -1, +1, +3, +5}`.

---

## Dimension 10 — Rubric Criteria: Rubric Spot Checks *(ADDED 03/25)*

**Applies to:** Tasks where the rubric includes spot-checks (random instance verification for repeated outputs).

CBs are expected to provide **up to 5 spot checks** if there are sufficiently similar outcomes, plus a criterion that checks the **volume** of the outcomes.

### [1-2 / Fail]
- *N/A*

### [3-4 / Non-Fail]
- `[Non-Fail - Too Many Spot Checks]`
  - There are more than 5 spot checks for any group of outcomes.

### [5 / Pass]
- Every group of outcomes has up to 5 spot checks.

### Example
- Output: 200 emails. Rubric should have 3 spot-checks (e.g., "Email #2, #7, #14 are correctly personalized") + 1 volume check ("Agent sends at least 200 replies").

---

## Dimension 11 — Rubric Criteria: Weight Diversity *(UPDATED 03/03)*

**Applies to:** **Safety tasks ONLY (per 05/04).** Tasks where "Does this Trajectory Have Safety Issues?" == Yes.

> **CALIBRATION: This dimension's Fail tag has NEVER fired in 33 real audits.** "Safety task" means literally `has_safety_issues == "yes"` in the row — NOT "scenario_type is in {Private Data Usage, Contextual Risk, Ambiguous Requests, Borderline, Third-Party, Jailbreaks, High-Stakes}". In all observed audits, `has_safety_issues` is blank even for those scenario types, so Dim 11 was out of scope. **Default: skip Dim 11 unless `has_safety_issues` literally equals "yes".**

The rubric should contain at least 1 negative-weight criterion.

### [1-2 / Fail]
- `[Fail - No Negative Criteria]`
  - The rubric doesn't contain any negative-weight criteria.

### [3-4 / Non-Fail]
- *N/A*

### [5 / Pass]
- The rubric contains at least one negative-weight criterion.

---

## Dimension 12 — Ratings: Validity *(dimension REMOVED 03/09; Fail tag RETIRED 05/23)*

> **DIMENSION STATUS:** This dimension was REMOVED on 03/09 as a stand-alone graded dimension. Only ONE tag survives: `[Non-Fail - Minor Incorrect Evaluations]`. The Fail variant was permanently retired on 05/23.

**Current scope:** This is now a discretionary signal for CB rating-correctness issues only (e.g., CB misreads of model output). It does NOT drive a Score 1-2 verdict; the worst outcome from this tag alone is Score 3-4.

### [1-2 / Fail] — RETIRED 05/23, do NOT emit
- **`[Fail - Incorrect Evaluations]`** — **PERMANENTLY RETIRED.** Do NOT emit this tag under any circumstance.
- **`[Fail - Major Evaluation Error]`** — Legacy tag, also out of policy post-05/23. Do NOT emit.

> Severe CB rating errors that would historically have triggered a Fail tag should now be routed to the appropriate dimension:
> - If the rubric itself has defects → Dim 8 (Rubric Quality)
> - If justifications defend an invalid rubric → Dim 21 (Failed Rubric/Unit Test Justification)
> - If CB genuinely misread model output → `[Non-Fail - Minor Incorrect Evaluations]` (this tag)

### [3-4 / Non-Fail] — Active
- **`[Non-Fail - Minor Incorrect Evaluations]`** *(UPDATED 05/23)*
  - **Spec wording:** *"The contributor incorrectly evaluated some of the rubric ratings."*
  - Emit when one or more CB ratings are objectively wrong against the model's actual output, regardless of count.
  - No threshold applies — emit even for a single wrong rating if the error is objective.

### [5 / Pass] — No tag
- The CB ratings and criteria weights are correct.

### Auditor notes (post-05/23)
- **pass@k gate:** The CSV's `rubric_justifications_breakdown_json` populates only criteria where all pass@k evaluations failed. CB-misread checks should be confined to that scope; do not re-rate criteria whose justification field is empty.
- **Score consequence:** This tag alone yields Score 3-4 at worst. To reach Score 2, another dimension must bind (Dim 8 Rubric Quality, Dim 21 Justification, or G5 leak detection).
- **"057ad pattern":** For the canonical pattern where 15/15 criteria are CB-mismarked, the framework now emits `[Non-Fail - Minor Incorrect Evaluations]` and relies on **other dimensions** to drive a Score 2 verdict when warranted.

---

## Dimension 13 — Tests: Correctness *(ADDED 04/06)*

**Applies to:** All tasks with `verifiers.py` (skip if experimental task).

> **CALIBRATION:** `[Fail - Incorrect Tests]` is NEVER used in 33 real audits. Even tasks with auto-eval-flagged incorrect tests get `[Non-Fail - Incorrect Tests]` (2× in corpus). **Default to Non-Fail when any test issue exists; reserve Fail for cases where >50% of tests are objectively wrong AND would let broken outputs through.**

Test logic should align with the conversational and environmental context. *(04/09: overly specific unit tests are also counted as incorrect.)*

Tests may check artefacts not explicitly requested if they are **implicitly required** to achieve the goal (see examples below).

**Example 1 (Incorrect):** Test checks unrequested implementation details — e.g., exact button color, exact response formatting when other choices are valid.

**Example 2 (Acceptable):** Prompt asks for a list of customer names + emails matching criteria. A test that checks the model mentions the correct count is acceptable: the model must find this info, mentioning it adds value, and the test serves as a hallucination check.

### [1-2 / Fail]
- `[Fail - Incorrect Tests]`
  - **If ≥10 unit tests:** at least 20% of unit tests contain incorrect logic or are misaligned with the task's context.
  - **If <10 unit tests:** at least one unit test contains incorrect logic or is misaligned with the task's context.

### [3-4 / Non-Fail]
- `[Non-Fail - Incorrect Tests]`
  - **If ≥10 unit tests:** at least one unit test (but fewer than 20%) contains incorrect logic or is misaligned.

### [5 / Pass]
- All unit tests contain correct logic and are aligned with the task's context.

---

## Dimension 14 — Tests: Underfitted Tests *(ADDED 04/14)*

**Applies to:** All tasks with `verifiers.py`.

> **CALIBRATION:** `[Fail - Underfitted Tests]` fires only **1× in 33 real audits.** Real QC defaults to `[Non-Fail - Underfitted Tests]` (3× in corpus) regardless of % underfit. The 30% threshold is spec-stated but rarely applied. **Fail this only when (a) the test suite would pass clearly broken output AND (b) the rubric also doesn't catch it.** Cite specific concrete cases (e.g., "test accepts 'Capital One is good, not bad' via a lone `no` token") rather than just "75% underfit per auto-eval".

Underfitted tests = too loose, overly broad, or lenient. They accept all valid solutions, but also accept some incorrect / invalid / arguably undesirable ones.

**Note (04/17):** Some tests may be wider to account for artifacts that can't easily be validated, more general prompt requests, or requests that may be fulfilled in multiple ways. Consider whether the corresponding **rubric** criterion covers the gap. If `rubric + test` together cover the valid solutions, the test is **not** underfitted.

### [1-2 / Fail]
- `[Fail - Underfitted Tests]`
  - More than 30% of the unit tests are underfitted.

### [3-4 / Non-Fail]
- `[Non-Fail - Underfitted Tests]`
  - Up to 30% of the unit tests are underfitted.

### [5 / Pass]
- There are no underfitted tests.

---

## Dimension 15 — Tests: Coverage *(ADDED 04/06)*

**Applies to:** All tasks with `verifiers.py`.

> **CALIBRATION:** `[Fail - Test Coverage]` fires 2× in 33 audits and ONLY when (a) >20% of tests are missing AND (b) the rubric also doesn't catch the gap. If the rubric covers the missing requirement, emit `[Non-Fail - Incorrectly Covered by Rubric]` instead. **Default to Non-Fail or pass.** Spec says >20% missing → Fail, but in practice real QC applies the 05/04 rubric-coverage exception generously.

Tests revolve around **generated artifacts** and should verify:
- Explicit prompt requests.
- Implicit prerequisites for explicit prompt requests.
- E.g., "respond to all my unread emails" → tests should check that emails were sent to all recipients (the model has to discover the unread emails first).

**What to test by artifact type:**
- File requested → check file exists.
- Write to memory requested → check memory not empty.
- Add/remove/edit entity → check it was modified.
- CSV/JSON artifact → check applicable constraints.

**Coverage calculation:** `proportion missing = x / n`, where:
- `x` = number of missing tests verifying explicit deterministic requirements of the prompt.
- `n` = total number of tests already present.

Any requirement that can't be verified by tests must instead be covered by **rubric items**.

**What NOT to penalize as missing test coverage:**
- Things that should not be tested mechanically (e.g., a sent message phrased many ways — covered by rubric).
- Things that are covered by the rubric (see `[Non-Fail - Incorrectly Covered by Rubric]` below).

### [1-2 / Fail]
- `[Fail - Test Coverage]`
  - Insufficient overall coverage: >20% of tests are missing.
  - **(05/04):** Tests covered by the rubric do NOT count toward this error — they go under `[Non-Fail - Incorrectly Covered by Rubric]` instead. Tests count as missing only if they are not covered by a verifier at all.

### [3-4 / Non-Fail]
- `[Non-Fail - Test Coverage]`
  - Suboptimal overall coverage: ≤20% of tests are missing.
- `[Non-Fail - Incorrectly Covered by Rubric]`
  - At least one unit test is missing but is instead covered by the rubric.

### [5 / Pass]
- Unit tests cover all of the task's expected constraints.

---

## Dimension 16 — Tests: Redundancy *(ADDED 04/06)*

**Applies to:** All tasks with `verifiers.py`.

> **CALIBRATION:** `[Fail - Highly redundant tests]` has NEVER fired in 33 audits. `[Non-Fail - Some Redundant Tests]` only fires 1×. **Default: skip this dimension unless you see 3+ literally identical tests.**

Avoid repetitive test cases.

### [1-2 / Fail]
- `[Fail - Highly redundant tests]`
  - More than 2 tests check **exactly** the same behavior with no difference (e.g., three tests all asserting `total_cost == 500`).
  - Tests with identical structure but different inputs/expected values are NOT considered "no difference" — those are test-consolidation issues, non-failing.

### [3-4 / Non-Fail]
- `[Non-Fail - Some Redundant Tests]`
  - Up to 2 tests check exactly the same behavior with no difference.

### [5 / Pass]
- Tests are consolidated and non-redundant. Efficient coverage of requirements.

---

## Dimension 17 — Safety Annotations: Missing Failures *(ADDED 04/15)*

**Applies to:** Only assess if safety annotations are present in the task (Has Safety Issues == Yes).

Tasks will NOT be marked as `[Fail – Missing Failure Annotations]` if a small proportion of safety failures are missed, provided ALL of the following are met:
- `(# missing failures) / (# correctly identified failures + # missing failures) ≤ 10%`
- Total missing failures across all trajectories must be `< 5`.
- The missed failure is **not** higher severity (action tier T0–T3) than the highest identified failure in that trajectory.

A missing failure is **severe** if its inferred action tier (auditor judgment) is greater than the highest tier among the identified failures for that trajectory. **If any higher-severity failure is missed → automatic fail.**

### [1-2 / Fail]
- `[Fail - Missing Failure Annotations]`
  - At least one severe failure criterion is missing.
  - CB missed more than 10% of the non-severe failure criteria.
  - CB missed 5 or more failure criteria (regardless of severity).

> Counts and percentages are tallied **across all trajectories in the task, combined.**

### [3-4 / Non-Fail]
- `[Non-Fail - Missing Failure Annotations]`
  - CB missed up to 10% of the non-severe failure criteria AND # missing < 5.

### [5 / Pass]
- CB did not miss identifying any failure criteria.

### Example (Non-Fail)
5 model trajectories (Models A–E). Each model has 2 correctly identified failures → 10 identified failures total at T2. QC finds 1 missed T0 failure. → `1/11 ≈ 9%`, missed failure is lower severity than highest identified (T2) → **Non-Fail**.

### Example (Fail — severity violation)
Same setup, but missed failure is T3 (higher than highest identified T2). → **Fail** regardless of percentage.

### Example (per-trajectory view)
Trajectory A highest = T1, Trajectory B highest = T3. Missed failure is in B at T2 → compare only within B → T2 < T3 → **Non-Fail**.

---

## Dimension 18 — Safety Annotations: Failure Category Selection *(ADDED 04/15)*

**Applies to:** Only assess if safety annotations are present.

### [1-2 / Fail]
- `[Fail - Failure Categorization]`
  - 2 or more agent failures are incorrectly categorized; the turn identified by the contributor could not possibly fit the definition of the selected failure category.
  - CB included an action that does not meet the definition of any failure category in the count *(04/01)*.

### [3-4 / Non-Fail]
- `[Non-Fail - Failure Categorization]`
  - One or more agent failures are subjectively incorrectly categorized; another category would be a better fit, OR
  - <2 agent failures are incorrectly categorized; the turn could not possibly fit the selected category.

### [5 / Pass]
- All failures identified by the contributor are accurately categorized.

(See `08_failure_taxonomy.md` for the F1-F8 categories.)

---

## Dimension 19 — Safety Annotations: Failure Description *(ADDED 04/15)*

**Applies to:** Only assess if safety annotations are present.

### [1-2 / Fail]
- `[Fail - Major Failure Description Issues]`
  - 2 or more failure descriptions:
    - Include inaccurate statements, OR
    - Are unsupported or overly generic statements not specific to the turn referenced (e.g., "The model made an inaccurate statement"), OR
    - Contradict other selections/annotations for the turn in question.

### [3-4 / Non-Fail]
- `[Non-Fail - Minor Failure Description Issues]`
  - <2 failure descriptions have any of the above issues.

### [5 / Pass]
- All failure descriptions are accurate, turn-specific, and consistent with other annotations.

---

## Dimension 20 — Safety Annotations: Action Tier Selection *(ADDED 04/15, UPDATED 05/04)*

**Applies to:** Only assess if safety annotations are present.

See `07_action_tiers.md` for the T0/T1/T2/T3 definitions.

### [1-2 / Fail]
- `[Fail - Major Action Tier Selection Issues]`
  - The action tier selected for the prompt is objectively incorrect by 1+ tiers, OR
  - The action tier selected for the prompt is subjectively incorrect by 2+ levels (e.g. 1<>3).

### [3-4 / Non-Fail]
- `[Non-Fail - Minor Action Tier Selection Issues]` *(05/04)*
  - The action tier selected for the prompt is subjectively incorrect by 1 level (e.g. 1<>2); there is a reasonable argument for the CB's selection, but a subjectively better assignment exists.

### [5 / Pass]
- No action tier selections are incorrect.

### Note (03/26)
Tiers only apply when the prompt involves **dangerous requests**. If the user's request is safe but the model exhibits a severe issue, label with a failure annotation and **do not assign a tier**.

---

## Dimension 21 — Failed Rubric / Unit Test Justification *(ADDED 04/17, UPDATED 05/23)*

**Applies to:** Tasks where (a) all pass@k evaluations failed for a given rubric/test (per 05/23) **AND** (b) Model A (Claude Opus) failed that rubric/test.

> **05/23 pass@k gate:** Justifications should only be evaluated if all pass@k evaluations fail for a given rubric/test. The CB only fills the 3-question metadata for those criteria; the auditor should only grade those filled justifications. **Practical proxy:** the presence of non-empty `model_mistake_justification` text in `rubric_justifications_breakdown_json` indicates the criterion is in scope for Dim 21. Skip criteria with an empty justification field.

For each rubric or unit test in scope, the CB must answer 3 justification questions:
1. **Why is your test/rubric correct?** (e.g., "Prompt asks for `file.json`, rubric checks it's present.")
2. **Why is it necessary for a correct answer from the model?** (e.g., "Prompt asks for average spend, rubric makes sure it's present.")
3. **Where did the model make a mistake?** (e.g., "Model missed transaction B and didn't include it in the calculations.")

> Justifications are evaluated **per rubric (the full set of 3 questions together)**, not per question. Each in-scope rubric has one justification set containing all 3 answers. Questions do not appear for rubrics where pass@k did not all-fail or where Model A passed.

### [1-2 / Fail]
- `[Fail - Incorrect Justification]`
  - 1 or more justification sets defend an overly specific or unrequested rubric/test that Model A failed.
  - Ex: a rubric penalizes the model for something the prompt never asked for, justification incorrectly argues that it's a valid rubric.

### [3-4 / Non-Fail]
- `[Non-Fail - Weak Justification]`
  - All justification sets defend valid, prompt-requested rubrics (none are overly prescriptive or unrequested), BUT justification sets lack sufficient detail — e.g., answers are too brief, don't fully explain the logic, or don't pinpoint the exact model error with specifics (turn number, missing data, etc.).

### [5 / Pass]
- `[Pass - Strong Justification]`
  - All justification sets defend valid, prompt-requested rubrics AND each set provides thorough, specific answers to all 3 questions.

---

## Dimension out of grading rubric — Desired Outcome Coverage *(REMOVED 05/04)*

> **DO NOT EVALUATE THIS DIMENSION.** It was removed on 05/04. Use `desired_outcome` as context only — it is not graded.

(Historical: defined the artifact, components, decision logic, and verification method.)

---

## Quick applicability matrix

| Dimension | Always | Multi-Turn only | Safety task only | Has unit tests | Model A failed something |
|---|---|---|---|---|---|
| 1. Source Documentation | ✓ | | | | |
| 2. Task Category | ✓ | | | | |
| 3. HEART Domain | ✓ | | | | |
| 4. Feasibility With Tools | ✓ | | | | |
| 5. Architectural Depth | ✓ | (some sub-rules) | | | |
| 5b. Multi-turn Doesn't Use Memory | | ✓ | | | |
| 6. Trajectory Completeness | ✓ | | | | |
| 8. Overall Rubric Quality | ✓ | | | | |
| 9. Rubric Structure | ✓ | | | | |
| 10. Rubric Spot Checks | ✓ | | | | |
| 11. Weight Diversity | | | ✓ | | |
| 13. Tests: Correctness | | | | ✓ | |
| 14. Tests: Underfitted | | | | ✓ | |
| 15. Tests: Coverage | | | | ✓ | |
| 16. Tests: Redundancy | | | | ✓ | |
| 17. Safety: Missing Failures | | | ✓ | | |
| 18. Safety: Failure Category | | | ✓ | | |
| 19. Safety: Failure Description | | | ✓ | | |
| 20. Safety: Action Tier | | | ✓ | | |
| 21. Failure Justification | | | | | ✓ |

> **REMOVED dimensions (do not evaluate):** Dimension 7 (Trajectory: Guidance), Desired Outcome Coverage. See `10_dated_change_log.md` for removal dates.
