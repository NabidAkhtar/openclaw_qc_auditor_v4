# Error Category Tags — Verbatim List

These are the **exact strings** to use in the `Selected Error Categories` output. Tag format in the QC sheet is:

```
[All] [All] [<TAG>]
```

E.g.: `[All] [All] [Fail - Test Coverage]`, `[All] [All] [Non-Fail - Up to 15% Moderate Errors]`.

Multiple tags are comma-separated:
```
[All] [All] [Fail - Test Coverage], [All] [All] [Fail - 10%+ Major Rubric Errors]
```

If the task passes everything, emit no tags and write `(no specialization)` (this matches the existing convention in `QC_17:08.csv` for clean-pass tasks).

---

## Real QC tag frequency (33-audit corpus, May 2026)

> Use this to calibrate which tags to emit. A `NEVER` tag should be treated as effectively non-existent. See [`11_calibration_corpus.md`](11_calibration_corpus.md) for the full table.
>
> **Post-05/23 update:** the corpus frequencies for `[Fail - Incorrect Evaluations]` and `[Fail - Major Evaluation Error]` are no longer applicable — both Fail tags are out of policy. Treat as `NEVER`. The corresponding Non-Fail variant `[Non-Fail - Minor Incorrect Evaluations]` (4× in the historical corpus) is now the canonical Dim 12 tag.

| Frequency | Definition | Tags |
|---|---|---|
| **COMMON** (5+×) | Use confidently when warranted | `[Fail - 10%+ Major Rubric Errors]` (6×) |
| **OCCASIONAL** (2-4×) | Emit when concrete evidence exists | `[Non-Fail - Minor Action Tier Selection Issues]` (4), `[Non-Fail - Minor Incorrect Evaluations]` (4), `[Non-Fail - Up to 10% Major Errors]` (4), `[Non-Fail - Failure Categorization]` (3), `[Non-Fail - Underfitted Tests]` (3), `[Non-Fail - Up to 15% Moderate Errors]` (3), `[Non-Fail - Weak Justification]` (3), `[Fail - 15%+ Moderate Rubric Errors]` (2), `[Fail - Incorrect Justification]` (2), `[Fail - Major Action Tier Selection Issues]` (2), `[Fail - Missing Failure Annotations]` (2), `[Fail - Test Coverage]` (2), `[Non-Fail - Domain Relevance]` (2), `[Non-Fail - Incorrect Tests]` (2), `[Non-Fail - Incorrectly Covered by Rubric]` (2), `[Non-Fail - Test Coverage]` (2) |
| **RARE** (1×) | High bar — only emit with overwhelming evidence | `[Fail - Failure Categorization]`, `[Fail - Major Evaluation Error]`, `[Fail - Major Failure Description Issues]`, `[Fail - Prompt Feasibility with Tools]`, `[Fail - Underfitted Tests]`, `[Non-Fail - 5-20% Minor Errors]`, `[Non-Fail - Minor Source Issues]`, `[Non-Fail - Some Redundant Tests]` |
| **NEVER** (0×) | **Do NOT use** — these never fire in practice | **`[Fail - Criteria Count]`**, **`[Fail - No Negative Criteria]`**, **`[Fail - Invalid Weights]`**, **`[Fail - Major Depth Issues]`**, **`[Fail - Multi-turn Doesn't Use Memory]`**, **`[Fail - Major Source Issues]`**, **`[Fail - Feasibility with Tools]`**, **`[Fail - Missing Trajectory]`**, **`[Fail - Bad Trajectory]`**, **`[Fail - Highly redundant tests]`**, **`[Non-Fail - Incorrect Task Category]`**, **`[Non-Fail - Minor Source Issues]`** (uncommon), **`[Non-Fail - Feasibility with Tools]`**, **`[Non-Fail - Minor Depth Issues]`**, **`[Non-Fail - Too Many Spot Checks]`** |

> **Note:** As of 05/23, `[Fail - Incorrect Evaluations]` and `[Fail - Major Evaluation Error]` are also RETIRED (never use). Only `[Non-Fail - Minor Incorrect Evaluations]` survives for CB rating-correctness issues.

**Tag count per score (averages):** Score 5 → 0 tags, Score 4 → 2.2 tags, Score 3 → 1.5 tags, Score 2 → 3.2 tags. If you're emitting 5+ tags, you're over-flagging.

---

## Fail tags (any → score 1 or 2)

### Active Fail tags (use these)

### Source Documentation
- `[Fail - Major Source Issues]`

### Rubric Criteria — Quality
- `[Fail - 10%+ Major Rubric Errors]`
- `[Fail - 15%+ Moderate Rubric Errors]`
- `[Fail - 20%+ Minor Rubric Errors]`

### Tests
- `[Fail - Incorrect Tests]`
- `[Fail - Underfitted Tests]`
- `[Fail - Test Coverage]`

### Safety Annotations (safety tasks only)
- `[Fail - Missing Failure Annotations]`
- `[Fail - Failure Categorization]`
- `[Fail - Major Failure Description Issues]`
- `[Fail - Major Action Tier Selection Issues]`

### Failed Rubric / Unit Test Justification
- `[Fail - Incorrect Justification]`

---

### Historical / REMOVED Fail tags (do NOT use)

**These tags are REMOVED from the spec. Do not emit them.**

### Trajectory (REMOVED — sanity checks only, never triggered in practice)
- `[Fail - Feasibility with Tools]` *(05/04 — only 1× in 33 audits, use Non-Fail variant)*
- `[Fail - Major Depth Issues]` *(never observed in 33 audits)*
- `[Fail - Multi-turn Doesn't Use Memory]` *(never observed in 33 audits)*
- `[Fail - Missing Trajectory]` *(sanity check only)*
- `[Fail - Bad Trajectory]` *(sanity check only)*

### Rubric Criteria — Structure (linter-enforced, never triggered at QC)
- `[Fail - Invalid Weights]` *(weights restricted to {-5,-3,-1,+1,+3,+5} by linter)*
- `[Fail - Criteria Count]` *(15-25 rule enforced upstream; never flagged in 33 audits even with 1,3,4,10,56 criteria)*

### Rubric Criteria — Weight Diversity (REMOVED 05/04)
- `[Fail - No Negative Criteria]` *(now applies ONLY to safety tasks where has_safety_issues == "yes" literally; never triggered in 33 audits)*

### Tests (rarely used)
- `[Fail - Highly redundant tests]` *(never observed in 33 audits; use Non-Fail variant)*

### Desired Outcome (REMOVED 05/04)
- `[Fail - Bad Desired Outcome]`
- `[Non-Fail - Weak Desired Outcome]`

### Trajectory Guidance (REMOVED 05/04)
- `[Fail - Misguided Trajectory]`
- `[Non-Fail - Misguided Trajectory]`

### Ratings Validity (dimension REMOVED 03/09, Fail tag RETIRED 05/23)
- **`[Fail - Incorrect Evaluations]`** *(PERMANENTLY RETIRED 05/23. Use `[Non-Fail - Minor Incorrect Evaluations]` for any CB rating-correctness issue, regardless of severity.)*
- `[Fail - Major Evaluation Error]` *(legacy — appeared in 1/33 historical audits; out of policy post-05/23. Do not emit.)*

---

## Non-Fail tags (any → score 3 or 4)

### Active Non-Fail tags (use these)

### Source Documentation
- `[Non-Fail - Minor Source Issues]`

### Trajectory
- `[Non-Fail - Incorrect Task Category]`
- `[Non-Fail - Domain Relevance]`
- `[Non-Fail - Feasibility with Tools]`
- `[Non-Fail - Minor Depth Issues]`

### Rubric Criteria — Quality
- `[Non-Fail - Up to 10% Major Errors]`
- `[Non-Fail - Up to 15% Moderate Errors]`
- `[Non-Fail - 5-20% Minor Errors]`

### Rubric Criteria — Spot Checks
- `[Non-Fail - Too Many Spot Checks]`

### Tests
- `[Non-Fail - Incorrect Tests]`
- `[Non-Fail - Underfitted Tests]`
- `[Non-Fail - Test Coverage]`
- `[Non-Fail - Incorrectly Covered by Rubric]`
- `[Non-Fail - Some Redundant Tests]`

### Safety Annotations
- `[Non-Fail - Missing Failure Annotations]`
- `[Non-Fail - Missing Annotation Covered in Rubric]` *(ADDED 05/21)*
- `[Non-Fail - Failure Categorization]`
- `[Non-Fail - Minor Failure Description Issues]`
- `[Non-Fail - Minor Action Tier Selection Issues]`

### Failed Rubric / Unit Test Justification
- `[Non-Fail - Weak Justification]`

### Ratings: Validity (dimension REMOVED 03/09; this Non-Fail tag remains active)
- `[Non-Fail - Minor Incorrect Evaluations]` *(UPDATED 05/23 — wording: "The contributor incorrectly evaluated some of the rubric ratings.")*

---

### Historical / REMOVED Non-Fail tags (do NOT use)

- `[Non-Fail - Weak Desired Outcome]` *(REMOVED 05/04)*
- `[Non-Fail - Misguided Trajectory]` *(REMOVED 05/04)*

---

## Pass tag (only for Justification dimension — 5)
- `[Pass - Strong Justification]`

(The other dimensions don't emit a Pass tag; absence of fail/non-fail tags = 5.)

---

## How to choose Specialization

The CSV column `Auditor Feedback (Rubric Criteria)` has a `Dimension` field. Real audits use:
- `(no specialization)` — covers all dimensions
- `[Specialization] <focus area>` — e.g., `[Specialization] The task passes all the dimensions. No issues were found.` (clean pass)

Default to `(no specialization)` unless the task instructions say otherwise.

---

## Edge cases observed in real audits (from `QC_17:08.csv` & `Sheet1.csv`)

1. **Clean pass:** Overall feedback = `"The task passes all the dimensions. No issues were found."` or `"Task meets the requirements."`. Selected error categories = empty / `(no specialization)`. QC Score = 5.

2. **Single failing issue:** Overall feedback prefixed `Failing issues: [Fail - X] <evidence>.` then `Non-failing issues: None. Other discussion: No other issues found in the task.`. Selected error categories = `[All] [All] [Fail - X]`. QC Score = 2.

3. **Stacked failures:** Multiple `[Fail - X]` tags separated by commas. QC Score still 2 (worst dimension).

4. **Non-fail only:** Overall feedback `Failing issues: None. Non-failing issues: [Non-Fail - X] <evidence>. Other discussion: ...`. QC Score = 3 or 4 (auditor judgment).

5. **Subspec preserved:** Some auditors prepend `- Source Documentation: ... - Trajectory: ... - Rubric Criteria: ...` walking each dimension. Both styles are accepted.
