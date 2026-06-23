"""Loop engineering task-flow refactor — gate script and machine-readable config tests.

覆盖范围：LOOP_ENGINEERING_TASK_FLOW_REFACTOR_PLAN 的 P0–P4 落地物。
测试对象：authority_graph、context_router、test_catalog、verification matrix、
contract coverage、task evidence、project map 生成脚本。
目的：证明 agent 上下文路由、测试语义、AC 验证链、证据索引与项目地图机制可机械校验。
"""

from __future__ import annotations

import json
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
    load_authority_graph,
    loop_required,
    modules_for_paths,
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


def _restore_loop_generated_files() -> None:
    """ponytail: pre-commit pytest must not leave hook-owned files dirty."""
    subprocess.run(
        ["git", "checkout", "--", *_LOOP_GENERATED_PATHS],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
    )


def test_authorityGraph_allReferencedPathsExist() -> None:
    """覆盖：specs/context/authority_graph.yaml。
    对象：各 module 的 docs/contracts/rules/implementation_tasks/tests 路径。
    目的：P0 权威图引用的每个路径在仓库中必须存在，防止 agent 路由到幽灵文档。
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
    """覆盖：scripts/context_router.build_context_pack。
    对象：layer2_sensors 模块上下文包。
    目的：P0 context_pack 必须包含设计文档与 machine-readable 契约，不得为空路由。
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
    """覆盖：modules_for_paths + build_context_pack。
    对象：backend/app/layer2_sensors/snapshot_builder.py 触达路径。
    目的：按文件路由时必须推断正确 module，避免 agent 读错权威上下文。
    """
    rel = "backend/app/layer2_sensors/snapshot_builder.py"
    graph = load_authority_graph()
    matched = modules_for_paths([rel], graph)
    assert "layer2_sensors" in matched
    pack = build_context_pack(task=None, modules=matched, touched_paths=[rel])
    assert "layer2_sensors" in pack["modules"]


def test_contextRouter_cli_moduleFlag_exitsZero() -> None:
    """覆盖：scripts/context_router.py CLI --module。
    对象：layer2_sensors 命令行入口。
    目的：Plan P0 规定的 context_router 命令必须可执行且返回 0。
    """
    result = _run_script("context_router.py", "--module", "layer2_sensors")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["modules"] == ["layer2_sensors"]


@pytest.mark.skipif(not SAMPLE_TASK.is_dir(), reason="sample task directory missing")
def test_contextRouter_cli_taskFlag_writesContextPack() -> None:
    """覆盖：scripts/context_router.py CLI --task。
    对象：06-22-round3-019-layer2-sensor 任务目录。
    目的：复杂任务 Plan P0 必须能生成 context_pack.json。
    """
    pack_path = SAMPLE_TASK / "context_pack.json"
    source_index = SAMPLE_TASK / "research" / "source-index.md"
    had_index = source_index.is_file()
    index_before = source_index.read_text(encoding="utf-8") if had_index else None
    if pack_path.is_file():
        pack_path.unlink()
    result = _run_script(
        "context_router.py",
        "--task",
        ".trellis/tasks/archive/2026-06/06-22-round3-019-layer2-sensor",
    )
    try:
        assert result.returncode == 0, result.stderr
        assert pack_path.is_file()
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        assert validate_context_pack(pack) == []
        if had_index:
            assert "context_pack.json" in source_index.read_text(encoding="utf-8")
    finally:
        rel = SAMPLE_TASK.relative_to(PROJECT_ROOT).as_posix()
        subprocess.run(
            ["git", "checkout", "--", f"{rel}/context_pack.json"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            check=False,
        )
        if had_index and index_before is not None:
            source_index.write_text(index_before, encoding="utf-8")


def test_writeLoopEvidenceStubs_createsManifestAndIndex(tmp_path: Path) -> None:
    """覆盖：loop_engineering_common.write_loop_evidence_stubs。
    对象：含 MASTER §2 AC 的任务目录。
    目的：context_router 必须为 loop 任务写出 evidence_index 与 loop_manifest 初稿。
    """
    (tmp_path / "MASTER.plan.md").write_text(
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


def test_taskTrack_complexWhenMasterWithoutMeta(tmp_path: Path) -> None:
    """覆盖：loop_engineering_common.task_track 默认推断。
    对象：仅有 MASTER.plan.md、无 task.json 的目录。
    目的：复杂任务默认 complex，统一单轨，不依赖 loop_engineering_version flag。
    """
    (tmp_path / "MASTER.plan.md").write_text("# master\n", encoding="utf-8")
    assert task_track(tmp_path) == "complex"
    assert loop_required(tmp_path) is True


def test_taskTrack_debtLiteSkipsLoop(tmp_path: Path) -> None:
    """覆盖：task_track=debt-lite 时 loop_required 为 false。
    对象：018c 类 repair-debt-lite 任务。
    目的：轻量切片与 complex 单轨并存但不重复维护 loop 四件套。
    """
    (tmp_path / "MASTER.plan.md").write_text("# master\n", encoding="utf-8")
    (tmp_path / "task.json").write_text(
        '{"meta":{"task_track":"debt-lite"}}',
        encoding="utf-8",
    )
    assert task_track(tmp_path) == "debt-lite"
    assert loop_required(tmp_path) is False


def test_deprecatedLoopMeta_errorsOnOldFlags(tmp_path: Path) -> None:
    """覆盖：deprecated_loop_meta_errors。
    对象：含 loop_engineering_exempt 的 task.json。
    目的：R1 旧 flag 必须报错，引导迁移到 task_track。
    """
    (tmp_path / "task.json").write_text(
        '{"meta":{"loop_engineering_version":"1"}}', encoding="utf-8"
    )
    errors = deprecated_loop_meta_errors(tmp_path)
    assert any("loop_engineering_version" in e for e in errors)


def test_authorityGraphCoverageGaps_detectsUnknownBackendPath(tmp_path: Path) -> None:
    """覆盖：authority_graph_coverage_gaps。
    对象：MASTER 引用 authority_graph 未收录的 backend 路径。
    目的：R3 freeze warning 能发现新模块未扩图。
    """
    (tmp_path / "MASTER.plan.md").write_text(
        "touch backend/app/brand_new_module/foo.py\n", encoding="utf-8"
    )
    gaps = authority_graph_coverage_gaps(tmp_path)
    assert "backend/app/brand_new_module/foo.py" in gaps


def test_discoverUnmappedBackendPackages_emptyWhenGraphComplete() -> None:
    """覆盖：discover_unmapped_backend_packages。
    对象：authority_graph 全量 backend/app 顶层包。
    目的：日常维护第三步：新包必须扩图，本测试在图完整时应无缺口。
    """
    from loop_engineering_common import discover_unmapped_backend_packages

    assert discover_unmapped_backend_packages() == []


def test_loopMaintain_fix_writesCatalogAndMaps() -> None:
    """覆盖：scripts/loop_maintain.py --fix。
    对象：test_catalog 与 docs/generated 生成物。
    目的：一键完成日常维护前三步中的 catalog + docs/specs 索引。
    """
    from loop_engineering_common import TEST_CATALOG_PATH

    result = _run_script("loop_maintain.py", "--fix")
    try:
        assert result.returncode == 0, result.stderr + result.stdout
        assert TEST_CATALOG_PATH.is_file()
        assert (PROJECT_ROOT / "docs/generated/docs_specs_index.generated.md").is_file()
    finally:
        _restore_loop_generated_files()


def test_loopMaintain_check_passesWhenRepoFresh() -> None:
    """覆盖：scripts/loop_maintain.py 检查模式。
    对象：catalog、project map、authority_graph 包覆盖。
    目的：CI/本地可用单命令验证三步维护状态。
    """
    check = _run_script("loop_maintain.py")
    assert check.returncode == 0, check.stderr + check.stdout


def test_generateProjectMap_writesDocsSpecsIndex() -> None:
    """覆盖：generate_project_map 同时写出 docs_specs_index.generated.md。
    对象：docs/generated/docs_specs_index.generated.md。
    目的：R4 机械全量索引生成，减负 MIGRATION_MAP 手工维护。
    """
    index_path = PROJECT_ROOT / "docs/generated/docs_specs_index.generated.md"
    gen = _run_script("generate_project_map.py")
    try:
        assert gen.returncode == 0, gen.stderr
        assert index_path.is_file()
        text = index_path.read_text(encoding="utf-8")
        assert "docs/ops/user_intervention_policy.md" in text
    finally:
        _restore_loop_generated_files()


def test_testCatalog_coversEveryDiscoveredTestModule() -> None:
    """覆盖：tests/test_catalog.yaml + scripts/check_test_catalog.py。
    对象：tests/**/test_*.py 与 catalog 登记一致性。
    目的：P1 每个测试模块必须有 purpose/type/verifies/command/failure_meaning，防止测试语义黑洞。
    """
    assert TEST_CATALOG_PATH.is_file(), "tests/test_catalog.yaml must exist"
    errors = check_catalog()
    assert errors == [], f"test catalog gaps: {errors}"
    catalog = yaml.safe_load(TEST_CATALOG_PATH.read_text(encoding="utf-8")) or {}
    discovered = set(discover_test_modules())
    assert discovered == set(catalog.keys())


def test_testCatalog_round3GateEntry_documentsStagedOnlySemantics() -> None:
    """覆盖：tests/test_catalog.yaml 中 Batch 3 gate 条目。
    对象：tests/test_batch3_staged_downstream_gate.py catalog 元数据。
    目的：P1 关键 gate 测试必须声明 staged-only 语义与失败业务含义。
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
    """覆盖：specs/verification/feature_verification_matrix.yaml。
    对象：feature AC → pytest 目标映射。
    目的：P2 每个 AC 必须绑定存在且已登记的测试，功能验收可追溯到 pytest。
    """
    assert FEATURE_MATRIX_PATH.is_file()
    errors = check_matrix()
    assert errors == [], f"verification matrix errors: {errors}"


def test_contractCoverage_everyContractHasRequirementOrWaiver() -> None:
    """覆盖：specs/verification/contract_coverage.yaml。
    对象：specs/contracts/*.yaml 覆盖矩阵。
    目的：P2 每个契约文件必须有 tests 或 explicit waiver，防止契约无验证落点。
    """
    assert CONTRACT_COVERAGE_PATH.is_file()
    errors = check_coverage()
    assert errors == [], f"contract coverage errors: {errors}"


def test_taskEvidence_checkScript_passesOnSampleTask() -> None:
    """覆盖：scripts/check_task_evidence.py。
    对象：带 MASTER.plan.md 的示例复杂任务目录。
    目的：P3 evidence_index / loop_manifest / audit_matrix 机械门禁必须对真实任务可运行。
    """
    from check_task_evidence import check_task_evidence  # noqa: E402

    task = SAMPLE_TASK
    if not task.is_dir():
        pytest.skip("sample task missing")
    errors = check_task_evidence(task)
    assert errors == [], f"task evidence errors: {errors}"


def test_loopDashboard_cli_listsTasksWithoutCrash() -> None:
    """覆盖：scripts/loop_dashboard.py。
    对象：.trellis/tasks 下活跃任务列表。
    目的：P3 提供统一任务状态视图，merge coordinator 可一眼看到 blocker。
    """
    result = _run_script("loop_dashboard.py")
    assert result.returncode == 0, result.stderr
    assert "Task" in result.stdout or "task" in result.stdout.lower()


def test_generateProjectMap_writesAndCheckPasses() -> None:
    """覆盖：scripts/generate_project_map.py。
    对象：docs/generated/project_map.generated.{md,json}。
    目的：P4 项目地图必须从机器可读配置自动生成且 --check 能发现 stale。
    """
    md_path = PROJECT_ROOT / "docs/generated/project_map.generated.md"
    json_path = PROJECT_ROOT / "docs/generated/project_map.generated.json"
    index_path = PROJECT_ROOT / "docs/generated/docs_specs_index.generated.md"
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
        _restore_loop_generated_files()


def test_collectModuleAuthorities_layer2_includesForbiddenClaims() -> None:
    """覆盖：loop_engineering_common.collect_module_authorities。
    对象：layer2_sensors forbidden_claims 字段。
    目的：context_pack 必须把禁止声明（production-live）注入 agent，防止越权宣称。
    """
    graph = load_authority_graph()
    bundle = collect_module_authorities("layer2_sensors", graph)
    claims = " ".join(bundle["forbidden_claims"]).lower()
    assert "production-live" in claims
