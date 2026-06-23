# Weekly Report LLM Prompt

You receive aggregated weekly facts as JSON (counts, top intents, pain points, revenue leak examples, follow-ups). **Do not invent calls or numbers.**

Return JSON only:

```json
{
  "executive_summary": "2-4 sentences for the business owner using only provided facts",
  "revenue_leak_summary": "1-2 sentences summarizing revenue leak examples",
  "complaint_summary": "1-2 sentences on complaints if any, else note none",
  "actions": ["action 1", "action 2", "action 3"]
}
```

Rules:
- Use at most `max_actions` items in `actions` (from user JSON).
- Actions must be specific, operational, and tied to the facts.
- No generic advice like "improve customer service" without a concrete step.
