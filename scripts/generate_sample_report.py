#!/usr/bin/env python3
"""Load saved analyses, aggregate the week, and write sample_report.md."""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.aggregation import aggregate_week
from core.config import load_config
from core.ingestion import load_analysis_pair
from core.models import CallAnalysis, CallRecord
from core.reporting import generate_report
from core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def load_pairs(
    analyses_dir: Path,
    *,
    workers: int = 8,
) -> list[tuple[CallRecord, CallAnalysis]]:
    paths = sorted(analyses_dir.glob("*.json"))
    if not paths:
        return []

    workers = max(1, min(workers, len(paths)))

    def _load(path: Path) -> tuple[CallRecord, CallAnalysis]:
        call_data, analysis_data = load_analysis_pair(path)
        return (
            CallRecord.model_validate(call_data),
            CallAnalysis.model_validate(analysis_data),
        )

    if workers == 1 or len(paths) < 4:
        return [_load(p) for p in paths]

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(_load, paths))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekly report from analyses.")
    parser.add_argument(
        "--analyses-dir",
        type=Path,
        default=ROOT / "outputs" / "analyses",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "outputs" / "sample_report.md",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Parallel JSON loaders (default: configs/generic.yaml report_load_workers)",
    )
    parser.add_argument(
        "--use-db",
        action="store_true",
        help="Persist report to SQLite database",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()
    workers = args.workers or int(config.generic.get("report_load_workers", 8))

    logger.info("Loading analyses from %s", args.analyses_dir)
    pairs = load_pairs(args.analyses_dir, workers=workers)
    if not pairs:
        logger.error("No analyses in %s. Run scripts/run_analysis.py first.", args.analyses_dir)
        sys.exit(1)

    logger.info("Loaded %s calls — aggregating", len(pairs))
    aggregation = aggregate_week(pairs, config=config)

    logger.info("Generating report")
    report_md = generate_report(aggregation, config=config)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report_md, encoding="utf-8")
    logger.info("Wrote %s", args.out)

    if args.use_db:
        try:
            from core.db_crud import save_weekly_report
            save_weekly_report(aggregation, report_md)
            logger.info("Persisted report to DB")
        except Exception:
            logger.warning("Failed to persist report to DB", exc_info=True)


if __name__ == "__main__":
    main()