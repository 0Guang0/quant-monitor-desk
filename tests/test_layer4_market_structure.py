"""第四层市场结构快照测试（Round 3 任务 022）。

覆盖范围：用 staged fixture 生成市场注册表、交易日历、宽度快照与血缘记录。
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
import yaml
from backend.app.config import PROJECT_ROOT
from backend.app.core.snapshot_lineage import LINEAGE_REQUIRED_FIELDS
from backend.app.layer4_markets.market_structure import (
    FORBIDDEN_LAYER1_STANDARDIZATION_FIELDS,
    FORBIDDEN_LAYER5_HISTORY_FIELDS,
    Layer4MarketError,
    MarketStructureBuilder,
    collect_result_field_names,
    seed_registry_rows,
)

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "layer4_staged_market"
_MUTATION_ROOT = PROJECT_ROOT / ".audit-sandbox" / "layer4_market_mutations"
AS_OF = datetime(2026, 6, 15, 8, 0, tzinfo=UTC)
TRADE_DATE = date(2026, 6, 14)
_MARKET_ID = "CN_A"


def _build(
    *,
    bundle_dir: Path = _FIXTURE,
    as_of: datetime = AS_OF,
    upstream_snapshot_ids: tuple[str, ...] = (),
) -> object:
    """ponytail: shared build() for AC tests; copytree only when mutating fixture."""
    return MarketStructureBuilder().build(
        market_id=_MARKET_ID,
        trade_date=TRADE_DATE,
        as_of=as_of,
        bundle_dir=bundle_dir,
        upstream_snapshot_ids=upstream_snapshot_ids,
    )


def _copy_bundle(tmp_path: Path) -> Path:
    """Copy fixture under PROJECT_ROOT so path guard allows mutation tests."""
    dest = _MUTATION_ROOT / tmp_path.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(_FIXTURE, dest)
    return dest


def _mutate_bundle_file(
    tmp_path: Path,
    filename: str,
    *,
    loader,
    dumper,
    mutator,
) -> Path:
    """ponytail: copy bundle then load→mutate→dump one fixture file."""
    bundle = _copy_bundle(tmp_path)
    file_path = bundle / filename
    data = loader(file_path.read_text(encoding="utf-8"))
    mutator(data)
    file_path.write_text(dumper(data), encoding="utf-8")
    return bundle


def _mutate_manifest(tmp_path: Path, mutator) -> Path:
    return _mutate_bundle_file(
        tmp_path,
        "manifest.yaml",
        loader=lambda text: yaml.safe_load(text),
        dumper=lambda data: yaml.safe_dump(data, allow_unicode=True),
        mutator=mutator,
    )


def _mutate_calendar(tmp_path: Path, mutator) -> Path:
    return _mutate_bundle_file(
        tmp_path,
        "calendar.json",
        loader=json.loads,
        dumper=lambda data: json.dumps(data, indent=2),
        mutator=mutator,
    )


def _mutate_breadth(tmp_path: Path, mutator) -> Path:
    return _mutate_bundle_file(
        tmp_path,
        "breadth.json",
        loader=json.loads,
        dumper=lambda data: json.dumps(data, indent=2),
        mutator=mutator,
    )


def test_marketRegistry_uniqueMarketIds() -> None:
    """覆盖范围：市场注册表种子行的 market_id 唯一性
    测试对象：seed_registry_rows / MarketStructureBuildResult.registry_rows
    目的/目标：证明 8 个 market_id 元数据种子无重复，满足 contract PK
    验证点：len(ids)==len(set(ids))；至少含 CN_A；build 结果携带完整种子
    失败含义：registry 重复 id 仍绿，下游 market_calendar FK 与 adapter 路由会错乱
    """
    rows = seed_registry_rows()
    ids = [row.market_id for row in rows]
    assert len(ids) == len(set(ids))
    assert "CN_A" in ids
    assert len(rows) == 8

    result = _build()
    result_ids = [row.market_id for row in result.registry_rows]
    assert len(result_ids) == len(set(result_ids))


def test_marketAdapter_nonStagedSource_rejects(tmp_path: Path) -> None:
    """覆盖范围：市场数据来源不是「仅测试 fixture」时的拒绝逻辑
    测试对象：MarketStructureBuilder.build 对 manifest source_mode 的校验
    目的/目标：防止把线上真实行情误当成 staged 市场快照来生成
    验证点：source_mode=production_live → Layer4MarketError 且含 staged_fixture_only
    失败含义：非 staged 源仍能建快照，Batch3 gate 双闸与 AC-022-6 失效
    """
    bundle = _mutate_manifest(
        tmp_path, lambda m: m.update({"source_mode": "production_live"})
    )
    with pytest.raises(Layer4MarketError, match="staged_fixture_only"):
        _build(bundle_dir=bundle)


def test_marketCalendar_rejectsDuplicateTradeDate(tmp_path: Path) -> None:
    """覆盖范围：交易日历主键 (market_id, trade_date) 重复时的拒绝逻辑
    测试对象：MarketStructureBuilder.build 加载 calendar.json 的去重校验
    目的/目标：同一市场同一交易日不得出现两条日历行
    验证点：重复 PK → Layer4MarketError 且含 duplicate
    失败含义：重复日历仍绿，contract PK 与交易日判定会失真
    """
    bundle = _mutate_calendar(tmp_path, lambda rows: rows.append(dict(rows[0])))

    with pytest.raises(Layer4MarketError, match="duplicate"):
        _build(bundle_dir=bundle)


def test_marketBreadth_requiredFieldsPresent() -> None:
    """覆盖范围：市场宽度快照 contract required_fields 是否齐全
    测试对象：MarketStructureBuilder.build 产出的 breadth_row
    目的/目标：宽度行必须含 advancers/decliners/total_amount/breadth_label 等契约字段
    验证点：breadth_row 各 required 字段非空；market_id 与 trade_date 与入参一致
    失败含义：缺字段仍绿，AC-022-3 与 layer4_market_contract 宽度模型不合格
    """
    result = _build()
    row = result.breadth_row
    assert row.market_id == _MARKET_ID
    assert row.trade_date == TRADE_DATE
    assert row.advancers > 0
    assert row.decliners > 0
    assert row.total_amount > 0
    assert row.breadth_label
    assert row.source
    assert row.quality_flag


def test_marketSnapshot_lineageRequiredFieldsComplete() -> None:
    """覆盖范围：市场快照附带的血缘（来源追溯）信息是否齐全
    测试对象：MarketStructureBuilder.build 产出的 lineage_envelope
    目的/目标：快照能说明数据从哪来、何时算的；缺关键字段视为不合格
    验证点：LINEAGE_REQUIRED_FIELDS 逐字段非空（rebuild_reason 可空）；layer_id=layer4；hashes 非空
    失败含义：血缘缺字段仍绿，AC-022-4 与增量重建审计会失真
    """
    result = _build(upstream_snapshot_ids=("l3-snap-001",))
    envelope = result.lineage_envelope
    for field in LINEAGE_REQUIRED_FIELDS:
        if field == "rebuild_reason":
            continue
        assert getattr(envelope, field) is not None, field
    assert envelope.layer_id == "layer4"
    assert envelope.source_content_hashes
    assert envelope.upstream_snapshot_ids == ("l3-snap-001",)


def test_marketSnapshot_lineageUpstreamFromLayer3() -> None:
    """覆盖范围：L4 lineage upstream_snapshot_ids 与 L3 snapshot_id 传播
    测试对象：MarketStructureBuilder.build 的 upstream_snapshot_ids 参数
    目的/目标：ADV-R3X contract-scoped — L3→L4 staged builder lineage 链可 runtime 断言
    验证点：传入 L3 lineage snapshot_id → envelope.upstream_snapshot_ids 原样保留
    失败含义：上游 L3 ID 未传播，跨层血缘链在 staged 路径不可审计
    """
    from tests.test_layer3_snapshot_builder import _build as build_layer3

    l3_result = build_layer3()
    l3_lineage = next(e for e in l3_result.lineage_envelopes if "MSFT" in e.snapshot_id)
    result = _build(upstream_snapshot_ids=(l3_lineage.snapshot_id,))
    assert result.lineage_envelope.upstream_snapshot_ids == (l3_lineage.snapshot_id,)
    for field in LINEAGE_REQUIRED_FIELDS:
        if field == "rebuild_reason":
            continue
        assert getattr(result.lineage_envelope, field) is not None, field


def test_marketSnapshotRejectsFutureInput(tmp_path: Path) -> None:
    """覆盖范围：观测时间晚于 snapshot as_of 时的拒绝逻辑
    测试对象：MarketStructureBuilder.build 对 as_of 边界的检查
    目的/目标：不允许用「未来」的市场观测回填历史快照
    验证点：breadth as_of_timestamp 晚于 build as_of → Layer4MarketError 含 future
    失败含义：未来可见数据混入快照，no_future_data 契约被绕过
    """
    future_ts = (AS_OF + timedelta(days=1)).isoformat()
    bundle = _mutate_breadth(tmp_path, lambda row: row.update({"as_of_timestamp": future_ts}))

    with pytest.raises(Layer4MarketError, match="future"):
        _build(bundle_dir=bundle)


def test_marketSnapshot_noLayer5HistoryFields() -> None:
    """覆盖范围：市场结构产出不得携带 Layer5 全量历史或 Layer1 标准化 suite 字段
    测试对象：MarketStructureBuildResult 全部 dataclass 字段名集合
    目的/目标：遵守 D-09 与 contract boundaries；Layer4 只输出市场结构语义
    验证点：产出字段名与 FORBIDDEN_LAYER5/LAYER1 集合无交集
    失败含义：夹带 L5 历史或 L1 标准化列，AC-022-7 与下游 Layer5 边界破裂
    """
    result = _build()
    field_names = collect_result_field_names(result)
    assert field_names.isdisjoint(FORBIDDEN_LAYER5_HISTORY_FIELDS)
    assert field_names.isdisjoint(FORBIDDEN_LAYER1_STANDARDIZATION_FIELDS)


def test_marketSnapshot_rejectsNonTradingDay(tmp_path: Path) -> None:
    """覆盖范围：非交易日拒绝生成市场快照（§5.2 S2 失败路径）
    测试对象：MarketStructureBuilder.build 对 is_trading_day 的校验
    目的/目标：非交易日不得产出 breadth 快照，防止错误交易日数据混入
    验证点：calendar is_trading_day=false → Layer4MarketError 含 non-trading
    失败含义：非交易日仍绿，AC-022-2 与 quality_rules 非交易日规则失效
    """
    bundle = _mutate_calendar(tmp_path, lambda rows: rows[0].update({"is_trading_day": False}))

    with pytest.raises(Layer4MarketError, match="non-trading"):
        _build(bundle_dir=bundle)


def test_marketSnapshotRejectsFutureCalendarInput(tmp_path: Path) -> None:
    """覆盖范围：calendar 观测时间晚于 snapshot as_of 时的拒绝逻辑
    测试对象：MarketStructureBuilder.build 对 calendar as_of_timestamp 边界的检查
    目的/目标：no_future_data 双观测点之一；calendar 未来数据不得回填
    验证点：calendar as_of_timestamp 晚于 build as_of → Layer4MarketError 含 future
    失败含义：仅 breadth 有 future 测而 calendar 路径可回归，look-ahead 防护半失效
    """
    future_ts = (AS_OF + timedelta(days=1)).isoformat()
    bundle = _mutate_calendar(
        tmp_path, lambda rows: rows[0].update({"as_of_timestamp": future_ts})
    )

    with pytest.raises(Layer4MarketError, match="future"):
        _build(bundle_dir=bundle)


def test_marketAdapter_rejectsMissingManifest(tmp_path: Path) -> None:
    """覆盖范围：bundle 缺少 manifest.yaml 时的拒绝逻辑（空 fixture）
    测试对象：MarketStructureBuilder.build 首步 _read_manifest
    目的/目标：无 manifest 不得静默成功，staged 协议必须可观测
    验证点：空目录作 bundle_dir → Layer4MarketError 含 missing Layer 4 manifest
    失败含义：缺 manifest 仍绿，staged 血缘与 source_mode 双闸可被绕过
    """
    empty = _MUTATION_ROOT / tmp_path.name / "empty_manifest"
    empty.mkdir(parents=True, exist_ok=True)

    with pytest.raises(Layer4MarketError, match="missing Layer 4 manifest"):
        _build(bundle_dir=empty)


def test_marketAdapter_rejectsMissingCalendar(tmp_path: Path) -> None:
    """覆盖范围：bundle 缺少 calendar.json 时的拒绝逻辑（空 fixture）
    测试对象：StagedCNAMarketAdapter.load_calendar / _load_calendar_rows
    目的/目标：无交易日历文件不得构建快照
    验证点：删除 calendar.json 后 build → Layer4MarketError 含 missing calendar
    失败含义：缺 calendar 仍绿，交易日判定与 PK 校验链断裂
    """
    bundle = _copy_bundle(tmp_path)
    (bundle / "calendar.json").unlink()

    with pytest.raises(Layer4MarketError, match="missing calendar"):
        _build(bundle_dir=bundle)


def test_marketBreadth_rejectsMissingRequiredField(tmp_path: Path) -> None:
    """覆盖范围：breadth 缺 contract required_fields 时的拒绝逻辑（§5.2 S3）
    测试对象：_load_breadth_row 对 _BREADTH_REQUIRED 的 fail-fast
    目的/目标：缺 advancers 等必填字段不得进入 snapshot
    验证点：删除 advancers → Layer4MarketError 含 missing required field
    失败含义：缺字段仍绿，AC-022-3 宽度模型与 quality_flag 语义失真
    """
    bundle = _mutate_breadth(tmp_path, lambda row: row.pop("advancers"))

    with pytest.raises(Layer4MarketError, match="missing required field"):
        _build(bundle_dir=bundle)


def test_marketBreadth_rejectsNegativeVolume(tmp_path: Path) -> None:
    """覆盖范围：breadth 负成交量/金额时的拒绝逻辑（quality_rules）
    测试对象：_load_breadth_row 对 no_negative_volume_amount 的校验
    目的/目标：负 advancers/decliners/total_amount 不得进入快照
    验证点：total_amount=-1 → Layer4MarketError 含 non-negative
    失败含义：负值仍绿，layer4_market_contract quality_rules 未接线
    """
    bundle = _mutate_breadth(tmp_path, lambda row: row.update({"total_amount": -1}))

    with pytest.raises(Layer4MarketError, match="non-negative"):
        _build(bundle_dir=bundle)


def test_marketAdapter_bundleDirOutsideProject_rejects() -> None:
    """覆盖范围：bundle_dir 须在 PROJECT_ROOT 下（信任边界）
    测试对象：MarketStructureBuilder.build 的 _resolve_bundle_root
    目的/目标：阻止任意路径读 manifest，对齐 staged 本地信任边界
    验证点：项目外目录作 bundle_dir → Layer4MarketError 含 project root
    失败含义：任意可读目录可作来源，未来 CLI 切片无路径白名单
    """
    from tests.path_jail_support import path_outside_project_root

    outside = path_outside_project_root(suffix="outside_l4")
    shutil.copytree(_FIXTURE, outside)

    with pytest.raises(Layer4MarketError, match="project root"):
        _build(bundle_dir=outside)
