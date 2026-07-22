#!/usr/bin/env python3
"""Analyze transcripts in parallel and save JSON results."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.batch import run_parallel_analysis
from core.config import load_config
from core.ingestion import load_transcripts
from core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze call transcripts (parallel).")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=ROOT / "data" / "sample_transcripts",
        help="Directory of .txt transcripts (+ optional .meta.json)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "outputs" / "analyses",
        help="Directory for per-call JSON output",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Parallel LLM workers (default: from configs/generic.yaml)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip calls that already have output JSON",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-analyze even if output JSON exists",
    )
    parser.add_argument(
        "--use-db",
        action="store_true",
        help="Persist results to SQLite database",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()

    min_chars = int(config.generic.get("min_transcript_chars", 50))
    workers = args.workers or int(config.generic.get("analysis_workers", 4))
    max_retries = int(config.generic.get("llm_max_retries", 3))
    retry_delay = float(config.generic.get("llm_retry_base_delay_seconds", 1.0))
    skip_existing = args.skip_existing and not args.force

    records = load_transcripts(args.data_dir)
    if not records:
        logger.error("No transcripts found in %s", args.data_dir)
        sys.exit(1)

    logger.info(
        "Analyzing %s calls with %s workers (skip_existing=%s, use_db=%s)",
        len(records),
        workers,
        skip_existing,
        args.use_db,
    )

    results = run_parallel_analysis(
        records,
        config=config,
        out_dir=args.out_dir,
        workers=workers,
        skip_existing=skip_existing,
        min_chars=min_chars,
        max_retries=max_retries,
        retry_base_delay=retry_delay,
        use_db=args.use_db,
    )

    ok = sum(1 for r in results if r.ok and not r.skipped)
    skipped = sum(1 for r in results if r.skipped)
    failed = [r for r in results if not r.ok]

    logger.info("Done: %s written, %s skipped, %s failed", ok, skipped, len(failed))
    for item in failed:
        logger.error("  %s: %s", item.call_id, item.error)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()