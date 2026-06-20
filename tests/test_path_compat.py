"""Tests for Windows long-path compatibility helpers."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from backend.app.storage.path_compat import (
    is_file,
    needs_extended_path,
    to_extended_path,
    write_bytes,
)


def test_needsExtendedPath_shortPath_false(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("Windows-only")
    assert needs_extended_path(tmp_path) is False


def test_toExtendedPath_longPath_writesReadable(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("Windows-only")
    # Mirror deep basetemp evidence layout (~275 chars) that broke phase3/4 tests.
    deep = (
        tmp_path
        / ".audit-sandbox"
        / "pytest-9agent-restored-targeted"
        / "test_layer1Ingestion_phase3_taskEvidenceArtifacts0"
        / "evidence"
        / ".phase3-micro-fetch-sandbox"
        / "data"
        / "raw"
        / "akshare"
        / "macro_supplementary"
        / "2024-06-15"
    )
    from backend.app.storage.path_compat import mkdir_parents

    mkdir_parents(deep, exist_ok=True)
    target = deep / ("a" * 64 + ".json")
    assert needs_extended_path(target)
    write_bytes(target, b"ok")
    assert is_file(target)
    assert to_extended_path(target).read_bytes() == b"ok"
