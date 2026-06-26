"""Round 3H source final-decision planning gate tests."""

from __future__ import annotations

from tests.contract_gate_support import PROJECT_ROOT

BATCH3H_ROOT = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY"
    / "BATCH_3H_REAL_DATA_PRODUCTION_ENTRY"
)
ROUND4_ROOT = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST"
    / "BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION"
)

SOURCE_GROUPS = {
    "R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md": {
        "fred",
        "us_treasury",
        "sec_edgar",
        "cftc_cot",
        "bis",
        "world_bank",
    },
    "R3H_02_MARKET_DATA_ADAPTERS.md": {
        "alpha_vantage",
        "stooq",
        "yahoo_finance",
        "deribit",
        "coingecko",
    },
    "R3H_03_CN_MARKET_ADAPTERS.md": {
        "baostock",
        "akshare",
        "cninfo",
        "tdx_pytdx",
        "mootdx",
        "eastmoney",
        "sina_finance",
        "ths_ifind",
        "qmt_xtdata",
        "qmt_xqshare",
    },
    "R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md": {
        "kalshi",
        "polymarket",
        "web_search",
    },
}


def test_r3hTaskCards_coverEveryTargetSource() -> None:
    """覆盖范围：Round 3H 全部目标 source 任务卡覆盖
    测试对象：R3H-01 至 R3H-04 任务卡
    目的/目标：防止退回“只做一组 adapter / sample source”口径
    验证点：每个目标 source 都出现在负责它的 R3H 卡中
    失败含义：Round4 可能包装未关闭的 source 空壳
    """
    for card_name, source_ids in SOURCE_GROUPS.items():
        text = (BATCH3H_ROOT / card_name).read_text(encoding="utf-8")
        missing = sorted(source_id for source_id in source_ids if source_id not in text)
        assert not missing, f"{card_name} missing sources: {missing}"


def test_r3hFinalDecisionEnums_areGateAuthority() -> None:
    """覆盖范围：Round 3H source 最终状态枚举
    测试对象：BATCH_3H_HARDENING_RULES 与 R3H-05
    目的/目标：每个 source 只能 READY_WITH_EVIDENCE 或 ADR_DISABLED_OUT_OF_SCOPE
    验证点：枚举和 BLOCK 语义同时存在
    失败含义：source 可能重新落入 vague proposed-disabled 状态
    """
    combined = "\n".join(
        [
            (BATCH3H_ROOT / "BATCH_3H_HARDENING_RULES.md").read_text(
                encoding="utf-8"
            ),
            (BATCH3H_ROOT / "R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md").read_text(
                encoding="utf-8"
            ),
        ]
    )
    assert "READY_WITH_EVIDENCE" in combined
    assert "ADR_DISABLED_OUT_OF_SCOPE" in combined
    assert "BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE" in combined
    assert "vague proposed-disabled" in combined


def test_batch04RequiresR3hAdmissionBeforeProductization() -> None:
    """覆盖范围：Round4 产品化入口门禁
    测试对象：Batch04 README/manifest/hardening/playbook
    目的/目标：Round4 不能包装未完成 source registry 空壳
    验证点：Batch04 入口文件要求 R3H-05 PASS 或 WARN_WITH_ADR
    失败含义：API/前端/Agent 可能先于真实数据接入闭环启动
    """
    entry_files = [
        "README.md",
        "BATCH_04_TASK_CARD_MANIFEST.md",
        "BATCH_04_HARDENING_RULES.md",
        "BATCH_04_COORDINATOR_PLAYBOOK.md",
    ]
    for filename in entry_files:
        text = (ROUND4_ROOT / filename).read_text(encoding="utf-8")
        assert "R3H-05" in text, filename
        assert "PASS_ROUND4_REAL_DATA_READY" in text, filename
        assert "WARN_ROUND4_ALLOWED_WITH_NARROWED_SCOPE_ADR" in text, filename
        assert "BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE" in text, filename
