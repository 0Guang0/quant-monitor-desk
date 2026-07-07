#!/usr/bin/env python3
"""Report acceptance-language drift in active authority docs/contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_AUTHORITY_PATHS: tuple[Path, ...] = tuple(
    PROJECT_ROOT / path
    for path in (
        "docs/modules/source_route_plan.md",
        "docs/modules/data_sources.md",
        "docs/modules/write_manager.md",
        "docs/architecture/04_data_architecture.md",
        "rules/GLOBAL_RULES.md",
        "rules/GLOBAL_TESTING_POLICY.md",
        "specs/contracts/source_route_contract.yaml",
        "specs/contracts/write_contract.yaml",
        "specs/contracts/source_route_db_acceptance_contract.yaml",
    )
)

STAGE_RE = re.compile(r"\b(?:Phase|Batch|Wave)\s*\d+|第[一二三四五六七八九十0-9]+阶段")
NON_LIVE_MODE_RE = re.compile(r"\b(?:mock|replay|dry_run|not_implemented)\b", re.IGNORECASE)
SUCCESS_RE = re.compile(r"\b(?:PASS|SUCCESS|accepted|completed|success)\b", re.IGNORECASE)
NEGATION_RE = re.compile(r"\b(?:not|never|cannot|can't|must not)\b", re.IGNORECASE)
NEGATION_MARKERS = ("不得", "不能", "不可", "不算", "只能")


@dataclass(frozen=True, kw_only=True)
class LanguageViolation:
    path: str
    line: int
    rule: str
    text: str


def _is_mock_success_claim(line: str) -> bool:
    if not NON_LIVE_MODE_RE.search(line) or not SUCCESS_RE.search(line):
        return False
    return not NEGATION_RE.search(line) and not any(marker in line for marker in NEGATION_MARKERS)


def check_paths(paths: list[Path], *, root: Path = PROJECT_ROOT) -> list[LanguageViolation]:
    violations: list[LanguageViolation] = []
    for path in paths:
        if not path.exists():
            violations.append(
                LanguageViolation(
                    path=_relative(path, root),
                    line=0,
                    rule="missing_authority_file",
                    text="authority file does not exist",
                )
            )
            continue
        in_fence = False
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if STAGE_RE.search(stripped):
                violations.append(
                    LanguageViolation(
                        path=_relative(path, root),
                        line=line_no,
                        rule="execution_stage_vocabulary",
                        text=stripped,
                    )
                )
            if _is_mock_success_claim(stripped):
                violations.append(
                    LanguageViolation(
                        path=_relative(path, root),
                        line=line_no,
                        rule="non_live_mode_as_acceptance_success",
                        text=stripped,
                    )
                )
    return violations


def build_report(
    paths: list[Path] | None = None,
    *,
    root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    targets = paths if paths is not None else list(DEFAULT_AUTHORITY_PATHS)
    violations = check_paths(targets, root=root)
    return {
        "status": "FAIL" if violations else "PASS",
        "mode": "authority_acceptance_language_guard",
        "violation_count": len(violations),
        "violations": [asdict(item) for item in violations],
    }


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _format_text(report: dict[str, object]) -> str:
    lines = [
        f"status={report['status']} mode={report['mode']} violations={report['violation_count']}"
    ]
    for item in report["violations"]:
        lines.append(f"- {item['path']}:{item['line']} {item['rule']}: {item['text']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check authority acceptance language")
    parser.add_argument("paths", nargs="*", type=Path, help="Optional authority files to scan")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when violations exist")
    args = parser.parse_args(argv)

    report = build_report(args.paths or None)
    output = (
        json.dumps(report, indent=2, sort_keys=True)
        if args.format == "json"
        else _format_text(report)
    )
    print(output)
    return 1 if args.strict and report["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
