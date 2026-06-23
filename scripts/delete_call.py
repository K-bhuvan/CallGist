#!/usr/bin/env python3
"""Delete transcript, metadata, and analysis files for a call id."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def delete_call(call_id: str, data_dir: Path, analyses_dir: Path) -> None:
    targets = [
        data_dir / f"{call_id}.txt",
        data_dir / f"{call_id}.meta.json",
        analyses_dir / f"{call_id}.json",
    ]
    removed = []
    for path in targets:
        if path.exists():
            path.unlink()
            removed.append(str(path))
    if not removed:
        print(f"No files found for call id: {call_id}")
        sys.exit(1)
    for path in removed:
        print(f"Deleted {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete call data by id")
    parser.add_argument("call_id", help="Call id (filename stem, e.g. call_01)")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=ROOT / "data" / "sample_transcripts",
    )
    parser.add_argument(
        "--analyses-dir",
        type=Path,
        default=ROOT / "outputs" / "analyses",
    )
    args = parser.parse_args()
    delete_call(args.call_id, args.data_dir, args.analyses_dir)


if __name__ == "__main__":
    main()
