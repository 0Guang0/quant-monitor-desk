"""Ops 只读 DB 巡检（DbInspector）与 qmd_ops db-inspect CLI 契约测试。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.ops.db_inspector import (
    REQUIRED_TOP_LEVEL_FIELDS,
    DbInspector,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _init_db(db_path: Path) -> None:
    con = duckdb.connect(str(db_path))
    apply_migrations(con)
    con.close()


def _seed_evidence(db_path: Path) -> None:
    _init_db(db_path)
    cm = ConnectionManager(db_path)
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO fetch_log (
                fetch_id, run_id, source_id, data_domain, status, row_count, fetch_time
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            ["f-1", "run-1", "baostock", "market_bar_1d", "SUCCESS", 42],
        )
        con.execute(
            """
            INSERT INTO data_sync_job (
                job_id, run_id, job_type, status, created_at
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            ["job-1", "run-1", "backfill", "COMPLETED"],
        )


def _write_files(directory: Path, count: int, *, prefix: str = "file", suffix: str = ".txt") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        (directory / f"{prefix}-{i}{suffix}").write_text("x", encoding="utf-8")


def _run_qmd_db_inspect_cli(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(_PROJECT_ROOT / "scripts" / "qmd_ops.py"), "db-inspect", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=_PROJECT_ROOT)


def _parse_cli_json(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_dbInspect_missingDb_returnsFail(tmp_path: Path) -> None:
    """覆盖范围：数据库文件不存在
    测试对象：DbInspector.inspect
    目的/目标：数据库文件缺失时应判定失败并明确提示找不到文件
    验证点：status=='FAIL'；db.exists 与 read_only_open 为假；errors 含 not found
    失败含义：坏路径被当成可巡检库，运维误判环境健康
    """
    missing = tmp_path / "missing.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    report = DbInspector(missing, data_root).inspect()
    assert report.status == "FAIL"
    assert report.db["exists"] is False
    assert report.db["read_only_open"] is False
    assert report.errors
    assert any("not found" in err.lower() for err in report.errors)


def test_dbInspect_deferredItemMapping_nonEmpty(tmp_path: Path) -> None:
    """覆盖范围：延期项与证据字段映射
    测试对象：report.deferred_item_mapping
    目的/目标：巡检报告须携带已知 R3/R2.6 延期项及 evidence_fields
    验证点：mapping 非空；item_id 含 DB-R3-001 等；每项有 evidence_fields
    失败含义：审计延期项无法从巡检 JSON 对照，gate 追溯断档
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    report = DbInspector(db, tmp_path).inspect()
    assert report.deferred_item_mapping
    item_ids = {entry["item_id"] for entry in report.deferred_item_mapping}
    assert item_ids >= {
        "DB-R3-001",
        "DB-R3-002",
        "R3-PARTIAL-2",
        "R2.6-IMPL-8",
        "R3-EARLY-DB-INSPECT-CLI",
    }
    for entry in report.deferred_item_mapping:
        assert entry["evidence_fields"]


def test_dbInspect_dbFile_unchanged(tmp_path: Path) -> None:
    """覆盖范围：只读巡检不修改库文件
    测试对象：DbInspector 对 duckdb 文件字节
    目的/目标：inspect 前后数据库文件内容应完全一致
    验证点：read_bytes() before == after
    失败含义：声称只读却改写库，生产巡检有风险
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    before = db.read_bytes()
    DbInspector(db, tmp_path).inspect()
    after = db.read_bytes()
    assert before == after


def test_dbInspect_emptySchemaDb_returnsWarn(tmp_path: Path) -> None:
    """覆盖范围：已迁移但无业务数据的空库
    测试对象：DbInspector 对仅 schema 的库
    目的/目标：能只读打开且已有表结构时，应给出预警而非直接判失败
    验证点：status=='WARN'；read_only_open；table_count>0；schema_version 表存在
    失败含义：空库误报 FAIL 或无法只读打开，运维无法区分「空」与「坏」
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    report = DbInspector(db, tmp_path).inspect()
    assert report.status == "WARN"
    assert report.db["read_only_open"] is True
    assert report.schema["table_count"] > 0
    assert any(t["name"] == "schema_version" and t["exists"] for t in report.key_tables)


def test_dbInspect_outputJsonShape_hasRequiredFields(tmp_path: Path) -> None:
    """覆盖范围：to_dict JSON 顶层形状
    测试对象：REQUIRED_TOP_LEVEL_FIELDS 与 inspect().to_dict()
    目的/目标：巡检报告须包含合约要求的全部顶层字段，且能被程序序列化
    验证点：各 REQUIRED 字段存在；mode=='read_only'；status∈{PASS,WARN,FAIL}；json.dumps 成功
    失败含义：命令行或下游程序解析缺字段，数据库巡检结果无法被机器消费
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    payload = DbInspector(db, tmp_path).inspect().to_dict()
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        assert field in payload
    assert payload["mode"] == "read_only"
    assert payload["status"] in {"PASS", "WARN", "FAIL"}
    json.dumps(payload)


def test_dbInspect_fixtureWithEvidence_reportsCounts(tmp_path: Path) -> None:
    """覆盖范围：含 fetch_log 与 sync job 的库
    测试对象：key_tables 与 evidence 段
    目的/目标：有抓取与任务数据时应回报行数与 latest_fetch 摘要
    验证点：fetch_log 存在且 row_count==1；evidence 含 baostock/42；COMPLETED job 计数为 1
    失败含义：有数据却报零行，运维无法从巡检判断 pipeline 是否跑过
    """
    db = tmp_path / "t.duckdb"
    _seed_evidence(db)
    report = DbInspector(db, tmp_path).inspect()
    fetch_table = next(t for t in report.key_tables if t["name"] == "fetch_log")
    assert fetch_table["exists"] is True
    assert fetch_table["row_count"] == 1
    assert report.evidence["latest_fetch"]["source_id"] == "baostock"
    assert report.evidence["latest_fetch"]["row_count"] == 42
    assert report.evidence["job_status_counts"].get("COMPLETED") == 1


def test_dbInspect_layer1AxisTables_presentAfterMigration(tmp_path: Path) -> None:
    """覆盖范围：011 layer1 表在迁移后可见
    测试对象：axis_observation 与 axis_snapshot_lineage
    目的/目标：迁移后 layer1 关键表应出现在 key_tables（可为空表）
    验证点：两表 exists 为真；axis_observation row_count==0
    失败含义：layer1 表未建或巡检未列入，R3 DB 能力无法验收
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    report = DbInspector(db, tmp_path).inspect()
    axis_obs = next(t for t in report.key_tables if t["name"] == "axis_observation")
    assert axis_obs["exists"] is True
    assert axis_obs["row_count"] == 0
    lineage = next(t for t in report.key_tables if t["name"] == "axis_snapshot_lineage")
    assert lineage["exists"] is True


def test_dbInspect_pathScan_staysUnderDataRoot(tmp_path: Path) -> None:
    """覆盖范围：data_root 内 raw 扫描边界
    测试对象：DbInspector data_root 文件计数
    目的/目标：仅统计 data_root 下文件，不扫兄弟目录
    验证点：data/raw 内 1 个 csv 计为 raw_files_count==1；outside 目录不计入
    失败含义：路径扫描越界，可能泄露或误计 data_root 外文件
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw" / "vendor"
    raw_dir.mkdir(parents=True)
    (raw_dir / "sample.csv").write_text("x", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.parquet").write_text("x", encoding="utf-8")

    report = DbInspector(db, data_root, limit=5).inspect()
    assert report.data_root["raw_files_count"] == 1
    assert report.data_root["parquet_files_count"] == 0
    assert report.data_root["scan_limited"] is False


def test_dbInspect_limit_hardCapsAtContractMaximum(tmp_path: Path) -> None:
    """覆盖范围：--limit 硬顶 100（raw 子目录）
    测试对象：DbInspector limit=500 对 110 个文件
    目的/目标：超过契约上限时计数封顶并标记 scan_limited
    验证点：raw_files_count==100；scan_limited 为 True
    失败含义：大目录扫描无上限，巡检可能拖垮 IO 或超时
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    _write_files(data_root / "raw", 110, prefix="sample", suffix=".csv")

    report = DbInspector(db, data_root, limit=500).inspect()
    assert report.data_root["raw_files_count"] == 100
    assert report.data_root["scan_limited"] is True


def test_dbInspect_pathOutsideDataRoot_rejectedFromScan(tmp_path: Path) -> None:
    """覆盖范围：data_root 外 parquet 不得计入
    测试对象：include_path_check 与空 data_root
    目的/目标：即使磁盘上 data_root 外有大量文件，计数仍应为零
    验证点：outside 有 5 个 parquet；报告 parquet/raw 计数均为 0
    失败含义：巡检扫描逃逸 data_root，违背只读边界契约
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    data_root.mkdir()
    outside = tmp_path / "outside-secrets"
    outside.mkdir()
    for i in range(5):
        (outside / f"leak-{i}.parquet").write_text("x", encoding="utf-8")

    assert len(list(outside.glob("*.parquet"))) == 5

    report = DbInspector(db, data_root, include_path_check=True).inspect()
    assert report.data_root["path"] == str(data_root)
    assert report.data_root["exists"] is True
    assert report.data_root["parquet_files_count"] == 0
    assert report.data_root["raw_files_count"] == 0
    assert report.data_root["scan_limited"] is False


@pytest.mark.parametrize(
    ("subdir", "count_key"),
    [
        ("raw", "raw_files_count"),
        ("parquet", "parquet_files_count"),
        ("audit", "audit_files_count"),
        ("report", "report_files_count"),
    ],
)
def test_dbInspect_subdirScan_respectsLimit(tmp_path: Path, subdir: str, count_key: str) -> None:
    """覆盖范围：data_root 各子目录扫描上限（R3-AUDIT-DEF-03）
    测试对象：DbInspector._inspect_data_root / limit 硬顶 100
    目的/目标：raw/parquet/audit/report 子目录超限时计数封顶且 scan_limited 为真
    验证点：对应 count_key==100；scan_limited 为 True
    失败含义：某一子目录无上限，四目录契约不一致
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    _write_files(data_root / subdir, 110)

    report = DbInspector(db, data_root, limit=500).inspect()
    assert report.data_root[count_key] == 100
    assert report.data_root["scan_limited"] is True


@pytest.mark.parametrize(
    ("subdir", "count_key"),
    [
        ("raw", "raw_files_count"),
        ("parquet", "parquet_files_count"),
        ("audit", "audit_files_count"),
        ("report", "report_files_count"),
    ],
)
def test_dbInspect_subdirScan_limitFloorClampsToOne(tmp_path: Path, subdir: str, count_key: str) -> None:
    """覆盖范围：--limit 下限钳制对各子目录一致（B-027）
    测试对象：DbInspector limit floor（min 1）
    目的/目标：limit=0 时各子目录最多计 1 个文件且 scan_limited 为真
    验证点：count_key==1；scan_limited 为 True
    失败含义：limit=0 被当成无限制或零计数，CLI 与库行为不一致
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    _write_files(data_root / subdir, 5)

    report = DbInspector(db, data_root, limit=0).inspect()
    assert report.data_root[count_key] == 1
    assert report.data_root["scan_limited"] is True


@pytest.mark.parametrize(
    ("subdir", "count_key"),
    [
        ("raw", "raw_files_count"),
        ("parquet", "parquet_files_count"),
        ("audit", "audit_files_count"),
        ("report", "report_files_count"),
    ],
)
def test_qmdOps_cli_subdirScan_respectsContractLimit(
    tmp_path: Path, subdir: str, count_key: str
) -> None:
    """覆盖范围：CLI db-inspect 子目录扫描上限
    测试对象：qmd_ops db-inspect --limit
    目的/目标：命令行与库内巡检对子目录扫描应共享同一套数量上限
    验证点：returncode==0；JSON 中 count_key==100 且 scan_limited 为真
    失败含义：命令行路径绕过库内上限，运维脚本与程序接口结果不一致
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    _write_files(data_root / subdir, 110)

    payload = _parse_cli_json(
        _run_qmd_db_inspect_cli(
            "--db",
            str(db),
            "--data-root",
            str(data_root),
            "--limit",
            "500",
            "--format",
            "json",
        )
    )
    assert payload["data_root"][count_key] == 100
    assert payload["data_root"]["scan_limited"] is True


def test_dbInspect_missingDataRoot_stillOpensDbReadOnly(tmp_path: Path) -> None:
    """覆盖范围：data_root 不存在但 db 存在
    测试对象：DbInspector 在缺失 data_root 时
    目的/目标：仍应只读打开库；data_root 段标记不存在且计数为零
    验证点：db.read_only_open 为真；data_root.exists 为假；raw_files_count==0
    失败含义：缺数据目录导致无法巡检库本身，误把 schema 问题当成路径问题
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    missing_root = tmp_path / "no-such-data-root"
    report = DbInspector(db, missing_root, include_path_check=True).inspect()
    assert report.db["read_only_open"] is True
    assert report.data_root["exists"] is False
    assert report.data_root["raw_files_count"] == 0


def test_dbInspect_limit_floorClampsToMinimumOne(tmp_path: Path) -> None:
    """覆盖范围：raw 子目录 limit=0 下限
    测试对象：DbInspector limit floor（raw 专用用例）
    目的/目标：与参数化子目录测试互补，验证 raw 路径 limit=0→1
    验证点：raw_files_count==1；scan_limited 为 True
    失败含义：raw 扫描在 limit=0 时行为与其他子目录不一致
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    _write_files(data_root / "raw", 5, prefix="sample", suffix=".csv")

    report = DbInspector(db, data_root, limit=0).inspect()
    assert report.data_root["raw_files_count"] == 1
    assert report.data_root["scan_limited"] is True


def test_qmdOps_cli_limitHardCapsAtContractMaximum(tmp_path: Path) -> None:
    """覆盖范围：CLI --limit 硬顶 100（raw）
    测试对象：qmd_ops db-inspect 子进程
    目的/目标：命令行 --limit 500 仍应被契约钳到 100
    验证点：returncode==0；JSON raw_files_count==100；scan_limited 为真
    失败含义：CLI 未继承库内硬顶，脚本与 Python API 结果不一致
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    _write_files(data_root / "raw", 110, prefix="sample", suffix=".csv")

    payload = _parse_cli_json(
        _run_qmd_db_inspect_cli(
            "--db",
            str(db),
            "--data-root",
            str(data_root),
            "--limit",
            "500",
            "--format",
            "json",
        )
    )
    assert payload["data_root"]["raw_files_count"] == 100
    assert payload["data_root"]["scan_limited"] is True


def test_qmdOps_cli_invokesSameInspector(tmp_path: Path) -> None:
    """覆盖范围：CLI 与 DbInspector 输出一致性
    测试对象：qmd_ops db-inspect JSON
    目的/目标：命令行巡检应产出与库内 inspect 同形的只读报告
    验证点：returncode==0；mode==read_only；db.read_only_open；含 deferred_item_mapping
    失败含义：命令行包装了另一套逻辑，运维与测试断言无法互证
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    data_root.mkdir()
    payload = _parse_cli_json(
        _run_qmd_db_inspect_cli(
            "--db",
            str(db),
            "--data-root",
            str(data_root),
            "--format",
            "json",
        )
    )
    assert payload["mode"] == "read_only"
    assert payload["db"]["read_only_open"] is True
    assert "deferred_item_mapping" in payload


def test_dbInspect_symlinkOutsideDataRoot_notCounted(tmp_path: Path) -> None:
    """覆盖范围：raw 下指向外部的符号链接
    测试对象：DbInspector 路径安全扫描
    目的/目标：symlink 指向 data_root 外目录时不得把外部 parquet 计入
    验证点：平台支持 symlink 时 parquet/raw 计数均为 0
    失败含义：通过 symlink 可间接枚举 data_root 外敏感文件
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw"
    raw_dir.mkdir(parents=True)
    outside = tmp_path / "outside-secrets"
    outside.mkdir()
    (outside / "leak.parquet").write_text("x", encoding="utf-8")
    try:
        raw_dir.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")

    report = DbInspector(db, data_root, include_path_check=True).inspect()
    assert report.data_root["parquet_files_count"] == 0
    assert report.data_root["raw_files_count"] == 0


def test_qmdOps_cli_rejectsForbiddenSqlFlag() -> None:
    """覆盖范围：CLI 禁止 --sql 旁路
    测试对象：qmd_ops db-inspect --sql
    目的/目标：只读巡检不得接受任意 SQL 执行参数
    验证点：returncode != 0
    失败含义：运维 CLI 可执行任意 SQL，只读承诺被破坏
    """
    result = _run_qmd_db_inspect_cli("--sql", "SELECT 1")
    assert result.returncode != 0


def test_qmdOps_cli_rejectsForbiddenEnableQmtFlag() -> None:
    """覆盖范围：CLI 禁止 --enable-qmt
    测试对象：qmd_ops db-inspect --enable-qmt
    目的/目标：db-inspect 不得携带启用 QMT 的旁路开关
    验证点：returncode != 0
    失败含义：巡检命令可意外拉起重型 QMT 依赖，违背 extras 策略
    """
    result = _run_qmd_db_inspect_cli("--enable-qmt")
    assert result.returncode != 0


def test_dbInspect_includePathCheckDisabled_skipsScanCounts(tmp_path: Path) -> None:
    """覆盖范围：include_path_check=false
    测试对象：DbInspector 路径扫描开关
    目的/目标：关闭路径检查时即使有 raw 文件也不计数
    验证点：raw/parquet 计数为 0；scan_limited 为 False
    失败含义：关闭开关仍扫描磁盘，性能与契约语义不符
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "sample.csv").write_text("x", encoding="utf-8")

    report = DbInspector(db, data_root, include_path_check=False).inspect()
    assert report.data_root["raw_files_count"] == 0
    assert report.data_root["parquet_files_count"] == 0
    assert report.data_root["scan_limited"] is False


def test_qmdOps_cli_jsonRoundTripsStrictly(tmp_path: Path) -> None:
    """覆盖范围：CLI JSON 可严格序列化
    测试对象：qmd_ops db-inspect --format json
    目的/目标：标准输出必须是严格合法的 JSON 文本
    验证点：returncode==0；loads 后再 dumps 不抛错
    失败含义：命令行输出非严格 JSON，自动化解析与管道工具会失败
    """
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    data_root.mkdir()
    payload = _parse_cli_json(
        _run_qmd_db_inspect_cli(
            "--db",
            str(db),
            "--data-root",
            str(data_root),
            "--format",
            "json",
        )
    )
    json.dumps(payload)
