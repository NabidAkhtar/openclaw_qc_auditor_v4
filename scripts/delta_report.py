#!/usr/bin/env python3
"""Phase 2.1 delta report — compare locked v2 audits to human-reviewer scores.

Usage:
    python audits_v2/scripts/delta_report.py \\
        --audits-dir audits_v2/results/_20_may_l0_v2 \\
        --human-csv  <human_scored.csv> \\
        --out        audits_v2/results/_20_may_l0_v2/_delta_report.md

The human CSV must have at least:
    - a task-id column (any of: `task_id`, `Task ID`, `taskId`)
    - a score column   (any of: `QC Score`, `qc_score`, `Final Score`, `score`)
    - a tags column    (any of: `Selected error categories`,
                          `Selected Error Categories`, `selected_error_categories`,
                          `tags`)

Outputs:
    - A side-by-side delta MD report.
    - Computes exact-match %, within-1 %, off-by-2+ %, average tag F1,
      per-tag precision/recall.
    - Buckets mismatches into: my-5-vs-human-low (missed Non-Fail),
      my-low-vs-human-5 (over-flagged), tag-mismatch-same-score (discipline).
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

TAG_RE = re.compile(r"\[(?:Fail|Non-Fail|Pass) - [^\]]+\]")


def detect_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return None


def extract_tags(text: str) -> set[str]:
    if not isinstance(text, str):
        return set()
    return set(TAG_RE.findall(text))


def parse_audit_md(path: Path) -> dict:
    text = path.read_text()
    m_s = re.search(r"\*\*Qc Score\*\*\s*\|\s*`(\d)`", text)
    m_t = re.search(r"\*\*Selected Error Categories\*\*\s*\|\s*`([^`]+)`", text)
    return {
        "score": int(m_s.group(1)) if m_s else None,
        "tags": extract_tags(m_t.group(1) if m_t else ""),
    }


def f1_metrics(mine: set[str], human: set[str]) -> dict:
    if not mine and not human:
        return {"p": 1.0, "r": 1.0, "f1": 1.0, "tp": 0, "fp": 0, "fn": 0}
    tp = len(mine & human)
    fp = len(mine - human)
    fn = len(human - mine)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"p": p, "r": r, "f1": f, "tp": tp, "fp": fp, "fn": fn}


def bucket(my_score: int, human_score: int, my_tags: set[str], human_tags: set[str]) -> str:
    if my_score == human_score and my_tags != human_tags:
        return "tag_mismatch_same_score"
    if my_score == 5 and human_score <= 4:
        return "my_5_human_lower (missed Non-Fail)"
    if my_score <= 4 and human_score == 5:
        return "my_lower_human_5 (over-flagged)"
    if my_score == human_score:
        return "exact"
    return f"score_delta_{my_score - human_score:+d}"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--audits-dir", required=True)
    p.add_argument("--human-csv", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    aud_dir = Path(args.audits_dir)
    human_df = pd.read_csv(args.human_csv, dtype=str, keep_default_na=False)

    id_col = detect_col(human_df, ["task_id", "Task ID", "taskId", "task id"])
    sc_col = detect_col(human_df, ["QC Score", "qc_score", "Final Score",
                                   "score", "Score"])
    tag_col = detect_col(human_df, ["Selected error categories",
                                    "Selected Error Categories",
                                    "selected_error_categories",
                                    "tags", "Tags"])
    if not id_col or not sc_col:
        raise SystemExit(
            f"Human CSV missing required columns. "
            f"Found: id={id_col!r}, score={sc_col!r}, tags={tag_col!r}\n"
            f"Columns present: {list(human_df.columns)}"
        )

    human_map = {}
    for _, r in human_df.iterrows():
        tid = r[id_col].strip()
        if not tid:
            continue
        score = r[sc_col].strip()
        try:
            score_int = int(score)
        except (TypeError, ValueError):
            score_int = None
        human_map[tid] = {
            "score": score_int,
            "tags": extract_tags(r[tag_col]) if tag_col else set(),
        }

    rows = []
    for md in sorted(aud_dir.glob("*.md")):
        if md.name.startswith("_"):
            continue
        tid = md.stem
        mine = parse_audit_md(md)
        h = human_map.get(tid)
        if h is None:
            rows.append({"task_id": tid, "missing_human": True, **mine})
            continue
        f = f1_metrics(mine["tags"], h["tags"])
        delta = None
        if mine["score"] is not None and h["score"] is not None:
            delta = mine["score"] - h["score"]
        rows.append({
            "task_id": tid,
            "missing_human": False,
            "my_score": mine["score"],
            "human_score": h["score"],
            "delta": delta,
            "my_tags": sorted(mine["tags"]),
            "human_tags": sorted(h["tags"]),
            **f,
            "bucket": bucket(mine["score"] or 0, h["score"] or 0,
                             mine["tags"], h["tags"]),
        })

    matched = [r for r in rows if not r.get("missing_human")]
    missing = [r for r in rows if r.get("missing_human")]
    n = len(matched) or 1

    exact = sum(1 for r in matched if r["delta"] == 0)
    within1 = sum(1 for r in matched if r["delta"] is not None and abs(r["delta"]) <= 1)
    out2 = sum(1 for r in matched if r["delta"] is not None and abs(r["delta"]) >= 2)
    avg_f1 = sum(r["f1"] for r in matched) / n
    avg_p = sum(r["p"] for r in matched) / n
    avg_r = sum(r["r"] for r in matched) / n

    bucket_count = Counter(r["bucket"] for r in matched)
    fp_tag_count = Counter()
    fn_tag_count = Counter()
    for r in matched:
        fp_tag_count.update(set(r["my_tags"]) - set(r["human_tags"]))
        fn_tag_count.update(set(r["human_tags"]) - set(r["my_tags"]))

    lines = [
        "# Phase 2.1 Delta Report",
        "",
        f"**Locked audits dir:** `{aud_dir}`",
        f"**Human-scored CSV:** `{args.human_csv}`",
        f"**Matched tasks:** {len(matched)}  (missing human row: {len(missing)})",
        "",
        "## Calibration metrics",
        "",
        "| Metric | Value | Target (corpus) |",
        "|---|---|---|",
        f"| Exact score match | {exact}/{len(matched)} ({100*exact/n:.0f}%) | {93}% |",
        f"| Within 1 score point | {within1}/{len(matched)} ({100*within1/n:.0f}%) | 100% |",
        f"| Off by 2+ | {out2}/{len(matched)} ({100*out2/n:.0f}%) | 0% |",
        f"| Avg tag F1 | {avg_f1:.2f} | 0.93 |",
        f"| Avg tag precision | {avg_p:.2f} | — |",
        f"| Avg tag recall | {avg_r:.2f} | — |",
        "",
        "## Per-task table",
        "",
        "| Task ID | My | Human | Δ | F1 | My-only tags | Human-only tags | Bucket |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in matched:
        fp = ", ".join(sorted(set(r["my_tags"]) - set(r["human_tags"]))) or "—"
        fn = ", ".join(sorted(set(r["human_tags"]) - set(r["my_tags"]))) or "—"
        delta_str = "?" if r["delta"] is None else str(r["delta"])
        lines.append(
            f"| `{r['task_id']}` | {r['my_score']} | {r['human_score']} | {delta_str} | {r['f1']:.2f} | {fp} | {fn} | {r['bucket']} |"
        )

    if missing:
        lines += ["", "## Tasks with no human row", ""]
        for r in missing:
            lines.append(f"- `{r['task_id']}`")

    lines += ["", "## Bucket frequency", "", "| Bucket | Count |", "|---|---|"]
    for b, c in bucket_count.most_common():
        lines.append(f"| {b} | {c} |")

    lines += ["", "## Tag-level errors", "",
              "### My false-positive tags (I emitted, human did not)",
              "",
              "| Tag | Count |", "|---|---|"]
    for t, c in fp_tag_count.most_common():
        lines.append(f"| `{t}` | {c} |")

    lines += ["", "### Tags I missed (human emitted, I did not)",
              "",
              "| Tag | Count |", "|---|---|"]
    for t, c in fn_tag_count.most_common():
        lines.append(f"| `{t}` | {c} |")

    Path(args.out).write_text("\n".join(lines))
    print(f"[ok] Wrote {args.out}")
    print()
    print(f"Exact match: {exact}/{len(matched)} ({100*exact/n:.0f}%)")
    print(f"Within 1:    {within1}/{len(matched)} ({100*within1/n:.0f}%)")
    print(f"Off by 2+:   {out2}/{len(matched)} ({100*out2/n:.0f}%)")
    print(f"Avg tag F1:  {avg_f1:.2f}")
    if missing:
        print(f"Skipped (no human row): {len(missing)}")


if __name__ == "__main__":
    main()
