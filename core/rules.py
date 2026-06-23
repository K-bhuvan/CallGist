"""Deterministic action rules from action_rules.yaml."""
from __future__ import annotations

from typing import Any

from core.models import CallAnalysis


def is_lost_lead(analysis: CallAnalysis, rules: dict[str, Any]) -> bool:
    lead_lost = rules.get("lead_lost", {})
    intents = set(lead_lost.get("primary_intents", []))
    if analysis.primary_intent not in intents:
        return False

    definite_outcomes = set(lead_lost.get("outcomes", []))
    if analysis.outcome in definite_outcomes:
        return True

    tentative_outcomes = set(lead_lost.get("tentative_outcomes", []))
    if analysis.outcome not in tentative_outcomes:
        return False

    if lead_lost.get("tentative_require_follow_up_needed") is False:
        return not analysis.follow_up_needed
    return True


def is_follow_up(analysis: CallAnalysis, rules: dict[str, Any]) -> bool:
    expected = rules.get("follow_up", {}).get("follow_up_needed", True)
    return analysis.follow_up_needed is expected


def is_new_lead(analysis: CallAnalysis, rules: dict[str, Any]) -> bool:
    intents = set(rules.get("new_lead_intents", []))
    return analysis.primary_intent in intents


def is_complaint(analysis: CallAnalysis, rules: dict[str, Any]) -> bool:
    intents = set(rules.get("complaint_intents", []))
    return analysis.primary_intent in intents


def is_revenue_leak(analysis: CallAnalysis, rules: dict[str, Any]) -> bool:
    for rule in rules.get("revenue_leak", []):
        name = rule.get("rule")
        if name == "lost_lead_with_quality":
            qualities = set(rule.get("lead_quality", []))
            if is_lost_lead(analysis, rules) and analysis.lead_quality in qualities:
                return True
        elif name == "unresolved_high_complaint":
            intents = set(rule.get("primary_intents", []))
            outcomes = set(rule.get("outcomes", []))
            min_sev = rule.get("min_pain_severity", "high")
            if analysis.primary_intent not in intents:
                continue
            if analysis.outcome not in outcomes:
                continue
            if any(p.severity == min_sev for p in analysis.pain_points):
                return True
    return False
