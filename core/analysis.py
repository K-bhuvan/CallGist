"""Single-call LLM analysis."""
from __future__ import annotations

import yaml

from core.config import AppConfig, load_config
from core.llm import chat_json
from core.models import CallAnalysis, CallRecord


def analyze_call(
    record: CallRecord,
    config: AppConfig | None = None,
) -> CallAnalysis:
    config = config or load_config()
    template = (config.prompts_dir / "call_analysis.md").read_text(encoding="utf-8")
    taxonomy_yaml = yaml.dump(config.taxonomy, sort_keys=False, allow_unicode=True)
    system_prompt = template.replace("{{taxonomy_yaml}}", taxonomy_yaml)
    user_prompt = (
        f"Call ID: {record.call_id}\n"
        f"Call date: {record.call_date or 'unknown'}\n"
        f"Direction: {record.direction or 'unknown'}\n"
        f"Staff: {record.staff_name or 'unknown'}\n\n"
        f"Transcript:\n{record.transcript_text}"
    )
    model = str(config.generic.get("llm_model", "gpt-4o-mini"))
    payload = chat_json(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
    )
    return CallAnalysis.model_validate(payload)
