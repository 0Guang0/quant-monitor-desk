"""第二层跨资产传感器加载、双计_guard、血缘与 staged 快照测试。

覆盖范围：CrossAsset 注册表、日快照构建、期货换月、ResourceGuard
与 WriteManager 持久化路径。
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.layer2_sensors import (
    CrossAssetObservation,
    CrossAssetRegistryLoader,
    CrossAssetRegistryWriter,
    CrossAssetSnapshotBuilder,
    DoubleCountGuardError,
    FuturesRollHandler,
    Layer2LineageBuilder,
    Layer2ObservationWriter,
    Layer2RollEventWriter,
    Layer2SnapshotWriter,
    ResourceGuardBlockedError,
    assert_model_eligible,
)
from backend.app.layer2_sensors.futures_roll import ContractLiquidity
from backend.app.layer2_sensors.lineage import LINEAGE_REQUIRED_FIELDS
from backend.app.layer2_sensors.observation import reject_future_observation
from backend.app.layer2_sensors.schema_ddl import ensure_layer2_staging_tables
from backend.app.layer2_sensors.sensor_loader import STAGED_REGISTRY_FIXTURE

AS_OF = datetime(2026, 6, 15, 16, 0, tzinfo=UTC)
TRADE_DATE = date(2026, 6, 14)
TRADE_DT = datetime(2026, 6, 14, 16, 0, tzinfo=UTC)


@lru_cache(maxsize=1)
def _staged_registry():
    return CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)


def _staged_asset(asset_id: str, *, registry=None):
    reg = registry if registry is not None else _staged_registry()
    return next(a for a in reg.assets if a.asset_id == asset_id)


def _layer2_cm(tmp_path: Path, name: str) -> ConnectionManager:
    cm = ConnectionManager(tmp_path / name)
    with cm.writer() as con:
        apply_migrations(con)
        ensure_layer2_staging_tables(con)
    return cm


def _obs(
    asset_id: str,
    *,
    trade_time: datetime | None = None,
    close: float = 100.0,
    as_of_visibility: datetime | None = None,
    fetch_time: datetime | None = None,
    source: str = "staged_fixture",
) -> CrossAssetObservation:
    tt = trade_time or TRADE_DT
    vis = as_of_visibility or tt
    ft = fetch_time or vis
    return CrossAssetObservation(
        asset_id=asset_id,
        trade_time=tt,
        market="US",
        asset_type="index",
        open=close - 1,
        high=close + 1,
        low=close - 2,
        close=close,
        pre_close=close - 0.5,
        volume=1_000_000.0,
        amount=None,
        open_interest=None,
        source=source,
        as_of_timestamp=vis,
        fetch_time=ft,
    )


def _insert_validation_report(cm: ConnectionManager, report_id: str) -> None:
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO validation_report (
                validation_report_id, run_id, data_domain, source_id,
                status, checked_rows, failed_rows, warning_rows,
                can_write_clean, needs_manual_review,
                rule_set_id, rule_version,
                source_fetch_ids_json, source_content_hashes_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                report_id,
                "run-layer2",
                "layer2_cross_asset_daily",
                "staged_fixture",
                "PASSED",
                1,
                0,
                0,
                True,
                False,
                "layer2_v1",
                "layer2_sensor_staged_v1",
                json.dumps(["fetch-l2-wm"]),
                json.dumps(["hash-l2-wm"]),
            ],
        )


def test_crossAssetRegistryLoader_stagedFixture_loadsAxisInputAssets() -> None:
    """覆盖范围：staged 资产注册表加载与轴输入标记
    测试对象：CrossAssetRegistryLoader.load（STAGED_REGISTRY_FIXTURE）
    目的/目标：staged_fixture_only 模式下正确解析 VIX 等轴输入仅展示资产
    验证点：mode=staged_fixture_only；L2-VIX is_axis_input/display_only/eligible 与 double_count_guard
    失败含义：注册表误标可入模资产，Layer1 轴输入双计_guard 失效
    """
    result = _staged_registry()
    assert result.mode == "staged_fixture_only"
    vix = _staged_asset("L2-VIX")
    assert vix.is_axis_input is True
    assert vix.display_only is True
    assert vix.eligible_for_model is False
    assert vix.double_count_guard == "layer1_axis_input_display_only"


def test_crossAssetRegistryLoader_rejectsNonStagedMode(tmp_path: Path) -> None:
    """覆盖范围：非 staged 模式注册表拒收
    测试对象：CrossAssetRegistryLoader.load（production_live YAML）
    目的/目标：Layer2 当前仅允许 staged_fixture_only，防误用线上配置
    验证点：pytest.raises(Exception, match=staged_fixture_only)
    失败含义：production_live 注册表仍可加载，Batch3 双闸失效
    """
    bad = tmp_path / "bad_registry.yaml"
    bad.write_text(
        "version: v1\nmode: production_live\nassets:\n"
        "  - asset_id: X\n    display_name_cn: x\n    asset_group: USD\n"
        "    asset_type: index\n    market: US\n    primary_source: staged_fixture\n"
        "    validation_source: none\n    fallback_policy: none\n"
        "    is_axis_input: false\n    display_only: false\n"
        "    eligible_for_model: true\n    double_count_guard: none\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="staged_fixture_only"):
        CrossAssetRegistryLoader().load(registry_path=bad)


def test_crossAssetRegistryLoader_rejectsPrimarySourceNone(tmp_path: Path) -> None:
    """覆盖范围：primary_source=none 非法配置
    测试对象：CrossAssetRegistryLoader.load
    目的/目标：每个资产必须声明可接受的主数据源，none 不可作为 primary
    验证点：pytest.raises(Exception, match=primary_source)
    失败含义：无来源资产进入流水线，血缘无法追溯
    """
    bad = tmp_path / "bad_none_primary.yaml"
    bad.write_text(
        "version: v1\nmode: staged_fixture_only\nassets:\n"
        "  - asset_id: X\n    display_name_cn: x\n    asset_group: USD\n"
        "    asset_type: index\n    market: US\n    primary_source: none\n"
        "    validation_source: none\n    fallback_policy: none\n"
        "    is_axis_input: false\n    display_only: false\n"
        "    eligible_for_model: false\n    double_count_guard: none\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="primary_source"):
        CrossAssetRegistryLoader().load(registry_path=bad)


def test_crossAssetRegistryLoader_rejectsDuplicateInstrumentId(tmp_path: Path) -> None:
    """覆盖范围：instrument_id 全局唯一性
    测试对象：CrossAssetRegistryLoader.load（重复 FUT:DUP）
    目的/目标：跨资产不得共享同一 instrument_id，防映射冲突
    验证点：pytest.raises(Exception, match=duplicate instrument_id)
    失败含义：重复 instrument 可共存，Layer5 对齐与 roll 逻辑错乱
    """
    bad = tmp_path / "dup_instrument.yaml"
    bad.write_text(
        "version: v1\nmode: staged_fixture_only\nassets:\n"
        "  - asset_id: A\n    display_name_cn: a\n    asset_group: Metals\n"
        "    asset_type: futures\n    market: US\n    instrument_id: FUT:DUP\n"
        "    layer5_instrument_id: L5-A\n    primary_source: staged_fixture\n"
        "    validation_source: none\n    fallback_policy: none\n"
        "    is_axis_input: false\n    display_only: false\n"
        "    eligible_for_model: true\n    double_count_guard: none\n"
        "  - asset_id: B\n    display_name_cn: b\n    asset_group: Metals\n"
        "    asset_type: futures\n    market: US\n    instrument_id: FUT:DUP\n"
        "    layer5_instrument_id: L5-B\n    primary_source: staged_fixture\n"
        "    validation_source: none\n    fallback_policy: none\n"
        "    is_axis_input: false\n    display_only: false\n"
        "    eligible_for_model: true\n    double_count_guard: none\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="duplicate instrument_id"):
        CrossAssetRegistryLoader().load(registry_path=bad)


def test_doubleCountGuard_axisInputCannotEnterModelAggregation() -> None:
    """覆盖范围：轴输入资产不得入模聚合
    测试对象：assert_model_eligible（L2-VIX）
    目的/目标：Layer1 轴输入仅展示，进入模型聚合须抛 DoubleCountGuardError
    验证点：pytest.raises(DoubleCountGuardError, match=display/reference only)
    失败含义：VIX 等展示指标进入模型，与 Layer1 双计策略冲突
    """
    result = _staged_registry()
    vix = _staged_asset("L2-VIX")
    with pytest.raises(DoubleCountGuardError, match="display/reference only"):
        assert_model_eligible(vix)


def test_snapshotBuilder_forModel_blocksAxisInput() -> None:
    """覆盖范围：for_model 构建时拦截轴输入
    测试对象：CrossAssetSnapshotBuilder.build_daily_snapshots(for_model=True)
    目的/目标：即使能建展示快照，for_model=True 对轴输入须 fail-closed
    验证点：pytest.raises(DoubleCountGuardError)
    失败含义：模型路径可写入轴输入快照，双计_guard 被绕过
    """
    vix = _staged_asset("L2-VIX")
    builder = CrossAssetSnapshotBuilder()
    with pytest.raises(DoubleCountGuardError):
        builder.build_daily_snapshots(
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            registry_entry=vix,
            observations=[_obs("L2-VIX")],
            source_fetch_ids=("fetch-1",),
            source_content_hashes=("hash-1",),
            for_model=True,
        )


def test_doubleCountGuard_modelEligibleAsset_passes() -> None:
    """覆盖范围：可入模资产通过资格检查
    测试对象：assert_model_eligible（L2-COPPER）
    目的/目标：eligible_for_model 的常规定价资产应无 guard 异常
    验证点：assert_model_eligible 不抛错
    失败含义：合法铜价资产被拒，模型特征链路断供
    """
    result = _staged_registry()
    copper = _staged_asset("L2-COPPER")
    assert_model_eligible(copper)


def test_snapshotRejectsFutureInput() -> None:
    """覆盖范围：未来可见性时间戳拒收
    测试对象：reject_future_observation（as_of_visibility 超前）
    目的/目标：as_of 边界后可见的数据不得参与当前快照
    验证点：pytest.raises(Exception, match=future input blocked)
    失败含义：未来数据泄漏进快照，时点审计失真
    """
    future = _obs("L2-COPPER", as_of_visibility=AS_OF + timedelta(hours=1))
    with pytest.raises(Exception, match="future input blocked"):
        reject_future_observation(as_of=AS_OF, observation=future)


def test_snapshotRejectsFutureTradeTime() -> None:
    """覆盖范围：未来 trade_time 拒收
    测试对象：reject_future_observation（trade_time 超前 as_of）
    目的/目标：成交时间不得晚于 as_of 可见边界
    验证点：pytest.raises(Exception, match=future trade_time blocked)
    失败含义：未来交易日数据可入库，回测与实盘边界混乱
    """
    future = _obs(
        "L2-COPPER",
        trade_time=AS_OF + timedelta(hours=1),
    )
    with pytest.raises(Exception, match="future trade_time blocked"):
        reject_future_observation(as_of=AS_OF, observation=future)


def test_snapshotRejectsFutureFetch_viaBuilder() -> None:
    """覆盖范围：未来 fetch_time 经 builder 拒收
    测试对象：CrossAssetSnapshotBuilder.build_daily_snapshots
    目的/目标：抓取时间晚于 as_of 的观测不得建快照
    验证点：pytest.raises(Exception, match=future fetch blocked)
    失败含义：延迟抓取未校验，血缘时间窗不可信
    """
    copper = _staged_asset("L2-COPPER")
    future_fetch = _obs("L2-COPPER", fetch_time=AS_OF + timedelta(hours=1))
    builder = CrossAssetSnapshotBuilder()
    with pytest.raises(Exception, match="future fetch blocked"):
        builder.build_daily_snapshots(
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            registry_entry=copper,
            observations=[future_fetch],
            source_fetch_ids=("fetch-1",),
            source_content_hashes=("hash-1",),
        )


def test_snapshotBuilder_rejectsMixedTradeDateBatch() -> None:
    """覆盖范围：同批观测 trade_date 必须一致
    测试对象：CrossAssetSnapshotBuilder.build_daily_snapshots（混合两日）
    目的/目标：日快照批内不得混入多个 trade_date
    验证点：pytest.raises(Exception, match=mixed trade_date batch)
    失败含义：一日快照掺入他日 bar，OHLC 聚合错误
    """
    copper = _staged_asset("L2-COPPER")
    mixed = [
        _obs("L2-COPPER"),
        _obs(
            "L2-COPPER",
            trade_time=datetime(2026, 6, 13, 16, 0, tzinfo=UTC),
        ),
    ]
    with pytest.raises(Exception, match="mixed trade_date batch"):
        CrossAssetSnapshotBuilder().build_daily_snapshots(
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            registry_entry=copper,
            observations=mixed,
            source_fetch_ids=("fetch-1",),
            source_content_hashes=("hash-1",),
        )


def test_snapshotBuilder_rejectsTradeDateMismatch() -> None:
    """覆盖范围：观测日与请求 trade_date 对齐
    测试对象：CrossAssetSnapshotBuilder.build_daily_snapshots（trade_date 无匹配观测）
    目的/目标：指定 trade_date 下无观测应 fail-closed
    验证点：pytest.raises(Exception, match=no observations)
    失败含义：空日仍产出快照或误用邻日数据
    """
    copper = _staged_asset("L2-COPPER")
    wrong_day = _obs(
        "L2-COPPER",
        trade_time=datetime(2026, 6, 13, 16, 0, tzinfo=UTC),
    )
    with pytest.raises(Exception, match="no observations"):
        CrossAssetSnapshotBuilder().build_daily_snapshots(
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            registry_entry=copper,
            observations=[wrong_day],
            source_fetch_ids=("fetch-1",),
            source_content_hashes=("hash-1",),
        )


def test_stagedSource_rejectsTdxPytdx_viaBuilder() -> None:
    """覆盖范围：staged 路径拒绝 tdx_pytdx 来源
    测试对象：CrossAssetSnapshotBuilder（source=tdx_pytdx）
    目的/目标：staged fixture 管线不得接受未审批 TDX 实时源
    验证点：pytest.raises(Exception, match=tdx_pytdx)
    失败含义：生产 TDX 数据混入 staged 快照，gate 隔离失效
    """
    copper = _staged_asset("L2-COPPER")
    tdx_obs = _obs("L2-COPPER", source="tdx_pytdx")
    with pytest.raises(Exception, match="tdx_pytdx"):
        CrossAssetSnapshotBuilder().build_daily_snapshots(
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            registry_entry=copper,
            observations=[tdx_obs],
            source_fetch_ids=("fetch-1",),
            source_content_hashes=("hash-1",),
        )


def test_crossAssetSnapshotBuilder_buildsDailySnapshotWithLineage() -> None:
    """覆盖范围：日快照与血缘正常构建
    测试对象：CrossAssetSnapshotBuilder.build_daily_snapshots（L2-COPPER 多 bar）
    目的/目标：收盘取末 bar；产出 lineage layer2 与 source_fetch_ids
    验证点：roll is None；close=100；pct_change 正确；lineage.layer_id=layer2
    失败含义：主路径建不出带血缘日快照，Layer2 落库链路断裂
    """
    copper = _staged_asset("L2-COPPER")
    obs = [
        _obs(
            "L2-COPPER",
            trade_time=datetime(2026, 6, 14, 10, 0, tzinfo=UTC),
            close=90.0,
        ),
        _obs(
            "L2-COPPER",
            trade_time=datetime(2026, 6, 14, 15, 0, tzinfo=UTC),
            close=100.0,
        ),
    ]
    snap, lineage, roll = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=copper,
        observations=obs,
        source_fetch_ids=("fetch-l2-1",),
        source_content_hashes=("hash-l2-abc",),
    )
    assert roll is None
    assert snap.close == 100.0
    assert snap.pct_change == pytest.approx(100.0 / 90.0 - 1.0)
    assert lineage.layer_id == "layer2"
    assert lineage.source_fetch_ids == ("fetch-l2-1",)


def test_snapshotDeterministicRebuild_sameInputsSameHash() -> None:
    """覆盖范围：相同输入确定性重建
    测试对象：CrossAssetSnapshotBuilder 两次相同入参
    目的/目标：close/pct_change 与 parameter_hash 可复现
    验证点：snap1==snap2 关键字段；lin1.parameter_hash==lin2.parameter_hash
    失败含义：同输入哈希漂移，增量重建无法判等
    """
    copper = _staged_asset("L2-COPPER")
    obs = [_obs("L2-COPPER")]
    builder = CrossAssetSnapshotBuilder()
    snap1, lin1, _ = builder.build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=copper,
        observations=obs,
        source_fetch_ids=("f",),
        source_content_hashes=("hash-det",),
    )
    snap2, lin2, _ = builder.build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=copper,
        observations=obs,
        source_fetch_ids=("f",),
        source_content_hashes=("hash-det",),
    )
    assert snap1.close == snap2.close
    assert snap1.pct_change == snap2.pct_change
    assert lin1.parameter_hash == lin2.parameter_hash


def test_snapshotLineageContainsSourceHashes() -> None:
    """覆盖范围：Layer2LineageBuilder 必填字段
    测试对象：Layer2LineageBuilder.build
    目的/目标：LINEAGE_REQUIRED_FIELDS 除 rebuild_reason 外均非空
    验证点：逐字段 getattr 非 None
    失败含义：血缘信封残缺，axis_snapshot_lineage 写入被拒
    """
    lineage = Layer2LineageBuilder().build(
        snapshot_id="l2-test-lineage",
        snapshot_type="cross_asset_daily_snapshot",
        as_of=AS_OF,
        input_window_start=AS_OF - timedelta(days=5),
        input_window_end=AS_OF - timedelta(days=1),
        source_dataset_ids=("staged:cross_asset_observation:L2-COPPER",),
        source_fetch_ids=("fetch-1",),
        source_content_hashes=("sha256-deadbeef",),
        rule_version="layer2_sensor_staged_v1",
        parameter_hash="param-hash-1",
    )
    for field in LINEAGE_REQUIRED_FIELDS:
        if field == "rebuild_reason":
            continue
        assert getattr(lineage, field) is not None


def test_futuresRollHandler_emitsExplicitRollEvent_notSilentSwitch() -> None:
    """覆盖范围：期货换月显式 roll 事件
    测试对象：FuturesRollHandler.detect_roll
    目的/目标：流动性挑战者胜出时须 roll_event=True 并记录新旧合约
    验证点：roll 非空；roll_event；old/new contract 正确
    失败含义：换月静默切换，持仓连续性与审计丢失
    """
    roll = FuturesRollHandler().detect_roll(
        asset_id="L2-HG-MAIN",
        roll_date=TRADE_DATE,
        incumbent=ContractLiquidity("HGZ25", TRADE_DATE, volume=1000, open_interest=5000),
        challenger=ContractLiquidity("HGF26", TRADE_DATE, volume=5000, open_interest=5200),
    )
    assert roll is not None
    assert roll.roll_event is True
    assert roll.old_contract == "HGZ25"
    assert roll.new_contract == "HGF26"


def test_futuresRollEvent_persistedViaWriteManager(tmp_path: Path) -> None:
    """覆盖范围：roll 事件经 WriteManager 持久化
    测试对象：Layer2RollEventWriter.write_roll_event
    目的/目标：detect_roll 结果写入 cross_asset_roll_event 表
    验证点：res.status=SUCCESS；DB 行 roll_event 与合约对
    失败含义：换月事件仅内存存在，复盘无法查历史 roll
    """
    cm = _layer2_cm(tmp_path, "layer2_roll.duckdb")
    _insert_validation_report(cm, "vr-roll-1")

    roll = FuturesRollHandler().detect_roll(
        asset_id="L2-HG-MAIN",
        roll_date=TRADE_DATE,
        incumbent=ContractLiquidity("HGZ25", TRADE_DATE, volume=1000, open_interest=5000),
        challenger=ContractLiquidity("HGF26", TRADE_DATE, volume=5000, open_interest=5200),
    )
    assert roll is not None
    res = Layer2RollEventWriter(cm).write_roll_event(roll, validation_report_id="vr-roll-1")
    assert res.status == "SUCCESS"
    with cm.reader() as con:
        row = con.execute(
            "SELECT roll_event, old_contract, new_contract FROM cross_asset_roll_event"
        ).fetchone()
        assert row[0] is True
        assert row[1] == "HGZ25"
        assert row[2] == "HGF26"


def test_crossAssetSnapshotBuilder_resourceGuardBlocksBatchBuild() -> None:
    """覆盖范围：ResourceGuard HARD_STOP 阻断构建
    测试对象：CrossAssetSnapshotBuilder（mock guard HARD_STOP）
    目的/目标：资源守卫拒绝时不得继续 build_daily_snapshots
    验证点：pytest.raises(ResourceGuardBlockedError)
    失败含义：低资源环境仍批量建快照，可能 OOM
    """
    guard = MagicMock()
    guard.check.return_value = (Decision.HARD_STOP, "eco limit")
    copper = _staged_asset("L2-COPPER")
    with pytest.raises(ResourceGuardBlockedError):
        CrossAssetSnapshotBuilder(resource_guard=guard).build_daily_snapshots(
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            registry_entry=copper,
            observations=[_obs("L2-COPPER")],
            source_fetch_ids=("fetch-1",),
            source_content_hashes=("hash-1",),
        )


def test_resourceGuard_realInstance_returnsDecision(tmp_path: Path) -> None:
    """覆盖范围：真实 ResourceGuard 返回决策枚举
    测试对象：ResourceGuard.check（真实 DuckDB 连接）
    目的/目标：check 应返回 OK/WARN/PAUSE/HARD_STOP 之一
    验证点：decision in 四枚举值
    失败含义：守卫接口异常，service 层无法解释阻断原因
    """
    db = tmp_path / "rg.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
        decision, _ = ResourceGuard(con=con).check()
    assert decision in (Decision.OK, Decision.WARN, Decision.PAUSE, Decision.HARD_STOP)


def test_noAcceptedChannel_notModelEligible() -> None:
    """覆盖范围：无接受通道资产不可入模
    测试对象：assert_model_eligible（L2-NO-CHANNEL）
    目的/目标：缺 primary 等通道的资产须 DoubleCountGuardError
    验证点：pytest.raises(DoubleCountGuardError)
    失败含义：无来源资产进入模型聚合
    """
    missing = _staged_asset("L2-NO-CHANNEL")
    with pytest.raises(DoubleCountGuardError):
        assert_model_eligible(missing)


def test_vixAxisInput_displayOnlySnapshot_carriesGuardFlag() -> None:
    """覆盖范围：轴输入展示快照质量标记
    测试对象：CrossAssetSnapshotBuilder（L2-VIX 非 for_model）
    目的/目标：展示快照须含 LAYER1_AXIS_INPUT_DISPLAY_ONLY 标记
    验证点：quality_flags 含该常量
    失败含义：展示用 VIX 无标记，下游难区分可入模与仅参考
    """
    vix = _staged_asset("L2-VIX")
    snap, _, _ = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=vix,
        observations=[_obs("L2-VIX", close=18.5)],
        source_fetch_ids=("fetch-vix",),
        source_content_hashes=("hash-vix",),
    )
    assert "LAYER1_AXIS_INPUT_DISPLAY_ONLY" in snap.quality_flags


def test_incrementalRebuildPreservesAsOfBoundary() -> None:
    """覆盖范围：增量重建 as_of 边界
    测试对象：build_daily_snapshots(is_incremental=True)
    目的/目标：增量血缘 is_incremental=True 且 input_window_end<=as_of
    验证点：lineage.is_incremental；window_end 不越界
    失败含义：增量重建越界读未来数据，时点一致性破坏
    """
    copper = _staged_asset("L2-COPPER")
    _snap, lineage, _ = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=copper,
        observations=[_obs("L2-COPPER")],
        source_fetch_ids=("fetch-inc2",),
        source_content_hashes=("hash-inc2",),
        is_incremental=True,
        rebuild_reason="incremental",
    )
    assert lineage.is_incremental is True
    assert lineage.input_data_window_end <= lineage.as_of_timestamp


def test_upstreamSnapshotIds_propagateToLineage() -> None:
    """覆盖范围：上游快照 ID 写入血缘
    测试对象：build_daily_snapshots(upstream_snapshot_ids=...)
    目的/目标：Layer1 等上游快照 ID 须原样进入 lineage
    验证点：lineage.upstream_snapshot_ids == 入参元组
    失败含义：跨层血缘链断裂，无法追溯 Layer1 输入
    """
    copper = _staged_asset("L2-COPPER")
    upstream = ("l1-snap-env-2026-06-14",)
    _snap, lineage, _ = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=copper,
        observations=[_obs("L2-COPPER")],
        source_fetch_ids=("fetch-inc",),
        source_content_hashes=("hash-inc",),
        upstream_snapshot_ids=upstream,
    )
    assert lineage.upstream_snapshot_ids == upstream


def test_rollEvent_integratedInSnapshotBuild_setsActiveContract() -> None:
    """覆盖范围：构建集成换月设活跃合约
    测试对象：build_daily_snapshots（roll_incumbent/challenger）
    目的/目标：换月时 snap.active_contract 切到挑战者合约
    验证点：roll 非空；active_contract=HGF26
    失败含义：换月后快照仍指旧合约，连续价序列错误
    """
    main = _staged_asset("L2-HG-MAIN")
    snap, _, roll = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=main,
        observations=[_obs("L2-HG-MAIN")],
        source_fetch_ids=("fetch-roll",),
        source_content_hashes=("hash-roll",),
        roll_incumbent=ContractLiquidity("HGZ25", TRADE_DATE, 1000, 5000),
        roll_challenger=ContractLiquidity("HGF26", TRADE_DATE, 5000, 5200),
    )
    assert roll is not None
    assert snap.active_contract == "HGF26"


def test_layer2Observation_blocksAxisInputWithoutDisplayOnlyWrite(tmp_path: Path) -> None:
    """覆盖范围：观测写入拦截非 display_only 轴输入
    测试对象：Layer2ObservationWriter.write_observations（VIX, display_only_write=False）
    目的/目标：轴输入未经 display_only 路径不得写入观测表
    验证点：pytest.raises(DoubleCountGuardError)
    失败含义：轴输入观测误入库，与展示/入模策略冲突
    """
    vix = _staged_asset("L2-VIX")
    cm = ConnectionManager(tmp_path / "block.duckdb")
    with pytest.raises(DoubleCountGuardError):
        Layer2ObservationWriter(cm).write_observations(
            registry_entry=vix,
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            observations=[_obs("L2-VIX")],
            validation_report_id="vr-x",
            display_only_write=False,
        )


def test_layer2Snapshot_writeWithRollEvent_persistsAllTables(tmp_path: Path) -> None:
    """覆盖范围：快照+换月一并落库
    测试对象：Layer2SnapshotWriter.write_daily_snapshot（含 roll_event）
    目的/目标：日快照、血缘、roll 三表均有记录且 active_contract 更新
    验证点：roll_row=1；snap active_contract=HGF26
    失败含义：换月与日快照不同步持久化，DB 状态不一致
    """
    cm = _layer2_cm(tmp_path, "layer2_roll_snap.duckdb")
    _insert_validation_report(cm, "vr-roll-snap")

    main = _staged_asset("L2-HG-MAIN")
    snap, lineage, roll = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=main,
        observations=[_obs("L2-HG-MAIN")],
        source_fetch_ids=("fetch-roll-snap",),
        source_content_hashes=("hash-roll-snap",),
        roll_incumbent=ContractLiquidity("HGZ25", TRADE_DATE, 1000, 5000),
        roll_challenger=ContractLiquidity("HGF26", TRADE_DATE, 5000, 5200),
    )
    assert roll is not None
    Layer2SnapshotWriter(cm).write_daily_snapshot(
        snapshot=snap,
        lineage=lineage,
        roll_event=roll,
        validation_report_id="vr-roll-snap",
    )
    with cm.reader() as con:
        roll_row = con.execute("SELECT COUNT(*) FROM cross_asset_roll_event").fetchone()[0]
        snap_row = con.execute("SELECT active_contract FROM cross_asset_daily_snapshot").fetchone()
        assert roll_row == 1
        assert snap_row[0] == "HGF26"


def test_layer2Observation_writeViaWriteManager(tmp_path: Path) -> None:
    """覆盖范围：观测经 WriteManager 成功写入
    测试对象：Layer2ObservationWriter.write_observations（L2-COPPER）
    目的/目标：合法观测在 validation_report 存在时 status=SUCCESS
    验证点：result.status == SUCCESS
    失败含义：主路径观测无法落库，Layer2 管道中断
    """
    cm = _layer2_cm(tmp_path, "layer2_obs_wm.duckdb")
    _insert_validation_report(cm, "vr-layer2-obs-1")

    copper = _staged_asset("L2-COPPER")
    result = Layer2ObservationWriter(cm).write_observations(
        registry_entry=copper,
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        observations=[_obs("L2-COPPER")],
        validation_report_id="vr-layer2-obs-1",
    )
    assert result.status == "SUCCESS"


def test_layer2Observation_rejectsAssetIdMismatch(tmp_path: Path) -> None:
    """覆盖范围：观测 asset_id 与注册表条目一致
    测试对象：Layer2ObservationWriter（registry=copper, obs=vix）
    目的/目标：观测 asset_id 必须与 registry_entry.asset_id 匹配
    验证点：pytest.raises(Exception, match=asset_id)
    失败含义：错资产观测可写入，跨资产污染
    """
    copper = _staged_asset("L2-COPPER")
    with pytest.raises(Exception, match="asset_id"):
        Layer2ObservationWriter(ConnectionManager(tmp_path / "x.duckdb")).write_observations(
            registry_entry=copper,
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            observations=[_obs("L2-VIX")],
            validation_report_id="vr-x",
        )


def test_layer2Snapshot_writeViaWriteManager(tmp_path: Path) -> None:
    """覆盖范围：日快照与血缘经 WriteManager 写入
    测试对象：Layer2SnapshotWriter.write_daily_snapshot
    目的/目标：快照与 lineage 均 SUCCESS 且 layer_id=layer2
    验证点：snap_res/lin_res.status=SUCCESS；DB lineage layer_id=layer2
    失败含义：快照或血缘单独失败，staging 表不完整
    """
    cm = _layer2_cm(tmp_path, "layer2_wm.duckdb")
    _insert_validation_report(cm, "vr-layer2-1")

    copper = _staged_asset("L2-COPPER")
    snap, lineage, roll = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=copper,
        observations=[_obs("L2-COPPER")],
        source_fetch_ids=("fetch-l2-wm",),
        source_content_hashes=("hash-l2-wm",),
    )
    snap_res, lin_res = Layer2SnapshotWriter(cm).write_daily_snapshot(
        snapshot=snap,
        lineage=lineage,
        roll_event=roll,
        validation_report_id="vr-layer2-1",
    )
    assert snap_res.status == "SUCCESS"
    assert lin_res.status == "SUCCESS"
    with cm.reader() as con:
        lin = con.execute(
            "SELECT layer_id FROM axis_snapshot_lineage WHERE snapshot_id = ?",
            [lineage.snapshot_id],
        ).fetchone()
        assert lin[0] == "layer2"


def test_layer2Registry_syncViaWriteManager(tmp_path: Path) -> None:
    """覆盖范围：注册表全量同步到 DB
    测试对象：CrossAssetRegistryWriter.sync_registry
    目的/目标：loaded.assets 条数与 cross_asset_registry 行数一致
    验证点：res.status=SUCCESS；count==len(assets)
    失败含义：YAML 注册表与 DB 副本不一致，运行时读到过期元数据
    """
    cm = _layer2_cm(tmp_path, "layer2_reg.duckdb")
    _insert_validation_report(cm, "vr-reg-1")
    loaded = _staged_registry()
    res = CrossAssetRegistryWriter(cm).sync_registry(
        loaded.assets, validation_report_id="vr-reg-1"
    )
    assert res.status == "SUCCESS"
    with cm.reader() as con:
        count = con.execute("SELECT COUNT(*) FROM cross_asset_registry").fetchone()[0]
        assert count == len(loaded.assets)


def test_layer2Loader_defaultRejectsProductionLiveMode(tmp_path: Path) -> None:
    """覆盖范围：默认 loader 拒绝 production_live
    测试对象：CrossAssetRegistryLoader.load（production_live 与 staged fixture 对照）
    目的/目标：production_live 抛错；STAGED_REGISTRY_FIXTURE 仍为 staged_fixture_only
    验证点：bad yaml raises staged_fixture_only；fixture mode 正确
    失败含义：生产模式配置被误当作 staged 加载
    """
    bad = tmp_path / "production_live.yaml"
    bad.write_text(
        "version: v1\nmode: production_live\nassets:\n"
        "  - asset_id: X\n    display_name_cn: x\n    asset_group: USD\n"
        "    asset_type: index\n    market: US\n    primary_source: staged_fixture\n"
        "    validation_source: none\n    fallback_policy: none\n"
        "    is_axis_input: false\n    display_only: false\n"
        "    eligible_for_model: true\n    double_count_guard: none\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="staged_fixture_only"):
        CrossAssetRegistryLoader().load(registry_path=bad)
    result = _staged_registry()
    assert result.mode == "staged_fixture_only"
