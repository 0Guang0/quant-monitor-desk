"""Shared sensitive error-message redaction for persistence layers."""

from __future__ import annotations

import re

_SENSITIVE_ERROR_PATTERNS = (
    re.compile(r"(?i)\b(token|password|api[_-]?key|apikey|secret)\b\s*[:=]\s*[^,\s;]+"),
    re.compile(r"(?i)\bauthorization\b\s*[:=]\s*[^,\s;]+(?:\s+[^,\s;]+)?"),
    re.compile(r"(?i)\bbearer\s+[^,\s;]+"),
)


def redact_error_message(message: str | None) -> str | None:
    if message is None:
        return None
    redacted = message
    for pattern in _SENSITIVE_ERROR_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted
