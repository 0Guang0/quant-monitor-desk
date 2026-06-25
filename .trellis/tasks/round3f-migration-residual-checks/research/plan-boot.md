# Plan Boot — B3F-MIG migration residuals

- **日期**: 2026-06-25
- **Playbook**: `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.1 + §3.3 + §7.2 + §8.1
- **Manifest**: `B3F-MIG` · branch `feature/round3f-migration-residual-checks`
- **Worktree**: `../quant-monitor-desk-wt-b3f-mig`
- **合并顺序**: **第 1**（B3F-SH 依赖本分支 migration）

## 用户目标

关闭 Round 3F `R3F-MIG-01..06`：009 已关 CHECK 仅 verify；012 落地显式列重建与 `registry_generation`/`removed_from_yaml_at`；008→009→3F 路由文档对齐；**不**建 `source_health_snapshot` 表（归 B3F-SH）。

## 依赖与前置

- post Batch 3V `master` 基线 `7f628c9`；八路 worktree 同基线开波。
- **B3F-SH** 须在 B3F-MIG 合并后再合并（§7.2 序 4）。
- Registry 三件套闭合归 **B3F-REG** / 主会话，本任务不写 registry 闭合。

## AC 草稿

| ID | 验收 |
|----|------|
| AC-MIG-01 | 009 status CHECK 仍在磁盘；无重复 013 status CHECK migration |
| AC-MIG-02 | `manual_review_queue.priority` 无 DB CHECK；ADR-002 记录 app-layer |
| AC-MIG-03 | 012 重建 `fetch_log`/`manual_review_queue` 显式列、无 `SELECT *` |
| AC-MIG-04 | `registry_generation`/`removed_from_yaml_at` 列 + `SourceRegistry.sync_to_db` tombstone |
| AC-MIG-05 | `MIGRATION_COVERAGE.md` + `MIGRATION_008_PLAN.md` 路由 009-resolved / 3F-open |
| AC-MIG-06 | roadmap `R3F-MIG-06` 保持 CLOSED B3V regression guard |

## 当前缺口（基线 7f628c9 + worktree 草稿）

1. Trellis task-dir / MASTER / implement 未冻结（本 Plan 波次）。
2. `012_migration_residuals.sql` 与 `test_round3f_migration_residuals.py` 已在 worktree 草稿，Execute 须 RED→GREEN 证据链。
3. `test_round3f_migration_residuals.py` 须入 `test_catalog.yaml`（loop gate）。

## 约束摘要

- **禁止**：重复实现 009 CHECK；`source_health_snapshot` 建表；sync 业务重构；registry 三件套直接闭合。
- **允许**：`012` migration、`MIGRATION_COVERAGE`/`008 PLAN`、ADR-002、migration 测试。

## 原计划已读

- [x] `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.1 + §3.3 + §7.2 + §8.1
- [x] `BATCH_3F_TASK_CARD_MANIFEST.md` §1 B3F-MIG
- [x] `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3F `R3F-MIG-01..06`
- [x] GLOBAL×3 + `BATCH_3F_HARDENING_RULES.md`

## Phase P0 complete

- [x] Round 3F 协调包 README + manifest 已读
- [x] GitNexus query/context 已完成（migration / SourceRegistry 邻接）
- [x] `research/source-index.md` 索引完整
- [x] `context_pack.json` 待 `context_router` 生成
