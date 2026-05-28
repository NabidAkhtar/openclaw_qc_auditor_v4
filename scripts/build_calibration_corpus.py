#!/usr/bin/env python3
"""Rebuild openclaw_qc_auditor/reference/11_calibration_corpus.md from qc_reads 2 weeks.csv.

Refresh helper. Re-run when new QC audit data is added to the corpus CSV.

Usage:
    python openclaw_qc_auditor/scripts/build_calibration_corpus.py
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

CORPUS_CSV = Path("qc_reads 2 weeks.csv")
OUT_MD = Path("openclaw_qc_auditor/reference/11_calibration_corpus.md")
OUT_JSON = Path("openclaw_qc_auditor/results/_corpus/qc_corpus.json")


def load_corpus() -> list[dict]:
    if not CORPUS_CSV.exists():
        raise SystemExit(f"Corpus not found at {CORPUS_CSV}")
    df = pd.read_csv(CORPUS_CSV, dtype=str, keep_default_na=False)
    out = []
    for _, r in df.iterrows():
        out.append({
            "task_id": r["Task ID"],
            "attempt": r["Attempt ID"],
            "score": r["QC Score"],
            "feedback": r["Overall Auditor feedback"],
            "tags": r["Selected error categories"],
            "auditor": r["Auditor"],
        })
    return out


def tag_freq(records: list[dict]) -> Counter:
    c = Counter()
    for r in records:
        for m in re.findall(r"\[(Fail|Non-Fail|Pass) - ([^\]]+)\]", r["tags"]):
            c[f"[{m[0]} - {m[1]}]"] += 1
    return c


def score_stats(records: list[dict]) -> dict:
    by_score = {}
    for r in records:
        by_score.setdefault(r["score"], []).append(r)
    return by_score


def main() -> None:
    records = load_corpus()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"[ok] Wrote {len(records)} records to {OUT_JSON}")

    freq = tag_freq(records)
    by_score = score_stats(records)

    # Build the markdown
    n_total = len(records)
    print(f"\n=== Corpus summary ({n_total} audits) ===")
    for s in sorted(by_score):
        print(f"  Score {s}: {len(by_score[s])} ({100*len(by_score[s])/n_total:.0f}%)")

    print("\n=== Tag frequency ===")
    for tag, n in sorted(freq.items(), key=lambda x: (-x[1], x[0])):
        bucket = "COMMON" if n >= 5 else ("OCCASIONAL" if n >= 2 else "RARE")
        print(f"  {n:>2}x [{bucket}] {tag}")

    print(f"\n[note] To update {OUT_MD}, edit by hand using these stats; this script")
    print("       only refreshes the JSON dump. The MD doc has handcrafted worked examples.")


if __name__ == "__main__":
    main()
