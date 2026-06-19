# Phase 2 — 非 MANIFEST 跟踪文件删留审查

> **日期**：2026-06-19  
> **分支**：`chore/import-repaired-docs-20260619`  
> **输入**：`.tmp/non_manifest_tracked_docs_specs.txt`（25 项）  
> **原则**：不得覆盖 `MANIFEST.json` 权威 docs/specs；Trellis/Batch 过程材料默认保留，除非确认为无引用 scratch。

## 审查结论摘要

| 处置 | 数量 | 说明 |
|------|------|------|
| **保留** | 25 | 全部有活跃引用或实施价值 |
| **删除** | 0 | 无 archive/scratch/zip 类条目 |
| **调和更新** | 3 | `INDEX.md`、`agent_workflow_boundaries.md`、`verification_commands.md` |

**Commit 2 动作**：0 个 `git rm`；3 个文件加权威边界说明与 `uv` 主路径。

## 逐项审查

| # | 路径 | 处置 | 理由 |
|---|------|------|------|
| 1 | `docs/AUDIT_DEFERRED_REGISTRY.md` | **保留** | Round 2 延期项注册表；被 `ROUND3_HANDOFF.md`、审计闭环引用 |
| 2 | `docs/INDEX.md` | **保留 + 调和** | 项目文档导航枢纽；补 MANIFEST 权威说明与新 repair 契约链接 |
| 3 | `docs/ROUND3_HANDOFF.md` | **保留** | Round 2→3 交接；含 Batch 完成边界与 gold path |
| 4 | `docs/implementation_tasks/ROUND_1_DATA_FOUNDATION/DECISIONS.md` | **保留** | Round 1 Trellis 决策；`implementation_tasks/README.md` 索引 |
| 5–10 | `ROUND_1/.../plans/*.plan.md`（6） | **保留** | Round 1 执行计划；已归档任务对照依据 |
| 11 | `ROUND_2/.../BATCH_B_REPAIR_STATUS.md` | **保留** | Batch B 修复状态 |
| 12 | `ROUND_2/.../BATCH_C_LEDGER.md` | **保留** | Batch C 台账 |
| 13 | `ROUND_2/.../BATCH_C_REPAIR_STATUS.md` | **保留** | Batch C 修复状态 |
| 14 | `ROUND_2/.../BATCH_D_STATUS.md` | **保留** | Batch D 状态；manifest protocol 测试上下文 |
| 15 | `ROUND_2/.../DECISIONS.md` | **保留** | Round 2 决策权威 |
| 16 | `ROUND_2/.../ROUND2_GAPS_AND_DEVIATIONS.md` | **保留** | Round 2 缺口台账；防 silent drift |
| 17–20 | `ROUND_2/.../plans/*.plan.md`（4） | **保留** | Batch A/B/C/D Trellis 计划 |
| 21 | `docs/modules/README.md` | **保留** | 模块权威 vs 兼容索引；与修复包 modules 不冲突 |
| 22 | `docs/ops/agent_workflow_boundaries.md` | **保留 + 调和** | `.cursor`/`.trellis` 信任边界；`pip` 改 `uv` 主路径 |
| 23 | `docs/ops/verification_commands.md` | **保留 + 调和** | Windows 验收命令；补 `uv run` 与 gap ledger 引用 |
| 24 | `docs/schema/MIGRATION_008_PLAN.md` | **保留** | 计划中的 008 CHECK 约束；`AUDIT_DEFERRED_REGISTRY` 引用 |
| 25 | `docs/schema/MIGRATION_COVERAGE.md` | **保留** | 设计 schema vs 已应用 migration 矩阵；**Phase 3 schema 对齐的输入** |

## 与修复包口径冲突检查

| 文件 | 冲突点 | Phase 2 处理 | Phase 3 处理 |
|------|--------|--------------|--------------|
| `agent_workflow_boundaries.md` | 仍写 `pip install -e` | 文档改为 `uv sync` 主路径 | — |
| `verification_commands.md` | 仅 `.venv\python` | 补 `uv run` 等价命令 | pytest 全绿后更新基线 |
| `INDEX.md` | 未列 repair 新增契约 | 补链接与权威声明 | — |
| `MIGRATION_COVERAGE.md` | 与修复包 `schema.sql` 删减相关 | 保留作 drift 追踪 | 合并 migration 列到 `schema.sql` |
| Round 2 `DECISIONS.md` | 含 Primary/Validation 决策 | 与修复包一致，无删 | — |
| `plans/*.plan.md` | 可能含旧验收命令 | 保留；执行时以 MANIFEST 任务文件为准 | 可选批量 uv 化（低优先） |

## Phase 2 vs Phase 3 边界

```text
Phase 2（本文件）：非 MANIFEST 的 docs 补充材料 — 删留 + 文档口径调和
Phase 3（见 REPAIR_IMPORT_CODE_GAP_LEDGER.md）：backend / configs / tests / Trellis manifest — 代码与契约对齐
```

**pytest 口径差台账 ≠ 仅 api_limits / source_registry / schema.sql。**

台账 8 项覆盖：

| 类别 | 台账项 | 归属 |
|------|--------|------|
| 运行时代码 | `api_limits.py` + `configs/resource_limits.yaml` | Phase 3 |
| 运行时代码 | `source_registry.py` list 格式 | Phase 3 |
| 契约文件 | `specs/schema/schema.sql` ↔ migrations | Phase 3 |
| 测试断言 | `test_migrationMap_exists_shouldGuideNavigation` | Phase 3 |
| Trellis manifest | Batch D `implement.jsonl` + `api_security_contract.yaml` | Phase 3 |
| 补充文档 | `agent_workflow_boundaries.md` pip→uv | Phase 2（已调和） |

Phase 2 保留的 `MIGRATION_COVERAGE.md` 是 Phase 3 schema 工作的**输入文档**，不是 Phase 3 本身。

## 变更记录

| 日期 | 动作 |
|------|------|
| 2026-06-19 | 25 项审查完成；0 删除；3 项调和 |
