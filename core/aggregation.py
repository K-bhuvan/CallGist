"""Weekly aggregation from per-call analyses."""
from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Iterable

from core.config import AppConfig, load_config
from core.models import (
    CallAnalysis,
    CallRecord,
    FollowUpItem,
    IntentCount,
    NeedsReviewItem,
    OutcomeCount,
    PainPointAgg,
    RevenueLeakExample,
    WeeklyAggregation,
)
from core import rules


def _severity_rank(severity: str) -> int:
    return {"low": 1, "medium": 2, "high": 3}.get(severity, 0)


def _suggested_follow_up_action(analysis: CallAnalysis) -> str:
    intent = analysis.primary_intent
    outcome = analysis.outcome

    if intent in ("complaint", "refund request") or outcome == "complaint unresolved":
        return "Escalate to a manager and confirm a resolution plan with the customer."
    if intent in ("new lead", "emergency request") and outcome == "lead lost":
        return "Call back with clear pricing and availability to try to recover the job."
    if intent == "price question":
        return "Follow up with transparent pricing and explain which promotions apply."
    if intent == "follow-up request" or outcome == "follow-up needed":
        return "Complete the promised callback or quote before the customer's deadline."
    if intent in ("appointment scheduling", "rescheduling") and outcome == "booked appointment":
        return "Send appointment confirmation and any prep instructions."
    if outcome in ("quote requested", "booked appointment") and intent == "new lead":
        return "Deliver the promised estimate email or confirm the on-site quote visit."
    if intent == "cancellation":
        return "Offer to hold a placeholder date or send a link to reschedule when ready."
    if intent == "service status question":
        return "Proactively text job status so the customer does not need to call again."
    return "Reach out to complete the open item from this call."


def aggregate_week(
    items: Iterable[tuple[CallRecord, CallAnalysis]],
    *,
    config: AppConfig | None = None,
    business_name: str | None = None,
    week_start: date | None = None,
    week_end: date | None = None,
) -> WeeklyAggregation:
    config = config or load_config()
    threshold = float(config.generic.get("confidence_threshold", 0.7))
    max_top_intents = int(config.generic.get("max_top_intents", 5))
    max_staff_notes = int(config.generic.get("max_staff_coaching_notes", 5))
    business_name = business_name or str(
        config.industry_config.get("default_business_name", "Business")
    )
    pairs = list(items)
    dates = [record.call_date for record, _ in pairs if record.call_date]
    if week_start is None:
        week_start = min(dates) if dates else date.today()
    if week_end is None:
        week_end = max(dates) if dates else week_start

    action_rules = config.action_rules
    intent_counter: Counter[str] = Counter()
    outcome_counter: Counter[str] = Counter()
    pain_counter: Counter[str] = Counter()
    pain_samples: dict[str, PainPointAgg] = {}
    note_counter: Counter[str] = Counter()
    revenue_examples: list[RevenueLeakExample] = []
    follow_up_list: list[FollowUpItem] = []
    needs_review: list[NeedsReviewItem] = []

    new_leads = 0
    lost_leads = 0
    follow_ups = 0
    complaints = 0

    for record, analysis in pairs:
        outcome_counter[analysis.outcome] += 1
        if record.low_quality:
            needs_review.append(
                NeedsReviewItem(
                    call_id=record.call_id,
                    issue=record.quality_note or "Low quality transcript",
                    confidence=analysis.confidence_score,
                )
            )

        confident = analysis.confidence_score >= threshold and not record.low_quality
        if not confident and not record.low_quality:
            needs_review.append(
                NeedsReviewItem(
                    call_id=record.call_id,
                    issue="Low confidence classification",
                    confidence=analysis.confidence_score,
                )
            )

        if confident:
            intent_counter[analysis.primary_intent] += 1
            for pain in analysis.pain_points:
                pain_counter[pain.label] += 1
                existing = pain_samples.get(pain.label)
                if existing is None or _severity_rank(pain.severity) >= _severity_rank(
                    existing.severity
                ):
                    pain_samples[pain.label] = PainPointAgg(
                        label=pain.label,
                        severity=pain.severity,
                        evidence=pain.evidence,
                        count=pain_counter[pain.label],
                    )

            if rules.is_new_lead(analysis, action_rules):
                new_leads += 1
            if rules.is_lost_lead(analysis, action_rules):
                lost_leads += 1
            if rules.is_complaint(analysis, action_rules):
                complaints += 1

        if rules.is_follow_up(analysis, action_rules):
            follow_ups += 1
            follow_up_list.append(
                FollowUpItem(
                    call_id=record.call_id,
                    reason=analysis.follow_up_reason or analysis.summary,
                    suggested_action=_suggested_follow_up_action(analysis),
                )
            )

        if confident and rules.is_revenue_leak(analysis, action_rules):
            revenue_examples.append(
                RevenueLeakExample(call_id=record.call_id, summary=analysis.summary)
            )

        for note in analysis.staff_coaching_notes:
            note_counter[note] += 1

    top_intents = [
        IntentCount(intent=intent, count=count)
        for intent, count in intent_counter.most_common(max_top_intents)
    ]
    top_pain_points = sorted(
        [
            PainPointAgg(
                label=label,
                severity=sample.severity,
                evidence=sample.evidence,
                count=pain_counter[label],
            )
            for label, sample in pain_samples.items()
        ],
        key=lambda row: (row.count, _severity_rank(row.severity)),
        reverse=True,
    )[:10]

    staff_coaching_notes = [note for note, _ in note_counter.most_common(max_staff_notes)]

    outcome_breakdown = [
        OutcomeCount(outcome=outcome, count=count)
        for outcome, count in sorted(outcome_counter.items(), key=lambda item: (-item[1], item[0]))
    ]

    return WeeklyAggregation(
        business_name=business_name,
        week_start=week_start,
        week_end=week_end,
        total_calls=len(pairs),
        outcome_breakdown=outcome_breakdown,
        new_leads=new_leads,
        lost_leads=lost_leads,
        follow_ups=follow_ups,
        complaints=complaints,
        top_intents=top_intents,
        top_pain_points=top_pain_points,
        revenue_leak_examples=revenue_examples,
        follow_up_list=follow_up_list,
        needs_review=needs_review,
        staff_coaching_notes=staff_coaching_notes,
    )
