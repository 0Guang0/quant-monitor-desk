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

    sync = data_sub.add_parser("sync", help="Sync job (default dry-run)")
    sync.add_argument("--domain", required=True, dest="data_domain")
    sync.add_argument("--operation", default=None)
    sync.add_argument("--start", default=None)
    sync.add_argument("--end", default=None)
    sync.add_argument("--since", default=None)
    sync.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Plan only; default true (R3F-CLI-01)",
    )
    sync.add_argument("--format", choices=["json", "text"], default="json")

    init_p = data_sub.add_parser("init-basic", help="Initialize schema (default dry-run)")
    init_p.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    init_p.add_argument("--db", type=str, default=None)
    init_p.add_argument("--format", choices=["json", "text"], default="json")

    health = data_sub.add_parser("health", help="Read-only health placeholder (Phase C)")
    health.add_argument("--domain", default=None, dest="data_domain")
    health.add_argument("--format", choices=["json", "text"], default="json")


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
                operation=args.operation,
                dry_run=args.dry_run,
                start=args.start,
                end=args.end,
                since=args.since,
            )
        elif args.data_command == "init-basic":
            from pathlib import Path

            db = Path(args.db) if args.db else None
            payload = data_commands.init_basic(dry_run=args.dry_run, db_path=db)
        elif args.data_command == "health":
            payload = data_commands.health_check(data_domain=args.data_domain)
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
