# Weekly CallGist Report

Business: {{ business_name }}
Week: {{ week_start }} - {{ week_end }}

## Executive Summary

{{ executive_summary }}

## Call Volume

- Total calls analyzed: {{ total_calls }}

**Outcomes (each call counted once):**

| Outcome | Calls |
|---|---:|
{%- for row in outcome_rows %}
| {{ row.outcome }} | {{ row.count }} |
{%- else %}
| - | - |
{%- endfor %}

**Action flags (can overlap):**

- New leads: {{ new_leads }}
- Likely lost leads: {{ lost_leads }}
- Follow-ups needed: {{ follow_ups }}
- Complaints: {{ complaints }}

*Action flags can overlap - one call may appear in more than one flag.*

## Top Customer Intents

| Rank | Intent | Calls | Why it matters |
|---:|---|---:|---|
{%- for row in intent_rows %}
| {{ loop.index }} | {{ row.intent }} | {{ row.count }} | {{ row.reason }} |
{%- else %}
| — | — | — | — |
{%- endfor %}

## Top Pain Points

| Rank | Pain Point | Severity | Evidence |
|---:|---|---|---|
{%- for row in pain_rows %}
| {{ loop.index }} | {{ row.pain_point }} | {{ row.severity }} | {{ row.evidence }} |
{%- else %}
| — | — | — | — |
{%- endfor %}

## Revenue Leaks

{{ revenue_leak_summary }}

{% if revenue_examples -%}
Examples:

{% for ex in revenue_examples -%}
- **{{ ex.call_id }}**: {{ ex.summary }}
{% endfor -%}
{% else -%}
No revenue leaks flagged this week.
{% endif %}

## Complaints and Risks

{{ complaint_summary }}

## Staff Coaching Notes

{{ staff_notes }}

## Recommended Actions for Next Week

1. {{ action_1 }}
2. {{ action_2 }}
3. {{ action_3 }}

## Calls That Need Follow-Up

| Call | Reason | Suggested action |
|---|---|---|
{%- for item in follow_up_list %}
| {{ item.call_id }} | {{ item.reason }} | {{ item.suggested_action }} |
{%- else %}
| — | — | — |
{%- endfor %}

## Needs Review (low confidence)

Calls below confidence threshold — verify before acting:

| Call | Issue | Confidence |
|---|---|---|
{%- for item in needs_review %}
| {{ item.call_id }} | {{ item.issue }} | {{ item.confidence }} |
{%- else %}
| — | — | — |
{%- endfor %}