# 014_implement_data_sync_orchestrator 实现 DataSyncOrchestrator

## 1. 任务目标

实现 FullLoad、Incremental、Backfill、RevisionAudit、Reconcile 状态机。

## 2. 预期结果

完成后，Claude Code / Codex 应能在不依赖上下文记忆的情况下，依据本任务和输入文件完成对应模块的可运行实现或可验证骨架。

## 3. 输入文件

- `docs/modules/data_sync_orchestrator.md`
- `specs/contracts/sync_job_contract.yaml`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `specs/contracts/runtime_versions.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/ops/idempotency_retry_dlq_policy.md`

## 4. 相关代码 / 输出文件

- `backend/sync/orchestrator.py`
- `backend/sync/jobs.py`
- `tests/test_sync_orchestrator.py`

## 5. 现有模式 / 参考

- 遵循 `docs/architecture/03_runtime_flows.md` 中的运行链路。
- 遵循 `docs/architecture/04_data_architecture.md` 中的数据分层。
- 遵循 `docs/quality/final_package_rules.md` 中的最终包规则。
- 任何写入 clean table 的行为都必须经过 `DuckDBWriteManager`。
- 任何重任务都必须先通过 `ResourceGuard`。

## 6. 技术约束

- 后端优先使用 Python、FastAPI、Pydantic、DuckDB、Parquet、Polars Lazy。
- 前端使用 Vite + React + TypeScript；页面布局只是占位，正式实现前必须提醒用户确认。
- 配置与契约使用 YAML / JSON / SQL / Markdown。
- 不允许新增未经用户确认的大型依赖。

## 7. 资源约束

- 默认运行模式为 `eco`。
- 不允许全市场全历史扫描作为默认行为。
- 不允许无分页 API 或 Agent 大查询。
- 如果触发 `RESOURCE_GUARD_PAUSED`，必须停止非核心任务并汇报原因。

## 8. 边界约束

- 不得恢复 `Primary / Shadow / Emergency` 旧口径。
- 不得输出交易动作语义。
- 不得绕过 `WriteManager`。
- 不得把 Agent 文本当作事实来源。
- 不得固定死前端最终页面设计。
- 不得修改与本任务无关的金融语义和 spec。

## 9. 实现步骤

- `实现 job/run/task id`
- 记录 job_run_log
- 重任务先过 ResourceGuard
- 先写或补充最小测试 / smoke test，再实现。
- 运行本任务验收命令。
- 汇报改动文件、测试结果、未完成项、资源保护状态。

## 10. 测试要求

- 只 mock 外部 I/O，例如数据库、HTTP、文件系统、消息队列。
- 纯计算逻辑和条件分支必须使用真实值。
- 每个测试至少包含一个业务语义断言。
- 禁止只用 `assertNotNull` 或 `assertDoesNotThrow` 作为唯一断言。
- 测试命名建议：`functionName_condition_expectedBehavior`。

## 11. 验收命令

本任务为后端实现任务。验收命令：

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run python -m compileall backend scripts tests
```

## 12. 完成标准

- 本任务列出的输出文件已创建或更新。
- 测试命令通过，或明确说明未运行原因和阻塞项。
- 没有生成临时 round report、scratch、tmp 或一次性 self-check 文件。
- 没有引入与现有 docs/specs/contracts 冲突的口径。

## 13. Red Flags

出现以下情况必须停止并修正：

- 为了完成本任务修改了无关模块。
- 跳过测试并声称“看起来没问题”。
- 前端页面布局被当作最终设计写死。
- Agent 能自由 SQL、自由联网或直接写库。
- 大查询未经过 ResourceGuard。
- 测试只验证方法调用，不验证业务结果。

## 14. 输出要求

执行完成后只输出：

1. 改动文件清单。
2. 新增文件清单。
3. 删除文件清单。
4. 测试命令和结果。
5. ResourceGuard 是否触发。
6. 未完成项或需要用户确认的点。

## 15. 审计修复补充要求

DataSyncOrchestrator 必须实现：

- idempotency_key，避免重复同步造成重复写入。
- NETWORK_ERROR 指数退避；RATE_LIMITED cooldown；AUTH_FAILED/SCHEMA_DRIFT 进入人工复核。
- dead letter / manual_review_queue。
- 批任务必须支持 item-level 部分成功，不得用一个总状态覆盖全部。
- 所有 retry、skip、partial success 必须写 audit log。

## 16. 未闭合项覆盖补充（Plan 不得遗漏）

执行 orchestrator / job matrix / backfill / reconcile 后续计划前，必须读取 `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`，并核对以下仍未闭合项：

| ID                         | 归属阶段                    | 本任务卡处理要求                                                                   |
| -------------------------- | --------------------------- | ---------------------------------------------------------------------------------- |
| `R3-PARTIAL-1`             | Batch6 pipeline repay       | backfill 要么走 validate + clean write + pytest，要么 ADR 保留 scope。             |
| `R3-PARTIAL-3` / `D2-P2-2` | Batch6 reconcile repay      | reconcile re-fetch / compare closure pytest；`D2-P2-2` 只能作为 alias。            |
| `R3-PARTIAL-5`             | Batch6 ops optional         | COMPLETED-vs-write crash window 需同事务关闭或 recovery runbook / re-deferral。    |
| `D2-P1-1`                  | Batch6 job matrix           | `run_revision_audit` / `run_data_quality` runners 与 job type pytest。             |
| `D2-P1-3`                  | Batch6 ops / task 035 prep  | `python -m quant_monitor.sync` 或 successor console script smoke。                 |
| `D2-P2-1`                  | Batch6 source-health        | `source_health_snapshot` migration + snapshot pytest。                             |
| `D2-P3-1`                  | Batch6 registry lifecycle   | `registry_generation` / `removed_from_yaml_at` migration + sync pytest。           |
| `D7-P1-1` / `R2-RISK-1`    | Batch6 orchestrator hygiene | handler registry extraction + handler registry pytest；关闭 alias 时不得重复实现。 |
| `D3-P1-2`                  | Batch6 hygiene              | `_validate_domain_roles` 复杂度必须 refactor 或 justified ADR/noqa。               |
| `R2-HYG-4`                 | Batch6 test hygiene         | `test_duckdb_connection` inter-call smell：refactor 或 close as wont-fix ADR。     |
