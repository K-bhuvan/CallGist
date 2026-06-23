"""Pydantic models for CallGist."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class PainPoint(BaseModel):
    label: str
    severity: str
    business_area: str
    evidence: str


class CallAnalysis(BaseModel):
    summary: str
    primary_intent: str
    secondary_intents: list[str] = Field(default_factory=list)
    pain_points: list[PainPoint] = Field(default_factory=list)
    outcome: str
    follow_up_needed: bool
    follow_up_reason: Optional[str] = None
    lead_quality: str
    customer_sentiment: str
    staff_coaching_notes: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)


class CallRecord(BaseModel):
    call_id: str
    transcript_text: str
    call_date: Optional[date] = None
    direction: Optional[str] = None
    staff_name: Optional[str] = None
    source_path: Optional[str] = None
    low_quality: bool = False
    quality_note: Optional[str] = None


class IntentCount(BaseModel):
    intent: str
    count: int


class OutcomeCount(BaseModel):
    outcome: str
    count: int


class PainPointAgg(BaseModel):
    label: str
    severity: str
    evidence: str
    count: int


class FollowUpItem(BaseModel):
    call_id: str
    reason: str
    suggested_action: str = ""


class NeedsReviewItem(BaseModel):
    call_id: str
    issue: str
    confidence: float


class RevenueLeakExample(BaseModel):
    call_id: str
    summary: str


class WeeklyAggregation(BaseModel):
    business_name: str
    week_start: date
    week_end: date
    total_calls: int
    outcome_breakdown: list[OutcomeCount] = Field(default_factory=list)
    new_leads: int
    lost_leads: int
    follow_ups: int
    complaints: int
    top_intents: list[IntentCount]
    top_pain_points: list[PainPointAgg]
    revenue_leak_examples: list[RevenueLeakExample]
    follow_up_list: list[FollowUpItem]
    needs_review: list[NeedsReviewItem]
    staff_coaching_notes: list[str]
