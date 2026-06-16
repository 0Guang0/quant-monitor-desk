"""Round 1 stub ValidationGate (replaced in Round 2)."""

from __future__ import annotations


class ValidationGateError(RuntimeError):
    """Unknown or invalid validation_report_id."""


class ValidationRejected(RuntimeError):
    """Validation report indicates write must not proceed."""


class StubValidationGate:
    def assert_can_write(self, validation_report_id: str, write_mode: str) -> None:
        if validation_report_id.startswith("stub-pass-"):
            return
        if validation_report_id.startswith("stub-fail-"):
            raise ValidationRejected(f"validation rejected: {validation_report_id}")
        raise ValidationGateError(f"unknown validation_report_id: {validation_report_id}")
