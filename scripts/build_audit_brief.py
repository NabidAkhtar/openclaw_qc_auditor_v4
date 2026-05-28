#!/usr/bin/env python3
"""Build a per-task LLM audit brief.

The brief bundles everything the LLM auditor (`system_prompts/llm_auditor.md`)
needs to produce a human-accurate verdict on a single task:

- Task identity (task_id, universe, scenario, safety flag, rubric size, etc.)
- Task design (prompt, agent_objective, core_functionalities, desired_outcome)
- Deterministic verdict from audit_v2.py (if available)
- Final rubric criteria JSON
- CB per-criterion justifications JSON
- Auto-evaluator feedback (full text)
- Trajectory validator feedback
- Unit test evaluator feedback
- Model A's actual assistant turns (the file content / chat output)

Usage:
    python3 openclaw_qc_auditor/scripts/build_audit_brief.py \\
        --csv qc_reads_22_data.csv \\
        --task-id <task_id> \\
        --audits-dir openclaw_qc_auditor/results/_qcr22_audited \\
        --out openclaw_qc_auditor/results/_qcr22_audited/_brief_057ad.md

Multi-task batch:
    python3 openclaw_qc_auditor/scripts/build_audit_brief.py \\
        --csv qc_reads_22_data.csv \\
        --audits-dir openclaw_qc_auditor/results/_qcr22_audited \\
        --out-dir openclaw_qc_auditor/results/_qcr22_audited/_briefs
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

MAX_SECTION_CHARS = 30_000  # generous per-section limit; the LLM context is large enough


def trim(s: str, n: int = MAX_SECTION_CHARS) -> str:
    if not isinstance(s, str):
        return ""
    s = s.strip()
    if len(s) <= n:
        return s
    return s[:n] + f"\n\n... [truncated to {n} chars] ..."


def pretty_json(raw: str, sort_keys: bool = False) -> str:
    """Try to pretty-print a JSON string. Fall back to raw if it can't parse."""
    if not isinstance(raw, str) or not raw.strip():
        return ""
    try:
        return json.dumps(json.loads(raw), indent=2, sort_keys=sort_keys)
    except Exception:
        try:
            return json.dumps(json.loads(json.loads(raw)), indent=2, sort_keys=sort_keys)
        except Exception:
            return raw.strip()


def load_deterministic_verdict(audits_dir: Path | None, task_id: str) -> dict:
    """Pull the script's verdict (Score + tags + gap-check notes) from the
    per-task MD if it exists. Returns empty dict otherwise."""
    if audits_dir is None:
        return {}
    md = audits_dir / f"{task_id}.md"
    if not md.exists():
        return {}
    text = md.read_text()
    out = {"source_md": str(md)}
    m = re.search(r"\*\*Qc Score\*\*\s*\|\s*`(\d)`", text)
    if m:
        out["score"] = int(m.group(1))
    m = re.search(r"\*\*Selected Error Categories\*\*\s*\|\s*`([^`]+)`", text)
    if m:
        out["tags_str"] = m.group(1)
        out["tags"] = re.findall(r"\[(?:Fail|Non-Fail|Pass) - [^\]]+\]", m.group(1))
    m = re.search(r"\*\*Model A failure rate\*\*\s*\|\s*([^|\n]+)", text)
    if m:
        out["model_a_failure_rate"] = m.group(1).strip()
    # Gap-check firings block
    g_block = re.search(
        r"## v2 gap-check flags \(new in this run\)\n\n(.+?)\n\n---", text, re.DOTALL
    )
    if g_block:
        flags = []
        for ln in g_block.group(1).splitlines():
            ln = ln.strip()
            if ln.startswith("-"):
                flags.append(ln.lstrip("- ").strip())
        out["gap_flags"] = flags
    # Narrative
    n = re.search(r"## Overall Auditor Feedback\n\n```\n(.+?)\n```", text, re.DOTALL)
    if n:
        out["narrative"] = n.group(1)
    return out


def build_brief(row: pd.Series, det: dict) -> str:
    """Assemble the brief from a single CSV row and the deterministic verdict."""
    def s(field: str) -> str:
        v = row.get(field, "")
        return "" if pd.isna(v) else str(v)

    rubric_pretty = pretty_json(s("final_rubric_criteria_json"))
    justifications_pretty = pretty_json(s("rubric_justifications_breakdown_json"))
    turns_pretty = pretty_json(s("assistant_turns_by_model_json"))
    tool_runs_pretty = pretty_json(s("unit_test_tool_runs_model_a_json"))
    failing_tests_pretty = pretty_json(s("failing_tests_json"))

    det_block = "_(no deterministic verdict available)_"
    if det:
        det_block_lines = [
            f"- Deterministic Score: **{det.get('score', '?')}**",
            f"- Deterministic Tags: `{det.get('tags_str', '(none)')}`",
            f"- Model A failure rate: {det.get('model_a_failure_rate', '(n/a)')}",
        ]
        if det.get("gap_flags"):
            det_block_lines.append("- Gap-check firings (G1-G5):")
            for f in det["gap_flags"]:
                det_block_lines.append(f"  - {f}")
        if det.get("narrative"):
            det_block_lines.append("- Deterministic narrative (verbatim):")
            det_block_lines.append("```")
            det_block_lines.append(det["narrative"])
            det_block_lines.append("```")
        det_block = "\n".join(det_block_lines)

    sections = [
        f"# Audit Brief: task `{s('task_id')}`",
        "",
        f"> Source delivery row from `{row.get('__source_csv__','')}`. Use this brief together",
        f"> with the system prompt at `openclaw_qc_auditor/system_prompts/llm_auditor.md`",
        f"> to produce a human-accurate verdict.",
        "",
        "---",
        "",
        "## Task identity",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| task_id | `{s('task_id')}` |",
        f"| attempt | `{s('attempt')}` |",
        f"| assigned_universe | {s('assigned_universe')} |",
        f"| scenario_type | {s('scenario_type')} |",
        f"| reviewer_prompt_category | {s('reviewer_prompt_category')} |",
        f"| has_safety_issues | {s('has_safety_issues')} |",
        f"| safety_tier_annotation | {s('safety_tier_annotation')} |",
        f"| final_rubric_criteria_count | {s('final_rubric_criteria_count')} |",
        f"| failing_tests_count | {s('failing_tests_count')} |",
        f"| trajectory_validator_passes | {s('trajectory_validator_passes')} |",
        f"| workspace_verification_passed | {s('workspace_verification_passed')} |",
        f"| unit_test_eval_passes | {s('unit_test_eval_passes')} |",
        f"| rubric_evaluator_passes | {s('rubric_evaluator_passes')} |",
        "",
        "---",
        "",
        "## Deterministic verdict (from audit_v2.py)",
        "",
        det_block,
        "",
        "---",
        "",
        "## Task design",
        "",
        "### agent_objective",
        "",
        trim(s("agent_objective"), 4000),
        "",
        "### core_functionalities",
        "",
        trim(s("core_functionalities"), 4000),
        "",
        "### desired_outcome",
        "",
        trim(s("desired_outcome"), 4000),
        "",
        "### opening_prompt",
        "",
        trim(s("opening_prompt"), 4000),
        "",
        "---",
        "",
        "## Final rubric criteria (JSON)",
        "",
        "```json",
        trim(rubric_pretty, 12000),
        "```",
        "",
        "---",
        "",
        "## CB per-criterion justifications (JSON)",
        "",
        "```json",
        trim(justifications_pretty, 12000),
        "```",
        "",
        "---",
        "",
        "## Auto-evaluator feedback (rubric_evaluator_feedback)",
        "",
        trim(s("rubric_evaluator_feedback"), 8000),
        "",
        "---",
        "",
        "## Trajectory validator feedback",
        "",
        trim(s("trajectory_validator_feedback"), 4000),
        "",
        "---",
        "",
        "## Unit test evaluator feedback",
        "",
        trim(s("unit_test_eval_feedback"), 8000),
        "",
        "### Failing tests JSON",
        "",
        "```json",
        trim(failing_tests_pretty, 2000),
        "```",
        "",
        "---",
        "",
        "## Model A assistant turns (the actual file content / chat output)",
        "",
        "**This is the most important section for Dim 12 verification.** Read it carefully",
        "and compare against every CB-failed criterion.",
        "",
        "```json",
        trim(turns_pretty, 30000),
        "```",
        "",
        "---",
        "",
        "## Model A unit-test tool runs",
        "",
        "```json",
        trim(tool_runs_pretty, 6000),
        "```",
        "",
        "---",
        "",
        "## Reminder",
        "",
        "Apply the workflow in `openclaw_qc_auditor/system_prompts/llm_auditor.md`.",
        "Output format is `## Verdict` + `## Overall Auditor Feedback`. No closing summary.",
        "",
    ]
    return "\n".join(sections)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--csv", required=True, help="Delivery CSV path")
    p.add_argument("--task-id", default=None,
                   help="Single task id to build brief for; default = all rows in the CSV")
    p.add_argument("--audits-dir", default=None,
                   help="Optional: directory containing audit_v2.py per-task MDs "
                        "to pull the deterministic verdict from")
    p.add_argument("--out", default=None,
                   help="Output path for a single-task brief (requires --task-id)")
    p.add_argument("--out-dir", default=None,
                   help="Output dir for batch (one _brief_<task_id>.md per task)")
    args = p.parse_args()

    df = pd.read_csv(args.csv, dtype=str, keep_default_na=False)
    df["__source_csv__"] = args.csv
    audits_dir = Path(args.audits_dir) if args.audits_dir else None

    if args.task_id:
        sub = df[df["task_id"] == args.task_id]
        if sub.empty:
            sys.exit(f"task_id {args.task_id} not in {args.csv}")
        row = sub.iloc[0]
        det = load_deterministic_verdict(audits_dir, args.task_id)
        brief = build_brief(row, det)
        if args.out:
            out = Path(args.out)
        elif args.out_dir:
            out = Path(args.out_dir) / f"_brief_{args.task_id}.md"
        else:
            sys.exit("Provide --out or --out-dir")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(brief)
        print(f"[ok] Wrote {out}  ({len(brief)} chars)")
        return

    # Batch mode
    if not args.out_dir:
        sys.exit("Batch mode requires --out-dir")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n_written = 0
    for _, row in df.iterrows():
        tid = row["task_id"]
        if not tid.strip():
            continue
        det = load_deterministic_verdict(audits_dir, tid)
        brief = build_brief(row, det)
        path = out_dir / f"_brief_{tid}.md"
        path.write_text(brief)
        n_written += 1
        print(f"[ok] {path}  ({len(brief)} chars)")
    print(f"\n[ok] Wrote {n_written} briefs to {out_dir}")


if __name__ == "__main__":
    main()
