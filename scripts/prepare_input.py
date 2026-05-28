#!/usr/bin/env python3
"""Convert a Datacompass xlsx export into the canonical delivery CSV.

Datacompass exports its delivery data as `.xlsx`. The audit pipeline reads
CSV. This converter normalizes the xlsx into a UTF-8 CSV with the same
column order. JSON-bearing cells are preserved verbatim.

Usage:
    python scripts/prepare_input.py <input.xlsx> <output.csv>

Example:
    python scripts/prepare_input.py \\
        ~/Downloads/QC_reads_22.xlsx \\
        QC_reads_22.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("xlsx_path", help="Datacompass xlsx export.")
    p.add_argument("csv_path", help="Output CSV path.")
    p.add_argument("--sheet", default=0,
                   help="Sheet name or 0-indexed position. Defaults to first sheet.")
    args = p.parse_args()

    xlsx = Path(args.xlsx_path)
    if not xlsx.exists():
        sys.exit(f"[err] File not found: {xlsx}")
    if xlsx.suffix.lower() not in {".xlsx", ".xlsm"}:
        sys.exit(f"[err] Expected .xlsx, got {xlsx.suffix}")

    try:
        sheet = int(args.sheet)
    except (TypeError, ValueError):
        sheet = args.sheet

    df = pd.read_excel(xlsx, sheet_name=sheet, dtype=str, keep_default_na=False)
    df.to_csv(args.csv_path, index=False)

    print(f"[ok] {xlsx.name} -> {args.csv_path}")
    print(f"     Rows: {len(df)}  Cols: {len(df.columns)}")
    if "task_id" in df.columns:
        print(f"     Tasks: {len(df['task_id'].dropna().unique())}")


if __name__ == "__main__":
    main()
