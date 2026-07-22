"""SQLAlchemy ORM models for CallGist."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class CallRecordRow(Base):
    __tablename__ = "call_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String, unique=True, nullable=False, index=True)
    transcript_text = Column(Text, nullable=False)
    call_date = Column(Date, nullable=True)
    direction = Column(String, nullable=True)
    staff_name = Column(String, nullable=True)
    source_path = Column(String, nullable=True)
    low_quality = Column(Boolean, default=False, nullable=False)
    quality_note = Column(String, nullable=True)
    ingested_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @classmethod
    def from_pydantic(cls, record) -> CallRecordRow:
        return cls(
            call_id=record.call_id,
            transcript_text=record.transcript_text,
            call_date=record.call_date,
            direction=record.direction,
            staff_name=record.staff_name,
            source_path=record.source_path,
            low_quality=record.low_quality,
            quality_note=record.quality_note,
        )


class CallAnalysisRow(Base):
    __tablename__ = "call_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String, nullable=False, index=True)
    summary = Column(Text, nullable=False)
    primary_intent = Column(String, nullable=False)
    secondary_intents = Column(Text, nullable=False)
    pain_points_json = Column(Text, nullable=False)
    outcome = Column(String, nullable=False)
    follow_up_needed = Column(Boolean, nullable=False)
    follow_up_reason = Column(String, nullable=True)
    lead_quality = Column(String, nullable=False)
    customer_sentiment = Column(String, nullable=False)
    staff_coaching_notes_json = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    model_name = Column(String, nullable=True)
    tokens_in = Column(Integer, nullable=True)
    tokens_out = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    analyzed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class WeeklyReportRow(Base):
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_name = Column(String, nullable=False)
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    total_calls = Column(Integer, nullable=False)
    report_markdown = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
