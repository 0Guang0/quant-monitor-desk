"""R3-DCP-03 — post-write inspect after 2× baostock incremental."""

from __future__ import annotations

import json

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.ops.data_health_profiles import run_data_health_profile
from backend.app.ops.db_inspector import DbInspector
from backend.app.sync.watermark import compute_incremental_window, read_bar_trade_date_watermark

from tests.incremental_baostock_support import (
    FIXTURE_DATE,
    SYMBOL,
    bootstrap_db,
    build_service,
    incremental_spec,
    seed_watermark_row,
)
from tests.post_write_inspect_support import (
    build_evidence_bundle_from_fetch_log,
    run_two_incremental,
)
from tests.support.qmd_ops_cli import run_qmd_db_inspect_cli


def _security_bar_table(report) -> dict:
    table = next(t for t in report.key_tables if t["name"] == "security_bar_1d")
    assert table["exists"] is True, "security_bar_1d missing from Inspector key_tables"
    return table


def test_postWriteInspect_twoIncremental_rowCountStable(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：2× baostock incremental 写后 DbInspector 行数稳定
    测试对象：DbInspector.inspect key_tables.security_bar_1d.row_count
    目的/目标：写后抽检应通过 Inspector 报告字段证明行数不随重复增量膨胀
    验证点：两次 inspect 的 security_bar_1d.row_count 相等；max(trade_date) ≥ fixture 日
    失败含义：写后巡检无法证明幂等落库，Wave 3 生产入口缺 gate
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = bootstrap_db(tmp_path)
    with cm.writer() as con:
        seed_watermark_row(con, "2024-06-24")
        wm = read_bar_trade_date_watermark(con, instrument_id=SYMBOL)
    window = compute_incremental_window(wm, end=FIXTURE_DATE)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    service, orch = build_service(cm, raw_root)
    kwargs = dict(
        datasource_service=service,
        clean_table="security_bar_1d",
        write_mode="upsert_by_pk",
        primary_keys=("instrument_id", "trade_date", "adjustment_type"),
    )
    r1 = orch.run_incremental(incremental_spec(window, job_id="job-pwi-inspect-1"), **kwargs)
    assert r1.status == "COMPLETED"
    report_before = DbInspector(cm.db_path, raw_root).inspect()
    table_before = _security_bar_table(report_before)
    assert table_before["row_count"] is not None

    r2 = orch.run_incremental(incremental_spec(window, job_id="job-pwi-inspect-2"), **kwargs)
    assert r2.status == "COMPLETED"
    report_after = DbInspector(cm.db_path, raw_root).inspect()
    table_after = _security_bar_table(report_after)
    assert table_after["row_count"] == table_before["row_count"]

    with ConnectionManager(cm.db_path).reader() as con:
        max_date = con.execute(
            "SELECT MAX(trade_date) FROM security_bar_1d WHERE instrument_id = ?",
            [SYMBOL],
        ).fetchone()[0]
    assert max_date is not None
    assert str(max_date) >= FIXTURE_DATE.isoformat()


def test_postWriteHealth_twoIncremental_marketBarP0(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：2× incremental 后从 fetch_log 组 evidence bundle 跑 health profile
    测试对象：build_evidence_bundle_from_fetch_log + run_data_health_profile
    目的/目标：写后 health 应消费 incremental 会话产出的 raw 证据而非仅用 good_bundle 夹具
    验证点：run_data_health_profile 无未处理异常；checks 非空；overall_status ∈ {PASS,WARN}
    失败含义：incremental → health 接线断，写后质量 gate 不可用
    """
    cm, _raw_root, _orch = run_two_incremental(tmp_path, monkeypatch)
    bundle_dir = tmp_path / "evidence_bundle"
    build_evidence_bundle_from_fetch_log(cm, bundle_dir)

    report, limitations, _, _, _ = run_data_health_profile(
        profile_id="market_bar_p0",
        domain="market_bar_1d",
        evidence_path=bundle_dir,
        db_path=cm.db_path,
        start_date=None,
        end_date=None,
        max_rows=100,
    )
    assert report.profile == "market_bar_p0"
    assert report.production_db_mutated is False
    assert report.overall_status in {"PASS", "WARN"}
    assert len(report.checks) >= 1
    assert isinstance(limitations, list)


def test_postWriteCli_dbInspect_jsonIncludesSecurityBar1d(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：2× incremental 后 qmd_ops db-inspect JSON smoke
    测试对象：qmd_ops db-inspect CLI
    目的/目标：CLI 只读巡检应 exit 0 且 JSON 含 security_bar_1d
    验证点：returncode==0；key_tables 含 security_bar_1d
    失败含义：运维 CLI 无法验收写后库状态
    """
    cm, raw_root, _orch = run_two_incremental(tmp_path, monkeypatch)

    result = run_qmd_db_inspect_cli(
        "--db",
        str(cm.db_path),
        "--data-root",
        str(raw_root),
        "--format",
        "json",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    names = {t["name"] for t in payload.get("key_tables") or []}
    assert "security_bar_1d" in names
