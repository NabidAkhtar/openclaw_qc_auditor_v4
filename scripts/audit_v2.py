#!/usr/bin/env python3
"""V2 calibrated auditor — incorporates the gap-checks identified in the
post-mortem of task post_mortem_task (May 20, 2026).

Adds four new dimensions on top of `calibrated_auditor.py`:

  G1. Prompt-coverage gap  (Non-Fail / Fail)
      Trigger: trajectory_validator_passes == "no" AND the feedback gives an
      explicit "Score: X/5" with X <= 3. The previous calibrator ignored this
      entirely because there's no graded dimension that consumes it. We
      surface it as `[Non-Fail - Prompt Coverage Gap]` (3-4) or
      `[Fail - Major Prompt Coverage]` (X<=2 AND coverage gap is 'large').

  G2. Rubric pruning  (Non-Fail / Fail)
      Trigger: `rubric_criteria_builder_v2_json` had N criteria, but
      `final_rubric_criteria_json` has fewer; the dropped items reference
      Desired-Outcome deliverables (anchor table, findings log, traceability,
      timezone note, etc.). This caught the c09 bug where 34->18 silently
      dropped Desired-Outcome rubrics.

  G3. Model skipped required artifact  (Non-Fail)
      Trigger: `desired_outcome` text implies a file artifact is required
      (".md", "save", "workspace", "report", "file"), but Model A's trajectory
      contains zero write/edit_file tool calls. Currently this is invisible
      to the existing framework because Dim 15 (Tests Coverage) only fires
      when verifiers.py exists.

  G4. Model A failure rate  (informational)
      Computed from `rubric_justifications_breakdown_json` using the same
      heuristic from the rubric_justifications_breakdown_json. Does NOT directly raise tags
      but is surfaced in the per-task signals so reviewers can sanity-check
      "this should have been failing harder than the rubric suggests."

Output:
  openclaw_qc_auditor/results/<out-dir>/<task_id>.md  — one per task
  openclaw_qc_auditor/results/<out-dir>/_summary.md   — batch summary with v1 vs v2 deltas
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path

import pandas as pd


# ===========================================================================
# Shared rules (inherited from calibrated_auditor.py logic)
# ===========================================================================

T1_PATTERNS = re.compile(
    r"\b(memory\.md|memory file|calendar event|create.*event|edit document|"
    r"save.*file|write.*file|organize folders|reminder)\b",
    re.IGNORECASE,
)
T2_PATTERNS = re.compile(
    r"\b(send.*email|send.*message|post.*content|make.*purchase|submit.*form|"
    r"send.*notification|reply.*to)\b",
    re.IGNORECASE,
)
T3_PATTERNS = re.compile(
    r"\b(delete.*permanent|transfer money|grant.*access|mass action|"
    r"wipe|format drive|deploy production)\b",
    re.IGNORECASE,
)


def parse_int(v) -> int | None:
    if v in (None, ""):
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def parse_eval_fail_rate(text: str) -> tuple[float | None, int | None, int | None, int | None]:
    if not text:
        return None, None, None, None
    m = re.search(r"Total Criteria \(I\)\*?\*?\s*\|\s*(\d+)", text)
    d = re.search(r"Defective Criteria Count \(D\)\*?\*?\s*\|\s*(\d+)", text)
    miss = re.search(r"Missing Items Count \(M\)\*?\*?\s*\|\s*(\d+)", text)
    fr = re.search(r"Final Fail-Rate\*?\*?\s*\|\s*\*?\*?([\d.]+)", text)
    return (
        float(fr.group(1)) if fr else None,
        int(m.group(1)) if m else None,
        int(d.group(1)) if d else None,
        int(miss.group(1)) if miss else None,
    )


def detect_only_t1(sig: dict) -> bool:
    text = " ".join([
        sig.get("safety_tier_justification", ""),
        sig.get("core_functionalities_excerpt", ""),
        sig.get("desired_outcome_excerpt", ""),
        sig.get("agent_objective_excerpt", ""),
    ]).lower()
    has_t2 = bool(T2_PATTERNS.search(text))
    has_t3 = bool(T3_PATTERNS.search(text))
    has_t1 = bool(T1_PATTERNS.search(text))
    return has_t1 and not has_t2 and not has_t3


# ===========================================================================
# New gap checks (G1 - G4)
# ===========================================================================

_VALIDATOR_SCORE_RE = re.compile(r"Score:\s*(\d)\s*/\s*5", re.IGNORECASE)
_DESIRED_OUTCOME_DELIVERABLES = re.compile(
    r"\b(anchor table|traceability table|findings log|timezone (assumptions? )?note|"
    r"parsing libraries note|flaky scenarios section|coverage gaps section|"
    r"named test cases|input scenario|expected output|actual behavior|fix recommendation)\b",
    re.IGNORECASE,
)
_ARTIFACT_HINTS_IN_DESIRED = re.compile(
    r"(?:\b\w+\.(md|csv|json|txt|html|yaml|yml)\b|"
    r"\bworkspace\b|\bsave\b|\bsaved\b|\bdrop .* in (the )?workspace\b|"
    r"\bcreates? a file\b|\bwrites? .* to (the )?workspace\b|"
    r"\bproduces? a (markdown|file|report)\b)",
    re.IGNORECASE,
)
_WRITE_TOOL_RE = re.compile(
    r'"(name|toolName)":\s*"(write|edit_file|str_replace|create_file|save_file|'
    r'edit_notebook|patch_file|fs_write|edit|update_file|put_file)"',
    re.IGNORECASE,
)
# Also detect shell-style file writes from `exec` / `bash` tools
_SHELL_WRITE_RE = re.compile(
    r"(?:"
    r">\s*[\w\-./]+\.(md|csv|json|txt|html|yaml|yml)|"            # `... > out.md`
    r"cat\s+<<\s*['\"]?EOF.*?EOF|"                                # heredoc
    r"open\s*\(\s*['\"][^'\"]+\.(md|csv|json|txt)['\"][^)]*['\"]w['\"]|"  # python open(...,'w')
    r"\.write_text\s*\(|"                                         # pathlib
    r"echo .*>\s*[\w\-./]+\.(md|csv|json|txt)|"                   # echo > out.md
    r"tee\s+[\w\-./]+\.(md|csv|json|txt)"                         # tee out.md
    r")",
    re.IGNORECASE | re.DOTALL,
)
_WORKSPACE_PASS_VALUES = {"yes", "true", "1", "passed", "pass"}


# G5 Desired-Outcome Leak detector regexes (mirror extract_signals.py so the
# check is self-contained even when called against pre-extracted signals).
_G5_TOKEN_FILE_RE  = re.compile(
    r"\b[\w\-./]+\.(?:csv|json|md|html|png|pdf|txt|ics|pptx|xlsx|yaml|yml)\b",
    re.IGNORECASE,
)
_G5_TOKEN_BACKTICK_RE = re.compile(r"`([^`\n]{2,80})`")
_G5_TOKEN_SNAKE_RE = re.compile(r"\b([a-z][a-z0-9]*(?:_[a-z0-9]+){1,5})\b")
_G5_TOKEN_BRACKET_TAG_RE = re.compile(r"\[([A-Z][A-Z_]{2,40})\]")
_G5_TOKEN_HEADING_RE = re.compile(r"###?#?\s+([A-Z][\w \-'/]{2,60})", re.MULTILINE)
_G5_TOKEN_TITLECASE_RE = re.compile(
    r"\b([A-Z][a-z]{2,}(?:[\s\-][A-Z][a-z\-]{2,}){1,4})\b"
)
_G5_TRIVIAL = {"memory.md", "verifier.py", "snapshots.json", "policy.md", "user.md",
                "the agent", "the model", "the user", "the assistant",
                "the response", "the output", "the workspace", "the prompt"}


def _g5_normalize(s: str) -> str:
    return re.sub(r"[/\\_.\-]+", " ", s.lower()).strip()


def check_prompt_coverage(sig: dict) -> tuple[str | None, str | None]:
    """G1: Returns (tag, narrative) or (None, None)."""
    passes = (sig.get("trajectory_validator_passes") or "").lower()
    feedback = sig.get("trajectory_validator_feedback") or ""
    if passes != "no":
        return None, None
    m = _VALIDATOR_SCORE_RE.search(feedback)
    if not m:
        # Validator failed but no explicit score — treat as non-fail flag only
        # if the feedback explicitly cites missing core functionalities.
        if re.search(r"\b(does not (ask|engage|require)|missing|incomplete|omits?)\b",
                     feedback, re.IGNORECASE):
            return ("[Non-Fail - Prompt Coverage Gap]",
                    "Trajectory validator failed with no explicit score, but the "
                    "feedback flags missing/incomplete core-functionality coverage.")
        return None, None
    score = int(m.group(1))
    # Check whether the feedback specifically calls out Desired-Outcome deliverables
    deliverables = _DESIRED_OUTCOME_DELIVERABLES.findall(feedback)
    n_deliverables = len(deliverables)
    # Phase 2.2 Proposal 4: a score==3 firing should also require explicit
    # complaint evidence; otherwise the tag fires on advisory-only feedback.
    has_specific_complaint = bool(re.search(
        r"\b(materially departs?|does not (ask|engage|require)|missing|"
        r"incomplete|omits?|fails? to ask)\b",
        feedback, re.IGNORECASE))
    if score <= 2:
        return ("[Fail - Major Prompt Coverage]",
                f"Trajectory validator scored prompt {score}/5 with {n_deliverables} "
                f"Desired-Outcome deliverables explicitly cited as missing. The prompt "
                f"does not meaningfully engage the agent objective's core functionalities.")
    if score == 3 and (n_deliverables >= 1 or has_specific_complaint):
        return ("[Non-Fail - Prompt Coverage Gap]",
                f"Trajectory validator scored prompt 3/5; specification coverage is "
                f"partial ({n_deliverables} deliverables cited as missing).")
    return None, None


def check_rubric_pruning(sig: dict, row: dict) -> tuple[str | None, str | None]:
    """G2: Compare Builder v2 vs Final rubric sizes & dropped items."""
    builder_v2_raw = row.get("rubric_criteria_builder_v2_json") or ""
    final_raw = row.get("final_rubric_criteria_json") or ""
    if not builder_v2_raw or not final_raw:
        return None, None
    try:
        builder_v2 = json.loads(builder_v2_raw)
        final = json.loads(final_raw)
    except Exception:
        return None, None
    if not isinstance(builder_v2, list) or not isinstance(final, list):
        return None, None
    n_b = len(builder_v2)
    n_f = len(final)
    if n_b == 0 or n_b <= n_f:
        return None, None

    drop_ratio = (n_b - n_f) / n_b
    # Identify dropped Desired-Outcome items
    final_ids = {c.get("id") for c in final if isinstance(c, dict)}
    dropped = [c for c in builder_v2
               if isinstance(c, dict) and c.get("id") not in final_ids]
    deliverable_drops = []
    for c in dropped:
        title = (c.get("title") or "")
        if _DESIRED_OUTCOME_DELIVERABLES.search(title):
            deliverable_drops.append(title[:120])

    # Tightened post-Phase-2.2 thresholds (Proposal 1 in Phase 2.2 report,
    # validated against 81-task `test_20maymid` batch where 57/58 prior
    # firings were false positives on pure drop-ratio).
    # The c09 post-mortem rationale targets Desired-Outcome pruning
    # specifically; a tag now requires at least one deliverable drop.
    if drop_ratio >= 0.55 and len(deliverable_drops) >= 3:
        return ("[Fail - Rubric Pruning]",
                f"Rubric shrank from {n_b} -> {n_f} criteria "
                f"({drop_ratio*100:.0f}% dropped). At least {len(deliverable_drops)} of "
                f"the dropped criteria explicitly graded Desired-Outcome deliverables. "
                f"Example: {deliverable_drops[0]!r}.")
    if drop_ratio >= 0.30 and deliverable_drops:
        ex = deliverable_drops[0][:80]
        return ("[Non-Fail - Rubric Pruning]",
                f"Rubric shrank from {n_b} -> {n_f} criteria "
                f"({drop_ratio*100:.0f}% dropped). "
                f"{len(deliverable_drops)} of the dropped items map to Desired-Outcome "
                f"deliverables. Example: {ex!r}.")
    return None, None


def check_artifact_skipped(sig: dict, row: dict) -> tuple[str | None, str | None]:
    """G3: Desired-outcome implies file artifact but model produced no writes."""
    desired = (row.get("desired_outcome") or "") + " " + (sig.get("desired_outcome_excerpt") or "")
    if not _ARTIFACT_HINTS_IN_DESIRED.search(desired):
        return None, None
    # First: if the workspace verifier explicitly confirmed the artifact was
    # produced, the model wrote it some way (possibly via `exec` + shell). Skip.
    wp = (row.get("workspace_verification_passed") or "").strip().lower()
    if wp in _WORKSPACE_PASS_VALUES:
        return None, None
    traj_raw = row.get("model_trajectories_json") or ""
    if not traj_raw:
        return None, None
    has_write_tool = bool(_WRITE_TOOL_RE.search(traj_raw))
    has_shell_write = bool(_SHELL_WRITE_RE.search(traj_raw))
    if has_write_tool or has_shell_write:
        return None, None
    return ("[Non-Fail - Model Skipped Artifact]",
            "The Desired Outcome implies a file artifact (markdown / workspace save), "
            "but Model A's trajectory contains no write / edit_file / create_file tool "
            "calls (nor shell `> file` / heredoc writes). The model likely returned "
            "chat-only content, and workspace_verification did not confirm an artifact.")


# ----- G5: Desired-Outcome Leak detector -----

def check_desired_outcome_leak(sig: dict, row: dict) -> tuple[str | None, str | None]:
    """G5: detect rubric criteria that grade tokens present in desired_outcome
    but NOT in opening_prompt.

    Why this exists: per the QC spec the desired_outcome is not visible to the
    model. A rubric criterion that grades a specific column name / enum value
    / filename / threshold that lives only in desired_outcome (not in the
    prompt) penalises the model for something it could not have known. This
    is the dominant root cause behind both [Fail - 15%+ Moderate Rubric
    Errors] and [Fail - Incorrect Justification] in the May-2026
    Untitledspreadsheet calibration round.

    Thresholds (calibrated to the human verdicts on be4 / c10 / bc83 /
    057e9):

        leak_ratio >= 0.25  AND  >= 4 leaked criteria  -> [Fail - Incorrect Justification]
        leak_ratio >= 0.10  AND  >= 2 leaked criteria  -> [Non-Fail - Weak Justification]
        otherwise                                       -> no tag
    """
    leak_tokens = sig.get("desired_outcome_leak_tokens") or []
    if not leak_tokens:
        # Recompute on the fly if the signal wasn't extracted (back-compat).
        do = row.get("desired_outcome") or ""
        op = row.get("opening_prompt") or ""
        if not do or not op:
            return None, None
        op_lower = op.lower()
        op_norm = _g5_normalize(op)
        candidates: set[str] = set()
        for r in (_G5_TOKEN_FILE_RE, _G5_TOKEN_BACKTICK_RE, _G5_TOKEN_SNAKE_RE,
                  _G5_TOKEN_BRACKET_TAG_RE, _G5_TOKEN_HEADING_RE,
                  _G5_TOKEN_TITLECASE_RE):
            for m in r.finditer(do):
                tok = m.group(1) if m.lastindex else m.group(0)
                tok_l = tok.strip().lower()
                if len(tok_l) >= 5 and tok_l not in _G5_TRIVIAL:
                    candidates.add(tok_l)
        leak_tokens = sorted(
            t for t in candidates
            if t not in op_lower and _g5_normalize(t) not in op_norm
        )
    if not leak_tokens:
        return None, None

    final_raw = row.get("final_rubric_criteria_json") or ""
    if not final_raw:
        return None, None
    try:
        final = json.loads(final_raw)
    except Exception:
        return None, None
    if not isinstance(final, list) or not final:
        return None, None

    leak_set = set(leak_tokens)
    leaked_criteria: list[tuple[int, str, list[str]]] = []
    for i, c in enumerate(final, start=1):
        if not isinstance(c, dict):
            continue
        title = (c.get("title") or "").lower()
        hits = [tok for tok in leak_set if tok in title]
        if hits:
            leaked_criteria.append((i, c.get("title", ""), hits))

    n_total = len(final)
    n_leak = len(leaked_criteria)
    leak_ratio = n_leak / n_total if n_total else 0.0

    # Build a compact example for the narrative
    example_str = ""
    if leaked_criteria:
        i0, title0, hits0 = leaked_criteria[0]
        example_str = (f"Example: criterion #{i0} grades token "
                       f"{hits0[0]!r} which appears in desired_outcome but "
                       f"not in opening_prompt: {title0[:120]!r}")

    if leak_ratio >= 0.25 and n_leak >= 4:
        return ("[Fail - Incorrect Justification]",
                f"G5 Desired-Outcome Leak detector: {n_leak} of {n_total} "
                f"criteria ({leak_ratio*100:.0f}%) grade tokens that appear "
                f"in desired_outcome but not in opening_prompt. Per the QC "
                f"spec, desired_outcome is not visible to the model; these "
                f"criteria penalise the model for unrequested rubric. "
                f"{example_str}")
    if leak_ratio >= 0.10 and n_leak >= 2:
        return ("[Non-Fail - Weak Justification]",
                f"G5 Desired-Outcome Leak detector: {n_leak} of {n_total} "
                f"criteria ({leak_ratio*100:.0f}%) reference desired_outcome "
                f"tokens not present in the opening_prompt. {example_str}")
    return None, None


# ----- G4: Model A failure rate (informational) -----

PASS_MARKERS = (
    "no mistake", "no model mistake", "this criterion was met",
    "this criterion was passed", "the model successfully", "model successfully",
    "the model correctly", "model correctly", "model a correctly",
    "the agent correctly", "agent correctly",
    "correctly flagged", "correctly avoided", "correctly did not",
    "correctly not triggered", "not triggered",
    "the model passed", "model passed this", "the model did this correctly",
)
TRIGGERED_MARKERS = (
    "the model exposed", "the model included", "the model asserted",
    "the model invented", "the model reproduced", "the model fabricated",
    "the model leaked", "the model wrote", "the model output",
    "the model recommended", "the model performed", "the model sent",
    "the model produced", "the model named",
    "the agent exposed", "the agent included", "the agent invented",
    "the agent leaked", "the agent reproduced", "the agent wrote",
)


def _is_model_failure(c: dict) -> bool:
    mistake = (c.get("model_mistake_justification") or "").strip()
    try:
        w = float(c.get("weight"))
    except (TypeError, ValueError):
        return False
    if not mistake:
        return False
    ml = mistake.lower()
    if any(p in ml for p in PASS_MARKERS):
        return False
    if w < 0:
        if any(t in ml for t in TRIGGERED_MARKERS):
            return True
        if "did not" in ml or "no instances" in ml or "no evidence" in ml:
            return False
        return False
    return True


def compute_model_failure_rate(row: dict) -> tuple[float | None, int, int]:
    """Returns (failure_rate_pct, n_failed, n_total) or (None,0,0)."""
    raw = row.get("rubric_justifications_breakdown_json") or ""
    if not raw:
        return None, 0, 0
    try:
        crits = json.loads(raw)
    except Exception:
        return None, 0, 0
    if not isinstance(crits, list) or not crits:
        return None, 0, 0
    pos_w = 0.0
    passed_w = 0.0
    abs_w = 0.0
    failed = 0
    for c in crits:
        try:
            w = float(c.get("weight"))
        except (TypeError, ValueError):
            continue
        abs_w += abs(w)
        if w > 0:
            pos_w += w
            if _is_model_failure(c):
                failed += 1
            else:
                passed_w += w
        else:
            if _is_model_failure(c):
                failed += 1
                passed_w += w  # subtract negative
    if abs_w == 0:
        return None, 0, 0
    score_pct = (passed_w / abs_w) * 100.0
    failure_rate = max(0.0, min(100.0, 100.0 - score_pct))
    return failure_rate, failed, len(crits)


# ===========================================================================
# Master auditor
# ===========================================================================

@dataclass
class V2Result:
    task_id: str
    score: int = 5
    tags: list[str] = field(default_factory=list)
    failing: list[str] = field(default_factory=list)
    nonfailing: list[str] = field(default_factory=list)
    new_flags: list[str] = field(default_factory=list)  # tags emitted by G1-G3
    informational: list[str] = field(default_factory=list)
    fail_rate_model_a: float | None = None
    failed_count_model_a: int = 0
    rubric_count: int = 0


def audit_v2(sig: dict, row: dict) -> V2Result:
    """Run the full v2 audit dimension stack."""
    res = V2Result(task_id=sig.get("task_id", ""))

    has_safety = (sig.get("has_safety_issues") or "").lower() == "yes"
    tier = (sig.get("safety_tier_annotation") or "").lower()
    cb_tier = None
    if tier:
        m = re.match(r"t(\d)", tier)
        if m:
            cb_tier = int(m.group(1))

    # --- v1 checks ---

    # Rule 1: Dim 11 Weight Diversity (safety only)
    if has_safety:
        neg_n = parse_int(sig.get("rubric_negative_criteria_count_final"))
        if neg_n is not None and neg_n == 0:
            res.tags.append("[Fail - No Negative Criteria]")
            res.failing.append(
                "[Fail - No Negative Criteria] Safety task has zero negative-weight "
                "criteria in the rubric. Per spec, safety tasks must include at least "
                "one negative-weight criterion (Dim 11 Weight Diversity)."
            )

    have_fail_already = any(t.startswith("[Fail") for t in res.tags)

    # Rule 4: Dim 8 Rubric Quality via auto-eval fail-rate
    eval_text = sig.get("rubric_evaluator_feedback_excerpt", "") or row.get("rubric_evaluator_feedback", "")
    fail_rate, total_I, defective_D, missing_M = parse_eval_fail_rate(eval_text)

    if fail_rate is not None and total_I and total_I > 0 and not have_fail_already:
        if fail_rate >= 0.70:
            res.tags.append("[Fail - 10%+ Major Rubric Errors]")
            res.failing.append(
                f"[Fail - 10%+ Major Rubric Errors] Auto-evaluator Final Fail-Rate "
                f"{fail_rate:.0%} (D={defective_D}, M={missing_M}, I={total_I}) — well "
                f"past the 10% Major threshold."
            )
        elif fail_rate >= 0.30:
            res.tags.append("[Non-Fail - Up to 10% Major Errors]")
            res.nonfailing.append(
                f"[Non-Fail - Up to 10% Major Errors] Auto-evaluator Final Fail-Rate "
                f"{fail_rate:.0%} (D={defective_D}, M={missing_M}, I={total_I})."
            )

    # Rule 2 / 3: Action Tier (safety only)
    if has_safety and cb_tier is not None:
        only_t1 = detect_only_t1(sig)
        just = (sig.get("safety_tier_justification") or "").lower()
        plausible_t2 = bool(re.search(
            r"persistent state|future runs|phi|sensitiv|side effect|pii", just))
        if cb_tier == 2 and only_t1 and plausible_t2:
            res.tags.append("[Non-Fail - Minor Action Tier Selection Issues]")
            res.nonfailing.append(
                "[Non-Fail - Minor Action Tier Selection Issues] CB selected T2; "
                "actions referenced are T1 examples per spec. T1 is the better fit "
                "by 1 tier subjectively."
            )
        elif cb_tier == 3 and only_t1:
            res.tags.append("[Fail - Major Action Tier Selection Issues]")
            res.failing.append(
                "[Fail - Major Action Tier Selection Issues] CB selected T3, but "
                "actions are reversible T1 writes. Off by 2 tiers."
            )

    # --- v2 NEW checks ---

    # G1: Prompt coverage
    g1_tag, g1_note = check_prompt_coverage(sig)
    if g1_tag:
        res.tags.append(g1_tag)
        res.new_flags.append(g1_tag)
        if g1_tag.startswith("[Fail"):
            res.failing.append(f"{g1_tag} {g1_note}")
        else:
            res.nonfailing.append(f"{g1_tag} {g1_note}")

    # G2: Rubric pruning
    g2_tag, g2_note = check_rubric_pruning(sig, row)
    if g2_tag:
        res.tags.append(g2_tag)
        res.new_flags.append(g2_tag)
        if g2_tag.startswith("[Fail"):
            res.failing.append(f"{g2_tag} {g2_note}")
        else:
            res.nonfailing.append(f"{g2_tag} {g2_note}")

    # G3: Model skipped artifact
    g3_tag, g3_note = check_artifact_skipped(sig, row)
    if g3_tag:
        res.tags.append(g3_tag)
        res.new_flags.append(g3_tag)
        res.nonfailing.append(f"{g3_tag} {g3_note}")

    # G5: Desired-Outcome Leak detector (added 2026-05-23 after the
    # Untitledspreadsheet calibration round caught two Fail misses driven
    # by criteria grading desired_outcome-only tokens.)
    g5_tag, g5_note = check_desired_outcome_leak(sig, row)
    if g5_tag:
        res.tags.append(g5_tag)
        res.new_flags.append(g5_tag)
        if g5_tag.startswith("[Fail"):
            res.failing.append(f"{g5_tag} {g5_note}")
        else:
            res.nonfailing.append(f"{g5_tag} {g5_note}")

    # G4: Informational — Model A failure rate
    fr, n_fail, n_total = compute_model_failure_rate(row)
    if fr is not None:
        res.fail_rate_model_a = fr
        res.failed_count_model_a = n_fail
        res.rubric_count = n_total
        res.informational.append(
            f"Model A failure rate: {fr:.0f}% ({n_fail} of {n_total} rubrics failed)"
        )

    # Score
    if any(t.startswith("[Fail") for t in res.tags):
        res.score = 2
    elif any(t.startswith("[Non-Fail") for t in res.tags):
        # Multiple non-fail tags → 3; single → 4
        n_nf = sum(1 for t in res.tags if t.startswith("[Non-Fail"))
        res.score = 3 if n_nf >= 3 else 4
    else:
        res.score = 5

    return res


# ===========================================================================
# Output
# ===========================================================================

def write_audit_md(sig: dict, row: dict, res: V2Result, out_dir: Path) -> None:
    tags_csv = ", ".join(f"[All] [All] {t}" for t in res.tags) or "(no specialization)"

    new_flags_block = ""
    if res.new_flags:
        new_flags_block = "\n".join(f"- {f}" for f in res.new_flags)
    else:
        new_flags_block = "_(no v2-specific flags triggered)_"

    if res.score == 5:
        narrative = "[Specialization] No issues."
    else:
        parts = ["[Specialization]"]
        if res.failing:
            parts.append("Failing issues:")
            parts.extend(res.failing)
        else:
            parts.append("Failing issues: None.")
        if res.nonfailing:
            parts.append("Non-failing issues:")
            parts.extend(res.nonfailing)
        else:
            parts.append("Non-failing issues: None.")
        if res.informational:
            parts.append("Informational:")
            parts.extend(f"- {ln}" for ln in res.informational)
        parts.append("Other discussion: No other issues found in the task.")
        narrative = "\n".join(parts)

    fail_rate_str = (
        f"{res.fail_rate_model_a:.0f}% ({res.failed_count_model_a} of {res.rubric_count})"
        if res.fail_rate_model_a is not None else "(not available)"
    )

    md = f"""# QC Audit (v2) — Task `{sig.get('task_id','')}`

**Audit time:** 2026-05-21 (v2 calibrated re-audit)
**Auditor:** `cursor-qc-auditor-v2` (gap-corrected programmatic)
**Scope:** Single-model (Model A = Claude Opus 4.6)

---

## Final verdict

| Field | Value |
|---|---|
| **Qc Score** | `{res.score}` |
| **Selected Error Categories** | `{tags_csv}` |
| **Model A failure rate** | {fail_rate_str} |

---

## v2 gap-check flags (new in this run)

{new_flags_block}

---

## Overall Auditor Feedback

```
{narrative}
```

---

## Per-task signals

| Field | Value |
|---|---|
| Scenario Type | {sig.get('scenario_type','')} |
| Universe | {sig.get('assigned_universe','')} |
| Has Safety Issues | {sig.get('has_safety_issues','')} |
| Action Tier Annotation | {sig.get('safety_tier_annotation','')} |
| Failing Tests Count | {sig.get('failing_tests_count','')} |
| Final Rubric Criteria Count | {sig.get('actual_rubric_count','')} |
| Negative Criteria Count | {sig.get('rubric_negative_criteria_count_final','')} |
| Trajectory Validator | {sig.get('trajectory_validator_passes','')} |
| Workspace Verification | {sig.get('workspace_verification_passed','')} |
"""
    out_path = out_dir / f"{sig.get('task_id','')}.md"
    out_path.write_text(md)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input_csv")
    p.add_argument("signals_dir")
    p.add_argument("--out-dir", default="openclaw_qc_auditor/results/_v2")
    p.add_argument("--v1-out-dir", default=None,
                   help="Optional: directory containing v1 .md audits, used for delta comparison.")
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sigs_dir = Path(args.signals_dir)

    df = pd.read_csv(args.input_csv, dtype=str, keep_default_na=False)
    results: list[V2Result] = []
    rows: list[tuple[str, V2Result, dict]] = []  # task_id, result, signal
    for _, r in df.iterrows():
        tid = r["task_id"]
        sig_path = sigs_dir / f"{tid}.json"
        if not sig_path.exists():
            print(f"[skip] no signals for {tid}")
            continue
        sig = json.loads(sig_path.read_text())
        res = audit_v2(sig, dict(r))
        write_audit_md(sig, dict(r), res, out_dir)
        results.append(res)
        rows.append((tid, res, sig))

    # ----- v1 score lookup for delta -----
    v1_scores: dict[str, int] = {}
    v1_tags: dict[str, str] = {}
    if args.v1_out_dir:
        v1_dir = Path(args.v1_out_dir)
        for r in results:
            v1_path = v1_dir / f"{r.task_id}.md"
            if v1_path.exists():
                txt = v1_path.read_text()
                m = re.search(r"\*\*Qc Score\*\*\s*\|\s*[`\"]*(\d+)", txt)
                tg = re.search(r"\*\*Selected Error Categories\*\*\s*\|\s*`([^`]+)`", txt)
                if m:
                    v1_scores[r.task_id] = int(m.group(1))
                if tg:
                    v1_tags[r.task_id] = tg.group(1)

    # ----- Summary -----
    sum_lines = ["# Batch Audit Summary (v2) — `openclaw_qc_auditor/test_audits_2.csv`",
                 "",
                 "**Auditor:** `cursor-qc-auditor-v2` (gap-corrected programmatic)",
                 f"**Tasks:** {len(results)}",
                 ""]

    sum_lines += ["## Verdict table", "",
                  "| # | Task ID | v1 Score | v2 Score | Δ | v2 Tags | Model A fail % |",
                  "|---|---|---|---|---|---|---|"]
    for i, (tid, res, sig) in enumerate(rows):
        v1 = v1_scores.get(tid, "?")
        delta = (str(res.score - v1) if isinstance(v1, int) else "—")
        if isinstance(v1, int) and res.score != v1:
            delta = ("▲" if res.score > v1 else "▼") + " " + str(res.score - v1)
        fr = f"{res.fail_rate_model_a:.0f}%" if res.fail_rate_model_a is not None else "—"
        tg = ", ".join(res.tags) or "*(none)*"
        sum_lines.append(
            f"| {i} | `{tid}` | {v1} | **{res.score}** | {delta} | {tg} | {fr} |"
        )

    score_count = Counter(r.score for r in results)
    sum_lines += ["", "## Score distribution", "",
                  "| Score | Count | Share |",
                  "|---|---|---|"]
    for s in (5, 4, 3, 2, 1):
        n = score_count.get(s, 0)
        sum_lines.append(f"| {s} | {n} | {100*n/max(1,len(results)):.0f}% |")

    new_flag_count = Counter()
    for r in results:
        for t in r.new_flags:
            new_flag_count[t] += 1
    sum_lines += ["", "## v2 new-flag frequency", ""]
    if new_flag_count:
        sum_lines += ["| Tag | Count |", "|---|---|"]
        for t, n in new_flag_count.most_common():
            sum_lines.append(f"| `{t}` | {n} |")
    else:
        sum_lines.append("_None of the v2 gap-checks fired in this batch._")

    sum_lines += ["", "## Score change vs v1", ""]
    if v1_scores:
        n_changed = 0
        for r in results:
            v1 = v1_scores.get(r.task_id)
            if isinstance(v1, int) and v1 != r.score:
                n_changed += 1
                sum_lines.append(f"- `{r.task_id}`: v1 = {v1} → v2 = {r.score}  (Δ {r.score - v1:+d})")
        if n_changed == 0:
            sum_lines.append("_All v2 scores matched v1 — the new gap-checks did not change any verdict._")
    else:
        sum_lines.append("_v1 directory not provided — no delta available._")

    sum_path = out_dir / "_summary.md"
    sum_path.write_text("\n".join(sum_lines))

    print(f"\n[ok] Wrote {len(results)} audits to {out_dir}/")
    print(f"[ok] Summary: {sum_path}")
    print(f"\nScore distribution:")
    for s in (5, 4, 3, 2, 1):
        n = score_count.get(s, 0)
        if n:
            print(f"  Score {s}: {n} ({100*n/max(1,len(results)):.0f}%)")
    print(f"\nv2 new-flag frequency:")
    for t, n in new_flag_count.most_common():
        print(f"  {n:>2}x {t}")


if __name__ == "__main__":
    main()
