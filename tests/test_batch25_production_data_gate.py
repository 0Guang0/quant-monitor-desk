"""Batch 2.5 生产数据就绪门禁测试。

覆盖范围：Batch 2.5 Trellis 执行证据、三份 registry 与本地 data/raw、目标 DuckDB
是否仍明确为 staged/fixture，防止措辞漂移被误读为已开放 production-live。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import duckdb
import pytest
from tests.contract_gate_support import PROJECT_ROOT, trellis_task_dir

BATCH25_TASK_SLUG = "06-20-round3-batch2-5-layer1-obs-ingest"
TASK_DIR = trellis_task_dir(BATCH25_TASK_SLUG)
EVIDENCE_DIR = TASK_DIR / "execute-evidence"


def _read_text(path: Path) -> str:
    assert path.is_file(), f"missing evidence file: {path}"
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(_read_text(path))


def _table_count(con: duckdb.DuckDBPyConnection, table_name: str) -> int:
    exists = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = ?
        """,
        [table_name],
    ).fetchone()[0]
    assert exists == 1, f"expected table to exist: {table_name}"
    return int(con.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0])


def _registry_table_row(registry_text: str, item_id: str) -> bool:
    """Match markdown table rows regardless of column padding (prettier-safe)."""
    return bool(re.search(rf"\|\s*{re.escape(item_id)}\s*\|", registry_text))


def test_batch25_deferredItems_documentedInRegistries() -> None:
    """覆盖范围：Batch 2.5 DEFERRED/RESOLVED 项在 registry 与任务证据中的一致登记
    测试对象：三份 registry、batch25-deferred-items.md、final_registry_update.md、ROUND3_BATCH25_PENDING_FIX_REGISTRY
    目的/目标：B2.5-O-05 仍 deferred；B2.5-O-06 已由 Batch 3V migration 009 闭合；历史 task 证据仍可追溯
    验证点：B2.5-O-05 在 audit/unresolved/task_register；B2.5-O-06 在 RESOLVED；resolved 批次含 O-02..O-07；pending 含 R3-B2.75-01
    失败含义：registry 与任务证据脱节，2.5/3V 收尾状态无法被审计追溯
    """
    deferred_ids = ("B2.5-O-05",)
    audit_deferred = _read_text(PROJECT_ROOT / "docs/AUDIT_DEFERRED_REGISTRY.md")
    unresolved = _read_text(PROJECT_ROOT / "docs/UNRESOLVED_ISSUES_REGISTRY.md")
    task_register = _read_text(TASK_DIR / "research/batch25-deferred-items.md")
    final_registry = _read_text(EVIDENCE_DIR / "final_registry_update.md")

    for item_id in deferred_ids:
        assert _registry_table_row(audit_deferred, item_id)
        assert _registry_table_row(unresolved, item_id)
        assert item_id in task_register
        assert "DEFERRED" in task_register or "Deferred" in task_register
        assert item_id in final_registry

    resolved_ids = (
        "B2.5-O-02",
        "B2.5-O-03",
        "B2.5-O-04",
        "B2.5-O-06",
        "B2.5-O-07",
        "B2.5-WIN-PATH-01",
    )
    resolved = _read_text(PROJECT_ROOT / "docs/RESOLVED_ISSUES_REGISTRY.md")
    for item_id in resolved_ids:
        assert item_id in resolved

    pending = _read_text(PROJECT_ROOT / "docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md")
    assert "R3-B2.75-01" in pending


def test_batch25_evidence_is_staged_not_production_live() -> None:
    """覆盖范围：Batch 2.5 执行证据是否明确为 staged/fixture 而非 production-live
    测试对象：MASTER.plan、AUDIT_DEFERRED、phase1/2/4 execute-evidence 工件
    目的/目标：防止把 2.5 执行证据误读为已开放线上行情或已写入生产观测
    验证点：master 标 staged/fixture 与 DEFERRED；phase1 答 No 于 production live；phase2 dry_run 且 fred deferred、路由 akshare；phase4 分类 fixture_or_staged_evidence 且路径在 sandbox/fixture
    失败含义：证据叙事像 live production，正式发版前可能误判数据就绪
    """
    master = _read_text(TASK_DIR / "MASTER.plan.md")
    registry = _read_text(PROJECT_ROOT / "docs/AUDIT_DEFERRED_REGISTRY.md")
    phase1_classification = _read_text(EVIDENCE_DIR / "phase1_data_classification.md")
    phase2 = _read_json(EVIDENCE_DIR / "phase2_route_preview.json")
    phase4 = _read_json(EVIDENCE_DIR / "phase4_clean_write_and_snapshot_evidence.json")

    assert "**staged/fixture**（非 live production）" in master
    assert "B2.5-O-05" in master
    assert "**DEFERRED**" in master
    assert "| B2.5-O-05 |" in registry
    assert "Batch 6" in registry
    assert "Not closed by Batch 2.75 Request 3" in registry

    assert "external_user_auth_required | false" in phase1_classification
    assert "Are data-root files production live vendor ingestion? | **No**" in phase1_classification
    assert "Are DB rows production observation writes?            | **No**" in phase1_classification

    assert phase2["dry_run"] is True
    assert phase2["fred_primary_deferred"] is True
    preview = phase2["previews"][0]
    assert preview["binding"]["primary_source_declared"] == "FRED:DGS10"
    assert preview["binding"]["data_domain"] == "macro_supplementary"
    assert preview["binding"]["operation"] == "fetch_macro_series"
    assert "deferred" in preview["binding"]["staged_route_note"].lower()
    assert preview["route_plan"]["selected_source_id"] == "akshare"

    assert phase4["phase1_baseline_classification"] == "fixture_or_staged_evidence"
    assert ".phase4-clean-write-sandbox" in phase4["evidence_db_path"]
    assert phase4["commit"]["staged_fixture_path"].startswith("tests/fixtures/")
    assert "deferred" in phase4["commit"]["fred_primary_deferred_note"].lower()


def test_current_target_db_has_no_clean_layer1_production_observations() -> None:
    """覆盖范围：当前目标 DuckDB 是否尚无 Layer1 清洁生产观测行
    测试对象：data/duckdb/quant_monitor.duckdb 中 fetch_log 等表行数
    目的/目标：本地目标库不应已被 Batch 2.5  promoted 成生产观测数据
    验证点：fetch_log、validation_report、write_audit_log、axis_* 表 count 均为 0；无库文件则 pytest.skip
    失败含义：目标库已有 Layer1 行，说明 staged 证据可能已写入生产路径
    """
    db_path = PROJECT_ROOT / "data/duckdb/quant_monitor.duckdb"
    if not db_path.is_file():
        pytest.skip("target DB not present; local readiness gate only")

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        assert _table_count(con, "fetch_log") == 0
        assert _table_count(con, "validation_report") == 0
        assert _table_count(con, "write_audit_log") == 0
        assert _table_count(con, "axis_observation") == 0
        assert _table_count(con, "axis_feature_snapshot") == 0
        assert _table_count(con, "axis_interpretation_snapshot") == 0
        assert _table_count(con, "axis_snapshot_lineage") == 0
    finally:
        con.close()


def test_current_raw_data_root_contains_only_staged_batch25_fixture_payloads() -> None:
    """覆盖范围：data/raw 现存文件是否全是 Batch 2.5 staged fixture 载荷
    测试对象：data/raw 下非 .gitkeep 的 JSON 文件
    目的/目标：raw 目录里不应混入 vendor live 拉数残留
    验证点：每文件 JSON 的 source_used==staged_fixture、macro_supplementary、fetch_macro_series、ENV-E1-DGS10、staged_route_note 含 FRED:DGS10 deferred；无文件则 skip
    失败含义：raw 根目录出现非 staged 载荷，本地数据根与 2.5 叙事不一致
    """
    raw_root = PROJECT_ROOT / "data/raw"
    raw_files = sorted(p for p in raw_root.rglob("*") if p.is_file() and p.name != ".gitkeep")
    if not raw_files:
        pytest.skip("no staged raw evidence in data/raw; local readiness gate only")

    for raw_file in raw_files:
        payload = json.loads(raw_file.read_text(encoding="utf-8"))
        assert payload["source_used"] == "staged_fixture"
        assert payload["data_domain"] == "macro_supplementary"
        assert payload["operation"] == "fetch_macro_series"
        assert payload["indicator_id"] == "ENV-E1-DGS10"
        assert "FRED:DGS10 deferred" in payload["staged_route_note"]
