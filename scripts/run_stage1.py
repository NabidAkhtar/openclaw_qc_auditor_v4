#!/usr/bin/env python3
"""One-shot Stage 1 wrapper: signals + deterministic audit + LLM briefs.

Runs the three preparatory scripts in order so a user only needs one
command before dispatching Stage 2 LLM subagents.

Usage:
    python scripts/run_stage1.py <delivery.csv> <batch_name>

Example:
    python scripts/run_stage1.py qcr22.csv qcr22
    # produces:
    #   results/_signals_qcr22/<task_id>.json
    #   results/_qcr22_audited/<task_id>.md                  (deterministic verdicts)
    #   results/_qcr22_audited/_summary.md                   (batch summary)
    #   results/_qcr22_audited/_briefs/_brief_<task_id>.md   (Stage 2 input)

Run this script from the openclaw_qc_auditor_v1.1 folder root.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    print(f"\n>>> {' '.join(cmd)}")
    r = subprocess.run(cmd, check=False)
    if r.returncode != 0:
        sys.exit(f"[err] Command failed with exit code {r.returncode}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv_path", help="Delivery CSV (or output of prepare_input.py).")
    p.add_argument("batch_name",
                   help="Short name used in result subfolders (e.g. 'qcr22').")
    p.add_argument("--results-root", default="results",
                   help="Override the results root directory. Default: results/")
    args = p.parse_args()

    results_root = Path(args.results_root)
    signals_dir = results_root / f"_signals_{args.batch_name}"
    audited_dir = results_root / f"_{args.batch_name}_audited"
    briefs_dir = audited_dir / "_briefs"
    verdicts_dir = audited_dir / "_llm_verdicts"

    py = sys.executable

    run([py, str(HERE / "extract_signals.py"), args.csv_path,
         "--out-dir", str(signals_dir)])

    run([py, str(HERE / "audit_v2.py"), args.csv_path, str(signals_dir),
         "--out-dir", str(audited_dir)])

    run([py, str(HERE / "build_audit_brief.py"),
         "--csv", args.csv_path,
         "--audits-dir", str(audited_dir),
         "--out-dir", str(briefs_dir)])

    verdicts_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[done] Stage 1 complete.")
    print(f"  Signals:           {signals_dir}/")
    print(f"  Deterministic MDs: {audited_dir}/")
    print(f"  LLM briefs:        {briefs_dir}/")
    print(f"  Stage 2 verdicts:  {verdicts_dir}/  (empty, populated by LLM subagents)")
    print(f"\nNext: dispatch one LLM subagent per task. See SETUP_GUIDE.md.")


if __name__ == "__main__":
    main()
