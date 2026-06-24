"""Read-only CLI entry for data health (Round 3 C-20 thin wrapper)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.app.config import PROJECT_ROOT
from backend.app.ops.data_health import (
    V2_PROFILES,
    DataHealthService,
    build_text_summary,
    evidence_dir_within_project,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only staged evidence data health")
    parser.add_argument(
        "--evidence",
        type=Path,
        required=True,
        help="Staged pilot evidence directory (read-only, project-relative)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--profile",
        default="staged_pilot_bundle",
        help=(
            "Data health profile (staged_pilot_bundle or v2: "
            + ", ".join(sorted(V2_PROFILES))
            + ")"
        ),
    )
    parser.add_argument("--output", type=Path, default=None, help="Optional output file")

    args = parser.parse_args(argv)
    evidence_dir = args.evidence
    if not evidence_dir.is_dir():
        print(f"error: evidence directory not found: {evidence_dir}", file=sys.stderr)
        return 2
    if not evidence_dir_within_project(evidence_dir):
        print(
            f"error: evidence path must resolve under project root: {PROJECT_ROOT}",
            file=sys.stderr,
        )
        return 2

    profile = args.profile
    if profile != "staged_pilot_bundle" and profile not in V2_PROFILES:
        print(f"error: unknown data health profile: {profile}", file=sys.stderr)
        return 2

    service = DataHealthService()
    report = service.check_evidence_dir(
        evidence_dir,
        profile=None if profile == "staged_pilot_bundle" else profile,
    )

    if args.format == "json":
        output = json.dumps(report.to_dict(), indent=2)
    else:
        output = report.text_summary or build_text_summary(report)

    if args.output is not None:
        if not args.output.parent.is_dir():
            print(
                f"error: output parent directory does not exist: {args.output.parent}",
                file=sys.stderr,
            )
            return 2
        args.output.write_text(output + ("\n" if args.format == "text" else ""), encoding="utf-8")
    else:
        print(output)

    if report.overall_status in {"FAIL", "BLOCKED"}:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
