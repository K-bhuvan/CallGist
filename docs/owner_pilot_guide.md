# Owner pilot guide (Milestone 1)

Use this checklist when you show a CallGist weekly report to a home-services business owner for the first time. The goal is trust and clarity—not a product demo of every technical detail.

## Before the meeting

- [ ] Run the pipeline on the owner’s pilot week (or sample data): `python scripts/run_analysis.py` then `python scripts/generate_sample_report.py`.
- [ ] Open [`outputs/sample_report.md`](../outputs/sample_report.md) and skim executive summary, volume counts, and top pain points.
- [ ] Confirm you can explain **one example call** from [`outputs/analyses/`](../outputs/analyses/) if the owner asks “how do you know that?”
- [ ] Read [`docs/data_handling.md`](data_handling.md) and be ready to state retention and deletion policy.
- [ ] Optional: run `python scripts/ground_truth_review.py` if you have human-labeled calls for accuracy context.

## During the meeting (30–45 minutes)

1. **Frame the product** (2 min): “This turns your phone calls into a short weekly action list—not a transcript dump.”
2. **Walk the report top to bottom** (15 min):
   - Call volume: new leads, lost leads, follow-ups, complaints (rules-based counts).
   - Top intents and pain points with **one quote** from evidence.
   - Revenue leak examples and complaint summary.
   - Recommended actions for next week.
   - Follow-up list with suggested actions per call.
3. **Ask grounding questions** (10 min):
   - “Does this match what you felt happened this week?”
   - “Which lost lead or follow-up would you have handled first?”
   - “Is any pain point missing or mislabeled?”
4. **Capture feedback** (5 min): note wrong intents, missing outcomes, and wording the owner dislikes.

## After the meeting

- [ ] Update taxonomy or prompts only with owner agreement; re-run analysis for affected calls.
- [ ] Adjust `industry_packs/home_services/action_rules.yaml` if lost-lead or follow-up rules do not match how the owner runs the shop.
- [ ] Store owner-approved report copy under `outputs/` with a dated filename if they want a record.
- [ ] Do not share raw transcripts outside agreed pilot terms.

## What to avoid

- Do not claim 100% accuracy; show confidence and “needs review” rows when present.
- Do not promise automatic CRM integration (Milestone 2+).
- Do not leave API keys or `.env` on a shared screen.

## Success criteria for the pilot readout

The owner can name **three concrete actions** they will take next week based on the report, and at least one pain point they agree is real and frequent.
