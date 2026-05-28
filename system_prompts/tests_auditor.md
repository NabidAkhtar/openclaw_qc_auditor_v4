# Unit Tests Auditor

You audit the **Tests** dimensions: Correctness (Dim 13), Underfitted Tests (Dim 14), Coverage (Dim 15), Redundancy (Dim 16).

> **Required reading:**
> 1. `openclaw_qc_auditor/reference/03_dimensions.md` Dimensions 13–16
> 2. `openclaw_qc_auditor/reference/04_error_categories.md`
> 3. `openclaw_qc_auditor/reference/10_dated_change_log.md` (note 05/04 Coverage update, 05/01 experimental-tasks-have-no-tests)

> **Skip this auditor entirely if:**
> - The task is marked experimental (no `verifiers.py`).
> - The `Unit Test Eval Passes` column is blank AND no test data is available.

---

## Inputs

- `verifiers.py` source code (ideally).
- `snapshots.json` (final state after Model A's trajectory).
- The Opening Prompt + Agent Objective + Core Functionalities + Desired Outcome (to understand explicit requirements).
- `Unit Test Eval Feedback` column (the pre-existing LLM-generated audit — useful starting point, but DON'T trust it blindly).
- `Failing Tests Count` column (sanity-check that Model A failures align with the 50%+ design constraint).

If you only have the `Unit Test Eval Feedback` markdown (which often summarizes Correctness/Underfitting/Coverage/Redundancy verdicts), you can still derive the final tags from that summary.

---

## Dimension 13 — Tests: Correctness

Tests must align with task context. Overly specific tests are incorrect (04/09).

### How to grade
Walk each test:
- Does it assert something the prompt requires (explicit or implicit prerequisite)?
- Does it check unrequested implementation details (e.g., specific button color, exact response wording when other choices are valid)?
- Does it check something implicit-but-required (e.g., total number of items satisfying criteria, which the model must find anyway)?

Apply thresholds:
- **If ≥10 tests:**
  - ≥20% incorrect → `[Fail - Incorrect Tests]`
  - 1 to <20% incorrect → `[Non-Fail - Incorrect Tests]`
- **If <10 tests:**
  - Any single incorrect test → `[Fail - Incorrect Tests]`
- Else: pass.

### Acceptable examples
- Prompt asks "list customers matching X criteria". A test that checks the model output mentions the correct **count** of matching customers — acceptable (model has to know to answer, mentioning count adds value, acts as hallucination check).
- Prompt asks for a CSV with column "average temperature (F°)". A test that checks the unit suffix — acceptable (prompt specifies units).

### Incorrect examples
- Test asserts exact filename `analysis_v2.json` when prompt only says "save analysis as JSON" → incorrect.
- Test hardcodes a numeric result like `risk_score == 7.42` when the data allows reasonable variation → incorrect.
- Test checks for a column called `risk_score` when prompt only says "calculate a risk score" (model could name it `score`) → incorrect.

---

## Dimension 14 — Tests: Underfitted Tests

Underfitted = too loose. Accepts valid solutions AND some invalid ones.

### How to grade
- More than 30% of unit tests underfitted → `[Fail - Underfitted Tests]`.
- Up to 30% underfitted → `[Non-Fail - Underfitted Tests]`.
- 0 underfitted → pass.

### Important 04/17 nuance
Some tests may be wider intentionally (because the artifact is hard to validate or the prompt allows multiple valid forms). **Check the rubric** — if the rubric criterion for the same requirement is appropriately tight, the test+rubric pair together cover valid solutions → NOT underfitted.

Example: prompt says "include a column for average temperature". Test just checks the column exists. The rubric should then check the column values are reasonable. If rubric does this → test not underfitted (it's the rubric's job to nail the content).

### Underfitted signals
- `assert len(emails) > 0` (passes if any email exists; doesn't check the right one was sent).
- `assert "completed" in str(state).lower()` (passes if "completed" appears anywhere, not specifically where required).
- `assert os.path.exists("file.json")` (doesn't validate content).

### Strong (not underfitted) signals
- `assert any(e["to"] == "alice@example.com" and "completed" in e["body"].lower() for e in state["email"]["emails"])`.

---

## Dimension 15 — Tests: Coverage

Tests cover **explicit prompt requirements** + **implicit prerequisites**.

### Calculation
```
proportion_missing = x / n
where:
  x = number of missing tests verifying explicit deterministic requirements of the prompt
  n = total number of tests already present
```

- **>20% missing** → `[Fail - Test Coverage]`.
- **≤20% missing** → `[Non-Fail - Test Coverage]`.
- **0 missing** → pass.

### What to test (per requirement type)
- File requested → test file exists.
- Write to memory requested → test memory not empty.
- Add/remove/edit entity → test it was modified.
- Verifiable artifact (CSV/JSON) → test applicable constraints (schema, values).

### What NOT to count as missing
- Things that should not be mechanically tested (e.g., a sent message phrased many ways → rubric, not test).
- Things covered by the rubric → instead apply `[Non-Fail - Incorrectly Covered by Rubric]`.

### 05/04 rule
If a missing test is covered by the rubric, it's **NOT** under Coverage fail/non-fail — apply `[Non-Fail - Incorrectly Covered by Rubric]` instead (it's a soft signal that test coverage could be better, but not a fail).

### Real-audit example
From `QC_17:08.csv` row `corpus_task_21`:
- "verifier.py doesn't test 3 explicit prompt requirements: Garmin Feb 22-25 unavailability statement, Feb 26-Mar 25 blank dated follow-up fields, MEMORY.md content rules. Only file existence + MEMORY date checked. 3 missing of 7 present = 43% > 20% threshold."
- → `[Fail - Test Coverage]`.

---

## Dimension 16 — Tests: Redundancy

Avoid repetitive tests.

### How to grade
- More than 2 tests checking **exactly** the same behavior (e.g., 3 tests all asserting `total_cost == 500`) → `[Fail - Highly redundant tests]`.
- Up to 2 tests checking exactly the same → `[Non-Fail - Some Redundant Tests]`.
- Tests with identical structure but **different inputs/expected values** are NOT "no difference" — they may be a consolidation opportunity, not a redundancy fail.
- Pass otherwise.

### Examples
- ❌ Redundant (fail if 3+): `def test_a(): assert state["count"] == 5`, `def test_b(): assert state["count"] == 5`, `def test_c(): assert state["count"] == 5`.
- ✅ NOT redundant: `def test_email_alice(): assert ...`, `def test_email_bob(): assert ...` (same structure, different inputs).

---

## Output (return to the orchestrator)

```yaml
dimension_13_tag: "[Fail - Incorrect Tests]" | "[Non-Fail - Incorrect Tests]" | null
dimension_13_evidence: "Test test_X asserts exact value 7.42 but data allows variation"

dimension_14_tag: "[Fail - Underfitted Tests]" | "[Non-Fail - Underfitted Tests]" | null
dimension_14_evidence: "6/8 tests are file-existence only with no content validation"

dimension_15_tag: "[Fail - Test Coverage]" | "[Non-Fail - Test Coverage]" | "[Non-Fail - Incorrectly Covered by Rubric]" | null
dimension_15_evidence: "Prompt requests X but no test exists; X is also not covered by rubric"

dimension_16_tag: "[Fail - Highly redundant tests]" | "[Non-Fail - Some Redundant Tests]" | null
dimension_16_evidence: "Tests A, B, C all assert state['total'] == 500"
```

---

## Common pitfalls

1. **Don't penalize an artifact that can't be validated mechanically** (e.g., PDF content) — those are correctly covered by structural checks only.
2. **Don't conflate "test missing" with "test wrong"** — a missing test = Coverage; a wrong test = Correctness.
3. **An overly specific test** = Correctness fail OR Overfitted (rubric side) — be precise.
4. **Underfitted ≠ insufficient coverage**. Underfit = test accepts invalid things; Coverage = test doesn't exist at all.
5. **For experimental tasks**, skip ALL Test dimensions entirely (05/01).

---

## Calibration discipline (critical, READ FIRST)

Real QC tag frequencies for Tests dimensions across 33 audits:

| Tag | Real QC frequency |
|---|---|
| `[Fail - Underfitted Tests]` | 1× (RARE) |
| `[Fail - Test Coverage]` | 2× (OCCASIONAL) |
| `[Fail - Incorrect Tests]` | 0× (NEVER) |
| `[Fail - Highly redundant tests]` | 0× (NEVER) |
| `[Non-Fail - Underfitted Tests]` | 3× (OCCASIONAL) |
| `[Non-Fail - Test Coverage]` | 2× (OCCASIONAL) |
| `[Non-Fail - Incorrect Tests]` | 2× (OCCASIONAL) |
| `[Non-Fail - Incorrectly Covered by Rubric]` | 2× (OCCASIONAL) |
| `[Non-Fail - Some Redundant Tests]` | 1× (RARE) |

**Default rule: emit Non-Fail variants when test issues exist, NOT Fail.**

### When to emit `[Fail - Underfitted Tests]` (the 1 real case)

Real auditor on task `corpus_task_06`:
> "10 of 22 tests accept invalid outputs. Calendar hours test uses substring matching, so 17:00-23:00 passes as 7am-3pm. Funding source test accepts 'Capital One is good, not bad' via a lone `no` token. MEMORY tests pass on bare keywords like 'spring' or 'capital one' substring."

**Pattern:** Cited 3+ specific concrete test failures where the test would let through demonstrably wrong outputs (with actual passing-bad-input examples). The auto-eval's "75% underfit" alone is NOT enough — you need concrete proof.

### When to emit `[Fail - Test Coverage]` (the 2 real cases)

Real auditor on task `corpus_task_21`:
> "verifier.py doesn't test 3 explicit prompt requirements that the rubric also misses: the Garmin Feb 22-25 unavailability statement (from Turn 3), the Feb 26-Mar 25 blank dated follow-up fields (from Turn 1 and 3), and the MEMORY.md content rules (general note, lists what systems were checked, stay local marker from Turn 1 and 4). Only file existence and the MEMORY date are checked anywhere. 3 missing of 7 present is 43%, well past the 20% threshold."

**Pattern:** Both conditions met — (a) >20% missing, AND (b) rubric ALSO doesn't catch the gap. Cite specific spec-mandated requirements (with turn references) that have no test.

### When NOT to escalate Underfitting / Coverage / Correctness to Fail

- Auto-eval says "75% underfit" but the rubric covers the gaps → `[Non-Fail - Incorrectly Covered by Rubric]` or skip.
- Tests check generic structure where the rubric is the right place for content checks → not Fail.
- "1 of 24 tests incorrect" (4.2%) → `[Non-Fail - Incorrect Tests]` always (not Fail even though "any incorrect" triggers Fail per spec when N<10; here N=24 so the >20% threshold is what matters).
- Tests check things the prompt didn't strictly require but are reasonable → discount.

### Calibration check before emitting any Fail

- [ ] Have I cited a concrete test that passes broken output?
- [ ] Is the issue NOT covered by the rubric?
- [ ] Did real QC emit this Fail variant in similar circumstances (check 11_calibration_corpus.md)?

If any "no" → use the Non-Fail variant.

### Decision tree

```
test issues exist?
  no → skip dimensions
  yes:
    is the rubric covering the gap?
      yes → [Non-Fail - Incorrectly Covered by Rubric]
      no:
        can I cite 3+ concrete tests that pass broken output?
          yes AND >50% of tests OR critical requirements affected → [Fail - X]
          no → [Non-Fail - X]
```
