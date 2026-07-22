"""PII redaction for transcripts before sending to LLM APIs."""
from __future__ import annotations

import re

# Patterns to look for. Phone numbers are the highest priority since they
# vary widely per country. We use a conservative regex that catches US/CA
# formats without being too aggressive.
_PATTERNS = [
    (
        "phone",
        re.compile(
            r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        ),
        "[PHONE]",
    ),
    (
        "email",
        re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
        "[EMAIL]",
    ),
    (
        "ssn",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "[SSN]",
    ),
    (
        "credit_card",
        re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
        "[CARD]",
    ),
    (
        "address",
        re.compile(
            r"\b\d{1,5}\s+[\w\s,.]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Court|Ct|Place|Pl|Boulevard|Blvd|Terrace|Ter|Way|Circle|Cir|Trail|Trl|Parkway|Pkwy)\b",
            re.IGNORECASE,
        ),
        "[ADDRESS]",
    ),
]


def redact(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    result = text
    for label, pattern, replacement in _PATTERNS:
        result, n = pattern.subn(replacement, result)
        if n > 0:
            counts[label] = n
    return result, counts


def should_redact(text: str) -> bool:
    return any(pattern.search(text) for _, pattern, _ in _PATTERNS)
