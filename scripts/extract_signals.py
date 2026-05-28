#!/usr/bin/env python3
"""Pre-extract per-task audit signals from a rich CSV (lowercase snake_case schema with JSON blobs).

For each row, produces a compact signals JSON containing:
    - identifying fields (task_id, attempt, scenario_type, universe, requires_memory)
    - actual rubric count + total positive/negative weight sums
    - rubric criterion list (idx, weight, category, text — trimmed)
    - rubric_evaluator I/D/M counts + parsed atomicity/self-containedness/etc. flag list
    - unit-test verdicts (Correctness/Underfitting/Coverage/Redundancy) parsed from the markdown report
    - failing tests count + per-failure justification snippets
    - safety annotations (failure list per model, tiers, justifications)
    - the opening prompt, agent objective, desired outcome (trimmed)
    - the trajectory validator feedback
    - the per-failed-rubric justification breakdown

Output: openclaw_qc_auditor/results/_signals/<task_id>.json (one per task).

Usage:
    python extract_signals.py openclaw_qc_auditor/Sample_prev-week.csv
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd


def safe_json(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, (dict, list)):
        return x
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return None
        try:
            return json.loads(s)
        except Exception:
            try:
                return json.loads(json.loads(s))
            except Exception:
                return None
    return None


def parse_eval_metrics(text: str) -> dict:
    if not text:
        return {}
    out = {}
    for label, key in [
        (r"Total Criteria \(I\)", "total"),
        (r"Defective Criteria Count \(D\)", "defective"),
        (r"Missing Items Count \(M\)", "missing"),
        (r"Final Fail-Rate", "fail_rate"),
    ]:
        m = re.search(rf"{label}\s*\|[^|]*\|\s*\*?\*?([\d.]+)", text)
        if m:
            out[key] = m.group(1)
    return out


def parse_test_metrics(text: str) -> dict:
    """Parse the test eval markdown table for Correctness/Underfitting/Coverage/Redundancy results."""
    if not text:
        return {}
    out = {}
    for label, key in [
        ("Correctness", "correctness"),
        ("Underfitting", "underfitting"),
        ("Coverage", "coverage"),
        ("Redundancy", "redundancy"),
    ]:
        m = re.search(rf"\|\s*{label}\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", text)
        if m:
            result = m.group(1).strip()
            verdict = m.group(2).strip()
            # normalize verdict
            v = "pass" if "Pass" in verdict else ("fail" if "Fail" in verdict else "unknown")
            out[key] = {"result_text": result, "verdict": v}
    return out


def extract_atomicity_flags(text: str) -> list[dict]:
    """Pull each `Item [N]` block under `Atomicity` / `Self-Containedness` / `Completeness` / `Classification` etc."""
    if not text:
        return []
    flags = []
    # Each section header
    sec_pattern = re.compile(
        r"####\s*\*\*\d+\.\s*([A-Za-z\s\-/]+?)\*\*\s*\n+(.*?)(?=####|$)",
        re.DOTALL,
    )
    for sec in sec_pattern.finditer(text):
        section = sec.group(1).strip()
        body = sec.group(2)
        if "None" in body[:10] or "*None*" in body[:20]:
            continue
        # find item blocks
        item_pattern = re.compile(
            r"\*\*(?:Item \[(\d+)\]|Missing Criterion)[:\*]+\*\*?\s*`?(.+?)`?\s*\n.*?\*\*(?:Dimension Failed|Suggested Weight)\*\*[:\*]+\s*(.+?)(?:\n|$)",
            re.DOTALL,
        )
        for it in item_pattern.finditer(body):
            idx = it.group(1) or "missing"
            text_snip = (it.group(2) or "")[:150]
            flags.append({"section": section, "item_idx": idx, "text": text_snip})
    return flags


def trim(s: str, n: int = 600) -> str:
    if not s:
        return ""
    s = s.strip()
    if len(s) <= n:
        return s
    return s[:n] + "..."


# G5 Desired-Outcome Leak: token extraction
# A "token" is a noun-like identifier the rubric is likely to grade against:
#   - filenames (e.g. categories_manuel.json)
#   - backtick-quoted identifiers (e.g. `column_name`)
#   - snake_case identifiers of length >= 5 (e.g. content_summary)
#   - quoted enum-style values inside straight or curly quotes
#   - bracketed status tags (e.g. [MATCHED], [STALE])
#   - section heading literals (e.g. ### Matched)
#   - Title Case multi-word phrases (e.g. "Reconciliation View", "Section A: Preferences")
_LEAK_FILE_RE = re.compile(
    r"\b[\w\-./]+\.(?:csv|json|md|html|png|pdf|txt|ics|pptx|xlsx|yaml|yml)\b",
    re.IGNORECASE,
)
_LEAK_BACKTICK_RE = re.compile(r"`([^`\n]{2,80})`")
_LEAK_SNAKE_RE = re.compile(r"\b([a-z][a-z0-9]*(?:_[a-z0-9]+){1,5})\b")
_LEAK_QUOTED_RE = re.compile(
    r"['\"\u201c\u2018]([A-Za-z][\w\s\-/]{2,40})['\"\u201d\u2019]"
)
_LEAK_BRACKET_TAG_RE = re.compile(r"\[([A-Z][A-Z_]{2,40})\]")
_LEAK_HEADING_RE = re.compile(r"###?#?\s+([A-Z][\w \-'/]{2,60})", re.MULTILINE)
_LEAK_TITLECASE_PHRASE_RE = re.compile(
    r"\b([A-Z][a-z]{2,}(?:[\s\-][A-Z][a-z\-]{2,}){1,4})\b"
)
_TRIVIAL_TOKENS = {
    "i.e", "e.g", "etc", "and", "or", "but", "the", "this", "that",
    "memory.md", "verifier.py",  # universal across all OpenClaw tasks
    "snapshots.json", "policy.md", "user.md",
}

# Phrases that are inevitably in every desired_outcome and not failure-relevant.
_GENERIC_TITLECASE = {
    "the agent", "the model", "the user", "the assistant", "the response",
    "the output", "the workspace", "the prompt",
}


def _normalize_for_match(s: str) -> str:
    """Lowercase + collapse path / underscore / dash separators to single spaces.
    Used so 'lucia_crm_engagement_notes' matches 'lucia crm engagement notes'
    in the prompt."""
    return re.sub(r"[/\\_.\-]+", " ", s.lower()).strip()


def extract_leak_tokens(desired_outcome: str, opening_prompt: str) -> list[str]:
    """Tokens that appear in desired_outcome but NOT in opening_prompt.
    Used by G5 (Desired-Outcome Leak detector) in audit_v2.py."""
    if not desired_outcome or not opening_prompt:
        return []
    op_lower = opening_prompt.lower()
    op_norm = _normalize_for_match(opening_prompt)

    candidates: set[str] = set()
    regexes = [
        _LEAK_FILE_RE, _LEAK_BACKTICK_RE, _LEAK_SNAKE_RE,
        _LEAK_QUOTED_RE, _LEAK_BRACKET_TAG_RE, _LEAK_HEADING_RE,
        _LEAK_TITLECASE_PHRASE_RE,
    ]
    for r in regexes:
        for m in r.finditer(desired_outcome):
            tok = m.group(1) if m.lastindex else m.group(0)
            tok_l = tok.strip().lower()
            if not tok_l or len(tok_l) < 5:
                continue
            if tok_l in _TRIVIAL_TOKENS or tok_l in _GENERIC_TITLECASE:
                continue
            candidates.add(tok_l)

    # A token is a leak if neither it nor its normalized form appears in the
    # prompt's lowercase or normalized form. This avoids false positives like
    # "lucia_crm_engagement_notes" when the prompt says "lucia crm engagement
    # notes".
    leaks = []
    for tok in candidates:
        if tok in op_lower:
            continue
        if _normalize_for_match(tok) in op_norm:
            continue
        leaks.append(tok)
    return sorted(leaks)[:80]


def extract_signals(row: pd.Series) -> dict:
    s = {k: ("" if pd.isna(v) else str(v).strip()) for k, v in row.items()}

    # Core IDs
    out = {
        "task_id": s.get("task_id", ""),
        "attempt": s.get("attempt", ""),
        "scenario_type": s.get("scenario_type", ""),
        "assigned_universe": s.get("assigned_universe", ""),
        "requires_memory": s.get("requires_memory", ""),
        "reviewer_prompt_category": s.get("reviewer_prompt_category", ""),
        "review_decision": s.get("review_decision", ""),
        "idea_approved": s.get("idea_approved", ""),
        "idea_feedback": trim(s.get("idea_feedback", ""), 400),
    }

    # Design content
    out["agent_objective_excerpt"] = trim(s.get("agent_objective", ""), 800)
    out["core_functionalities_excerpt"] = trim(s.get("core_functionalities", ""), 1200)
    out["desired_outcome_excerpt"] = trim(s.get("desired_outcome", ""), 800)
    out["opening_prompt"] = trim(s.get("opening_prompt", ""), 1200)
    out["main_request_summary"] = trim(s.get("main_request_summary", ""), 400)

    # G5 supporting signal: tokens that appear in desired_outcome but NOT in
    # opening_prompt. These are the "Desired-Outcome leak" candidates: when a
    # rubric criterion's title contains one of these tokens, it is grading
    # something the model could not have known to do (per QC spec, the
    # desired_outcome is not visible to the model). G5 uses this.
    out["desired_outcome_leak_tokens"] = extract_leak_tokens(
        s.get("desired_outcome", ""), s.get("opening_prompt", "")
    )

    # Source
    out["source_of_inspiration"] = s.get("source_of_inspiration", "")
    out["source_of_inspiration_link"] = s.get("source_of_inspiration_link", "")

    # Trajectory validator
    out["trajectory_validator_passes"] = s.get("trajectory_validator_passes", "")
    out["trajectory_validator_feedback"] = trim(
        s.get("trajectory_validator_feedback", ""), 800
    )
    out["workspace_verification_passed"] = s.get("workspace_verification_passed", "")

    # Safety
    out["has_safety_issues"] = s.get("has_safety_issues", "")
    out["safety_failure_recognition"] = trim(s.get("safety_failure_recognition", ""), 1500)
    out["safety_tier_annotation"] = s.get("safety_tier_annotation", "")
    out["safety_tier_justification"] = trim(s.get("safety_tier_justification", ""), 800)
    out["safety_tier_eval_feedback"] = trim(s.get("safety_tier_eval_feedback", ""), 800)

    # Tests
    out["unit_test_eval_passes"] = s.get("unit_test_eval_passes", "")
    out["unit_test_eval_override_justification"] = trim(
        s.get("unit_test_eval_override_justification", ""), 400
    )
    out["failing_tests_count"] = s.get("failing_tests_count", "")
    test_metrics = parse_test_metrics(s.get("unit_test_eval_feedback", ""))
    out["test_dimensions"] = test_metrics
    out["unit_test_eval_feedback_excerpt"] = trim(
        s.get("unit_test_eval_feedback", ""), 4000
    )

    failing_tests = safe_json(s.get("failing_tests_json", ""))
    if isinstance(failing_tests, list):
        out["failing_tests"] = [
            {
                "name": ft.get("name", ft.get("nodeid", "")),
                "msg": trim(ft.get("message", ft.get("longrepr", "")), 400),
            }
            for ft in failing_tests
        ]
    else:
        out["failing_tests"] = []

    # Rubric
    out["rubric_evaluator_passes"] = s.get("rubric_evaluator_passes", "")
    out["rubric_evaluator_override_justification"] = trim(
        s.get("rubric_evaluator_override_justification", ""), 400
    )
    eval_metrics = parse_eval_metrics(s.get("rubric_evaluator_feedback", ""))
    out["rubric_eval_metrics"] = eval_metrics
    out["rubric_evaluator_feedback_excerpt"] = trim(
        s.get("rubric_evaluator_feedback", ""), 8000
    )
    out["rubric_eval_flags_parsed"] = extract_atomicity_flags(
        s.get("rubric_evaluator_feedback", "")
    )

    out["final_rubric_criteria_count_field"] = s.get("final_rubric_criteria_count", "")
    out["rubric_total_weight_positive"] = s.get("rubric_total_weight_positive", "")
    out["rubric_total_weight_negative"] = s.get("rubric_total_weight_negative", "")
    out["rubric_negative_criteria_count_final"] = s.get(
        "rubric_negative_criteria_count_final", ""
    )

    rubric_json = safe_json(s.get("final_rubric_criteria_json", ""))
    if isinstance(rubric_json, list):
        out["actual_rubric_count"] = len(rubric_json)
        out["rubric_criteria"] = [
            {
                "idx": i + 1,
                "weight": c.get("weight"),
                "category": c.get("category", c.get("type", "")),
                "label": c.get("label", c.get("target", "")),
                "text": trim(c.get("text", c.get("description", "")), 350),
            }
            for i, c in enumerate(rubric_json)
        ]
    else:
        out["actual_rubric_count"] = "?"
        out["rubric_criteria"] = []

    # Justifications breakdown for Dim 21
    jb = safe_json(s.get("rubric_justifications_breakdown_json", ""))
    if jb is not None:
        if isinstance(jb, list):
            out["rubric_justifications"] = [
                {
                    "idx": i,
                    "rubric_text": trim(str(j.get("rubric") or j.get("text") or ""), 200),
                    "q1": trim(str(j.get("why_correct") or j.get("q1") or j.get("rubric_is_correct") or ""), 400),
                    "q2": trim(str(j.get("why_present") or j.get("q2") or j.get("rubric_is_necessary") or ""), 400),
                    "q3": trim(str(j.get("model_mistake") or j.get("q3") or j.get("what_model_did_wrong") or ""), 400),
                }
                for i, j in enumerate(jb)
            ]
        else:
            out["rubric_justifications"] = jb
    else:
        out["rubric_justifications"] = []

    # Test justifications
    tj = safe_json(s.get("test_justifications_for_model_json", ""))
    if isinstance(tj, list):
        out["test_justifications"] = [
            {
                "idx": i,
                "test": trim(str(j.get("test") or j.get("name") or ""), 200),
                "q1": trim(str(j.get("why_correct") or j.get("q1") or ""), 400),
                "q2": trim(str(j.get("why_present") or j.get("q2") or ""), 400),
                "q3": trim(str(j.get("model_mistake") or j.get("q3") or ""), 400),
            }
            for i, j in enumerate(tj)
        ]
    else:
        out["test_justifications"] = []

    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv_path")
    p.add_argument("--out-dir", default="openclaw_qc_auditor/results/_signals", help="Output directory.")
    args = p.parse_args()

    df = pd.read_csv(args.csv_path, dtype=str, keep_default_na=False)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for _, row in df.iterrows():
        sig = extract_signals(row)
        path = out_dir / f"{sig['task_id']}.json"
        path.write_text(json.dumps(sig, indent=2, ensure_ascii=False))
        print(
            f"[ok] {sig['task_id']}  scen={sig['scenario_type'][:24]:<24}  "
            f"univ={sig['assigned_universe'][:20]:<20}  rubric_n={sig['actual_rubric_count']:<3}  "
            f"failing_tests={sig.get('failing_tests_count', ''):<3}  "
            f"safety={sig['has_safety_issues']:<4}  tier={sig['safety_tier_annotation'][:10]}"
        )

    print(f"\nWrote {len(df)} signal files to {out_dir}/")


if __name__ == "__main__":
    main()
