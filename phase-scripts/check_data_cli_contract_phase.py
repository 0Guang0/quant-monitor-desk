#!/usr/bin/env python3
"""data_cli_contract Phase 1 契约/文档门禁（阶段性 · 非业务 pytest）

功能：
  静态核对 specs/contracts/data_cli_contract.yaml 的 phase1_gate、正式命令登记、
  docs_anchor、retired_commands、status、health 契约，以及 legacy 验收入口清零
  （scripts.check_acceptance_helper_consumers.build_report）。
  对应原 tests/test_data_cli_contract.py 中 YAML/文档/phase artifact-guard 用例。
  另含 legacy sandbox-clean-write 子命令已从 CLI 树移除（invalid choice）。
  不含 runtime 行为：syncDryRunDoesNotWrite、routePreviewContract_isReadOnly（仍留 pytest）。

业务价值：
  防止 P1-GATE 关账权威、正式 CLI 公开面与 design 文档锚点相对契约漂移，
  避免 agent 用错误入口或 draft 契约冒充正式验收。

退役 / 清理时间（满足任一即可删本文件）：
  1. P1-GATE 阶段文档已过时，CLI 契约仅由 runtime CLI 测试 + design SSOT 校验；或
  2. 本检查已 promote 进正式 scripts/check_* + production_gate，无需独立 phase-script。

运行：
  uv run python phase-scripts/check_data_cli_contract_phase.py
  uv run python phase-scripts/check_data_cli_contract_phase.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/data_cli_contract.yaml"


def _contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def check_phase1_gate(violations: list[str]) -> None:
    gate = _contract()["phase1_gate"]
    if gate.get("acceptance_authority") != "SourceRouteDbAcceptanceSpine":
        violations.append(
            f"phase1_gate.acceptance_authority={gate.get('acceptance_authority')!r}"
        )
    segment = gate.get("production_equivalent_data_root_segment")
    if segment != "source-route-db":
        violations.append(
            f"phase1_gate.production_equivalent_data_root_segment={segment!r}"
        )
    if "source-route-db" not in str(segment):
        violations.append("phase1_gate segment missing source-route-db")
    requires = " ".join(gate.get("gate_eligible_requires") or [])
    if "dry-run" not in requires:
        violations.append("phase1_gate.gate_eligible_requires missing dry-run")
    non_gate = gate.get("non_gate_evidence") or {}
    if "dry_run" not in non_gate:
        violations.append("phase1_gate.non_gate_evidence missing dry_run")
    runtime = gate.get("current_runtime_seams") or {}
    module = runtime.get("prod_source_tier_module") or ""
    if not str(module).endswith("live_prod_source_tiers"):
        violations.append(
            f"phase1_gate.current_runtime_seams.prod_source_tier_module={module!r}"
        )
    if runtime.get("domain_fetch_operation") != "domain_fetch_operation":
        violations.append(
            f"phase1_gate.domain_fetch_operation={runtime.get('domain_fetch_operation')!r}"
        )


def check_official_commands_expose(violations: list[str]) -> None:
    must_expose = set(_contract()["phase1_gate"].get("official_commands_must_expose") or [])
    required = {"acceptance_report", "gate_eligible", "observability_evidence"}
    missing = required - must_expose
    if missing:
        violations.append(f"official_commands_must_expose missing: {sorted(missing)}")


def check_section137_commands(violations: list[str]) -> None:
    commands = _contract().get("commands") or {}
    for key in ("qmd data full-load", "qmd data scheduler run"):
        if key not in commands:
            violations.append(f"commands missing: {key}")


def check_scheduler_run(violations: list[str]) -> None:
    entry = (_contract().get("commands") or {}).get("qmd data scheduler run") or {}
    if "profile" not in (entry.get("required_args") or []):
        violations.append("scheduler run required_args missing profile")
    if "execute_binding" not in (entry.get("must_use") or []):
        violations.append("scheduler run must_use missing execute_binding")


def check_docs_anchors(violations: list[str]) -> None:
    commands = _contract().get("commands") or {}
    orchestrator_anchors = [
        entry["docs_anchor"]
        for key, entry in commands.items()
        if "docs_anchor" in entry and "data_sync_orchestrator" in entry["docs_anchor"]
    ]
    if not orchestrator_anchors:
        violations.append("no data_sync_orchestrator docs_anchor found")
        return
    for anchor in orchestrator_anchors:
        if "docs/modules/design/data_sync_orchestrator.md" not in anchor:
            violations.append(f"docs_anchor not design SSOT: {anchor}")


def check_legacy_inventory(violations: list[str]) -> None:
    from scripts.check_acceptance_helper_consumers import build_report

    report = build_report(PROJECT_ROOT)
    if report.get("strict_status") != "PASS":
        violations.append(f"legacy inventory strict_status={report.get('strict_status')!r}")
    if report.get("legacy_compat_count") != 0:
        violations.append(f"legacy_compat_count={report.get('legacy_compat_count')}")
    if report.get("retired_legacy_cli_count") != 0:
        violations.append(
            f"retired_legacy_cli_count={report.get('retired_legacy_cli_count')}"
        )


def check_retired_commands(violations: list[str]) -> None:
    gate = _contract()["phase1_gate"]
    retired = {item["command"] for item in gate.get("retired_commands") or []}
    legacy_promote = "qmd data sandbox" + "-clean-write"
    if legacy_promote in retired:
        violations.append(f"retired_commands still lists deleted CLI: {legacy_promote}")
    must_expose = gate.get("official_commands_must_expose") or []
    if "failure_class" not in must_expose:
        violations.append("official_commands_must_expose missing failure_class")
    if "BLOCKED" not in (gate.get("failure_class_values") or []):
        violations.append("failure_class_values missing BLOCKED")


def check_status_frozen(violations: list[str]) -> None:
    status = _contract().get("status")
    if status != "frozen":
        violations.append(f"status={status!r}, expect frozen")


def check_health_command(violations: list[str]) -> None:
    entry = (_contract().get("commands") or {}).get("qmd data health") or {}
    if entry.get("side_effects_allowed") is not False:
        violations.append(
            f"health.side_effects_allowed={entry.get('side_effects_allowed')!r}"
        )
    forbidden = entry.get("forbidden_args") or []
    if "clean-write" not in forbidden:
        violations.append("health.forbidden_args missing clean-write")


def check_sandbox_clean_write_not_registered(violations: list[str]) -> None:
    """Legacy promote CLI must be rejected by argparse (invalid choice)."""
    import os
    import subprocess

    legacy_subcommand = "sandbox" + "-clean-write"
    env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
    proc = subprocess.run(
        [sys.executable, "-m", "backend.app.cli.main", "data", legacy_subcommand],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if proc.returncode == 0:
        violations.append("legacy sandbox-clean-write still registered (exit 0)")
    elif "invalid choice" not in proc.stderr.lower():
        violations.append(
            "legacy sandbox-clean-write stderr missing invalid choice: "
            f"{proc.stderr.strip()[:200]!r}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="有违例时 exit 1（关账/人工门禁用）",
    )
    args = parser.parse_args(argv)

    violations: list[str] = []
    check_phase1_gate(violations)
    check_official_commands_expose(violations)
    check_section137_commands(violations)
    check_scheduler_run(violations)
    check_docs_anchors(violations)
    check_legacy_inventory(violations)
    check_retired_commands(violations)
    check_status_frozen(violations)
    check_health_command(violations)
    check_sandbox_clean_write_not_registered(violations)

    if not violations:
        print("PASS: data_cli_contract phase gate")
        return 0

    print("FAIL: data_cli_contract phase gate")
    for item in violations:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
