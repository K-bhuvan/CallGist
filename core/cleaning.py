"""Transcript cleaning and quality checks."""
from __future__ import annotations

import re

from core.models import CallRecord


def clean_transcript(text: str) -> str:
    text = text.replace("\r\n", "\n").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def apply_cleaning(record: CallRecord, min_chars: int) -> CallRecord:
    cleaned = clean_transcript(record.transcript_text)
    low_quality = len(cleaned) < min_chars
    note = "Transcript too short for reliable analysis" if low_quality else None
    return record.model_copy(
        update={
            "transcript_text": cleaned,
            "low_quality": low_quality,
            "quality_note": note,
        }
    )
