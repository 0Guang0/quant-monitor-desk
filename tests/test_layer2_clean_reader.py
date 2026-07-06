"""S00 — Layer2CleanObservationReader contract tests (DCP-07)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from backend.app.layer1_axes.clean_observation_reader import resolve_read_limit as l1_resolve_read_limit
from backend.app.layer2_sensors.clean_observation_reader import (
    Layer2CleanObservationFallbackForbiddenError,
    Layer2CleanObservationReadError,
    Layer2CleanObservationReader,
    resolve_read_limit,
)
from backend.app.layer2_sensors.models import CrossAssetObservation, CrossAssetRegistryEntry
from backend.app.layer2_sensors.observation import CrossAssetObservationError, assert_observation_source
from backend.app.layer2_sensors.sensor_loader import (
    CLEAN_REPLAY_REGISTRY_FIXTURE,
    CrossAssetRegistryLoadError,
    CrossAssetRegistryLoader,
    STAGED_REGISTRY_FIXTURE,
)
from tests.layer1_clean_e2e_support import AS_OF, bootstrap_layer1_clean_db, seed_macro_series


def _vix_entry():
    loaded = CrossAssetRegistryLoader().load(registry_path=CLEAN_REPLAY_REGISTRY_FIXTURE)
    return next(a for a in loaded.assets if a.asset_id == "L2-VIX")


def test_layer2CleanReader_readsVixclsFromAxisObservation(tmp_path) -> None:
    """覆盖范围：L2-VIX P0 从 axis_observation(VIXCLS) 读入 CrossAssetObservation
    测试对象：Layer2CleanObservationReader.read_observations
    目的/目标：ADR-013 — registry FRED:VIXCLS 映射 clean 行；source=fred 非 staged_fixture
    验证点：len>=30；asset_id==L2-VIX；close 可断言；source==fred
    失败含义：Layer2 无法从 Tier A macro clean 读 P0 传感器
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    entry = _vix_entry()
    start = date(2026, 1, 1)
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id="VIXCLS",
            n=40,
            start=start,
            base_value=18.0,
            source_used="fred",
            step=0.15,
        )
        obs = Layer2CleanObservationReader().read_observations(
            con, entry, as_of_end=AS_OF
        )
    assert len(obs) >= 30
    assert all(o.asset_id == "L2-VIX" for o in obs)
    assert all(o.source == "fred" for o in obs)
    assert "staged_fixture" not in obs[-1].source
    assert obs[-1].close is not None and obs[-1].close > 0


def test_layer2CleanReader_emptyMacro_failClosedNoFallback(tmp_path) -> None:
    """覆盖范围：clean 表无 VIXCLS 行时禁止 silent 换源
    测试对象：Layer2CleanObservationReader.read_observations
    目的/目标：EasyXT forbidden 对齐 — 空结果须 Layer2CleanObservationReadError
    验证点：pytest.raises(Layer2CleanObservationReadError)
    失败含义：空库仍“成功”会掩盖 Tier A 未写入或悄悄 fallback
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    entry = _vix_entry()
    with cm.writer() as con:
        with pytest.raises(Layer2CleanObservationReadError):
            Layer2CleanObservationReader().read_observations(con, entry)


def test_layer2CleanReader_rejectsStagedFixtureSourceUsed(tmp_path) -> None:
    """覆盖范围：axis_observation 行若标 staged_fixture 须拒绝
    测试对象：Layer2CleanObservationReader.read_observations
    目的/目标：非 Tier A clean 来源行不得进入 Layer2 clean 读路径
    验证点：pytest.raises(Layer2CleanObservationFallbackForbiddenError)
    失败含义：staged 行混入 clean replay PASS 路径
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    entry = _vix_entry()
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id="VIXCLS",
            n=5,
            start=date(2026, 2, 1),
            base_value=20.0,
            source_used="staged_fixture",
        )
        with pytest.raises(Layer2CleanObservationFallbackForbiddenError):
            Layer2CleanObservationReader().read_observations(con, entry)


def test_layer2CleanReader_respectsRowCap(tmp_path) -> None:
    """覆盖范围：VIXCLS clean 读默认 limit 受 P0 row_cap 约束
    测试对象：Layer2CleanObservationReader + resolve_read_limit
    目的/目标：种子行数超过 cap 时 reader 返回 ≤120 行（对齐 Layer1 VIXCLS cap）
    验证点：seed 200 行；读 L2-VIX len≤120
    失败含义：clean 读可无界拉取，违背 resource cap 纪律
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    entry = _vix_entry()
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id="VIXCLS",
            n=200,
            start=date(2024, 1, 1),
            base_value=15.0,
            source_used="fred",
        )
        obs = Layer2CleanObservationReader().read_observations(
            con, entry, as_of_end=AS_OF
        )
    cap = resolve_read_limit("L2-VIX")
    assert cap == 120
    assert len(obs) <= cap


def test_layer2CleanReplayRegistry_loadsP0VixPrimaryFred() -> None:
    """覆盖范围：production_clean_replay 模式加载 P0 L2-VIX
    测试对象：CrossAssetRegistryLoader.load（CLEAN_REPLAY_REGISTRY_FIXTURE）
    目的/目标：S00 registry mode 扩展仅白名单 P0 可 primary_source=fred
    验证点：mode==production_clean_replay；L2-VIX primary_source==fred
    失败含义：clean replay 注册表无法加载，e2e 无法证明非 fixture 路径
    """
    loaded = CrossAssetRegistryLoader().load(registry_path=CLEAN_REPLAY_REGISTRY_FIXTURE)
    assert loaded.mode == "production_clean_replay"
    vix = next(a for a in loaded.assets if a.asset_id == "L2-VIX")
    assert vix.primary_source == "fred"
    assert vix.instrument_id == "FRED:VIXCLS"


def test_layer2CleanReader_rejectsSourceSwitched(tmp_path) -> None:
    """覆盖范围：source_switched=True 的 clean 行须 fail-closed
    测试对象：Layer2CleanObservationReader.read_observations
    目的/目标：A3/A4 — silent_fallback 信号不得进入 Layer2 P0 clean 读
    验证点：fred 行但 source_switched=True → pytest.raises(Layer2CleanObservationFallbackForbiddenError)
    失败含义：换源行仍可读，违背 EasyXT forbidden 对齐
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    entry = _vix_entry()
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id="VIXCLS",
            n=5,
            start=date(2026, 2, 1),
            base_value=20.0,
            source_used="fred",
        )
        con.execute(
            "UPDATE axis_observation SET source_switched = TRUE WHERE indicator_id = ?",
            ["VIXCLS"],
        )
        with pytest.raises(Layer2CleanObservationFallbackForbiddenError):
            Layer2CleanObservationReader().read_observations(con, entry)


def test_layer2CleanReader_rejectsMacroSupplementaryPrefix(tmp_path) -> None:
    """覆盖范围：macro_supplementary 前缀 source_used 须拒绝
    测试对象：Layer2CleanObservationReader.read_observations
    目的/目标：A3/A4 — FORBIDDEN_FALLBACK_SOURCE_PREFIXES 含 macro_supplementary
    验证点：source_used=macro_supplementary:akshare → pytest.raises
    失败含义：validation-only 源前缀可渗入 P0 clean 读
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    entry = _vix_entry()
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id="VIXCLS",
            n=5,
            start=date(2026, 2, 1),
            base_value=20.0,
            source_used="macro_supplementary:akshare",
        )
        with pytest.raises(Layer2CleanObservationFallbackForbiddenError):
            Layer2CleanObservationReader().read_observations(con, entry)


def test_layer2CleanReader_rejectsNonFredSourceUsed(tmp_path) -> None:
    """覆盖范围：P0 路径非 fred source_used 须拒绝
    测试对象：Layer2CleanObservationReader.read_observations
    目的/目标：A4 — _assert_clean_source_used 要求 source_used==fred
    验证点：source_used=akshare → pytest.raises(Layer2CleanObservationFallbackForbiddenError)
    失败含义：非 Tier A 源可混入 L2-VIX clean replay
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    entry = _vix_entry()
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id="VIXCLS",
            n=5,
            start=date(2026, 2, 1),
            base_value=20.0,
            source_used="akshare",
        )
        with pytest.raises(Layer2CleanObservationFallbackForbiddenError):
            Layer2CleanObservationReader().read_observations(con, entry)


def test_layer2CleanReader_respectsAsOfEndFilter(tmp_path) -> None:
    """覆盖范围：as_of_end 时间窗过滤 publish_timestamp
    测试对象：Layer2CleanObservationReader.read_observations
    目的/目标：A4 — 未来 publish 行不得进入读结果
    验证点：种子 40 行 + 1 行 publish>AS_OF；读结果 len==40 且末行 close 非未来值
    失败含义：as_of_end 过滤失效，特征链可偷看未来数据
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    entry = _vix_entry()
    start = date(2026, 1, 1)
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id="VIXCLS",
            n=40,
            start=start,
            base_value=18.0,
            source_used="fred",
        )
        future_pub = AS_OF + timedelta(days=1)
        con.execute(
            """
            INSERT INTO axis_observation (
                observation_id, indicator_id, as_of_timestamp, publish_timestamp,
                raw_value, content_hash, source_used, source_switched, quality_flags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, FALSE, NULL)
            """,
            [
                "VIXCLS-future",
                "VIXCLS",
                future_pub,
                future_pub,
                99.99,
                "hash-future",
                "fred",
            ],
        )
        obs = Layer2CleanObservationReader().read_observations(
            con, entry, as_of_end=AS_OF
        )
    assert len(obs) == 40
    assert all(o.as_of_timestamp <= AS_OF for o in obs)
    assert obs[-1].close != 99.99


def test_layer2CleanReader_rowCapMatchesLayer1Vixcls(tmp_path) -> None:
    """覆盖范围：L2-VIX row_cap 与 Layer1 VIXCLS cap 程序化对账
    测试对象：resolve_read_limit（L2）vs Layer1 VIXCLS
    目的/目标：A4 — P0_ROW_CAPS 不得与 Layer1 RA.R1.VIXCLS_30D_IMPLIED_VOL 漂移
    验证点：resolve_read_limit('L2-VIX') == l1_resolve_read_limit('RA.R1.VIXCLS_30D_IMPLIED_VOL')
    失败含义：跨层 cap 不一致可导致读窗口不对称
    """
    assert resolve_read_limit("L2-VIX") == l1_resolve_read_limit(
        "RA.R1.VIXCLS_30D_IMPLIED_VOL"
    )


def test_layer2CleanReplayRegistry_rejectsNonP0FredPrimary(tmp_path) -> None:
    """覆盖范围：production_clean_replay 下非 L2-VIX 资产不得 primary_source=fred
    测试对象：CrossAssetRegistryLoader.load
    目的/目标：A4/A8 — plan-doubt Q3 P0 白名单负向可执行 AC
    验证点：tmp yaml mode=production_clean_replay + L2-COPPER fred → CrossAssetRegistryLoadError
    失败含义：非 P0 资产可绑 fred primary，clean replay 白名单失效
    """
    bad = tmp_path / "bad_clean_replay.yaml"
    bad.write_text(
        "version: v1\nmode: production_clean_replay\nassets:\n"
        "  - asset_id: L2-COPPER\n    display_name_cn: 铜\n    asset_group: Metals\n"
        "    asset_type: futures\n    market: COMEX\n    instrument_id: COMEX:HG\n"
        "    primary_source: fred\n    validation_source: none\n    fallback_policy: none\n"
        "    is_axis_input: false\n    display_only: false\n"
        "    eligible_for_model: true\n    double_count_guard: none\n",
        encoding="utf-8",
    )
    with pytest.raises(CrossAssetRegistryLoadError, match="P0-whitelist"):
        CrossAssetRegistryLoader().load(registry_path=bad)


def test_layer2CleanReader_rejectsNonWhitelistAsset(tmp_path) -> None:
    """覆盖范围：reader 对非 P0 白名单 asset_id 须拒绝
    测试对象：Layer2CleanObservationReader.read_observations
    目的/目标：A8 — asset_id ∉ P0_CLEAN_REPLAY_ASSET_IDS 抛 KeyError
    验证点：L2-COPPER registry entry → pytest.raises(KeyError, match=whitelist)
    失败含义：非 P0 资产可走 clean reader，竖切边界破裂
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    staged = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in staged.assets if a.asset_id == "L2-COPPER")
    with cm.writer() as con:
        with pytest.raises(KeyError, match="whitelist"):
            Layer2CleanObservationReader().read_observations(con, copper)


def test_layer2AssertObservationSource_rejectsStagedForFredPrimary() -> None:
    """覆盖范围：snapshot 路径 assert_observation_source fred 绑定
    测试对象：assert_observation_source
    目的/目标：A4 — primary_source=fred 时 staged_fixture 观测须 CrossAssetObservationError
    验证点：fred entry + staged_fixture obs → pytest.raises
    失败含义：builder 入口未阻断 staged 混入 clean replay
    """
    entry = CrossAssetRegistryEntry(
        asset_id="L2-VIX",
        display_name="VIX",
        display_name_cn="VIX",
        asset_group="Volatility",
        asset_type="index",
        market="US",
        instrument_id="FRED:VIXCLS",
        layer5_instrument_id="",
        primary_source="fred",
        validation_source="none",
        fallback_policy="none",
        mapped_axis="",
        is_axis_input=True,
        display_only=True,
        eligible_for_model=False,
        double_count_guard="layer1_axis_input_display_only",
        contract_code="",
        roll_rule="",
    )
    obs = CrossAssetObservation(
        asset_id="L2-VIX",
        trade_time=AS_OF,
        market="US",
        asset_type="index",
        open=20.0,
        high=20.0,
        low=20.0,
        close=20.0,
        pre_close=None,
        volume=None,
        amount=None,
        open_interest=None,
        source="staged_fixture",
        as_of_timestamp=AS_OF,
        fetch_time=AS_OF,
    )
    with pytest.raises(CrossAssetObservationError):
        assert_observation_source(entry, obs)

