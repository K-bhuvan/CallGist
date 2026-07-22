"""Email delivery via SendGrid for weekly reports."""
from __future__ import annotations

import os

from python_http_client import exceptions as http_exceptions
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Email,
    HtmlContent,
    Mail,
    PlainTextContent,
    To,
)

from core.logging import get_logger

logger = get_logger(__name__)

FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "reports@callgist.app")
FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "CallGist")


def _get_client() -> SendGridAPIClient | None:
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        logger.warning("SENDGRID_API_KEY not set — email delivery disabled")
        return None
    return SendGridAPIClient(api_key)


def _render_html_body(report_markdown: str) -> str:
    import re

    html = report_markdown
    html = re.sub(r"^# (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^- \*\*(.+?)\*\*", r"<li><strong>\1</strong>", html, flags=re.MULTILINE)
    html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = f"""<html><body style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:600px;margin:0 auto;padding:20px;line-height:1.6">
{html}
</body></html>"""
    return html


def send_report(
    to_email: str,
    report_markdown: str,
    subject: str | None = None,
    business_name: str = "Business",
    week_label: str = "",
) -> bool:
    client = _get_client()
    if client is None:
        return False

    if subject is None:
        subject = f"{business_name} — Weekly CallGist ({week_label})"

    from_email = Email(FROM_EMAIL, FROM_NAME)
    to = To(to_email)

    try:
        mail = Mail(
            from_email=from_email,
            to_emails=[to],
            subject=subject,
            plain_text_content=PlainTextContent(report_markdown),
            html_content=HtmlContent(_render_html_body(report_markdown)),
        )
        response = client.send(mail)
        logger.info(
            "Email sent to %s — status %s",
            to_email,
            response.status_code,
        )
        return response.status_code in (200, 201, 202)
    except http_exceptions.UnauthorizedError:
        logger.error("SendGrid auth failed — check SENDGRID_API_KEY")
        return False
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False
