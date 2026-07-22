"""CRUD operations bridging Pydantic models with the SQLite database."""
from __future__ import annotations

import json
from datetime import date

from sqlalchemy import func

from core.db import get_session
from core.db_models import CallAnalysisRow, CallRecordRow, WeeklyReportRow
from core.models import CallAnalysis, CallRecord, WeeklyAggregation


def upsert_call_record(record: CallRecord) -> CallRecordRow:
    session = get_session()
    try:
        existing = session.query(CallRecordRow).filter_by(call_id=record.call_id).first()
        if existing:
            existing.transcript_text = record.transcript_text
            existing.call_date = record.call_date
            existing.direction = record.direction
            existing.staff_name = record.staff_name
            existing.source_path = record.source_path
            existing.low_quality = record.low_quality
            existing.quality_note = record.quality_note
        else:
            existing = CallRecordRow(
                call_id=record.call_id,
                transcript_text=record.transcript_text,
                call_date=record.call_date,
                direction=record.direction,
                staff_name=record.staff_name,
                source_path=record.source_path,
                low_quality=record.low_quality,
                quality_note=record.quality_note,
            )
            session.add(existing)
        session.commit()
        return existing
    finally:
        session.close()


def get_call_record(call_id: str) -> CallRecordRow | None:
    session = get_session()
    try:
        return session.query(CallRecordRow).filter_by(call_id=call_id).first()
    finally:
        session.close()


def list_call_records(call_date_min: date | None = None, call_date_max: date | None = None) -> list[CallRecordRow]:
    session = get_session()
    try:
        q = session.query(CallRecordRow)
        if call_date_min:
            q = q.filter(CallRecordRow.call_date >= call_date_min)
        if call_date_max:
            q = q.filter(CallRecordRow.call_date <= call_date_max)
        return q.order_by(CallRecordRow.call_date, CallRecordRow.call_id).all()
    finally:
        session.close()


def upsert_call_analysis(
    call_id: str,
    analysis: CallAnalysis,
    cost_info: dict | None = None,
) -> CallAnalysisRow:
    session = get_session()
    try:
        existing = session.query(CallAnalysisRow).filter_by(call_id=call_id).first()
        if existing:
            existing.summary = analysis.summary
            existing.primary_intent = analysis.primary_intent
            existing.secondary_intents = json.dumps(analysis.secondary_intents)
            existing.pain_points_json = json.dumps(
                [p.model_dump() for p in analysis.pain_points]
            )
            existing.outcome = analysis.outcome
            existing.follow_up_needed = analysis.follow_up_needed
            existing.follow_up_reason = analysis.follow_up_reason
            existing.lead_quality = analysis.lead_quality
            existing.customer_sentiment = analysis.customer_sentiment
            existing.staff_coaching_notes_json = json.dumps(analysis.staff_coaching_notes)
            existing.confidence_score = analysis.confidence_score
        else:
            existing = CallAnalysisRow(
                call_id=call_id,
                summary=analysis.summary,
                primary_intent=analysis.primary_intent,
                secondary_intents=json.dumps(analysis.secondary_intents),
                pain_points_json=json.dumps(
                    [p.model_dump() for p in analysis.pain_points]
                ),
                outcome=analysis.outcome,
                follow_up_needed=analysis.follow_up_needed,
                follow_up_reason=analysis.follow_up_reason,
                lead_quality=analysis.lead_quality,
                customer_sentiment=analysis.customer_sentiment,
                staff_coaching_notes_json=json.dumps(analysis.staff_coaching_notes),
                confidence_score=analysis.confidence_score,
            )
            session.add(existing)
        if cost_info:
            existing.model_name = cost_info.get("model_name")
            existing.tokens_in = cost_info.get("tokens_in")
            existing.tokens_out = cost_info.get("tokens_out")
            existing.cost_usd = cost_info.get("cost_usd")
        session.commit()
        return existing
    finally:
        session.close()


def get_call_analysis(call_id: str) -> CallAnalysisRow | None:
    session = get_session()
    try:
        return session.query(CallAnalysisRow).filter_by(call_id=call_id).first()
    finally:
        session.close()


def list_call_analyses(call_ids: list[str] | None = None) -> list[CallAnalysisRow]:
    session = get_session()
    try:
        q = session.query(CallAnalysisRow)
        if call_ids:
            q = q.filter(CallAnalysisRow.call_id.in_(call_ids))
        return q.order_by(CallAnalysisRow.call_id).all()
    finally:
        session.close()


def save_weekly_report(
    aggregation: WeeklyAggregation,
    report_markdown: str,
) -> WeeklyReportRow:
    session = get_session()
    try:
        row = WeeklyReportRow(
            business_name=aggregation.business_name,
            week_start=aggregation.week_start,
            week_end=aggregation.week_end,
            total_calls=aggregation.total_calls,
            report_markdown=report_markdown,
        )
        session.add(row)
        session.commit()
        return row
    finally:
        session.close()


def get_weekly_report(week_start: date) -> list[WeeklyReportRow]:
    session = get_session()
    try:
        return (
            session.query(WeeklyReportRow)
            .filter(WeeklyReportRow.week_start == week_start)
            .order_by(WeeklyReportRow.generated_at.desc())
            .all()
        )
    finally:
        session.close()


def total_cost_for_period(since: date | None = None) -> tuple[float, int]:
    session = get_session()
    try:
        q = session.query(func.coalesce(func.sum(CallAnalysisRow.cost_usd), 0.0))
        if since:
            q = q.filter(CallAnalysisRow.analyzed_at >= since)
        cost = q.scalar()
        count = session.query(CallAnalysisRow).count()
        return float(cost), count
    finally:
        session.close()
