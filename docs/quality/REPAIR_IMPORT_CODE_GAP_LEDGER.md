# 修复包导入后 — 代码与 docs/specs 口径差台账

> **状态**：open（2026-06-19，`chore/import-repaired-docs-20260619` / Commit 1 导入后记录）  
> **性质**：本文件是**项目实施补充台账**，不在 `MANIFEST.json` 权威包内；用于跟踪修复包 docs/specs 已更新但 backend/tests/configs 尚未对齐的项。  
> **关闭条件**：下列 8 项 pytest 全部恢复绿色，且相关 `configs/` 与 Trellis `implement.jsonl` 已同步。

## 背景

2026-06-19 按 Manifest 定向导入 `quant_monitor_implementation_docs_v1` 修复包后：

- `docs/`、`specs/`、`MIGRATION_MAP.md`、`MANIFEST.json`、`FINAL_AUDIT_REPORT.md` 已更新为修复口径；
- `backend/`、`frontend/`、`tests/`、`scripts/`、`configs/` **未在本 commit 修改**；
- 全量 `pytest -q`：**362 passed, 8 failed**（导入当日基线）。

验收命令（导入当日已通过项）：

```text
MANIFEST SHA-256 自检     OK（160 files）
JSON/YAML 解析            OK
scripts/check_doc_links   OK（130 markdown files）
compileall                OK
pytest -q                 8 FAILED（见下表）
```

## 失败项台账

| # | 测试 | 失败原因 | 修复包权威口径 | 当前代码/配置状态 | 建议修复方向 | 优先级 |
|---|------|----------|----------------|-------------------|--------------|--------|
| 1 | `tests/test_audit_fixes.py::test_apiLimits_enforcesMaxPageSize` | `load_api_limits()` 对 `api_limits` 值做 `int()`，修复包在 `specs/contracts/resource_limits.yaml` 写入 `authority: specs/contracts/api_security_contract.yaml`（字符串） | `api_limits` 数值权威在 `specs/contracts/api_security_contract.yaml`；`resource_limits.yaml` 仅引用 authority | `backend/app/core/api_limits.py` 合并 contract + `configs/resource_limits.yaml` 时未跳过 `authority` 键；`configs/resource_limits.yaml` 仍为旧值 100/500 | 更新 `load_api_limits()`：读 `api_security_contract.yaml` 取数值，或跳过非 int 键；同步 `configs/resource_limits.yaml` | P1 |
| 2 | `tests/test_schema_contract.py::test_foundationMigrationColumns_existInSchemaContract` | `resource_guard_log` 等表在 migrations 中存在，但不在 `specs/schema/schema.sql` | 修复包 `schema.sql` 为 Round 1 契约草案，未含后续 migration 表 | 实现已跑过 `001`–`003` migrations | 将 migration 列合并回 `specs/schema/schema.sql`，或改测试策略为 migration-aware contract | P1 |
| 3 | `tests/test_schema_contract.py::test_ingestionMigrationColumns_existInSchemaContract` | `fetch_log` 等在 `004_ingestion_sources.sql` 中，不在 `specs/schema/schema.sql` | 同上 | 实现已跑过 `004` migration | 同上；对齐 ingestion 表到 schema 契约 | P1 |
| 4 | `tests/test_source_registry.py::test_defaultYaml_loadsFromRepoSeed` | `SourceRegistry.load()` 要求 `sources` 为 mapping | 修复包 `specs/datasource_registry/source_registry.yaml` 将 `sources` 改为 **YAML 列表**（每项含 `source_id`） | `backend/app/datasources/source_registry.py` 仍按 dict 解析 | 更新 loader 支持 list-of-sources，或提供兼容层将 list 归一化为 dict | P1 |
| 5 | `tests/test_project_scaffold.py::test_migrationMap_exists_shouldGuideNavigation` | 测试断言 `MIGRATION_MAP.md` 含英文 `"Five-layer model"` | 修复包 `MIGRATION_MAP.md` 改为中文导航索引 | 测试仍绑定旧英文锚点 | 更新测试断言为修复包导航关键词，或在中英文 MIGRATION_MAP 保留双语锚点 | P2 |
| 6 | `tests/test_manifest_protocol.py::test_batch_d_suggest_implement_empty` | 新增 spec 被 module 1-hop 引用但未列入 Batch D `implement.jsonl` | `specs/contracts/api_security_contract.yaml` 为 P2-01 新增权威契约 | Trellis Batch D manifest 未登记该文件 | 更新 `.trellis/tasks/.../implement.jsonl`（或等效 manifest）纳入 `api_security_contract.yaml` | P2 |
| 7 | `tests/test_manifest_protocol.py::test_batch_d_manifest_freeze_passes` | E7：module spec 1-hop ref missing | 同上 | 同上 | 同上 | P2 |
| 8 | `tests/test_manifest_protocol.py::test_validate_manifest_freeze_bundle` | E7：同上 | 同上 | 同上 | 同上 | P2 |

## 关联但未导致 pytest 失败的口径差

以下项应在关闭上表前一并处理，避免 silent drift：

| 区域 | 说明 |
|------|------|
| `configs/resource_limits.yaml` | 仍为 `default_page_size: 100` / `max_page_size: 500`；契约已为 200/1000 |
| `docs/ops/agent_workflow_boundaries.md` | 非 manifest 补充文件，仍写 `pip install -e ".[dev]"`；应改为 `uv sync` / `uv run` |
| `README.md` | 已合并为项目型 + 修复包口径；**故意偏离** manifest 中 README hash |
| `specs/schema/schema.sql` vs migrations | 契约落后于 `backend/migrations/`；schema contract 测试会持续红灯直至合并 |

## 建议修复顺序

1. **P1 运行时阻断**：`api_limits` loader + `configs/resource_limits.yaml`（#1）
2. **P1 数据源**：`source_registry.yaml` list 格式 loader（#4）
3. **P1 契约**：`specs/schema/schema.sql` 与 migrations 对齐（#2、#3）
4. **P2 测试/manifest**：MIGRATION_MAP 测试断言（#5）；Batch D `implement.jsonl`（#6–#8）

## 复现命令

```bash
uv run pytest -q \
  tests/test_audit_fixes.py::test_apiLimits_enforcesMaxPageSize \
  tests/test_schema_contract.py \
  tests/test_source_registry.py::test_defaultYaml_loadsFromRepoSeed \
  tests/test_project_scaffold.py::test_migrationMap_exists_shouldGuideNavigation \
  tests/test_manifest_protocol.py -k "batch_d"
```

## 变更记录

| 日期 | 动作 | 备注 |
|------|------|------|
| 2026-06-19 | 创建台账 | 修复包 Manifest 导入 Commit 1；8 pytest failures 基线 |
