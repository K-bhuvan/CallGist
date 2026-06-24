"""Load transcript files and optional metadata sidecars."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from core.config import project_root
from core.models import CallRecord


def _parse_date(value: object | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _relative_source_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root().resolve()))
    except ValueError:
        return str(path)


def load_transcripts(directory: Path) -> list[CallRecord]:
    directory = Path(directory)
    records: list[CallRecord] = []
    for txt_path in sorted(directory.glob("*.txt")):
        call_id = txt_path.stem
        text = txt_path.read_text(encoding="utf-8")
        meta_path = txt_path.with_suffix(".meta.json")
        call_date: date | None = None
        direction: str | None = None
        staff_name: str | None = None
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            call_date = _parse_date(meta.get("call_date"))
            direction = meta.get("direction")
            staff_name = meta.get("staff_name")
        records.append(
            CallRecord(
                call_id=call_id,
                transcript_text=text,
                call_date=call_date,
                direction=direction,
                staff_name=staff_name,
                source_path=_relative_source_path(txt_path),
            )
        )
    return records


def load_analysis_pair(path: Path) -> tuple[dict, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["call"], data["analysis"]
