"""Batch 2.75 线上试点规划门禁文档对齐测试。

覆盖范围：MIGRATION_MAP、ROUND3 地图、018B 任务卡、production_live_pilot_policy
与三份 registry 是否一致反映 staged-only、fail-closed 与 sandbox-first 约束。
"""

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


def _read_three_registries() -> tuple[str, str, str]:
    """ponytail: audit/unresolved/resolved triple read used by registry alignment tests."""
    return (
        _read(AUDIT_REGISTRY),
        _read(UNRESOLVED_REGISTRY),
        _read(RESOLVED_REGISTRY),
    )


def test_projectMap_reflectsBatch275CurrentStatus() -> None:
    """覆盖范围：MIGRATION_MAP 是否反映 Batch 2.75 当前规划状态
    测试对象：MIGRATION_MAP.md
    目的/目标：项目地图读者能看到 2.75 试点策略与任务卡入口
    验证点：含 Last updated: 2026-06-23、Batch 2.75、production_live_pilot_policy.md、018B_production_live_pilot_gate.md、PILOT_FAIL_SOURCE
    失败含义：迁移地图未更新 2.75，新人会按旧批次顺序理解优先级
    """
    text = _read(MIGRATION_MAP)
    assert "Last updated: 2026-06-23" in text
    assert "Batch 2.75" in text
    assert "production_live_pilot_policy.md" in text
    assert "018B_production_live_pilot_gate.md" in text
    assert "PILOT_FAIL_SOURCE" in text


def test_round3Map_placesBatch275_beforeBatch3() -> None:
    """覆盖范围：ROUND3 地图里 Batch 2.75 相对 2.5/3 的执行顺序与来源索引
    测试对象：ROUND3_BATCH_IMPLEMENTATION_MAP.md §4.2 与 §5
    目的/目标：2.75 live pilot 规划必须在 Batch 3 建模之前，且来源包写明 raw-only 约束
    验证点：含 R3-B2.75-PROD-LIVE-PILOT 等；执行顺序 Batch 2.5 < 2.75 < 3；来源索引含 Batch 2.75、raw-only micro-fetch、no production DB mutation
    失败含义：顺序或来源索引错误，可能先开 Batch 3 而跳过 pilot 门禁
    """
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
    """覆盖范围：018B 任务卡对授权、sandbox 与默认参数的 fail-closed 要求
    测试对象：018B_production_live_pilot_gate.md
    目的/目标：任务卡明文禁止未授权 live、生产库写入与静默回退 fixture
    验证点：required_tokens 全部出现；dry_run/raw_only/write_target/allow_clean_write 字段与对应默认值文案同在
    失败含义：任务卡缺关键禁止项，执行者可能默认打开 live 或写生产库
    """
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
    """覆盖范围：production_live_pilot_policy 默认控制项与通过 2.75 的含义
    测试对象：docs/quality/production_live_pilot_policy.md
    目的/目标：策略表应保持线上源默认关闭、只写沙箱、禁止全市场拉取与静默回退
    验证点：各 control/default 成对出现；含 Passing Batch 2.75 does not mean formal production data access is open
    失败含义：策略文档弱化默认锁，读者可能以为过 2.75 即开放正式生产数据
    """
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
    """覆盖范围：三份 registry 对 B2.5-O-05 与 Batch 2.75 项的交叉引用
    测试对象：AUDIT_DEFERRED、UNRESOLVED、RESOLVED registries
    目的/目标：live FRED 仍 deferred 到 2.75，且 2.75 规划/开放项状态一致
    验证点：audit/unresolved 含 B2.5-O-05 与 018B；audit 含 production_live_pilot_policy、Not closed by Batch 2.75 Request 3、test_fred_staged_semantics；resolved 含 R3-B2.75-01、PILOT_FAIL_SOURCE；unresolved 含 R3-B2.75-REQ2-EM
    失败含义：registry 叙事不一致，会误判 FRED live 或 Request 2 是否已闭合
    """
    audit, unresolved, _resolved = _read_three_registries()
    for registry in (audit, unresolved):
        assert "B2.5-O-05" in registry
        assert "018B_production_live_pilot_gate.md" in registry
    assert "production_live_pilot_policy.md" in audit
    assert "Not closed by Batch 2.75 Request 3" in audit
    assert "test_fred_staged_semantics.py" in audit
    assert "R3-B2.75-01" in _resolved
    assert "PILOT_FAIL_SOURCE" in _resolved
    assert "R3-B2.75-REQ2-EM" in unresolved


def test_resolvedRegistry_recordsPlanningGateWithoutClosingLivePilot() -> None:
    """覆盖范围：R3-B2.75-PLAN-01 规划门禁已 RESOLVED 但未闭合 live pilot
    测试对象：AUDIT_DEFERRED、RESOLVED、UNRESOLVED registries
    目的/目标：规划阶段通过不等于线上 live pilot 已关闭
    验证点：PLAN-01 在 audit 与 resolved；resolved 写明 Does not close R3-B2.75-01 且仍含 PILOT_FAIL_SOURCE；REQ2-EM 仍在 unresolved；resolved 含 25 passed in current session
    失败含义：把规划门禁误当 live pilot 闭合，会过早宣称 production-live 就绪
    """
    audit, _unresolved, resolved = _read_three_registries()

    assert "R3-B2.75-PLAN-01" in audit
    assert "R3-B2.75-PLAN-01" in resolved
    assert "Does not close `R3-B2.75-01`" in resolved
    assert "R3-B2.75-01" in resolved
    assert "PILOT_FAIL_SOURCE" in resolved
    assert "R3-B2.75-REQ2-EM" in _unresolved
    assert "25 passed in current session" in resolved


def test_docsIndexesExposeBatch275EntryPoints() -> None:
    """覆盖范围：建模 README 与 docs INDEX 是否暴露 Batch 2.75 入口
    测试对象：ROUND_3_MODELING_LAYERS/README.md、docs/INDEX.md
    目的/目标：文档索引能一键找到 018B 策略与相邻任务卡
    验证点：readme 含 018B、018A、018C、019；index 含 production_live_pilot_policy 与 018B
    失败含义：索引缺入口，执行者要从散落路径手工搜 2.75 材料
    """
    readme = _read(MODELING_README)
    index = _read(DOCS_INDEX)
    assert "018B_production_live_pilot_gate.md" in readme
    assert "018A_layer1_observation_ingestion_bridge.md" in readme
    assert "018C_tdx_pytdx_low_cost_probe.md" in readme
    assert "`019`" in readme
    assert "production_live_pilot_policy.md" in index
    assert "018B_production_live_pilot_gate.md" in index


def test_policy_requiresStagedPilotConflictEvidenceChecklist() -> None:
    """覆盖范围：策略 §6 对 staged pilot 冲突证据的检查清单
    测试对象：production_live_pilot_policy.md §6
    目的/目标：live pilot 证据必须来自冲突报告或显式无冲突记录，不能用 fixture 顶替
    验证点：含 Conflict report or explicit no-conflict evidence；含 No fixture/staged fallback satisfies live pilot evidence
    失败含义：策略未要求冲突证据，staged 数据可能被当成 live pilot 合格证明
    """
    text = _read(POLICY)
    assert "Conflict report or explicit no-conflict evidence" in text
    assert "No fixture/staged fallback satisfies live pilot evidence" in text


def test_stagedPilotModuleAlignsWithProductionLivePolicyControls() -> None:
    """覆盖范围：staged_pilot 预批准请求信封是否与策略默认一致
    测试对象：backend.app.ops.staged_pilot.approved_pilot_requests()
    目的/目标：代码层预批准请求应与策略一致：只拉 raw、只写沙箱、默认 dry-run、禁止清洁写入
    验证点：每个 request 满足 raw_only is True、write_target==sandbox、allow_clean_write is False、dry_run is True
    失败含义：模块默认参数比策略松，试点可能悄悄允许写库或非 dry-run
    """
    from backend.app.ops.staged_pilot import approved_pilot_requests

    for request in approved_pilot_requests():
        assert request.raw_only is True
        assert request.write_target == "sandbox"
        assert request.allow_clean_write is False
        assert request.dry_run is True


def test_r3h10_policyDocumentsRehearsalVsProductFetchSsot() -> None:
    """覆盖范围：R3H-10 rehearsal 与产品 fetch 硬边界文档（S10-03）
    测试对象：production_live_pilot_policy.md §9 · datasource_service.md §7
    目的/目标：审计员可区分 rehearsal 证据与 DataSourceService 产品金路径
    验证点：policy 含 REHEARSAL_ONLY / product fetch SSOT；datasource_service 含 rehearsal-only 列表
    失败含义：文档未写清边界，R3H-08 可能误用 staged pilot 充当产品 live
    """
    policy = _read(POLICY)
    ds_doc = _read(PROJECT_ROOT / "docs/modules/datasource_service.md")
    assert "Rehearsal vs product fetch SSOT" in policy
    assert "REHEARSAL_ONLY" in policy
    assert "DataSourceService" in policy
    assert "Rehearsal vs product live" in ds_doc
    assert "interface_probe" in ds_doc


def test_r3h10_rehearsalScriptsDoNotClaimProductLiveReady() -> None:
    """覆盖范围：rehearsal 入口不声称 product-live ready（S10-03）
    测试对象：rehearsal_boundary · staged_pilot · run_staged_pilot.py
    目的/目标：rehearsal 模块显式 REHEARSAL_ONLY，且 PRODUCT_LIVE_READY 为 False
    验证点：REHEARSAL_ONLY is True；PRODUCT_LIVE_READY is False；脚本 description 含 REHEARSAL_ONLY
    失败含义：rehearsal 入口可被误读为 R3H-08 产品 live 替身
    """
    from backend.app.ops import live_pilot, rehearsal_boundary, staged_pilot

    script = _read(PROJECT_ROOT / "scripts/run_staged_pilot.py")
    assert rehearsal_boundary.REHEARSAL_ONLY is True
    assert rehearsal_boundary.PRODUCT_LIVE_READY is False
    assert "REHEARSAL_ONLY" in (staged_pilot.__doc__ or "")
    assert "REHEARSAL_ONLY" in (live_pilot.__doc__ or "")
    assert "REHEARSAL_ONLY" in script


def test_r3h10_syncOrchestratorDefaultChainExcludesStagedPilot() -> None:
    """覆盖范围：sync orchestrator 默认 import 链不含 staged pilot（S10-03）
    测试对象：backend.app.sync.orchestrator 模块源码
    目的/目标：产品 Sync 路径与 rehearsal 模块解耦
    验证点：orchestrator.py 不含 staged_pilot / live_pilot  import
    失败含义：编排器默认链耦合 rehearsal，产品路径边界模糊
    """
    orch_path = PROJECT_ROOT / "backend/app/sync/orchestrator.py"
    text = orch_path.read_text(encoding="utf-8")
    assert "staged_pilot" not in text
    assert "live_pilot" not in text
