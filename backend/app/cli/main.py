"""Unified packaged CLI: `qmd-ops` / `qmd-data` entrypoints."""

from __future__ import annotations

import argparse
import sys

from backend.app.cli import data_commands
from backend.app.cli.errors import CliFailure, DOCS_ANCHOR_DATA_SYNC_CLI


def _build_data_parser(sub: argparse._SubParsersAction) -> None:
    data = sub.add_parser("data", help="Data sync CLI (dry-run / route-preview first)")
    data_sub = data.add_subparsers(dest="data_command", required=True)

    rp = data_sub.add_parser("route-preview", help="Read-only SourceRoutePlan preview")
    rp.add_argument("--domain", required=True, dest="data_domain")
    rp.add_argument("--operation", default=None)
    rp.add_argument("--market-id", default=None)
    rp.add_argument("--use-fallback", action="store_true")
    rp.add_argument("--format", choices=["json", "text"], default="json")

    sync = data_sub.add_parser(
        "sync",
        help=(
            "Sync job (default dry-run). Tier A: --source-id <id> (11 sources, ADR-009). "
            "Legacy: --domain cn_equity_daily_bar (baostock) or macro_series --source-id fred."
        ),
    )
    sync.add_argument(
        "--domain",
        required=True,
        dest="data_domain",
        help="e.g. cn_equity_daily_bar, macro_series",
    )
    sync.add_argument("--source-id", default=None, dest="source_id")
    sync.add_argument("--operation", default=None)
    sync.add_argument("--start", default=None)
    sync.add_argument("--end", default=None)
    sync.add_argument("--since", default=None)
    sync.add_argument("--instrument-id", default=None, dest="instrument_id")
    sync.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Plan only; default true (R3F-CLI-01)",
    )
    sync.add_argument("--format", choices=["json", "text"], default="json")

    backfill = data_sub.add_parser(
        "backfill",
        help="Bounded historical backfill (R3-DCP-09 · default dry-run)",
    )
    backfill.add_argument("--domain", required=True, dest="data_domain")
    backfill.add_argument("--source-id", required=True, dest="source_id")
    backfill.add_argument("--start", required=True)
    backfill.add_argument("--end", required=True)
    backfill.add_argument("--instrument-id", default=None, dest="instrument_id")
    backfill.add_argument("--max-shards", type=int, default=None, dest="max_shards")
    backfill.add_argument("--truncate-to-cap", action="store_true")
    backfill.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    backfill.add_argument("--format", choices=["json", "text"], default="json")

    full_load = data_sub.add_parser(
        "full-load",
        help="Full domain load with checkpoint resume (§13.4.1 · default dry-run)",
    )
    full_load.add_argument("--domain", required=True, dest="data_domain")
    full_load.add_argument("--source-id", required=True, dest="source_id")
    full_load.add_argument("--start", required=True)
    full_load.add_argument("--end", default=None)
    full_load.add_argument("--instrument-id", default=None, dest="instrument_id")
    full_load.add_argument("--max-shards", type=int, default=None, dest="max_shards")
    full_load.add_argument("--truncate-to-cap", action="store_true")
    full_load.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    full_load.add_argument("--format", choices=["json", "text"], default="json")

    live_fetch = data_sub.add_parser(
        "live-fetch",
        help="Product live fetch (default dry-run · R3H-08 S08-05)",
    )
    live_fetch.add_argument("--source-id", required=True, dest="source_id")
    live_fetch.add_argument("--domain", required=True, dest="data_domain")
    live_fetch.add_argument("--operation", default=None)
    live_fetch.add_argument("--instrument-id", default=None, dest="instrument_id")
    live_fetch.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    live_fetch.add_argument("--format", choices=["json", "text"], default="json")

    init_p = data_sub.add_parser("init-basic", help="Initialize schema (default dry-run)")
    init_p.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    init_p.add_argument("--db", type=str, default=None)
    init_p.add_argument("--format", choices=["json", "text"], default="json")

    health = data_sub.add_parser("health", help="Read-only data health profile (market_bar_p0)")
    health.add_argument("--domain", required=True, dest="data_domain")
    health.add_argument("--profile", required=True)
    health.add_argument("--evidence-dir", default=None, dest="evidence_dir")
    health.add_argument("--db-path", default=None, dest="db_path")
    health.add_argument("--start", default=None)
    health.add_argument("--end", default=None)
    health.add_argument("--max-rows", type=int, default=1000)
    health.add_argument("--format", choices=["json", "text"], default="json")
    health.add_argument("--allow-network", action="store_true")
    health.add_argument("--clean-write", action="store_true")
    health.add_argument("--full-market-scan", action="store_true")
    health.add_argument("--full-history", action="store_true")

    sched = data_sub.add_parser("scheduler", help="Built-in sync scheduler (§13.6 · default dry-run)")
    sched_sub = sched.add_subparsers(dest="scheduler_command", required=True)
    sched_run = sched_sub.add_parser("run", help="Run a named scheduler profile")
    sched_run.add_argument("--profile", required=True)
    sched_run.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    sched_run.add_argument("--format", choices=["json", "text"], default="json")

    incremental = data_sub.add_parser(
        "incremental",
        help="Daily incremental via scheduler profile (§13.7)",
    )
    incremental.add_argument("--profile", required=True)
    incremental.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    incremental.add_argument("--format", choices=["json", "text"], default="json")

    rev_audit = data_sub.add_parser("revision-audit", help="Revision audit job (§13.7)")
    rev_audit.add_argument("--domain", required=True, dest="data_domain")
    rev_audit.add_argument("--market", required=True, dest="market_id")
    rev_audit.add_argument("--lookback-days", type=int, default=90, dest="lookback_days")
    rev_audit.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    rev_audit.add_argument("--format", choices=["json", "text"], default="json")

    reconcile = data_sub.add_parser("reconcile", help="Conflict reconcile (§13.7)")
    reconcile.add_argument("--conflict-id", required=True, dest="conflict_id")
    reconcile.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    reconcile.add_argument("--format", choices=["json", "text"], default="json")

    quality = data_sub.add_parser("quality-check", help="Data quality check job (§13.7)")
    quality.add_argument("--domain", required=True, dest="data_domain")
    quality.add_argument("--date", required=True, dest="check_date")
    quality.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    quality.add_argument("--format", choices=["json", "text"], default="json")


def _run_data(args: argparse.Namespace) -> int:
    fmt = getattr(args, "format", "json")
    try:
        if args.data_command == "route-preview":
            payload = data_commands.route_preview(
                data_domain=args.data_domain,
                operation=args.operation,
                market_id=args.market_id,
                use_fallback=args.use_fallback,
            )
        elif args.data_command == "sync":
            payload = data_commands.sync_plan(
                data_domain=args.data_domain,
                source_id=getattr(args, "source_id", None),
                operation=args.operation,
                dry_run=args.dry_run,
                start=args.start,
                end=args.end,
                since=args.since,
                instrument_id=args.instrument_id,
            )
        elif args.data_command == "backfill":
            payload = data_commands.backfill_plan(
                data_domain=args.data_domain,
                source_id=args.source_id,
                start=args.start,
                end=args.end,
                max_shards=args.max_shards,
                truncate_to_cap=args.truncate_to_cap,
                dry_run=args.dry_run,
                instrument_id=args.instrument_id,
            )
        elif args.data_command == "full-load":
            payload = data_commands.full_load_plan(
                data_domain=args.data_domain,
                source_id=args.source_id,
                start=args.start,
                end=args.end,
                max_shards=args.max_shards,
                truncate_to_cap=args.truncate_to_cap,
                dry_run=args.dry_run,
                instrument_id=args.instrument_id,
            )
        elif args.data_command == "live-fetch":
            payload = data_commands.live_fetch(
                source_id=args.source_id,
                data_domain=args.data_domain,
                operation=args.operation,
                instrument_id=args.instrument_id,
                dry_run=args.dry_run,
            )
        elif args.data_command == "init-basic":
            from pathlib import Path

            db = Path(args.db) if args.db else None
            payload = data_commands.init_basic(dry_run=args.dry_run, db_path=db)
        elif args.data_command == "health":
            from pathlib import Path

            evidence = Path(args.evidence_dir) if args.evidence_dir else None
            db = Path(args.db_path) if args.db_path else None
            payload = data_commands.health_check(
                data_domain=args.data_domain,
                profile=args.profile,
                evidence_dir=evidence,
                db_path=db,
                start=args.start,
                end=args.end,
                max_rows=args.max_rows,
                allow_network=args.allow_network,
                clean_write=args.clean_write,
                full_market_scan=args.full_market_scan,
                full_history=args.full_history,
            )
        elif args.data_command == "scheduler":
            if args.scheduler_command != "run":
                raise CliFailure(
                    error_code="CAPABILITY_MISSING",
                    message=f"unknown scheduler subcommand: {args.scheduler_command}",
                    docs_anchor="docs/modules/data_sync_orchestrator.md#136-调度计划",
                )
            payload = data_commands.scheduler_run(
                profile=args.profile,
                dry_run=args.dry_run,
            )
        elif args.data_command == "incremental":
            payload = data_commands.incremental_profile_plan(
                profile=args.profile,
                dry_run=args.dry_run,
            )
        elif args.data_command == "revision-audit":
            payload = data_commands.revision_audit_plan(
                data_domain=args.data_domain,
                market_id=args.market_id,
                lookback_days=args.lookback_days,
                dry_run=args.dry_run,
            )
        elif args.data_command == "reconcile":
            payload = data_commands.reconcile_plan(
                conflict_id=args.conflict_id,
                dry_run=args.dry_run,
            )
        elif args.data_command == "quality-check":
            payload = data_commands.quality_check_plan(
                data_domain=args.data_domain,
                check_date=args.check_date,
                dry_run=args.dry_run,
            )
        else:
            raise CliFailure(
                error_code="CAPABILITY_MISSING",
                message=f"unknown data subcommand: {args.data_command}",
                docs_anchor=DOCS_ANCHOR_DATA_SYNC_CLI,
            )
    except CliFailure as err:
        print(data_commands.emit_failure(err, fmt=fmt), file=sys.stderr)
        return err.exit_code()
    print(data_commands.emit_payload(payload, fmt=fmt))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QMD packaged ops CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    _build_data_parser(sub)
    args = parser.parse_args(argv)
    if args.command == "data":
        return _run_data(args)
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
