# GitNexus Summary — Round 2 Batch D（需求锚定深度分析）

> Phase P0b + 1b · 2026-06-18

## Query 1: DataSyncOrchestrator sync job orchestration

**结论：** 仓库尚无 orchestrator 符号；相关流程分散在 validator/gate/registry 测试与文档中。

| 命中 | 相关性 |
|------|--------|
| `SourceRegistry.sync_to_db` | Batch D 启动需 registry bootstrap |
| `BaseDataAdapter.fetch` | Orchestrator 调用入口 |
| `test_batch_c_validation_flow` | 手工 E2E 模板，Orchestrator 应自动化同等链 |
| `014_implement_data_sync_orchestrator.md` | 权威任务卡 |
| `sync_job_contract.yaml` | 状态机契约 |

## Query 2: DbValidationGate WriteManager ingestion flow

**结论：** Gate 已被 WriteManager 与 batch C E2E 测试导入；Orchestrator 应在 `WRITING` 前调用 gate。

| 符号 | 关系 |
|------|------|
| `DbValidationGate.assert_can_write` | WriteManager 构造注入 |
| `test_batchCFlow_*` | quality→conflict→gate→write 语义测 |
| `ci_ingestion_smoke.py` | 可扩展为 GPT-P3-6 smoke |

## Context: ResourceGuard

- 仅被 `test_resource_guard.py` 与 foundation smoke 直接导入
- 方法：`snapshot()`, `check()` — Orchestrator 在 `FETCHING` 前调用
- **风险：** 低；新增调用方，无 upstream 破坏

## Context: DbValidationGate

- 导入方：validators 测试、write_manager、batch_c_validation_flow
- **impact 预判：** Orchestrator 成为新 caller（downstream），修改 gate 行为影响 WriteManager — Execute 前须 `impact(DbValidationGate)`

## Context: BaseDataAdapter

- 子类：SkeletonAdapterBase + 测试 FakeAdapter
- Orchestrator 应通过 registry 解析 source_id → adapter factory，不新增 vendor 实现

## CodeGraph 遗漏文档补读

| 文档 | 原因 |
|------|------|
| `docs/modules/write_manager.md` | job_id 与 write_audit 关联 |
| `docs/quality/final_package_rules.md` | 任务卡 §5 |
| `specs/schema/schema.sql` L73–113 | sync 表列定义 |
| `.trellis/tasks/06-17-round2-batch-c-validation-conflict/finish.md` | Batch C handoff |

## 实现风险（Plan 写入 MASTER §7）

1. **状态机爆炸** — 仅实现契约列出的 normal/terminal/retryable 转移，禁止 ad-hoc 状态
2. **事务边界** — job_event_log 与 data_sync_job 更新须同 writer 连接（对齐 C-C1 caller-owned tx）
3. **004 表不可 ALTER** — fetch_log CHECK 继续 app 层（C-C2）
4. **eco 默认** — Backfill 须分片 + ResourceGuard，禁止默认全市场扫描

## analysis_waiver

`false` — Execute 6.pre 须刷新 GitNexus 并写 `gitnexus-execute-summary.md`。
