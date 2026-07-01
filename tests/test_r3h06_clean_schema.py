"""R3H-06 clean schema — domain DDL、OHLCV、cninfo 形、域路由与幂等。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import duckdb
import pytest

from backend.app.db.migrate import MIGRATIONS_DIR, apply_migrations

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = PROJECT_ROOT / "specs/schema/schema.sql"
MIGRATION_013 = MIGRATIONS_DIR / "013_clean_domain_tables.sql"
FRED_AUTH = PROJECT_ROOT / ".audit-sandbox/round3g/fred_user_authorization.yaml"
FRED_EVIDENCE = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/fred"


def _table_columns_from_pragma(con, table: str) -> set[str]:
    return {row[1] for row in con.execute(f"PRAGMA table_info('{table}')").fetchall()}


def _table_columns_from_sql(sql_text: str, table: str) -> set[str] | None:
    pattern = rf"CREATE TABLE IF NOT EXISTS {re.escape(table)}\s*\((.*?)\);"
    match = re.search(pattern, sql_text, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    columns: set[str] = set()
    for line in match.group(1).splitlines():
        line = line.strip().rstrip(",")
        if not line or line.upper().startswith(("PRIMARY", "UNIQUE", "FOREIGN", "CONSTRAINT")):
            continue
        columns.add(line.split()[0].strip('"'))
    return columns


def test_r3h06_bootShell_moduleLoads() -> None:
    """覆盖范围：R3H-06 测试模块引导
    测试对象：tests.test_r3h06_clean_schema 模块
    目的/目标：Execute 9.0 boot 空壳可 import、pytest 可发现
    验证点：本模块 __name__ 含 test_r3h06
    失败含义：boot 模块不可发现则后续 §9 步骤无法挂测
    """
    import tests.test_r3h06_clean_schema as mod

    assert "test_r3h06" in mod.__name__


def test_bar_ddl_migration013_createsBarTables() -> None:
    """覆盖范围：013 bar 域 DDL
    测试对象：apply_migrations 后的 instrument_registry、security_bar_1d
    目的/目标：AC-SCHEMA-G3G4-BAR — bar 表存在且 PK 含 adjustment_type
    验证点：两表存在；security_bar_1d PK 列包含 adjustment_type
    失败含义：bar 域无正式 PK 表则 Wave 3 promote 仍被 schema 阻塞
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert "instrument_registry" in tables
    assert "security_bar_1d" in tables
    pk_cols = {
        row[1]
        for row in con.execute("PRAGMA table_info('security_bar_1d')").fetchall()
        if row[5]
    }
    assert "adjustment_type" in pk_cols
    assert "instrument_id" in pk_cols
    assert "trade_date" in pk_cols


def test_bar_ddl_schemaContract_alignsWithMigration013() -> None:
    """覆盖范围：013 与 schema.sql bar 表列契约
    测试对象：instrument_registry、security_bar_1d
    目的/目标：迁移列集合为 schema 契约子集
    验证点：mig_cols ⊆ contract_cols（PRAGMA 对照）
    失败含义：migration 与 schema.sql 漂移导致契约测试与运行时列不一致
    """
    assert MIGRATION_013.is_file()
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    mig_text = MIGRATION_013.read_text(encoding="utf-8")
    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")
    for table in ("instrument_registry", "security_bar_1d"):
        mig_cols = _table_columns_from_sql(mig_text, table)
        pragma_cols = _table_columns_from_pragma(con, table)
        contract_cols = _table_columns_from_sql(schema_text, table)
        assert mig_cols and contract_cols and pragma_cols
        assert mig_cols.issubset(contract_cols), f"{table}: {mig_cols - contract_cols}"
        assert mig_cols.issubset(pragma_cols), f"{table}: {mig_cols - pragma_cols}"


CN_ANNOUNCEMENT_COLUMNS = frozenset(
    {
        "announcement_id",
        "instrument_id",
        "title",
        "publish_timestamp",
        "announcement_url",
        "announcement_type",
        "data_domain",
        "source_used",
        "pdf_file_id",
        "extracted_text_file_id",
        "content_status",
        "batch_id",
        "source_fetch_id",
        "content_hash",
        "schema_hash",
        "quality_flags",
        "created_at",
    }
)

CAPABILITY_BASE_FIELDS = frozenset(
    {
        "announcement_id",
        "instrument_id",
        "title",
        "publish_timestamp",
        "url",
        "source_used",
    }
)


def test_disclosure_ddl_cnAnnouncementClean_hasSection61Columns() -> None:
    """覆盖范围：cn_announcement_clean §6.1 全列
    测试对象：013 migration + schema.sql cn_announcement_clean
    目的/目标：AC-CNINFO-SHAPE — 公告形 DDL 列齐全
    验证点：§6.1 列集合 ⊆ 实际 DDL 列
    失败含义：cninfo clean 缺列则 metadata 指针与 capabilities 无法对齐
    """
    mig_text = MIGRATION_013.read_text(encoding="utf-8")
    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")
    mig_cols = _table_columns_from_sql(mig_text, "cn_announcement_clean")
    contract_cols = _table_columns_from_sql(schema_text, "cn_announcement_clean")
    assert mig_cols and contract_cols
    assert CN_ANNOUNCEMENT_COLUMNS.issubset(mig_cols)
    assert CN_ANNOUNCEMENT_COLUMNS.issubset(contract_cols)


def test_disclosure_ddl_capabilitiesBaseFields_subsetOfDdl() -> None:
    """覆盖范围：capabilities cn_announcements 基字段 ⊆ DDL
    测试对象：cn_announcement_clean 列名（url→announcement_url 映射）
    目的/目标：registry capabilities 基字段可在 clean 表落列
    验证点：capabilities 字段除 url 外直接存在；url 映射 announcement_url
    失败含义：capabilities 与 DDL 脱节则 promote 字段无处落盘
    """
    mig_cols = _table_columns_from_sql(
        MIGRATION_013.read_text(encoding="utf-8"), "cn_announcement_clean"
    )
    assert mig_cols
    for field in CAPABILITY_BASE_FIELDS:
        if field == "url":
            assert "announcement_url" in mig_cols
        else:
            assert field in mig_cols


def test_disclosure_ddl_stgDisclosureSmoke_exists() -> None:
    """覆盖范围：stg_disclosure_smoke staging 表
    测试对象：013 migration
    目的/目标：公告 promote 有专用 staging 表
    验证点：stg_disclosure_smoke 存在且列与 cn_announcement_clean 一致
    失败含义：disclosure staging 缺失则 cninfo promote 无法走专用路径
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert "stg_disclosure_smoke" in tables
    clean_cols = [
        row[1] for row in con.execute("PRAGMA table_info('cn_announcement_clean')").fetchall()
    ]
    stg_cols = [
        row[1] for row in con.execute("PRAGMA table_info('stg_disclosure_smoke')").fetchall()
    ]
    assert clean_cols == stg_cols


def test_ohlcv_stgFoundationSmoke_hasOhlcvColumns() -> None:
    """覆盖范围：014 stg_foundation_smoke OHLCV 列
    测试对象：apply_migrations 后 stg_foundation_smoke PRAGMA
    目的/目标：AC-SCHEMA-G4-OHLCV — staging 含 open/high/low/volume/adjustment_type
    验证点：OHLCV 列存在且与 security_bar_1d 列序一致
    失败含义：staging 无 OHLCV 则 bar promote 仍只有 close 单列
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    stg_cols = [row[1] for row in con.execute("PRAGMA table_info('stg_foundation_smoke')").fetchall()]
    bar_cols = [row[1] for row in con.execute("PRAGMA table_info('security_bar_1d')").fetchall()]
    assert stg_cols == bar_cols
    for col in ("open", "high", "low", "volume", "adjustment_type"):
        assert col in stg_cols


def test_ohlcv_populateStaging_passesAdjustmentType() -> None:
    """覆盖范围：populate_staging_from_bundle OHLCV 传递
    测试对象：baostock fixture → stg_foundation_smoke
    目的/目标：staging 行携带 adjustment_type 默认 none
    验证点：INSERT 后 adjustment_type='none' 且 open/high/low 有值
    失败含义：adjustment_type 未传递则 PK upsert 语义错误
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
        load_rehearsal_bundle,
        populate_staging_from_bundle,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import load_candidate_set

    candidate = next(c for c in load_candidate_set("r3g_p0") if c.source_id == "baostock")
    bundle = load_rehearsal_bundle(candidate, dry_run=True)
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    populate_staging_from_bundle(con, bundle, batch_id="t", max_rows=10)
    row = con.execute(
        "SELECT open, high, low, close, adjustment_type FROM stg_foundation_smoke LIMIT 1"
    ).fetchone()
    assert row is not None
    assert row[4] == "none"
    assert row[0] is not None and row[3] is not None


def test_stg_disclosure_populate_mapsFilingIdToAnnouncementId() -> None:
    """覆盖范围：populate_disclosure_from_bundle
    测试对象：cninfo manifest → stg_disclosure_smoke
    目的/目标：filing_id 形合成键归一化为 announcement_id
    验证点：announcement_id 非空；content_status=metadata_only
    失败含义：filing_id 未归一化则 disclosure PK 与 capabilities 不一致
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
        load_rehearsal_bundle,
        populate_disclosure_from_bundle,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import load_candidate_set

    candidate = next(c for c in load_candidate_set("r3g_p0") if c.source_id == "cninfo")
    bundle = load_rehearsal_bundle(candidate, dry_run=True)
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    count = populate_disclosure_from_bundle(con, bundle, batch_id="t", max_rows=10)
    assert count > 0
    rows = con.execute(
        "SELECT announcement_id, content_status FROM stg_disclosure_smoke"
    ).fetchall()
    assert all(r[0] for r in rows)
    assert all(r[1] == "metadata_only" for r in rows)


def test_domain_router_resolvesThreeDomains() -> None:
    """覆盖范围：clean_write_targets 三域路由
    测试对象：resolve_clean_write_target
    目的/目标：bar/cninfo/fred 分别指向三张 clean 表 + upsert_by_pk
    验证点：表名与 write_mode、PK 符合冻结卡
    失败含义：域路由错误则三源仍同表或 append 叠行
    """
    from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target

    bar = resolve_clean_write_target("cn_equity_daily_bar")
    assert bar.target_table == "security_bar_1d"
    assert bar.write_mode == "upsert_by_pk"
    assert "adjustment_type" in bar.primary_keys

    disc = resolve_clean_write_target("cn_announcements")
    assert disc.target_table == "cn_announcement_clean"
    assert disc.primary_keys == ("announcement_id",)

    macro = resolve_clean_write_target("macro_series")
    assert macro.target_table == "axis_observation"
    assert macro.primary_keys == ("observation_id",)


def test_cninfo_no_bar_promote_leavesSecurityBar1dEmpty(tmp_path: Path) -> None:
    """覆盖范围：cninfo promote 负向 — 不写 bar 表
    测试对象：run_limited_production_entry execute（cninfo）
    目的/目标：AC-CNINFO-NO-BAR — security_bar_1d 行数不变
    验证点：promote 前后 security_bar_1d COUNT 均为 0；cn_announcement_clean > 0
    失败含义：cninfo 仍写 bar 表则 G5/CNINFO-SHAPE 未闭合
    """
    import json
    import yaml

    from backend.app.db.connection import ConnectionManager
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        PromoteRequest,
        build_before_proof,
        run_limited_production_entry,
    )
    from backend.app.ops.sandbox_clean_write.rollback_plan import (
        build_rollback_plan,
        write_rollback_plan,
    )
    from backend.app.ops.sandbox_clean_write.approval_contract import validate_approval_contract
    from tests.test_round3g_limited_production_clean_write import _audit_sandbox_promote_db

    prod_db = _audit_sandbox_promote_db(tmp_path)
    evidence = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01"
    approval = {
        "approval_id": "r3h06-cninfo-no-bar",
        "approver": "test",
        "approved_at": "2026-06-29",
        "audit_decision_file": "audit.json",
        "production_db_path": str(prod_db),
        "rollback_plan_path": "rollback.json",
        "rollback_required": True,
        "no_agent_triggered_write": True,
        "no_cap_expansion": True,
        "source_candidates": [
            {
                "source_id": "cninfo",
                "domain": "cn_announcements",
                "symbols": ["sh.600519"],
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "max_rows": 10,
                "target_table": "cn_announcement_clean",
                "metadata_only": True,
            }
        ],
    }
    audit = {
        "decision": "PASS_ALLOW_LIMITED_PROD_WRITE",
        "production_db_path": str(prod_db),
        "source_id": "cninfo",
        "domain": "cn_announcements",
        "symbols": ["sh.600519"],
        "start_date": "2024-01-01",
        "end_date": "2024-03-31",
        "max_rows": 10,
        "target_table": "cn_announcement_clean",
    }
    approval_path = tmp_path / "approval.yaml"
    audit_path = tmp_path / "audit.json"
    before_path = tmp_path / "before.json"
    rollback_path = tmp_path / "rollback.json"
    after_path = tmp_path / "after.json"
    approval["audit_decision_file"] = audit_path.as_posix()
    approval["rollback_plan_path"] = rollback_path.as_posix()
    approval_path.write_text(yaml.dump(approval), encoding="utf-8")
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    contract, _, candidate = validate_approval_contract(approval_path, audit_path)
    before = build_before_proof(
        prod_db,
        candidate,
        backup_or_snapshot_pointer=".audit-sandbox/round3g/pytest/cninfo_backup.duckdb",
    )
    before_path.write_text(json.dumps(before), encoding="utf-8")
    rollback = build_rollback_plan(contract, candidate, before_proof=before)
    write_rollback_plan(rollback_path, rollback)

    run_limited_production_entry(
        PromoteRequest(
            approval_file=approval_path,
            audit_decision=audit_path,
            before_proof=before_path,
            after_proof=after_path,
            rollback_plan=rollback_path,
            evidence_dir=evidence,
            dry_run=False,
            execute=True,
        )
    )
    cm = ConnectionManager(prod_db)
    with cm.reader() as con:
        bar_count = con.execute("SELECT COUNT(*) FROM security_bar_1d").fetchone()[0]
        ann_count = con.execute("SELECT COUNT(*) FROM cn_announcement_clean").fetchone()[0]
    assert bar_count == 0
    assert ann_count > 0


def test_idempotency_duplicatePromote_rowCountStable(tmp_path: Path) -> None:
    """覆盖范围：真实 promote 重复 execute 幂等
    测试对象：run_limited_production_entry execute ×2（baostock）
    目的/目标：AC-G6-IDEMPOTENCY — upsert_by_pk 行数不增长
    验证点：第二次 execute 后 security_bar_1d COUNT 不变
    失败含义：重复 promote 叠行则 G6 幂等未闭合
    """
    import json
    import yaml

    from backend.app.db.connection import ConnectionManager
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        PromoteRequest,
        build_before_proof,
        run_limited_production_entry,
    )
    from backend.app.ops.sandbox_clean_write.rollback_plan import (
        build_rollback_plan,
        write_rollback_plan,
    )
    from backend.app.ops.sandbox_clean_write.approval_contract import validate_approval_contract
    from tests.test_round3g_limited_production_clean_write import _audit_sandbox_promote_db

    prod_db = _audit_sandbox_promote_db(tmp_path)
    evidence = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01"
    approval = {
        "approval_id": "r3h06-idem",
        "approver": "test",
        "approved_at": "2026-06-29",
        "audit_decision_file": "audit.json",
        "production_db_path": str(prod_db),
        "rollback_plan_path": "rollback.json",
        "rollback_required": True,
        "no_agent_triggered_write": True,
        "no_cap_expansion": True,
        "source_candidates": [
            {
                "source_id": "baostock",
                "domain": "cn_equity_daily_bar",
                "symbols": ["sh.600519"],
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "max_rows": 10,
                "target_table": "security_bar_1d",
                "metadata_only": False,
            }
        ],
    }
    audit = {
        "decision": "PASS_ALLOW_LIMITED_PROD_WRITE",
        "production_db_path": str(prod_db),
        "source_id": "baostock",
        "domain": "cn_equity_daily_bar",
        "symbols": ["sh.600519"],
        "start_date": "2024-01-01",
        "end_date": "2024-03-31",
        "max_rows": 10,
        "target_table": "security_bar_1d",
    }
    approval_path = tmp_path / "approval.yaml"
    audit_path = tmp_path / "audit.json"
    before_path = tmp_path / "before.json"
    rollback_path = tmp_path / "rollback.json"
    after_path = tmp_path / "after.json"
    approval["audit_decision_file"] = audit_path.as_posix()
    approval["rollback_plan_path"] = rollback_path.as_posix()
    approval_path.write_text(yaml.dump(approval), encoding="utf-8")
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    contract, _, candidate = validate_approval_contract(approval_path, audit_path)
    before = build_before_proof(
        prod_db,
        candidate,
        backup_or_snapshot_pointer=".audit-sandbox/round3g/pytest/idem_backup.duckdb",
    )
    before_path.write_text(json.dumps(before), encoding="utf-8")
    rollback = build_rollback_plan(contract, candidate, before_proof=before)
    write_rollback_plan(rollback_path, rollback)

    req = PromoteRequest(
        approval_file=approval_path,
        audit_decision=audit_path,
        before_proof=before_path,
        after_proof=after_path,
        rollback_plan=rollback_path,
        evidence_dir=evidence,
        dry_run=False,
        execute=True,
    )
    run_limited_production_entry(req)
    cm = ConnectionManager(prod_db)
    with cm.reader() as con:
        count1 = con.execute("SELECT COUNT(*) FROM security_bar_1d").fetchone()[0]
    assert count1 > 0
    run_limited_production_entry(req)
    with cm.reader() as con:
        count2 = con.execute("SELECT COUNT(*) FROM security_bar_1d").fetchone()[0]
    assert count2 == count1


def _build_promote_request(
    tmp_path: Path,
    *,
    source_id: str,
    domain: str,
    target_table: str,
    symbols: list[str],
    approval_id: str,
    metadata_only: bool = False,
    fred_authorization: Path | None = None,
) -> tuple[Any, Any]:
    """Shared promote fixture for R3H-06 E2E tests."""
    import json
    import yaml

    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        PromoteRequest,
        build_before_proof,
    )
    from backend.app.ops.sandbox_clean_write.rollback_plan import (
        build_rollback_plan,
        write_rollback_plan,
    )
    from backend.app.ops.sandbox_clean_write.approval_contract import validate_approval_contract
    from tests.test_round3g_limited_production_clean_write import _audit_sandbox_promote_db

    prod_db = _audit_sandbox_promote_db(tmp_path)
    evidence = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01"
    approval = {
        "approval_id": approval_id,
        "approver": "test",
        "approved_at": "2026-06-29",
        "audit_decision_file": "audit.json",
        "production_db_path": str(prod_db),
        "rollback_plan_path": "rollback.json",
        "rollback_required": True,
        "no_agent_triggered_write": True,
        "no_cap_expansion": True,
        "source_candidates": [
            {
                "source_id": source_id,
                "domain": domain,
                "symbols": symbols,
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "max_rows": 10,
                "target_table": target_table,
                "metadata_only": metadata_only,
            }
        ],
    }
    audit = {
        "decision": "PASS_ALLOW_LIMITED_PROD_WRITE",
        "production_db_path": str(prod_db),
        "source_id": source_id,
        "domain": domain,
        "symbols": symbols,
        "start_date": "2024-01-01",
        "end_date": "2024-03-31",
        "max_rows": 10,
        "target_table": target_table,
    }
    approval_path = tmp_path / f"{approval_id}-approval.yaml"
    audit_path = tmp_path / f"{approval_id}-audit.json"
    before_path = tmp_path / f"{approval_id}-before.json"
    rollback_path = tmp_path / f"{approval_id}-rollback.json"
    after_path = tmp_path / f"{approval_id}-after.json"
    approval["audit_decision_file"] = audit_path.as_posix()
    approval["rollback_plan_path"] = rollback_path.as_posix()
    approval_path.write_text(yaml.dump(approval), encoding="utf-8")
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    contract, _, candidate = validate_approval_contract(approval_path, audit_path)
    before = build_before_proof(
        prod_db,
        candidate,
        backup_or_snapshot_pointer=f".audit-sandbox/round3g/pytest/{approval_id}_backup.duckdb",
    )
    before_path.write_text(json.dumps(before), encoding="utf-8")
    rollback = build_rollback_plan(contract, candidate, before_proof=before)
    write_rollback_plan(rollback_path, rollback)
    req = PromoteRequest(
        approval_file=approval_path,
        audit_decision=audit_path,
        before_proof=before_path,
        after_proof=after_path,
        rollback_plan=rollback_path,
        evidence_dir=evidence,
        dry_run=False,
        execute=True,
        fred_authorization=fred_authorization,
    )
    from backend.app.db.connection import ConnectionManager

    return req, ConnectionManager(prod_db)


def test_macro_populate_fromBundle_writesAxisObservationStaging() -> None:
    """覆盖范围：populate_macro_from_bundle macro staging
    测试对象：fred fixture → stg_axis_observation_smoke
    目的/目标：AC-SCHEMA-G3-ROUTER macro 映射 — indicator_id/raw_value 落 staging
    验证点：行数>0；indicator_id=DGS10；security_bar_1d 无行
    失败含义：fred 仍走 bar 形 staging 则 macro 域未闭合
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
        load_rehearsal_bundle,
        populate_macro_from_bundle,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import load_candidate_set

    candidate = next(c for c in load_candidate_set("r3g_p0") if c.source_id == "fred")
    bundle = load_rehearsal_bundle(candidate, dry_run=True)
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    count = populate_macro_from_bundle(con, bundle, batch_id="t", max_rows=10)
    assert count > 0
    row = con.execute(
        "SELECT indicator_id, raw_value FROM stg_axis_observation_smoke LIMIT 1"
    ).fetchone()
    assert row is not None
    assert row[0] == "DGS10"
    assert row[1] is not None
    bar_count = con.execute("SELECT COUNT(*) FROM security_bar_1d").fetchone()[0]
    assert bar_count == 0


def test_fred_promote_execute_writesAxisObservation_notBar(tmp_path: Path) -> None:
    """覆盖范围：fred promote execute E2E
    测试对象：run_limited_production_entry execute（fred/macro）
    目的/目标：macro promote 写入 axis_observation 且不写 security_bar_1d
    验证点：axis_observation>0；indicator_id 在批准序列；bar COUNT=0
    失败含义：_non_target_row_count 或 macro 路由错误则 promote 崩溃或写错表
    """
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        run_limited_production_entry,
    )

    req, cm = _build_promote_request(
        tmp_path,
        source_id="fred",
        domain="macro_series",
        target_table="axis_observation",
        symbols=["DGS10"],
        approval_id="r3h06-fred-promote",
        fred_authorization=FRED_AUTH,
    )
    run_limited_production_entry(req)
    with cm.reader() as con:
        bar_count = con.execute("SELECT COUNT(*) FROM security_bar_1d").fetchone()[0]
        obs_count = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
        indicators = {
            row[0]
            for row in con.execute(
                "SELECT DISTINCT indicator_id FROM axis_observation"
            ).fetchall()
        }
    assert bar_count == 0
    assert obs_count > 0
    assert indicators == {"DGS10"}


def test_idempotency_baostock_promote_ohlcvColumnsNotNull(tmp_path: Path) -> None:
    """覆盖范围：baostock promote 后 OHLCV clean 列
    测试对象：run_limited_production_entry execute（baostock）
    目的/目标：AC-SCHEMA-G4-OHLCV — promote 后 security_bar_1d OHLCV 非空
    验证点：open/high/low/close/volume IS NOT NULL
    失败含义：仅 close 写入 clean 则 G4 未闭合
    """
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        run_limited_production_entry,
    )

    req, cm = _build_promote_request(
        tmp_path,
        source_id="baostock",
        domain="cn_equity_daily_bar",
        target_table="security_bar_1d",
        symbols=["sh.600519"],
        approval_id="r3h06-ohlcv",
    )
    run_limited_production_entry(req)
    with cm.reader() as con:
        row = con.execute(
            "SELECT open, high, low, close, volume FROM security_bar_1d LIMIT 1"
        ).fetchone()
    assert row is not None
    assert all(v is not None for v in row)


def test_idempotency_cninfo_duplicatePromote_rowCountStable(tmp_path: Path) -> None:
    """覆盖范围：cninfo 重复 promote 幂等
    测试对象：run_limited_production_entry execute ×2（cninfo）
    目的/目标：AC-G6-IDEMPOTENCY disclosure 域 upsert 行数不增长
    验证点：两次 execute 后 cn_announcement_clean COUNT 不变
    失败含义：披露域 append 叠行则 G6 未闭合
    """
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        run_limited_production_entry,
    )

    req, cm = _build_promote_request(
        tmp_path,
        source_id="cninfo",
        domain="cn_announcements",
        target_table="cn_announcement_clean",
        symbols=["sh.600519"],
        approval_id="r3h06-cninfo-idem",
        metadata_only=True,
    )
    run_limited_production_entry(req)
    with cm.reader() as con:
        count1 = con.execute("SELECT COUNT(*) FROM cn_announcement_clean").fetchone()[0]
    assert count1 > 0
    run_limited_production_entry(req)
    with cm.reader() as con:
        count2 = con.execute("SELECT COUNT(*) FROM cn_announcement_clean").fetchone()[0]
    assert count2 == count1


def test_idempotency_fred_duplicatePromote_rowCountStable(tmp_path: Path) -> None:
    """覆盖范围：fred 重复 promote 幂等
    测试对象：run_limited_production_entry execute ×2（fred）
    目的/目标：AC-G6-IDEMPOTENCY macro 域 upsert 行数不增长
    验证点：两次 execute 后 axis_observation COUNT 不变
    失败含义：macro 域叠行或 indicator_id 路由错误则 G6 未闭合
    """
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        run_limited_production_entry,
    )

    req, cm = _build_promote_request(
        tmp_path,
        source_id="fred",
        domain="macro_series",
        target_table="axis_observation",
        symbols=["DGS10"],
        approval_id="r3h06-fred-idem",
        fred_authorization=FRED_AUTH,
    )
    run_limited_production_entry(req)
    with cm.reader() as con:
        count1 = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert count1 > 0
    run_limited_production_entry(req)
    with cm.reader() as con:
        count2 = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert count2 == count1


def test_domain_router_cnFilingsAndPdfReports_resolveToDisclosureClean() -> None:
    """覆盖范围：METADATA_DOMAINS 全量路由
    测试对象：resolve_clean_write_target（cn_filings、cn_pdf_reports）
    目的/目标：capabilities 子域均路由 disclosure clean 表
    验证点：target=cn_announcement_clean；write_mode=upsert_by_pk
    失败含义：filings/pdf 子域落错表则 capabilities 与 promote 分叉
    """
    from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target

    for domain in ("cn_filings", "cn_pdf_reports"):
        target = resolve_clean_write_target(domain)
        assert target.target_table == "cn_announcement_clean"
        assert target.write_mode == "upsert_by_pk"


def test_domain_router_unknownDomain_raises() -> None:
    """覆盖范围：未知 domain 负向路由
    测试对象：resolve_clean_write_target
    目的/目标：未注册 domain fail-closed
    验证点：抛 CleanWriteTargetError
    失败含义：未知 domain 静默落默认表则三域路由 SSOT 失效
    """
    from backend.app.ops.sandbox_clean_write.clean_write_targets import (
        CleanWriteTargetError,
        resolve_clean_write_target,
    )

    with pytest.raises(CleanWriteTargetError, match="no clean write target"):
        resolve_clean_write_target("not_a_registered_domain")


def test_disclosure_pdfFileId_requiresFileRegistry(tmp_path: Path) -> None:
    """覆盖范围：pdf_file_id 指针校验
    测试对象：populate_disclosure_from_bundle + file_registry
    目的/目标：§6.1 pdf_file_id 须挂接已登记 file_registry
    验证点：未知 pdf_file_id 抛 RehearsalLoaderError
    失败含义：任意指针可写入 clean 则后续抓取管道可被投毒
    """
    from datetime import UTC, datetime, time
    from unittest.mock import patch

    from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
        DisclosureStagingRow,
        RehearsalLoaderError,
        load_rehearsal_bundle,
        populate_disclosure_from_bundle,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import load_candidate_set

    candidate = next(c for c in load_candidate_set("r3g_p0") if c.source_id == "cninfo")
    bundle = load_rehearsal_bundle(candidate, dry_run=True)
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    bogus = DisclosureStagingRow(
        announcement_id="ann-bogus",
        instrument_id="sh.600519",
        title="t",
        publish_timestamp=datetime.combine(
            datetime.fromisoformat("2024-01-01").date(), time(0, 0), tzinfo=UTC
        ),
        announcement_url="https://example.com/a.pdf",
        announcement_type=None,
        data_domain="cn_announcements",
        source_used="cninfo",
        pdf_file_id="missing-file-id",
        extracted_text_file_id=None,
        content_status="pdf_registered",
        batch_id="t",
        source_fetch_id="sf1",
        content_hash="h",
        schema_hash="s",
        quality_flags="STAGED_FIXTURE",
        created_at=datetime.now(UTC),
    )
    with patch(
        "backend.app.ops.sandbox_clean_write.rehearsal_loader._disclosure_rows_from_bundle",
        return_value=[bogus],
    ):
        with pytest.raises(RehearsalLoaderError, match="pdf_file_id not in file_registry"):
            populate_disclosure_from_bundle(con, bundle, batch_id="t", max_rows=10)


def test_disclosure_announcementUrl_rejectsInvalidScheme() -> None:
    """覆盖范围：announcement_url scheme 白名单
    测试对象：populate_disclosure_from_bundle URL 校验
    目的/目标：仅 http/https URL 可入 clean
    验证点：javascript: scheme 抛 RehearsalLoaderError
    失败含义：未来 SSRF 面若服务端 fetch 该列则可被滥用
    """
    from datetime import UTC, datetime, time
    from unittest.mock import patch

    from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
        DisclosureStagingRow,
        RehearsalLoaderError,
        load_rehearsal_bundle,
        populate_disclosure_from_bundle,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import load_candidate_set

    candidate = next(c for c in load_candidate_set("r3g_p0") if c.source_id == "cninfo")
    bundle = load_rehearsal_bundle(candidate, dry_run=True)
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    bad_url = DisclosureStagingRow(
        announcement_id="ann-bad-url",
        instrument_id="sh.600519",
        title="t",
        publish_timestamp=datetime.combine(
            datetime.fromisoformat("2024-01-01").date(), time(0, 0), tzinfo=UTC
        ),
        announcement_url="javascript:alert(1)",
        announcement_type=None,
        data_domain="cn_announcements",
        source_used="cninfo",
        pdf_file_id=None,
        extracted_text_file_id=None,
        content_status="metadata_only",
        batch_id="t",
        source_fetch_id="sf1",
        content_hash="h",
        schema_hash="s",
        quality_flags="STAGED_FIXTURE",
        created_at=datetime.now(UTC),
    )
    with patch(
        "backend.app.ops.sandbox_clean_write.rehearsal_loader._disclosure_rows_from_bundle",
        return_value=[bad_url],
    ):
        with pytest.raises(RehearsalLoaderError, match="announcement_url scheme not allowed"):
            populate_disclosure_from_bundle(con, bundle, batch_id="t", max_rows=10)


def test_barBundle_oversizedJson_rejects(tmp_path: Path) -> None:
    """覆盖范围：bars.json 字节硬顶（A6-NB-3）
    测试对象：_load_baostock_bundle
    目的/目标：超大证据文件 fail-closed，避免全文件 json.loads OOM
    验证点：超过 _MAX_BARS_JSON_BYTES 抛 RehearsalLoaderError
    失败含义：恶意/超大 bundle 可撑爆 promote 进程内存
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
        RehearsalLoaderError,
        _MAX_BARS_JSON_BYTES,
        _load_baostock_bundle,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import RehearsalCandidate

    evidence = tmp_path / "ev"
    evidence.mkdir()
    (evidence / "bars.json").write_bytes(b"x" * (_MAX_BARS_JSON_BYTES + 1))
    candidate = RehearsalCandidate(
        source_id="baostock",
        domain="cn_equity_daily_bar",
        operation="fetch_daily_bars",
        symbols_or_series=("sh.600519",),
        window_days=30,
    )
    with pytest.raises(RehearsalLoaderError, match="bars.json exceeds"):
        _load_baostock_bundle(evidence, candidate)


def test_pilotCompat_implementationPaths_zeroMarketBarClean() -> None:
    """覆盖范围：活卡 9.8.1 rg 门禁
    测试对象：backend/scripts/tests/specs/ROUND_3 实现路径
    目的/目标：AC-PILOT-COMPAT — 实现路径零 market_bar_clean 残留
    验证点：扫描命中列表为空
    失败含义：pilot 仍引用已删除单表则 G3/G6 路由分叉
    """
    roots = (
        PROJECT_ROOT / "backend",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "specs",
        PROJECT_ROOT / "docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY",
    )
    needle = "market_bar_clean"
    self_test = Path(__file__).resolve()
    suffixes = {".py", ".sql", ".yaml", ".yml", ".json", ".md", ".ts", ".tsx"}
    hits: list[str] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.resolve() == self_test:
                continue
            if not path.is_file() or path.suffix not in suffixes:
                continue
            try:
                if needle in path.read_text(encoding="utf-8"):
                    hits.append(str(path.relative_to(PROJECT_ROOT)))
            except (OSError, UnicodeDecodeError):
                continue
    assert not hits, f"market_bar_clean references: {hits}"


def test_promote_domainTargetMismatch_blocksExecute(tmp_path: Path) -> None:
    """覆盖范围：domain 与 target_table 错配门禁
    测试对象：run_limited_production_entry execute
    目的/目标：bar domain 不得写 axis_observation（契约 fail-closed）
    验证点：LimitedProductionEntryError 含 target_table != domain router
    失败含义：错配 promote 可写错 clean 表
    """
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        LimitedProductionEntryError,
        run_limited_production_entry,
    )

    req, _cm = _build_promote_request(
        tmp_path,
        source_id="baostock",
        domain="cn_equity_daily_bar",
        target_table="axis_observation",
        symbols=["sh.600519"],
        approval_id="r3h06-mismatch",
    )
    with pytest.raises(LimitedProductionEntryError, match="target_table"):
        run_limited_production_entry(req)
