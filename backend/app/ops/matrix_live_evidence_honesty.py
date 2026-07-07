"""Matrix live evidence honesty — mock/replay must not back live PASS rows (ADR-016)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_NON_LIVE_ID_RE = re.compile(
    r"(^|[-_/])(?:mock|replay)(?:[-_/]|$)|[-_]mock[-_]|[-_]replay[-_]",
    re.IGNORECASE,
)
_REPLAY_FIXTURE_PATH_RE = re.compile(r"tests[/\\]fixtures[/\\]replay", re.IGNORECASE)
_REPLAY_HASH_RE = re.compile(r"replay-hash", re.IGNORECASE)
_NON_LIVE_PROVENANCE = frozenset({"mock_replay", "mock", "replay", "dry_run"})

_IDENTIFIER_FIELDS = (
    "source_fetch_id",
    "fetch_id",
    "run_id",
    "content_hash",
    "fetch_provenance",
    "implementation_mode",
)


def non_live_marker_reasons_from_identifier(value: str) -> tuple[str, ...]:
    """Return human-readable reasons when an id/hash looks mock or replay backed."""
    text = str(value or "").strip()
    if not text:
        return ()
    reasons: list[str] = []
    if _NON_LIVE_ID_RE.search(text):
        reasons.append(f"identifier contains mock/replay marker: {text!r}")
    if _REPLAY_HASH_RE.search(text):
        reasons.append(f"content_hash looks replay-backed: {text!r}")
    if text.lower() in _NON_LIVE_PROVENANCE:
        reasons.append(f"provenance classification is non-live: {text!r}")
    return tuple(reasons)


def _reasons_from_mapping(payload: dict[str, Any], *, path_hint: str) -> tuple[str, ...]:
    reasons: list[str] = []
    for field in _IDENTIFIER_FIELDS:
        if field not in payload:
            continue
        value = payload.get(field)
        if isinstance(value, str):
            for reason in non_live_marker_reasons_from_identifier(value):
                reasons.append(f"{path_hint}{field}: {reason}")
    for field in ("relative_paths", "raw_file_paths"):
        raw_paths = payload.get(field)
        if isinstance(raw_paths, str):
            raw_paths = [raw_paths]
        if isinstance(raw_paths, list):
            for item in raw_paths:
                path_text = str(item)
                if _REPLAY_FIXTURE_PATH_RE.search(path_text):
                    reasons.append(f"{path_hint}{field}: replay fixture path {path_text!r}")
    return tuple(reasons)


def non_live_marker_reasons_from_json_payload(
    payload: object,
    *,
    path_hint: str = "",
) -> tuple[str, ...]:
    """Scan parsed JSON for mock/replay evidence markers."""
    if isinstance(payload, dict):
        return _reasons_from_mapping(payload, path_hint=path_hint)
    if isinstance(payload, list):
        reasons: list[str] = []
        for index, item in enumerate(payload):
            reasons.extend(
                non_live_marker_reasons_from_json_payload(item, path_hint=f"{path_hint}[{index}].")
            )
        return tuple(reasons)
    return ()


def _raw_path_belongs_to_source(rel_posix: str, source_id: str) -> bool:
    needle = f"raw/{source_id}/"
    legacy = f"raw/raw/{source_id}/"
    return (
        rel_posix.startswith(needle)
        or f"/{needle}" in rel_posix
        or rel_posix.startswith(legacy)
        or f"/{legacy}" in rel_posix
    )


def iter_source_raw_evidence_files(data_root: Path, source_id: str) -> list[Path]:
    raw_base = data_root / "raw"
    if not raw_base.is_dir():
        return []
    files: list[Path] = []
    for candidate in raw_base.rglob("*"):
        if not candidate.is_file():
            continue
        rel = candidate.relative_to(data_root).as_posix()
        if _raw_path_belongs_to_source(rel, source_id):
            files.append(candidate)
    return sorted(files)


def _scan_fetch_log_non_live_markers(
    db_path: Path,
    source_id: str,
    *,
    target_key: str,
) -> list[str]:
    try:
        import duckdb
    except ImportError:
        return [f"{target_key}: duckdb unavailable for fetch_log honesty scan"]
    if not db_path.is_file():
        return []
    violations: list[str] = []
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
        if "fetch_log" not in tables:
            return []
        rows = con.execute(
            """
            SELECT fetch_id, raw_file_paths, content_hash
            FROM fetch_log
            WHERE source_id = ?
            """,
            [source_id],
        ).fetchall()
    finally:
        con.close()
    for fetch_id, raw_file_paths, content_hash in rows:
        for reason in non_live_marker_reasons_from_identifier(str(fetch_id or "")):
            violations.append(f"{target_key}: fetch_log.fetch_id {reason}")
        for reason in non_live_marker_reasons_from_identifier(str(content_hash or "")):
            violations.append(f"{target_key}: fetch_log.content_hash {reason}")
        if raw_file_paths and _REPLAY_FIXTURE_PATH_RE.search(str(raw_file_paths)):
            violations.append(
                f"{target_key}: fetch_log.raw_file_paths replay fixture path {raw_file_paths!r}"
            )
    return violations


def collect_live_pass_row_evidence_violations(
    data_root: Path,
    row: dict[str, object],
    *,
    target_key: str,
) -> list[str]:
    """Return violations when a live PASS row is backed by mock/replay evidence."""
    if row.get("status") != "PASS":
        return []
    if row.get("implementation_mode") != "live":
        return []
    source_id = str(row.get("source_id") or "")
    if not source_id:
        return [f"{target_key}: live PASS row missing source_id"]

    violations: list[str] = []
    for path in iter_source_raw_evidence_files(data_root, source_id):
        if path.suffix.lower() not in {".json", ".ndjson"}:
            continue
        rel = path.relative_to(data_root).as_posix()
        if _REPLAY_FIXTURE_PATH_RE.search(rel):
            violations.append(f"{target_key}: raw path under replay fixtures: {rel}")
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        for reason in non_live_marker_reasons_from_json_payload(parsed, path_hint=f"{rel}:"):
            violations.append(f"{target_key}: {reason}")

    db_path = data_root / "duckdb" / "quant_monitor.duckdb"
    violations.extend(
        _scan_fetch_log_non_live_markers(db_path, source_id, target_key=target_key)
    )
    return violations


def validate_matrix_live_evidence_honesty(
    data_root: Path,
    payload: dict[str, object],
) -> list[str]:
    """Scan all matrix rows; reject live PASS rows backed by mock/replay evidence."""
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return ["matrix report rows missing or not a list"]
    violations: list[str] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        target_key = str(item.get("target") or item.get("source_id") or "unknown")
        violations.extend(
            collect_live_pass_row_evidence_violations(data_root, item, target_key=target_key)
        )
    return violations


def resolve_matrix_report_data_root(
    *,
    report_path: Path | None,
    payload: dict[str, object],
    explicit_data_root: Path | None,
) -> Path | None:
    if explicit_data_root is not None:
        return explicit_data_root
    bound = payload.get("data_root")
    if isinstance(bound, str) and bound.strip():
        return Path(bound)
    if report_path is None:
        return None
    if report_path.name == "source-matrix-acceptance.json" and report_path.parent.name == "reports":
        return report_path.parent.parent
    return None


__all__ = [
    "collect_live_pass_row_evidence_violations",
    "iter_source_raw_evidence_files",
    "non_live_marker_reasons_from_identifier",
    "non_live_marker_reasons_from_json_payload",
    "resolve_matrix_report_data_root",
    "validate_matrix_live_evidence_honesty",
]
