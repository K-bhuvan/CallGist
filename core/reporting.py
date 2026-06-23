"""Template-first weekly report generation."""
from __future__ import annotations

import json

from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.config import AppConfig, load_config
from core.llm import chat_json
from core.models import WeeklyAggregation


def _intent_reason(intent: str) -> str:
    reasons = {
        "new lead": "Direct impact on booked jobs and revenue.",
        "emergency request": "Urgent demand; slow response loses jobs.",
        "price question": "Pricing clarity affects conversion.",
        "appointment scheduling": "Scheduling friction blocks revenue.",
        "complaint": "Unresolved complaints hurt retention and reviews.",
    }
    return reasons.get(intent, "Frequent theme worth monitoring.")


def _llm_sections(config: AppConfig, facts: dict) -> dict:
    prompt = (config.prompts_dir / "weekly_report.md").read_text(encoding="utf-8")
    model = str(config.generic.get("llm_model", "gpt-4o-mini"))
    max_actions = int(config.generic.get("max_recommended_actions", 3))
    user = json.dumps({"facts": facts, "max_actions": max_actions}, indent=2)
    return chat_json(
        [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user},
        ],
        model=model,
    )


def generate_report(
    aggregation: WeeklyAggregation,
    config: AppConfig | None = None,
) -> str:
    config = config or load_config()
    max_top_intents = int(config.generic.get("max_top_intents", 5))
    display_intents = aggregation.top_intents[:max_top_intents]
    facts = json.loads(aggregation.model_dump_json())
    llm = _llm_sections(config, facts)

    actions = llm.get("actions") or []
    while len(actions) < 3:
        actions.append("")

    template_name = "report_template.md"
    env = Environment(
        loader=FileSystemLoader(str(config.industry_pack_dir)),
        autoescape=select_autoescape(disabled_extensions=("md",)),
    )
    template = env.get_template(template_name)

    top_intents = ", ".join(row.intent for row in display_intents[:3])
    if not top_intents:
        top_intents = "mixed topics"

    main_issue = (
        aggregation.top_pain_points[0].label
        if aggregation.top_pain_points
        else "no single recurring pain point"
    )
    issue_count = aggregation.top_pain_points[0].count if aggregation.top_pain_points else 0

    intent_rows = [
        {
            "intent": row.intent,
            "count": row.count,
            "reason": _intent_reason(row.intent),
        }
        for row in display_intents
    ]
    outcome_rows = [
        {"outcome": row.outcome, "count": row.count}
        for row in aggregation.outcome_breakdown
    ]
    pain_rows = [
        {
            "pain_point": row.label,
            "severity": row.severity,
            "evidence": row.evidence,
        }
        for row in aggregation.top_pain_points
    ]

    return template.render(
        business_name=aggregation.business_name,
        week_start=aggregation.week_start.isoformat(),
        week_end=aggregation.week_end.isoformat(),
        executive_summary=llm.get(
            "executive_summary",
            f"Customers mostly called about {top_intents}.",
        ),
        top_intents=top_intents,
        main_issue=main_issue,
        issue_count=issue_count,
        total_calls=aggregation.total_calls,
        outcome_rows=outcome_rows,
        new_leads=aggregation.new_leads,
        lost_leads=aggregation.lost_leads,
        follow_ups=aggregation.follow_ups,
        complaints=aggregation.complaints,
        intent_rows=intent_rows,
        pain_rows=pain_rows,
        revenue_leak_summary=llm.get("revenue_leak_summary", ""),
        revenue_examples=aggregation.revenue_leak_examples,
        complaint_summary=llm.get("complaint_summary", ""),
        staff_notes="\n".join(f"- {n}" for n in aggregation.staff_coaching_notes)
        or "- None noted this week.",
        action_1=actions[0],
        action_2=actions[1],
        action_3=actions[2],
        follow_up_list=aggregation.follow_up_list,
        needs_review=aggregation.needs_review,
    )

