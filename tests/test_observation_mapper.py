"""把「小批量拉数结果」转成正式观测行时的边界测试。

覆盖范围：拉数成功/失败、原始文件缺失或格式不对时如何拒绝，
以及合法数据如何映射成可入库的观测记录。
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from backend.app.datasources.fetch_result import FetchResult
from backend.app.datasources.route_models import SourceRoutePlan
from backend.app.layer1_axes.ingestion import (
    FROZEN_STAGED_INDICATOR,
    STAGED_DATA_DOMAIN,
    STAGED_OPERATION,
    IngestionRouteBinding,
    MicroFetchResult,
)
from backend.app.layer1_axes.observation_mapper import (
    ObservationMappingError,
    map_micro_fetch_to_observation_row,
    observation_row_to_domain,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PROJECT_ROOT / "tests/fixtures/layer1_macro_observation_fixture.json"


def _binding() -> IngestionRouteBinding:
    return IngestionRouteBinding(
        indicator_id=FROZEN_STAGED_INDICATOR,
        axis_id="environment",
        data_domain=STAGED_DATA_DOMAIN,
        operation=STAGED_OPERATION,
        frequency="daily",
        unit="pct",
        primary_source_declared="akshare",
        validation_source="fred",
        fallback_policy="none",
    )


def _route_plan() -> SourceRoutePlan:
    return SourceRoutePlan(
        route_plan_id="plan-mapper",
        data_domain=STAGED_DATA_DOMAIN,
        operation=STAGED_OPERATION,
        route_status="READY",
        selected_source_id="akshare",
        run_id="run-mapper",
        job_id="job-mapper",
    )


def _micro(
    *,
    status: str = "SUCCESS",
    raw_paths: tuple[str, ...] = (),
    source_id: str = "akshare",
    selected_source: str | None = "akshare",
) -> MicroFetchResult:
    plan = _route_plan()
    if selected_source is not None:
        plan = SourceRoutePlan(
            route_plan_id=plan.route_plan_id,
            data_domain=plan.data_domain,
            operation=plan.operation,
            route_status=plan.route_status,
            selected_source_id=selected_source,
            run_id=plan.run_id,
            job_id=plan.job_id,
        )
    return MicroFetchResult(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=date(2024, 6, 15),
        binding=_binding(),
        route_plan=plan,
        fetch_result=FetchResult(
            run_id="run-mapper",
            source_id=source_id,
            data_domain=STAGED_DATA_DOMAIN,
            status=status,  # type: ignore[arg-type]
            row_count=1 if status == "SUCCESS" else 0,
            fetch_time="2024-06-15T12:00:00Z",
            raw_file_paths=raw_paths,
            content_hash="abc123",
            as_of_timestamp="2024-06-15",
        ),
        run_id="run-mapper",
        job_id="job-mapper",
        fetch_id="fetch-mapper",
        file_registry_ids=(),
        resource_guard_decision="OK",
        resource_guard_reason="",
        staged_fixture_path=str(FIXTURE),
    )


def _write_raw(data_root: Path, rel: str, payload: dict) -> None:
    path = data_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_mapMicroFetch_mapsValidFixturePayload(tmp_path: Path) -> None:
    """覆盖范围：合法原始拉取数据如何映射成可入库观测行
    测试对象：map_micro_fetch_to_observation_row
    目的/目标：冻结指标夹具的数值与来源须正确写入观测行核心字段
    验证点：indicator_id/raw_value/source_used/quality_flags 与夹具一致
    失败含义：合法拉取无法映射，正式提交路径永远无法生成观测行
    """
    rel = "raw/akshare/macro_supplementary/2024-06-15/valid.json"
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    _write_raw(tmp_path, rel, payload)
    row = map_micro_fetch_to_observation_row(
        _micro(raw_paths=(rel,)),
        data_root=tmp_path,
        fixture_path=FIXTURE,
    )
    expected_value = payload["observations"][0]["metric_value"]
    assert row["indicator_id"] == FROZEN_STAGED_INDICATOR
    assert row["raw_value"] == float(expected_value)
    assert row["source_used"] == "akshare"
    assert row["quality_flags"] == "STAGED_FIXTURE"


def test_mapMicroFetch_rejectsNonSuccessStatus(tmp_path: Path) -> None:
    """覆盖范围：拉数失败时，不能把拉取结果转成可入库观测行
    测试对象：map_micro_fetch_to_observation_row
    目的/目标：底层返回失败状态时，映射步骤必须立刻拒绝，不得生成观测记录
    验证点：抛出 ObservationMappingError，消息含 fetch status 'FAILED'
    失败含义：失败拉数仍能进入提交路径，脏数据会写入正式观测表
    """
    base = _micro(raw_paths=("raw/placeholder.json",))
    micro = replace(
        base,
        fetch_result=FetchResult(
            run_id="run-mapper",
            source_id="akshare",
            data_domain=STAGED_DATA_DOMAIN,
            status="FAILED",
            row_count=0,
            fetch_time="2024-06-15T12:00:00Z",
            error_message="simulated failure",
        ),
    )
    with pytest.raises(ObservationMappingError, match="fetch status 'FAILED'"):
        map_micro_fetch_to_observation_row(micro, data_root=tmp_path)


def test_mapMicroFetch_rejectsMissingRawPaths(tmp_path: Path) -> None:
    """覆盖范围：拉数结果未记录原始文件路径时如何拒绝映射
    测试对象：map_micro_fetch_to_observation_row
    目的/目标：没有原始文件落盘路径就无法追溯数据来源，必须拒绝映射
    验证点：抛出 ObservationMappingError，消息含 missing raw_file_paths
    失败含义：无原始路径仍映射成功，血缘与审计链断裂
    """
    micro = _micro(raw_paths=("raw/placeholder.json",))
    empty_fetch = micro.fetch_result.model_copy(update={"raw_file_paths": []})
    micro = replace(micro, fetch_result=empty_fetch)
    with pytest.raises(ObservationMappingError, match="missing raw_file_paths"):
        map_micro_fetch_to_observation_row(micro, data_root=tmp_path)


def test_mapMicroFetch_rejectsMissingRawFile(tmp_path: Path) -> None:
    """覆盖范围：原始文件路径指向磁盘上不存在文件时如何拒绝
    测试对象：map_micro_fetch_to_observation_row
    目的/目标：声明的原始文件必须在数据目录下真实存在，否则不能映射
    验证点：抛出 ObservationMappingError，消息含 raw fetch file missing
    失败含义：幽灵路径也能映射，后续无法校验原始内容
    """
    with pytest.raises(ObservationMappingError, match="raw fetch file missing"):
        map_micro_fetch_to_observation_row(
            _micro(raw_paths=("raw/missing.json",)),
            data_root=tmp_path,
        )


def test_mapMicroFetch_rejectsNonObjectPayload(tmp_path: Path) -> None:
    """覆盖范围：原始 JSON 格式不对（例如是数组而非对象）时如何拒绝
    测试对象：map_micro_fetch_to_observation_row
    目的/目标：观测原始数据必须是 JSON 对象结构，数组等格式一律拒绝
    验证点：抛出 ObservationMappingError，消息含 must be a JSON object
    失败含义：非对象内容被误解析，字段提取会静默出错
    """
    rel = "raw/akshare/macro_supplementary/2024-06-15/bad.json"
    (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / rel).write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ObservationMappingError, match="must be a JSON object"):
        map_micro_fetch_to_observation_row(_micro(raw_paths=(rel,)), data_root=tmp_path)


def test_mapMicroFetch_rejectsEmptyObservations(tmp_path: Path) -> None:
    """覆盖范围：原始文件里观测列表为空时如何拒绝映射
    测试对象：map_micro_fetch_to_observation_row
    目的/目标：至少要有一条有效观测记录才能生成入库行，空列表必须拒绝
    验证点：抛出 ObservationMappingError，消息含 no observations
    失败含义：空列表也能生成观测行，会写入无意义的占位数据
    """
    rel = "raw/akshare/macro_supplementary/2024-06-15/empty.json"
    _write_raw(tmp_path, rel, {"observations": []})
    with pytest.raises(ObservationMappingError, match="no observations"):
        map_micro_fetch_to_observation_row(_micro(raw_paths=(rel,)), data_root=tmp_path)


def test_mapMicroFetch_rejectsMissingMetricValue(tmp_path: Path) -> None:
    """覆盖范围：原始观测条目缺少数值字段时如何拒绝
    测试对象：map_micro_fetch_to_observation_row
    目的/目标：观测数值必须从原始条目明确给出，缺字段时不能猜测或填默认值
    验证点：抛出 ObservationMappingError，消息含 missing metric_value
    失败含义：缺值仍映射，正式观测表会写入空值或错误默认值
    """
    rel = "raw/akshare/macro_supplementary/2024-06-15/no-metric.json"
    _write_raw(tmp_path, rel, {"observations": [{"unit": "pct"}]})
    with pytest.raises(ObservationMappingError, match="missing metric_value"):
        map_micro_fetch_to_observation_row(_micro(raw_paths=(rel,)), data_root=tmp_path)


def test_mapMicroFetch_rejectsFixtureIndicatorMismatch(tmp_path: Path) -> None:
    """覆盖范围：原始文件里的指标编号与当前请求指标不一致时如何拒绝
    测试对象：map_micro_fetch_to_observation_row（带测试夹具校验）
    目的/目标：防止把错误指标的拉取结果映射到当前指标，避免张冠李戴
    验证点：抛出 ObservationMappingError，消息含 indicator_id does not match
    失败含义：指标错配仍写入，第一层面板会展示错误序列
    """
    rel = "raw/akshare/macro_supplementary/2024-06-15/wrong-ind.json"
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["indicator_id"] = "WRONG-ID"
    _write_raw(tmp_path, rel, payload)
    with pytest.raises(ObservationMappingError, match="indicator_id does not match"):
        map_micro_fetch_to_observation_row(
            _micro(raw_paths=(rel,)),
            data_root=tmp_path,
            fixture_path=FIXTURE,
        )


def test_mapMicroFetch_resolvesSourceFromPayloadWhenRouteEmpty(tmp_path: Path) -> None:
    """覆盖范围：路由未选定数据源时，如何从合法原始文件解析数据来源
    测试对象：map_micro_fetch_to_observation_row
    目的/目标：路由没有选中源时，仍应从原始 JSON 中读出数据来源并写入观测行
    验证点：映射结果的 source_used 等于原始文件中的 source_used
    失败含义：合法原始来源无法解析，或错误地拒绝可映射数据
    """
    rel = "raw/akshare/macro_supplementary/2024-06-15/ok.json"
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["source_used"] = "payload_source"
    _write_raw(tmp_path, rel, payload)
    plan = SourceRoutePlan(
        route_plan_id="plan-mapper",
        data_domain=STAGED_DATA_DOMAIN,
        operation=STAGED_OPERATION,
        route_status="READY",
        selected_source_id=None,
        run_id="run-mapper",
        job_id="job-mapper",
    )
    micro = MicroFetchResult(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=date(2024, 6, 15),
        binding=_binding(),
        route_plan=plan,
        fetch_result=FetchResult(
            run_id="run-mapper",
            source_id="",
            data_domain=STAGED_DATA_DOMAIN,
            status="SUCCESS",
            row_count=1,
            fetch_time="2024-06-15T12:00:00Z",
            raw_file_paths=[rel],
            content_hash="abc123",
            as_of_timestamp="2024-06-15",
        ),
        run_id="run-mapper",
        job_id="job-mapper",
        fetch_id="fetch-mapper",
        file_registry_ids=(),
        resource_guard_decision="OK",
        resource_guard_reason="",
        staged_fixture_path=str(FIXTURE),
    )
    row = map_micro_fetch_to_observation_row(micro, data_root=tmp_path, fixture_path=FIXTURE)
    assert row["source_used"] == "payload_source"


def test_mapMicroFetch_rejectsUnresolvedSource(tmp_path: Path) -> None:
    """覆盖范围：路由和原始文件都无法确定数据来源时如何拒绝
    测试对象：map_micro_fetch_to_observation_row
    目的/目标：观测记录的数据来源必须明确，不能留空也不能猜测
    验证点：抛出 ObservationMappingError，消息含 cannot resolve source_used
    失败含义：来源不明的观测仍写入，下游冲突校验与审计无法追溯
    """
    rel = "raw/akshare/macro_supplementary/2024-06-15/ok.json"
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload.pop("source_used", None)
    _write_raw(tmp_path, rel, payload)
    plan = SourceRoutePlan(
        route_plan_id="plan-mapper",
        data_domain=STAGED_DATA_DOMAIN,
        operation=STAGED_OPERATION,
        route_status="READY",
        selected_source_id=None,
        run_id="run-mapper",
        job_id="job-mapper",
    )
    micro = MicroFetchResult(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=date(2024, 6, 15),
        binding=_binding(),
        route_plan=plan,
        fetch_result=FetchResult(
            run_id="run-mapper",
            source_id="",
            data_domain=STAGED_DATA_DOMAIN,
            status="SUCCESS",
            row_count=1,
            fetch_time="2024-06-15T12:00:00Z",
            raw_file_paths=[rel],
            content_hash="abc123",
            as_of_timestamp="2024-06-15",
        ),
        run_id="run-mapper",
        job_id="job-mapper",
        fetch_id="fetch-mapper",
        file_registry_ids=(),
        resource_guard_decision="OK",
        resource_guard_reason="",
        staged_fixture_path=str(FIXTURE),
    )
    with pytest.raises(ObservationMappingError, match="cannot resolve source_used"):
        map_micro_fetch_to_observation_row(micro, data_root=tmp_path, fixture_path=FIXTURE)


def test_observationRowToDomain_parsesCommaSeparatedFlags() -> None:
    """覆盖范围：从数据库读出的观测行，质量标记字符串如何还原为结构化列表
    测试对象：observation_row_to_domain
    目的/目标：持久化层用逗号拼接的质量标记，读回时应正确拆成元组供业务使用
    验证点：domain.quality_flags 等于 ('STAGED_FIXTURE', 'REVIEW')
    失败含义：质量标记解析错误，特征引擎与质量门禁会误判数据状态
    """
    row = {
        "indicator_id": FROZEN_STAGED_INDICATOR,
        "as_of_timestamp": None,
        "publish_timestamp": None,
        "raw_value": 1.0,
        "source_used": "staged",
        "source_switched": False,
        "quality_flags": "STAGED_FIXTURE,REVIEW",
    }
    domain = observation_row_to_domain(row)
    assert domain.quality_flags == ("STAGED_FIXTURE", "REVIEW")
