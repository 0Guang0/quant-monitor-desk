"""Source → F0 health profile bindings (YAML SSOT; not part of retired M-DATA-03 harness)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from backend.app.config import PROJECT_ROOT

_BINDINGS_PATH = PROJECT_ROOT / "specs/contracts/data_quality_rules.yaml"


@lru_cache(maxsize=1)
def load_source_health_bindings() -> dict[str, dict[str, Any]]:
    raw = yaml.safe_load(_BINDINGS_PATH.read_text(encoding="utf-8")) or {}
    return dict(raw["source_health_bindings"])


def _relative_to_data_root(data_root: Path, path: Path) -> str:
    return path.resolve().relative_to(data_root.resolve()).as_posix()


def _raw_path_belongs_to_source(rel_posix: str, source_id: str) -> bool:
    needle = f"raw/{source_id}/"
    legacy = f"raw/raw/{source_id}/"
    return (
        rel_posix.startswith(needle)
        or f"/{needle}" in rel_posix
        or rel_posix.startswith(legacy)
        or f"/{legacy}" in rel_posix
    )


def iter_raw_source_files(data_root: Path, source_id: str) -> list[Path]:
    raw_base = data_root / "raw"
    if not raw_base.is_dir():
        return []
    files: list[Path] = []
    for candidate in raw_base.rglob("*"):
        if not candidate.is_file():
            continue
        rel = _relative_to_data_root(data_root, candidate).replace("\\", "/")
        if _raw_path_belongs_to_source(rel, source_id):
            files.append(candidate)
    return sorted(files)


def latest_raw_evidence_dir(data_root: Path, source_id: str) -> Path | None:
    json_files = [
        path for path in iter_raw_source_files(data_root, source_id) if path.suffix == ".json"
    ]
    if not json_files:
        return None
    return max(json_files, key=lambda path: path.stat().st_mtime).parent


def run_f0_data_health(
    source_id: str, *, data_root: Path, db_path: Path
) -> tuple[str, str]:
    """Run F0 data health on latest raw evidence for a source; return (status, detail)."""
    from backend.app.ops.data_health import DataHealthLoadError
    from backend.app.ops.data_health_profiles import run_data_health_profile

    binding = load_source_health_bindings()[source_id]
    health_domain = str(binding["health_domain"])
    health_profile_id = str(binding["health_profile_id"])

    evidence_dir = latest_raw_evidence_dir(data_root, source_id)
    if evidence_dir is None:
        return "FAIL", "no raw evidence for F0 data health"

    try:
        report, *_ = run_data_health_profile(
            profile_id=health_profile_id,
            domain=health_domain,
            evidence_path=evidence_dir,
            db_path=db_path if db_path.is_file() else None,
            start_date=None,
            end_date=None,
            max_rows=1000,
            live_acceptance=True,
        )
    except DataHealthLoadError as exc:
        return "FAIL", f"F0 evidence unloadable: {exc}"

    status = str(report.overall_status)
    detail = report.gate_rationale or status
    if status in {"FAIL", "BLOCKED"}:
        return "FAIL", f"data-health {status}: {detail}"
    return status, detail


__all__ = [
    "iter_raw_source_files",
    "latest_raw_evidence_dir",
    "load_source_health_bindings",
    "run_f0_data_health",
]
