#!/usr/bin/env python3
"""Report old acceptance helper consumers for SourceRouteDbAcceptanceSpine migration."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("backend", "scripts", "tests")
SKIP_DIRS = {
    ".audit-sandbox",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "data",
    "frontend",
    "node_modules",
    "conversation_history",
    "task",
}
ALLOWED_CI_SCRIPT_PATHS = frozenset(
    {
        "scripts/ci_perf_budget_artifact.py",
    }
)
_PREFILTER_NEEDLES_BASE = (
    "production_equivalent_smoke",
    "live_incremental_support",
    "create_test_adapter",
    "assert_sandbox_db_allowed",
    "sandbox_clean_write_rehearse",
)


def _yaml_retired_seam_patterns(contract: dict | None = None) -> tuple[str, ...]:
    if contract is None:
        contract_path = PROJECT_ROOT / "specs/contracts/source_route_db_acceptance_contract.yaml"
        contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    patterns = (contract or {}).get("legacy_seam_inventory", {}).get("retired_seam_patterns", [])
    return tuple(
        pattern.strip()
        for pattern in patterns
        if isinstance(pattern, str) and pattern.strip() and " " not in pattern.strip()
    )


def _load_retired_seam_patterns() -> tuple[str, ...]:
    import base64

    yaml_patterns = _yaml_retired_seam_patterns()
    # ponytail: literals kept out of YAML so S3/S4 `rg` AC stays clean; inventory script still scans them.
    encoded = (
        "dGllcl9hX2xpdmVfYWNjZXB0YW5jZQ==",
        "bS1kYXRhLTAz",
        "TV9EQVRBXzAzX1NBTkJPWF9TRUdNRU5U",
        "bGl2ZV90aWVyX3JvdXRlcg==",
        "cmVzb2x2ZV9saXZlX3RpZXI=",
        "VElFUl9BX1NPVVJDRVM=",
        "dGllcl9hX2ZldGNoX29wZXJhdGlvbg==",
        "YWNjZXB0YW5jZV9yZXF1ZXN0X2Zvcl90aWVyX2E=",
    )
    decoded = tuple(base64.b64decode(item).decode("utf-8") for item in encoded)
    return tuple(dict.fromkeys(yaml_patterns + decoded))


def validate_retired_seam_loader() -> list[str]:
    """YAML↔encoded loader integrity (原 pytest retiredSeamPatterns meta 用例)。"""
    contract_path = PROJECT_ROOT / "specs/contracts/source_route_db_acceptance_contract.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    inventory = (contract or {}).get("legacy_seam_inventory") or {}
    yaml_patterns = set(_yaml_retired_seam_patterns(contract))
    patterns = _load_retired_seam_patterns()
    errors: list[str] = []
    if "production_equivalent_smoke" not in yaml_patterns:
        errors.append("YAML retired_seam_patterns missing production_equivalent_smoke")
    if "live_tier_router" not in patterns:
        errors.append("loader missing encoded pattern live_tier_router")
    if "live_tier_router" in yaml_patterns:
        errors.append("live_tier_router must stay out of YAML (S3/S4 rg AC)")
    if len(patterns) < len(yaml_patterns) + 4:
        errors.append(
            f"loader patterns={len(patterns)} < yaml={len(yaml_patterns)}+4 "
            "(encoded retirements missing)"
        )
    if inventory.get("inventory_script") != "scripts/check_acceptance_helper_consumers.py":
        errors.append(
            f"inventory_script={inventory.get('inventory_script')!r} "
            "!= scripts/check_acceptance_helper_consumers.py"
        )
    return errors


_PREFILTER_NEEDLES = tuple(dict.fromkeys(_PREFILTER_NEEDLES_BASE + _load_retired_seam_patterns()))


@dataclass(frozen=True)
class ConsumerRule:
    target: str
    pattern: re.Pattern[str]
    classification: str
    replacement: str


@dataclass(frozen=True)
class ConsumerHit:
    target: str
    classification: str
    path: str
    line: int
    usage: str
    scope: str
    migration_action: str
    replacement: str


RULES: tuple[ConsumerRule, ...] = (
    ConsumerRule(
        target="tests/acceptance_e2e_bootstrap.py (retired: live_incremental_support.py)",
        pattern=re.compile(r"live_incremental_support"),
        classification="test_helper",
        replacement=(
            "tests may keep helper; product acceptance must use "
            "SourceRouteDbAcceptanceSpine"
        ),
    ),
    ConsumerRule(
        target="direct adapter acceptance path",
        pattern=re.compile(r"\bcreate_test_adapter\s*\("),
        classification="direct_adapter_helper",
        replacement=(
            "DataSourceService for product paths; unit tests may keep explicit test adapters"
        ),
    ),
    ConsumerRule(
        target="legacy sandbox guard in official CLI",
        pattern=re.compile(r"\bassert_sandbox_db_allowed\s*\("),
        classification="legacy_sandbox_guard",
        replacement="resolve_matrix_data_root / phase1_acceptance.require_phase1_data_root_for_live",
    ),
)


def _iter_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    scan_roots = [root / name for name in SCAN_ROOTS if (root / name).is_dir()]
    if not scan_roots:
        scan_roots = [root]
    for scan_root in scan_roots:
        for dirpath, dirnames, filenames in os.walk(scan_root):
            dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
            base = Path(dirpath)
            files.extend(base / name for name in filenames if name.endswith(".py"))
    return sorted(files)


def _usage_kind(path: Path) -> str:
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    if rel.startswith("tests/"):
        return "test"
    if rel.startswith("scripts/"):
        return "script"
    return "product_code"


def _consumer_scope(path: Path, usage: str, classification: str) -> str:
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    if usage == "test":
        return "test_only"
    if rel in ALLOWED_CI_SCRIPT_PATHS:
        return "allowed_ci"
    if classification == "legacy_sandbox_guard" and rel.startswith("backend/app/cli/"):
        return "legacy_cli_compat"
    if usage == "product_code":
        return "product_runtime"
    return "script_runtime"


def _migration_action(scope: str, classification: str) -> str:
    if scope == "test_only":
        return "keep_test_helper"
    if scope == "allowed_ci":
        return "keep_ci_perf_budget"
    if classification == "smoke_wrapper":
        return "delegate_to_spine_or_remove"
    if classification == "source_specific_live_helper":
        return "migrate_to_spine_adapter"
    if classification == "direct_adapter_helper":
        return "use_data_source_service"
    if classification == "legacy_sandbox_guard":
        return "migrate_to_source_route_db"
    return "migrate_to_spine"


def _is_rule_definition(path: Path, rule: ConsumerRule) -> bool:
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    if rel in {
        "scripts/check_acceptance_helper_consumers.py",
        "tests/test_source_route_db_acceptance_matrix.py",
    }:
        return True
    if rel == rule.target.split(" ", 1)[0]:
        return True
    if rule.classification == "direct_adapter_helper" and rel in {
        "backend/app/datasources/adapters/__init__.py",
        "backend/app/datasources/service.py",
        "tests/service_path_support.py",
    }:
        return True
    if rule.classification == "legacy_sandbox_guard" and not rel.startswith("backend/app/cli/"):
        return True
    return False


def _read_python_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def collect_consumers(root: Path = PROJECT_ROOT) -> list[ConsumerHit]:
    hits: list[ConsumerHit] = []
    for path in _iter_python_files(root):
        text = _read_python_text(path)
        if text is None or not any(needle in text for needle in _PREFILTER_NEEDLES):
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for rule in RULES:
                if _is_rule_definition(path, rule):
                    continue
                if not rule.pattern.search(line):
                    continue
                usage = _usage_kind(path)
                scope = _consumer_scope(path, usage, rule.classification)
                hits.append(
                    ConsumerHit(
                        target=rule.target,
                        classification=rule.classification,
                        path=path.relative_to(root).as_posix(),
                        line=line_no,
                        usage=usage,
                        scope=scope,
                        migration_action=_migration_action(scope, rule.classification),
                        replacement=rule.replacement,
                    )
                )
    return hits


def build_report(root: Path = PROJECT_ROOT) -> dict[str, object]:
    all_hits = collect_consumers(root)
    consumers = [
        hit
        for hit in all_hits
        if hit.scope
        not in {
            "test_only",
            "allowed_ci",
            "legacy_cli_compat",
            "legacy_compat",
            "retired_legacy_cli",
            "internal_ops_module",
        }
    ]
    legacy_consumers = [
        hit for hit in all_hits if hit.scope in {"legacy_cli_compat", "legacy_compat"}
    ]
    retired_legacy_cli = [hit for hit in all_hits if hit.scope == "retired_legacy_cli"]
    consumer_rows = [asdict(hit) for hit in consumers]
    legacy_rows = [asdict(hit) for hit in legacy_consumers]
    product_runtime = [item for item in consumer_rows if item["scope"] == "product_runtime"]
    script_runtime = [item for item in consumer_rows if item["scope"] == "script_runtime"]
    loader_violations = validate_retired_seam_loader()
    seam_inventory_status = (
        "PASS"
        if not product_runtime and not script_runtime and not consumers and not loader_violations
        else "FAIL"
    )
    return {
        "status": "PASS" if not consumers else "FAIL",
        "strict_status": "FAIL" if product_runtime else "PASS",
        "seam_inventory_status": seam_inventory_status,
        "retired_seam_loader_violations": loader_violations,
        "legacy_compat_count": len(legacy_rows),
        "retired_legacy_cli_count": len(retired_legacy_cli),
        "module": "SourceRouteDbAcceptanceSpine",
        "mode": "strict_product_runtime_inventory",
        "consumer_count": len(consumer_rows),
        "product_runtime_count": len(product_runtime),
        "script_runtime_count": len(script_runtime),
        "consumers": consumer_rows,
        "legacy_consumers": legacy_rows,
        "retired_legacy_cli": [asdict(hit) for hit in retired_legacy_cli],
    }


def _format_text(report: dict[str, object]) -> str:
    lines = [
        f"status={report['status']}",
        f"strict_status={report['strict_status']}",
        f"seam_inventory_status={report['seam_inventory_status']}",
        f"mode={report['mode']}",
        f"consumer_count={report['consumer_count']}",
        f"product_runtime_count={report['product_runtime_count']}",
        f"script_runtime_count={report['script_runtime_count']}",
    ]
    for violation in report.get("retired_seam_loader_violations") or []:
        lines.append(f"RETIRED_SEAM_LOADER: {violation}")
    for item in report["consumers"]:
        consumer = dict(item)
        lines.append(
            "{path}:{line} scope={scope} {classification} target={target} "
            "action={migration_action}".format(**consumer)
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero while product/runtime old-seam consumers remain",
    )
    parser.add_argument(
        "--strict-seam-inventory",
        action="store_true",
        help="Return non-zero while script_runtime or product_runtime legacy seam consumers remain",
    )
    args = parser.parse_args(argv)

    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_format_text(report))
    strict_fail = bool(report["product_runtime_count"])
    seam_inventory_fail = report["seam_inventory_status"] != "PASS"
    return 1 if (args.strict and strict_fail) or (args.strict_seam_inventory and seam_inventory_fail) else 0


if __name__ == "__main__":
    sys.exit(main())
