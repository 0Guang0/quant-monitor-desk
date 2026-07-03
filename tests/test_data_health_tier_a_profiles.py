"""M-DATA-03 S-R2-F0 — four Tier-A data health profile families."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from backend.app.ops.data_health import DataHealthLoadError
from backend.app.ops.data_health_profiles import (
    CRYPTO_DERIVATIVE_P0_RULE_IDS,
    DISCLOSURE_P0_RULE_IDS,
    LAYER1_OBSERVATION_P0_RULE_IDS,
    run_data_health_profile,
)
from backend.app.ops.tier_a_live_acceptance import source_bindings

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_RULES_PATH = _PROJECT_ROOT / "specs" / "contracts" / "data_quality_rules.yaml"
_REPLAY = _PROJECT_ROOT / "tests" / "fixtures" / "replay"
_GOOD_BUNDLE = _PROJECT_ROOT / "tests" / "fixtures" / "data_health" / "good_bundle"

_TIER_A_SOURCES = tuple(source_bindings().keys())


def _copy_replay(src: Path, tmp_path: Path, name: str) -> Path:
    dest = tmp_path / name
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dest / src.name)
    return dest


def test_fourProfileFamilies_registeredInContract() -> None:
    """覆盖范围：四族 profile 契约登记
    测试对象：data_quality_rules.yaml ops_cli_profiles + live_tier_a_evidence_v1
    目的/目标：S-R2-F0 AC — 四族 profile ID 在契约中可解析
    验证点：market_bar / layer1 / disclosure / crypto 域存在；11 源 binding 含 health_profile_id
    失败含义：profile 族与 source_bindings 漂移，F0 无法按源路由
    """
    raw = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8")) or {}
    profiles = raw.get("ops_cli_profiles") or {}
    assert "market_bar_1d" in profiles
    assert "layer1_observation" in profiles
    assert "us_disclosure" in profiles
    assert "crypto_derivative" in profiles
    bindings = source_bindings()
    assert len(bindings) == 11
    families = {b["health_profile_id"] for b in bindings.values()}
    assert families == {
        "market_bar_p0",
        "layer1_observation_p0",
        "disclosure_p0",
        "crypto_derivative_p0",
    }


@pytest.mark.parametrize(
    ("fixture_rel", "profile_id", "domain", "rule_ids"),
    [
        (
            "official_macro/fred/dgs10_replay_bundle.json",
            "layer1_observation_p0",
            "layer1_observation",
            LAYER1_OBSERVATION_P0_RULE_IDS,
        ),
        (
            "official_macro/us_treasury/yield_curve_replay_bundle.json",
            "layer1_observation_p0",
            "layer1_observation",
            LAYER1_OBSERVATION_P0_RULE_IDS,
        ),
        (
            "sec_edgar/filings_replay_bundle.json",
            "disclosure_p0",
            "us_disclosure",
            DISCLOSURE_P0_RULE_IDS,
        ),
        (
            "cn_market/cninfo/sh600519_filings_replay.json",
            "disclosure_p0",
            "cn_disclosure",
            DISCLOSURE_P0_RULE_IDS,
        ),
        (
            "crypto_market/deribit/btc_options_surface_replay.json",
            "crypto_derivative_p0",
            "crypto_derivative",
            CRYPTO_DERIVATIVE_P0_RULE_IDS,
        ),
    ],
)
def test_profileRunner_replayFixture_notFailBlocked(
    tmp_path: Path,
    fixture_rel: str,
    profile_id: str,
    domain: str,
    rule_ids: tuple[str, ...],
) -> None:
    """覆盖范围：非 market_bar 三族 replay 夹具
    测试对象：run_data_health_profile
    目的/目标：replay 证据跑 F0 须非 FAIL/BLOCKED
    验证点：overall_status ∉ {FAIL, BLOCKED}；rules_run 覆盖契约 rule ID
    失败含义：profile 实现缺口或证据加载失败
    """
    src = _REPLAY / fixture_rel
    evidence_dir = _copy_replay(src, tmp_path, profile_id)
    report, *_ = run_data_health_profile(
        profile_id=profile_id,
        domain=domain,
        evidence_path=evidence_dir,
        db_path=None,
        start_date=None,
        end_date=None,
        max_rows=100,
    )
    assert report.overall_status not in {"FAIL", "BLOCKED"}
    seen = {c.rule_id for c in report.checks}
    assert set(rule_ids).issubset(seen)


def test_marketBar_standaloneMarketReplay_passes(tmp_path: Path) -> None:
    """覆盖范围：live 增量 market bar JSON（alpha_vantage 两 bar）
    测试对象：run_data_health_profile market_bar_p0
    目的/目标：standalone bar 证据可跑 market_bar_p0 且非 FAIL/BLOCKED
    验证点：overall_status 非 FAIL/BLOCKED
    失败含义：standalone bar 加载未接线
    """
    src = _REPLAY / "market_data/alpha_vantage/aapl_daily_replay.json"
    evidence_dir = _copy_replay(src, tmp_path, "alpha_vantage")
    report, *_ = run_data_health_profile(
        profile_id="market_bar_p0",
        domain="market_bar_1d",
        evidence_path=evidence_dir,
        db_path=None,
        start_date=None,
        end_date=None,
        max_rows=100,
    )
    assert report.overall_status not in {"FAIL", "BLOCKED"}


def test_marketBar_liveAcceptance_skipsRehearsalCloseoutGate(tmp_path: Path) -> None:
    """覆盖范围：F0 方向 B — live 验收不走 R3G staged-only gate
    测试对象：run_data_health_profile market_bar_p0 live_acceptance=True
    目的/目标：Tier A live 报告不得含 staged-only gate_rationale（AC-5）
    验证点：gate_rationale 为空；overall_status 非 FAIL/BLOCKED
    失败含义：行情源 F0 仍依赖彩排 closeout，与宏观源双标准
    """
    src = _REPLAY / "market_data/alpha_vantage/aapl_daily_replay.json"
    evidence_dir = _copy_replay(src, tmp_path, "alpha_vantage")
    report, *_ = run_data_health_profile(
        profile_id="market_bar_p0",
        domain="market_bar_1d",
        evidence_path=evidence_dir,
        db_path=None,
        start_date=None,
        end_date=None,
        max_rows=100,
        live_acceptance=True,
    )
    assert report.overall_status not in {"FAIL", "BLOCKED"}
    assert "staged-only" not in (report.gate_rationale or "").lower()


def test_layer1_fredLiveSeriesPayload_notFailBlocked(tmp_path: Path) -> None:
    """覆盖范围：fred live fetch 证据形状
    测试对象：load_layer1 + layer1_observation_p0
    目的/目标：series[].rows live 载荷须可规范化并非 FAIL/BLOCKED
    验证点：overall_status ∈ {PASS, WARN}
    失败含义：live 增量 fred 证据仍被 SKIP/FAIL
    """
    evidence_dir = tmp_path / "fred-live"
    evidence_dir.mkdir()
    payload = {
        "source_id": "fred",
        "series": [
            {
                "series_id": "DGS10",
                "source_fetch_id": "live-1",
                "content_hash": "hash-live",
                "as_of_timestamp": "2026-07-03T12:00:00Z",
                "rows": [
                    {"observation_date": "2026-07-01", "value": "4.40"},
                    {"observation_date": "2026-07-02", "value": "4.41"},
                ],
            }
        ],
    }
    (evidence_dir / "live.json").write_text(json.dumps(payload), encoding="utf-8")
    report, *_ = run_data_health_profile(
        profile_id="layer1_observation_p0",
        domain="layer1_observation",
        evidence_path=evidence_dir,
        db_path=None,
        start_date=None,
        end_date=None,
        max_rows=100,
    )
    assert report.overall_status in {"PASS", "WARN"}


def test_f0_nestedRawStorePath_findsEvidenceDir(tmp_path: Path) -> None:
    """覆盖范围：RawStore 嵌套 raw/{source}/raw/{source} 路径
    测试对象：_latest_raw_evidence_dir
    目的/目标：live 增量落盘嵌套路径时 F0 可定位证据目录
    验证点：返回含 JSON 的日期目录；fred 不串源
    失败含义：live manifest/F0 误报 no raw evidence 或跨源污染
    """
    from backend.app.ops.tier_a_live_acceptance import (
        _latest_raw_evidence_dir,
        ensure_isolated_db,
        _run_f0_data_health,
    )

    data_root = tmp_path / "sandbox"
    nested = (
        data_root
        / "raw"
        / "baostock"
        / "raw"
        / "baostock"
        / "cn_equity_daily_bar"
        / "2026-07-03"
    )
    nested.mkdir(parents=True)
    payload = {
        "schema_version": "cn_market_evidence_v1",
        "source_id": "baostock",
        "bars": [{"symbol": "sh.600000", "trade_date": "2026-06-15", "close": 10.5}],
    }
    (nested / "evidence.json").write_text(json.dumps(payload), encoding="utf-8")
    other = data_root / "raw" / "mootdx" / "raw" / "mootdx" / "cn_equity_daily_bar" / "2026-07-03"
    other.mkdir(parents=True)
    (other / "other.json").write_text('{"source_id":"mootdx"}', encoding="utf-8")

    evidence_dir = _latest_raw_evidence_dir(data_root, "baostock")
    assert evidence_dir is not None
    assert evidence_dir.name == "2026-07-03"
    assert _latest_raw_evidence_dir(data_root, "fred") is None

    db_path = ensure_isolated_db(data_root)
    status, detail = _run_f0_data_health(
        "baostock", data_root=data_root, db_path=db_path
    )
    assert "no raw evidence" not in detail.lower()


def test_f0_noRawEvidence_returnsFail(isolated_live_data_root: Path) -> None:
    """覆盖范围：无 raw 证据 F0 路径
    测试对象：_run_f0_data_health
    目的/目标：S-R2-F0 禁 SKIP — 无证据须 FAIL 非 SKIP
    验证点：status==FAIL；detail 含 no raw evidence
    失败含义：SKIP 路径残留
    """
    from backend.app.ops.tier_a_live_acceptance import _run_f0_data_health, ensure_isolated_db

    db_path = ensure_isolated_db(isolated_live_data_root)
    status, detail = _run_f0_data_health(
        "fred", data_root=isolated_live_data_root, db_path=db_path
    )
    assert status == "FAIL"
    assert "no raw evidence" in detail.lower()


def test_f0_partialFredPayload_returnsFail(tmp_path: Path) -> None:
    """覆盖范围：不完整 fred JSON
    测试对象：_run_f0_data_health
    目的/目标：仅 series_id 的残缺载荷须 FAIL 非 SKIP
    验证点：status==FAIL
    失败含义：partial 证据被 SKIP 放过
    """
    from backend.app.ops.tier_a_live_acceptance import _run_f0_data_health, ensure_isolated_db

    data_root = tmp_path / "data"
    data_root.mkdir()
    raw_dir = data_root / "raw" / "fred" / "2026-07-03"
    raw_dir.mkdir(parents=True)
    (raw_dir / "abc.json").write_text('{"series_id":"DGS10"}', encoding="utf-8")
    db_path = ensure_isolated_db(data_root)
    status, detail = _run_f0_data_health("fred", data_root=data_root, db_path=db_path)
    assert status == "FAIL"
    assert detail


def test_allTierASources_bindingRoutesToSupportedProfile() -> None:
    """覆盖范围：11 源 source_bindings F0 路由
    测试对象：source_bindings health_profile_id / health_domain
    目的/目标：每源映射到已支持的四族之一
    验证点：11 源均在 _TIER_A_SOURCES；profile+domain 组合合法
    失败含义：某源 F0 路由缺失
    """
    supported = {
        "market_bar_p0": {"market_bar_1d"},
        "layer1_observation_p0": {"layer1_observation"},
        "disclosure_p0": {"us_disclosure", "cn_disclosure"},
        "crypto_derivative_p0": {"crypto_derivative"},
    }
    for source_id in _TIER_A_SOURCES:
        binding = source_bindings()[source_id]
        profile = binding["health_profile_id"]
        domain = binding["health_domain"]
        assert profile in supported
        assert domain in supported[profile]


def test_goodBundle_marketBar_stillPasses() -> None:
    """覆盖范围：既有 good_bundle 回归
    测试对象：run_data_health_profile market_bar_p0
    目的/目标：扩展四族后不破坏既有 market_bar 路径
    验证点：good_bundle overall_status 非 BLOCKED
    失败含义：market_bar 回归破坏
    """
    report, *_ = run_data_health_profile(
        profile_id="market_bar_p0",
        domain="market_bar_1d",
        evidence_path=_GOOD_BUNDLE,
        db_path=None,
        start_date=None,
        end_date=None,
        max_rows=100,
    )
    assert report.overall_status not in {"FAIL", "BLOCKED"}


def test_macroStagingPersist_writesRawDiscoverableByF0(tmp_path: Path) -> None:
    """覆盖范围：macro staging adapter raw 落盘
    测试对象：persist_incremental_fetch_payload + _run_f0_data_health
    目的/目标：live incremental 后 F0 能找到 raw JSON（非 no raw evidence）
    验证点：raw 文件存在；F0 status 非 FAIL
    失败含义：staging 旁路仍不写 raw，验收层 F0 必败
    """
    import json
    from types import SimpleNamespace

    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.ops.macro_incremental_common import persist_incremental_fetch_payload
    from backend.app.ops.tier_a_live_acceptance import (
        _iter_source_raw_files,
        _run_f0_data_health,
        ensure_isolated_db,
    )
    from backend.app.storage.raw_store import RawStore
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase

    data_root = tmp_path / "sandbox"
    data_root.mkdir()
    raw_root = data_root / "raw" / "fred"
    raw_root.mkdir(parents=True)
    bundle = {
        "series": [
            {
                "series_id": "DGS10",
                "source_fetch_id": "persist-test",
                "content_hash": "abc123",
                "as_of_timestamp": "2026-07-03T12:00:00Z",
                "retrieved_at": "2026-07-03T12:00:00Z",
                "observations": [
                    {"series_id": "DGS10", "observation_date": "2026-07-01", "value": "4.40"}
                ],
                "rows": [
                    {"series_id": "DGS10", "observation_date": "2026-07-01", "value": "4.40"}
                ],
            }
        ],
        "source_id": "fred",
    }
    payload = SimpleNamespace(
        content=json.dumps(bundle).encode("utf-8"),
        file_type="json",
    )
    req = FetchRequest(
        run_id="run-persist",
        source_id="fred",
        data_domain="macro_series",
        instrument_id="DGS10",
        start_time="2026-07-01",
    )

    class _StubAdapter(SkeletonAdapterBase):
        source_id = "fred"
        supported_domains = frozenset({"macro_series"})

    adapter = _StubAdapter(object(), raw_store=RawStore(raw_root), fetch_port=object())
    persist_incremental_fetch_payload(adapter, payload, req, as_of="2026-07-03")
    assert _iter_source_raw_files(data_root, "fred")
    db_path = ensure_isolated_db(data_root)
    status, detail = _run_f0_data_health("fred", data_root=data_root, db_path=db_path)
    assert status != "FAIL", detail


def test_missingEvidence_raisesLoadError(tmp_path: Path) -> None:
    """覆盖范围：空证据目录
    测试对象：run_data_health_profile layer1
    目的/目标：无 JSON 须 DataHealthLoadError
    验证点：pytest.raises DataHealthLoadError
    失败含义：空目录静默 PASS
    """
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(DataHealthLoadError):
        run_data_health_profile(
            profile_id="layer1_observation_p0",
            domain="layer1_observation",
            evidence_path=empty,
            db_path=None,
            start_date=None,
            end_date=None,
            max_rows=50,
        )
