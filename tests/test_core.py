from __future__ import annotations

from datetime import date

import pytest

from core.aggregation import _severity_rank, _suggested_follow_up_action, aggregate_week
from core.cleaning import apply_cleaning, clean_transcript
from core.models import CallAnalysis, CallRecord, PainPoint
from core.pii_redaction import redact, should_redact
from core.rules import is_complaint, is_follow_up, is_lost_lead, is_new_lead, is_revenue_leak

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def action_rules() -> dict:
    return {
        "new_lead_intents": ["new lead", "emergency request"],
        "complaint_intents": ["complaint", "refund request"],
        "lead_lost": {
            "primary_intents": ["new lead", "emergency request", "price question"],
            "outcomes": ["lead lost"],
            "tentative_outcomes": ["no clear outcome"],
            "tentative_require_follow_up_needed": False,
        },
        "revenue_leak": [
            {
                "rule": "lost_lead_with_quality",
                "lead_quality": ["high", "medium"],
            },
            {
                "rule": "unresolved_high_complaint",
                "primary_intents": ["complaint", "refund request"],
                "outcomes": ["complaint unresolved"],
                "min_pain_severity": "high",
            },
        ],
        "follow_up": {"follow_up_needed": True},
    }


def make_analysis(**overrides) -> CallAnalysis:
    defaults = {
        "summary": "test call",
        "primary_intent": "new lead",
        "secondary_intents": [],
        "pain_points": [],
        "outcome": "booked appointment",
        "follow_up_needed": False,
        "follow_up_reason": None,
        "lead_quality": "high",
        "customer_sentiment": "neutral",
        "staff_coaching_notes": [],
        "confidence_score": 0.9,
    }
    return CallAnalysis(**(defaults | overrides))


# ---------------------------------------------------------------------------
# cleaning.py
# ---------------------------------------------------------------------------

class TestCleanTranscript:
    def test_strips_and_normalizes_crlf(self):
        assert clean_transcript("hello\r\nworld\r\n") == "hello\nworld"

    def test_collapses_multiple_blank_lines(self):
        assert clean_transcript("a\n\n\n\nb\n\nc") == "a\n\nb\n\nc"

    def test_returns_empty_string_for_empty_input(self):
        assert clean_transcript("") == ""

    def test_handles_single_line(self):
        assert clean_transcript("  one line  \n") == "one line"


class TestApplyCleaning:
    def test_flags_short_transcript_as_low_quality(self):
        record = CallRecord(call_id="c1", transcript_text="hi")
        result = apply_cleaning(record, min_chars=50)
        assert result.low_quality is True
        assert result.quality_note == "Transcript too short for reliable analysis"

    def test_does_not_flag_long_transcript(self):
        record = CallRecord(call_id="c1", transcript_text="x" * 51)
        result = apply_cleaning(record, min_chars=50)
        assert result.low_quality is False
        assert result.quality_note is None

    def test_cleans_transcript_content(self):
        record = CallRecord(call_id="c1", transcript_text="hello\r\n\r\n\r\nworld")
        result = apply_cleaning(record, min_chars=10)
        assert result.transcript_text == "hello\n\nworld"


# ---------------------------------------------------------------------------
# rules.py
# ---------------------------------------------------------------------------

class TestIsNewLead:
    def test_matches_new_lead_intent(self, action_rules):
        a = make_analysis(primary_intent="new lead")
        assert is_new_lead(a, action_rules)

    def test_matches_emergency_intent(self, action_rules):
        a = make_analysis(primary_intent="emergency request")
        assert is_new_lead(a, action_rules)

    def test_does_not_match_other_intent(self, action_rules):
        a = make_analysis(primary_intent="complaint")
        assert not is_new_lead(a, action_rules)


class TestIsLostLead:
    def test_lost_with_definite_outcome(self, action_rules):
        a = make_analysis(primary_intent="new lead", outcome="lead lost")
        assert is_lost_lead(a, action_rules)

    def test_lost_with_tentative_outcome_no_follow_up(self, action_rules):
        a = make_analysis(
            primary_intent="new lead",
            outcome="no clear outcome",
            follow_up_needed=False,
        )
        assert is_lost_lead(a, action_rules)

    def test_not_lost_tentative_with_follow_up(self, action_rules):
        a = make_analysis(
            primary_intent="new lead",
            outcome="no clear outcome",
            follow_up_needed=True,
        )
        assert not is_lost_lead(a, action_rules)

    def test_not_lost_different_intent(self, action_rules):
        a = make_analysis(primary_intent="complaint", outcome="lead lost")
        assert not is_lost_lead(a, action_rules)

    def test_not_lost_different_outcome(self, action_rules):
        a = make_analysis(primary_intent="new lead", outcome="booked appointment")
        assert not is_lost_lead(a, action_rules)


class TestIsComplaint:
    def test_matches_complaint(self, action_rules):
        assert is_complaint(make_analysis(primary_intent="complaint"), action_rules)

    def test_matches_refund(self, action_rules):
        assert is_complaint(make_analysis(primary_intent="refund request"), action_rules)

    def test_does_not_match_lead(self, action_rules):
        assert not is_complaint(make_analysis(primary_intent="new lead"), action_rules)


class TestIsFollowUp:
    def test_needs_follow_up(self, action_rules):
        a = make_analysis(follow_up_needed=True)
        assert is_follow_up(a, action_rules)

    def test_does_not_need_follow_up(self, action_rules):
        a = make_analysis(follow_up_needed=False)
        assert not is_follow_up(a, action_rules)


class TestIsRevenueLeak:
    def test_lost_lead_revenue_leak(self, action_rules):
        a = make_analysis(
            primary_intent="new lead",
            outcome="lead lost",
            lead_quality="high",
        )
        assert is_revenue_leak(a, action_rules)

    def test_lost_lead_low_quality_not_leak(self, action_rules):
        a = make_analysis(
            primary_intent="new lead",
            outcome="lead lost",
            lead_quality="low",
        )
        assert not is_revenue_leak(a, action_rules)

    def test_unresolved_high_complaint_leak(self, action_rules):
        a = make_analysis(
            primary_intent="complaint",
            outcome="complaint unresolved",
            pain_points=[
                PainPoint(
                    label="pricing unclear",
                    severity="high",
                    business_area="pricing",
                    evidence="customer upset",
                )
            ],
        )
        assert is_revenue_leak(a, action_rules)

    def test_unresolved_low_severity_not_leak(self, action_rules):
        a = make_analysis(
            primary_intent="complaint",
            outcome="complaint unresolved",
            pain_points=[
                PainPoint(
                    label="pricing unclear",
                    severity="low",
                    business_area="pricing",
                    evidence="minor issue",
                )
            ],
        )
        assert not is_revenue_leak(a, action_rules)

    def test_no_pain_points_not_leak(self, action_rules):
        a = make_analysis(
            primary_intent="complaint",
            outcome="complaint unresolved",
            pain_points=[],
        )
        assert not is_revenue_leak(a, action_rules)


# ---------------------------------------------------------------------------
# aggregation.py
# ---------------------------------------------------------------------------

class TestSeverityRank:
    def test_ranks(self):
        assert _severity_rank("low") == 1
        assert _severity_rank("medium") == 2
        assert _severity_rank("high") == 3

    def test_unknown_returns_zero(self):
        assert _severity_rank("critical") == 0


class TestSuggestedFollowUpAction:
    def test_complaint_escalation(self):
        a = make_analysis(primary_intent="complaint", outcome="complaint unresolved")
        assert "Escalate to a manager" in _suggested_follow_up_action(a)

    def test_lost_lead_recovery(self):
        a = make_analysis(primary_intent="new lead", outcome="lead lost")
        assert "Call back with clear pricing" in _suggested_follow_up_action(a)

    def test_price_question(self):
        a = make_analysis(primary_intent="price question")
        assert "transparent pricing" in _suggested_follow_up_action(a)

    def test_follow_up_request(self):
        a = make_analysis(primary_intent="follow-up request")
        assert "promised callback or quote" in _suggested_follow_up_action(a)

    def test_booked_appointment(self):
        a = make_analysis(primary_intent="appointment scheduling", outcome="booked appointment")
        assert "appointment confirmation" in _suggested_follow_up_action(a)

    def test_reach_out_fallback(self):
        a = make_analysis(primary_intent="general question")
        assert "Reach out to complete" in _suggested_follow_up_action(a)


class TestAggregateWeek:
    def test_empty_pairs_returns_zero_everything(self):
        result = aggregate_week([], business_name="TestCo", week_start=date(2025, 1, 1))
        assert result.total_calls == 0
        assert result.new_leads == 0
        assert result.lost_leads == 0
        assert result.follow_ups == 0
        assert result.complaints == 0
        assert result.top_intents == []
        assert result.outcome_breakdown == []

    def test_counts_new_lead(self, action_rules):
        record = CallRecord(call_id="c1", transcript_text="hello world " * 10, call_date=date(2025, 1, 1))
        analysis = make_analysis(primary_intent="new lead", confidence_score=0.9)
        result = aggregate_week([(record, analysis)])
        assert result.new_leads == 1

    def test_counts_lost_lead(self, action_rules):
        record = CallRecord(call_id="c1", transcript_text="hello world " * 10, call_date=date(2025, 1, 1))
        analysis = make_analysis(
            primary_intent="new lead",
            outcome="lead lost",
            confidence_score=0.9,
        )
        result = aggregate_week([(record, analysis)])
        assert result.lost_leads == 1

    def test_low_quality_goes_to_needs_review(self, action_rules):
        record = CallRecord(
            call_id="c1",
            transcript_text="short",
            low_quality=True,
            quality_note="too short",
        )
        analysis = make_analysis(confidence_score=0.9)
        result = aggregate_week([(record, analysis)])
        assert len(result.needs_review) == 1
        assert result.needs_review[0].call_id == "c1"

    def test_low_confidence_goes_to_needs_review(self, action_rules):
        record = CallRecord(call_id="c1", transcript_text="hello world " * 10, call_date=date(2025, 1, 1))
        analysis = make_analysis(confidence_score=0.3)
        result = aggregate_week([(record, analysis)])
        assert len(result.needs_review) == 1

    def test_low_quality_calls_not_counted_for_intents(self, action_rules):
        record = CallRecord(
            call_id="c1",
            transcript_text="short",
            low_quality=True,
            quality_note="too short",
        )
        analysis = make_analysis(primary_intent="new lead", confidence_score=0.9)
        result = aggregate_week([(record, analysis)])
        assert result.top_intents == []

    def test_follow_up_flag(self, action_rules):
        record = CallRecord(call_id="c1", transcript_text="hello world " * 10, call_date=date(2025, 1, 1))
        analysis = make_analysis(follow_up_needed=True, confidence_score=0.9)
        result = aggregate_week([(record, analysis)])
        assert result.follow_ups == 1
        assert len(result.follow_up_list) == 1

    def test_auto_dates_from_records(self, action_rules):
        records = [
            (CallRecord(call_id="c1", transcript_text="x" * 10, call_date=date(2025, 1, 1)), make_analysis()),
            (CallRecord(call_id="c2", transcript_text="x" * 10, call_date=date(2025, 1, 5)), make_analysis()),
        ]
        result = aggregate_week(records, business_name="Co")
        assert result.week_start == date(2025, 1, 1)
        assert result.week_end == date(2025, 1, 5)

    def test_outcome_breakdown(self, action_rules):
        record = CallRecord(call_id="c1", transcript_text="x" * 10, call_date=date(2025, 1, 1))
        analysis = make_analysis(outcome="booked appointment", confidence_score=0.9)
        result = aggregate_week([(record, analysis)])
        assert len(result.outcome_breakdown) == 1
        assert result.outcome_breakdown[0].outcome == "booked appointment"
        assert result.outcome_breakdown[0].count == 1

    def test_complaint_flag(self, action_rules):
        record = CallRecord(call_id="c1", transcript_text="x" * 10, call_date=date(2025, 1, 1))
        analysis = make_analysis(primary_intent="complaint", confidence_score=0.9)
        result = aggregate_week([(record, analysis)])
        assert result.complaints == 1


# ---------------------------------------------------------------------------
# pii_redaction.py
# ---------------------------------------------------------------------------

class TestPIIRedaction:
    def test_redacts_phone_number(self):
        text, counts = redact("Call me at 555-123-4567 tomorrow.")
        assert "555-123-4567" not in text
        assert "[PHONE]" in text
        assert counts["phone"] == 1

    def test_redacts_email(self):
        text, counts = redact("My email is john@example.com")
        assert "john@example.com" not in text
        assert "[EMAIL]" in text
        assert counts["email"] == 1

    def test_redacts_ssn(self):
        text, counts = redact("SSN: 123-45-6789")
        assert "123-45-6789" not in text
        assert "[SSN]" in text
        assert counts["ssn"] == 1

    def test_redacts_street_address(self):
        text, counts = redact("My address is 742 Evergreen Terrace")
        assert "742 Evergreen Terrace" not in text
        assert "[ADDRESS]" in text

    def test_clean_text_unchanged(self):
        text, counts = redact("The customer wanted a quote for AC repair.")
        assert text == "The customer wanted a quote for AC repair."
        assert counts == {}

    def test_should_redact_detects_pii(self):
        assert should_redact("call 555-123-4567")
        assert not should_redact("just a normal transcript about HVAC")

    def test_redacts_multiple_phone_numbers(self):
        text, counts = redact("Call 555-111-2222 or 555-333-4444")
        assert counts["phone"] == 2

    def test_redacts_credit_card(self):
        text, counts = redact("Card number is 4111-1111-1111-1111")
        assert "4111-1111-1111-1111" not in text
        assert "[CARD]" in text
