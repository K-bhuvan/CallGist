# Disclaimer

**Please read before using CallGist with real customer data or publishing this repository.**

## Not legal advice

CallGist is software tooling. Nothing in this repository, documentation, or generated reports constitutes legal, compliance, or professional advice. Consult qualified counsel for call recording, privacy, and telecommunications rules in your jurisdiction.

## Sample data is fictional

Transcripts under `data/sample_transcripts/`, example emails in `README.md`, and demo business names (e.g. BrightPipe HVAC) are **synthetic** for development and demonstration. They do not represent real people or businesses.

## Your responsibilities with real call data

If you analyze real phone calls, **you** (or the business customer) are responsible for:

- **Recording and monitoring consent** — laws vary by country and US state (e.g. one-party vs all-party consent).
- **Privacy notices** — informing staff and, where required, callers that calls may be recorded or analyzed.
- **Data minimization** — uploading only what you need; avoiding payment card numbers and unnecessary personal data.
- **Retention and deletion** — honoring reasonable retention limits and deletion requests.
- **Third-party processing** — transcripts sent to an LLM provider (e.g. OpenAI) are subject to that provider’s terms and data policies. Review their documentation before processing customer conversations.

CallGist does not guarantee that use of the software complies with applicable law. Misuse can create regulatory and civil liability.

## Generated reports

AI-generated classifications, summaries, and recommendations may be **incorrect or incomplete**. Reports may include false lost-lead or complaint flags. Owners should verify high-stakes items (especially revenue and complaint claims) before acting. See the “Needs Review” section when confidence is low.

## No warranty

This project is provided **“as is”** under the [MIT License](../LICENSE), without warranty of any kind.

## Security

Do not commit API keys, `.env` files, or real customer recordings/transcripts to a public repository. See [SECURITY.md](../SECURITY.md).
