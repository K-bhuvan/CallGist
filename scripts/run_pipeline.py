#!/usr/bin/env python3
"""Run the full pipeline and email the report. Designed for cron/weekly invocation."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.config import load_config
from core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def run_full_pipeline(
    data_dir: str | None = None,
    out_dir: str | None = None,
    report_out: str | None = None,
    to_email: str | None = None,
    workers: int | None = None,
    skip_existing: bool = True,
    use_db: bool = True,
) -> tuple[str, str]:

    from core.aggregation import aggregate_week
    from core.batch import run_parallel_analysis
    from core.emailer import send_report
    from core.ingestion import load_analysis_pair, load_transcripts
    from core.models import CallAnalysis, CallRecord
    from core.reporting import generate_report

    config = load_config()

    data_path = Path(data_dir) if data_dir else ROOT / "data" / "sample_transcripts"
    output_dir = Path(out_dir) if out_dir else ROOT / "outputs" / "analyses"
    report_path = Path(report_out) if report_out else ROOT / "outputs" / "sample_report.md"
    n_workers = workers or int(config.generic.get("analysis_workers", 4))

    logger.info("Step 1/4: Loading transcripts from %s", data_path)
    records = load_transcripts(data_path)
    if not records:
        msg = "No transcripts found"
        logger.error(msg)
        return msg, ""

    logger.info("Step 2/4: Analyzing %s calls with %s workers", len(records), n_workers)
    results = run_parallel_analysis(
        records,
        config=config,
        out_dir=output_dir,
        workers=n_workers,
        skip_existing=skip_existing,
        min_chars=int(config.generic.get("min_transcript_chars", 50)),
        max_retries=int(config.generic.get("llm_max_retries", 3)),
        retry_base_delay=float(config.generic.get("llm_retry_base_delay_seconds", 1.0)),
        use_db=use_db,
    )
    failed = [r for r in results if not r.ok]
    if failed:
        logger.error("%s calls failed", len(failed))
        for item in failed:
            logger.error("  %s: %s", item.call_id, item.error)

    logger.info("Step 3/4: Aggregating and generating report")
    paths = sorted(output_dir.glob("*.json"))

    def _load(path: Path) -> tuple[CallRecord, CallAnalysis]:
        call_data, analysis_data = load_analysis_pair(path)
        return (
            CallRecord.model_validate(call_data),
            CallAnalysis.model_validate(analysis_data),
        )

    pairs = [_load(p) for p in paths]
    aggregation = aggregate_week(pairs, config=config)
    report_md = generate_report(aggregation, config=config)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_md, encoding="utf-8")

    if use_db:
        try:
            from core.db_crud import save_weekly_report
            save_weekly_report(aggregation, report_md)
        except Exception:
            logger.warning("DB persist failed", exc_info=True)

    recipient = to_email or os.getenv("REPORT_TO_EMAIL", "")
    if recipient and os.getenv("SENDGRID_API_KEY"):
        week_label = f"{aggregation.week_start.isoformat()} – {aggregation.week_end.isoformat()}"
        logger.info("Step 4/4: Emailing report to %s", recipient)
        send_report(
            to_email=recipient,
            report_markdown=report_md,
            business_name=aggregation.business_name,
            week_label=week_label,
        )
    else:
        logger.info("Step 4/4: Skipping email (REPORT_TO_EMAIL or SENDGRID_API_KEY not set)")

    return f"Report written to {report_path}", report_md


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Run full CallGist pipeline.")
    parser.add_argument("--data-dir", type=str, default=None)
    parser.add_argument("--out-dir", type=str, default=None)
    parser.add_argument("--report-out", type=str, default=None)
    parser.add_argument("--to-email", type=str, default=None)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--no-skip-existing", action="store_true")
    parser.add_argument("--no-db", action="store_true")
    args = parser.parse_args()

    msg, _ = run_full_pipeline(
        data_dir=args.data_dir,
        out_dir=args.out_dir,
        report_out=args.report_out,
        to_email=args.to_email,
        workers=args.workers,
        skip_existing=not args.no_skip_existing,
        use_db=not args.no_db,
    )
    logger.info(msg)


if __name__ == "__main__":
    main()