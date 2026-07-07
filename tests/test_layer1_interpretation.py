"""第一层特征计算、文字解读与快照血缘测试。

覆盖范围：用历史观测算特征、生成合规解读文案、记录快照来源，
以及经统一写入管理器把结果落库时的门禁行为。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from backend.app.core.resource_guard import Decision
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.layer1_axes.feature_engine import (
    AxisFeatureEngine,
    Layer1SnapshotError,
    ResourceGuardBlockedError,
)
from backend.app.layer1_axes.interpretation import (
    AxisInterpretationEngine,
    InterpretationRejectedError,
)
from backend.app.layer1_axes.lineage import (
    LINEAGE_REQUIRED_FIELDS,
    Layer1SnapshotWriter,
    Layer2WritebackError,
    LineageSnapshotError,
    SnapshotLineageBuilder,
    guard_layer2_writeback,
)
from backend.app.layer1_axes.models import AxisObservation, ValidationReportRef

AS_OF = datetime(2026, 6, 15, 16, 0, tzinfo=UTC)


def _obs(
    indicator_id: str,
    value: float,
    *,
    publish: datetime | None = None,
    source_switched: bool = False,
    fallback_policy: str | None = None,
) -> AxisObservation:
    pub = publish or AS_OF - timedelta(days=1)
    return AxisObservation(
        indicator_id=indicator_id,
        as_of_timestamp=AS_OF,
        publish_timestamp=pub,
        raw_value=value,
        source_used="fixture",
        source_switched=source_switched,
        fallback_policy=fallback_policy,
    )


def _history(indicator_id: str, n: int, value: float = 1.0) -> list[AxisObservation]:
    return [
        _obs(
            indicator_id,
            value,
            publish=AS_OF - timedelta(days=i + 2),
        )
        for i in range(n)
    ]


def test_axisFeatureEngine_insufficientHistory_noFakeZ() -> None:
    """覆盖范围：历史观测条数不足时，特征计算不应伪造统计量
    测试对象：AxisFeatureEngine.compute_features
    目的/目标：样本不够时不应输出 z 分数或百分位等不可靠统计
    验证点：state_bucket 为 insufficient_history；z 与 percentile 为 None；含 INSUFFICIENT_HISTORY 标记
    失败含义：短历史仍产出假 z 值，面板会展示误导性统计
    """
    engine = AxisFeatureEngine(min_obs_required=10, window_len=20)
    hist = _history("ENV-E1-EFFR", 3)
    rows = engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)
    row = rows[0]
    assert row.state_bucket == "insufficient_history"
    assert row.z_score is None
    assert row.percentile_rank is None
    assert "INSUFFICIENT_HISTORY" in row.quality_flags


def test_axisFeatureEngine_robustZUnavailable_whenMadZero() -> None:
    """覆盖范围：历史值全部相同时，稳健 z 分数应不可用
    测试对象：AxisFeatureEngine.compute_features
    目的/目标：中位绝对偏差为零时不应输出不可靠的稳健 z 分数
    验证点：robust_z_score 为 None；含 ROBUST_Z_UNAVAILABLE 标记
    失败含义：零方差序列仍给稳健 z，异常检测会误报
    """
    engine = AxisFeatureEngine(min_obs_required=5, window_len=10)
    hist = _history("ENV-E1-EFFR", 6, value=100.0)
    current = _obs("ENV-E1-EFFR", 100.0)
    row = engine.compute_features(as_of=AS_OF, observations=[current], history=hist)[0]
    assert row.robust_z_score is None
    assert "ROBUST_Z_UNAVAILABLE" in row.quality_flags


def test_axisFeatureEngine_sourceSwitched_recordsQualityFlag() -> None:
    """覆盖范围：观测数据来源发生切换时，特征应记录质量标记
    测试对象：AxisFeatureEngine.compute_features
    目的/目标：来源切换必须写入 SOURCE_SWITCHED 标记并保留陈旧原因说明
    验证点：quality_flags 含 SOURCE_SWITCHED；stale_reason 等于 fallback_policy
    失败含义：来源切换无标记，下游无法识别数据血缘变化
    """
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    policy = "last_good_cache + stale_reason"
    current = _obs(
        "ENV-E1-EFFR",
        1.05,
        source_switched=True,
        fallback_policy=policy,
    )
    row = engine.compute_features(as_of=AS_OF, observations=[current], history=hist)[0]
    assert "SOURCE_SWITCHED" in row.quality_flags
    assert row.stale_reason == policy


def test_axisFeatureEngine_resourceGuard_ecoProfile() -> None:
    """覆盖范围：资源门禁报硬停止时，特征计算应立即中断
    测试对象：AxisFeatureEngine.compute_features
    目的/目标：资源不足时必须拒绝继续计算，不能拖垮环境
    验证点：pytest.raises(ResourceGuardBlockedError, match=resource guard blocked)
    失败含义：资源不足仍算特征，可能拖垮沙箱或生产环境
    """
    guard = MagicMock()
    guard.check.return_value = (Decision.HARD_STOP, "eco limit")
    engine = AxisFeatureEngine(resource_guard=guard, min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    with pytest.raises(ResourceGuardBlockedError, match="resource guard blocked"):
        engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)


def test_snapshotRejectsFutureInput() -> None:
    """覆盖范围：发布日期晚于截止时间的观测应被拒绝参与快照计算
    测试对象：AxisFeatureEngine.compute_features
    目的/目标：禁止用未来发布时间的观测参与快照，守住 as_of 边界语义
    验证点：pytest.raises(Layer1SnapshotError, match='future input')
    失败含义：未来数据进入第一层快照，截止时间边界被破坏
    """
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    future = _obs("ENV-E1-EFFR", 1.0, publish=AS_OF + timedelta(days=1))
    with pytest.raises(Layer1SnapshotError, match="future input"):
        engine.compute_features(as_of=AS_OF, observations=[future], history=[future])


def test_axisInterpretation_rejectsForbiddenActionTerms() -> None:
    """覆盖范围：解读文案含禁止交易动作词时如何拒绝
    测试对象：AxisInterpretationEngine.reject_if_forbidden 与 build_interpretation
    目的/目标：第一层解读不得出现「买入」等交易动作暗示
    验证点：两处均 pytest.raises(InterpretationRejectedError, match=forbidden action terms)
    失败含义：禁止词进入解读快照，合规与产品边界被突破
    """
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    feat = engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)[0]
    interp_engine = AxisInterpretationEngine()
    with pytest.raises(InterpretationRejectedError, match="forbidden action terms"):
        interp_engine.reject_if_forbidden("建议买入")
    with pytest.raises(InterpretationRejectedError, match="forbidden action terms"):
        interp_engine.build_interpretation(
            as_of=AS_OF,
            features=[feat],
            templates={feat.indicator_id: "市场出现买入信号"},
        )


def test_layer2ValueCannotWritebackToLayer1() -> None:
    """覆盖范围：第二层数据不得回写到第一层快照表
    测试对象：guard_layer2_writeback
    目的/目标：第二层标识不得写入第一层特征快照等表，守住层级边界
    验证点：pytest.raises(Layer2WritebackError, match=layer2 writeback)
    失败含义：第二层污染第一层快照，层级边界与审计链失效
    """
    with pytest.raises(Layer2WritebackError, match="layer2 writeback"):
        guard_layer2_writeback(
            target_table="axis_feature_snapshot",
            layer_id="layer2",
        )


def _insert_validation_report(
    cm: ConnectionManager,
    report_id: str,
    *,
    fetch_ids: list[str] | None = None,
    hashes: list[str] | None = None,
) -> None:
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
                "run-layer1",
                "layer1_axis_feature",
                "fixture",
                "PASSED",
                1,
                0,
                0,
                True,
                False,
                "layer1_v1",
                "layer1_v1",
                json.dumps(fetch_ids or ["fetch-1"]),
                json.dumps(hashes or ["hash-abc"]),
            ],
        )


def _persist_lineage(
    tmp_path: Path,
    lineage,
    *,
    report_id: str = "vr-lineage",
    fetch_ids: list[str] | None = None,
    hashes: list[str] | None = None,
) -> ConnectionManager:
    db = tmp_path / "lineage_wm.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    _insert_validation_report(
        cm,
        report_id,
        fetch_ids=fetch_ids,
        hashes=hashes,
    )
    writer = Layer1SnapshotWriter(cm)
    result = writer.write_lineage(lineage=lineage, validation_report_id=report_id)
    assert result.status == "SUCCESS"
    return cm


def test_snapshotLineageIncludesAllRequiredFields(tmp_path) -> None:
    """覆盖范围：快照来源追溯记录持久化后，必填字段是否齐全
    测试对象：SnapshotLineageBuilder.build 与 Layer1SnapshotWriter.write_lineage
    目的/目标：除重建原因可空外，契约要求的来源追溯字段均须非空
    验证点：axis_snapshot_lineage 行存在；各 required 列在表中且非空（rebuild_reason 可空）
    失败含义：血缘缺字段仍通过，增量重建与审计无法追溯来源
    """
    report = ValidationReportRef(
        validation_report_id="vr-1",
        rule_version="layer1_v1",
        source_fetch_ids_json='["fetch-1"]',
        source_content_hashes_json='["hash-abc"]',
    )
    builder = SnapshotLineageBuilder()
    lineage = builder.build(
        snapshot_id="snap-1",
        snapshot_type="axis_feature_snapshot",
        as_of=AS_OF,
        validation_report=report,
        input_window_start=AS_OF - timedelta(days=30),
        input_window_end=AS_OF,
        source_dataset_ids=("ds-1",),
        parameter_hash="ph-1",
    )
    cm = _persist_lineage(tmp_path, lineage, report_id="vr-1")
    with cm.reader() as con:
        row = con.execute(
            "SELECT * FROM axis_snapshot_lineage WHERE snapshot_id = ?", ["snap-1"]
        ).fetchone()
        cols = [d[0] for d in con.description]
    assert row is not None
    for field in LINEAGE_REQUIRED_FIELDS:
        assert field in cols
        idx = cols.index(field)
        assert row[idx] is not None or field == "rebuild_reason"


def test_snapshotLineageContainsSourceHashes(tmp_path) -> None:
    """覆盖范围：快照血缘中来源指纹与拉取编号是否正确落库
    测试对象：Layer1SnapshotWriter.write_lineage
    目的/目标：校验报告中的内容指纹与拉取编号必须原样写入血缘表
    验证点：stored 列含 deadbeef 与 fetch-99
    失败含义：来源指纹丢失，下游无法验证快照输入一致性
    """
    report = ValidationReportRef(
        validation_report_id="vr-2",
        rule_version="layer1_v1",
        source_fetch_ids_json='["fetch-99"]',
        source_content_hashes_json='["deadbeef"]',
    )
    lineage = SnapshotLineageBuilder().build(
        snapshot_id="snap-2",
        snapshot_type="axis_feature_snapshot",
        as_of=AS_OF,
        validation_report=report,
        input_window_start=AS_OF - timedelta(days=7),
        input_window_end=AS_OF,
        source_dataset_ids=("vendor/bar",),
        parameter_hash="ph-2",
    )
    cm = _persist_lineage(tmp_path, lineage, report_id="vr-2")
    with cm.reader() as con:
        stored = con.execute(
            """
            SELECT source_content_hashes, source_fetch_ids
            FROM axis_snapshot_lineage WHERE snapshot_id=?
            """,
            ["snap-2"],
        ).fetchone()
    assert "deadbeef" in stored[0]
    assert "fetch-99" in stored[1]


def test_incrementalRebuildPreservesAsOfBoundary() -> None:
    """覆盖范围：增量重建快照时，输入窗口不得越过截止时间
    测试对象：SnapshotLineageBuilder.build（is_incremental=True）
    目的/目标：输入数据窗口结束时间不得晚于快照截止时间
    验证点：window_end <= as_of；is_incremental 为 True
    失败含义：增量快照窗口越界，会混入截止时间之后的数据
    """
    report = ValidationReportRef(
        validation_report_id="vr-3",
        rule_version="layer1_v1",
        source_fetch_ids_json="[]",
        source_content_hashes_json='["hash-incremental-boundary"]',
    )
    builder = SnapshotLineageBuilder()
    as_of = AS_OF
    lineage = builder.build(
        snapshot_id="snap-inc",
        snapshot_type="axis_feature_snapshot",
        as_of=as_of,
        validation_report=report,
        input_window_start=as_of - timedelta(days=5),
        input_window_end=as_of,
        source_dataset_ids=("ds",),
        parameter_hash="ph-inc",
        is_incremental=True,
        rebuild_reason="incremental",
    )
    assert lineage.input_data_window_end <= lineage.as_of_timestamp
    assert lineage.is_incremental is True


def test_snapshotDeterministicRebuild_sameInputsSameHash() -> None:
    """覆盖范围：相同输入与规则版本应产出确定性参数指纹
    测试对象：SnapshotLineageBuilder.parameter_hash_for
    目的/目标：相同规则版本与输入必须产出相同哈希；换版本则不同
    验证点：h1 == h2；换 layer1_v2 后 h1 != h3
    失败含义：同输入不同哈希，增量重建去重与缓存失效
    """
    inputs = ("ds-a", "ds-b")
    h1 = SnapshotLineageBuilder.parameter_hash_for(rule_version="layer1_v1", inputs=inputs)
    h2 = SnapshotLineageBuilder.parameter_hash_for(rule_version="layer1_v1", inputs=inputs)
    assert h1 == h2
    h3 = SnapshotLineageBuilder.parameter_hash_for(rule_version="layer1_v2", inputs=inputs)
    assert h1 != h3


def test_layer1Snapshot_writeViaWriteManager(tmp_path: Path) -> None:
    """覆盖范围：特征快照经统一写入管理器落库是否成功
    测试对象：Layer1SnapshotWriter.write_features
    目的/目标：带校验报告的特征行应写入成功，且表内恰好一行
    验证点：result.status == SUCCESS；COUNT(*) == 1
    失败含义：WriteManager 路径写特征失败，第一层面板无特征数据
    """
    db = tmp_path / "layer1_wm.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    _insert_validation_report(cm, "vr-layer1-wm")
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    feat = engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)[0]
    writer = Layer1SnapshotWriter(cm)
    result = writer.write_features(
        rows=[feat],
        validation_report_id="vr-layer1-wm",
    )
    assert result.status == "SUCCESS"
    with cm.reader() as con:
        cnt = con.execute("SELECT COUNT(*) FROM axis_feature_snapshot").fetchone()[0]
    assert cnt == 1


def test_axisFeatureEngine_windowLen_truncatesHistory() -> None:
    """覆盖范围：滑动窗口长度对长历史的截断统计是否正确
    测试对象：AxisFeatureEngine.compute_features（600 条历史，window_len=20）
    目的/目标：统计只应使用尾部 20 条，而非全部 600 条
    验证点：valid_obs_count == 20；z_score 非 None
    失败含义：窗口截断失效，特征受远古数据污染
    """
    engine = AxisFeatureEngine(min_obs_required=5, window_len=20)
    hist = _history("ENV-E1-EFFR", 600, value=1.0)
    hist[-1] = _obs("ENV-E1-EFFR", 50.0)
    row = engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)[0]
    assert row.valid_obs_count == 20
    assert row.z_score is not None


def test_axisFeatureEngine_shuffledHistory_sortedBeforeStats() -> None:
    """覆盖范围：乱序历史在统计前是否按时间正确排序
    测试对象：AxisFeatureEngine.compute_features
    目的/目标：历史顺序不应影响绝对变化量等时序统计结果
    验证点：乱序输入仍产出非 None 的 raw_delta_abs
    失败含义：未排序即算变化量，相邻观测对比错误
    """
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    shuffled = list(reversed(hist))
    row = engine.compute_features(as_of=AS_OF, observations=[shuffled[-1]], history=shuffled)[0]
    assert row.raw_delta_abs == pytest.approx(0.0)


def test_snapshotLineage_missingContentHashes_rejectsSyntheticFallback() -> None:
    """覆盖范围：生产模式下缺少内容指纹时不得自动编造
    测试对象：SnapshotLineageBuilder.build（allow_synthetic_hashes=False）
    目的/目标：校验报告无内容指纹时不得自动合成，必须拒绝建血缘
    验证点：None 或空列表 hashes 均 pytest.raises(LineageSnapshotError, match='source_content_hashes required')
    失败含义：生产血缘伪造指纹，审计无法验证真实输入
    """
    builder = SnapshotLineageBuilder()
    for hashes_json in (None, "[]"):
        report = ValidationReportRef(
            validation_report_id=f"vr-empty-{hashes_json or 'none'}",
            rule_version="layer1_v1",
            source_fetch_ids_json="[]",
            source_content_hashes_json=hashes_json,
        )
        with pytest.raises(
            LineageSnapshotError,
            match="source_content_hashes required",
        ):
            builder.build(
                snapshot_id="snap-empty-hashes",
                snapshot_type="axis_feature_snapshot",
                as_of=AS_OF,
                validation_report=report,
                input_window_start=AS_OF - timedelta(days=1),
                input_window_end=AS_OF,
                source_dataset_ids=("macro_supplementary:ENV-E1-DGS10",),
                parameter_hash="ph-empty",
                allow_synthetic_hashes=False,
            )


def test_snapshotLineage_allowSyntheticHashes_permitsFixtureFallback() -> None:
    """覆盖范围：测试夹具模式下允许从数据集编号合成内容指纹
    测试对象：SnapshotLineageBuilder.build（allow_synthetic_hashes=True）
    目的/目标：显式测试路径下可从来源数据集编号派生内容指纹
    验证点：envelope.source_content_hashes 非空且首项为 sha256(dataset_id)
    失败含义：测试环境无法建血缘，阻塞分阶段验证
    """
    report = ValidationReportRef(
        validation_report_id="vr-fixture",
        rule_version="layer1_v1",
        source_fetch_ids_json="[]",
        source_content_hashes_json=None,
    )
    envelope = SnapshotLineageBuilder().build(
        snapshot_id="snap-fixture",
        snapshot_type="axis_feature_snapshot",
        as_of=AS_OF,
        validation_report=report,
        input_window_start=AS_OF - timedelta(days=1),
        input_window_end=AS_OF,
        source_dataset_ids=("fixture:ENV-E1-DGS10",),
        parameter_hash="ph-fixture",
        allow_synthetic_hashes=True,
    )
    assert envelope.source_content_hashes
    assert envelope.source_content_hashes[0] == hashlib.sha256(b"fixture:ENV-E1-DGS10").hexdigest()


def test_snapshotLineage_agentOutputsNotSource_rejectsAgentProse() -> None:
    """覆盖范围：来源数据集编号含智能体生成文案时如何拒绝
    测试对象：SnapshotLineageBuilder.build
    目的/目标：智能体生成的文本不得作为数据来源登记进血缘
    验证点：pytest.raises(LineageSnapshotError, match='agent outputs')
    失败含义：智能体文案进入血缘，来源追溯与合规边界失效
    """
    report = ValidationReportRef(
        validation_report_id="vr-agent",
        rule_version="layer1_v1",
        source_fetch_ids_json="[]",
        source_content_hashes_json='["hash"]',
    )
    builder = SnapshotLineageBuilder()
    with pytest.raises(LineageSnapshotError, match="agent outputs"):
        builder.build(
            snapshot_id="snap-agent",
            snapshot_type="axis_feature_snapshot",
            as_of=AS_OF,
            validation_report=report,
            input_window_start=AS_OF - timedelta(days=1),
            input_window_end=AS_OF,
            source_dataset_ids=("agent_summary:建议买入",),
            parameter_hash="ph-agent",
        )


def test_layer1Snapshot_forbiddenSubstitute_blocksWriteWithQualityError(
    tmp_path: Path,
) -> None:
    """覆盖范围：特征含禁止替代标记时，写入快照应被拒绝
    测试对象：Layer1SnapshotWriter.write_features
    目的/目标：使用了禁止替代指标的特征不得写入快照表
    验证点：pytest.raises(LineageSnapshotError, match='forbidden substitute')
    失败含义：违规替代仍持久化，第一层质量门禁被绕过
    """
    db = tmp_path / "layer1_substitute.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    _insert_validation_report(cm, "vr-sub")
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    feat = engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)[0]
    feat = replace(
        feat,
        quality_flags=feat.quality_flags + ("FORBIDDEN_SUBSTITUTE_USED",),
    )
    writer = Layer1SnapshotWriter(cm)
    with pytest.raises(LineageSnapshotError, match="forbidden substitute"):
        writer.write_features(rows=[feat], validation_report_id="vr-sub")


def test_layer1Snapshot_writeLineageViaWriteManager(tmp_path: Path) -> None:
    """覆盖范围：快照血缘经统一写入管理器落库并记审计
    测试对象：Layer1SnapshotWriter.write_lineage
    目的/目标：血缘表与写入审计表均应有成功记录
    验证点：lineage COUNT==1；audit 中 target_table=axis_snapshot_lineage 且 status=SUCCESS
    失败含义：血缘写入无审计，WriteManager 追溯链不完整
    """
    report = ValidationReportRef(
        validation_report_id="vr-lineage-wm",
        rule_version="layer1_v1",
        source_fetch_ids_json='["fetch-1"]',
        source_content_hashes_json='["hash-lineage"]',
    )
    lineage = SnapshotLineageBuilder().build(
        snapshot_id="snap-wm-lineage",
        snapshot_type="axis_feature_snapshot",
        as_of=AS_OF,
        validation_report=report,
        input_window_start=AS_OF - timedelta(days=7),
        input_window_end=AS_OF,
        source_dataset_ids=("ds-wm",),
        parameter_hash="ph-wm",
    )
    cm = _persist_lineage(tmp_path, lineage, report_id="vr-lineage-wm")
    with cm.reader() as con:
        cnt = con.execute(
            "SELECT COUNT(*) FROM axis_snapshot_lineage WHERE snapshot_id = ?",
            ["snap-wm-lineage"],
        ).fetchone()[0]
        audit_cnt = con.execute(
            """
            SELECT COUNT(*) FROM write_audit_log
            WHERE target_table = 'axis_snapshot_lineage' AND status = 'SUCCESS'
            """
        ).fetchone()[0]
    assert cnt == 1
    assert audit_cnt >= 1


def test_layer1Interpretation_writeViaWriteManager(tmp_path: Path) -> None:
    """覆盖范围：解读快照经统一写入管理器落库是否成功
    测试对象：Layer1SnapshotWriter.write_interpretation
    目的/目标：由特征生成的解读行应写入成功，且解读表内恰好一行
    验证点：result.status == SUCCESS；COUNT(*) == 1
    失败含义：解读无法持久化，第一层面板缺自然语言摘要
    """
    db = tmp_path / "layer1_interp_wm.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    _insert_validation_report(cm, "vr-interp")
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    feat = engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)[0]
    interp_rows = AxisInterpretationEngine().build_interpretation(as_of=AS_OF, features=[feat])
    writer = Layer1SnapshotWriter(cm)
    result = writer.write_interpretation(
        rows=interp_rows,
        validation_report_id="vr-interp",
    )
    assert result.status == "SUCCESS"
    with cm.reader() as con:
        cnt = con.execute("SELECT COUNT(*) FROM axis_interpretation_snapshot").fetchone()[0]
    assert cnt == 1
