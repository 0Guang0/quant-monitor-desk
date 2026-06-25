# Project overview — B3F-MIG

## 任务一句话

Batch 3F 第一合并位：闭合 migration 009 残余与 012 列生命周期，供 B3F-SH 依赖；009 CHECK **verify-only**。

## 模块边界

| 层            | 触及                                                         |
| ------------- | ------------------------------------------------------------ |
| DB migrations | `012`（fetch_log/MRQ 显式重建 + source_registry 列）         |
| 文档          | `MIGRATION_COVERAGE`, `MIGRATION_008_PLAN`, ADR-002          |
| 应用          | `SourceRegistry.sync_to_db` tombstone 时间戳                 |
| 测试          | `test_round3f_migration_residuals.py` + schema/coverage 基线 |

## 不在范围

- `source_health_snapshot` 表与 writer（B3F-SH）
- Registry 三件套 RESOLVED 批处理（B3F-REG）
- sync orchestrator / live pilot

## GitNexus 摘要

- `apply_migrations` 执行链：007–012 顺序；009 已含 status CHECK。
- `SourceRegistry.sync_to_db`：MIG-04 写入 `registry_generation` / tombstone `removed_from_yaml_at`。
- 风险：重复 009 CHECK → playbook 负向边界（B3F-AUD-VS-02）。
