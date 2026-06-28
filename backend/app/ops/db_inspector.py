"""Read-only DB and data-root inspector (Round 3 Batch 1 Phase A)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import yaml
from backend.app.db.connection import ConnectionManager
from backend.app.db.sql_identifiers import quote_ident

_OPS_INSPECT_CONTRACT = (
    Path(__file__).resolve().parents[3] / "specs/contracts/ops_db_inspect_contract.yaml"
)


def _key_tables_from_contract(raw: dict[str, Any]) -> tuple[str, ...]:
    key_tables = raw.get("key_tables")
    if not key_tables:
        raise ValueError("ops_db_inspect_contract: key_tables required")
    names = tuple(str(name) for name in key_tables)
    for name in names:
        quote_ident(name)
    return names


def _deferred_mapping_from_contract(
    raw: dict[str, Any],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    mapping = raw.get("deferred_item_mapping") or {}
    items: list[tuple[str, tuple[str, ...]]] = []
    for item_id, spec in mapping.items():
        if not isinstance(spec, dict):
            raise ValueError(f"invalid deferred_item_mapping entry for {item_id!r}")
        if "evidence_fields" in spec:
            fields = tuple(str(field) for field in spec["evidence_fields"])
        elif "rule" in spec:
            fields = (f"rule: {spec['rule']}",)
        else:
            raise ValueError(
                f"deferred_item_mapping[{item_id!r}] missing evidence_fields or rule"
            )
        items.append((str(item_id), fields))
    items.sort(key=lambda item: item[0])
    return tuple(items)


_raw_contract = yaml.safe_load(_OPS_INSPECT_CONTRACT.read_text(encoding="utf-8"))
_contract: dict[str, Any] = _raw_contract if isinstance(_raw_contract, dict) else {}
KEY_TABLES: tuple[str, ...] = _key_tables_from_contract(_contract)
DEFERRED_ITEM_MAPPING: tuple[tuple[str, tuple[str, ...]], ...] = _deferred_mapping_from_contract(
    _contract
)

# Layer 5 tables — listed for forward inventory; no migration until Batch 5 (023).
FUTURE_PHASE_KEY_TABLES: frozenset[str] = frozenset({"instrument_registry", "security_bar_1d"})

REQUIRED_TOP_LEVEL_FIELDS: tuple[str, ...] = (
    "status",
    "generated_at",
    "mode",
    "db",
    "data_root",
    "schema",
    "key_tables",
    "evidence",
    "warnings",
    "errors",
    "deferred_item_mapping",
)

EMPTY_EVIDENCE: dict[str, Any] = {
    "latest_fetch": {
        "fetch_time": None,
        "source_id": None,
        "status": None,
        "row_count": None,
    },
    "job_status_counts": {},
    "validation_status_counts": {},
    "conflict_status_counts": {},
    "manual_review_status_counts": {},
    "latest_write": None,
}


@dataclass
class InspectReport:
    status: str
    generated_at: str
    mode: str = "read_only"
    db: dict[str, Any] = field(default_factory=dict)
    data_root: dict[str, Any] = field(default_factory=dict)
    schema: dict[str, Any] = field(default_factory=dict)
    key_tables: list[dict[str, Any]] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    deferred_item_mapping: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DbInspector:
    """Read-only inspector for local DuckDB and adjacent data-root evidence."""

    def __init__(
        self,
        db_path: Path | str,
        data_root: Path | str,
        *,
        limit: int = 20,
        include_path_check: bool = True,
        profile: str = "eco",
    ) -> None:
        self.db_path = Path(db_path)
        self.data_root = Path(data_root)
        self.limit = min(max(limit, 1), 100)
        self.include_path_check = include_path_check
        self.profile = profile

    def inspect(self) -> InspectReport:
        generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        report = InspectReport(
            status="PASS",
            generated_at=generated_at,
            deferred_item_mapping=_build_deferred_mapping(),
        )
        report.data_root = self._inspect_data_root(report)
        report.db = self._build_db_block(report)
        if report.db.get("exists") and not report.errors:
            self._populate_db_contents(report)
        report.status = _derive_status(report)
        return report

    def _inspect_data_root(self, report: InspectReport) -> dict[str, Any]:
        root = self.data_root
        exists = root.exists()
        block: dict[str, Any] = {
            "path": str(root),
            "exists": exists,
            "raw_files_count": 0,
            "parquet_files_count": 0,
            "audit_files_count": 0,
            "report_files_count": 0,
            "scan_limited": False,
        }
        if not exists or not self.include_path_check:
            return block

        scan_limited = False
        try:
            for key, subdir in (
                ("raw_files_count", "raw"),
                ("parquet_files_count", "parquet"),
                ("audit_files_count", "audit"),
                ("report_files_count", "report"),
            ):
                count, limited = _count_files_under(root / subdir, self.limit, root)
                block[key] = count
                scan_limited = scan_limited or limited
        except OSError as exc:
            report.warnings.append(f"data root scan partial failure: {exc}")
        block["scan_limited"] = scan_limited
        return block

    def _build_db_block(self, report: InspectReport) -> dict[str, Any]:
        block: dict[str, Any] = {
            "path": str(self.db_path),
            "exists": self.db_path.exists(),
            "read_only_open": False,
            "file_size_bytes": 0,
            "connection_error": None,
        }
        if not block["exists"]:
            report.errors.append(f"database file not found: {self.db_path}")
            return block

        try:
            block["file_size_bytes"] = self.db_path.stat().st_size
        except OSError as exc:
            report.errors.append(f"failed to stat database file: {exc}")
        return block

    def _populate_db_contents(self, report: InspectReport) -> None:
        try:
            cm = ConnectionManager(self.db_path, profile=self.profile)
            with cm.reader() as con:
                con.execute("SELECT 1").fetchone()
                report.db["read_only_open"] = True
                try:
                    tables = _list_tables(con)
                    table_set = set(tables)
                    report.schema = {"tables": tables, "table_count": len(tables)}
                    report.key_tables = [_table_stats(con, name, tables) for name in KEY_TABLES]
                except Exception as exc:
                    report.errors.append(f"schema introspection failed: {exc}")
                    report.schema = {"tables": [], "table_count": 0, "error": str(exc)}
                    report.key_tables = [
                        {"name": name, "exists": False, "row_count": None, "error": str(exc)}
                        for name in KEY_TABLES
                    ]
                    table_set = set()
                try:
                    if not table_set:
                        table_set = set(_list_tables(con))
                    report.evidence = {
                        "latest_fetch": _latest_fetch(con, table_set),
                        "job_status_counts": _status_counts(
                            con, table_set, "data_sync_job", "status"
                        ),
                        "validation_status_counts": _status_counts(
                            con, table_set, "validation_report", "status"
                        ),
                        "conflict_status_counts": _status_counts(
                            con, table_set, "source_conflict", "reconcile_status"
                        ),
                        "manual_review_status_counts": _status_counts(
                            con, table_set, "manual_review_queue", "status"
                        ),
                        "latest_write": _latest_write(con, table_set),
                    }
                except Exception as exc:
                    report.warnings.append(f"evidence collection partial failure: {exc}")
                    report.evidence = dict(EMPTY_EVIDENCE)
        except Exception as exc:  # pragma: no cover - surfaced in report.errors
            report.db["connection_error"] = str(exc)
            report.errors.append(f"failed to open database read-only: {exc}")


def _build_deferred_mapping() -> list[dict[str, Any]]:
    return [
        {"item_id": item_id, "evidence_fields": list(fields)}
        for item_id, fields in DEFERRED_ITEM_MAPPING
    ]


def _count_files_under(directory: Path, cap: int, data_root: Path) -> tuple[int, bool]:
    if not directory.is_dir():
        return 0, False
    resolved_root = data_root.resolve()
    count = 0
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        try:
            if not path.resolve().is_relative_to(resolved_root):
                continue
        except (OSError, ValueError):
            continue
        count += 1
        if count >= cap:
            return count, True
    return count, False


def _list_tables(con: duckdb.DuckDBPyConnection) -> list[str]:
    rows = con.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
        """
    ).fetchall()
    return [str(row[0]) for row in rows]


def _table_stats(con: duckdb.DuckDBPyConnection, name: str, tables: list[str]) -> dict[str, Any]:
    if name not in tables:
        return {"name": name, "exists": False, "row_count": None, "error": None}
    try:
        quoted = quote_ident(name)
        row_count = con.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0]
        return {
            "name": name,
            "exists": True,
            "row_count": int(row_count),
            "error": None,
        }
    except Exception as exc:
        return {"name": name, "exists": True, "row_count": None, "error": str(exc)}


def _latest_fetch(con: duckdb.DuckDBPyConnection, tables: set[str]) -> dict[str, Any]:
    empty = dict(EMPTY_EVIDENCE["latest_fetch"])
    if "fetch_log" not in tables:
        return empty
    row = con.execute(
        """
        SELECT fetch_time, source_id, status, row_count
        FROM fetch_log
        ORDER BY fetch_time DESC NULLS LAST
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return empty
    fetch_time, source_id, status, row_count = row
    return {
        "fetch_time": fetch_time.isoformat() if hasattr(fetch_time, "isoformat") else fetch_time,
        "source_id": source_id,
        "status": status,
        "row_count": row_count,
    }


def _status_counts(
    con: duckdb.DuckDBPyConnection, tables: set[str], table_name: str, status_col: str
) -> dict[str, int]:
    if table_name not in tables:
        return {}
    quoted_table = quote_ident(table_name)
    quoted_col = quote_ident(status_col)
    rows = con.execute(
        f"""
        SELECT {quoted_col}, COUNT(*)
        FROM {quoted_table}
        GROUP BY {quoted_col}
        """
    ).fetchall()
    return {str(status or "NULL"): int(count) for status, count in rows}


def _latest_write(con: duckdb.DuckDBPyConnection, tables: set[str]) -> dict[str, Any] | None:
    if "write_audit_log" not in tables:
        return None
    row = con.execute(
        """
        SELECT write_id, target_table, write_mode, finished_at
        FROM write_audit_log
        ORDER BY finished_at DESC NULLS LAST
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return None
    write_id, target_table, write_mode, finished_at = row
    return {
        "write_id": write_id,
        "table_name": target_table,
        "operation": write_mode,
        "written_at": finished_at.isoformat() if hasattr(finished_at, "isoformat") else finished_at,
    }


def _derive_status(report: InspectReport) -> str:
    if report.errors:
        return "FAIL"
    if not report.db.get("exists") or not report.db.get("read_only_open"):
        return "FAIL"
    if report.schema.get("error"):
        return "FAIL"

    key_exists = [t for t in report.key_tables if t.get("exists")]
    if not key_exists:
        return "FAIL"

    total_rows = sum(int(t.get("row_count") or 0) for t in report.key_tables if t.get("exists"))
    has_fetch_evidence = bool(report.evidence.get("latest_fetch", {}).get("fetch_time"))
    raw_count = int(report.data_root.get("raw_files_count") or 0)
    parquet_count = int(report.data_root.get("parquet_files_count") or 0)

    if total_rows == 0 and not has_fetch_evidence and raw_count == 0 and parquet_count == 0:
        return "WARN"
    if total_rows == 0:
        return "WARN"
    if raw_count == 0 and parquet_count == 0:
        return "WARN"
    return "PASS"


def format_text_report(report: InspectReport) -> str:
    """Human-readable summary for --format text."""
    db_state = "exists and opened read-only" if report.db.get("read_only_open") else "not available"
    lines = [
        f"QMD DB Inspect: {report.status}",
        f"DB: {report.db.get('path')} {db_state}",
        f"Tables: {report.schema.get('table_count', 0)} found",
    ]
    tables_by_name = {t.get("name"): t.get("row_count") for t in report.key_tables}
    fetch_rows = tables_by_name.get("fetch_log", 0)
    job_rows = tables_by_name.get("data_sync_job", 0)
    validation_rows = tables_by_name.get("validation_report", 0)
    lines.append(
        f"Evidence: fetch_log={fetch_rows}, data_sync_job={job_rows}, "
        f"validation_report={validation_rows}"
    )
    lines.append(
        f"Data root: raw={report.data_root.get('raw_files_count', 0)}, "
        f"parquet={report.data_root.get('parquet_files_count', 0)}"
    )
    if report.status == "WARN":
        lines.append(
            "Meaning: database is present, but this run does not prove "
            "real vendor data ingestion yet."
        )
    elif report.status == "FAIL":
        lines.append("Meaning: inspection could not complete successfully.")
        if report.errors:
            lines.append(f"Errors: {'; '.join(report.errors)}")
    return "\n".join(lines)
