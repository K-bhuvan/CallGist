# CallGist Data Handling (Pilot Summary)

CallGist helps home service businesses understand phone calls. This page explains what data we store, how long we keep it, and how you can delete it.

## What we process

- Call **transcripts** (text) or audio recordings you provide
- Optional metadata: call date, inbound/outbound direction, staff name
- **Analysis results**: structured summaries, intents, pain points, and outcomes (JSON)

We do **not** need payment card numbers. Avoid uploading card details in notes or transcripts.

## Where data lives (Milestone 1)

- Files on the machine running CallGist: `data/` for uploads, `outputs/` for analyses and reports
- Processing uses your configured LLM API for analysis and report wording; transcripts are sent to that API only when you run analysis

## Retention

- **Default: 90 days** unless you agree to a longer period in writing
- Delete individual calls anytime with `python scripts/delete_call.py <call_id>`
- Remove all pilot data by deleting files under `data/` and `outputs/` when the pilot ends

## Privacy practices

- Phone numbers: store only what you need; hash or omit when exact numbers are not required
- Redaction: transcript cleaning can be extended to redact sensitive strings; owners should avoid unnecessary personal data in uploads
- **No training**: customer call content is not used to train models unless you give explicit written permission

## Owner responsibilities

- Obtain appropriate consent or notice for recording/transcription under your local laws
- Tell staff that calls may be analyzed for quality and operations
- Review the weekly report’s “Needs Review” section before acting on low-confidence items

## Questions

Contact your CallGist pilot operator for deletion requests, retention changes, or a copy of your data export.
