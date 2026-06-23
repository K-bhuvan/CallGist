# Call Analysis Prompt

You analyze one home-services customer phone call transcript and return **only** valid JSON matching the schema below.

Use intents, outcomes, pain point labels, business areas, lead quality levels, and sentiments from this taxonomy:

```yaml
{{taxonomy_yaml}}
```

## Rules

- Choose **one** `primary_intent` from the taxonomy intents list.
- `secondary_intents` may include other taxonomy intents (0-3 items).
- `outcome` must be from the taxonomy outcomes list.
- Each `pain_points[].label` should prefer taxonomy pain_point_labels when it fits; you may use a short custom label if needed.
- `pain_points[].business_area` must be from taxonomy business_areas.
- `lead_quality` must be from taxonomy lead_quality_levels.
- `customer_sentiment` must be from taxonomy sentiments.
- Include short evidence quotes or paraphrases from the customer side.
- `confidence_score` is 0.0-1.0 for how sure you are about primary intent and outcome.
- Staff coaching notes should be constructive process suggestions, not personal blame.

## JSON schema

```json
{
  "summary": "string",
  "primary_intent": "string",
  "secondary_intents": ["string"],
  "pain_points": [
    {
      "label": "string",
      "severity": "low|medium|high",
      "business_area": "string",
      "evidence": "string"
    }
  ],
  "outcome": "string",
  "follow_up_needed": true,
  "follow_up_reason": "string or null",
  "lead_quality": "string",
  "customer_sentiment": "string",
  "staff_coaching_notes": ["string"],
  "confidence_score": 0.0
}
```
