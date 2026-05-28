# Grading Scale (1-5)

Source: `QC_spec_doc.pdf` → "General Grading Instructions (How the 1-5 scale is used)". These rules are **mechanical** — apply them after the dimension verdicts are in.

---

## Rule 1 — Grade to the LOWEST dimension across all rubrics

If Instruction Following is a 2 and everything else is a 5, the **task score is 2**.

> Across all turns too: if turn 2 is a 2, the task is a 2.

## Rule 2 — Any 1-2 (Fail) criterion = task FAIL

If the task meets **any** `[Fail - X]` criterion in **any** dimension, the entire task fails (final score is 1 or 2).

## Rule 3 — Any 3-4 (Non-Fail) criterion (and no fails) = 3-4

If the task does NOT fail but meets a `[Non-Fail - X]` criterion on **any** dimension, the entire task is 3-4.

## Rule 4 — Score of 5 requires every dimension to be a 5

ALL dimensions must be 5. A single non-fail issue pulls the task down to 3-4.

---

## Rule 5 — Choosing 1 vs 2

- Score **1** if the attempter put **little to no effort**.
- Score **2** if there is a failing issue but the attempter clearly tried.

## Rule 6 — Choosing 3 vs 4

Use your best judgment on how serious the minor issue is.
- Lean **3** if multiple non-fail issues stack up or the issue is more substantive.
- Lean **4** if there is a single, minor issue.

---

## Rule 7 — Prompt / task instructions take precedence over other dimensions

If the prompt or task instructions ask the user to intentionally do something (e.g. "make spelling mistakes in the prompt"), that intentional behavior is **not** marked toward a fail.

---

## Decision algorithm (deterministic)

```
For each dimension D in scope:
    if D triggers any [Fail - X]:
        task_score in {1, 2}
        select 1 if attempter put little/no effort, else 2
    elif D triggers any [Non-Fail - X]:
        D_floor = 3-4
    else:
        D_floor = 5

task_score = min(D_floor for all D in scope)
if any D has Fail tag: task_score is the min(1, 2) decision above

If 3-4 selected:
    choose 4 unless multiple/severe non-fail issues -> choose 3
```

---

## What "dimensions in scope" means

Not every dimension applies to every task. See `03_dimensions.md` for the full applicability matrix. Examples:
- Safety Annotation dimensions apply **only** to tasks where `Has Safety Issues == yes`.
- Weight Diversity (negative-criteria requirement) applies **only** to Safety tasks (per 05/04).
- Test dimensions apply **only** if `verifiers.py` exists (non-experimental tasks).
- Failed Rubric/Unit Test Justification applies **only** when Model A failed at least one rubric or unit test.
- Desired Outcome Coverage is **REMOVED** as of 05/04 — context only, not graded.
- Trajectory Guidance is **REMOVED** as of 05/04.
- Ratings → Validity is **REMOVED** as of 03/09 (replaced by Ranking Validity, then removed entirely).
