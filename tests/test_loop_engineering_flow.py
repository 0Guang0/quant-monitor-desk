"""Loop 工程任务流重构门禁测试。

覆盖范围：LOOP_ENGINEERING_TASK_FLOW_REFACTOR_PLAN 的 P0–P4 落地物。
测试对象：authority_graph、context_router、test_catalog、verification matrix、
contract coverage、task evidence、project map 生成脚本。
目的：证明 agent 上下文路由、测试语义、AC 验证链、证据索引与项目地图机制可机械校验。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tests.contract_gate_support import PROJECT_ROOT

SCRIPTS = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from loop_engineering_common import (  # noqa: E402
    AUTHORITY_GRAPH_PATH,
    CONTRACT_COVERAGE_PATH,
    FEATURE_MATRIX_PATH,
    TEST_CATALOG_PATH,
    authority_graph_coverage_gaps,
    collect_module_authorities,
    deprecated_loop_meta_errors,
    discover_test_modules,
    discover_unmapped_backend_packages,
    infer_task_touched_paths,
    load_authority_graph,
    loop_required,
    modules_for_paths,
    normalize_ac_id,
    path_exists,
    task_track,
    write_loop_evidence_stubs,
)
from context_router import build_context_pack, validate_context_pack  # noqa: E402
from check_test_catalog import check_catalog  # noqa: E402
from check_verification_matrix import check_matrix  # noqa: E402
from check_contract_coverage import check_coverage  # noqa: E402

ROUND3_MODULES = (
    "layer1_axes",
    "layer2_sensors",
    "layer5_evidence",
    "datasources",
    "validators",
    "ops",
)

SAMPLE_TASK = PROJECT_ROOT / ".trellis/tasks/archive/2026-06/06-22-round3-019-layer2-sensor"


def _run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


_LOOP_GENERATED_PATHS = (
    "tests/test_catalog.yaml",
    "docs/generated/project_map.generated.json",
    "docs/generated/project_map.generated.md",
    "docs/generated/docs_specs_index.generated.md",
)


def _snapshot_loop_generated_files() -> dict[str, str]:
    snap: dict[str, str] = {}
    for rel in _LOOP_GENERATED_PATHS:
        path = PROJECT_ROOT / rel
        snap[rel] = path.read_text(encoding="utf-8") if path.is_file() else ""
    return snap


def _restore_loop_generated_files(snapshot: dict[str, str] | None = None) -> None:
    """Restore loop-generated artifacts; snapshot avoids reverting to stale git HEAD."""
    if snapshot is not None:
        for rel, content in snapshot.items():
            path = PROJECT_ROOT / rel
            if content:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            elif path.is_file():
                path.unlink()
        return
    subprocess.run(
        ["git", "checkout", "--", *_LOOP_GENERATED_PATHS],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
    )


def test_authorityGraph_allReferencedPathsExist() -> None:
    """覆盖范围：authority_graph.yaml 各模块引用路径存在性
    测试对象：load_authority_graph 与 path_exists（Round3 模块及全量 bucket）
    目的/目标：P0 权威图引用的 docs/contracts/rules/implementation_tasks/tests 路径必须真实存在
    验证点：Round3 六模块均在图中；missing 列表为空
    失败含义：幽灵路径会导致 agent 上下文路由到不存在的文档
    """
    graph = load_authority_graph()
    modules = graph.get("modules") or {}
    assert modules, "authority_graph must define modules"
    missing: list[str] = []
    for module_name in ROUND3_MODULES:
        assert module_name in modules, f"missing Round 3 module: {module_name}"
    for module_name, cfg in modules.items():
        for bucket in ("docs", "contracts", "rules", "implementation_tasks", "tests"):
            for rel in cfg.get(bucket) or []:
                if not path_exists(str(rel)):
                    missing.append(f"{module_name}/{bucket}: {rel}")
    assert missing == [], f"authority graph broken paths: {missing}"


def test_contextRouter_layer2Module_packHasDesignAndContractAuthorities() -> None:
    """覆盖范围：layer2_sensors 模块 context_pack 内容
    测试对象：build_context_pack + validate_context_pack
    目的/目标：P0 上下文包须含设计文档、契约 YAML 与登记测试，不得空路由
    验证点：validate 零错误；含 layer2_cross_asset_sensor.md、layer2_sensor_contract.yaml、test_layer2_sensor_loader.py
    失败含义：空包会让 Execute agent 缺少 layer2 权威输入
    """
    pack = build_context_pack(task="sample", modules=["layer2_sensors"], touched_paths=[])
    errors = validate_context_pack(pack)
    assert errors == [], f"context pack validation failed: {errors}"
    paths = {item["path"] for item in pack["source_authorities"]}
    assert "docs/modules/layer2_cross_asset_sensor.md" in paths
    assert "specs/contracts/layer2_sensor_contract.yaml" in paths
    assert "layer2_sensors" in pack["modules"]
    assert "tests/test_layer2_sensor_loader.py" in {t["path"] for t in pack["tests"]}


def test_contextRouter_filePath_mapsToLayer2Module() -> None:
    """覆盖范围：按触达文件路径推断模块
    测试对象：modules_for_paths + build_context_pack
    目的/目标：编辑 layer2 snapshot_builder 时应路由到 layer2_sensors 模块
    验证点：matched 含 layer2_sensors；pack.modules 含 layer2_sensors
    失败含义：路径映射错误会导致 agent 读取错误模块权威
    """
    rel = "backend/app/layer2_sensors/snapshot_builder.py"
    graph = load_authority_graph()
    matched = modules_for_paths([rel], graph)
    assert "layer2_sensors" in matched
    pack = build_context_pack(task=None, modules=matched, touched_paths=[rel])
    assert "layer2_sensors" in pack["modules"]


def test_contextRouter_cli_moduleFlag_exitsZero() -> None:
    """覆盖范围：context_router.py CLI --module
    测试对象：scripts/context_router.py 子进程（layer2_sensors）
    目的/目标：Plan P0 规定的模块路由命令须可执行且退出码为 0
    验证点：returncode==0；stdout JSON modules==['layer2_sensors']
    失败含义：CLI 不可用会阻断 Plan freeze 自动 context 生成
    """
    result = _run_script("context_router.py", "--module", "layer2_sensors")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["modules"] == ["layer2_sensors"]


@pytest.mark.skipif(not SAMPLE_TASK.is_dir(), reason="sample task directory missing")
def test_contextRouter_cli_taskFlag_writesContextPack() -> None:
    """覆盖范围：context_router.py CLI --task
    测试对象：round3-019-layer2-sensor 归档任务目录副本（repo 内 sandbox）
    目的/目标：A5-P2-002 — 复杂任务须能生成 context_pack.json 且不污染 archive 原件
    验证点：returncode==0；pack 文件存在且 validate_context_pack 为空
    失败含义：任务级路由失败或测试写坏归档 context_pack
    """
    sandbox_root = PROJECT_ROOT / ".audit-sandbox" / "loop-context-router-task"
    if sandbox_root.exists():
        shutil.rmtree(sandbox_root)
    shutil.copytree(SAMPLE_TASK, sandbox_root)
    pack_path = sandbox_root / "context_pack.json"
    pack_path.unlink(missing_ok=True)
    rel = sandbox_root.relative_to(PROJECT_ROOT).as_posix()
    try:
        result = _run_script("context_router.py", "--task", rel)
        assert result.returncode == 0, result.stderr
        assert pack_path.is_file()
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        assert validate_context_pack(pack) == []
    finally:
        shutil.rmtree(sandbox_root, ignore_errors=True)


def test_writeLoopEvidenceStubs_createsManifestAndIndex(tmp_path: Path) -> None:
    """覆盖范围：loop 证据桩文件生成
    测试对象：write_loop_evidence_stubs（含 EXECUTION_INDEX §2 AC 的临时任务）
    目的/目标：context_router 须为 loop 任务写出 loop_manifest 与 evidence_index 初稿
    验证点：两文件均存在；manifest.acs 含 019-01/019-02 类 AC id
    失败含义：无证据桩会导致 P3 evidence 门禁无法 bootstrap
    """
    (tmp_path / "EXECUTION_INDEX.md").write_text(
        "## 2. AC\n### AC-019-01\n| AC-019-02 | desc |\n",
        encoding="utf-8",
    )
    pack = {"modules": ["layer2_sensors"]}
    manifest_path, evidence_path = write_loop_evidence_stubs(tmp_path, pack)
    assert manifest_path.is_file()
    assert evidence_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ac_ids = {item["id"] for item in manifest["acs"]}
    assert "019-01" in ac_ids or "AC-019-01" in ac_ids or "019-02" in ac_ids


def test_taskTrack_complexWhenV4IndexWithoutMeta(tmp_path: Path) -> None:
    """覆盖范围：无 task.json 时 task_track 默认推断
    测试对象：task_track、loop_required（EXECUTION_INDEX + frozen）
    目的/目标：有 v4 三件套无 meta 时默认 complex 且须走 loop
    验证点：task_track=='complex'；loop_required 为 True
    失败含义：默认轨道错误会导致 simple 任务误套 loop 或反之
    """
    (tmp_path / "EXECUTION_INDEX.md").write_text("## 1.\n| step |\n", encoding="utf-8")
    frozen = tmp_path / "frozen"
    frozen.mkdir()
    (frozen / "card.md").write_text("## 9.\n", encoding="utf-8")
    assert task_track(tmp_path) == "complex"
    assert loop_required(tmp_path) is True


def test_taskTrack_debtLiteSkipsLoop(tmp_path: Path) -> None:
    """覆盖范围：debt-lite 轨道跳过 loop
    测试对象：task_track、loop_required（meta.task_track=debt-lite）
    目的/目标：Repair 轻量切片不必维护 loop 四件套
    验证点：task_track=='debt-lite'；loop_required 为 False
    失败含义：debt-lite 仍要求 loop 会增加 Repair 切片摩擦
    """
    (tmp_path / "task.json").write_text(
        '{"meta":{"task_track":"debt-lite"}}',
        encoding="utf-8",
    )
    assert task_track(tmp_path) == "debt-lite"
    assert loop_required(tmp_path) is False


def test_deprecatedLoopMeta_errorsOnOldFlags(tmp_path: Path) -> None:
    """覆盖范围：废弃 loop_engineering_* meta 检测
    测试对象：deprecated_loop_meta_errors（loop_engineering_version）
    目的/目标：R1 旧 flag 须报错并引导迁移到 task_track
    验证点：errors 含 loop_engineering_version
    失败含义：旧 flag 静默通过会导致双轨配置回流
    """
    (tmp_path / "task.json").write_text(
        '{"meta":{"loop_engineering_version":"1"}}', encoding="utf-8"
    )
    errors = deprecated_loop_meta_errors(tmp_path)
    assert any("loop_engineering_version" in e for e in errors)


def test_authorityGraphCoverageGaps_detectsUnknownBackendPath(tmp_path: Path) -> None:
    """覆盖范围：计划工件引用未收录 backend 路径的缺口检测
    测试对象：authority_graph_coverage_gaps
    目的/目标：R3 freeze warning 须能发现新模块未扩 authority_graph
    验证点：gaps 含 backend/app/brand_new_module/foo.py
    失败含义：缺口未检出会导致 agent 上下文缺少新包映射
    """
    (tmp_path / "EXECUTION_INDEX.md").write_text(
        "touch backend/app/brand_new_module/foo.py\n", encoding="utf-8"
    )
    gaps = authority_graph_coverage_gaps(tmp_path)
    assert "backend/app/brand_new_module/foo.py" in gaps


def test_discoverUnmappedBackendPackages_emptyWhenGraphComplete() -> None:
    """覆盖范围：backend/app 顶层包与 authority_graph 对齐
    测试对象：discover_unmapped_backend_packages
    目的/目标：日常维护第三步：图完整时不得有未映射顶层包
    验证点：返回 []
    失败含义：未映射包会导致 loop_maintain 持续报错或漏扩图
    """
    assert discover_unmapped_backend_packages() == []


def test_loopMaintain_fix_writesCatalogAndMaps() -> None:
    """覆盖范围：loop_maintain.py --fix 生成物
    测试对象：scripts/loop_maintain.py --fix
    目的/目标：一键刷新 test_catalog 与 docs/specs 索引
    验证点：returncode==0；test_catalog.yaml 与 docs_specs_index.generated.md 存在
    失败含义：--fix 失败会导致 CI catalog/索引门禁无法自愈
    """
    from loop_engineering_common import TEST_CATALOG_PATH

    snap = _snapshot_loop_generated_files()
    result = _run_script("loop_maintain.py", "--fix")
    try:
        assert result.returncode == 0, result.stderr + result.stdout
        assert TEST_CATALOG_PATH.is_file()
        assert (PROJECT_ROOT / "docs/generated/docs_specs_index.generated.md").is_file()
    finally:
        _restore_loop_generated_files(snap)


def test_loopMaintain_check_passesWhenRepoFresh() -> None:
    """覆盖范围：loop_maintain.py 检查模式（无 --fix）
    测试对象：scripts/loop_maintain.py 默认检查
    目的/目标：CI/本地单命令验证 catalog、project map、authority 包覆盖
    验证点：returncode==0
    失败含义：仓库 stale 时检查应失败，误绿会放过维护债务
    """
    check = _run_script("loop_maintain.py")
    assert check.returncode == 0, check.stderr + check.stdout


def test_generateProjectMap_writesDocsSpecsIndex() -> None:
    """覆盖范围：generate_project_map 写出 docs/specs 索引
    测试对象：scripts/generate_project_map.py
    目的/目标：R4 机械生成全量 docs/specs 索引，减负手工 MIGRATION_MAP
    验证点：returncode==0；索引文件含 user_intervention_policy.md
    失败含义：索引未生成会导致 docs 门禁与 agent 路由缺条目
    """
    index_path = PROJECT_ROOT / "docs/generated/docs_specs_index.generated.md"
    snap = _snapshot_loop_generated_files()
    gen = _run_script("generate_project_map.py")
    try:
        assert gen.returncode == 0, gen.stderr
        assert index_path.is_file()
        text = index_path.read_text(encoding="utf-8")
        assert "docs/ops/user_intervention_policy.md" in text
    finally:
        _restore_loop_generated_files(snap)


def test_testCatalog_coversEveryDiscoveredTestModule() -> None:
    """覆盖范围：test_catalog 与发现测试模块的一致性
    测试对象：check_catalog、discover_test_modules、tests/test_catalog.yaml
    目的/目标：P1 每个 test_*.py 须在 catalog 登记完整元数据
    验证点：check_catalog 零错误；discovered 键集等于 catalog 键集
    失败含义：catalog 缺口会导致测试语义与 CI 追溯黑洞
    """
    assert TEST_CATALOG_PATH.is_file(), "tests/test_catalog.yaml must exist"
    errors = check_catalog()
    assert errors == [], f"test catalog gaps: {errors}"
    catalog = yaml.safe_load(TEST_CATALOG_PATH.read_text(encoding="utf-8")) or {}
    discovered = set(discover_test_modules())
    assert discovered == set(catalog.keys())


def test_testCatalog_round3GateEntry_documentsStagedOnlySemantics() -> None:
    """覆盖范围：Batch3 gate 测试的 catalog 元数据
    测试对象：test_batch3_staged_downstream_gate.py 的 catalog 条目
    目的/目标：关键 gate 须声明 staged-only 语义与 production/live 失败含义
    验证点：purpose 含 staged/batch 3；failure_meaning 含 production 与 live；verifies 含 BATCH3 gate 文档
    失败含义：元数据缺失会导致误将 staged gate 当作生产放行
    """
    catalog = yaml.safe_load(TEST_CATALOG_PATH.read_text(encoding="utf-8")) or {}
    entry = catalog["tests/test_batch3_staged_downstream_gate.py"]
    purpose = entry["purpose"].lower()
    failure = entry["failure_meaning"].lower()
    assert "staged" in purpose or "batch 3" in purpose
    assert "production" in failure and "live" in failure
    verifies = entry["verifies"]["docs"]
    assert "docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md" in verifies


def test_verificationMatrix_acLinksResolveToExistingTests() -> None:
    """覆盖范围：feature_verification_matrix AC→pytest 映射
    测试对象：check_matrix、feature_verification_matrix.yaml
    目的/目标：P2 每个 AC 须绑定存在且已登记的测试
    验证点：矩阵文件存在；check_matrix 零错误
    失败含义：AC 无测试落点会导致功能验收无法追溯 pytest
    """
    assert FEATURE_MATRIX_PATH.is_file()
    errors = check_matrix()
    assert errors == [], f"verification matrix errors: {errors}"


def test_contractCoverage_everyContractHasRequirementOrWaiver() -> None:
    """覆盖范围：contract_coverage 矩阵完整性
    测试对象：check_coverage、contract_coverage.yaml
    目的/目标：P2 每个 specs/contracts/*.yaml 须有 tests 或 explicit waiver
    验证点：覆盖文件存在；check_coverage 零错误
    失败含义：无覆盖契约会成为「纸面契约」无 pytest 落点
    """
    assert CONTRACT_COVERAGE_PATH.is_file()
    errors = check_coverage()
    assert errors == [], f"contract coverage errors: {errors}"


def test_taskEvidence_checkScript_passesOnSampleTask() -> None:
    """覆盖范围：复杂任务 evidence 机械门禁
    测试对象：check_task_evidence（round3-019 示例任务）
    目的/目标：P3 evidence_index/loop_manifest/audit_matrix 须对真实任务可运行
    验证点：errors == []
    失败含义：示例任务 evidence 失败会阻断 loop handoff 回归基线
    """
    from check_task_evidence import check_task_evidence  # noqa: E402

    task = SAMPLE_TASK
    if not task.is_dir():
        pytest.skip("sample task missing")
    errors = check_task_evidence(task)
    assert errors == [], f"task evidence errors: {errors}"


def test_loopDashboard_cli_listsTasksWithoutCrash() -> None:
    """覆盖范围：loop_dashboard.py CLI 可用性
    测试对象：scripts/loop_dashboard.py
    目的/目标：P3 提供统一任务状态视图供 merge coordinator 查看 blocker
    验证点：returncode==0；stdout 含 Task/task
    失败含义：dashboard 崩溃会导致并行任务协调失去总览
    """
    result = _run_script("loop_dashboard.py")
    assert result.returncode == 0, result.stderr
    assert "Task" in result.stdout or "task" in result.stdout.lower()


def test_generateProjectMap_writesAndCheckPasses() -> None:
    """覆盖范围：project_map 生成与 --check 一致性
    测试对象：scripts/generate_project_map.py（写模式与 --check）
    目的/目标：P4 项目地图须自动生成且 --check 能发现 stale
    验证点：写出 md/json/index；JSON modules 含 layer2_sensors；--check returncode==0
    失败含义：地图 stale 未检出会导致 agent 读到过期模块索引
    """
    md_path = PROJECT_ROOT / "docs/generated/project_map.generated.md"
    json_path = PROJECT_ROOT / "docs/generated/project_map.generated.json"
    index_path = PROJECT_ROOT / "docs/generated/docs_specs_index.generated.md"
    snap = _snapshot_loop_generated_files()
    gen = _run_script("generate_project_map.py")
    try:
        assert gen.returncode == 0, gen.stderr
        assert md_path.is_file()
        assert json_path.is_file()
        assert index_path.is_file()
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert "layer2_sensors" in payload.get("modules", {})
        check = _run_script("generate_project_map.py", "--check")
        assert check.returncode == 0, check.stderr
    finally:
        _restore_loop_generated_files(snap)


def test_collectModuleAuthorities_layer2_includesForbiddenClaims() -> None:
    """覆盖范围：layer2 模块 forbidden_claims 注入
    测试对象：collect_module_authorities('layer2_sensors', graph)
    目的/目标：context_pack 须把 production-live 禁止声明注入 agent
    验证点：forbidden_claims 拼接文本含 production-live
    失败含义：缺禁止声明会导致 agent 越权宣称生产 live 能力
    """
    graph = load_authority_graph()
    bundle = collect_module_authorities("layer2_sensors", graph)
    claims = " ".join(bundle["forbidden_claims"]).lower()
    assert "production-live" in claims


def test_normalizeAcId_canonicalizesTableCaptures() -> None:
    """覆盖范围：AC ID 规范化
    测试对象：normalize_ac_id
    目的/目标：EXECUTION_INDEX 表格捕获 BOOT/01 须统一为 AC-BOOT/AC-01
    验证点：normalize 输出带 AC- 前缀
    失败含义：loop_manifest 与 matrix AC 集合永久分叉
    """
    assert normalize_ac_id("BOOT") == "AC-BOOT"
    assert normalize_ac_id("AC-01") == "AC-01"
    assert normalize_ac_id("01") == "AC-01"


def test_inferTaskTouchedPaths_readsExecutionIndex(tmp_path: Path) -> None:
    """覆盖范围：v4 任务路径推断
    测试对象：infer_task_touched_paths
    目的/目标：EXECUTION_INDEX §3 路径应进入 touched_paths
    验证点：含 GLOBAL_TESTING_POLICY 路径
    失败含义：v4.1 context_pack 长期为空包
    """
    idx = tmp_path / "EXECUTION_INDEX.md"
    idx.write_text(
        "## 3.\n| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | must-read |\n",
        encoding="utf-8",
    )
    paths = infer_task_touched_paths(tmp_path)
    assert "docs/implementation_tasks/GLOBAL_TESTING_POLICY.md" in paths


def test_taskEvidence_rejectsEmptyManifestAcs(tmp_path: Path) -> None:
    """覆盖范围：空 loop_manifest.acs 不得绕过 AC 校验
    测试对象：check_task_evidence
    目的/目标：有 plan AC 但 manifest acs=[] 须 fail-closed
    验证点：errors 含 loop_manifest has no AC entries
    失败含义：handoff 假绿
    """
    from check_task_evidence import check_task_evidence  # noqa: E402

    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "task.json").write_text(
        '{"meta":{"task_track":"complex"},"status":"in_progress"}', encoding="utf-8"
    )
    (tmp_path / "EXECUTION_INDEX.md").write_text(
        "## 2.\n| AC-BOOT | pytest |\n## 3.\n", encoding="utf-8"
    )
    (tmp_path / "frozen").mkdir()
    (tmp_path / "frozen" / "card.md").write_text("## 9.\n", encoding="utf-8")
    (tmp_path / "context_pack.json").write_text(
        '{"modules":["datasources"],"source_authorities":[],"tests":[]}', encoding="utf-8"
    )
    (tmp_path / "loop_manifest.json").write_text('{"acs":[]}', encoding="utf-8")
    (tmp_path / "evidence_index.json").write_text("{}", encoding="utf-8")
    errors = check_task_evidence(tmp_path)
    assert any("no AC entries" in e for e in errors)
