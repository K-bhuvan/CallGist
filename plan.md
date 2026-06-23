# CallGist MVP Plan

## 1. Product Summary

**CallGist** helps small businesses understand what customers are saying on phone calls without needing a dedicated IT, analytics, or operations team.

The MVP listens to call recordings or reads call transcripts, identifies customer intents and pain points, groups recurring themes, and sends a weekly report to the business owner.

The product should not be positioned as a generic transcription tool. The core value is:

> Turn customer calls into weekly business actions.

---

## 2. Target Customer

Start with one narrow customer type instead of all small businesses.

Recommended first niche:

**Home service businesses**
- plumbers
- electricians
- HVAC companies
- roofing companies
- cleaning companies
- pest control companies

Why this niche is strong:
- phone calls directly affect revenue
- owners often lack internal analytics teams
- missed calls and poor intake create obvious revenue loss
- customers frequently mention pricing, scheduling, urgency, complaints, and service quality
- weekly insights can produce immediate operational improvements

---

## 3. MVP Goal

The MVP should answer five owner-level questions every week:

1. What are customers calling about?
2. What problems or complaints keep repeating?
3. Where are we losing leads or revenue?
4. What should staff improve on calls?
5. What should the owner fix next week?

The MVP is successful if the owner can read the weekly report in under 5 minutes and know what to do next.

---

## 4. Core Architecture Principle

CallGist should be built as a **generic call intelligence engine** with **industry-specific configuration packs**.

The first commercial validation target should be home services, but the core system should not be hardcoded for home services.

Design principle:

```text
CallGist = Generic Engine + Industry Config Pack
```

The generic engine handles:

- call ingestion
- audio transcription
- transcript cleaning
- structured call analysis
- intent classification
- pain point extraction
- outcome detection
- weekly aggregation
- report generation
- report delivery

The industry config pack defines:

- industry-specific intents
- pain point labels
- call outcome labels
- severity rules
- lead-quality rules
- **revenue-leak and lost-lead rules** (deterministic, in `action_rules.yaml`)
- recommended action templates
- weekly report wording
- examples used in prompts

`action_rules.yaml` must define explicit conditions for high-stakes labels — for example:

- **likely lost lead:** primary intent is `new lead` or `emergency request`, outcome is `lead lost` or `no clear outcome`, and `follow_up_needed` is false
- **revenue leak:** lost lead with `lead_quality` high or medium, or complaint unresolved with severity high
- **needs follow-up:** `follow_up_needed` is true regardless of outcome

Do not let the LLM invent these counts; compute them from per-call JSON using these rules.

For the MVP, build:

```text
Generic CallGist Engine
  + Home Services Industry Pack
```

This keeps the code reusable while making the first product sharp enough to sell and validate.

Do not build a separate “HVAC-only” or “plumbing-only” codebase. Build one engine with configurable taxonomies, prompts, and report templates.

---

## 5. Core User Flow

### Business Owner Flow

1. Owner uploads call recordings or transcripts.
2. CallGist processes the calls.
3. Each call is classified by intent and outcome.
4. Pain points and repeated themes are grouped.
5. A weekly report is generated.
6. Owner reviews the report and takes action.

### MVP Input

Manual upload of:
- `.mp3`, `.wav`, `.m4a` (audio)
- `.txt` or `.csv` (transcripts and call notes)

---

## 6. MVP Features

### Must Have

#### 6.1 Call Upload

Allow the user to upload:
- audio recordings
- existing transcripts
- CSV files containing call notes/transcripts

Metadata to capture:
- call date
- caller phone number, if available
- duration
- call direction: inbound or outbound
- staff member, if available
- call source, if available

#### 6.2 Transcription

If audio is uploaded, convert it to text.

Store:
- raw transcript
- language, if detected

Do not build diarization in the MVP. Basic transcript quality is enough to validate the business value.

#### 6.3 Intent Classification

Classify each call into one primary intent and optional secondary intents.

Initial intent categories:

- new lead
- price question
- appointment scheduling
- rescheduling
- cancellation
- complaint
- refund request
- service status question
- emergency request
- follow-up request
- general question
- spam / irrelevant
- unknown

Each call should have:
- primary intent
- secondary intents
- confidence score
- short reason

Calls below the confidence threshold (define in `generic.yaml`, e.g. 0.7) are excluded from headline weekly stats and listed in the report’s “Needs Review” section.

#### 6.4 Pain Point Extraction

Extract pain points from the customer side.

Examples:
- pricing unclear
- appointment availability too limited
- customer waited too long
- staff did not follow up
- customer confused about service coverage
- customer unhappy with technician
- customer asked for unavailable service
- customer did not understand warranty
- customer complained about hidden fees

Each pain point should include:
- label
- short explanation
- customer quote or paraphrased evidence
- severity: low / medium / high
- business area: pricing, scheduling, service quality, communication, operations, sales, support

#### 6.5 Call Outcome Detection

Detect the likely outcome of the call.

Initial outcome categories:

- booked appointment
- quote requested
- lead lost
- follow-up needed
- complaint unresolved
- complaint resolved
- customer satisfied
- customer dissatisfied
- no clear outcome
- spam / irrelevant

#### 6.6 Weekly Report

Generate a weekly owner report with:

1. Executive summary
2. Top customer intents
3. Top pain points
4. Revenue leaks
5. Customer complaints
6. Staff coaching notes
7. Suggested owner actions
8. Follow-up list
9. Example call snippets

The report is saved as markdown and delivered to the owner (manually at first, then via scheduled job).

#### 6.7 Owner Report Delivery (Not a Dashboard)

The product is the **weekly email** (or mobile-readable message), not a web portal.

Optional later for operators only: minimal upload UI to ingest transcripts. Owners never need a login to read their report.

The weekly report email is primary. Any web UI is secondary and operator-facing only.

---

## 7. Non-Goals for MVP

Do not build these in the first version:

- complex CRM replacement
- real-time call monitoring
- live agent assist
- advanced call center analytics
- multi-location enterprise dashboard
- custom workflow automation
- deep sentiment charts
- complex role-based permissions
- full billing system before validation
- phone system integrations

The MVP should prove that weekly call intelligence is valuable enough for owners to pay for.

---

## 8. AI Processing Pipeline

### Step 1: Ingest

Input:
- audio file
- transcript file
- CSV row

Output:
- normalized call record

### Step 2: Transcribe

Input:
- audio file

Output:
- transcript text

Tool: **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** — open-source Whisper, run locally. No API key.

Model size for home-service phone calls (English):
- `medium` on CPU (default starting point)
- `large-v3` if you have a GPU and want higher accuracy

Whisper does not separate speakers. Diarization is out of scope for MVP.

### Step 3: Clean Transcript

Tasks:
- remove filler if needed
- normalize speaker labels
- detect empty or low-quality calls
- redact sensitive information where possible

### Step 4: Analyze Single Call

For each call, produce structured JSON:

```json
{
  "summary": "Customer called to ask about emergency HVAC repair pricing and availability.",
  "primary_intent": "price question",
  "secondary_intents": ["emergency request", "appointment scheduling"],
  "pain_points": [
    {
      "label": "unclear emergency pricing",
      "severity": "medium",
      "business_area": "pricing",
      "evidence": "Customer repeatedly asked what the emergency fee includes."
    }
  ],
  "outcome": "quote requested",
  "follow_up_needed": true,
  "follow_up_reason": "Customer asked for a callback with exact pricing.",
  "lead_quality": "high",
  "customer_sentiment": "concerned",
  "staff_coaching_notes": [
    "Staff should explain emergency fee structure more clearly."
  ]
}
```

### Step 5: Aggregate Weekly Themes

Group calls by:
- intent
- pain point
- outcome
- staff issue
- product/service issue
- lost lead reason
- unresolved customer issue

### Step 6: Generate Weekly Report

The report should be generated from structured data, not directly from raw transcripts.

Rules:
- **Aggregate in code** — counts, rankings, and follow-up lists come from per-call JSON + `action_rules.yaml`
- **Template-first** — fill the report template (Section 10) from aggregated facts
- **LLM writes only** the executive summary and recommended-action wording, using top-N structured facts as input (no free-form analysis of raw transcripts)
- **Flag uncertainty** — calls with `confidence_score` below threshold appear in a separate “needs review” section, not in headline stats
- **Cap actions** — maximum 3 recommended owner actions per week (reduces generic advice)

This reduces hallucinations and makes the report easier to audit.

---

## 9. Suggested Data Model

### users

- id
- name
- email
- role
- business_id
- created_at

### businesses

- id
- name
- industry
- timezone
- owner_email
- report_day
- created_at

### calls

- id
- business_id
- source
- call_date
- duration_seconds
- direction
- caller_number_hash
- staff_name
- audio_path
- transcript_text
- transcript_status
- created_at

### call_analyses

- id
- call_id
- summary
- primary_intent
- secondary_intents
- outcome
- lead_quality
- customer_sentiment
- follow_up_needed
- follow_up_reason
- confidence_score
- analysis_json
- created_at

### pain_points

- id
- call_id
- label
- severity
- business_area
- evidence
- created_at

### weekly_reports

- id
- business_id
- week_start
- week_end
- report_markdown
- report_json
- email_sent_at
- created_at

---

## 10. Weekly Report Template

```markdown
# Weekly CallGist Report

Business: {{business_name}}
Week: {{week_start}} - {{week_end}}

## Executive Summary

This week, customers mostly called about {{top_intents}}. The most important issue to fix is {{main_issue}} because it appeared in {{issue_count}} calls and may affect revenue or customer satisfaction.

## Call Volume

- Total calls analyzed: {{total_calls}}
- New leads: {{new_leads}}
- Likely lost leads: {{lost_leads}}
- Follow-ups needed: {{follow_ups}}
- Complaints: {{complaints}}

## Top Customer Intents

| Rank | Intent | Calls | Why it matters |
|---|---:|---:|---|
| 1 | {{intent}} | {{count}} | {{reason}} |

## Top Pain Points

| Rank | Pain Point | Severity | Evidence |
|---|---|---|---|
| 1 | {{pain_point}} | {{severity}} | {{evidence}} |

## Revenue Leaks

{{revenue_leak_summary}}

Examples:
- {{example_1}}
- {{example_2}}

## Complaints and Risks

{{complaint_summary}}

## Staff Coaching Notes

{{staff_notes}}

## Recommended Actions for Next Week

1. {{action_1}}
2. {{action_2}}
3. {{action_3}}

## Calls That Need Follow-Up

| Call | Reason | Suggested action |
|---|---|---|
| {{call_ref}} | {{reason}} | {{action}} |

## Needs Review (low confidence)

Calls below confidence threshold — verify before acting:

| Call | Issue | Confidence |
|---|---|---|
| {{call_ref}} | {{issue}} | {{confidence}} |
```

---

## 11. Tech Stack

Bootstrapped project. One paid dependency: **LLM API key** (pay-per-use) for call analysis and weekly report generation.

| Layer | Choice |
|-------|--------|
| **Language** | Python |
| **Milestone 1** | CLI scripts |
| **Milestone 2+** | HTML email generation; optional minimal operator upload (not owner dashboard) |
| **Database** | SQLite → PostgreSQL in Docker when multi-tenant |
| **Storage** | Local `data/` directory |
| **Transcription** | `faster-whisper` (local, free) |
| **Analysis** | LLM API with structured JSON output |
| **Jobs** | Manual runs → `cron` or APScheduler |
| **Email** | Markdown report file → manual send during pilots |
| **Auth** | None (Milestone 1) → simple password gate (Milestone 2) |
| **Deployment** | Local machine |

---

## 12. Development Milestones

### Milestone 1: Local Prototype

Goal:
Process 10 uploaded transcripts and generate a weekly report manually.

Build:
- transcript upload
- single-call analysis script
- weekly aggregation script
- markdown report output

Success:
- report is useful enough to show a real business owner

### Milestone 2: Owner Delivery (Email, Mobile-First)

Goal:
Owner receives an accurate weekly report on their phone — without logging into an app.

Build:
- mobile-friendly HTML email version of the weekly report (single column, large type, 3 actions up top)
- plain-text fallback for email clients
- optional: minimal operator upload page (transcripts only) — not an owner dashboard
- SQLite for report history and owner email address

Success:
- owner reads the full email on their phone
- owner can forward the 3 actions to staff without explanation
- no owner login required to read the report

Do not build: call list UI, charts, analytics dashboard, or “portal” for owners.

### Milestone 3: Automated Weekly Send

Goal:
Report lands in the owner's inbox every week without manual work.

Build:
- scheduled weekly job (`cron` or APScheduler)
- send HTML + text email to `owner_email` on file
- report history in SQLite

Success:
- owner receives report on schedule; open rate trackable

Delivery may start with manual forward during early pilots; automate when 3+ businesses are active.

### Milestone 4: Trust and Revenue-Leak Tuning

Goal:
Owners trust the revenue-leak, follow-up, and coaching sections enough to act on them.

Build (mostly config and prompt tuning, not new features):
- define and test `action_rules.yaml` (`lead_lost_rules`, `revenue_leak_rules`, `follow_up_rules`)
- flag low-confidence classifications in the report
- owner ground-truth review on 10 calls per pilot business; iterate taxonomy and rules
- soften staff coaching wording in `report_template.md` (suggest improvements, not blame)

Success:
- owner agrees that lost-lead and follow-up items match their memory of the calls
- false lost-lead rate acceptable on the 10-call review sample

### Milestone 5: Pilot with Real Businesses

Goal:
Validate willingness to pay.

Pilot:
- 3 to 5 businesses
- 4 weeks of reports
- manually assist where needed
- measure whether owners take action

Success:
- at least 2 businesses would pay $50-$150/month

---

## 13. Validation Plan

Before building too much software, run a concierge MVP.

### Pilot screening (before accepting a business)

Confirm before onboarding:
- they can provide a **full calendar week** of calls (not cherry-picked highlights)
- they have recordings, transcripts, CSV exports, or call notes — any format is fine
- they understand calls are processed locally and how data is stored/deleted (see Section 15)

Decline or defer pilots that cannot provide representative call data.

### Concierge MVP

0. Screen pilot using criteria above.
1. Collect 20–50 calls from one calendar week (recordings or transcripts).
2. Run scripts + LLM prompts through the pipeline.
3. Produce a weekly report.
4. **Ground-truth review:** owner labels intent and outcome on 10 calls; compare to CallGist output and fix taxonomy/rules.
5. Ask:
   - Was this useful?
   - What surprised you?
   - What would you fix based on this?
   - Would you pay for this monthly?
   - What price feels reasonable?
6. If they say they already use CallRail / OpenPhone / similar, show differentiation: recurring themes, revenue leaks, follow-up list, and week-over-week actions — not per-call summaries.

### Validation Metrics

Strong signals:
- owner reads the whole report
- owner forwards report to staff
- owner asks for next week's report
- owner changes phone script or process
- owner identifies lost revenue
- owner agrees to pay

Weak signals:
- owner says “interesting” but takes no action → tighten to 3 prioritized actions; ask which one they would do first
- owner wants a dashboard before using the report
- owner says they already get this from another tool → use differentiation pitch in step 6
- owner cannot provide call data

---

## 14. MVP Success Metrics

Product metrics:
- calls processed per business per week
- report open rate
- number of suggested actions generated (target: ≤3 per week)
- number of follow-up calls identified
- percentage of calls classified with high confidence

Business metrics:
- pilot conversion rate
- willingness to pay
- retention after 4 weeks
- number of owner-reported actions taken
- number of recovered leads, if trackable

Quality metrics (measure via 10-call ground-truth review per pilot):
- intent classification accuracy
- false lost-lead rate
- false complaint rate
- report usefulness rating (1–5)
- owner trust rating (1–5)

Track quality metrics after each concierge report and after each pilot week; iterate `taxonomy.yaml` and `action_rules.yaml` when accuracy drops.

---

## 15. Privacy and Compliance Notes

CallGist handles sensitive customer conversations, so privacy must be part of the MVP.

Important requirements:
- show clear consent guidance to business owners
- allow businesses to delete calls and transcripts
- redact sensitive data where possible
- avoid storing payment card data
- avoid storing unnecessary personal data
- hash phone numbers when exact numbers are not needed
- keep retention short by default (e.g. 90 days unless owner opts in)
- do not train models on customer data without explicit permission
- include a privacy notice and terms of use before launch

**Before the first pilot** (not “before launch”):
- one-page data handling summary for owners (what is stored, where, retention, deletion, no training)
- `delete_call` script or CLI command that removes audio, transcript, and analysis for a call
- default retention policy documented in README

For regulated industries like healthcare, legal, insurance, and finance, be careful. These may require stricter compliance and should not be the first MVP niche unless the product is designed for that from the start.

---

## 16. Main Risks

Each risk lists the threat, mitigation strategy, and **concrete plan items** that implement it.

### Risk 1: Crowded Market

Many call platforms already offer AI summaries and analytics.

**Mitigation:** Position as a **weekly owner action report**, not transcription or dashboards.

**Differentiation vs incumbents (CallRail, OpenPhone, etc.):**
- recurring themes across the week (not per-call summaries)
- revenue leaks and follow-up list with evidence
- max 3 prioritized owner actions

**Plan items:** Section 17 positioning; Section 6.7 dashboard secondary; Section 13 concierge step 6; report template Sections on revenue leaks and follow-ups.

### Risk 2: Data Access

Small businesses may not have recordings available.

**Mitigation:** Accept transcripts, CSV, and call notes — audio is optional.

**Mitigation:** Screen pilots for a **full calendar week** of calls; reject cherry-picked samples.

**Plan items:** Section 5 MVP input; Section 13 pilot screening; Risk 2 weak signal in validation metrics.

### Risk 3: Privacy Concerns

Owners may worry about uploading customer calls.

**Mitigation:** Local processing, short retention, deletion, redaction, hashed phone numbers, no training on customer data.

**Plan items:** Section 15 requirements; `delete_call` before first pilot; one-page data handling summary; `caller_number_hash` in data model; pipeline Step 3 redaction; Section 19 checklist items 6a–6c.

### Risk 4: Low Report Trust

If the AI makes wrong claims, owners will stop trusting it.

**Mitigation:**
- structured per-call JSON with evidence quotes and confidence scores
- weekly report built from aggregated JSON + `action_rules.yaml`, not raw transcripts
- low-confidence calls flagged, not headlined
- owner ground-truth review on 10 calls per pilot

**Plan items:** Section 8 Steps 4 and 6; Section 14 quality metrics; Section 13 step 4; Milestone 4; `action_rules.yaml` for deterministic lost-lead counts.

### Risk 5: Insights Are Too Generic

Generic advice will not create willingness to pay.

**Mitigation:** Home services industry pack with specific taxonomy, `action_rules.yaml`, and template-driven weekly report; LLM only polishes summary and actions from top-N facts; cap at 3 actions per week.

**Plan items:** Sections 2 and 4; `industry_packs/home_services/`; Section 8 Step 6 rules; Section 13 weak-signal response for “interesting but no action.”

### Risk 6: Transcription Quality

Noisy phone audio and no speaker diarization can produce bad transcripts → bad analysis → lost trust.

**Mitigation:**
- use `faster-whisper` `medium` or `large-v3` model
- pipeline Step 3: flag empty or low-quality transcripts; skip or mark low-confidence
- prefer transcript upload when owner already has one
- spot-check 5 transcripts against audio during first pilot

**Plan items:** Section 8 Steps 2 and 3; Milestone 4 ground-truth review catches downstream errors.

### Risk 7: Staff Pushback on Coaching Notes

Owners sharing blunt AI coaching notes can create staff conflict.

**Mitigation:** Wording templates in `report_template.md` — frame as process improvements (“consider explaining emergency fees earlier”) not personal criticism.

**Plan items:** Milestone 4; industry pack report template.

---

## 17. Product Positioning

> Find lost leads, repeated complaints, and customer pain points from your business calls every week.

---

## 18. Repo Structure

```text
callgist/
  README.md
  plan.md
  core/
    ingestion.py
    transcription.py
    analysis.py
    aggregation.py
    reporting.py
  configs/
    generic.yaml
    home_services.yaml
  prompts/
    call_analysis.md
    weekly_report.md
  industry_packs/
    home_services/
      taxonomy.yaml
      action_rules.yaml
      report_template.md
  data/
    sample_transcripts/
  docs/
    data_handling.md
  scripts/
    run_analysis.py
    generate_sample_report.py
    delete_call.py
  outputs/
    sample_report.md
```

The generic engine lives in `core/`. Industry-specific behavior lives in `industry_packs/home_services/` config files.

---

## 19. First Build Checklist

Start with this order:

1. Create repo: `callgist`
2. Add `README.md`
3. Add this `plan.md`
4. Create the generic engine folders: `core/`, `prompts/`, and `configs/`
5. Create the first industry pack: `industry_packs/home_services/`
6. Add `generic.yaml` and `home_services.yaml`
6a. Add `docs/data_handling.md` (one-page summary for pilot owners)
6b. Add `scripts/delete_call.py` (remove audio, transcript, analysis for one call)
6c. Document default 90-day retention in README
7. Define `action_rules.yaml` with `lead_lost_rules`, `revenue_leak_rules`, and `follow_up_rules`
8. Create sample home-services transcript files
9. Write the first single-call analysis function
10. Make the analysis function read taxonomy and rules from config
11. Define structured JSON output (include `confidence_score` and evidence on every pain point)
12. Write weekly aggregation logic (counts from JSON + rules, not LLM)
13. Generate `sample_report.md` using template-first pipeline (Section 8 Step 6)
14. Test with 10–20 real or realistic home-services calls
15. Run ground-truth review: compare 10 classifications against your own labels
16. Show report to one business owner
17. Improve taxonomy, action rules, and report format from feedback
18. Build upload UI only after the report is clearly useful

---

## 20. Prompt Files

### prompts/call_analysis.md

Purpose:
Analyze one customer call and return structured JSON.

Expected output:
- summary
- primary intent
- secondary intents
- pain points
- outcome
- follow-up needed
- lead quality
- customer sentiment
- staff coaching notes
- confidence score

### prompts/weekly_report.md

Purpose:
Aggregate many analyzed calls into a weekly owner report.

Expected output:
- executive summary (from top-N aggregated facts only)
- top intents
- top pain points
- revenue leaks (computed via `action_rules.yaml`)
- complaints
- recommended actions (max 3)
- follow-up list
- needs-review section for low-confidence calls

---

## 21. Final MVP Principle

Build the smallest system that can produce a report a business owner would pay for.

The first product does not need to be beautiful.

It needs to answer:

> What happened on our calls this week, what should I worry about, and what should I fix next?
