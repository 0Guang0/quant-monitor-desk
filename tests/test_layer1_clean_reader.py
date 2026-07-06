"""S00 — Layer1CleanObservationReader contract tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from backend.app.layer1_axes.clean_observation_reader import (
    CleanObservationFallbackForbiddenError,
    CleanObservationReadError,
    amihud_observations_from_bars,
    read_bar_history,
    read_macro_clean_observations,
    resolve_bar_read_limit,
    resolve_read_limit,
    resolve_window_cap,
)
from tests.contract_gate_support import load_yaml
from tests.layer1_clean_e2e_support import (
    AS_OF,
    bootstrap_layer1_clean_db,
    seed_macro_series,
    seed_spy_bars,
)

PROJECT_ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
WHITELIST = PROJECT_ROOT / "specs" / "model_inputs" / "layer1_source_whitelist.yaml"


def test_layer1CleanReader_macro_readsSpecIndicatorFromCleanTable(tmp_path) -> None:
    """覆盖范围：macro P0 从 axis_observation 读入并还原 spec indicator_id
    测试对象：read_macro_clean_observations
    目的/目标：DGS10 行映射为 ENV-E1-DGS10；source_used 为 tier A clean（fred）
    验证点：len>=30；indicator_id==ENV-E1-DGS10；source_used==fred；非 staged_fixture
    失败含义：clean 读路径未接通或错误回退到 fixture 语义
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    start = date(2026, 1, 1)
    with cm.writer() as con:
        seed_macro_series(con, db_indicator_id="DGS10", n=40, start=start, base_value=4.0)
        obs = read_macro_clean_observations(con, "ENV-E1-DGS10", as_of_end=AS_OF)
    assert len(obs) >= 30
    assert all(o.indicator_id == "ENV-E1-DGS10" for o in obs)
    assert obs[-1].source_used == "fred"
    assert "staged_fixture" not in obs[-1].source_used


def test_layer1CleanReader_emptyMacro_failClosedNoFallback(tmp_path) -> None:
    """覆盖范围：clean 表无行时禁止 silent 换源（EasyXT forbidden 对齐）
    测试对象：read_macro_clean_observations
    目的/目标：空结果须 CleanObservationReadError，不得返回空列表冒充成功
    验证点：pytest.raises(CleanObservationReadError)
    失败含义：空库仍“成功”会掩盖 Tier A 未写入或悄悄 fallback
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        with pytest.raises(CleanObservationReadError):
            read_macro_clean_observations(con, "ENV-E1-DGS10")


def test_layer1CleanReader_rejectsStagedFixtureSourceUsed(tmp_path) -> None:
    """覆盖范围：axis_observation 行若标 staged_fixture 须拒绝
    测试对象：read_macro_clean_observations
    目的/目标：非 clean 来源行不得进入 Layer1 clean 读路径
    验证点：pytest.raises(CleanObservationFallbackForbiddenError)
    失败含义：staged 行混入 PASS 路径
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id="DGS10",
            n=5,
            start=date(2026, 2, 1),
            base_value=3.0,
            source_used="staged_fixture",
        )
        with pytest.raises(CleanObservationFallbackForbiddenError):
            read_macro_clean_observations(con, "ENV-E1-DGS10")


def test_layer1CleanReader_amihudFromSpyBars(tmp_path) -> None:
    """覆盖范围：流动性 P0 从 security_bar_1d 推导 Amihud 序列
    测试对象：read_bar_history + amihud_observations_from_bars
    目的/目标：ADR-010 ponytail bar 路径可产出 LIQ.B-I1.AMIHUD_ILLIQ 观测
    验证点：len>=25；indicator_id 正确；raw_value>0
    失败含义：流动性轴无法从 Tier A bar clean 读入
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_spy_bars(con, n=60, start=date(2026, 1, 1))
        bars = read_bar_history(con, "SPY")
        obs = amihud_observations_from_bars(
            bars, spec_indicator_id="LIQ.B-I1.AMIHUD_ILLIQ", as_of=AS_OF
        )
    assert len(obs) >= 25
    assert obs[-1].indicator_id == "LIQ.B-I1.AMIHUD_ILLIQ"
    assert obs[-1].raw_value is not None and obs[-1].raw_value > 0


def test_layer1CleanReader_macroRespectsWhitelistRowCap(tmp_path) -> None:
    """覆盖范围：macro clean 读默认 limit 受 K1 row_cap 约束
    测试对象：read_macro_clean_observations + resolve_read_limit
    目的/目标：A4 — 种子行数超过 cap 时 reader 返回 ≤ whitelist row_cap
    验证点：seed 600 行；读 ENV-E1-DGS10 len≤500；显式 limit=999 仍≤500
    失败含义：clean 读可无界拉取，违背 resource_limits / whitelist cap
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    start = date(2024, 1, 1)
    with cm.writer() as con:
        seed_macro_series(con, db_indicator_id="DGS10", n=600, start=start, base_value=4.0)
        default_obs = read_macro_clean_observations(con, "ENV-E1-DGS10", as_of_end=AS_OF)
        explicit_obs = read_macro_clean_observations(
            con, "ENV-E1-DGS10", as_of_end=AS_OF, limit=999
        )
    cap = resolve_read_limit("ENV-E1-DGS10")
    assert cap == 500
    assert len(default_obs) <= cap
    assert len(explicit_obs) <= cap


def test_layer1CleanReader_barHistoryRespectsWhitelistRowCap(tmp_path) -> None:
    """覆盖范围：bar clean 读 limit 受 K1 SPY row_cap 约束
    测试对象：read_bar_history + resolve_bar_read_limit
    目的/目标：A4 — 流动性 ponytail bar 历史不超过 whitelist row_cap
    验证点：seed 400 bars；读 SPY len≤300
    失败含义：Amihud 输入可无界膨胀，违背 A4 cap 证明
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_spy_bars(con, n=400, start=date(2024, 1, 1))
        bars = read_bar_history(con, "SPY")
    cap = resolve_bar_read_limit("SPY")
    assert cap == 300
    assert len(bars) <= cap


def test_layer1CleanReader_rejectsAkshareSourceUsed(tmp_path) -> None:
    """覆盖范围：macro P0 行若标 akshare 等非 Tier A 源须拒绝
    测试对象：read_macro_clean_observations
    目的/目标：A3-P1 — P0 正源 allowlist 拒 akshare；不得 silent 接受 macro_supplementary 语义
    验证点：seed DGS10 + source_used=akshare → pytest.raises(CleanObservationFallbackForbiddenError)
    失败含义：非 Tier A 源混入 clean 读路径，违背 ADR-010 trust boundary
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id="DGS10",
            n=5,
            start=date(2026, 2, 1),
            base_value=3.0,
            source_used="akshare",
        )
        with pytest.raises(CleanObservationFallbackForbiddenError):
            read_macro_clean_observations(con, "ENV-E1-DGS10")


def test_layer1CleanReader_rejectsSourceSwitchedRow(tmp_path) -> None:
    """覆盖范围：source_switched=True 的 clean 行须 fail-closed
    测试对象：read_macro_clean_observations
    目的/目标：A3-P2 — silent_fallback 信号不得进入 Layer1 clean 读
    验证点：fred 行但 source_switched=True → pytest.raises(CleanObservationFallbackForbiddenError)
    失败含义：换源行仍可读，违背 EasyXT forbidden 对齐
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_macro_series(
            con, db_indicator_id="DGS10", n=5, start=date(2026, 2, 1), base_value=3.0
        )
        con.execute(
            "UPDATE axis_observation SET source_switched = TRUE WHERE indicator_id = ?",
            ["DGS10"],
        )
        with pytest.raises(CleanObservationFallbackForbiddenError):
            read_macro_clean_observations(con, "ENV-E1-DGS10")


def test_layer1CleanReader_emptyBar_failClosedNoFallback(tmp_path) -> None:
    """覆盖范围：bar clean 表无行时禁止 silent 换源
    测试对象：read_bar_history
    目的/目标：A8-P2-001 — 空 security_bar_1d 须 CleanObservationReadError
    验证点：bootstrap 后不 seed bar → pytest.raises(CleanObservationReadError)
    失败含义：空 bar 库仍“成功”会掩盖 Tier A 未写入
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        with pytest.raises(CleanObservationReadError):
            read_bar_history(con, "SPY")


def test_layer1CleanReader_rejectsStagedFixtureBarSource(tmp_path) -> None:
    """覆盖范围：security_bar_1d 行若标 staged_fixture 须拒绝
    测试对象：read_bar_history
    目的/目标：A3-P3-002 / A8-P2-002 — bar 路径对称 forbidden guard
    验证点：seed_spy_bars(source_used=staged_fixture) → pytest.raises
    失败含义：staged bar 混入流动性 Amihud 输入链
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_spy_bars(
            con, n=10, start=date(2026, 1, 1), source_used="staged_fixture"
        )
        with pytest.raises(CleanObservationFallbackForbiddenError):
            read_bar_history(con, "SPY")


def test_layer1CleanReader_rejectsMacroSupplementaryPrefix(tmp_path) -> None:
    """覆盖范围：macro_supplementary 前缀 source_used 须拒绝
    测试对象：read_macro_clean_observations
    目的/目标：A4-P3-004 — FORBIDDEN_FALLBACK_SOURCE_PREFIXES 含 macro_supplementary
    验证点：source_used=macro_supplementary:akshare → pytest.raises
    失败含义：validation-only 源前缀可渗入 P0 clean 读
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id="DGS10",
            n=5,
            start=date(2026, 2, 1),
            base_value=3.0,
            source_used="macro_supplementary:akshare",
        )
        with pytest.raises(CleanObservationFallbackForbiddenError):
            read_macro_clean_observations(con, "ENV-E1-DGS10")


def test_layer1CleanReader_macroRespectsAsOfEndFilter(tmp_path) -> None:
    """覆盖范围：as_of_end 时间窗过滤 publish_timestamp
    测试对象：read_macro_clean_observations
    目的/目标：A4-P3-003 — 未来 publish 行不得进入读结果
    验证点：种子 40 行 + 1 行 publish>AS_OF；读结果末行 publish≤AS_OF 且 len<41
    失败含义：as_of_end 过滤失效，特征链可偷看未来数据
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    start = date(2026, 1, 1)
    with cm.writer() as con:
        seed_macro_series(con, db_indicator_id="DGS10", n=40, start=start, base_value=4.0)
        future_pub = AS_OF + timedelta(days=1)
        con.execute(
            """
            INSERT INTO axis_observation (
                observation_id, indicator_id, as_of_timestamp, publish_timestamp,
                raw_value, content_hash, source_used, source_switched, quality_flags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, FALSE, NULL)
            """,
            [
                "DGS10-future",
                "DGS10",
                future_pub,
                future_pub,
                9.99,
                "hash-future",
                "fred",
            ],
        )
        obs = read_macro_clean_observations(con, "ENV-E1-DGS10", as_of_end=AS_OF)
    assert len(obs) == 40
    assert all(o.publish_timestamp <= AS_OF for o in obs)
    assert obs[-1].raw_value != 9.99


def test_layer1CleanReader_amihudRejectsStagedFixtureBarDict() -> None:
    """覆盖范围：Amihud 构造路径须复用 forbidden guard
    测试对象：amihud_observations_from_bars
    目的/目标：A3-P3-001 — 绕过 read_bar_history 传入 staged_fixture bar 须拒绝
    验证点：bar dict source_used=staged_fixture → pytest.raises
    失败含义：Amihud 路径可渗入非 Tier A bar 语义
    """
    bars = [
        {
            "trade_date": "2026-01-02",
            "open": 400.0,
            "high": 401.0,
            "low": 399.0,
            "close": 400.5,
            "volume": 1_000_000.0,
            "source_used": "staged_fixture",
        },
        {
            "trade_date": "2026-01-03",
            "open": 400.5,
            "high": 402.0,
            "low": 400.0,
            "close": 401.0,
            "volume": 1_000_000.0,
            "source_used": "staged_fixture",
        },
    ]
    with pytest.raises(CleanObservationFallbackForbiddenError):
        amihud_observations_from_bars(
            bars, spec_indicator_id="LIQ.B-I1.AMIHUD_ILLIQ", as_of=AS_OF
        )


def test_layer1CleanReader_amihudEmptyBars_failClosed(tmp_path) -> None:
    """覆盖范围：全无效 bar 序列 Amihud 推导须 fail-closed
    测试对象：amihud_observations_from_bars
    目的/目标：A8-P3-001 — volume≤0 过滤后无观测须 CleanObservationReadError
    验证点：单 bar volume=0 → pytest.raises(CleanObservationReadError)
    失败含义：无效 bar 序列返回空列表冒充成功
    """
    bars = [
        {
            "trade_date": "2026-01-02",
            "open": 400.0,
            "high": 401.0,
            "low": 399.0,
            "close": 400.5,
            "volume": 0.0,
            "source_used": "alpha_vantage",
        }
    ]
    with pytest.raises(CleanObservationReadError):
        amihud_observations_from_bars(
            bars, spec_indicator_id="LIQ.B-I1.AMIHUD_ILLIQ", as_of=AS_OF
        )


def _parse_yaml_cap(value: object) -> int:
    if isinstance(value, int):
        return value
    return int(str(value).rstrip("dw"))


def test_dcp06Reader_capsMatchK1WhitelistYaml() -> None:
    """覆盖范围：reader cap 常量与 K1 whitelist YAML 程序化对账
    测试对象：resolve_read_limit + resolve_window_cap vs layer1_source_whitelist.yaml
    目的/目标：A4-P2-001 — 五 P0 spec row_cap/window_cap 与运行时 cap 逐项相等
    验证点：DGS10/BAA10Y/VIXCLS/088691/SPY 各 resolve_* == YAML 解析值
    失败含义：手写 cap 与 K1 漂移，resource_limits 假绿
    """
    doc = load_yaml(WHITELIST)
    by_series: dict[str, dict] = {}
    for row in doc.get("rows") or []:
        sym = row.get("symbol_or_series")
        key = str(sym[0] if isinstance(sym, list) else sym)
        by_series[key] = row

    spec_to_series = {
        "ENV-E1-DGS10": "DGS10",
        "CRD.CS1.BAA10Y": "BAA10Y",
        "RA.R1.VIXCLS_30D_IMPLIED_VOL": "VIXCLS",
        "SEN-S1-COT_LF_NET": "088691",
        "LIQ.B-I1.AMIHUD_ILLIQ": "SPY",
    }
    for spec_id, series in spec_to_series.items():
        row = by_series[series]
        assert resolve_read_limit(spec_id) == int(row["row_cap"]), spec_id
        assert resolve_window_cap(spec_id) == _parse_yaml_cap(row["window_cap"]), spec_id
