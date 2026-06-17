"""Test helpers for database write paths."""

from __future__ import annotations

from backend.app.db.validation_gate import StubValidationGate
from backend.app.db.write_manager import WriteManager


def create_test_write_manager(conn_manager) -> WriteManager:
    """Explicit stub gate for tests — production must inject a real ValidationGate."""
    return WriteManager(conn_manager, StubValidationGate())
