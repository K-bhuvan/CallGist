"""Single-call LLM analysis."""
from __future__ import annotations

import yaml

from core.config import AppConfig, load_config
from core.llm import chat_json
from core.models import CallAnalysis, CallRecord


def build_analysis_system_prompt(config: AppConfig) -> str:
    template = (config.prompts_dir / "call_analysis.md").read_text(encoding="utf-8")
    taxonomy_yaml = yaml.dump(config.taxonomy, sort_keys=False, allow_unicode=True)
    return template.replace("{{taxonomy_yaml}}", taxonomy_yaml)


def low_quality_analysis() -> CallAnalysis:
    return CallAnalysis(
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


def analyze_call(
    record: CallRecord,
    config: AppConfig | None = None,
    *,
    system_prompt: str | None = None,
    max_retries: int = 3,
    retry_base_delay: float = 1.0,
) -> CallAnalysis:
    config = config or load_config()
    system_prompt = system_prompt or build_analysis_system_prompt(config)
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
        max_retries=max_retries,
        retry_base_delay=retry_base_delay,
    )
    return CallAnalysis.model_validate(payload)
