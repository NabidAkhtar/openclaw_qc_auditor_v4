#!/usr/bin/env python3
"""Phase 2.3 — Append a freshly human-scored batch to the calibration corpus.

DRY-RUN BY DEFAULT. Pass --apply to actually write to
`audits_v2/reference/11_calibration_corpus.md`. Always prints the proposed
markdown diff first.

Usage:
    python audits_v2/scripts/append_to_corpus.py \\
        --human-csv audits_v2/results/_test_20maymid_v2/_human_scores_template.csv \\
        --batch-name "test_20maymid.csv (Round 1, May 2026)" \\
        [--apply]

The human CSV must have the same columns as the delta_report.py input
(`task_id`, `QC Score`, `Selected error categories`). The script:

1. Re-derives my locked verdicts from `--audits-dir`.
2. Joins to the human verdicts.
3. Computes per-task delta + tag F1.
4. Builds a new markdown subsection appendable to `11_calibration_corpus.md`.
5. Either prints the proposed diff (default) or appends + rewrites
   reference/11_calibration_corpus.md when you pass --apply.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

CORPUS_MD = Path("openclaw_qc_auditor/reference/11_calibration_corpus.md")
TAG_RE = re.compile(r"\[(?:Fail|Non-Fail|Pass) - [^\]]+\]")


def extract_tags(text: str) -> set[str]:
    if not isinstance(text, str):
        return set()
    return set(TAG_RE.findall(text))


def detect_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return None


def parse_audit_md(path: Path) -> tuple[int | None, set[str]]:
    text = path.read_text()
    m_s = re.search(r"\*\*Qc Score\*\*\s*\|\s*`(\d)`", text)
    m_t = re.search(r"\*\*Selected Error Categories\*\*\s*\|\s*`([^`]+)`", text)
    return (
        int(m_s.group(1)) if m_s else None,
        extract_tags(m_t.group(1) if m_t else ""),
    )


def build_section(batch_name: str, rows: list[dict]) -> str:
    today = date.today().isoformat()
    n = len(rows)
    matched = [r for r in rows if r["human_score"] is not None]
    n_m = len(matched) or 1
    exact = sum(1 for r in matched if r["delta"] == 0)
    within1 = sum(1 for r in matched if r["delta"] is not None and abs(r["delta"]) <= 1)
    score_count = Counter(r["human_score"] for r in matched)

    lines = [
        "",
        "---",
        "",
        f"## Round added on {today} — `{batch_name}`",
        "",
        f"**Tasks:** {n}  (matched human verdicts: {len(matched)})",
        f"**My locked exact match:** {exact}/{n_m} ({100*exact/n_m:.0f}%)  "
        f"**Within 1:** {within1}/{n_m} ({100*within1/n_m:.0f}%)",
        "",
        "### Ground-truth verdicts (for self-check on future audits)",
        "",
        "| Task ID | Human Score | Human Tags |",
        "|---|---|---|",
    ]
    for r in rows:
        hs = r["human_score"] if r["human_score"] is not None else "?"
        ht = ", ".join(sorted(r["human_tags"])) or "*(none)*"
        lines.append(f"| `{r['task_id']}` | **{hs}** | {ht} |")

    lines += ["", "### Score distribution (this round)", "",
              "| Score | Count | Share |", "|---|---|---|"]
    for s in (5, 4, 3, 2, 1):
        c = score_count.get(s, 0)
        lines.append(f"| {s} | {c} | {100*c/n_m:.0f}% |")

    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--audits-dir", required=True,
                   help="Directory containing locked per-task .md files")
    p.add_argument("--human-csv", required=True,
                   help="CSV with task_id + QC Score + Selected error categories")
    p.add_argument("--batch-name", required=True,
                   help="Human-readable batch name for the corpus header")
    p.add_argument("--apply", action="store_true",
                   help="Write to 11_calibration_corpus.md (default: dry-run + print)")
    args = p.parse_args()

    aud_dir = Path(args.audits_dir)
    human_df = pd.read_csv(args.human_csv, dtype=str, keep_default_na=False)

    id_col = detect_col(human_df, ["task_id", "Task ID", "taskId"])
    sc_col = detect_col(human_df, ["QC Score", "qc_score", "Final Score", "score"])
    tg_col = detect_col(human_df, ["Selected error categories",
                                   "Selected Error Categories",
                                   "selected_error_categories", "tags"])
    if not id_col or not sc_col:
        raise SystemExit(
            f"Human CSV missing required cols. id={id_col!r} sc={sc_col!r}"
        )

    human_map = {}
    for _, r in human_df.iterrows():
        tid = r[id_col].strip()
        if not tid: continue
        try:
            hs = int(r[sc_col])
        except (TypeError, ValueError):
            hs = None
        human_map[tid] = {
            "score": hs,
            "tags": extract_tags(r[tg_col]) if tg_col else set(),
        }

    rows = []
    for md in sorted(aud_dir.glob("*.md")):
        if md.name.startswith("_"): continue
        tid = md.stem
        my_score, my_tags = parse_audit_md(md)
        h = human_map.get(tid, {"score": None, "tags": set()})
        delta = (my_score - h["score"]) if (my_score is not None and h["score"] is not None) else None
        rows.append({
            "task_id": tid,
            "my_score": my_score,
            "my_tags": my_tags,
            "human_score": h["score"],
            "human_tags": h["tags"],
            "delta": delta,
        })

    section = build_section(args.batch_name, rows)

    if args.apply:
        if not CORPUS_MD.exists():
            raise SystemExit(f"Corpus not found at {CORPUS_MD}")
        with CORPUS_MD.open("a") as f:
            f.write(section)
        print(f"[ok] Appended {len(rows)} tasks to {CORPUS_MD}")
    else:
        print("[dry-run] Proposed section to append to 11_calibration_corpus.md:")
        print("=" * 80)
        print(section)
        print("=" * 80)
        print("\nPass --apply to write.")


if __name__ == "__main__":
    main()
