# 桶 L23 — Phase A align-checklist

**分支：** `debt/test-hygiene/bucket-l23-layers`  
**阶段：** align-ponytail  
**注释修改：** 无（零 docstring / 意图性 `#` 改动）

## 模块级五问（全部 Y）

| 模块                                 | Q1 被测对象 | Q2 验证点 | Q3 失败含义 | Q4 无额外行为 | Q5 复用 helper                                          |
| ------------------------------------ | ----------- | --------- | ----------- | ------------- | ------------------------------------------------------- |
| `test_layer2_sensor_loader.py`       | Y           | Y         | Y           | Y             | Y — `_staged_registry` / `_staged_asset` / `_layer2_cm` |
| `test_layer3_loader.py`              | Y           | Y         | Y           | Y             | Y — `_mutate_bundle_json` / `_mutate_bundle_yaml`       |
| `test_layer3_snapshot_builder.py`    | Y           | Y         | Y           | Y             | Y — `_build` / `_mutate_l5_manifest`                    |
| `test_snapshot_lineage_kernel.py`    | Y           | Y         | Y           | Y             | Y — `_lineage_stub`                                     |
| `test_layer5_evidence_foundation.py` | Y           | Y         | Y           | Y             | Y — 已有 `_factual_record`                              |
| `test_resource_guard.py`             | Y           | Y         | Y           | Y             | Y — `_memory_guard` / 顶层 import                       |

## ponytail 改动摘要（价值守恒）

- 合并重复 staged 注册表加载、Layer2 DuckDB 初始化、L3 bundle/L5 manifest 变异 setup
- `test_resource_guard`：`ResourceGuard` / `apply_migrations` 提至模块顶；`check` 路径用 `_memory_guard`
- **未**删除/弱化 ResourceGuard 边界断言、lineage 必填字段循环、fail-closed 负向用例
- **未**改任何测试注释文本

## Phase B 备注（仅记录，本阶段未做 perf）

- `test_layer2_sensor_loader.py`：多用例重复 `_layer2_cm` + `_insert_validation_report`；可考虑 module-scoped 只读 migration（须 MERGE-C 改 conftest）
- `test_layer3_snapshot_builder.py`：`_mutate_l5_manifest` 每次 `copytree`；Phase B 可评估 session 级只读 L5 fixture

## 验证

```text
111 passed (6 modules, -q --tb=short)
```

见 `bucket-L23-pytest-green.txt`。
