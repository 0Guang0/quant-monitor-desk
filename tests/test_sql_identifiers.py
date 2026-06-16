"""SQL identifier quoting tests (Round 1 task 008)."""

from __future__ import annotations

import pytest
from backend.app.db.sql_identifiers import quote_ident


def test_quoteIdent_validName_returnsQuoted() -> None:
    assert quote_ident("file_registry") == '"file_registry"'


def test_quoteIdent_withUnderscore_returnsQuoted() -> None:
    assert quote_ident("stg_foundation_smoke") == '"stg_foundation_smoke"'


def test_quoteIdent_injectionAttempt_raises() -> None:
    with pytest.raises(ValueError, match="invalid SQL identifier"):
        quote_ident("file_registry; DROP TABLE write_audit_log; --")


def test_quoteIdent_uppercase_raises() -> None:
    with pytest.raises(ValueError, match="invalid SQL identifier"):
        quote_ident("FileRegistry")


def test_quoteIdent_empty_raises() -> None:
    with pytest.raises(ValueError, match="invalid SQL identifier"):
        quote_ident("")
