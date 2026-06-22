"""Document-only tests for Round 3 Batch 2.75 planning gates."""

from __future__ import annotations

from pathlib import Path

from tests.contract_gate_support import PROJECT_ROOT

MIGRATION_MAP = PROJECT_ROOT / "MIGRATION_MAP.md"
ROUND3_MAP = PROJECT_ROOT / "ROUND3_BATCH_IMPLEMENTATION_MAP.md"
TASK_CARD = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md"
)
POLICY = PROJECT_ROOT / "docs/quality/production_live_pilot_policy.md"
AUDIT_REGISTRY = PROJECT_ROOT / "docs/AUDIT_DEFERRED_REGISTRY.md"
UNRESOLVED_REGISTRY = PROJECT_ROOT / "docs/UNRESOLVED_ISSUES_REGISTRY.md"
RESOLVED_REGISTRY = PROJECT_ROOT / "docs/RESOLVED_ISSUES_REGISTRY.md"
MODELING_README = PROJECT_ROOT / "docs/implementation_tasks/ROUND_3_MODELING_LAYERS/README.md"
DOCS_INDEX = PROJECT_ROOT / "docs/INDEX.md"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing expected document: {path}"
    return path.read_text(encoding="utf-8")


def test_projectMap_reflectsBatch275CurrentStatus() -> None:
    text = _read(MIGRATION_MAP)
    assert "Last updated: 2026-06-21" in text
    assert "Batch 2.75" in text
    assert "production_live_pilot_policy.md" in text
    assert "018B_production_live_pilot_gate.md" in text
    assert "PILOT_FAIL_SOURCE" in text


def test_round3Map_placesBatch275_beforeBatch3() -> None:
    text = _read(ROUND3_MAP)
    assert "R3-B2.75-PROD-LIVE-PILOT" in text
    assert "018B_production_live_pilot_gate.md" in text
    assert "production_live_pilot_policy.md" in text
    order = text.split("## 5. Recommended execution order", maxsplit=1)[1]
    assert order.index("**Batch 2.5**") < order.index("**Batch 2.75**") < order.index("**Batch 3**")
    source_index = text.split("### 4.2 Batch-specific Plan source bundles", maxsplit=1)[1]
    assert "| Batch 2.75" in source_index
    assert "raw-only micro-fetch" in source_index
    assert "no production DB mutation" in source_index


def test_taskCard_requiresFailClosedAuthorizationAndSandboxFirst() -> None:
    text = _read(TASK_CARD)
    required_tokens = [
        "does not enable any live source",
        "No full-market fetch",
        "No full-history fetch",
        "No direct mutation of `data/duckdb/quant_monitor.duckdb`",
        "No silent fallback from a live source to a staged fixture",
        "fail closed unless a user-authorized pilot request explicitly declares",
        "Route status must be `READY`",
        "The first live pass is `raw_only=true`",
        "Any clean write must target sandbox DB",
        "The production target DB remains unchanged",
        "Batch 6 still owns formal production release",
        "This default plan has no clean write",
        "DGS10",
        "Optional third source",
        "fetch_macro_series",
    ]
    for token in required_tokens:
        assert token in text
    for field, default in (
        ("`dry_run`", "Must default to `true`"),
        ("`raw_only`", "Must default to `true`"),
        ("`write_target`", "Must default to `sandbox`"),
        ("`allow_clean_write`", "Must default to `false`"),
    ):
        assert field in text and default in text


def test_policy_preservesSandboxAndRawOnlyControls() -> None:
    text = _read(POLICY)
    for control, default in (
        ("Live source access", "Disabled"),
        ("QMT/xqshare/Yahoo/FRED", "Disabled unless explicitly authorized"),
        ("`dry_run`", "`true`"),
        ("`raw_only`", "`true` for the first live pass"),
        ("`write_target`", "`sandbox`"),
        ("Production clean DB mutation", "Forbidden"),
        ("Full-market/full-history/backfill", "Forbidden"),
        ("Silent fallback to fixture/staged data", "Forbidden"),
    ):
        assert control in text and default in text
    assert "Passing Batch 2.75 does not mean formal production data access is open" in text


def test_registriesKeepBatch25LiveFredDeferredToBatch275() -> None:
    audit = _read(AUDIT_REGISTRY)
    unresolved = _read(UNRESOLVED_REGISTRY)
    resolved = _read(RESOLVED_REGISTRY)
    for registry in (audit, unresolved):
        assert "B2.5-O-05" in registry
        assert "018B_production_live_pilot_gate.md" in registry
    assert "production_live_pilot_policy.md" in audit
    assert "Not closed by Batch 2.75 Request 3" in audit
    assert "test_fred_staged_semantics.py" in audit
    assert "R3-B2.75-01" in resolved
    assert "PILOT_FAIL_SOURCE" in resolved
    assert "R3-B2.75-REQ2-EM" in unresolved


def test_resolvedRegistry_recordsPlanningGateWithoutClosingLivePilot() -> None:
    audit = _read(AUDIT_REGISTRY)
    resolved = _read(RESOLVED_REGISTRY)
    unresolved = _read(UNRESOLVED_REGISTRY)

    assert "R3-B2.75-PLAN-01" in audit
    assert "R3-B2.75-PLAN-01" in resolved
    assert "Does not close `R3-B2.75-01`" in resolved
    assert "R3-B2.75-01" in resolved
    assert "PILOT_FAIL_SOURCE" in resolved
    assert "R3-B2.75-REQ2-EM" in unresolved
    assert "25 passed in current session" in resolved


def test_docsIndexesExposeBatch275EntryPoints() -> None:
    readme = _read(MODELING_README)
    index = _read(DOCS_INDEX)
    assert "018B_production_live_pilot_gate.md" in readme
    assert "018A_layer1_observation_ingestion_bridge.md" in readme
    assert "018C_tdx_pytdx_low_cost_probe.md" in readme
    assert "`019`" in readme
    assert "production_live_pilot_policy.md" in index
    assert "018B_production_live_pilot_gate.md" in index


def test_policy_requiresStagedPilotConflictEvidenceChecklist() -> None:
    """覆盖范围：production_live_pilot_policy 对 staged pilot 证据要求。

    测试对象：production_live_pilot_policy.md §6。
    目的/目标：ADV-POST14-A-012 — 策略要求 conflict report 或显式 no-conflict 证据。
    """
    text = _read(POLICY)
    assert "Conflict report or explicit no-conflict evidence" in text
    assert "No fixture/staged fallback satisfies live pilot evidence" in text


def test_stagedPilotModuleAlignsWithProductionLivePolicyControls() -> None:
    """覆盖范围：staged_pilot 模块与 Batch 2.75/14 策略控制对齐。

    测试对象：backend.app.ops.staged_pilot 默认请求信封。
    目的/目标：ADV-POST14-A-012 — raw_only/sandbox/allow_clean_write 默认 fail-closed。
    """
    from backend.app.ops.staged_pilot import approved_pilot_requests

    for request in approved_pilot_requests():
        assert request.raw_only is True
        assert request.write_target == "sandbox"
        assert request.allow_clean_write is False
        assert request.dry_run is True
