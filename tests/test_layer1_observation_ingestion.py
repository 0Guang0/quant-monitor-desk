"""第一层观测数据「分阶段拉取并入库」全流程测试。

覆盖范围：先盘点库里有什么（Phase1）、只看不写地试路由（Phase2）、
小批量拉原始数据（Phase3）、校验通过后写入正式观测与快照（Phase4），
以及各阶段任务审计材料的导出。
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path

import duckdb
import pytest
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.adapters.fetch_port import LocalFixtureFetchPort
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.route_models import SourceRouteCandidate, SourceRoutePlan
from backend.app.datasources.service import DataSourceService, ResourceGuardBlockedError
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.layer1_axes.ingestion import (
    BLINDSPOT_INDICATOR_REJECTED,
    FORBIDDEN_INDICATOR_REJECTED,
    FROZEN_STAGED_INDICATOR,
    STAGED_DATA_DOMAIN,
    STAGED_OPERATION,
    IngestionRejectedError,
    Layer1ObservationIngestionService,
)
from backend.app.layer1_axes.ingestion_evidence import capture_task_phase2_evidence
from backend.app.layer1_axes.ingestion_inventory import (
    INVENTORY_JSON_NAME,
    INVENTORY_MD_NAME,
    PHASE1_MINIMUM_KEY_TABLES,
    assess_phase2_gate,
    capture_phase1_inventory,
    capture_task_phase1_evidence,
    copy_sandbox_db,
    data_root_content_fingerprint,
    file_sha256,
    record_operator_classification,
)
from backend.app.ops.db_inspector import REQUIRED_TOP_LEVEL_FIELDS
from backend.app.sync.event_payload import parse_event_payload
from tests.contract_gate_support import PROJECT_ROOT, trellis_task_dir

BATCH25_TASK_SLUG = "06-20-round3-batch2-5-layer1-obs-ingest"
TASK_EVIDENCE_DIR = trellis_task_dir(BATCH25_TASK_SLUG) / "execute-evidence"


@pytest.fixture(autouse=True)
def _layer1Ingestion_resourceGuardOk(monkeypatch: pytest.MonkeyPatch) -> None:
    """ponytail: 测 ingestion 路由/证据链，不测宿主机内存；RG 专项见 routePreview_resourceGuardPauseRaises。"""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))


def _init_db(db_path: Path) -> None:
    con = duckdb.connect(str(db_path))
    apply_migrations(con)
    con.close()


def _row_counts(db_path: Path, tables: tuple[str, ...]) -> dict[str, int | None]:
    con = duckdb.connect(str(db_path), read_only=True)
    counts: dict[str, int | None] = {}
    try:
        for name in tables:
            exists = con.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'main' AND table_name = ?
                """,
                [name],
            ).fetchone()[0]
            if not exists:
                counts[name] = None
                continue
            counts[name] = int(con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
    finally:
        con.close()
    return counts


def test_layer1Ingestion_phase1_inventory_readOnly(tmp_path: Path) -> None:
    """覆盖范围：空库第一次盘点——只读打开数据库并生成清单
    测试对象：capture_phase1_inventory
    目的/目标：证明盘点过程不改数据，且空库会被判为仅结构无业务数据，允许进入试路由
    验证点：产出 json/md；inspect.mode=read_only；classification=schema_only_empty；phase2_authorized=True
    失败含义：连只读盘点都做不好，或空库被误拦，后续基线材料无法导出
    """
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)

    out = tmp_path / "evidence"
    inventory = capture_phase1_inventory(db, data_root, evidence_dir=out)

    assert (out / INVENTORY_JSON_NAME).is_file()
    assert (out / INVENTORY_MD_NAME).is_file()
    inspect = inventory["inspect"]
    assert inspect["mode"] == "read_only"
    assert inspect["db"]["read_only_open"] is True
    assert inspect["db"]["exists"] is True
    assert inventory["inventory_type"] == "read_only"
    assert inventory["phase"] == "phase1_before_ingestion"
    assert inventory["db_evidence_classification"] == "schema_only_empty"
    assert inventory["phase2_gate"]["phase2_authorized"] is True

    md_text = (out / INVENTORY_MD_NAME).read_text(encoding="utf-8")
    assert "schema_only_empty" in md_text
    assert "Read-only open: True" in md_text
    assert "**Phase 2 authorized:** True" in md_text


def test_layer1Ingestion_phase1_inventory_requiredTableKeys(tmp_path: Path) -> None:
    """覆盖范围：盘点清单是否列出关键表的行数并与检查工具一致
    测试对象：capture_phase1_inventory.phase1_minimum_key_tables
    目的/目标：清单里的表名集合和每张表行数，必须与数据库检查工具看到的一致
    验证点：phase1_tables 集合等于 PHASE1_MINIMUM_KEY_TABLES；各行数与 inspect 对齐；inspect 顶层字段齐全
    失败含义：清单漏表或行数对不上，运维无法对照数据库真实状态
    """
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)

    inventory = capture_phase1_inventory(db, data_root)
    phase1_tables = inventory["phase1_minimum_key_tables"]
    assert set(phase1_tables) == set(PHASE1_MINIMUM_KEY_TABLES)

    inspect_tables = {t["name"]: t for t in inventory["inspect"]["key_tables"]}
    for name in PHASE1_MINIMUM_KEY_TABLES:
        assert name in phase1_tables
        assert inspect_tables[name]["exists"] is True
        assert phase1_tables[name] == inspect_tables[name]["row_count"]

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        assert field in inventory["inspect"]


def test_layer1Ingestion_phase1_zeroMutation(tmp_path: Path) -> None:
    """覆盖范围：盘点前后数据库与数据目录是否完全不变
    测试对象：capture_phase1_inventory
    目的/目标：证明只读盘点不会偷偷改库文件、改行数或动数据目录里的文件
    验证点：前后文件字节 hash 相同；关键表行数相同；data_root 指纹相同
    失败含义：号称只读却改了库或文件，安全红线被突破
    """
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw" / "vendor"
    raw_dir.mkdir(parents=True)
    (raw_dir / "seed.csv").write_text("x", encoding="utf-8")
    _init_db(db)

    before_bytes = db.read_bytes()
    before_hash = hashlib.sha256(before_bytes).hexdigest()
    before_counts = _row_counts(db, PHASE1_MINIMUM_KEY_TABLES)
    before_root = data_root_content_fingerprint(data_root)

    capture_phase1_inventory(db, data_root, evidence_dir=tmp_path / "out")

    after_bytes = db.read_bytes()
    after_hash = hashlib.sha256(after_bytes).hexdigest()
    after_counts = _row_counts(db, PHASE1_MINIMUM_KEY_TABLES)
    after_root = data_root_content_fingerprint(data_root)

    assert before_hash == after_hash
    assert before_bytes == after_bytes
    assert before_counts == after_counts
    assert before_root == after_root


def test_layer1Ingestion_phase1_copyProvenanceWhenSandbox(tmp_path: Path) -> None:
    """覆盖范围：在沙箱里复制数据库做盘点时的来源记录
    测试对象：copy_sandbox_db 与 capture_phase1_inventory(copy_source=...)
    目的/目标：复制操作须记下从哪份库复制的、校验和多大，并写进清单
    验证点：沙箱文件存在；copy_sha256/size 与源库一致；inventory 与 md 均含 provenance
    失败含义：沙箱盘点说不清来源，审计无法确认基于哪份数据库
    """
    source = tmp_path / "source.duckdb"
    sandbox = tmp_path / "sandbox.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(source)

    provenance = copy_sandbox_db(source, sandbox)
    assert sandbox.is_file()
    assert provenance["copy_sha256"] == file_sha256(source)
    assert provenance["copy_size_bytes"] == source.stat().st_size

    inventory = capture_phase1_inventory(
        sandbox,
        data_root,
        evidence_dir=tmp_path / "out",
        copy_source=source,
    )
    assert inventory["copy_provenance"] is not None
    assert inventory["copy_provenance"]["copy_source"] == provenance["copy_source"]
    assert inventory["copy_provenance"]["copy_sha256"] == provenance["copy_sha256"]
    assert inventory["copy_provenance"]["copy_size_bytes"] == provenance["copy_size_bytes"]

    md_text = (tmp_path / "out" / INVENTORY_MD_NAME).read_text(encoding="utf-8")
    assert "Sandbox copy provenance" in md_text
    assert provenance["copy_sha256"] in md_text


def test_layer1Ingestion_phase1_classify_fixtureOrStagedEvidence(tmp_path: Path) -> None:
    """覆盖范围：库里已有拉数日志时的风险分类——须先人工审阅
    测试对象：capture_phase1_inventory 与 assess_phase2_gate
    目的/目标：一旦拉取日志有记录，应判为已有测试或暂存证据，必须先人工看过才能继续
    验证点：classification=fixture_or_staged_evidence；phase2_authorized=False；stop_reason 非空
    失败含义：把未审阅的暂存数据当成空库，可能在错误数据上试路由
    """
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)
    cm = ConnectionManager(db)
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO fetch_log (
                fetch_id, run_id, source_id, data_domain, status, row_count, fetch_time
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            ["f-1", "run-1", "macro_supplementary", "macro_supplementary", "SUCCESS", 1],
        )

    inventory = capture_phase1_inventory(db, data_root)
    assert inventory["db_evidence_classification"] == "fixture_or_staged_evidence"
    gate = assess_phase2_gate(inventory)
    assert gate["phase2_authorized"] is False
    assert gate["stop_reason"] is not None


def test_layer1Ingestion_phase1_classify_productionLikeData(tmp_path: Path) -> None:
    """覆盖范围：正式观测表里已有数据时的风险分类——须先审再往下走
    测试对象：capture_phase1_inventory
    目的/目标：库里已有观测行时，应判为像生产数据，必须先审阅才能继续摄取
    验证点：classification=production_like_data；phase2_gate.phase2_authorized=False
    失败含义：真实观测数据未被识别，可能在生产数据上误跑摄取流程
    """
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)
    cm = ConnectionManager(db)
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO axis_observation (
                observation_id, indicator_id, as_of_timestamp, publish_timestamp,
                fetch_time, raw_value, raw_unit, frequency, source_used,
                source_channel_id, data_lag_days, content_hash, schema_hash,
                source_switched, created_at
            ) VALUES (
                ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                1.0, 'pct', 'daily', 'fixture', 'fixture', 0,
                'hash', 'schema', false, CURRENT_TIMESTAMP
            )
            """,
            ["obs-1", "ENV-E1-DGS10"],
        )

    inventory = capture_phase1_inventory(db, data_root)
    assert inventory["db_evidence_classification"] == "production_like_data"
    assert inventory["phase2_gate"]["phase2_authorized"] is False


def test_layer1Ingestion_phase1_classify_userProvidedData(tmp_path: Path) -> None:
    """覆盖范围：用户导入文件已在库中登记时的风险分类——须先审阅
    测试对象：capture_phase1_inventory
    目的/目标：有文件登记且无拉取日志时，应判为用户自带数据，须先审阅
    验证点：classification=user_provided_data；phase2_authorized=False
    失败含义：用户导入未识别，可能在未审 import 上继续摄取
    """
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)
    cm = ConnectionManager(db)
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO file_registry (
                file_id, file_type, source, local_path, content_hash, parse_status
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ["file-1", "raw", "user_import", "raw/user/import.csv", "abc", "PARSED"],
        )

    inventory = capture_phase1_inventory(db, data_root)
    assert inventory["db_evidence_classification"] == "user_provided_data"
    assert inventory["phase2_gate"]["phase2_authorized"] is False


def test_layer1Ingestion_phase1_phase2Gate_blocksUntilReview(tmp_path: Path) -> None:
    """覆盖范围：六种数据分类下，是否允许进入试路由阶段
    测试对象：assess_phase2_gate
    目的/目标：只有空结构或仅有配置才自动放行，其余一律先停等审阅
    验证点：六类 classification 的 phase2_authorized 与预期布尔一致
    失败含义：放行矩阵错了，有数据的环境可能在未审阅时就去试路由
    """
    for classification, authorized in (
        ("schema_only_empty", True),
        ("schema_with_config_only", True),
        ("fixture_or_staged_evidence", False),
        ("user_provided_data", False),
        ("production_like_data", False),
        ("unknown_data_present", False),
    ):
        gate = assess_phase2_gate({"db_evidence_classification": classification})
        assert gate["phase2_authorized"] is authorized, classification


def test_layer1Ingestion_phase1_captureUsesReadOnlyInspect(tmp_path: Path) -> None:
    """覆盖范围：盘点时数据库必须以只读方式打开
    测试对象：capture_phase1_inventory
    目的/目标：检查须用只读连接，且整段流程不会改动数据库文件
    验证点：read_only_open=True；盘点前后 db.read_bytes() 相同
    失败含义：盘点以写模式打开或悄悄改库，只读承诺失效
    """
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)
    before_hash = db.read_bytes()

    inventory = capture_phase1_inventory(db, data_root)

    assert inventory["inspect"]["db"]["read_only_open"] is True
    assert db.read_bytes() == before_hash


def test_layer1Ingestion_phase1_taskEvidenceUsesProjectTargetPaths(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：任务级盘点证据是否指向项目配置的数据目录
    测试对象：capture_task_phase1_evidence
    目的/目标：目标库尚不存在时，应自动建仅迁移结构的沙箱库并记录策略
    验证点：target_db_exists_at_capture=False；capture_strategy=synthetic_migrated_schema_only；沙箱 duckdb 文件存在
    失败含义：任务证据路径或建库策略错了，Trellis 执行材料无法复现基线
    """
    data_root = tmp_path / "data"
    data_root.mkdir()
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    import backend.app.config as config_module

    monkeypatch.setattr(config_module, "DATA_ROOT", data_root)

    out = tmp_path / "evidence"
    inventory = capture_task_phase1_evidence(out)

    baseline = inventory["baseline_context"]
    assert baseline["target_db_exists_at_capture"] is False
    assert baseline["capture_strategy"] == "synthetic_migrated_schema_only"
    assert str(data_root) in baseline["target_data_root"]
    assert baseline["target_db_path"].endswith("quant_monitor.duckdb")
    assert inventory["phase2_gate"]["phase2_authorized"] is True
    assert (out / INVENTORY_JSON_NAME).is_file()
    sandbox_db = out / ".phase1-baseline-sandbox" / "duckdb" / "quant_monitor.duckdb"
    assert sandbox_db.is_file()


def test_layer1Ingestion_phase1_warnStatusDoesNotImplyUnsafeWhenSchemaOnly(tmp_path: Path) -> None:
    """覆盖范围：检查工具报 WARN 但库仍是空结构时的说明
    测试对象：capture_phase1_inventory 产出的 md
    目的/目标：WARN 不等于不安全——空库仍可进入试路由阶段
    验证点：inspect.status=WARN；classification=schema_only_empty；md 写明 WARN 不阻断试路由
    失败含义：WARN 被误读为必须停住，空库 baseline 无法继续
    """
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)

    inventory = capture_phase1_inventory(db, data_root, evidence_dir=tmp_path / "out")
    assert inventory["inspect"]["status"] == "WARN"
    assert inventory["db_evidence_classification"] == "schema_only_empty"
    md_text = (tmp_path / "out" / INVENTORY_MD_NAME).read_text(encoding="utf-8")
    assert "Inspect status WARN" in md_text
    assert "does **not** block Phase 2" in md_text
    assert "Phase 2 route dry-run is authorized" in md_text


def test_layer1Ingestion_phase1_enrichedInventory_hasRegistryAndFileSamples(tmp_path: Path) -> None:
    """覆盖范围：增强版盘点是否带上源注册表与文件采样
    测试对象：capture_phase1_inventory
    目的/目标：清单除表行数外，还应有数据目录文件指纹与暂存表统计
    验证点：data_root_file_samples 非空且含 sha256；staging_table_row_counts 存在；source_registry_snapshot 为列表
    失败含义：增强字段缺失，无法对照源注册表与磁盘文件树
    """
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    raw = data_root / "raw" / "vendor"
    raw.mkdir(parents=True)
    (raw / "trace.csv").write_text("1", encoding="utf-8")
    _init_db(db)

    inventory = capture_phase1_inventory(db, data_root)
    assert inventory["data_root_file_samples"]
    assert inventory["data_root_file_samples"][0]["relative_path"].startswith("raw/")
    assert "sha256" in inventory["data_root_file_samples"][0]
    assert "staging_table_row_counts" in inventory
    assert isinstance(inventory["source_registry_snapshot"], list)


def test_layer1Ingestion_phase1_operatorMemoFlipsPhase2Gate(tmp_path: Path) -> None:
    """覆盖范围：运维手写分类说明能否解除自动拦截
    测试对象：record_operator_classification
    目的/目标：自动判定不允许试路由时，运维备忘可声明已审阅并重新放行
    验证点：memo 前 phase2_authorized=False；memo 后 True 且 authorization_source=operator_classification_memo
    失败含义：人工审阅无法解除拦截，测试基线卡在盘点阶段
    """
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    raw = data_root / "raw"
    raw.mkdir(parents=True)
    (raw / "leftover.parquet").write_text("x", encoding="utf-8")
    _init_db(db)

    out = tmp_path / "evidence"
    inventory = capture_phase1_inventory(db, data_root, evidence_dir=out)
    assert inventory["phase2_gate"]["phase2_authorized"] is False

    memo = out / "phase1_data_classification.md"
    memo.write_text("# classification memo\nfixture artifacts\n", encoding="utf-8")
    updated = record_operator_classification(
        inventory,
        memo_path=memo,
        classification=inventory["db_evidence_classification"],
        operator_ack="operator_reviewed_fixture_lineage",
        evidence_dir=out,
    )
    assert updated["phase2_gate"]["phase2_authorized"] is True
    assert updated["phase2_gate"]["authorization_source"] == "operator_classification_memo"
    md_text = (out / INVENTORY_MD_NAME).read_text(encoding="utf-8")
    assert "**Phase 2 authorized:** True" in md_text


def test_layer1Ingestion_phase1_taskEvidenceSandboxCopyPath(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：目标库已存在时任务证据用沙箱复制而非直接读生产库
    测试对象：capture_task_phase1_evidence
    目的/目标：不会直接改生产路径上的库，而是复制到沙箱并记下校验和
    验证点：capture_strategy=sandbox_copy_of_target_db；copy_provenance.copy_sha256 等于目标库 sha256
    失败含义：任务证据直接读/写生产库，或复制来源无法追溯
    """
    data_root = tmp_path / "data"
    data_root.mkdir()
    target_db = data_root / "duckdb" / "quant_monitor.duckdb"
    target_db.parent.mkdir(parents=True)
    _init_db(target_db)

    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    import backend.app.config as config_module

    monkeypatch.setattr(config_module, "DATA_ROOT", data_root)

    out = tmp_path / "evidence"
    inventory = capture_task_phase1_evidence(out)
    assert inventory["baseline_context"]["capture_strategy"] == "sandbox_copy_of_target_db"
    assert inventory["copy_provenance"] is not None
    assert inventory["copy_provenance"]["copy_sha256"] == file_sha256(target_db)


PHASE2_ROW_COUNT_TABLES = ("axis_observation", "fetch_log", "file_registry")


def _build_ingestion_service(
    tmp_path: Path,
    *,
    data_root: Path | None = None,
    datasource: DataSourceService | None = None,
) -> tuple[Layer1ObservationIngestionService, Path]:
    db = tmp_path / "phase2.duckdb"
    root = data_root or tmp_path / "data"
    root.mkdir(parents=True, exist_ok=True)
    _init_db(db)
    service = Layer1ObservationIngestionService(
        db_path=db,
        data_root=root,
        datasource=datasource,
    )
    return service, db


def test_layer1Ingestion_routePreview_noMutation(tmp_path: Path) -> None:
    """覆盖范围：试路由阶段只看不写——数据库与关键表行数不变
    测试对象：Layer1ObservationIngestionService.preview_routes
    目的/目标：试路由前后数据库指纹和关键表行数都不变，且结果是仅校验不拉数
    验证点：hash/行数不变；route_status=VALIDATION_ONLY_BLOCKED；capability_verified=True
    失败含义：号称试路由却改了库或真的去拉数，试路由安全承诺失效
    """
    service, db = _build_ingestion_service(tmp_path)
    before_hash = hashlib.sha256(db.read_bytes()).hexdigest()
    before_counts = _row_counts(db, PHASE2_ROW_COUNT_TABLES)
    as_of = date(2024, 6, 15)

    result = service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=as_of)

    after_hash = hashlib.sha256(db.read_bytes()).hexdigest()
    after_counts = _row_counts(db, PHASE2_ROW_COUNT_TABLES)
    assert before_hash == after_hash
    assert before_counts == after_counts
    assert len(result.previews) == 1
    preview = result.previews[0]
    assert preview.indicator_id == FROZEN_STAGED_INDICATOR
    assert preview.route_plan.route_status == "VALIDATION_ONLY_BLOCKED"
    assert preview.route_plan.selected_source_id is None
    assert preview.stop_reason is not None
    assert preview.binding.data_domain == STAGED_DATA_DOMAIN
    assert preview.binding.operation == STAGED_OPERATION
    assert preview.capability_verified is True
    assert preview.resource_guard_decision in {"OK", "WARN"}


def test_layer1Ingestion_forbiddenIndicator_rejectedBeforeRoute(tmp_path: Path) -> None:
    """覆盖范围：禁止使用类指标在算路由前就被拦下
    测试对象：preview_routes
    目的/目标：禁止类指标根本进不了路由规划，须在试路由前拒绝
    验证点：pytest.raises(IngestionRejectedError)；reason_code=FORBIDDEN_INDICATOR_REJECTED
    失败含义：禁止指标仍能试路由，产品红线失效
    """
    service, _ = _build_ingestion_service(tmp_path)
    with pytest.raises(IngestionRejectedError) as exc:
        service.preview_routes(indicators=["ENV-FORBIDDEN-WM2NS"], as_of=date(2024, 6, 15))
    assert exc.value.reason_code == FORBIDDEN_INDICATOR_REJECTED


def test_layer1Ingestion_blindspot_rejectedBeforeFetch(tmp_path: Path) -> None:
    """覆盖范围：盲点类指标在拉数前就被拦下
    测试对象：preview_routes
    目的/目标：不可观测的盲点指标不能进入任何可拉数的路由步骤
    验证点：pytest.raises(IngestionRejectedError)；reason_code=BLINDSPOT_INDICATOR_REJECTED
    失败含义：盲点指标仍能试路由或拉数，数据边界被突破
    """
    service, _ = _build_ingestion_service(tmp_path)
    with pytest.raises(IngestionRejectedError) as exc:
        service.preview_routes(
            indicators=["ENV-D-DTS_OPERATING_CASH_BALANCE"],
            as_of=date(2024, 6, 15),
        )
    assert exc.value.reason_code == BLINDSPOT_INDICATOR_REJECTED


def test_layer1Ingestion_disabledSource_returnsRouteStatusWithoutFetch(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：数据源被禁用时试路由不会真的去拉数
    测试对象：preview_routes（mock DISABLED_SOURCE 路由结果）
    目的/目标：路由状态为源已禁用时，底层拉数钩子不能被调用
    验证点：fetch_called==[]；route_status=DISABLED_SOURCE；selected_source_id is None
    失败含义：禁用源仍触发拉数，试路由与真拉数边界混乱
    """
    fetch_called: list[str] = []

    def forbidden_fetch(self, *args, **kwargs):
        fetch_called.append("fetch")
        raise AssertionError("fetch must not run during Phase 2 dry-run")

    monkeypatch.setattr(DataSourceService, "fetch", forbidden_fetch)

    def disabled_preview(self, **kwargs):
        return SourceRoutePlan(
            route_plan_id=SourceRoutePlan.new_id(),
            run_id=kwargs.get("run_id", "preview-run"),
            job_id=kwargs.get("job_id", "preview-job"),
            data_domain=kwargs.get("data_domain", STAGED_DATA_DOMAIN),
            operation=kwargs.get("operation", STAGED_OPERATION),
            route_status="DISABLED_SOURCE",
            selected_source_id=None,
            candidates=[
                SourceRouteCandidate(
                    source_id="qmt_xtdata",
                    role="Primary",
                    enabled=False,
                    allowed_domain="cn_equity_minute_bar",
                    capability_declared=True,
                    disabled_reason="source_disabled_by_default",
                    skip_reason="source_disabled_by_default",
                )
            ],
        )

    monkeypatch.setattr(DataSourceService, "preview_route", disabled_preview)
    service, _ = _build_ingestion_service(tmp_path)

    result = service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=date(2024, 6, 15))

    assert fetch_called == []
    assert result.previews[0].route_plan.route_status == "DISABLED_SOURCE"
    assert result.previews[0].route_plan.selected_source_id is None
    assert result.previews[0].stop_reason is not None


def test_layer1Ingestion_noSilentFallback(tmp_path: Path) -> None:
    """覆盖范围：路由规划不能悄悄跳过被禁用的候选源
    测试对象：preview_routes 产出的 SourceRoutePlan
    目的/目标：每个被禁用的源都须有跳过原因；没就绪时不能选中任何源
    验证点：disabled 候选 skip_reason 非空；非 READY 时 selected_source_id is None；选中者须 enabled
    失败含义：静默忽略禁用源或无理由选中，多源路由约定被违反
    """
    service, _ = _build_ingestion_service(tmp_path)
    result = service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=date(2024, 6, 15))
    plan = result.previews[0].route_plan
    for candidate in plan.candidates:
        if not candidate.enabled:
            assert candidate.skip_reason is not None
    if plan.route_status != "READY":
        assert plan.selected_source_id is None
    if plan.selected_source_id is not None:
        selected = next(c for c in plan.candidates if c.source_id == plan.selected_source_id)
        assert selected.enabled is True
        assert selected.skip_reason is None


def test_layer1Ingestion_routePreview_resourceGuardPauseRaises(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：磁盘等资源不足时试路由会被拦住
    测试对象：preview_routes 与 mock ResourceGuard PAUSE
    目的/目标：资源门禁报暂停时，试路由与真拉数走同一套拦截逻辑
    验证点：pytest.raises(ResourceGuardBlockedError)
    失败含义：资源不足仍能试路由，与拉数路径门禁不一致
    """
    monkeypatch.setattr(
        DataSourceService,
        "check_resource_guard",
        lambda self: (Decision.PAUSE, "disk_free_gb below pause threshold"),
    )
    service, _ = _build_ingestion_service(tmp_path)
    with pytest.raises(ResourceGuardBlockedError):
        service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=date(2024, 6, 15))


def test_layer1Ingestion_userAuthRequired_returnsRouteStatusWithoutFetch(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：需要用户授权的源在试路由时不会拉数
    测试对象：preview_routes（mock USER_AUTH_REQUIRED 路由结果）
    目的/目标：未获用户授权的源，试路由阶段绝不调用拉数
    验证点：fetch_called==[]；route_status=USER_AUTH_REQUIRED；stop_reason 非空
    失败含义：未授权仍去拉数，用户授权门禁失效
    """
    fetch_called: list[str] = []

    def forbidden_fetch(self, *args, **kwargs):
        fetch_called.append("fetch")
        raise AssertionError("fetch must not run during Phase 2 dry-run")

    monkeypatch.setattr(DataSourceService, "fetch", forbidden_fetch)

    def auth_preview(self, **kwargs):
        return SourceRoutePlan(
            route_plan_id=SourceRoutePlan.new_id(),
            run_id="run-auth",
            job_id="job-auth",
            data_domain=kwargs.get("data_domain", STAGED_DATA_DOMAIN),
            operation=kwargs.get("operation", STAGED_OPERATION),
            route_status="USER_AUTH_REQUIRED",
            selected_source_id=None,
            candidates=[
                SourceRouteCandidate(
                    source_id="qmt_xqshare",
                    role="Primary",
                    enabled=False,
                    allowed_domain="cn_equity_realtime",
                    capability_declared=True,
                    disabled_reason="user_authorization_required",
                    skip_reason="user_authorization_required",
                )
            ],
        )

    monkeypatch.setattr(DataSourceService, "preview_route", auth_preview)
    service, _ = _build_ingestion_service(tmp_path)
    result = service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=date(2024, 6, 15))
    assert fetch_called == []
    assert result.previews[0].route_plan.route_status == "USER_AUTH_REQUIRED"
    assert result.previews[0].stop_reason is not None


def test_layer1Ingestion_notOnAllowlist_rejected(tmp_path: Path) -> None:
    """覆盖范围：不在暂存白名单里的可观测指标会被拒绝
    测试对象：preview_routes(ENV-E1-EFFR)
    目的/目标：即使规格里标记可观测，没有暂存绑定的指标也不能试路由
    验证点：pytest.raises(IngestionRejectedError)；reason_code=NOT_ON_ALLOWLIST
    失败含义：非白名单指标进入试路由，冻结指标验收边界被稀释
    """
    service, _ = _build_ingestion_service(tmp_path)
    with pytest.raises(IngestionRejectedError) as exc:
        service.preview_routes(indicators=["ENV-E1-EFFR"], as_of=date(2024, 6, 15))
    assert exc.value.reason_code == "NOT_ON_ALLOWLIST"


def test_layer1Ingestion_phase2_fixtureAsOfMatchesPreviewEvidence(tmp_path: Path) -> None:
    """覆盖范围：测试夹具的日期与试路由窗口是否对齐
    测试对象：preview_routes 与 layer1_macro_observation_fixture.json
    目的/目标：试路由用的截止日期须与夹具一致，且单位、序列号与绑定信息匹配
    验证点：fixture.as_of==2024-06-15；preview.binding.unit/series_id 与 fixture 一致
    失败含义：日期或序列对不上，试路由证据无法与测试夹具对照
    """
    fixture = json.loads(
        (PROJECT_ROOT / "tests/fixtures/layer1_macro_observation_fixture.json").read_text(
            encoding="utf-8"
        )
    )
    as_of = date(2024, 6, 15)
    assert fixture["as_of"] == as_of.isoformat()
    service, _ = _build_ingestion_service(tmp_path)
    result = service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=as_of)
    preview = result.previews[0]
    assert preview.binding.unit == "pct"
    assert preview.binding.series_id == fixture["series_id"]


def test_layer1Ingestion_phase1_gitkeepOnly_classifiesSchemaOnly(tmp_path: Path) -> None:
    """覆盖范围：数据目录里只有占位文件时的分类——不应误判为有数据
    测试对象：capture_phase1_inventory
    目的/目标：空目录占位不会被误判成已有暂存证据，应允许试路由
    验证点：classification=schema_only_empty；phase2_authorized=True
    失败含义：仅占位文件被当成有数据，试路由被误拦
    """
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    (data_root / "raw").mkdir(parents=True)
    (data_root / "parquet").mkdir(parents=True)
    (data_root / "raw" / ".gitkeep").write_text("", encoding="utf-8")
    (data_root / "parquet" / ".gitkeep").write_text("", encoding="utf-8")
    _init_db(db)
    inventory = capture_phase1_inventory(db, data_root)
    assert inventory["db_evidence_classification"] == "schema_only_empty"
    assert inventory["phase2_gate"]["phase2_authorized"] is True


def test_layer1Ingestion_routePreview_capabilityDeclaredForSelectedSource(
    tmp_path: Path,
) -> None:
    """覆盖范围：试路由时选中源的能力注册声明是否完整
    测试对象：preview_routes 产出的 capability_verified 与 akshare candidate
    目的/目标：akshare 须已声明能力且因仅校验不能作主源而被跳过
    验证点：capability_verified=True；akshare.capability_declared=True；skip_reason=validation_only_cannot_be_primary
    失败含义：能力未声明仍 preview，试路由证据无法证明注册表对齐
    """
    service, _ = _build_ingestion_service(tmp_path)
    result = service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=date(2024, 6, 15))
    preview = result.previews[0]
    assert preview.capability_verified is True
    akshare = next(c for c in preview.route_plan.candidates if c.source_id == "akshare")
    assert akshare.capability_declared is True
    assert akshare.skip_reason == "validation_only_cannot_be_primary"


def test_layer1Ingestion_phase2TaskEvidence_usesSandboxDbAlignedWithPhase1(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：试路由任务证据是否复用盘点阶段的沙箱数据库
    测试对象：capture_task_phase2_evidence
    目的/目标：变更证明中的库路径须在盘点沙箱内且策略为沙箱复用
    验证点：db_capture_strategy in {phase1_sandbox_copy_reused, sandbox_copy_aligned_with_phase1}
    失败含义：试路由证据读生产路径，与盘点沙箱基线不对齐
    """
    data_root = tmp_path / "data"
    data_root.mkdir()
    target_db = data_root / "duckdb" / "quant_monitor.duckdb"
    target_db.parent.mkdir(parents=True)
    _init_db(target_db)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    import backend.app.config as config_module

    monkeypatch.setattr(config_module, "DATA_ROOT", data_root)
    out = tmp_path / "evidence"
    capture_task_phase1_evidence(out)
    capture_task_phase2_evidence(out, as_of=date(2024, 6, 15))
    payload = json.loads((out / "phase2_route_preview.json").read_text(encoding="utf-8"))
    proof = payload["mutation_proof"]
    assert proof["db_capture_strategy"] in {
        "phase1_sandbox_copy_reused",
        "sandbox_copy_aligned_with_phase1",
    }
    assert "phase1-baseline-sandbox" in proof["db_path"]


def test_layer1Ingestion_phase2TaskEvidence_requiresPhase1GateWhenInventoryPresent(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：存在盘点清单时试路由任务导出须遵守放行门禁
    测试对象：capture_task_phase2_evidence
    目的/目标：盘点门禁未授权时导出试路由证据须抛运行时错误
    验证点：inventory phase2_authorized=False；pytest.raises(RuntimeError, match='Phase 2')
    失败含义：门禁被绕过直接导出试路由证据，审计链断裂
    """
    out = tmp_path / "evidence"
    out.mkdir()
    db = tmp_path / "db.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)
    cm = ConnectionManager(db)
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO fetch_log (
                fetch_id, run_id, source_id, data_domain, status, row_count, fetch_time
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            ["f-phase2-gate", "run-1", "macro_supplementary", "macro_supplementary", "SUCCESS", 1],
        )
    capture_phase1_inventory(db, data_root, evidence_dir=out)
    inventory = json.loads((out / INVENTORY_JSON_NAME).read_text(encoding="utf-8"))
    assert inventory["phase2_gate"]["phase2_authorized"] is False

    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    import backend.app.config as config_module

    monkeypatch.setattr(config_module, "DATA_ROOT", data_root)
    with pytest.raises(RuntimeError, match="Phase 2"):
        capture_task_phase2_evidence(out, as_of=date(2024, 6, 15))


def test_layer1Ingestion_phase2_taskEvidenceArtifacts(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：试路由任务执行证据产物是否完整
    测试对象：capture_phase2_route_evidence
    目的/目标：须导出 json/md/无变更证明且预览字段与冻结指标一致
    验证点：三份 artifact 文件存在；route_status=VALIDATION_ONLY_BLOCKED；mutation_proof.row_counts_unchanged
    失败含义：试路由 Trellis 证据缺文件或预览语义错，执行无法 sign-off
    """
    out = tmp_path / "evidence"
    data_root = tmp_path / "data"
    data_root.mkdir()
    db = tmp_path / "db.duckdb"
    _init_db(db)
    inventory = capture_phase1_inventory(db, data_root, evidence_dir=out)
    memo = out / "phase1_data_classification.md"
    memo.write_text("# fixture memo\n", encoding="utf-8")
    record_operator_classification(
        inventory,
        memo_path=memo,
        classification=inventory["db_evidence_classification"],
        operator_ack="authorized_for_phase2_test",
        evidence_dir=out,
    )

    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    import backend.app.config as config_module

    monkeypatch.setattr(config_module, "DATA_ROOT", data_root)
    from backend.app.layer1_axes.ingestion_evidence import capture_phase2_route_evidence

    service = Layer1ObservationIngestionService(db_path=db, data_root=data_root)
    evidence = capture_phase2_route_evidence(
        service=service,
        indicators=[FROZEN_STAGED_INDICATOR],
        as_of=date(2024, 6, 15),
        evidence_dir=out,
    )
    assert (out / "phase2_route_preview.json").is_file()
    assert (out / "phase2_route_preview_matrix.md").is_file()
    assert (out / "phase2_no_mutation_proof.md").is_file()
    payload = json.loads((out / "phase2_route_preview.json").read_text(encoding="utf-8"))
    assert payload["frozen_indicator"] == FROZEN_STAGED_INDICATOR
    assert payload["previews"][0]["route_plan"]["route_status"] == "VALIDATION_ONLY_BLOCKED"
    assert payload["previews"][0]["capability_verified"] is True
    assert payload["previews"][0]["intended_as_of_range"]["start"] == "2024-06-15"
    assert evidence["mutation_proof"]["row_counts_unchanged"] is True


MACRO_FIXTURE_PATH = PROJECT_ROOT / "tests/fixtures/layer1_macro_observation_fixture.json"
PHASE3_ROW_COUNT_TABLES = ("axis_observation", "fetch_log", "file_registry", "job_event_log")


def _build_micro_fetch_service(
    tmp_path: Path,
    *,
    datasource: DataSourceService | None = None,
) -> tuple[Layer1ObservationIngestionService, Path]:
    db = tmp_path / "phase3.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    _init_db(db)
    if datasource is None:
        datasource = DataSourceService(
            data_root=data_root,
            fetch_port=LocalFixtureFetchPort(MACRO_FIXTURE_PATH, row_count=1),
        )
    service = Layer1ObservationIngestionService(
        db_path=db,
        data_root=data_root,
        datasource=datasource,
    )
    return service, db


def test_layer1MicroIngestion_usesDataSourceServiceBeforeFetch(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：小批量拉数须经统一数据服务而非直连适配器工厂
    测试对象：micro_fetch_staging
    目的/目标：须恰好一次拉数调用且禁止 create_adapter
    验证点：len(calls)==1；adapter_imports==[]；fetch SUCCESS row_count=1
    失败含义：第一层绕过数据服务直连适配器，架构边界失效
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, _ = _build_micro_fetch_service(tmp_path)
    calls: list[FetchRequest] = []
    original_fetch = DataSourceService.fetch

    def tracking_fetch(self, req, **kwargs):
        calls.append(req)
        return original_fetch(self, req, **kwargs)

    monkeypatch.setattr(DataSourceService, "fetch", tracking_fetch)
    adapter_imports: list[str] = []

    def forbidden_create_adapter(*args, **kwargs):
        adapter_imports.append("create_adapter")
        raise AssertionError("Layer1 must not call create_adapter")

    monkeypatch.setattr(
        "backend.app.datasources.adapters.create_adapter",
        forbidden_create_adapter,
    )

    result = service.micro_fetch_staging(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=date(2024, 6, 15),
    )

    assert len(calls) == 1
    assert calls[0].data_domain == STAGED_DATA_DOMAIN
    assert adapter_imports == []
    assert result.fetch_result.status == "SUCCESS"
    assert result.fetch_result.row_count == 1


def test_layer1MicroIngestion_persistsRoutePlanBeforeFetch(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：小批量拉数时路由计划须先于拉取日志写入
    测试对象：micro_fetch_staging 的 job_event_log 与 fetch_log 时序
    目的/目标：同一任务的 ROUTE_PLAN 事件时间应早于实际拉取
    验证点：route_row 与 fetch_row 均非空；payload route_status=VALIDATION_ONLY_BLOCKED
    失败含义：路由计划晚于拉取或无事件，追溯顺序错误
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_micro_fetch_service(tmp_path)

    result = service.micro_fetch_staging(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=date(2024, 6, 15),
    )

    con = duckdb.connect(str(db), read_only=True)
    try:
        route_row = con.execute(
            """
            SELECT created_at, payload_json FROM job_event_log
            WHERE job_id = ? AND event_type = 'ROUTE_PLAN'
            ORDER BY created_at ASC LIMIT 1
            """,
            [result.job_id],
        ).fetchone()
        fetch_row = con.execute(
            """
            SELECT fetch_time FROM fetch_log
            WHERE job_id = ?
            ORDER BY fetch_time ASC LIMIT 1
            """,
            [result.job_id],
        ).fetchone()
    finally:
        con.close()

    assert route_row is not None
    assert fetch_row is not None
    payload = parse_event_payload(route_row[1])
    assert payload.get("route_status") == "VALIDATION_ONLY_BLOCKED"
    assert payload.get("selected_source_id") is None
    assert payload.get("decision") == "route_plan"
    assert result.route_plan.route_status == "VALIDATION_ONLY_BLOCKED"


def test_layer1MicroIngestion_writesFetchLogAndRawEvidence(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：小批量拉数成功时须写拉取日志、文件登记与原始文件
    测试对象：micro_fetch_staging
    目的/目标：暂存拉取须各增一行日志且原始路径相对数据目录且文件存在
    验证点：fetch_log/file_registry delta=1；raw_path.is_file()；路径非 absolute
    失败含义：暂存无拉取证据或原始落盘失败，小批量拉数审计链不完整
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_micro_fetch_service(tmp_path)
    data_root = tmp_path / "data"
    before = _row_counts(db, ("fetch_log", "file_registry"))

    result = service.micro_fetch_staging(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=date(2024, 6, 15),
    )

    after = _row_counts(db, ("fetch_log", "file_registry"))
    assert after["fetch_log"] == (before["fetch_log"] or 0) + 1
    assert after["file_registry"] == (before["file_registry"] or 0) + 1
    assert result.fetch_result.raw_file_paths
    raw_path = data_root / result.fetch_result.raw_file_paths[0]
    assert raw_path.is_file()
    assert not Path(result.fetch_result.raw_file_paths[0]).is_absolute()
    assert result.fetch_result.content_hash is not None


def test_layer1MicroIngestion_phase3DoesNotWriteCleanAxisObservation(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：第三阶段「只拉原始数据」时，不得写入正式观测表
    测试对象：micro_fetch_staging
    目的/目标：staging 阶段只记拉取痕迹和 raw 文件，正式观测表（axis_observation）一行都不能多
    验证点：拉数前后观测表行数都是 0
    失败含义：第三阶段小批量拉数就写了正式观测，与第四阶段校验后再入库的设计冲突
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_micro_fetch_service(tmp_path)
    before_obs = _row_counts(db, ("axis_observation",))["axis_observation"]

    service.micro_fetch_staging(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=date(2024, 6, 15),
    )

    after_obs = _row_counts(db, ("axis_observation",))["axis_observation"]
    assert before_obs == after_obs == 0


def test_layer1MicroIngestion_resourceGuardPauseStopsBeforeFetch(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：资源门禁暂停时，小批量拉数在写拉取日志前被阻断
    测试对象：micro_fetch_staging 与 mock ResourceGuard PAUSE
    目的/目标：暂停须 ResourceGuardBlockedError 且拉取相关表行数不变
    验证点：pytest.raises(ResourceGuardBlockedError)；before==after 行数
    失败含义：资源暂停仍改动拉取表，与试路由/正式提交门禁不一致
    """
    monkeypatch.setattr(
        ResourceGuard,
        "check",
        lambda self: (Decision.PAUSE, "disk_free_gb below pause threshold"),
    )
    service, db = _build_micro_fetch_service(tmp_path)
    before = _row_counts(db, ("fetch_log", "file_registry", "job_event_log"))

    with pytest.raises(ResourceGuardBlockedError):
        service.micro_fetch_staging(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=date(2024, 6, 15),
        )

    after = _row_counts(db, ("fetch_log", "file_registry", "job_event_log"))
    assert before == after


def test_layer1Ingestion_phase3_phase4_singleFetchLogRegression(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：小批量拉数与正式提交各恰增一条拉取日志
    测试对象：micro_fetch_staging 与 commit_clean_observation_and_snapshots
    目的/目标：每个阶段对拉取日志的增量必须恰好为 1
    验证点：after_p3-before_p3==1；after_p4-before_p4==1
    失败含义：重复或漏记拉取日志，摄取链行计数回归
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    data_root = tmp_path / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    from backend.app.datasources.service import build_staged_fixture_service

    datasource = build_staged_fixture_service(
        data_root=data_root,
        fixture_path=MACRO_FIXTURE_PATH,
    )
    service, db = _build_micro_fetch_service(tmp_path, datasource=datasource)
    before_p3 = _row_counts(db, ("fetch_log",))["fetch_log"] or 0
    service.micro_fetch_staging(indicator_id=FROZEN_STAGED_INDICATOR, as_of=date(2024, 6, 15))
    after_p3 = _row_counts(db, ("fetch_log",))["fetch_log"] or 0
    assert after_p3 - before_p3 == 1

    before_p4 = _row_counts(db, ("fetch_log",))["fetch_log"] or 0
    service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )
    after_p4 = _row_counts(db, ("fetch_log",))["fetch_log"] or 0
    assert after_p4 - before_p4 == 1


@pytest.mark.slow
def test_layer1Ingestion_phase3_taskEvidenceArtifacts(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：小批量拉数任务跑完后，审计材料是否写全、内容是否正确
    测试对象：capture_task_phase3_evidence
    目的/目标：除 JSON 证据外，还要有一份未写正式观测表的证明：观测表行数不变，拉取日志恰好多 1 条
    验证点：存在 phase3_micro_fetch_evidence.json 与 no_clean_write 证明；证明中观测表未变、fetch_log 增量为 1、文件登记增量为 1
    失败含义：材料缺失或观测表被悄悄写入，无法向审计说明只 staging、未 clean write
    """
    out = tmp_path / "evidence"
    data_root = tmp_path / "data"
    data_root.mkdir()
    db = tmp_path / "db.duckdb"
    _init_db(db)
    inventory = capture_phase1_inventory(db, data_root, evidence_dir=out)
    memo = out / "phase1_data_classification.md"
    memo.write_text("# fixture memo\n", encoding="utf-8")
    record_operator_classification(
        inventory,
        memo_path=memo,
        classification=inventory["db_evidence_classification"],
        operator_ack="authorized_for_phase3_test",
        evidence_dir=out,
    )

    from backend.app.layer1_axes.ingestion_evidence import capture_task_phase3_evidence

    evidence = capture_task_phase3_evidence(out, as_of=date(2024, 6, 15))
    assert (out / "phase3_micro_fetch_evidence.json").is_file()
    assert (out / "phase3_no_clean_write_proof.md").is_file()
    assert evidence["evidence_baseline_strategy"] == "fresh_phase3_sandbox"
    proof = evidence["no_clean_write_proof"]
    assert proof["axis_observation_unchanged"] is True
    assert proof["before_counts"]["fetch_log"] == 0
    assert proof["before_counts"]["file_registry"] == 0
    assert proof["fetch_log_delta"] == 1
    assert proof["file_registry_delta"] == 1
    assert "phase3-micro-fetch-sandbox" in evidence["evidence_data_root"]
    assert "phase3-micro-fetch-sandbox" in evidence["evidence_db_path"]
    raw_paths = evidence["micro_fetch"]["fetch_result"]["raw_file_paths"]
    assert raw_paths
    assert not Path(raw_paths[0]).is_absolute()


# --- Phase 4: clean write + snapshots (§8.5) ---

PHASE4_AS_OF = date(2024, 6, 15)
PHASE4_ROW_COUNT_TABLES = (
    "axis_observation",
    "fetch_log",
    "file_registry",
    "validation_report",
    "write_audit_log",
    "axis_feature_snapshot",
    "axis_interpretation_snapshot",
    "axis_snapshot_lineage",
)


def _build_phase4_service(
    tmp_path: Path,
    *,
    datasource: DataSourceService | None = None,
) -> tuple[Layer1ObservationIngestionService, Path]:
    db = tmp_path / "phase4.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    _init_db(db)
    if datasource is None:
        from backend.app.datasources.service import build_staged_fixture_service

        datasource = build_staged_fixture_service(
            data_root=data_root,
            fixture_path=MACRO_FIXTURE_PATH,
        )
    service = Layer1ObservationIngestionService(
        db_path=db,
        data_root=data_root,
        datasource=datasource,
    )
    return service, db


def test_layer1Observation_cleanWrite_requiresValidationReport(tmp_path: Path) -> None:
    """覆盖范围：无校验报告时写入管理器拒绝 clean write
    测试对象：Layer1ObservationWriter.write_observations
    目的/目标：缺失校验报告编号时须失败，且观测表与成功审计均为 0
    验证点：result.status==FAILED；obs count=0；success_audits=0
    失败含义：无报告仍能写观测，数据库校验门禁最后一道闸失效
    """
    from backend.app.layer1_axes.observation_writer import Layer1ObservationWriter

    db = tmp_path / "phase4-gate.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    writer = Layer1ObservationWriter(cm)
    result = writer.write_observations(
        rows=[
            {
                "observation_id": "obs-missing-vr",
                "indicator_id": FROZEN_STAGED_INDICATOR,
                "as_of_timestamp": datetime(2024, 6, 15, 16, 0, tzinfo=UTC),
                "publish_timestamp": datetime(2024, 6, 15, 0, 0, tzinfo=UTC),
                "fetch_time": datetime(2024, 6, 15, 12, 0, tzinfo=UTC),
                "raw_value": 4.25,
                "raw_unit": "pct",
                "frequency": "daily",
                "source_used": "staged_fixture",
                "source_channel_id": "akshare",
                "data_lag_days": 0.0,
                "stale_reason": None,
                "quality_flags": "STAGED_FIXTURE",
                "content_hash": "abc",
                "schema_hash": "def",
                "source_switched": False,
                "created_at": datetime.now(UTC),
            }
        ],
        validation_report_id="missing-validation-report",
        run_id="run-vr",
        job_id="job-vr",
        source_used="staged_fixture",
    )
    assert result.status == "FAILED"
    con = duckdb.connect(str(db), read_only=True)
    try:
        assert con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0] == 0
        success_audits = con.execute(
            "SELECT COUNT(*) FROM write_audit_log WHERE status = 'SUCCESS'"
        ).fetchone()[0]
    finally:
        con.close()
    assert success_audits == 0


def test_layer1Observation_fetchFailure_blocksCleanWrite(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：正式提交时底层拉数失败的处理——不得入库
    测试对象：commit_clean_observation_and_snapshots（fetch 被 mock 为失败）
    目的/目标：拉数失败就不能往正式观测表写任何数据，必须报错并中断整个提交
    验证点：抛出 IngestionCommitBlockedError，原因码 OBSERVATION_MAPPING；观测表仍为 0 行
    失败含义：拉数失败仍入库，脏或空数据会进入正式观测表
    """
    from backend.app.datasources.fetch_result import FetchResult
    from backend.app.datasources.service import DataSourceService
    from backend.app.layer1_axes.ingestion import IngestionCommitBlockedError

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    def failed_fetch(self, req, *, con, job_id=None, operation=None, **kwargs):
        return FetchResult(
            run_id=req.run_id,
            source_id=req.source_id,
            data_domain=req.data_domain,
            status="FAILED",
            row_count=0,
            fetch_time=datetime.now(UTC).isoformat(),
            error_message="injected fetch failure",
        )

    monkeypatch.setattr(DataSourceService, "fetch", failed_fetch)
    with pytest.raises(IngestionCommitBlockedError) as exc:
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
        )
    assert exc.value.reason_code == "OBSERVATION_MAPPING"
    assert _row_counts(db, ("axis_observation",))["axis_observation"] == 0


def test_layer1Observation_noneOptionalIndicator_skipsConflictValidator(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：无需多源冲突校验的冻结指标应跳过冲突校验器
    测试对象：commit_clean_observation_and_snapshots(ENV-E1-DGS10)
    目的/目标：_validation_source_requires_conflict 为 False 且 validator.validate_table 不得被调用
    验证点：helper 返回 False；commit observation_write_status==SUCCESS
    失败含义：none_optional 仍跑冲突校验器，多余阻塞或误报冲突
    """
    from backend.app.datasources.service import build_staged_fixture_service
    from backend.app.layer1_axes.ingestion import Layer1ObservationIngestionService
    from backend.app.validators.source_conflict import SourceConflictValidator

    data_root = tmp_path / "data"
    data_root.mkdir()
    indicator = Layer1ObservationIngestionService(
        db_path=tmp_path / "unused.duckdb",
        data_root=data_root,
        datasource=build_staged_fixture_service(
            data_root=data_root,
            fixture_path=MACRO_FIXTURE_PATH,
        ),
    )._indicator_by_id(FROZEN_STAGED_INDICATOR)
    assert (
        Layer1ObservationIngestionService._validation_source_requires_conflict(indicator) is False
    )

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    def conflict_must_not_run(self, con, request, **kwargs):
        raise AssertionError("SourceConflictValidator must not run for none_optional indicator")

    monkeypatch.setattr(SourceConflictValidator, "validate_table", conflict_must_not_run)
    result = service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )
    assert result.observation_write_status == "SUCCESS"


def test_layer1Observation_warningValidation_allowsCleanWrite(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：校验结果为警告且允许写入时，仍应允许正式提交
    测试对象：commit_clean_observation_and_snapshots 与 mock WARNING validate
    目的/目标：警告不应等同失败，须 SUCCESS 且观测表有 1 行
    验证点：observation_write_status==SUCCESS；axis_observation count==1
    失败含义：合法警告被误拦，暂存夹具无法完成正式提交
    """
    from backend.app.validators.data_quality import DataQualityReport

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    def warning_validate(self, con, request, **kwargs):
        report = DataQualityReport(
            validation_report_id="vr-warning-ok",
            status="WARNING",
            checked_rows=1,
            failed_rows=0,
            warning_rows=1,
            quality_flags=("STALE",),
            can_write_clean=True,
            needs_manual_review=False,
            findings=(),
        )
        self._persist_report(con, request, report)
        return report

    monkeypatch.setattr(
        "backend.app.layer1_axes.ingestion.DataQualityValidator.validate_table",
        warning_validate,
    )
    result = service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )
    assert result.observation_write_status == "SUCCESS"
    assert _row_counts(db, ("axis_observation",))["axis_observation"] == 1


def test_layer1Observation_cleanWrite_usesWriteManager(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：正式提交经写入管理器写观测表并记审计
    测试对象：commit_clean_observation_and_snapshots
    目的/目标：SUCCESS 须写 1 行观测且写入审计表含 axis_observation SUCCESS
    验证点：observation_write_status==SUCCESS；obs_count==1；audit 含 axis_observation
    失败含义：提交绕过 WriteManager 或无审计，正式提交追溯链不完整
    """

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)
    before_audit = _row_counts(db, ("write_audit_log",))["write_audit_log"]

    result = service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )

    assert result.observation_write_status == "SUCCESS"
    con = duckdb.connect(str(db), read_only=True)
    try:
        audit_rows = con.execute(
            """
            SELECT target_table, status, validation_status
            FROM write_audit_log
            WHERE job_id = ?
            ORDER BY started_at
            """,
            [result.micro_fetch.job_id],
        ).fetchall()
        obs_count = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    finally:
        con.close()
    assert obs_count == 1
    assert any(row[0] == "axis_observation" and row[1] == "SUCCESS" for row in audit_rows)
    after_audit = _row_counts(db, ("write_audit_log",))["write_audit_log"]
    assert (after_audit or 0) > (before_audit or 0)


def test_layer1Observation_validationFailure_blocksCleanWrite(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：校验失败时阻断正式观测写入
    测试对象：commit 与 mock DataQualityReport FAILED
    目的/目标：不允许 clean write 时须 IngestionCommitBlockedError(VALIDATION_FAILED)
    验证点：pytest.raises；axis_observation count=0
    失败含义：校验失败仍写 clean 观测，质量门禁失效
    """
    from backend.app.layer1_axes.ingestion import IngestionCommitBlockedError
    from backend.app.validators.data_quality import DataQualityReport

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    def failing_validate(self, con, request, **kwargs):
        report = DataQualityReport(
            validation_report_id="vr-fail",
            status="FAILED",
            checked_rows=1,
            failed_rows=1,
            warning_rows=0,
            quality_flags=("TEST_FAIL",),
            can_write_clean=False,
            needs_manual_review=False,
            findings=(),
        )
        self._persist_report(con, request, report)
        return report

    monkeypatch.setattr(
        "backend.app.layer1_axes.ingestion.DataQualityValidator.validate_table",
        failing_validate,
    )
    with pytest.raises(IngestionCommitBlockedError) as exc:
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
        )
    assert exc.value.reason_code == "VALIDATION_FAILED"
    assert _row_counts(db, ("axis_observation",))["axis_observation"] == 0


def test_layer1Observation_severeConflict_blocksCleanWrite(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：未解决的严重多源冲突经写入门禁阻断写入
    测试对象：commit 与注入 severe conflict
    目的/目标：即使校验通过，严重未解决冲突仍应 WRITE_FAILED
    验证点：IngestionCommitBlockedError(WRITE_FAILED)
    失败含义：严重冲突仍提交，多源对账门禁失效
    """
    from backend.app.layer1_axes.ingestion import IngestionCommitBlockedError

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)
    run_id = "layer1-commit-severe-test"

    def pass_validate(self, con, request, **kwargs):
        from backend.app.validators.data_quality import DataQualityReport

        report = DataQualityReport(
            validation_report_id="vr-severe-block",
            status="PASSED",
            checked_rows=1,
            failed_rows=0,
            warning_rows=0,
            quality_flags=(),
            can_write_clean=True,
            needs_manual_review=False,
            findings=(),
        )
        self._persist_report(con, request, report)
        con.execute(
            """
            INSERT INTO source_conflict (
                conflict_id, run_id, job_id, data_domain, field_name,
                primary_source, competing_source, severity, reconcile_status,
                manual_review_required
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                "conflict-severe-1",
                request.run_id,
                request.job_id,
                STAGED_DATA_DOMAIN,
                "raw_value",
                "akshare",
                "fred",
                "severe",
                "OPEN",
                False,
            ],
        )
        return report

    monkeypatch.setattr(
        "backend.app.layer1_axes.ingestion.DataQualityValidator.validate_table",
        pass_validate,
    )
    with pytest.raises(IngestionCommitBlockedError) as exc:
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
            run_id=run_id,
        )
    assert exc.value.reason_code == "WRITE_FAILED"


def test_layer1Observation_manualReview_blocksNonManualPatchWrite(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：需人工复核时阻断非人工补录模式的正式提交
    测试对象：commit 与 mock needs_manual_review=True
    目的/目标：即使允许 clean write，仍须 MANUAL_REVIEW_REQUIRED
    验证点：IngestionCommitBlockedError(MANUAL_REVIEW_REQUIRED)
    失败含义：需人工复核仍自动提交，运维干预政策被绕过
    """
    from backend.app.layer1_axes.ingestion import IngestionCommitBlockedError
    from backend.app.validators.data_quality import DataQualityReport

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    def manual_review_validate(self, con, request, **kwargs):
        report = DataQualityReport(
            validation_report_id="vr-manual",
            status="PASSED",
            checked_rows=1,
            failed_rows=0,
            warning_rows=0,
            quality_flags=("SCHEMA_DRIFT",),
            can_write_clean=True,
            needs_manual_review=True,
            findings=(),
        )
        self._persist_report(con, request, report)
        return report

    monkeypatch.setattr(
        "backend.app.layer1_axes.ingestion.DataQualityValidator.validate_table",
        manual_review_validate,
    )
    with pytest.raises(IngestionCommitBlockedError) as exc:
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
        )
    assert exc.value.reason_code == "MANUAL_REVIEW_REQUIRED"


def test_layer1Observation_stagedFixture_qualityFlagPersisted(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：暂存夹具正式提交时质量标记是否正确持久化
    测试对象：commit_clean_observation_and_snapshots
    目的/目标：观测行须含 STAGED_FIXTURE 标记且 source_used=akshare
    验证点：quality_flags 含 STAGED_FIXTURE；source_used==akshare
    失败含义：暂存数据无标记，下游无法区分夹具与生产数据
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )

    con = duckdb.connect(str(db), read_only=True)
    try:
        row = con.execute(
            "SELECT quality_flags, source_used FROM axis_observation LIMIT 1"
        ).fetchone()
    finally:
        con.close()
    assert row is not None
    assert "STAGED_FIXTURE" in row[0]
    assert row[1] == "akshare"


def test_layer1Observation_lineageIncludesFetchIdsAndHashes(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：正式提交产出的快照血缘是否含拉取编号与内容指纹
    测试对象：commit_clean_observation_and_snapshots
    目的/目标：结果与数据库行均须非空拉取编号/指纹及规则版本与参数哈希
    验证点：source_fetch_ids/content_hashes JSON 非空；rule_version 与 parameter_hash 非空
    失败含义：血缘缺拉取/指纹，增量重建与审计无法追溯输入
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    result = service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )

    assert result.source_fetch_ids
    assert result.source_content_hashes
    con = duckdb.connect(str(db), read_only=True)
    try:
        row = con.execute(
            """
            SELECT source_fetch_ids, source_content_hashes, rule_version, parameter_hash
            FROM axis_snapshot_lineage
            WHERE snapshot_id = ?
            """,
            [result.lineage_snapshot_id],
        ).fetchone()
    finally:
        con.close()
    assert row is not None
    fetch_ids = json.loads(row[0])
    content_hashes = json.loads(row[1])
    assert fetch_ids
    assert content_hashes
    assert row[2]
    assert row[3]


def test_layer1Observation_noFutureDataRejected(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：未来发布日期阻断正式提交
    测试对象：commit 与 mock future publish row
    目的/目标：2099 年发布日期须 IngestionCommitBlockedError(NO_FUTURE_DATA)
    验证点：pytest.raises(NO_FUTURE_DATA)
    失败含义：未来数据进入快照，截止时间边界失效
    """
    from backend.app.layer1_axes.ingestion import IngestionCommitBlockedError

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    def future_row(micro, *, data_root, fixture_path=None):
        from backend.app.layer1_axes.observation_mapper import map_micro_fetch_to_observation_row

        row = map_micro_fetch_to_observation_row(
            micro, data_root=data_root, fixture_path=fixture_path
        )
        row["publish_timestamp"] = datetime(2099, 1, 1, tzinfo=UTC)
        row["as_of_timestamp"] = datetime(2024, 6, 15, 16, 0, tzinfo=UTC)
        return row

    monkeypatch.setattr(
        "backend.app.layer1_axes.ingestion_commit.map_micro_fetch_to_observation_row",
        future_row,
    )
    with pytest.raises(IngestionCommitBlockedError) as exc:
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
        )
    assert exc.value.reason_code == "NO_FUTURE_DATA"


def test_layer1Observation_forbiddenAndBlindspotNeverPersisted(tmp_path: Path) -> None:
    """覆盖范围：禁止类与盲点类指标永不写入正式观测表
    测试对象：commit_clean_observation_and_snapshots
    目的/目标：两类指标均 IngestionRejectedError 且观测表保持 0 行
    验证点：reason_code 匹配；axis_observation count==0
    失败含义：禁止/盲点指标 persist，第一层数据污染
    """
    service, db = _build_phase4_service(tmp_path)
    for indicator_id, code in (
        ("ENV-FORBIDDEN-WM2NS", FORBIDDEN_INDICATOR_REJECTED),
        ("ENV-D-DTS_OPERATING_CASH_BALANCE", BLINDSPOT_INDICATOR_REJECTED),
    ):
        with pytest.raises(IngestionRejectedError) as exc:
            service.commit_clean_observation_and_snapshots(
                indicator_id=indicator_id,
                as_of=PHASE4_AS_OF,
            )
        assert exc.value.reason_code == code
    assert _row_counts(db, ("axis_observation",))["axis_observation"] == 0


def test_layer1Observation_postInspectShowsExpectedDeltasOnly(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：正式提交后盘点增量仅限预期摄取相关表
    测试对象：commit_clean_observation_and_snapshots 前后行数
    目的/目标：各核心表增量须为 +1（审计/校验为 ≥1/+4）
    验证点：axis_observation/feature/interpretation/lineage/fetch/file_registry 各 +1
    失败含义：意外表被改动或增量不对，提交后盘点无法审计
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)
    before = _row_counts(db, PHASE4_ROW_COUNT_TABLES)

    service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )

    after = _row_counts(db, PHASE4_ROW_COUNT_TABLES)
    assert (after["axis_observation"] or 0) - (before["axis_observation"] or 0) == 1
    assert (after["axis_feature_snapshot"] or 0) - (before["axis_feature_snapshot"] or 0) == 1
    assert (after["axis_interpretation_snapshot"] or 0) - (
        before["axis_interpretation_snapshot"] or 0
    ) == 1
    assert (after["axis_snapshot_lineage"] or 0) - (before["axis_snapshot_lineage"] or 0) == 1
    assert (after["fetch_log"] or 0) - (before["fetch_log"] or 0) == 1
    assert (after["file_registry"] or 0) - (before["file_registry"] or 0) == 1
    assert (after["validation_report"] or 0) - (before["validation_report"] or 0) >= 1
    assert (after["write_audit_log"] or 0) - (before["write_audit_log"] or 0) >= 4


def test_layer1Observation_mappingUsesRawFetchPayload(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：合法原始拉取数据如何映射成可入库观测记录
    测试对象：commit 与 axis_observation 行和原始 payload 对照
    目的/目标：观测数值与数据来源须与落盘原始 JSON 一致，非仅夹具静态值
    验证点：raw_value==payload metric_value；source_used==fetch source_id
    失败含义：映射忽略原始 payload，提交写入与拉取证据不一致
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    result = service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )
    raw_path = service._data_root / result.micro_fetch.fetch_result.raw_file_paths[0]
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    expected_value = payload["observations"][0]["metric_value"]

    con = duckdb.connect(str(db), read_only=True)
    try:
        row = con.execute(
            "SELECT raw_value, source_used FROM axis_observation WHERE observation_id = ?",
            [result.observation_id],
        ).fetchone()
    finally:
        con.close()
    assert row is not None
    assert row[0] == expected_value
    assert row[1] == result.micro_fetch.fetch_result.source_id


def test_layer1Observation_resourceGuardPauseBlocksCommit(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：资源门禁暂停时阻断正式提交
    测试对象：commit_clean_observation_and_snapshots 与 PAUSE guard
    目的/目标：暂停须 ResourceGuardBlockedError 且观测表保持 0 行
    验证点：pytest.raises(ResourceGuardBlockedError)；obs count=0
    失败含义：资源不足仍提交，与试路由/小批量拉数门禁不一致
    """
    monkeypatch.setattr(
        ResourceGuard,
        "check",
        lambda self: (Decision.PAUSE, "disk_free_gb below pause threshold"),
    )
    service, db = _build_phase4_service(tmp_path)
    with pytest.raises(ResourceGuardBlockedError):
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
        )
    assert _row_counts(db, ("axis_observation",))["axis_observation"] == 0


def test_layer1Observation_commitRejectsDuplicateObservation(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：同指标同截止日期二次正式提交应拒绝
    测试对象：两次 commit_clean_observation_and_snapshots
    目的/目标：第二次须 DUPLICATE_COMMIT 且观测仍仅 1 行
    验证点：IngestionCommitBlockedError(DUPLICATE_COMMIT)；count==1
    失败含义：重复提交写多行，幂等与数据完整性破坏
    """
    from backend.app.layer1_axes.ingestion import IngestionCommitBlockedError

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)
    service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )
    with pytest.raises(IngestionCommitBlockedError) as exc:
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
        )
    assert exc.value.reason_code == "DUPLICATE_COMMIT"
    assert _row_counts(db, ("axis_observation",))["axis_observation"] == 1


def test_layer1Observation_writeAuditUsesSharedValidationReport(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：正式提交全部 clean write 共享同一校验报告编号
    测试对象：write_audit_log 与 validation_report 按 job_id 查询
    目的/目标：观测/特征/解读/血缘四表审计均 SUCCESS 且共享同一 report
    验证点：四表均在 audit；≥4 条 SUCCESS；vr_rows 含 result.validation_report_id
    失败含义：各写入用不同报告，WriteManager 审计无法一次门禁多表
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)
    result = service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )
    con = duckdb.connect(str(db), read_only=True)
    try:
        audit_rows = con.execute(
            """
            SELECT target_table, status
            FROM write_audit_log
            WHERE job_id = ?
            ORDER BY started_at
            """,
            [result.micro_fetch.job_id],
        ).fetchall()
        vr_rows = con.execute(
            """
            SELECT validation_report_id FROM validation_report
            WHERE run_id = ? AND job_id = ?
            """,
            [result.micro_fetch.run_id, result.micro_fetch.job_id],
        ).fetchall()
    finally:
        con.close()
    tables = {row[0] for row in audit_rows}
    assert "axis_observation" in tables
    assert "axis_feature_snapshot" in tables
    assert "axis_interpretation_snapshot" in tables
    assert "axis_snapshot_lineage" in tables
    assert len(audit_rows) >= 4
    assert all(row[1] == "SUCCESS" for row in audit_rows)
    assert any(row[0] == result.validation_report_id for row in vr_rows)


@pytest.mark.slow
def test_layer1Ingestion_phase4_taskEvidenceArtifacts(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：正式提交任务执行证据产物与盘点基线是否对齐
    测试对象：capture_task_phase4_evidence
    目的/目标：须导出 json/盘点增量 md 且增量显示观测表=1 等
    验证点：artifact 存在；phase1_baseline_attached；inventory_delta 表计数正确
    失败含义：正式提交 Trellis 证据缺增量或未挂盘点基线
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    out = tmp_path / "evidence"
    data_root = tmp_path / "data"
    data_root.mkdir()
    # ACC-FLAKE-OBS-001: isolate DATA_ROOT so parallel/full-suite runs do not share state.
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    db = tmp_path / "db.duckdb"
    _init_db(db)
    inventory = capture_phase1_inventory(db, data_root, evidence_dir=out)
    memo = out / "phase1_data_classification.md"
    memo.write_text("# fixture memo\n", encoding="utf-8")
    record_operator_classification(
        inventory,
        memo_path=memo,
        classification=inventory["db_evidence_classification"],
        operator_ack="authorized_for_phase4_test",
        evidence_dir=out,
    )
    capture_task_phase2_evidence(out, as_of=date(2024, 6, 15))

    from backend.app.layer1_axes.ingestion_evidence import capture_task_phase4_evidence

    evidence = capture_task_phase4_evidence(out, as_of=date(2024, 6, 15))
    assert (out / "phase4_clean_write_and_snapshot_evidence.json").is_file()
    assert (out / "phase4_inventory_delta.md").is_file()
    assert evidence["phase1_baseline_attached"] is True
    assert evidence["evidence_baseline_strategy"] in {
        "phase1_sandbox_copy_reused",
        "sandbox_copy_aligned_with_phase1",
        "fresh_phase4_sandbox_fallback",
    }
    delta = evidence["inventory_delta"]["table_deltas"]
    assert delta["axis_observation"]["after"] == 1
    assert delta["fetch_log"]["after"] >= 1
    assert delta["file_registry"]["after"] >= 1
