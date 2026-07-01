"""Round 3 Batch 2.5 / 2.75 审计跟进 registry 对齐测试。

覆盖范围：三份 registry、ROUND3 地图、ponytail 扫描与 post-14 审计报告
是否一致反映 wave-A 合并、Bucket B 闭合与仍开放的 perf/hygiene 叙事。
"""

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
    """覆盖范围：Batch 2.5 已闭合项在 registry 与 .gitignore 中的状态
    测试对象：RESOLVED、UNRESOLVED registries 与 .gitignore
    目的/目标：已解决的文档债不应还在开放项表里占一行
    验证点：三项 ID 在 resolved 且 unresolved 无 | ID | OPEN；resolved 含 BATCH3 gate 与 pytest slow；gitignore 含 .audit-sandboxpytest-*/
    失败含义：已闭合项仍显示 OPEN，审计会重复派工同一文档债
    """
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


def test_hyg03_perfBudgetClosedInResolved() -> None:
    """覆盖范围：R3-B25-HYG-03 / R3-B25-PERF-BUDGET-01 在 Wave 4 prep 后应已闭合
    测试对象：RESOLVED_ISSUES_REGISTRY、UNRESOLVED_ISSUES_REGISTRY
    目的/目标：perf budget CI artifact 交付后不得仍标 UNRESOLVED DEFERRED
    验证点：两 ID 在 RESOLVED；UNRESOLVED 无 HYG-03 DEFERRED 行；RESOLVED 含 ci_perf_budget_artifact
    失败含义：性能基准债叙事陈旧，协调人仍会重复开 Batch6 perf 切片
    """
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)

    for item_id in ("R3-B25-HYG-03", "R3-B25-PERF-BUDGET-01"):
        assert item_id in resolved
    assert "| R3-B25-HYG-03 | DEFERRED" not in unresolved
    assert "ci_perf_budget_artifact" in resolved


WAVE4_PREP_CLOSED_IDS = (
    "R2-GAP-1",
    "R3-AUDIT-DEF-01",
    "R3-B25-PERF-BUDGET-01",
    "R3-B25-HYG-03",
    "D3-P1-2",
    "A9-P2-01",
    "R2-RISK-4",
    "R3-B6-021-O-01",
    "R3-B6-021-O-02",
    "R3Y-TEST-DEPTH-001",
)


def test_wave4PrepClosed_traceableInAuditDeferredResolved() -> None:
    """覆盖范围：Wave 4 prep 已闭合项在 AUDIT_DEFERRED RESOLVED 段可追溯
    测试对象：RESOLVED_ISSUES_REGISTRY、AUDIT_DEFERRED_REGISTRY §Wave 4 prep
    目的/目标：CR-001 — CLOSED 项不得仅在三件套 RESOLVED，AUDIT_DEFERRED 仍留 DEFERRED 行
    验证点：十项 ID 均在 RESOLVED；均在 AUDIT_DEFERRED Wave 4 prep RESOLVED 段
    失败含义：registry 双轨真相，Plan agent 会误读为仍 DEFERRED
    """
    resolved = _read(RESOLVED)
    audit = _read(AUDIT_DEFERRED)
    wave4_section = audit.split("## RESOLVED — Wave 4 prep hygiene", 1)[1].split("\n---\n", 1)[0]

    for item_id in WAVE4_PREP_CLOSED_IDS:
        assert item_id in resolved, item_id
        assert item_id in wave4_section, item_id


def test_wave4PrepClosed_notInAuditDeferredOpsOrBatch275Tables() -> None:
    """覆盖范围：已闭合项不得仍出现在 AUDIT_DEFERRED 活跃 DEFERRED 表
    测试对象：AUDIT_DEFERRED Round 3 ops / Batch 2.75 / PROMPT_18 / Batch1 audit 段
    目的/目标：CR-001 — 从 DEFERRED 表删除已迁 RESOLVED 的行
    验证点：十项 ID 在四个 DEFERRED 段内无 | ID | 表行
    失败含义：审计仍把已交付项当开放债重复派工
    """
    audit = _read(AUDIT_DEFERRED)
    deferred_chunks = []
    for header in (
        "## DEFERRED — Round 3 ops",
        "## DEFERRED — Round 3 Batch 2.75",
        "## DEFERRED — Round 3 PROMPT_18 R3Y follow-ups",
        "## DEFERRED — Round 3 Batch 1 audit",
    ):
        if header in audit:
            deferred_chunks.append(audit.split(header, 1)[1].split("\n## ", 1)[0])

    combined = "\n".join(deferred_chunks)
    for item_id in WAVE4_PREP_CLOSED_IDS:
        assert f"| {item_id}" not in combined, item_id


def test_task019_requiresBatch3StagedOnlyDownstreamGate() -> None:
    """覆盖范围：019 任务卡对 Batch 3 staged-only 下游门禁的前置引用
    测试对象：019_implement_layer2_cross_asset_sensor.md
    目的/目标：Layer2 实现必须承认 ingestion 仍是 staged 且 2.75 live 未就绪
    验证点：含 Batch 3 staged-only gate 文档路径、staged 非 production-live、018A 桥接、R3-B2.75-01、production-live readiness 措辞
    失败含义：019 卡未绑 Batch3 gate，建模层可能假设 production-live 已开
    """
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
    """覆盖范围：ROUND3 地图是否完整列出 Batch 2.75 范围内外条目
    测试对象：ROUND3_BATCH_IMPLEMENTATION_MAP.md
    目的/目标：地图同时记录 2.75 必做 ID、试点 verdict 与明确不在 2.75 的工作
    验证点：必含 R3-B2.75-PROD-LIVE-PILOT、各 PILOT_* verdict、perf-budget 脚本等；亦含 migration 008、ingestion split、frontend budget、Batch3 modeling 等「在范围内」说明 token
    失败含义：2.75 范围 ledger 残缺，执行者不知道哪些债仍属本批次
    """
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
    """覆盖范围：018B 任务卡内的 Batch 2.75 scope ledger 与 closeout 阶段
    测试对象：018B_production_live_pilot_gate.md
    目的/目标：任务卡自描述 2.75 各 phase、perf gate 与 handoff，并列出 not in Batch 2.75 项
    验证点：含 scope ledger 各 ID、Phase -1/4.5、production_equivalent_smoke、Batch 3 handoff；含 No migration 008、No R2b-R2d、No frontend budget、No Batch3 Layer2、No Batch6 gate 等排除项
    失败含义：018B 范围自述不全，审计无法对照 plan 验 scope 边界
    """
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
    """覆盖范围：ROUND3 地图对 post-audit ingestion split 与 Round4 交叉引用
    测试对象：ROUND3_BATCH_IMPLEMENTATION_MAP.md
    目的/目标：R2b/R2c/R2d 与 FE bundle budget 等债在地图有独立条目且标 Round4 cross-reference
    验证点：含 R3-B25-INGEST-SPLIT-R2B、INGEST-MONOLITH-R2C-R2D、rollback plan、R3-B25-FE-BUNDLE-BUDGET、Round4 cross-reference only
    失败含义：ingestion/FE 债未入地图，会被误当成 2.75 内必须当场闭合
    """
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
    """覆盖范围：PROMPT_14 akshare validation 失败后的 registry 登记
    测试对象：AUDIT_DEFERRED_REGISTRY、UNRESOLVED_ISSUES_REGISTRY
    目的/目标：R3-PROMPT14-AKSHARE-VAL-01 在 audit/unresolved 为 DEFERRED 且交叉引用 REQ2-EM
    验证点：item_id 在两 registry；unresolved 有 | ID | DEFERRED 行；交叉引用 token 在 audit∪unresolved 可索引
    失败含义：akshare validation 重 defer 无 SSOT，Request 2 状态会被误读为已关闭
    """
    audit = _read(AUDIT_DEFERRED)
    unresolved = _read(UNRESOLVED)

    for item_id in ("R3-PROMPT14-AKSHARE-VAL-01",):
        assert item_id in audit
        assert item_id in unresolved
        assert f"| {item_id} | DEFERRED" in unresolved

    cross_ref_tokens = (
        "fetch_daily_bar_validation",
        "stock_zh_a_hist",
        "R3-B2.75-REQ2-EM",
        "prompt14_user_authorization_2026-06-22.md",
        "feature-round3-real-data-staged-pilot",
    )
    combined = audit + unresolved
    for token in cross_ref_tokens:
        assert token in combined


def test_post14R3Partial1_noLongerClaimsBackfillSkipsValidator() -> None:
    """覆盖范围：R3-PARTIAL-1 陈旧「backfill 跳过 validator」叙事是否已修正
    测试对象：三份 registry 与 ROUND2_REPAIR_ALIGNMENT_TRACKER.md
    目的/目标：registry 应记录 ADV-R3X-SYNC-002 已闭合 severe-conflict 子范围，而非声称跳过 validator
    验证点：audit/unresolved 不含 skips validator + clean write；含 ADV-R3X-SYNC-002、validate+write、severe conflict；tracker 含 SYNC-002
    失败含义：陈旧叙事仍在，读者会以为 backfill 仍可绕过校验写库
    """
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
    """覆盖范围：adversarial_audit_report 与 PROMPT_15 闭合横幅是否同步
    测试对象：docs/quality/adversarial_audit_report.md
    目的/目标：读者看到历史快照标注并指向 post-14 审计与 PROMPT_15 RESOLVED 章节
    验证点：含 历史快照、PROMPT_15、adversarial_audit_post14、立即修复 等 token
    失败含义：对抗审计报告仍像未闭合快照，会误导 PROMPT_15 实际状态
    """
    text = _read(ADVERSARIAL_REPORT)

    for token in (
        "历史快照",
        "PROMPT_15",
        "adversarial_audit_post14",
        "立即修复",
    ):
        assert token in text


def test_post14PonytailScan_sc05DocumentsErrorRedactionWiring() -> None:
    """覆盖范围：PONYTAIL 扫描 SC-05 是否修正为 error_redaction 已接线
    测试对象：PONYTAIL_MODULE_SCAN_20260622.md SC-05 段
    目的/目标：扫描文档不得再写 error_redaction 为死代码
    验证点：含 SC-05、error_redaction、db/sync/datasources、PROMPT_17；不含「本仓库无引用」
    失败含义：SC-05 仍标死代码，后续 hardening 可能重复派工同一模块
    """
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
    """覆盖范围：ponytail 扫描是否新增 §10 Post PROMPT_16/17 delta
    测试对象：PONYTAIL_MODULE_SCAN_20260622.md §10
    目的/目标：Bucket A/C 闭合项有权威增量节，避免扫描表永久停在旧 OPEN 数
    验证点：含 ## 10. Post PROMPT_16/17 delta；该节含 PROMPT_16/17、SC-05、DS-01、OP-02
    失败含义：缺 delta 节，读者会按过时扫描表理解模块卫生状态
    """
    text = _read(PONYTAIL_SCAN)

    assert "## 10. Post PROMPT_16/17 delta" in text
    for token in ("PROMPT_16", "PROMPT_17", "SC-05", "DS-01", "OP-02"):
        assert token in text.split("## 10. Post PROMPT_16/17 delta", maxsplit=1)[1]


def test_post14DatabaseGuidelines_listsMigration009StatusCheck() -> None:
    """覆盖范围：database-guidelines 是否与 migration 009–011 叙事对齐
    测试对象：.trellis/spec/backend/database-guidelines.md
    目的/目标：spec 列出迁移分层并区分 fetch_log CHECK 与 SUCCESS evidence 的应用层职责
    验证点：含 009_status_check、010_lineage_not_null、011_layer1_tables、fetch_log、SUCCESS evidence、application layer
    失败含义：数据库指南缺新迁移说明，实现者可能误判 status CHECK 与证据层边界
    """
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
    """覆盖范围：PROMPT_14 staged pilot closeout 是否在 registry 可追溯
    测试对象：AUDIT_DEFERRED、RESOLVED registries
    目的/目标：PILOT_PASS_STAGED_RAW 与 pilot_closeout.json 证据路径可在 registry 查到
    验证点：R3-PROMPT14-STAGED-01、PILOT_PASS_STAGED_RAW、pilot_closeout.json、feature-round3-real-data-staged-pilot 至少在 audit 或 resolved 之一出现
    失败含义：staged pilot 闭合无 registry 行，无法审计 PROMPT_14 实际完成证据
    """
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
    """覆盖范围：R3-AUDIT-DEF-03 per-subdir scan cap 是否已 RESOLVED
    测试对象：三份 registry 与 tests/test_ops_db_inspector.py
    目的/目标：测试已存在后 DEFERRED 表不得再声称缺 per-subdir limit 测试
    验证点：DEF-03 在 resolved；audit 无 Per-subdir DEF-03 行；unresolved 无 DEFERRED DEF-03；inspector 测试含 raw/parquet/audit/report 与 R3-AUDIT-DEF-03
    失败含义：registry 仍标 deferred，会与已合并的 inspector 测试矛盾
    """
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
    """覆盖范围：R2-RISK-3 未实现 write_mode 显式拒绝是否已 RESOLVED
    测试对象：RESOLVED、UNRESOLVED registries
    目的/目标：UNSUPPORTED_MODES 行为已登记 resolved，而非留在 DEFERRED
    验证点：R2-RISK-3 在 resolved；unresolved 无 | R2-RISK-3 | DEFERRED；resolved 含 UNSUPPORTED_MODES、replace_partition、test_r3x_ponytail_structural_bucket_b
    失败含义：write_mode 拒绝仍标开放，与 bucket B 已闭合测试不一致
    """
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)

    assert "R2-RISK-3" in resolved
    assert f"| R2-RISK-3 | DEFERRED" not in unresolved
    for token in ("UNSUPPORTED_MODES", "replace_partition", "test_r3x_ponytail_structural_bucket_b"):
        assert token in resolved


_RECONCILED_LINE_PREFIX = "> Last reconciled:"


def _extract_last_reconciled_line(text: str) -> str:
    for line in text.splitlines():
        if line.startswith(_RECONCILED_LINE_PREFIX):
            return " ".join(line.split())
    raise AssertionError(f"missing {_RECONCILED_LINE_PREFIX!r} line")


def test_r3yRegistrySlice_alpha2LastReconciled() -> None:
    """覆盖范围：四份 SSOT 的 Last reconciled 行 normalize 后完全一致
    测试对象：UNRESOLVED、RESOLVED、AUDIT_DEFERRED、UNRESOLVED_ITEM_TASK_COVERAGE
    目的/目标：WAVE-B-HYG-02 — 子串匹配升级为整行相等，防措辞漂移
    验证点：四份文档提取的 Last reconciled 行 normalize 后相同
    失败含义：对账戳不一致，并行 slice 无法判断 registry 是否同一次 reconcile
    """
    coverage = PROJECT_ROOT / "docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md"
    paths = (UNRESOLVED, RESOLVED, AUDIT_DEFERRED, coverage)
    lines = [_extract_last_reconciled_line(_read(path)) for path in paths]
    canonical = lines[0]
    for path, line in zip(paths[1:], lines[1:], strict=True):
        assert line == canonical, f"{path.name} reconciled line drift:\n  got: {line}\n  exp: {canonical}"


def test_r3yAdvLineageDefer_registrySSOTWithOwner021() -> None:
    """覆盖范围：ADV-R3X-LINEAGE-001 DEFERRED 登记与 owner 021
    测试对象：AUDIT_DEFERRED、UNRESOLVED、UNRESOLVED_ITEM_TASK_COVERAGE
    目的/目标：血缘债在三 registry 与 COVERAGE 一致为 DEFERRED，owner 指向任务 021
    验证点：item 在三文档；unresolved 有 DEFERRED 表行且无 OPEN 行；audit 含 021、snapshot lineage pytest、Batch 5A+；coverage 含 021_implement_layer3_snapshot_builder.md
    失败含义：lineage defer 缺 owner 或状态不一，Batch 4B 前可能被误关
    """
    audit = _read(AUDIT_DEFERRED)
    unresolved = _read(UNRESOLVED)
    coverage = _read(PROJECT_ROOT / "docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md")

    item_id = "ADV-R3X-LINEAGE-001"
    assert item_id in audit
    assert item_id in unresolved
    assert item_id in coverage
    assert re.search(rf"\|\s*{re.escape(item_id)}\s*\|\s*DEFERRED", unresolved)
    assert f"| {item_id} | OPEN" not in unresolved
    for token in ("021", "snapshot lineage pytest", "Batch 6"):
        assert token in audit
    assert "021_implement_layer3_snapshot_builder.md" in coverage


def test_waveAMainlineResolvedRows_traceableInRegistries() -> None:
    """覆盖范围：wave-A 已合并主线项在 registry 的可追溯性
    测试对象：RESOLVED、AUDIT_DEFERRED registries
    目的/目标：019/020/023A、AUDIT-GATE-18、B3-STAGED-DOWNSTREAM-GATE 均可在两表查到
    验证点：五个 wave_a_ids 每个同时出现在 resolved 与 audit
    失败含义：wave-A 合并项未双登记，审计无法从 DEFERRED 表反查已闭合叙事
    """
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


def test_waveBMainlineResolvedRows_traceableInRegistries() -> None:
    """覆盖范围：wave-B 已合并主线项在 registry 的可追溯性
    测试对象：RESOLVED、AUDIT_DEFERRED registries
    目的/目标：021/PROMPT19-v2/MUT-PROOF/α-2 均可在两表查到
    验证点：五个 wave_b_ids 每个同时出现在 resolved 与 audit
    失败含义：wave-B 合并项未双登记，审计无法从 DEFERRED 表反查已闭合叙事
    """
    resolved = _read(RESOLVED)
    audit = _read(AUDIT_DEFERRED)

    wave_b_ids = (
        "R3-TASK-021",
        "R3-PROMPT19-V2",
        "R3Y-MUT-PROOF-001",
        "R3Y-REGISTRY-ALPHA2",
        "R3Y-SYNC-001",
    )
    for item_id in wave_b_ids:
        assert item_id in resolved, f"{item_id} missing from RESOLVED"
        assert item_id in audit, f"{item_id} missing from AUDIT_DEFERRED wave-B section"


def test_waveCMainlineResolvedRows_traceableInRegistries() -> None:
    """覆盖范围：wave-C 已合并主线项在 registry 的可追溯性
    测试对象：RESOLVED、AUDIT_DEFERRED registries
    目的/目标：PROMPT20-DH/022/STAGED-REG/PROMPT15-EVID 均可在两表查到
    验证点：四个 wave_c_ids 每个同时出现在 resolved 与 audit
    失败含义：wave-C 合并项未双登记，审计无法从 DEFERRED 表反查已闭合叙事
    """
    resolved = _read(RESOLVED)
    audit = _read(AUDIT_DEFERRED)

    wave_c_ids = (
        "R3-PROMPT20-DH",
        "R3-TASK-022",
        "R3Y-STAGED-REG-001",
        "R3Y-PROMPT15-EVID-001",
    )
    for item_id in wave_c_ids:
        assert item_id in resolved, f"{item_id} missing from RESOLVED"
        assert item_id in audit, f"{item_id} missing from AUDIT_DEFERRED wave-C section"


def test_batch3fMap_resolvedBatch6ItemsMarkedClosed() -> None:
    """覆盖范围：Batch 6 地图表中已 RESOLVED 项不得仍用活跃 repay 叙事
    测试对象：ROUND3_BATCH_IMPLEMENTATION_MAP.md §Batch 6 表
    目的/目标：R3-PARTIAL-5、R2-RISK-3 仅 regression guard，地图须标 CLOSED
    验证点：两 ID 邻近 chunk 含 CLOSED；不含「Close COMPLETED-vs-write」或「Add write_contract matrix doc」活跃措辞
    失败含义：地图仍派活已闭合项，六复杂线 agent 可能重复实现 crash-window / write_mode
    """
    text = _read(ROUND3_MAP)

    partial_chunk = text.split("R3-PARTIAL-5", maxsplit=1)[1][:320]
    risk_chunk = text.split("R2-RISK-3", maxsplit=1)[1][:320]

    assert "CLOSED" in partial_chunk
    assert "Close COMPLETED-vs-write crash window by same-transaction" not in partial_chunk
    assert "CLOSED" in risk_chunk
    assert "Add write_contract matrix doc or re-defer to Round5" not in risk_chunk


def test_batch3fPendingFixRegistry_reconciledInPendingFixDoc() -> None:
    """覆盖范围：WAVE-B-HYG-01/02/03 在待修复清单的 B3F-REG reconcile 登记
    测试对象：docs/quality/待修复清单.md
    目的/目标：R3F-LIN-03 要求 hygiene 残余行有明确 reconcile 状态
    验证点：§4 或 §5 含 WAVE-B-HYG-01/02/03 与 B3F-REG 或 reconcile 字样
    失败含义：hygiene 残余无收口记录，主会话无法批处理 registry 三件套
    """
    pending_fix = _read(PROJECT_ROOT / "docs/quality/待修复清单.md")

    for item_id in ("WAVE-B-HYG-01", "WAVE-B-HYG-02", "WAVE-B-HYG-03"):
        assert item_id in pending_fix
    assert "B3F-REG" in pending_fix or "reconcile" in pending_fix.lower()


def test_round3Map_checkpointReflectsPostBatch3VAndRound3F() -> None:
    """覆盖范围：ROUND3 地图 checkpoint 是否反映 post-Batch-3V 与 Round 3F 激活状态
    测试对象：ROUND3_BATCH_IMPLEMENTATION_MAP.md 头部与 §2
    目的/目标：地图须标明 Batch 3V Done、Wave E / Round 3F 为当前主线，且 Batch 3F 执行包可被索引
    验证点：含 2aeb6f0、Batch 3V、Round 3F、Wave E、Active、BATCH_3F_BATCH6_DATA_GOVERNANCE、PROJECT_IMPLEMENTATION_ROADMAP.md；Wave D 非 Active
    失败含义：地图 checkpoint 陈旧，协调人会按错误 wave/批次状态排期
    """
    text = _read(ROUND3_MAP)

    for token in (
        "2aeb6f0",
        "Batch 3V",
        "Round 3F",
        "Wave E",
        "Active",
        "BATCH_3F_BATCH6_DATA_GOVERNANCE",
        "PROJECT_IMPLEMENTATION_ROADMAP.md",
        "2.3 Worktree creation checklist",
        "376e30e6",
        "Wave D",
        "Done",
    ):
        assert token in text
    assert "| **D** | **Active**" not in text
    assert "**Active — Wave D" not in text


def test_round3Map_checkpointReflectsPostWaveCMerge() -> None:
    """覆盖范围：ROUND3 地图仍保留 wave-C 历史可追溯 token（向后兼容）
    测试对象：ROUND3_BATCH_IMPLEMENTATION_MAP.md §2.2 / §2.4
    目的/目标：post-Batch-01 地图仍提及 wave-C reconcile d49e21d3 等历史完成项
    验证点：含 d49e21d3、871b76e2、§2.2
    失败含义：wave-C 完成记录被 Batch 01 更新误删
    """
    text = _read(ROUND3_MAP)

    for token in (
        "d49e21d3",
        "871b76e2",
        "§2.2",
    ):
        assert token in text


def test_round3Map_checkpointReflectsPostWaveBMerge() -> None:
    """覆盖范围：ROUND3 地图仍保留 wave-B 历史可追溯 token（向后兼容）
    测试对象：ROUND3_BATCH_IMPLEMENTATION_MAP.md
    目的/目标：post-wave-C 地图仍提及 wave-B / 021 等历史完成项
    验证点：含 68b10982、post-wave-B、021、§2.4
    失败含义：wave-B 完成记录被 wave-C 更新误删
    """
    text = _read(ROUND3_MAP)

    for token in (
        "68b10982",
        "post-wave-B",
        "021",
        "§2.4",
    ):
        assert token in text


def test_round3Map_checkpointReflectsPost14AuditMerge() -> None:
    """覆盖范围：ROUND3 地图仍保留 wave-A 历史可追溯 token（向后兼容）
    测试对象：ROUND3_BATCH_IMPLEMENTATION_MAP.md
    目的/目标：post-wave-B 地图仍提及 PROMPT_18 / 020 等 wave-A 完成项
    验证点：含 PROMPT_18、020、2.4
    失败含义：wave-A 完成记录被 wave-B 更新误删
    """
    text = _read(ROUND3_MAP)

    for token in (
        "PROMPT_18",
        "020",
        "2.4",
    ):
        assert token in text


def test_post14PonytailScan_hasPostBucketBDeltaSection() -> None:
    """覆盖范围：ponytail 扫描 §11 Post Bucket B structural delta
    测试对象：PONYTAIL_MODULE_SCAN_20260622.md §11
    目的/目标：桶 B 结构性闭合有权威 delta，且全文不再声称 53 项仍 OPEN
    验证点：含 ## 11. Post Bucket B structural delta；节内含 bucket-b branch、remaining=0、SC-01、OP-01/03/06；全文无「仍 OPEN（Bucket B，53 项）」
    失败含义：扫描表永久显示 53 项 OPEN，与 bucket B merge 后事实不符
    """
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
    """覆盖范围：post-14 contract ponytail 审计报告是否反映 Bucket B merge
    测试对象：adversarial_audit_post14_contract_ponytail_lane.md
    目的/目标：执行摘要不得仍写 53 项桶 B 开放，应记录 Slice 1–4 merge 后 remaining=0
    验证点：含 4114fcb0 或 087f7271；不含 53 Bucket B items still open；含 Slice 4+4b、remaining=0、CLOSED@Slice
    失败含义：contract lane 报告仍标 53 项开放，与结构性闭合证据冲突
    """
    text = _read(POST14_HYGIENE_CONTRACT_LANE)

    assert "4114fcb0" in text or "087f7271" in text
    assert "53 Bucket B items still open" not in text
    for token in ("Slice 4+4b", "remaining=0", "CLOSED@Slice"):
        assert token in text
