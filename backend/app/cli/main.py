"""Unified packaged CLI: `qmd-ops` / `qmd-data` entrypoints."""

from __future__ import annotations

import argparse
import sys

from backend.app.cli import data_commands
from backend.app.cli.errors import CliFailure


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
            "Sync job (default dry-run). cn_equity_daily_bar: baostock watermark; "
            "macro_series with --source-id fred: macro incremental."
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

    scw = data_sub.add_parser(
        "sandbox-clean-write",
        help="Sandbox clean-write rehearsal (R3G-01)",
    )
    scw_sub = scw.add_subparsers(dest="sandbox_clean_write_command", required=True)
    rehearse = scw_sub.add_parser("rehearse", help="Run capped sandbox clean-write rehearsal")
    rehearse.add_argument("--candidate-set", required=True)
    rehearse.add_argument("--sandbox-db", required=True)
    rehearse.add_argument("--evidence-dir", required=True)
    rehearse.add_argument("--report", required=True)
    rehearse.add_argument("--no-production-mutation", action="store_true")
    rehearse.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    rehearse.add_argument("--allow-live-fetch", action="store_true")
    rehearse.add_argument("--fred-authorization", default=None)
    rehearse.add_argument("--format", choices=["json", "text"], default="json")
    audit = scw_sub.add_parser("audit", help="Pre-production adversarial audit (R3G-02)")
    audit.add_argument("--rehearsal-report", required=True)
    audit.add_argument("--sandbox-db", required=True)
    audit.add_argument("--evidence-dir", required=True)
    audit.add_argument("--decision-report", required=True)
    audit.add_argument("--format", choices=["json", "text"], default="json")
    promote = scw_sub.add_parser("promote", help="Limited production clean-write entry (R3G-03)")
    promote.add_argument("--approval-file", required=True)
    promote.add_argument("--audit-decision", required=True)
    promote.add_argument("--before-proof", required=True)
    promote.add_argument("--after-proof", required=True)
    promote.add_argument("--rollback-plan", required=True)
    promote.add_argument("--evidence-dir", default=None)
    promote.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    promote.add_argument("--execute", action="store_true")
    promote.add_argument("--allow-live-fetch", action="store_true")
    promote.add_argument("--fred-authorization", default=None)
    promote.add_argument("--format", choices=["json", "text"], default="json")


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
        elif args.data_command == "sandbox-clean-write":
            from pathlib import Path

            if args.sandbox_clean_write_command == "rehearse":
                fred_auth = Path(args.fred_authorization) if args.fred_authorization else None
                payload = data_commands.sandbox_clean_write_rehearse(
                    candidate_set=args.candidate_set,
                    sandbox_db=Path(args.sandbox_db),
                    evidence_dir=Path(args.evidence_dir),
                    report=Path(args.report),
                    no_production_mutation=args.no_production_mutation,
                    dry_run=args.dry_run,
                    allow_live_fetch=args.allow_live_fetch,
                    fred_authorization=fred_auth,
                )
            elif args.sandbox_clean_write_command == "audit":
                payload = data_commands.sandbox_clean_write_audit(
                    rehearsal_report=Path(args.rehearsal_report),
                    sandbox_db=Path(args.sandbox_db),
                    evidence_dir=Path(args.evidence_dir),
                    decision_report=Path(args.decision_report),
                )
            elif args.sandbox_clean_write_command == "promote":
                evidence = Path(args.evidence_dir) if args.evidence_dir else None
                fred_auth = Path(args.fred_authorization) if args.fred_authorization else None
                payload = data_commands.sandbox_clean_write_promote(
                    approval_file=Path(args.approval_file),
                    audit_decision=Path(args.audit_decision),
                    before_proof=Path(args.before_proof),
                    after_proof=Path(args.after_proof),
                    rollback_plan=Path(args.rollback_plan),
                    evidence_dir=evidence,
                    dry_run=args.dry_run,
                    execute=args.execute,
                    allow_live_fetch=args.allow_live_fetch,
                    fred_authorization=fred_auth,
                )
            else:
                raise CliFailure(
                    error_code="CAPABILITY_MISSING",
                    message=f"unknown sandbox-clean-write subcommand: {args.sandbox_clean_write_command}",
                    docs_anchor="docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md",
                )
        else:
            raise CliFailure(
                error_code="CAPABILITY_MISSING",
                message=f"unknown data subcommand: {args.data_command}",
                docs_anchor="docs/ops/data_sync_quick_reference.md",
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
