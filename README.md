# CallGist

<p align="center">
  <img src="public/logo.svg" alt="CallGist" width="96" height="96">
</p>

<p align="center"><strong>Weekly call intelligence for home-service owners — delivered to their inbox.</strong></p>

Every Monday, the owner gets one short email: what customers called about, what went wrong, which leads slipped, and **three things to fix this week**. Readable on a phone in under five minutes.

---

## How it works

1. **Ingest** — phone call transcripts (`.txt` files with optional `.meta.json`)
2. **Analyze** — each call classified by LLM (intent, outcome, pain points, lead quality, sentiment)
3. **Aggregate** — deterministic rules count new leads, lost leads, follow-ups, complaints, revenue leaks
4. **Report** — markdown report with executive summary, top issues, and 3 recommended actions
5. **Deliver** — emails the report automatically via SendGrid

### Try it

```bash
pip install -e ".[dev]"
cp .env.example .env          # configure your LLM provider + email
python scripts/run_pipeline.py
```

**LLM providers:** OpenAI or OpenRouter (any OpenAI-compatible API works). Set `LLM_PROVIDER` in `.env`.

**Email:** reports sent via SendGrid. Set `SENDGRID_API_KEY` and `REPORT_TO_EMAIL`.

| Command | What it does |
|---------|-------------|
| `callgist-pipeline` | Full run: ingest → analyze → aggregate → report → email |
| `callgist-analyze` | Analyze transcripts only (parallel, `--workers N`) |
| `callgist-report` | Generate weekly report from existing analyses |
| `callgist-validate` | Compare LLM predictions against ground truth labels |

---

## Example output

**Subject:** *BrightPipe HVAC — Weekly CallGist (Jun 16–20)*

> 45 calls this week. Here are the 3 things worth your time:
>
> 1. **Escalate unresolved complaints (3 open)** — mud tracking, rude tech, missed callbacks. Bad review risk.
> 2. **Train team on pricing** — drain promo confusion still showing up. Customers hear $49, get quoted $189.
> 3. **Close follow-up gaps** — 15 callbacks owed. Promised estimates need owners.
>
> | Outcome | Calls |
> |---|---:|
> | booked appointment | 24 |
> | lead lost | 4 |
> | complaint unresolved | 3 |
>
> See [`outputs/sample_report.md`](outputs/sample_report.md)

---

## Why owners trust it

Wrong "lost lead" claims kill the product. CallGist backs every headline with evidence:

- **Rules, not guesses** — lost leads and follow-ups are counted by deterministic rules, not the LLM
- **Evidence quotes** — every pain point tagged with what the customer actually said
- **Needs review** — low-confidence calls flagged separately so you verify before acting

Validation: [`docs/validation_results.md`](docs/validation_results.md) — 100% intent / 80% outcome on 10 test calls.

---

## Features

- **PII redaction** — phone numbers, emails, SSNs, cards, and addresses stripped before hitting the LLM
- **Cost tracking** — token usage and cost per call saved to database
- **Structured logging** — JSON or console output, configurable via `LOG_FORMAT`
- **Resumable** — `--skip-existing` picks up where you left off
- **Database optional** — file-based by default, `--use-db` persists to SQLite
- **CI/CD** — GitHub Actions runs tests on Python 3.9–3.12

---

## Project structure

```
columbus/
├── core/                  # Pipeline engine
│   ├── ingestion.py       # Load transcripts + metadata
│   ├── cleaning.py        # Normalize text, flag poor quality
│   ├── analysis.py        # Single-call LLM classification
│   ├── batch.py           # Parallel analysis with ThreadPoolExecutor
│   ├── aggregation.py     # Weekly rollup + deterministic rules
│   ├── reporting.py       # Jinja2 template + LLM-generated summary
│   ├── llm.py             # OpenAI/OpenRouter client with retries + cost tracking
│   ├── rules.py           # Action rules (lost lead, complaint, revenue leak)
│   ├── models.py          # Pydantic data models
│   ├── db.py / db_models.py / db_crud.py  # SQLAlchemy persistence
│   ├── emailer.py         # SendGrid email delivery
│   ├── pii_redaction.py   # Phone/email/SSN/card/address scrubbing
│   └── logging.py         # Structlog configuration
├── configs/               # YAML: model, thresholds, workers, industry
├── industry_packs/        # Pluggable vertical configs
│   └── home_services/     # Taxonomy, action rules, report template
├── prompts/               # LLM system prompts
├── scripts/               # CLI entry points
├── tests/                 # 51 unit tests (pure logic, no API key needed)
└── data/                  # Sample transcripts + ground truth labels
```

---

## Roadmap

| Stage | Owner experience |
|-------|------------------|
| **Now** | Weekly markdown report, email delivery, automated pipeline |
| **Next** | Mobile-friendly HTML email, real phone system integration |
| **Then** | Paid pilots — track opens, actions taken, revenue impact |

[`plan.md`](plan.md) · [`docs/data_handling.md`](docs/data_handling.md) · [`docs/DISCLAIMER.md`](docs/DISCLAIMER.md)

---

## License & disclaimer

Licensed under the [MIT License](LICENSE).

Sample transcripts and demo reports are **fictional**. If you use CallGist on real calls, you are responsible for recording consent, privacy, and third-party API terms. AI-generated reports may be wrong — verify before acting. Full details: [`docs/DISCLAIMER.md`](docs/DISCLAIMER.md). Security: [`SECURITY.md`](SECURITY.md).