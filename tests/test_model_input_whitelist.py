"""Round 3D — 五层模型输入白名单语义契约测试。

覆盖范围：specs/model_inputs/** 各行必填字段、P0 种子与 hardening 禁止角色转移。
"""

from __future__ import annotations

from typing import Any

import pytest
from tests.contract_gate_support import PROJECT_ROOT, load_yaml

MODEL_INPUTS = PROJECT_ROOT / "specs" / "model_inputs"

REQUIRED_ROW_FIELDS = (
    "input_id",
    "layer",
    "business_purpose",
    "data_domain",
    "source_id",
    "operation",
    "role",
    "readiness",
    "symbol_or_series",
    "window_cap",
    "row_cap",
    "requires_user_authorization",
    "allowed_next_gate",
    "forbidden_claims",
    "closure_test",
    "notes",
)

LAYER1_P0_SERIES = frozenset({"DGS10", "T10Y3M", "VIXCLS", "SP500", "DFII10"})

WHITELIST_FILES = {
    "layer1": MODEL_INPUTS / "layer1_source_whitelist.yaml",
    "layer2": MODEL_INPUTS / "layer2_source_whitelist.yaml",
    "layer3": MODEL_INPUTS / "layer3_anchor_source_plan.yaml",
    "layer4": MODEL_INPUTS / "layer4_market_source_plan.yaml",
    "layer5": MODEL_INPUTS / "layer5_instrument_source_plan.yaml",
}


def _load_whitelist_rows(layer_key: str) -> list[dict[str, Any]]:
    path = WHITELIST_FILES[layer_key]
    if not path.is_file():
        pytest.fail(f"missing whitelist file: {path.relative_to(PROJECT_ROOT)}")
    doc = load_yaml(path)
    rows = doc.get("rows") or []
    if not isinstance(rows, list) or not rows:
        pytest.fail(f"{path.name} must contain non-empty rows list")
    return rows


def _series_value(row: dict[str, Any]) -> str:
    sym = row.get("symbol_or_series")
    if isinstance(sym, list):
        return str(sym[0]) if sym else ""
    return str(sym or "")


# --- WL-01 Layer1 ---


def test_layer1_rows_have_required_fields() -> None:
    """覆盖范围：Layer1 白名单行 schema
    测试对象：specs/model_inputs/layer1_source_whitelist.yaml
    目的/目标：每行含任务卡 §6 全部必填字段
    验证点：REQUIRED_ROW_FIELDS 全集存在于每行
    失败含义：下游 FRED/SP3 无法无歧义选择 fetch scope
    """
    rows = _load_whitelist_rows("layer1")
    for row in rows:
        missing = [f for f in REQUIRED_ROW_FIELDS if f not in row]
        assert not missing, f"{row.get('input_id')}: missing {missing}"


def test_layer1_p0_fred_macro_series_sandbox_candidate() -> None:
    """覆盖范围：Layer1 P0 FRED 宏观序列
    测试对象：layer1_source_whitelist.yaml P0 种子行
    目的/目标：DGS10/T10Y3M/VIXCLS/SP500/DFII10 为 fred sandbox_candidate
    验证点：五序列存在；source_id=fred；readiness=sandbox_candidate；role=primary_candidate
    失败含义：FRED pilot 前置白名单未冻结，阻塞 B01-FRED/SP3
    """
    rows = _load_whitelist_rows("layer1")
    fred_p0 = [
        r
        for r in rows
        if r.get("source_id") == "fred"
        and _series_value(r) in LAYER1_P0_SERIES
        and r.get("readiness") == "sandbox_candidate"
    ]
    found_series = {_series_value(r) for r in fred_p0}
    assert found_series == LAYER1_P0_SERIES
    assert all(r.get("role") == "primary_candidate" for r in fred_p0)
    assert all(r.get("requires_user_authorization") is True for r in fred_p0)


def test_layer1_macro_supplementary_not_fred_primary() -> None:
    """覆盖范围：macro_supplementary 不得替代 FRED primary
    测试对象：layer1_source_whitelist.yaml akshare/macro_supplementary 行
    目的/目标：hardening §4/§8 — akshare 不得为 P0 FRED 序列 primary_candidate
    验证点：macro_supplementary 行 role≠primary_candidate；symbol 不与 P0 FRED 重叠作 primary
    失败含义：B2.5-O-05 可被错误闭合
    """
    rows = _load_whitelist_rows("layer1")
    macro_rows = [r for r in rows if r.get("data_domain") == "macro_supplementary"]
    assert macro_rows, "macro_supplementary domain must be documented explicitly"
    for row in macro_rows:
        assert row.get("source_id") == "akshare"
        assert row.get("role") != "primary_candidate"
        assert row.get("readiness") != "production_candidate"
        series = _series_value(row)
        if series in LAYER1_P0_SERIES:
            pytest.fail(
                f"macro_supplementary must not claim FRED P0 series {series} as primary path"
            )


def test_layer1_non_p0_indicators_deferred_or_p2() -> None:
    """覆盖范围：Layer1 非 P0 指标降级
    测试对象：layer1_source_whitelist.yaml 非 P0 行
    目的/目标：除五 P0 FRED 序列外 Layer1 指标标 deferred 或 P2
    验证点：非 P0 fred 行 readiness∈{deferred,P2} 或 notes 含 P2；无 production_candidate
    失败含义：白名单隐含全 Layer1 生产就绪
    """
    rows = _load_whitelist_rows("layer1")
    p0_ids = {
        r["input_id"]
        for r in rows
        if _series_value(r) in LAYER1_P0_SERIES and r.get("source_id") == "fred"
    }
    non_p0 = [r for r in rows if r["input_id"] not in p0_ids]
    assert non_p0, "deferred/P2 bucket must be explicit"
    for row in non_p0:
        if row.get("role") == "validation_only":
            # ponytail: akshare macro_supplementary — validation-only, not deferred bucket
            continue
        readiness = row.get("readiness")
        notes = str(row.get("notes") or "")
        deferred_ok = readiness in {"deferred", "fixture_only", "staged_only"}
        assert deferred_ok or "P2" in notes or row.get("role") == "deferred"
        assert readiness != "production_candidate"


# --- WL-02 Layer2 ---


def test_layer2_rows_have_required_fields() -> None:
    """覆盖范围：Layer2 跨资产白名单行 schema
    测试对象：specs/model_inputs/layer2_source_whitelist.yaml
    目的/目标：每行含任务卡 §6 全部必填字段
    验证点：REQUIRED_ROW_FIELDS 全集存在于每行
    失败含义：Layer2 staged/live 边界无法机器校验
    """
    rows = _load_whitelist_rows("layer2")
    for row in rows:
        missing = [f for f in REQUIRED_ROW_FIELDS if f not in row]
        assert not missing, f"{row.get('input_id')}: missing {missing}"


def test_layer2_display_only_assets_fixture_only() -> None:
    """覆盖范围：Layer2 VIX/HYG display-only 资产
    测试对象：layer2_source_whitelist.yaml 对照 layer2_cross_asset_registry_fixture
    目的/目标：L2-VIX、L2-HYG 标 fixture_only；无 live FRED 默认
    验证点：readiness=fixture_only；eligible live path 禁止
    失败含义：display-only 资产误作 sandbox live 输入
    """
    rows = _load_whitelist_rows("layer2")
    display_only_ids = {"L2-VIX", "L2-HYG"}
    mapped = {r.get("input_id"): r for r in rows if r.get("input_id") in display_only_ids}
    assert set(mapped) == display_only_ids
    for asset_id, row in mapped.items():
        assert row.get("readiness") == "fixture_only", asset_id
        assert row.get("role") in {"staged_fixture", "deferred"}
        assert "production-live ready" in (row.get("forbidden_claims") or [])


def test_layer2_copper_hg_staged_or_sandbox_not_live_fred() -> None:
    """覆盖范围：Layer2 Copper/HG 期货代理
    测试对象：layer2_source_whitelist.yaml L2-COPPER、L2-HG-MAIN
    目的/目标：staged_fixture 或 sandbox_candidate；无 live FRED 默认
    验证点：readiness∈{staged_fixture,sandbox_candidate,staged_only}；source_id≠fred 作 production
    失败含义：跨资产传感器误接 live FRED
    """
    rows = _load_whitelist_rows("layer2")
    copper_ids = {"L2-COPPER", "L2-HG-MAIN"}
    copper_rows = [r for r in rows if r.get("input_id") in copper_ids]
    assert len(copper_rows) == 2
    for row in copper_rows:
        assert row.get("readiness") in {"staged_fixture", "sandbox_candidate", "staged_only"}
        assert row.get("readiness") != "production_candidate"
        if row.get("source_id") == "fred":
            assert row.get("requires_user_authorization") is True


def test_layer2_hg_main_gate_readiness_consistency() -> None:
    """覆盖范围：L2-HG-MAIN allowed_next_gate 与 readiness 一致性
    测试对象：layer2_source_whitelist.yaml L2-HG-MAIN
    目的/目标：staged_fixture 当前态与 sandbox_clean_rehearsal 未来门不矛盾
    验证点：readiness=staged_fixture；allowed_next_gate 仅作下游授权升级路径
    失败含义：HG 被误读为已可 sandbox_clean_rehearsal live
    """
    rows = _load_whitelist_rows("layer2")
    hg = next((r for r in rows if r.get("input_id") == "L2-HG-MAIN"), None)
    assert hg is not None
    assert hg.get("readiness") == "staged_fixture"
    assert hg.get("allowed_next_gate") == "sandbox_clean_rehearsal"
    assert hg.get("role") == "staged_fixture"
    assert "production-live ready" in (hg.get("forbidden_claims") or [])
    notes = str(hg.get("notes") or "")
    assert "staged_fixture" in notes or "sandbox" in notes.lower()


    """覆盖范围：Layer2 无可用渠道资产
    测试对象：layer2_source_whitelist.yaml L2-NO-CHANNEL
    目的/目标：缺源资产标 deferred + closure_test
    验证点：readiness=deferred；role=deferred
    失败含义：无渠道资产被误标可拉数
    """
    rows = _load_whitelist_rows("layer2")
    no_ch = next((r for r in rows if r.get("input_id") == "L2-NO-CHANNEL"), None)
    assert no_ch is not None
    assert no_ch.get("readiness") == "deferred"
    assert no_ch.get("role") == "deferred"
    assert no_ch.get("closure_test")


# --- WL-03 Layer3 ---


def test_layer3_rows_have_required_fields() -> None:
    """覆盖范围：Layer3 anchor/source 计划行 schema
    测试对象：specs/model_inputs/layer3_anchor_source_plan.yaml
    目的/目标：每行含任务卡 §6 全部必填字段
    验证点：REQUIRED_ROW_FIELDS 全集存在于每行
    失败含义：产业链 anchor 源映射无法机器校验
    """
    rows = _load_whitelist_rows("layer3")
    for row in rows:
        missing = [f for f in REQUIRED_ROW_FIELDS if f not in row]
        assert not missing, f"{row.get('input_id')}: missing {missing}"


def test_layer3_staged_bundle_anchors_staged_only() -> None:
    """覆盖范围：Layer3 staged bundle anchor
    测试对象：layer3_anchor_source_plan.yaml MSFT/OPENAI
    目的/目标：staged bundle 项标 staged_only；loader_mode=staged_fixture_only
    验证点：readiness=staged_only；operation=load_staged_fixture
    失败含义：staged anchor 被误标 live source
    """
    rows = _load_whitelist_rows("layer3")
    staged_ids = {"L3-ANCHOR-MSFT", "L3-ANCHOR-OPENAI"}
    mapped = {r.get("input_id"): r for r in rows if r.get("input_id") in staged_ids}
    assert set(mapped) == staged_ids
    for row in mapped.values():
        assert row.get("readiness") == "staged_only"
        assert row.get("operation") == "load_staged_fixture"
        assert row.get("source_id") == "staged_fixture"


def test_layer3_missing_source_deferred_with_closure_test() -> None:
    """覆盖范围：Layer3 缺源 anchor
    测试对象：layer3_anchor_source_plan.yaml deferred 行
    目的/目标：无 source_keys 的产业链节点标 deferred + closure_test
    验证点：至少一行 readiness=deferred 且 closure_test 非空
    失败含义：缺源 anchor 静默进入 pilot
    """
    rows = _load_whitelist_rows("layer3")
    deferred = [r for r in rows if r.get("readiness") == "deferred"]
    assert deferred, "must document deferred anchors explicitly"
    for row in deferred:
        assert row.get("closure_test")
        assert row.get("role") == "deferred"


# --- WL-04 Layer4 ---


def test_layer4_rows_have_required_fields() -> None:
    """覆盖范围：Layer4 市场结构源计划行 schema
    测试对象：specs/model_inputs/layer4_market_source_plan.yaml
    目的/目标：每行含任务卡 §6 全部必填字段
    验证点：REQUIRED_ROW_FIELDS 全集存在于每行
    失败含义：市场结构首批源无法机器校验
    """
    rows = _load_whitelist_rows("layer4")
    for row in rows:
        missing = [f for f in REQUIRED_ROW_FIELDS if f not in row]
        assert not missing, f"{row.get('input_id')}: missing {missing}"


def test_layer4_cn_a_calendar_breadth_sandbox_candidate() -> None:
    """覆盖范围：Layer4 CN_A 首批市场输入
    测试对象：layer4_market_source_plan.yaml CN_A 行
    目的/目标：calendar/breadth 为 sandbox_candidate；对照 layer4_staged_market manifest
    验证点：market_id=CN_A；readiness=sandbox_candidate
    失败含义：A 股市场结构 pilot 无白名单锚点
    """
    rows = _load_whitelist_rows("layer4")
    cn_rows = [
        r
        for r in rows
        if "CN_A" in str(r.get("symbol_or_series"))
        or r.get("input_id", "").startswith("L4-CN-A")
    ]
    assert cn_rows, "CN_A entries required"
    for row in cn_rows:
        assert row.get("readiness") == "sandbox_candidate"
        assert row.get("readiness") != "production_candidate"


def test_layer4_non_cn_markets_deferred() -> None:
    """覆盖范围：Layer4 非 CN_A 市场
    测试对象：layer4_market_source_plan.yaml US/HK/FUT/options 行
    目的/目标：默认 deferred 除非已有 staged 支持
    验证点：US/HK/FUT/options market 行 readiness=deferred
    失败含义：非首批市场误进入 sandbox pilot
    """
    rows = _load_whitelist_rows("layer4")
    deferred_markets = {"US", "HK", "FUT", "OPTIONS"}
    found = {
        r.get("input_id", "")
        for r in rows
        if r.get("readiness") == "deferred"
        and any(
            m in str(r.get("notes") or "") or m in str(r.get("business_purpose") or "")
            for m in deferred_markets
        )
    }
    assert found, "must document US/HK/FUT/options as deferred"


# --- WL-05 Layer5 ---


def test_layer5_rows_have_required_fields() -> None:
    """覆盖范围：Layer5 instrument/evidence 源计划行 schema
    测试对象：specs/model_inputs/layer5_instrument_source_plan.yaml
    目的/目标：每行含任务卡 §6 全部必填字段
    验证点：REQUIRED_ROW_FIELDS 全集存在于每行
    失败含义：L5 证据链首批源无法机器校验
    """
    rows = _load_whitelist_rows("layer5")
    for row in rows:
        missing = [f for f in REQUIRED_ROW_FIELDS if f not in row]
        assert not missing, f"{row.get('input_id')}: missing {missing}"


def test_layer5_first_batch_sources_present() -> None:
    """覆盖范围：Layer5 首批 instrument/evidence 候选
    测试对象：layer5_instrument_source_plan.yaml
    目的/目标：baostock 日 K、cninfo 元数据、FRED macro daily、tdx validation-only
    验证点：四类 source_id 各至少一行；operation 与 source_route 契约一致
    失败含义：L5 白名单缺首批证据路径
    """
    rows = _load_whitelist_rows("layer5")
    by_source: dict[str, list] = {}
    for row in rows:
        by_source.setdefault(row.get("source_id", ""), []).append(row)
    for src in ("baostock", "cninfo", "fred", "tdx_pytdx"):
        assert src in by_source, f"missing source_id {src}"
    assert any(r.get("operation") == "fetch_daily_bar" for r in by_source["baostock"])
    assert any(
        "filing" in r.get("operation", "") or "announcement" in r.get("operation", "")
        for r in by_source["cninfo"]
    )
    assert any(r.get("operation") == "fetch_macro_series" for r in by_source["fred"])
    tdx = by_source["tdx_pytdx"]
    assert all(r.get("role") == "validation_only" for r in tdx)


def test_layer5_no_production_candidate() -> None:
    """覆盖范围：Layer5 禁止 production_candidate
    测试对象：layer5_instrument_source_plan.yaml 全部行
    目的/目标：Batch 01 不得将 L5 输入标 production_candidate
    验证点：无行 readiness=production_candidate
    失败含义：L5 证据链越权声称生产就绪
    """
    rows = _load_whitelist_rows("layer5")
    assert not any(r.get("readiness") == "production_candidate" for r in rows)


# --- WL-06 Matrix + hardening negative tests ---


def _all_whitelist_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in WHITELIST_FILES:
        rows.extend(_load_whitelist_rows(key))
    return rows


def test_all_whitelist_rows_have_required_fields() -> None:
    """覆盖范围：五层白名单全集行 schema
    测试对象：specs/model_inputs/*.yaml 全部 rows
    目的/目标：WL-06 验收 — 每行含任务卡 §6 必填字段
    验证点：五文件 rows 均通过 REQUIRED_ROW_FIELDS 检查
    失败含义：readiness matrix 下游无法信任机器可读白名单
    """
    for row in _all_whitelist_rows():
        missing = [f for f in REQUIRED_ROW_FIELDS if f not in row]
        assert not missing, f"{row.get('input_id')}: missing {missing}"


def test_forbidden_akshare_not_primary_candidate() -> None:
    """覆盖范围：hardening §5/§8 akshare 角色上限
    测试对象：全部白名单 akshare 行
    目的/目标：akshare 不得为 primary_candidate
    验证点：source_id=akshare 时 role≠primary_candidate
    失败含义：聚合源越权成为 Primary
    """
    ak_rows = [r for r in _all_whitelist_rows() if r.get("source_id") == "akshare"]
    assert ak_rows
    for row in ak_rows:
        assert row.get("role") != "primary_candidate", row.get("input_id")


def test_forbidden_tdx_not_production_candidate() -> None:
    """覆盖范围：hardening §5 tdx_pytdx 角色上限
    测试对象：全部白名单 tdx_pytdx 行
    目的/目标：tdx_pytdx 不得 readiness=production_candidate 或 production primary
    验证点：readiness≠production_candidate；role=validation_only
    失败含义：TDX 越权生产主源
    """
    tdx_rows = [r for r in _all_whitelist_rows() if r.get("source_id") == "tdx_pytdx"]
    assert tdx_rows
    for row in tdx_rows:
        assert row.get("readiness") != "production_candidate", row.get("input_id")
        assert row.get("role") == "validation_only", row.get("input_id")


def test_forbidden_fred_not_production_candidate() -> None:
    """覆盖范围：hardening §5/§8 fred 角色上限
    测试对象：全部白名单 fred 行
    目的/目标：FRED pilot 未闭合前不得 production_candidate
    验证点：source_id=fred 时 readiness≠production_candidate
    失败含义：FRED 越权声称 production-live
    """
    fred_rows = [r for r in _all_whitelist_rows() if r.get("source_id") == "fred"]
    assert fred_rows
    for row in fred_rows:
        assert row.get("readiness") != "production_candidate", row.get("input_id")
        assert row.get("requires_user_authorization") is True


def test_forbidden_macro_supplementary_not_fred_primary_closure() -> None:
    """覆盖范围：hardening §4 B2.5-O-05 macro_supplementary 不足闭合 FRED
    测试对象：macro_supplementary 域 + fred P0 序列行
    目的/目标：macro_supplementary 行不得声称闭合 FRED primary；P0 仅 fred sandbox
    验证点：macro 行 forbidden_claims 含 FRED primary substitute 或同类；P0 仅 fred
    失败含义：registry deferred 行被错误闭合
    """
    rows = _all_whitelist_rows()
    macro = [r for r in rows if r.get("data_domain") == "macro_supplementary"]
    assert macro
    for row in macro:
        claims = " ".join(str(c) for c in (row.get("forbidden_claims") or []))
        assert "FRED" in claims or "primary" in claims.lower()
        assert row.get("source_id") == "akshare"
    p0_fred = [
        r
        for r in rows
        if r.get("layer") == "layer1"
        and r.get("source_id") == "fred"
        and _series_value(r) in LAYER1_P0_SERIES
    ]
    assert len(p0_fred) == len(LAYER1_P0_SERIES)


def test_readiness_matrix_documents_layers() -> None:
    """覆盖范围：人类可读 readiness matrix
    测试对象：docs/quality/model_input_readiness_matrix.md
    目的/目标：矩阵说明 sandbox/staged/deferred 分区；非仅存在性
    验证点：含五层标题或 layer 标记；含 sandbox_candidate 与 deferred 语义
    失败含义：业务方无法读矩阵理解首批范围
    """
    path = PROJECT_ROOT / "docs" / "quality" / "model_input_readiness_matrix.md"
    assert path.is_file(), "model_input_readiness_matrix.md required"
    text = path.read_text(encoding="utf-8")
    for marker in ("Layer1", "Layer2", "Layer3", "Layer4", "Layer5"):
        assert marker in text, marker
    for term in ("sandbox_candidate", "deferred", "fixture_only", "validation_only"):
        assert term in text, term


def test_model_inputs_readme_indexes_whitelist_files() -> None:
    """覆盖范围：specs/model_inputs/README.md 索引
    测试对象：README 与五层 YAML 文件
    目的/目标：README 列出五文件并声明 Batch 01 边界
    验证点：README 含五 yaml 文件名；含 whitelist-driven 或 sandbox 表述
    失败含义：执行者找不到白名单 SSOT
    """
    readme = MODEL_INPUTS / "README.md"
    assert readme.is_file()
    text = readme.read_text(encoding="utf-8")
    for name in (
        "layer1_source_whitelist.yaml",
        "layer2_source_whitelist.yaml",
        "layer3_anchor_source_plan.yaml",
        "layer4_market_source_plan.yaml",
        "layer5_instrument_source_plan.yaml",
    ):
        assert name in text, name
    assert "sandbox" in text.lower() or "whitelist" in text.lower()
