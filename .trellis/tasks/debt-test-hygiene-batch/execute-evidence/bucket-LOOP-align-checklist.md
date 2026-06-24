# 桶 LOOP — Phase A align-checklist

**分支：** `debt/test-hygiene/bucket-loop-trellis`  
**Agent：** agent-LOOP  
**Worktree：** `quant-monitor-desk-worktrees/bucket-loop-trellis`

## 模块汇总（73 用例，五问全 Y）

| 模块                                   | 用例数 | 1 对象 | 2 验证点 | 3 失败含义 | 4 无额外行为 | 5 复用 helper                                          | Phase A 改动                                                                          |
| -------------------------------------- | ------ | ------ | -------- | ---------- | ------------ | ------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| `test_loop_engineering_flow.py`        | 22     | Y      | Y        | Y          | Y            | Y (`contract_gate_support`, `loop_engineering_common`) | 删 `test_discoverUnmappedBackendPackages` 内重复 import                               |
| `test_docs_specs_indexed.py`           | 5      | Y      | Y        | Y          | Y            | Y (`check_docs_specs_indexed`)                         | `coversUserInterventionPolicy` 断言改为显式 `missing_policy` 列表（语义更强，未弱化） |
| `test_documentation_index.py`          | 3      | Y      | Y        | Y          | Y            | Y (`contract_gate_support.PROJECT_ROOT`)               | 复用共享 `PROJECT_ROOT`，删本地 `Path` 推导                                           |
| `test_trellis_validate_plan.py`        | 13     | Y      | Y        | Y          | Y            | Y (`_minimal_master`, `_plan_boot_artifacts`)          | 顶栏 `import json`，删 4 处函数内重复 import                                          |
| `test_trellis_validate_execute.py`     | 6      | Y      | Y        | Y          | Y            | Y (`_write_master`, `_boot_artifacts`)                 | 顶栏 `import json`，删函数内重复 import                                               |
| `test_docstring_quadruple_coverage.py` | 3      | Y      | Y        | Y          | Y            | Y (`_collect_gaps`, `_missing_fields`)                 | 已对齐，无代码改动                                                                    |
| `test_module_boundaries.py`            | 4      | Y      | Y        | Y          | Y            | Y (`contract_gate_support`, `load_checker_module`)     | 已对齐，无代码改动                                                                    |
| `test_project_scaffold.py`             | 14     | Y      | Y        | Y          | Y            | Y (`contract_gate_support.PROJECT_ROOT`)               | 复用共享 `PROJECT_ROOT`，删本地推导                                                   |
| `test_backend_smoke.py`                | 3      | Y      | Y        | Y          | Y            | Y (`TestClient`, `get_resource_profile`)               | 已对齐，无代码改动                                                                    |

## ponytail 改动摘要

- **去重复 import**：`loop_engineering_common.discover_unmapped_backend_packages` 顶栏已有；`json` 在 trellis validate 两文件顶栏统一
- **复用 `contract_gate_support.PROJECT_ROOT`**：`documentation_index`、`project_scaffold` 与同桶 gate 测试一致
- **断言清晰化**：`test_migrationMapCoverage_coversUserInterventionPolicy` 从布尔短路改为显式 missing 列表（仍守卫同一 policy 路径）
- **未改**任何测试注释/docstring
- **未删/弱化** loop/catalog gate 断言；`check_catalog`/`check_matrix`/`check_coverage` 零错误要求未动
- **未改** `tests/conftest.py` 或共享 helper 实现

## 汇总

- 用例数：73
- 全 Y：是
- comment-conflicts：none
- deletion-candidates：空（§3.4 全在禁止删清单）
