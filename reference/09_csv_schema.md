# Input CSV Schema

The audit input is one row from `QC Reads before onsite - Sheet1.csv` (or the same schema). Row 1 is a section banner ("Task Overview", "Content & Prompts", etc.), row 2 is the actual header, rows 3+ are task data.

## Section groups (row 1)
- **Task Overview** (cols 1–6): identifiers, scenario type, universe.
- **Content & Prompts** (cols 7–11): the design content.
- **Evaluation Results** (cols 12–28): pre-existing automated/manual evaluator outputs.
- **Quality Assessment** (cols 29–32): execution + rubrics + qms.
- **QC Validation** (cols 33+): QC scores, auditor info, feedback, and the **OUTPUT** fields the auditor writes.

---

## Column-by-column

### Task Overview
| # | Column | Meaning |
|---|---|---|
| 1 | `Task Id` | Unique task identifier (24-char hex). |
| 2 | `Final Score` | The current final score (1-5, "Invalidated", or blank). Auditor sets this. |
| 3 | `Attempt` | The attempt ID (24-char hex). |
| 4 | `Scenario Type` | One of the 7 safety target domains (Borderline or Sensitive Requests, Ambiguous Requests, Private Data Usage, High-Stakes Actions, etc.) OR a non-safety category. |
| 5 | `Assigned Universe` | The persona/world (e.g. `👟 stride`, `🏠 property`, `👤 manuel romero`). |
| 6 | `Requires Memory` | "I acknowledge this" if the task requires MEMORY.md, blank otherwise. |

### Content & Prompts
| # | Column | Meaning |
|---|---|---|
| 7 | `Review Decision` | Reviewer's decision: `accept`, `accept_with_fixes`, `reject`, or blank. |
| 8 | `Agent Objective` | The CB-written agent objective (persona, problem, context, artifact). |
| 9 | `Core Functionalities` | The CB-written list of operational capabilities the agent must demonstrate. |
| 10 | `Desired Outcome` | The CB-written verifiable end-state. *(Not graded post-05/04, but read as context.)* |
| 11 | `Opening Prompt` | The first user turn that kicks off the trajectory. |

### Evaluation Results
| # | Column | Meaning |
|---|---|---|
| 12 | `Main Request Summary` | LLM-generated summary of what the user asked. |
| 13 | `Trajectory Validator Passes` | yes / no — whether automated trajectory validation passed. |
| 14 | `Trajectory Validator Feedback` | Free-text validator feedback (often includes a 1-5 score). |
| 15 | `Has Safety Issues` | yes / no — whether the task is a Safety task. **Drives Dimensions 11, 17-20.** |
| 16 | `Safety Failure Recognition` | CB's identification of safety failures. |
| 17 | `Safety Tier Annotation` | CB's selected action tier (t0 / t1 / t2 / t3, or N/A). |
| 18 | `Safety Tier Justification` | CB's justification for the tier. |
| 19 | `Unit Test Eval Passes` | yes / no — whether unit tests pass on Model A's trajectory. |
| 20 | `Unit Test Eval Feedback` | Markdown report on test suite quality (correctness / underfitting / coverage / redundancy). |
| 21 | `Failing Tests Count` | Number of failing tests on Model A. |
| 22 | `Rubric Evaluator Passes` | yes / no — whether rubric pass count meets requirements. |
| 23 | `Rubric Evaluator Feedback` | Markdown report on rubric quality. |
| 24 | `Final Rubric Criteria Count` | Total criteria in the rubric. **Must be 15-25 per Dimension 9.** |
| 25 | `Rubric Total Weight Positive` | Sum of positive weights. |
| 26 | `Rubric Total Weight Negative` | Sum of negative weights. (For safety tasks, must be ≠ 0.) |
| 27 | `Workspace Verification Passed` | True / False — workspace zip uploaded correctly. |
| 28 | `Idea Approved` | yes / no / blank — whether the task idea was approved upfront. |
| 29 | `Idea Feedback` | Approval feedback (often a 1-5 score with explanation). |

### Quality Assessment
| # | Column | Meaning |
|---|---|---|
| 30 | `Quality Execution` | LLM-generated execution audit (often a 1-5 score with explanation). |
| 31 | `Quality Selection Justification` | Justification for model selection / best-model designation. |
| 32 | `Quality Rubrics` | Detailed pre-audit of rubric quality (Atomicity / Self-Containedness / Completeness / Rounding / Weight Annotation / Classification / Redundancy with per-criterion findings). |
| 33 | `Quality Overall Qms` | Numeric QMS score (often 0 if no issue). |

### QC Validation (input + OUTPUT fields)
| # | Column | Meaning |
|---|---|---|
| 34 | `Qc Score` | **AUDIT OUTPUT.** Numeric 1-5 score the auditor assigns. |
| 35 | `Last Attempter` | Worker ID who last attempted the task. |
| 36 | `Auditor` | The QC auditor's worker ID. |
| 37 | `Project Team Verdict` | Project team's agreement: `Agree` / `Disagree` / blank. |
| 38 | `Project Team Proposed Score` | If they disagree, their proposed score. |
| 39 | `Qc Validation` | `Approve` / `Reject` / blank. |
| 40 | `Final Score` | The accepted final score (after project team review). |
| 41 | `Audit Time` | Timestamp of audit (`M/DD/YY, HH:MM AM/PM`). |
| 42 | `Overall Auditor Feedback` | **AUDIT OUTPUT.** Narrative: `Failing issues: ... Non-failing issues: ... Other discussion: ...`. |
| 43 | `Selected Error Categories` | **AUDIT OUTPUT.** Comma-separated `[All] [All] [<tag>]`. |
| 44 | `Auditor Feedback (Rubric Criteria)` | **AUDIT OUTPUT.** Optional dimension-level annotation (often `(no specialization)` or `[Specialization] ...`). |
| 45 | `Project Team Feedback` | Project team's reasoning if they disagreed. |
| 46 | `Qc Feedback` | Any rebuttal / response to QC. |

---

## Audit OUTPUT fields (the 4 fields the auditor MUST populate)

1. **`Qc Score`** — integer 1-5 (or "Invalidated" if the task should be removed entirely).
2. **`Overall Auditor Feedback`** — narrative report following the template in `templates/audit_report.md`.
3. **`Selected Error Categories`** — comma-separated tags. `(no specialization)` if clean pass.
4. **`Auditor Feedback (Rubric Criteria)`** — usually `(no specialization)` or `[Specialization] ...`.

Plus optional:
- **`Audit Time`** — timestamp.

---

## How to load a row from the CSV

The header is on **row 2** (zero-indexed: index 1). Row 1 is the section banner — skip it.

```python
import pandas as pd
df = pd.read_csv(csv_path, header=1)        # row 2 (1-indexed) is the real header
row = df[df["Task Id"] == task_id].iloc[0]   # or df.iloc[N] for row index
```

Some columns may be blank for any given row. Always check for `pd.isna()` before using.

---

## Auxiliary inputs (when present)

If the user also provides:
- A full `transformed.json` / `cds_outpute resposne.json` blob → use it to read `model_trajectories`, `final_rubric_criteria`, `failing_tests`, `rubric_justifications_breakdown` (deeper fidelity than the CSV's pre-flattened summaries).
- A `verifiers.py` file → read it for the Tests dimensions.
- A `snapshots.json` file → read it to validate test pass/fail claims.
- A workspace zip → access the policy.md, attached images, and other task inputs.

These are optional. Without them, audit using whatever the CSV row provides + flag any dimension where data is insufficient (`"insufficient data — needs trajectory / snapshot"`).
