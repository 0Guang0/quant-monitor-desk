# 修复包导入后 — 代码与 docs/specs 口径差台账

> **状态**：closed（2026-06-19，Phase 3 完成）  
> **性质**：本文件是**项目实施补充台账**，不在 `MANIFEST.json` 权威包内。  
> **关闭条件**：✅ 8 项 pytest 全部绿色；`configs/` 与 Batch D `implement.jsonl` 已同步。

## 背景

2026-06-19 按 Manifest 定向导入 `quant_monitor_implementation_docs_v1` 修复包后，backend/tests/configs 与修复口径存在差。Phase 3 已全部对齐。

## Phase 3 关闭记录

| # | 测试 | 修复动作 | 状态 |
|---|------|----------|------|
| 1 | `test_apiLimits_enforcesMaxPageSize` | `load_api_limits()` 以 `api_security_contract.yaml` 为 query budget 权威；跳过 `authority` 键；`configs/resource_limits.yaml` 同步 200/1000 | ✅ |
| 2–3 | `test_schema_contract` ×2 | `specs/schema/schema.sql` 补全 `resource_guard_log`、`stg_*`、`fetch_log` 及 003 扩展列 | ✅ |
| 4 | `test_defaultYaml_loadsFromRepoSeed` | `SourceRegistry` 支持 list `sources`、`enabled_by_default`、list `validation`/`fallback_policy`；测试改查 `cn_equity_daily_bar` | ✅ |
| 5 | `test_migrationMap_exists_shouldGuideNavigation` | 断言改为修复包中文导航锚点（`五层模型`、`docs/architecture/`、`MANIFEST.json`） | ✅ |
| 6–8 | `test_manifest_protocol` Batch D ×3 | `implement.jsonl` 末尾登记 `api_security_contract.yaml`（首行仍为 MASTER.plan.md） | ✅ |

## Phase 3 自检（2026-06-19）

```text
pytest -q                     OK（370 passed）
check_doc_links.py            OK（132 markdown）
compileall backend/scripts/tests  OK
```

## 变更文件摘要

| 区域 | 文件 |
|------|------|
| 运行时 | `backend/app/core/api_limits.py` |
| 运行时 | `backend/app/datasources/source_registry.py` |
| 配置 | `configs/resource_limits.yaml` |
| 契约 | `specs/schema/schema.sql` |
| 测试 | `tests/test_audit_fixes.py`、`test_project_scaffold.py`、`test_source_registry.py` |
| Trellis | `.trellis/tasks/archive/.../implement.jsonl` |

## 变更记录

| 日期 | 动作 | 备注 |
|------|------|------|
| 2026-06-19 | 创建台账 | Commit 1 导入；8 pytest failures 基线 |
| 2026-06-19 | Phase 2 调和 | `agent_workflow_boundaries.md`、`verification_commands.md` |
| 2026-06-19 | **Phase 3 关闭** | 全量 pytest 绿 |
