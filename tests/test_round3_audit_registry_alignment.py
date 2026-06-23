"""Round 3 Batch 2.5 / Batch 2.75 audit follow-up 文档对齐测试。"""

from __future__ import annotations

import re
from pathlib import Path

from tests.contract_gate_support import PROJECT_ROOT

AUDIT_DEFERRED = PROJECT_ROOT / "docs/AUDIT_DEFERRED_REGISTRY.md"
UNRESOLVED = PROJECT_ROOT / "docs/UNRESOLVED_ISSUES_REGISTRY.md"
RESOLVED = PROJECT_ROOT / "docs/RESOLVED_ISSUES_REGISTRY.md"
ADVERSARIAL_REPORT = PROJECT_ROOT / "docs/quality/adversarial_audit_report.md"
PONYTAIL_SCAN = PROJECT_ROOT / "docs/quality/PONYTAIL_MODULE_SCAN_20260622.md"
DATABASE_GUIDELINES = PROJECT_ROOT / ".trellis/spec/backend/database-guidelines.md"
ROUND3_MAP = PROJECT_ROOT / "ROUND3_BATCH_IMPLEMENTATION_MAP.md"
TASK_018B = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md"
)
TASK_019 = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md"
)
GITIGNORE = PROJECT_ROOT / ".gitignore"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing expected document: {path}"
    return path.read_text(encoding="utf-8")


def test_batch25ClosedItems_areResolvedAndNotStillOpen() -> None:
    unresolved = _read(UNRESOLVED)
    resolved = _read(RESOLVED)
    gitignore = _read(GITIGNORE)

    for item_id in ("R3-B25-DOC-01", "A08-P1-02", "R3-B25-HYG-04"):
        assert item_id in resolved
        assert f"| {item_id} | OPEN" not in unresolved
        assert f"| {item_id} | OPEN " not in unresolved

    assert "BATCH3_STAGED_DOWNSTREAM_GATE.md" in resolved
    assert "pytest slow marker" in resolved
    assert ".audit-sandboxpytest-*/" in gitignore


def test_hyg03_keepsOnlyPerformanceBudgetGapOpen() -> None:
    unresolved = _read(UNRESOLVED)

    assert "R3-B25-HYG-03" in unresolved
    assert "test tier 已补" in unresolved
    assert "A08-P2-01 / A08-P2-02" in unresolved
    assert "production-equivalent benchmark" in unresolved
    assert "performance-budget artifact" in unresolved
    assert "无 test tier / 新 A6 benchmark" not in unresolved


def test_task019_requiresBatch3StagedOnlyDownstreamGate() -> None:
    text = _read(TASK_019)

    for token in (
        "Batch 3 staged-only downstream gate",
        "docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md",
        "ingestion type 是 staged，不是 production-live",
        "018A_layer1_observation_ingestion_bridge.md",
        "R3-B2.75-01",
        "production-live readiness",
    ):
        assert token in text


def test_round3Map_tracksCompleteBatch275Scope() -> None:
    text = _read(ROUND3_MAP)

    for token in (
        "Batch 2.75 must include, and only include",
        "R3-B2.75-PROD-LIVE-PILOT",
        "R3-B2.75-01",
        "GLOBAL-P2-01",
        "B2.5-O-05",
        "R3-B25-PERF-BUDGET-01",
        "R3-B25-HYG-03",
        "production-equivalent benchmark",
        "performance-budget evidence artifact",
        "scripts/production_equivalent_smoke.py",
        "PILOT_PASS_RAW_ONLY",
        "PILOT_PASS_SANDBOX_CLEAN",
        "PILOT_FAIL_SOURCE",
        "PILOT_FAIL_VALIDATION",
        "PILOT_REDEFERRED",
        "Batch 3 handoff note",
    ):
        assert token in text

    for token in (
        "migration 008 CHECK closeout",
        "ingestion split R2b–R2d",
        "frontend Vitest/bundle budget",
        "Batch 3 modeling implementation",
    ):
        assert token in text


def test_task018B_declaresCompleteBatch275ScopeAndCloseout() -> None:
    text = _read(TASK_018B)

    for token in (
        "Batch 2.75 scope ledger",
        "R3-B2.75-PROD-LIVE-PILOT",
        "R3-B2.75-01",
        "GLOBAL-P2-01",
        "B2.5-O-05",
        "R3-B25-PERF-BUDGET-01",
        "R3-B25-HYG-03",
        "Phase -1 — current-state reconciliation",
        "Phase 4.5 — performance-budget evidence gate",
        "production_equivalent_smoke.py",
        "Batch 3 handoff note",
        "not in Batch 2.75",
        "CI nightly / Batch6",
    ):
        assert token in text

    for token in (
        "No migration 008 CHECK closeout",
        "No ingestion monolith split / R2b-R2d refactor",
        "No frontend Vitest or bundle budget implementation",
        "No Batch 3 Layer 2 modeling implementation",
        "No Batch6 production CLI/backfill/reconcile/source-health release gate closure",
    ):
        assert token in text


def test_round3Map_tracksPostAuditIngestionAndRound4References() -> None:
    text = _read(ROUND3_MAP)

    for token in (
        "R3-B25-INGEST-SPLIT-R2B",
        "R3-B25-INGEST-MONOLITH-R2C-R2D",
        "layer1_ingestion_refactor_rollback_plan.md",
        "R2b/R2c/R2d",
        "R3-B25-FE-BUNDLE-BUDGET",
        "Round4 cross-reference only",
    ):
        assert token in text


def test_post14Prompt14AkshareValidationDefer_isInRegistry() -> None:
    """覆盖范围：PROMPT_14 akshare validation 失败后的 registry 登记（ADV-POST14-A-009 / B-011）。
    测试对象：AUDIT_DEFERRED_REGISTRY + UNRESOLVED_ISSUES_REGISTRY。
    目的：确保 akshare validation re-defer 有 SSOT 行且交叉引用 R3-B2.75-REQ2-EM（不得关闭）。"""
    audit = _read(AUDIT_DEFERRED)
    unresolved = _read(UNRESOLVED)

    for item_id in ("R3-PROMPT14-AKSHARE-VAL-01",):
        assert item_id in audit
        assert item_id in unresolved
        assert f"| {item_id} | DEFERRED" in unresolved

    for token in (
        "fetch_daily_bar_validation",
        "stock_zh_a_hist",
        "R3-B2.75-REQ2-EM",
        "prompt14_user_authorization_2026-06-22.md",
        "feature-round3-real-data-staged-pilot",
    ):
        assert token in audit
        assert token in unresolved


def test_post14R3Partial1_noLongerClaimsBackfillSkipsValidator() -> None:
    """覆盖范围：R3-PARTIAL-1 陈旧叙事修正（ADV-POST14-B-004）。
    测试对象：三份 registry + ROUND2_REPAIR_ALIGNMENT_TRACKER。
    目的：registry 不再声称 backfill 跳过 validator；应记录 ADV-R3X-SYNC-002 已闭合 severe-conflict 子范围。"""
    audit = _read(AUDIT_DEFERRED)
    unresolved = _read(UNRESOLVED)
    tracker = _read(PROJECT_ROOT / "docs/quality/ROUND2_REPAIR_ALIGNMENT_TRACKER.md")

    assert "skips validator + clean write" not in audit
    assert "skips validator + clean write" not in unresolved
    for token in ("ADV-R3X-SYNC-002", "validate+write", "severe conflict"):
        assert token in audit
        assert token in unresolved
    assert "ADV-R3X-SYNC-002" in tracker


def test_post14AdversarialReport_syncsPrompt15ResolvedBanner() -> None:
    """覆盖范围：adversarial_audit_report 与 PROMPT_15 闭合状态同步（ADV-POST14-B-001）。
    测试对象：docs/quality/adversarial_audit_report.md。
    目的：读者可见历史快照标注 + 指向 post-14 审计与 PROMPT_15 RESOLVED 章节。"""
    text = _read(ADVERSARIAL_REPORT)

    for token in (
        "历史快照",
        "PROMPT_15",
        "adversarial_audit_post14",
        "立即修复",
    ):
        assert token in text


def test_post14PonytailScan_sc05DocumentsErrorRedactionWiring() -> None:
    """覆盖范围：SC-05 语义修正（ADV-POST14-B-003）。
    测试对象：PONYTAIL_MODULE_SCAN_20260622.md。
    目的：扫描文档记录 error_redaction 已被 db/sync/datasources 引用，非死代码。"""
    text = _read(PONYTAIL_SCAN)

    assert "SC-05" in text
    for token in (
        "error_redaction",
        "db/sync/datasources",
        "PROMPT_17",
    ):
        assert token in text
    assert "本仓库无引用" not in text


def test_post14PonytailScan_hasPost1617DeltaSection() -> None:
    """覆盖范围：ponytail 扫描 post-16/17 增量（ADV-POST14-B-006）。
    测试对象：PONYTAIL_MODULE_SCAN_20260622.md §10。
    目的：Bucket A/C 闭合项有权威 delta 节，避免扫描表永久陈旧。"""
    text = _read(PONYTAIL_SCAN)

    assert "## 10. Post PROMPT_16/17 delta" in text
    for token in ("PROMPT_16", "PROMPT_17", "SC-05", "DS-01", "OP-02"):
        assert token in text.split("## 10. Post PROMPT_16/17 delta", maxsplit=1)[1]


def test_post14DatabaseGuidelines_listsMigration009StatusCheck() -> None:
    """覆盖范围：database-guidelines 与 migration 009 叙事对齐（ADV-POST14-B-005）。
    测试对象：.trellis/spec/backend/database-guidelines.md。
    目的：spec 列出 007–011 迁移分层，并区分 fetch_log status CHECK vs SUCCESS evidence app 层。"""
    text = _read(DATABASE_GUIDELINES)

    for token in (
        "009_status_check_constraints",
        "010_lineage_not_null",
        "011_layer1_tables",
        "fetch_log",
        "SUCCESS evidence",
        "application layer",
    ):
        assert token in text


def test_post14Prompt14StagedPilotCloseout_isDocumented() -> None:
    """覆盖范围：PROMPT_14 staged pilot closeout 叙事（ADV-POST14-A-016）。
    测试对象：AUDIT_DEFERRED + RESOLVED registries。
    目的：closeout PILOT_PASS_STAGED_RAW 与 pilot_closeout.json 证据路径可在 registry 追溯。"""
    audit = _read(AUDIT_DEFERRED)
    resolved = _read(RESOLVED)

    for token in (
        "R3-PROMPT14-STAGED-01",
        "PILOT_PASS_STAGED_RAW",
        "pilot_closeout.json",
        "feature-round3-real-data-staged-pilot",
    ):
        assert token in audit or token in resolved


POST14_HYGIENE_CONTRACT_LANE = (
    PROJECT_ROOT / "docs/quality/adversarial_audit_post14_contract_ponytail_lane.md"
)


def test_post14AuditDef03_isResolvedNotDeferred() -> None:
    """覆盖范围：R3-AUDIT-DEF-03 registry 卫生（Slice 3 B-027 已落地）。
    测试对象：三份 registry + test_ops_db_inspector 子目录 limit 测试。
    目的：per-subdir scan cap 测试已存在后，DEFERRED 表不得再声称缺失。"""
    audit = _read(AUDIT_DEFERRED)
    unresolved = _read(UNRESOLVED)
    resolved = _read(RESOLVED)
    inspector_tests = _read(PROJECT_ROOT / "tests/test_ops_db_inspector.py")

    assert "R3-AUDIT-DEF-03" in resolved
    assert "| R3-AUDIT-DEF-03 | Per-subdir" not in audit
    assert f"| R3-AUDIT-DEF-03 | DEFERRED" not in unresolved
    for subdir in ("raw", "parquet", "audit", "report"):
        assert subdir in inspector_tests
    assert "R3-AUDIT-DEF-03" in inspector_tests


def test_post14R2Risk3_failClosedModesDocumented() -> None:
    """覆盖范围：R2-RISK-3 / ADV-POST14-B-008 契约对齐卫生。
    测试对象：RESOLVED registry + WriteManager UNSUPPORTED_MODES 测试。
    目的：未实现 write_mode 显式拒绝已登记为 RESOLVED，而非陈旧“窄于合约”单一叙事。"""
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)

    assert "R2-RISK-3" in resolved
    assert f"| R2-RISK-3 | DEFERRED" not in unresolved
    for token in ("UNSUPPORTED_MODES", "replace_partition", "test_r3x_ponytail_structural_bucket_b"):
        assert token in resolved


_RECONCILED_TOKENS = ("2026-06-24", "fix α-2", "527d6506", "wave-A", "PROMPT_18")


def test_r3yRegistrySlice_alpha2LastReconciled() -> None:
    """覆盖范围：fix α-2 registry 切片后 SSOT 对账戳（slice α2-1）。
    测试对象：三份 registry + UNRESOLVED_ITEM_TASK_COVERAGE 头部 Last reconciled。
    目的：四份 SSOT 对账戳含同一组 mandatory tokens，防止措辞漂移（AUD-α2-002）。"""
    coverage = PROJECT_ROOT / "docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md"
    for path in (UNRESOLVED, RESOLVED, AUDIT_DEFERRED, coverage):
        text = _read(path)
        for token in _RECONCILED_TOKENS:
            assert token in text, f"missing {token!r} in {path.name} Last reconciled block"


def test_r3yAdvLineageDefer_registrySSOTWithOwner021() -> None:
    """覆盖范围：ADV-R3X-LINEAGE-001 DEFERRED 登记（slice α2-2）。
    测试对象：AUDIT_DEFERRED + UNRESOLVED + COVERAGE。
    目的：三 registry 与 COVERAGE 含 owner `021`+、closure test 描述；不得仍为 OPEN。"""
    audit = _read(AUDIT_DEFERRED)
    unresolved = _read(UNRESOLVED)
    coverage = _read(PROJECT_ROOT / "docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md")

    item_id = "ADV-R3X-LINEAGE-001"
    assert item_id in audit
    assert item_id in unresolved
    assert item_id in coverage
    assert re.search(rf"\|\s*{re.escape(item_id)}\s*\|\s*DEFERRED", unresolved)
    assert f"| {item_id} | OPEN" not in unresolved
    for token in ("021", "snapshot lineage pytest", "Batch 4B+"):
        assert token in audit
    assert "021_implement_layer3_snapshot_builder.md" in coverage


def test_waveAMainlineResolvedRows_traceableInRegistries() -> None:
    """覆盖范围：wave-A 已合并项 RESOLVED 可追溯（slice α2-3）。
    测试对象：RESOLVED + AUDIT_DEFERRED wave-A RESOLVED 节。
    目的：R3-TASK-019/020/023A、R3Y-AUDIT-GATE-18、R3-B3-STAGED-DOWNSTREAM-GATE 可在 registry 追溯。"""
    resolved = _read(RESOLVED)
    audit = _read(AUDIT_DEFERRED)

    wave_a_ids = (
        "R3-TASK-019",
        "R3-TASK-020",
        "R3-TASK-023A",
        "R3Y-AUDIT-GATE-18",
        "R3-B3-STAGED-DOWNSTREAM-GATE",
    )
    for item_id in wave_a_ids:
        assert item_id in resolved, f"{item_id} missing from RESOLVED"
        assert item_id in audit, f"{item_id} missing from AUDIT_DEFERRED wave-A section"


def test_round3Map_checkpointReflectsPost14AuditMerge() -> None:
    """覆盖范围：ROUND3_BATCH_IMPLEMENTATION_MAP checkpoint 与 wave-B 索引新鲜度。
    测试对象：ROUND3_BATCH_IMPLEMENTATION_MAP.md 头部 checkpoint 与 §2.4 / PROMPT 索引。
    目的：map 不得仍写 pre-wave-A checkpoint；应反映 020/PROMPT_18 已合并与 §2.4 活跃切片。"""
    text = _read(ROUND3_MAP)

    for token in (
        "527d6506",
        "post-wave-A",
        "PROMPT_18",
        "2.4",
        "020",
        "Done",
    ):
        assert token in text
    assert "PROMPT_14 + PROMPT_17** dispatched" not in text
    assert "**In progress** (user live auth granted)" not in text


def test_post14PonytailScan_hasPostBucketBDeltaSection() -> None:
    """覆盖范围：ponytail 扫描 post Bucket B 增量（Slice 4+4b merge）。
    测试对象：PONYTAIL_MODULE_SCAN_20260622.md §11。
    目的：桶 B 结构性闭合有权威 delta；§4 历史表保留但不得无 delta 声称 53 项仍 OPEN。"""
    text = _read(PONYTAIL_SCAN)

    assert "## 11. Post Bucket B structural delta" in text
    section = text.split("## 11. Post Bucket B structural delta", maxsplit=1)[1]
    for token in (
        "debt/round3-ponytail-structural-bucket-b",
        "remaining=0",
        "SC-01",
        "OP-01",
        "OP-03",
        "OP-06",
    ):
        assert token in section
    assert "仍 OPEN（Bucket B，53 项）" not in text


def test_post14ContractPonytailLane_reflectsBucketBMerge() -> None:
    """覆盖范围：post-14 contract ponytail 审计报告新鲜度。
    测试对象：adversarial_audit_post14_contract_ponytail_lane.md。
    目的：执行摘要不得仍写 53 项桶 B 开放；应记录 Slice 1–4 merge 后状态。"""
    text = _read(POST14_HYGIENE_CONTRACT_LANE)

    assert "4114fcb0" in text or "087f7271" in text
    assert "53 Bucket B items still open" not in text
    for token in ("Slice 4+4b", "remaining=0", "CLOSED@Slice"):
        assert token in text
