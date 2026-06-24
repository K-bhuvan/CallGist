"""Parallel batch analysis for production-scale call volumes."""
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from core.analysis import analyze_call, build_analysis_system_prompt, low_quality_analysis
from core.cleaning import apply_cleaning
from core.config import AppConfig
from core.models import CallRecord

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    call_id: str
    ok: bool
    skipped: bool
    out_path: Path | None
    error: str | None = None


def _write_payload(out_path: Path, record: CallRecord, analysis) -> None:
    payload = {
        "call": record.model_dump(mode="json"),
        "analysis": analysis.model_dump(mode="json"),
    }
    tmp_path = out_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp_path.replace(out_path)


def analyze_one(
    record: CallRecord,
    *,
    config: AppConfig,
    system_prompt: str,
    min_chars: int,
    out_dir: Path,
    skip_existing: bool,
    max_retries: int,
    retry_base_delay: float,
) -> AnalysisResult:
    out_path = out_dir / f"{record.call_id}.json"
    if skip_existing and out_path.exists():
        return AnalysisResult(
            call_id=record.call_id,
            ok=True,
            skipped=True,
            out_path=out_path,
        )

    record = apply_cleaning(record, min_chars)
    try:
        if record.low_quality:
            analysis = low_quality_analysis()
        else:
            analysis = analyze_call(
                record,
                config=config,
                system_prompt=system_prompt,
                max_retries=max_retries,
                retry_base_delay=retry_base_delay,
            )
        _write_payload(out_path, record, analysis)
        return AnalysisResult(
            call_id=record.call_id,
            ok=True,
            skipped=False,
            out_path=out_path,
        )
    except Exception as exc:
        logger.exception("Failed %s", record.call_id)
        return AnalysisResult(
            call_id=record.call_id,
            ok=False,
            skipped=False,
            out_path=None,
            error=str(exc),
        )


def run_parallel_analysis(
    records: list[CallRecord],
    *,
    config: AppConfig,
    out_dir: Path,
    workers: int,
    skip_existing: bool,
    min_chars: int,
    max_retries: int,
    retry_base_delay: float,
) -> list[AnalysisResult]:
    if not records:
        return []

    out_dir.mkdir(parents=True, exist_ok=True)
    system_prompt = build_analysis_system_prompt(config)
    workers = max(1, min(workers, len(records)))
    total = len(records)
    completed = 0

    results: list[AnalysisResult] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                analyze_one,
                record,
                config=config,
                system_prompt=system_prompt,
                min_chars=min_chars,
                out_dir=out_dir,
                skip_existing=skip_existing,
                max_retries=max_retries,
                retry_base_delay=retry_base_delay,
            ): record.call_id
            for record in records
        }
        for future in as_completed(futures):
            call_id = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                logger.exception("Worker crashed for %s", call_id)
                results.append(
                    AnalysisResult(
                        call_id=call_id,
                        ok=False,
                        skipped=False,
                        out_path=None,
                        error=str(exc),
                    )
                )
            completed += 1
            if completed % 10 == 0 or completed == total:
                logger.info("Progress: %s/%s calls", completed, total)
    return results
