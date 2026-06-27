"""R3G-03 isolated pilot — dry-run or execute promote on pilot DuckDB only.

覆盖范围：baostock / cninfo / fred 三源顺序 promote
测试对象：隔离库 data/duckdb/quant_monitor_r3g03_pilot.duckdb（禁止主库 quant_monitor.duckdb）
目的/目标：Tier B 四门链真写仅落隔离库；主库零 mutation
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import yaml

from backend.app.config import PROJECT_ROOT
from backend.app.ops.sandbox_clean_write.approval_contract import (
    load_approval_contract,
    validate_approval_contract,
)
from backend.app.ops.sandbox_clean_write.limited_production_entry import (
    LimitedProductionEntryError,
    PromoteRequest,
    build_before_proof,
    run_limited_production_entry,
    write_before_proof,
)
from backend.app.ops.sandbox_clean_write.rollback_plan import (
    build_rollback_plan,
    write_rollback_plan,
)

PILOT_ROOT = PROJECT_ROOT / ".audit-sandbox" / "round3g" / "r3g03_pilot"
PILOT_DB = PROJECT_ROOT / "data" / "duckdb" / "quant_monitor_r3g03_pilot.duckdb"
MAIN_DB = PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb"
BACKUP_DIR = PILOT_ROOT / "backups"
FRED_AUTH = PROJECT_ROOT / ".audit-sandbox/round3g/fred_user_authorization.yaml"
EVIDENCE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "sandbox_clean_write" / "r3g01"
WINDOW_START = "2026-02-28"
WINDOW_END = "2026-06-27"
CN_SYMBOLS = ["sh.600000", "sh.600519", "sz.000001", "sh.601318", "sz.300750"]
FRED_SERIES = ["DGS10", "VIXCLS", "BAA10Y"]

PILOTS: tuple[dict, ...] = (
    {
        "slug": "baostock",
        "approval_id": "r3g03-pilot-baostock-20260627",
        "source_id": "baostock",
        "domain": "cn_equity_daily_bar",
        "symbols": CN_SYMBOLS,
        "max_rows": 800,
        "metadata_only": False,
        "live_fetch_authorized": False,
        "evidence": "tests/fixtures/sandbox_clean_write/r3g01/baostock/pilot_v2_closeout.json",
    },
    {
        "slug": "cninfo",
        "approval_id": "r3g03-pilot-cninfo-20260627",
        "source_id": "cninfo",
        "domain": "cn_announcements",
        "symbols": CN_SYMBOLS,
        "max_rows": 300,
        "metadata_only": True,
        "live_fetch_authorized": False,
        "evidence": "tests/fixtures/sandbox_clean_write/r3g01/cninfo/pilot_v2_closeout.json",
    },
    {
        "slug": "fred",
        "approval_id": "r3g03-pilot-fred-20260627",
        "source_id": "fred",
        "domain": "macro_series",
        "symbols": FRED_SERIES,
        "max_rows": 400,
        "metadata_only": False,
        "live_fetch_authorized": False,
        "evidence": "tests/fixtures/sandbox_clean_write/r3g01/fred/pilot_v2_closeout.json",
    },
)


def _write_pilot_artifacts(spec: dict) -> Path:
    slug = spec["slug"]
    run_dir = PILOT_ROOT / slug
    run_dir.mkdir(parents=True, exist_ok=True)
    db_rel = "data/duckdb/quant_monitor_r3g03_pilot.duckdb"
    audit_rel = f".audit-sandbox/round3g/r3g03_pilot/{slug}/audit_decision.json"
    rollback_rel = f".audit-sandbox/round3g/r3g03_pilot/{slug}/rollback_plan.json"

    symbols_key = "series" if spec["source_id"] == "fred" else "symbols"
    candidate_body: dict = {
        "source_id": spec["source_id"],
        "domain": spec["domain"],
        symbols_key: spec["symbols"],
        "start_date": WINDOW_START,
        "end_date": WINDOW_END,
        "max_rows": spec["max_rows"],
        "target_table": "market_bar_clean",
    }
    if spec["metadata_only"]:
        candidate_body["metadata_only"] = True
    if spec["live_fetch_authorized"]:
        candidate_body["live_fetch_authorized"] = True

    approval = {
        "approval_id": spec["approval_id"],
        "approver": "coordinator",
        "approved_at": "2026-06-27T12:00:00Z",
        "audit_decision_file": audit_rel,
        "source_candidates": [candidate_body],
        "production_db_path": db_rel,
        "rollback_plan_path": rollback_rel,
        "rollback_required": True,
        "no_agent_triggered_write": True,
        "no_cap_expansion": True,
    }
    audit = {
        "decision": "PASS_ALLOW_LIMITED_PROD_WRITE",
        "blocking_reasons": [],
        "warning_reasons": [],
        "evidence_paths": [spec["evidence"]],
        "production_mutation_allowed": False,
        "source_id": spec["source_id"],
        "domain": spec["domain"],
        symbols_key: spec["symbols"],
        "start_date": WINDOW_START,
        "end_date": WINDOW_END,
        "max_rows": spec["max_rows"],
        "target_table": "market_bar_clean",
        "production_db_path": db_rel,
    }

    approval_path = run_dir / "approval.yaml"
    audit_path = run_dir / "audit_decision.json"
    approval_path.write_text(yaml.dump(approval, sort_keys=False), encoding="utf-8")
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")

    contract = load_approval_contract(approval_path)
    _contract, _audit, candidate = validate_approval_contract(approval_path, audit_path)
    before = build_before_proof(PILOT_DB, candidate)
    before_path = run_dir / "before_proof.json"
    write_before_proof(before_path, before)
    rollback = build_rollback_plan(contract, candidate, before_proof=before)
    write_rollback_plan(run_dir / "rollback_plan.json", rollback)
    return run_dir


def _snapshot_pilot_db(slug: str) -> str:
    """Copy pilot DB before execute; return relative backup pointer for before_proof."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    rel = f".audit-sandbox/round3g/r3g03_pilot/backups/pre_{slug}.duckdb"
    dest = PROJECT_ROOT / rel
    if PILOT_DB.is_file():
        shutil.copy2(PILOT_DB, dest)
    return rel


def _refresh_before_proof(run_dir: Path, backup_pointer: str) -> None:
    approval_path = run_dir / "approval.yaml"
    audit_path = run_dir / "audit_decision.json"
    _contract, _audit, candidate = validate_approval_contract(approval_path, audit_path)
    before = build_before_proof(PILOT_DB, candidate, backup_or_snapshot_pointer=backup_pointer)
    write_before_proof(run_dir / "before_proof.json", before)
    contract = load_approval_contract(approval_path)
    rollback = build_rollback_plan(contract, candidate, before_proof=before)
    write_rollback_plan(run_dir / "rollback_plan.json", rollback)


def _run_promote(
    run_dir: Path,
    slug: str,
    *,
    execute: bool,
    allow_live_fetch: bool,
) -> dict:
    live_fetch = allow_live_fetch and slug == "fred"
    return run_limited_production_entry(
        PromoteRequest(
            approval_file=run_dir / "approval.yaml",
            audit_decision=run_dir / "audit_decision.json",
            before_proof=run_dir / "before_proof.json",
            after_proof=run_dir / "after_proof.json",
            rollback_plan=run_dir / "rollback_plan.json",
            evidence_dir=EVIDENCE_ROOT,
            dry_run=not execute,
            execute=execute,
            allow_live_fetch=live_fetch,
            fred_authorization=FRED_AUTH if slug == "fred" else None,
        )
    )


def _fred_live_ok(spec: dict) -> bool:
    if spec["slug"] != "fred":
        return False
    if not FRED_AUTH.is_file():
        return False
    api_env = "FRED_API_KEY"
    return bool(os.environ.get(api_env))


def main() -> int:
    parser = argparse.ArgumentParser(description="R3G-03 isolated pilot promote runner")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run --execute --no-dry-run on pilot DB only (default: dry-run)",
    )
    args = parser.parse_args()

    PILOT_ROOT.mkdir(parents=True, exist_ok=True)
    PILOT_DB.parent.mkdir(parents=True, exist_ok=True)
    main_mtime_before = MAIN_DB.stat().st_mtime if MAIN_DB.is_file() else None

    results: list[dict] = []
    failed = False
    for spec in PILOTS:
        slug = spec["slug"]
        if args.execute and _fred_live_ok(spec):
            spec = {**spec, "live_fetch_authorized": True}
        row: dict = {"slug": slug}
        try:
            run_dir = _write_pilot_artifacts(spec)
            if args.execute:
                backup = _snapshot_pilot_db(slug)
                _refresh_before_proof(run_dir, backup)
            report = _run_promote(
                run_dir,
                slug,
                execute=args.execute,
                allow_live_fetch=bool(spec.get("live_fetch_authorized")),
            )
            if args.execute:
                ok = (
                    report.get("production_mutation_allowed") is True
                    and report.get("dry_run") is False
                    and str(report.get("production_db_path", "")).endswith(
                        "quant_monitor_r3g03_pilot.duckdb"
                    )
                    and int(report.get("after_proof", {}).get("inserted_updated_row_count") or 0) > 0
                )
            else:
                ok = (
                    report.get("dry_run") is True
                    and report.get("production_mutation_allowed") is False
                )
            row["status"] = "PASS" if ok else "FAIL"
            row["validation_status"] = report.get("validation_status")
            row["write_id"] = report.get("write_manager_operation_id")
            row["inserted"] = report.get("after_proof", {}).get("inserted_updated_row_count")
            if not ok:
                failed = True
        except (LimitedProductionEntryError, Exception) as exc:
            failed = True
            row["status"] = "FAIL"
            row["error"] = str(exc)
        results.append(row)

    summary_name = "execute_summary.json" if args.execute else "dry_run_summary.json"
    summary_path = PILOT_ROOT / summary_name
    summary_path.write_text(
        json.dumps(
            {
                "pilot_db": str(PILOT_DB),
                "main_db": str(MAIN_DB),
                "execute": args.execute,
                "runs": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    for row in results:
        print(
            f"{row['slug']}: {row['status']} — "
            f"{row.get('validation_status') or row.get('error', '?')}"
        )
    print(f"summary: {summary_path}")
    print(f"pilot_db_exists: {PILOT_DB.is_file()}")
    if MAIN_DB.is_file():
        main_mtime_after = MAIN_DB.stat().st_mtime
        if main_mtime_before is not None and main_mtime_after != main_mtime_before:
            print("WARNING: main DB mtime changed — investigate")
            failed = True
        else:
            print(f"main_db_untouched: {MAIN_DB}")
    else:
        print("main_db_absent: ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
