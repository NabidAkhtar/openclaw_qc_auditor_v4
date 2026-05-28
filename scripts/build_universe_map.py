#!/usr/bin/env python3
"""Build the task_id -> universe-snapshot-path mapping for a batch.

Reads the input CSV's `assigned_universe` column and looks up each persona's
snapshot directory in `L12_universes/extracted/<persona>/`. Writes the JSON
mapping that build_subagent_prompts.py expects.

Usage:
    python scripts/build_universe_map.py <csv_path> <batch_name> \\
        [--universes-root /Users/.../L12_universes/extracted]

Output:
    results/_<batch>_audited/_task_to_universe.json
    + prints any missing personas so you know what to extract.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

csv.field_size_limit(sys.maxsize)

# Default: universes/ co-located inside the v4 folder (portable).
# Fall back to the legacy L12_universes/extracted/ path if `universes/` is empty.
_HERE = Path(__file__).resolve().parent.parent
DEFAULT_UNIVERSES = _HERE / "universes"
_LEGACY_UNIVERSES = Path(
    "/Users/vishal.kushwaha/Documents/Openclaw_RL copy/L12_universes/extracted"
)
if not DEFAULT_UNIVERSES.exists() or not any(DEFAULT_UNIVERSES.iterdir()):
    if _LEGACY_UNIVERSES.exists():
        DEFAULT_UNIVERSES = _LEGACY_UNIVERSES


def normalize(persona_field: str) -> str:
    """Strip emoji and normalize 'Amanda Evans' / '👤 amanda evans' -> 'amanda_evans'."""
    for emoji in ("👤", "💰", "🍽️"):
        persona_field = persona_field.replace(emoji, "")
    return persona_field.strip().replace(" ", "_").lower()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv_path")
    p.add_argument("batch_name")
    p.add_argument("--universes-root", default=str(DEFAULT_UNIVERSES))
    args = p.parse_args()

    root = Path(args.universes_root)
    if not root.exists():
        sys.exit(f"[err] universes-root not found: {root}")

    rows = list(csv.DictReader(open(args.csv_path, encoding="utf-8")))
    mapping: dict[str, str] = {}
    missing: Counter = Counter()

    for r in rows:
        tid = r["task_id"]
        persona = normalize(r["assigned_universe"])
        pdir = root / persona
        snaps = (
            [d for d in pdir.iterdir() if d.is_dir() and d.name.startswith("snapshot-openclaw-")]
            if pdir.exists()
            else []
        )
        if snaps:
            mapping[tid] = str(snaps[0].resolve())
        else:
            missing[persona] += 1

    out_dir = Path("results") / f"_{args.batch_name}_audited"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "_task_to_universe.json"
    out_path.write_text(json.dumps(mapping, indent=2))

    print(f"[ok] mapped {len(mapping)}/{len(rows)} tasks -> {out_path}")
    if missing:
        print(f"\nMissing personas ({sum(missing.values())} tasks):")
        for persona, count in missing.most_common():
            print(f"  {persona}: {count} tasks")
        print(
            "\nProvide universe data and re-run. Until then those tasks "
            "will not be audited."
        )


if __name__ == "__main__":
    main()
