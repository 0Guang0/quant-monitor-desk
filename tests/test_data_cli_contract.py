"""Round2.6 Phase B — data CLI contract tests (design/contract level)."""

from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_CONTRACT = PROJECT_ROOT / "specs/contracts/data_cli_contract.yaml"
ERROR_GUIDE = PROJECT_ROOT / "docs/ops/ERROR_CODE_GUIDE.md"
TASK2_DIR = (
    PROJECT_ROOT
    / ".trellis/tasks/archive/2026-06/06-19-round2-6-routing-service-gate"
)
TASK2_MASTER = TASK2_DIR / "MASTER.plan.md"
TASK2_IMPLEMENT = TASK2_DIR / "implement.jsonl"


def _load_contract() -> dict:
    return yaml.safe_load(CLI_CONTRACT.read_text(encoding="utf-8")) or {}


def test_routePreviewContract_isReadOnly() -> None:
    contract = _load_contract()
    route_preview = contract["commands"]["qmd data route-preview"]
    assert route_preview["side_effects_allowed"] is False
    assert route_preview["output"] == "SourceRoutePlan"


def test_syncDryRunDoesNotWrite() -> None:
    contract = _load_contract()
    sync_cmd = contract["commands"]["qmd data sync"]
    assert "dry-run" in sync_cmd.get("optional_args", [])
    assert "ResourceGuard" in sync_cmd.get("must_use", [])
    assert "SourceRoutePlan" in sync_cmd.get("must_use", [])


def test_initBasic_defaultsToDryRun() -> None:
    contract = _load_contract()
    init_cmd = contract["commands"]["qmd data init-basic"]
    assert init_cmd.get("default_mode") == "dry_run"


def test_cliFailure_mustExposeErrorCodeAndDocsAnchor() -> None:
    contract = _load_contract()
    rules = contract.get("rules") or []
    assert any("error_code" in r and "docs_anchor" in r for r in rules)
    guide = ERROR_GUIDE.read_text(encoding="utf-8")
    assert "DISABLED_SOURCE" in guide
    assert "docs_anchor" in guide or "ERROR_CODE" in guide.upper()


def test_productionCli_notYetImplemented_documentedInTask2() -> None:
    assert TASK2_MASTER.is_file()
    text = TASK2_MASTER.read_text(encoding="utf-8")
    assert "DataSourceService" in text
    assert "production_equivalent_smoke" in text or "016F" in text
    assert (PROJECT_ROOT / "specs/contracts/data_cli_contract.yaml").is_file()
    gate_impl = TASK2_IMPLEMENT.read_text(encoding="utf-8")
    assert "data_cli_contract.yaml" in gate_impl
