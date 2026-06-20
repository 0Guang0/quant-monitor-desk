"""Focused tests for observation_mapper boundary paths (audit A05-P1-01 / A04-P2-01)."""

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


def test_mapMicroFetch_rejectsNonSuccessStatus(tmp_path: Path) -> None:
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
    micro = _micro(raw_paths=("raw/placeholder.json",))
    empty_fetch = micro.fetch_result.model_copy(update={"raw_file_paths": []})
    micro = replace(micro, fetch_result=empty_fetch)
    with pytest.raises(ObservationMappingError, match="missing raw_file_paths"):
        map_micro_fetch_to_observation_row(micro, data_root=tmp_path)


def test_mapMicroFetch_rejectsMissingRawFile(tmp_path: Path) -> None:
    with pytest.raises(ObservationMappingError, match="raw fetch file missing"):
        map_micro_fetch_to_observation_row(
            _micro(raw_paths=("raw/missing.json",)),
            data_root=tmp_path,
        )


def test_mapMicroFetch_rejectsNonObjectPayload(tmp_path: Path) -> None:
    rel = "raw/akshare/macro_supplementary/2024-06-15/bad.json"
    (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / rel).write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ObservationMappingError, match="must be a JSON object"):
        map_micro_fetch_to_observation_row(_micro(raw_paths=(rel,)), data_root=tmp_path)


def test_mapMicroFetch_rejectsEmptyObservations(tmp_path: Path) -> None:
    rel = "raw/akshare/macro_supplementary/2024-06-15/empty.json"
    _write_raw(tmp_path, rel, {"observations": []})
    with pytest.raises(ObservationMappingError, match="no observations"):
        map_micro_fetch_to_observation_row(_micro(raw_paths=(rel,)), data_root=tmp_path)


def test_mapMicroFetch_rejectsMissingMetricValue(tmp_path: Path) -> None:
    rel = "raw/akshare/macro_supplementary/2024-06-15/no-metric.json"
    _write_raw(tmp_path, rel, {"observations": [{"unit": "pct"}]})
    with pytest.raises(ObservationMappingError, match="missing metric_value"):
        map_micro_fetch_to_observation_row(_micro(raw_paths=(rel,)), data_root=tmp_path)


def test_mapMicroFetch_rejectsFixtureIndicatorMismatch(tmp_path: Path) -> None:
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
