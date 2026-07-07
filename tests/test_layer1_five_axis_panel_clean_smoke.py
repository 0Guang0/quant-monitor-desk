"""S06 — G12 五轴 Tier A clean panel 集成 smoke + K1 对齐 + ResourceGuard."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from tests.contract_gate_support import load_yaml

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.layer1_axes.clean_observation_reader import (
    P0_MACRO_DB_KEYS,
    P0_WINDOW_CAPS,
    amihud_observations_from_bars,
    read_bar_history,
    read_macro_clean_observations,
    resolve_window_cap,
)
from backend.app.layer1_axes.feature_engine import (
    AxisFeatureEngine,
    ResourceGuardBlockedError,
)
from backend.app.layer1_axes.interpretation import AxisInterpretationEngine
from tests.layer1_clean_e2e_support import (
    AS_OF,
    bootstrap_layer1_clean_db,
    seed_cot_lf_net_weekly,
    seed_macro_series,
    seed_spy_bars,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WHITELIST = PROJECT_ROOT / "specs" / "model_inputs" / "layer1_source_whitelist.yaml"

P0_BINDINGS: tuple[tuple[str, str, str], ...] = (
    ("ENV-E1-DGS10", "DGS10", "fred"),
    ("CRD.CS1.BAA10Y", "BAA10Y", "fred"),
    ("RA.R1.VIXCLS_30D_IMPLIED_VOL", "VIXCLS", "fred"),
    ("SEN-S1-COT_LF_NET", "088691", "cftc_cot"),
)


def _seed_all_axes(con) -> None:
    seed_macro_series(
        con, db_indicator_id="DGS10", n=40, start=date(2026, 1, 1), base_value=4.0
    )
    seed_macro_series(
        con,
        db_indicator_id="BAA10Y",
        n=40,
        start=date(2026, 1, 1),
        base_value=1.8,
        step=0.02,
    )
    seed_macro_series(
        con,
        db_indicator_id="VIXCLS",
        n=40,
        start=date(2026, 1, 1),
        base_value=18.0,
        step=0.1,
    )
    seed_cot_lf_net_weekly(con, n=80, start=date(2024, 6, 3))
    seed_spy_bars(con, n=60, start=date(2026, 1, 1))


def test_layer1FiveAxisPanel_cleanSmoke_allP0AxesProduceFeatures(tmp_path) -> None:
    """覆盖范围：五轴 P0 锚点在同一隔离库经 clean 读→特征→解读全绿
    测试对象：read_macro/bar clean 路径 + AxisFeatureEngine + AxisInterpretationEngine
    目的/目标：G12 §3.5.1 硬门禁 — 五轴非 staged_fixture 输入可同时产出可断言快照链
    验证点：4 macro + 1 bar 轴均 state_bucket!=insufficient_history；source 非 staged_fixture
    失败含义：任一轴 clean 链未接通，五轴 PASS 硬门禁不成立
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        _seed_all_axes(con)
        guard = ResourceGuard(con=con)
        macro_specs = [s for s, _, _ in P0_BINDINGS]
        for spec_id in macro_specs:
            obs = read_macro_clean_observations(con, spec_id, as_of_end=AS_OF)
            assert obs[-1].indicator_id == spec_id
            assert "staged_fixture" not in obs[-1].source_used
            freq = "weekly" if spec_id == "SEN-S1-COT_LF_NET" else "daily"
            min_obs = 20 if freq == "weekly" else 30
            engine = AxisFeatureEngine(
                resource_guard=guard,
                frequency=freq,
                min_obs_required=min_obs,
                window_len=60,
            )
            feat = engine.compute_features(
                as_of=AS_OF, observations=[obs[-1]], history=obs
            )[0]
            assert feat.state_bucket != "insufficient_history"
            interp = AxisInterpretationEngine().build_interpretation(
                as_of=AS_OF, features=[feat]
            )[0]
            assert interp.boundary_reminder == "不构成交易动作"

        bars = read_bar_history(con, "SPY")
        liq_obs = amihud_observations_from_bars(
            bars, spec_indicator_id="LIQ.B-I1.AMIHUD_ILLIQ", as_of=AS_OF
        )
        assert liq_obs[-1].source_used == "alpha_vantage"
        liq_feat = AxisFeatureEngine(
            resource_guard=guard, min_obs_required=20, window_len=60
        ).compute_features(
            as_of=AS_OF, observations=[liq_obs[-1]], history=liq_obs
        )[0]
        assert liq_feat.indicator_id == "LIQ.B-I1.AMIHUD_ILLIQ"
        assert liq_feat.state_bucket != "insufficient_history"
        liq_interp = AxisInterpretationEngine().build_interpretation(
            as_of=AS_OF, features=[liq_feat]
        )[0]
        assert liq_interp.boundary_reminder == "不构成交易动作"


def test_layer1FiveAxisPanel_resourceGuardHardStop_blocksFeatureCompute() -> None:
    """覆盖范围：五轴 smoke 路径上 ResourceGuard HARD_STOP 须 fail-closed
    测试对象：AxisFeatureEngine.compute_features
    目的/目标：A4 — eco profile 硬停止时五轴特征计算不得继续
    验证点：pytest.raises(ResourceGuardBlockedError)
    失败含义：资源门禁在五轴路径被绕过，可能拖垮沙箱/生产
    """
    guard = MagicMock()
    guard.check.return_value = (Decision.HARD_STOP, "panel smoke cap")
    engine = AxisFeatureEngine(
        resource_guard=guard, min_obs_required=5, window_len=10
    )
    from backend.app.layer1_axes.models import AxisObservation

    obs = AxisObservation(
        indicator_id="ENV-E1-DGS10",
        as_of_timestamp=AS_OF,
        publish_timestamp=AS_OF - timedelta(days=1),
        raw_value=4.0,
        source_used="fred",
    )
    with pytest.raises(ResourceGuardBlockedError, match="resource guard blocked"):
        engine.compute_features(as_of=AS_OF, observations=[obs], history=[obs])


def test_dcp06K1_whitelistAlignsP0CleanBindings() -> None:
    """覆盖范围：DCP-06 P0 clean 绑定与 K1 layer1_source_whitelist 行一致
    测试对象：layer1_source_whitelist.yaml + P0_MACRO_DB_KEYS
    目的/目标：K1 行 source_id/symbol 与 runtime clean 读绑定可对账
    验证点：DGS10/VIXCLS/BAA10Y/088691/SPY 各有匹配行；macro_supplementary 非 primary
    失败含义：白名单与 Tier A clean 读路径漂移，下游 fetch scope 无 SSOT
    """
    doc = load_yaml(WHITELIST)
    rows = doc.get("rows") or []
    by_series: dict[str, dict] = {}
    for row in rows:
        sym = row.get("symbol_or_series")
        key = str(sym[0] if isinstance(sym, list) else sym)
        by_series[key] = row

    for spec_id, db_key, source_id in P0_BINDINGS:
        assert P0_MACRO_DB_KEYS[spec_id] == db_key
        row = by_series.get(db_key)
        assert row is not None, f"missing whitelist row for {db_key}"
        assert row.get("source_id") == source_id
        assert row.get("role") != "validation_only" or source_id == "akshare"

    liq = by_series.get("SPY")
    assert liq is not None
    assert liq.get("source_id") == "alpha_vantage"
    assert liq.get("role") == "primary_candidate"

    macro_supp = [r for r in rows if r.get("data_domain") == "macro_supplementary"]
    assert macro_supp
    assert all(r.get("role") != "primary_candidate" for r in macro_supp)

    dcp06_series = {"DGS10", "BAA10Y", "VIXCLS", "SPY", "088691"}
    for series in dcp06_series:
        row = by_series.get(series)
        assert row is not None, f"missing DCP-06 row for {series}"
        assert row.get("readiness") == "clean_replay_proven", series
        assert row.get("row_cap") is not None and int(row["row_cap"]) > 0
        assert row.get("window_cap") is not None


def test_layer1FiveAxisPanel_resourceGuardHardStop_blocksPanelFeatureCompute(
    tmp_path, monkeypatch
) -> None:
    """覆盖范围：五轴 panel 路径上真 ResourceGuard HARD_STOP 须 fail-closed
    测试对象：AxisFeatureEngine(resource_guard=ResourceGuard(con=con)) in panel loop
    目的/目标：A4-P2-003 — panel 特征链接迁移库 guard，非孤立 check() 枚举断言
    验证点：monkeypatch guard.check→HARD_STOP；panel compute_features raises ResourceGuardBlockedError(resource guard blocked)
    失败含义：资源门禁在五轴 panel 路径被绕过
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        _seed_all_axes(con)
        guard = ResourceGuard(con=con)
        monkeypatch.setattr(
            guard,
            "check",
            lambda: (Decision.HARD_STOP, "panel smoke cap"),
        )
        obs = read_macro_clean_observations(con, "ENV-E1-DGS10", as_of_end=AS_OF)
        engine = AxisFeatureEngine(
            resource_guard=guard, min_obs_required=5, window_len=10
        )
        with pytest.raises(ResourceGuardBlockedError, match="resource guard blocked"):
            engine.compute_features(as_of=AS_OF, observations=[obs[-1]], history=obs)


def test_layer1FiveAxisPanel_resourceGuardOnMigratedDb(tmp_path) -> None:
    """覆盖范围：五轴 smoke 路径在迁移隔离库上真 ResourceGuard.check
    测试对象：ResourceGuard + bootstrap_layer1_clean_db + panel feature compute
    目的/目标：A4 — panel 路径使用 ResourceGuard(con=con) 且 OK 时可算特征
    验证点：decision==OK 时 compute_features 成功；非 OK 时 raises
    失败含义：五轴集成未接真 ResourceGuard，沙箱 cap 无法 fail-closed
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_macro_series(
            con, db_indicator_id="DGS10", n=40, start=date(2026, 1, 1), base_value=4.0
        )
        guard = ResourceGuard(con=con)
        decision, _reason = guard.check()
        obs = read_macro_clean_observations(con, "ENV-E1-DGS10", as_of_end=AS_OF)
        engine = AxisFeatureEngine(
            resource_guard=guard, min_obs_required=30, window_len=60
        )
        if decision == Decision.OK:
            feat = engine.compute_features(
                as_of=AS_OF, observations=[obs[-1]], history=obs
            )[0]
            assert feat.state_bucket != "insufficient_history"
        else:
            with pytest.raises(ResourceGuardBlockedError, match="resource guard blocked"):
                engine.compute_features(
                    as_of=AS_OF, observations=[obs[-1]], history=obs
                )


def test_layer1FiveAxisPanel_windowLenWithinWhitelistCap() -> None:
    """覆盖范围：五轴 P0 feature window_len 不超过 K1 window_cap 意图
    测试对象：P0_WINDOW_CAPS + panel smoke 默认 window_len=60
    目的/目标：A4 — 特征窗与 whitelist window_cap 对齐，防止无界滚动
    验证点：panel 用 window_len=60 ≤ 各轴 resolve_window_cap
    失败含义：特征引擎可超出白名单窗上限，违背 resource_limits 意图
    """
    panel_window_len = 60
    for spec_id in (
        "ENV-E1-DGS10",
        "CRD.CS1.BAA10Y",
        "RA.R1.VIXCLS_30D_IMPLIED_VOL",
        "SEN-S1-COT_LF_NET",
        "LIQ.B-I1.AMIHUD_ILLIQ",
    ):
        assert panel_window_len <= resolve_window_cap(spec_id)
        assert panel_window_len <= P0_WINDOW_CAPS[spec_id]
