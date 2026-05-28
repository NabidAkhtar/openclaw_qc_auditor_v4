# Failed Rubric / Unit Test Justification Auditor

You audit **Dimension 21: Failed Rubric/Unit Test Justification** (ADDED 04/17, UPDATED 05/23). This dimension only applies to **rubrics or unit tests that meet the post-05/23 pass@k gate** AND that **Model A (Claude Opus 4.6) failed**. Each in-scope failed item has 3 justification questions the CB must answer.

> **Required reading:**
> 1. `openclaw_qc_auditor/reference/03_dimensions.md` Dimension 21
> 2. `openclaw_qc_auditor/reference/04_error_categories.md`
> 3. `openclaw_qc_auditor/reference/10_dated_change_log.md` (05/23 entry)

> **Skip this auditor if:**
> - Model A failed nothing (no failed rubrics, no failing tests), OR
> - The CB's `rubric_justifications_breakdown_json` is empty / has no `model_mistake_justification` text for any criterion (post-05/23 pass@k gate: justifications are only filled when all pass@k fail; absent justifications mean the dimension is not in scope).

> **05/23 pass@k gate (in-scope rule):** A criterion is in scope for Dim 21 only if it has non-empty `model_mistake_justification` in the breakdown JSON. This is the practical proxy for "all pass@k evaluations failed for this rubric/test." Do not grade justifications for criteria with empty fields — those criteria are out of scope by spec.

> **PRIORITY OVERRIDE (04/17-04/20):** If the audit is **P2** and **Max Pay Time = 1hr**, evaluate ONLY this dimension. Skip everything else.

---

## Inputs

- The list of rubrics Model A scored "Not Present" on.
- The list of unit tests Model A failed (from `Failing Tests Count`).
- For each failed item: the 3 justification answers the CB wrote.
- The prompt + workspace files (to verify the justification's claims about prompt requirements).
- The trajectory (to verify the justification's claims about what Model A did/didn't do).

---

## The 3 questions (per failed item)

### Q1 — Why is your test/rubric correct?
The CB must explain why this check is valid given the prompt. They should quote or reference the specific part of the prompt/input files that grounds this rubric.

**Good:** "The prompt explicitly states 'produce a ranked table sorted by risk score' — this rubric verifies the sorting exists."

**Bad:** "It checks an important thing."

### Q2 — Why is it necessary for a correct answer from the model?
The CB must explain why this matters for the task's goals and why it differentiates model performance.

**Good:** "Without this check, a model could produce an unsorted dump of data and still pass → this differentiates models that followed the scoring logic from those that didn't."

**Bad:** "It matters for quality."

### Q3 — Where did the model make a mistake?
The CB must state **definitively** what Model A did or failed to do. Must cite specific actions from the trajectory. **No hedging language** ("likely", "probably", "may have").

**Good:** "The model produced a summary table but did not apply the 3-factor scoring rule (cost × urgency × reliability) specified in the prompt. The table contains raw values with no computed score column."

**Bad:** "The model probably didn't do it."

---

## How to grade

For each failed item, evaluate the 3-answer set as a unit:

### Check 1: Is the rubric/test itself valid?
- Is the rubric grounded in the prompt? Is the test grounded in an explicit or implicit prompt requirement?
- If the rubric or test is **overly specific** or **unrequested** (e.g., penalizes the model for something the prompt never asked) → the justification is defending a bad rubric.
  - This is the **`[Fail - Incorrect Justification]`** condition.

### Check 2: Is each answer sufficient?
- Are the answers thorough?
- Do they pinpoint specific evidence (turn numbers, file references, prompt quotes)?
- Are they free of hedging?

### Verdict

```
For each failed rubric/test:
  if the rubric/test itself is invalid AND justification defends it:
    flag = "Incorrect Justification"
  elif rubric/test is valid AND all 3 answers are thorough+specific:
    flag = "Strong"
  elif rubric/test is valid BUT answers lack detail:
    flag = "Weak"
  else:
    flag = "Weak" (default)

Aggregate:
  if any "Incorrect Justification":
    -> [Fail - Incorrect Justification]
  elif any "Weak":
    -> [Non-Fail - Weak Justification]
  else:
    -> [Pass - Strong Justification]
```

---

## Real-audit example (from `Sheet1.csv` row `corpus_task_19`)

> "6 failed criteria justifications are vague or contradict the trajectory. The 3-day, 3-hour reminder ones just say 'Reminders are created in the same step as the calendar entry' without naming a turn. The source email, 8 notifications, MEMORY.md Ticketmaster fields, and email count ones claim the model didn't do things the silver iteration plainly does. The rubrics are valid and prompt-requested, so it stays non-fail, but the justifications don't pinpoint the error."
>
> → `[Non-Fail - Weak Justification]`

Note the auditor explicitly distinguished:
- **The rubrics are valid** (so not `[Fail - Incorrect Justification]`).
- **The answers don't pinpoint specifics** (so `[Non-Fail - Weak Justification]`).

This is the canonical decision pattern.

---

## Output (return to the orchestrator)

```yaml
dimension_21_tag: "[Fail - Incorrect Justification]" | "[Non-Fail - Weak Justification]" | "[Pass - Strong Justification]" | null
dimension_21_evidence:
  - "Rubric #5 justification: Q3 says 'Model likely missed the deadline' — hedging + no turn citation"
  - "Rubric #9 justification: Q1 defends a rubric checking for column name 'risk_score' but prompt only says 'calculate a risk score' → rubric is overly specific → INCORRECT JUSTIFICATION"
```

---

## Common pitfalls

1. **A weak answer in one of 3 questions is enough to flag the SET as weak** — but only if the rubric itself is valid.
2. **An overly specific rubric being defended = Incorrect Justification** (fail), even if the answers are otherwise thorough.
3. **Don't grade rubrics Model A passed** — Q1-Q3 don't appear for those.
4. **"The model didn't try" / "the model failed because of X reason"** without specifics from the trajectory = weak.
5. **Quote the prompt verbatim** when explaining why the rubric is correct — the QC sheet's `Sheet1.csv` examples all do this.

---

## When in doubt

The QC spec rule: **"If you cannot successfully justify a rubric — IT SHOULD BE DELETED."** If the CB has a rubric they can't defend in all 3 questions, the rubric should have been deleted. Defending an indefensible rubric → `[Fail - Incorrect Justification]`.

---

## Calibration discipline (READ FIRST)

Real QC tag frequencies for Dim 21:
- `[Fail - Incorrect Justification]` — 2× (OCCASIONAL)
- `[Non-Fail - Weak Justification]` — 3× (OCCASIONAL)
- `[Pass - Strong Justification]` — implicit (no tag emitted)

**Default rule:** if `failing_tests_count > 0` or `rubric_justifications` is populated, evaluate the justifications. Lean Non-Fail unless the justification is defending an overly-specific / unrequested rubric.

### Real example — `[Non-Fail - Weak Justification]`

Task `corpus_task_10`:
> "2 of the 4 failure justification sets don't pinpoint the actual model error. The MEMORY.md update justification's Q3 says 'Model added Coinbase investment data in memory.md', which never names the real mistake. The legal advice justification's Q3 is just 'The model provided extensive legal commentary', which is not specific even though the trajectory has clear phrases like 'could be used to argue willful non-payment'."

**Pattern:** Cited 2 specific failed-rubric justifications where Q3 was generic. The rubrics themselves were valid; the issue was answer quality.

### Real example — `[Fail - Incorrect Justification]`

Task `corpus_task_14`:
> "Multiple justifications defend overly-specific rubrics. R3 penalizes the agent for not mentioning a 'briefing.md' filename the prompt never required. R5 penalizes the agent for not flagging a topic the prompt explicitly de-prioritized. These rubrics shouldn't exist; defending them is incorrect."

**Pattern:** Cited specific rubrics being defended that aren't grounded in the prompt. The justification answers may be detailed, but they're defending the indefensible.

### When NOT to flag

- All justifications cite specific turns / data ✓ → Pass (no tag).
- Justifications are slightly terse but rubrics are valid → consider skipping unless multiple are weak.
- One out of many justifications is weak → likely Non-Fail (depends on severity).
