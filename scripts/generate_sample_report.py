#!/usr/bin/env python3
"""Load saved analyses, aggregate the week, and write sample_report.md."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.aggregation import aggregate_week
from core.config import load_config
from core.models import CallAnalysis, CallRecord
from core.reporting import generate_report


def load_pairs(analyses_dir: Path) -> list[tuple[CallRecord, CallAnalysis]]:
    pairs: list[tuple[CallRecord, CallAnalysis]] = []
    for path in sorted(analyses_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        record = CallRecord.model_validate(data["call"])
        analysis = CallAnalysis.model_validate(data["analysis"])
        pairs.append((record, analysis))
    return pairs


def main() -> None:
    config = load_config()
    analyses_dir = ROOT / "outputs" / "analyses"
    pairs = load_pairs(analyses_dir)
    if not pairs:
        print(f"No analyses in {analyses_dir}. Run scripts/run_analysis.py first.")
        sys.exit(1)

    aggregation = aggregate_week(pairs, config=config)
    report_md = generate_report(aggregation, config=config)
    out_path = ROOT / "outputs" / "sample_report.md"
    out_path.write_text(report_md, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
