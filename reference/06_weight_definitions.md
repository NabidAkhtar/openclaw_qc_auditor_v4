# Criteria Weight Definitions

Source: `QC_spec_doc.pdf` Appendix → "Criteria Weight Definitions" (Updated 04/15). Used for:
- Detecting **Incorrect Weights — Major** (off by 2 buckets) → moderate issue.
- Detecting **Incorrect Weights — Minor** (off by 1 bucket) → minor issue.
- Detecting **Invalid Weights** (outside the set) → automatic fail (`[Fail - Invalid Weights]`).

Allowed weight set: **`{-5, -3, -1, +1, +3, +5}`**. Any other value is invalid.

---

## +5 — Critically Important

**Definition (Agent-Building Context):** A criterion that determines whether the **primary deliverable** is functionally correct, complete, and usable for its intended purpose. Failure means the task objective is not meaningfully achieved.

**Heuristic (04/15):** If this fails → the user **cannot rely on or use** the output (or part of it) at all.

### Applies when
- The main artifact is missing or fundamentally incorrect.
- The structure or content prevents intended use.
- A key requirement (value, calculation, etc.) is inaccurate.
- A core requirement explicitly defining task success is violated.
- CSV missing required sections entirely → unusable.
- Financial totals are wrong → breaks core purpose of summary.
- Output format is wrong (e.g., JSON instead of required CSV).
- Required file not produced at all.

### Does NOT apply when
- The artifact is still usable despite minor inconsistencies.
- The check is a spot validation rather than holistic correctness.
- One or more column names slightly incorrect but data still interpretable.
- Minor schema mismatches that don't prevent use.

### Typical examples
- Fails to complete the task.
- Uses the wrong system or misses required tools.
- Produces an incorrect or unverifiable final artifact.
- Violates a hard constraint (e.g., books a flight when told not to).

---

## +3 — Important

**Definition:** A criterion that reflects core agent competence and strong execution, but is not strictly required for minimum validity. Failure significantly weakens quality or reliability but does not invalidate the outcome.

### Applies when
- Key logic is partially incorrect.
- Important sections are incomplete or weak.
- Errors require user correction but do not block usage.

### Examples
- Ranking logic is flawed but results are still usable.
- Some financial calculations are inconsistent but totals exist.
- Missing a non-critical but meaningful section of the output.

### Typical examples
- Suboptimal ranking logic.
- Weak handling of friction.
- Missing cross-source verification.
- Inefficient modular structure.

---

## +1 — Slightly Important

**Definition:** A criterion that improves polish, robustness, or reasoning clarity but does not substantially change task correctness.

**Heuristic (04/15):** If this fails → the output is still usable with **minimal friction**.

### Applies when
- Checking individual fields, headers, or values.
- Minor inconsistencies within a correct structure.
- Granular validation of parts of the output.
- Column name mismatches (e.g., `cost_total` vs `total_cost`).
- One or two incorrect cell values in a large table.
- Slight formatting inconsistencies.
- Missing optional metadata fields.

### Does NOT apply when
- Entire column missing that prevents interpretation.
- Widespread incorrect values across the dataset.
- Errors that break downstream usage.

### Typical examples
- Slightly messy formatting.
- Minor inefficiency.
- Lack of explanation depth.
- Not asking a non-critical clarification question.

---

## -1 — Slightly Detrimental

**Definition:** A minor architectural or behavioral flaw that slightly weakens execution quality but does not compromise task validity.

### Typical examples
- Extra unnecessary tool call.
- Redundant reasoning step.
- Overly verbose internal planning.
- Small formatting inconsistency.

---

## -3 — Detrimental

**Definition:** A significant execution issue that materially degrades reliability, reasoning quality, or tool correctness — but does not completely invalidate the result.

### Typical examples
- Incorrect intermediate reasoning but corrected later.
- Poor friction handling requiring heavy steering.
- Tool misuse followed by correction.
- Logical gaps in ranking explanation.

---

## -5 — Critically Detrimental

**Definition:** An error so severe that it breaks core agent reliability, violates constraints, or fundamentally invalidates the result. Includes architectural collapse, safety violations, or hallucinated outputs.

### Typical examples
- Hallucinating tool outputs.
- Taking irreversible actions without confirmation.
- Producing fabricated data not returned by tools.
- Failing to complete the task.
- Ignoring mandatory constraints.

---

## Auditing weight correctness

For each criterion in the rubric:
1. Read the criterion text + what it actually checks.
2. Identify which weight bucket best matches its severity (using the definitions above).
3. Compare against the CB's selected weight.
4. Diff:
   - 0 buckets off → correct.
   - 1 bucket off → **Minor issue** (e.g., +3 chosen when +1 fits, or +1 chosen when +3 fits).
   - 2+ buckets off → **Major issue** (e.g., +5 chosen when +1 fits, or +3 chosen when -1 fits — both are 2 buckets apart on the 6-position scale: -5, -3, -1, +1, +3, +5).

> The scale has 6 positions. "Off by one" means moving exactly one position (e.g., +1 → +3, or -3 → -1). "Off by two+" means moving two or more positions.

### Polarity rule
A positive-weight criterion measuring a desirable behavior should never be weighted negative (and vice-versa). Polarity flips are typically caught under **Incorrect Criteria** or **Overlapping/Redundant Criteria** rather than weight error.

---

## Evaluation Target reference

Each rubric also has a "target":
1. **User Facing Message** — any output produced by the agent visible to the end user (final artifacts, chat messages, generated files/exports).
2. **State Change** — internal updates/transitions to working memory, environment, or intermediate system state during execution, not user-facing.

Auditors don't grade target correctness as a separate dimension, but a criterion targeted at the wrong layer (e.g., checking user-facing output when the rubric clearly targets a state change) is a flag under **Incorrect Criteria** or **Miscategorized Criteria**.
