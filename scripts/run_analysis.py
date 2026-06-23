#!/usr/bin/env python3
"""Analyze all sample transcripts and save JSON results."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.analysis import analyze_call
from core.cleaning import apply_cleaning
from core.config import load_config
from core.ingestion import load_transcripts
from core.models import CallAnalysis


def main() -> None:
    config = load_config()
    min_chars = int(config.generic.get("min_transcript_chars", 50))
    data_dir = ROOT / "data" / "sample_transcripts"
    out_dir = ROOT / "outputs" / "analyses"
    out_dir.mkdir(parents=True, exist_ok=True)

    records = load_transcripts(data_dir)
    if not records:
        print(f"No transcripts found in {data_dir}")
        sys.exit(1)

    for record in records:
        record = apply_cleaning(record, min_chars)
        if record.low_quality:
            analysis = CallAnalysis(
                summary="Transcript too short to analyze reliably.",
                primary_intent="unknown",
                secondary_intents=[],
                pain_points=[],
                outcome="no clear outcome",
                follow_up_needed=False,
                follow_up_reason=None,
                lead_quality="not_applicable",
                customer_sentiment="neutral",
                staff_coaching_notes=[],
                confidence_score=0.0,
            )
        else:
            print(f"Analyzing {record.call_id}...")
            analysis = analyze_call(record, config)

        payload = {
            "call": record.model_dump(mode="json"),
            "analysis": analysis.model_dump(mode="json"),
        }
        out_path = out_dir / f"{record.call_id}.json"
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
