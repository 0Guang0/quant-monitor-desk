"""CLI failure envelope aligned with docs/ops/ERROR_CODE_GUIDE.md."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CliFailure(RuntimeError):
    error_code: str
    message: str
    docs_anchor: str
    retryable: bool = False
    manual_confirmation_required: bool = False

    def __str__(self) -> str:
        return self.message

    def exit_code(self) -> int:
        return 2

    def format_text(self) -> str:
        return (
            f"error_code={self.error_code}\n"
            f"message={self.message}\n"
            f"docs_anchor={self.docs_anchor}\n"
            f"retryable={str(self.retryable).lower()}\n"
            f"manual_confirmation_required={str(self.manual_confirmation_required).lower()}\n"
        )

    def format_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


_ROUTE_STATUS_TO_ERROR: dict[str, str] = {
    "DISABLED_SOURCE": "DISABLED_SOURCE",
    "NO_AVAILABLE_SOURCE": "NO_AVAILABLE_SOURCE",
    "CAPABILITY_MISSING": "CAPABILITY_MISSING",
    "USER_AUTH_REQUIRED": "USER_AUTH_REQUIRED",
    "VALIDATION_ONLY_BLOCKED": "DISABLED_SOURCE",
}


def error_for_route_status(route_status: str, *, detail: str) -> CliFailure:
    code = _ROUTE_STATUS_TO_ERROR.get(route_status, "NO_AVAILABLE_SOURCE")
    anchor = {
        "DISABLED_SOURCE": "docs/ops/incident_playbook.md#disabled-source",
        "CAPABILITY_MISSING": "docs/ops/ERROR_CODE_GUIDE.md#capability-missing",
        "USER_AUTH_REQUIRED": "docs/ops/ERROR_CODE_GUIDE.md#user-auth-required",
    }.get(code, "docs/ops/ERROR_CODE_GUIDE.md")
    return CliFailure(
        error_code=code,
        message=detail,
        docs_anchor=anchor,
        manual_confirmation_required=code in {"DISABLED_SOURCE", "USER_AUTH_REQUIRED"},
    )
