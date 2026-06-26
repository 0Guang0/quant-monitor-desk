# 029_implement_backtest_and_review 实现回测与复盘

> **Historical input notice:** do not implement this loose card directly. Canonical Round4 execution starts from `BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/README.md` and `BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_05_backtest_review_runtime.md`. This file is source material only. Before implementation, execution must follow rewritten `R3FR_01_REFERENCE_RULES_AND_LICENSE_GATE.md`, `R3FR_04_JQ2PTRADE_BACKTEST_ADOPTION_PLAN.md`, and the B04_05 local vertical slices. `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` is only a coverage map, not the execution card.

## 1. 任务目标

实现 event study、alert rule review、backtest report，不做自动交易。

## 2. 预期结果

完成后，Claude Code / Codex 应能在不依赖上下文记忆的情况下，依据本任务和输入文件完成对应模块的可运行实现或可验证骨架。

## 3. 输入文件

- `docs/modules/backtest_and_review.md`
- `specs/contracts/backtest_contract.yaml`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `specs/contracts/runtime_versions.md`
- `docs/quality/staged_acceptance_policy.md`
- `specs/contracts/backtest_reproducibility_contract.yaml`

## 4. 相关代码 / 输出文件

> **Superseded paths:** canonical Round4 execution uses `backend/app/review/**` per `B04_05_backtest_review_runtime.md §4`. The loose `backend/backtest/` path below is historical input only.

- `backend/app/review/` (canonical — see B04_05)
- `tests/test_backtest_review.py`

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

- ResourceGuard 限制范围
- T+窗口指标
- Agent 不能编造回测结论
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

> **Superseded:** use acceptance commands in `B04_05_backtest_review_runtime.md §8`. The command block below is historical loose-card input only.

本任务涉及 API / Agent / 通知 / 回测。验收命令：

```bash
uv sync --locked
uv run pytest -q tests/test_api_routes.py tests/test_agent_tools.py tests/test_notifications.py tests/test_backtest_review.py tests/test_no_action_semantics_guard.py
uv run ruff check .
uv run python -m compileall backend scripts tests
cd frontend && npm ci && npm audit --audit-level=high && npm run typecheck && npm run build
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

## 15. Round2.6 补充：BacktestReviewEngine 生命周期与指标契约

执行本任务前必须读取：

- `docs/modules/backtest_review_lifecycle.md`
- `docs/modules/review_sandbox_api.md`
- `specs/contracts/backtest_metric_contract.yaml`
- `specs/contracts/review_sandbox_contract.yaml`
- `specs/contracts/reference_adoption_guardrails.yaml`

新增要求：

- 回测实现必须按 lifecycle 拆分 review context、event set、window compute、metric snapshot、report builder。
- 默认指标必须符合 `backtest_metric_contract.yaml`，不得新增交易语义指标作为默认输出。
- 用户策略/片段导入如启用，必须先通过 review sandbox 规则。
- `pyproject.toml` 只有在 backtest 真实需要新依赖且用户确认 optional extra 策略后才可改。

必须补测试：`test_backtestReviewLifecycle_hasFrozenContext`、`test_requiredMetricSchemaStable`、`test_reportHasNoActionSemantics`。

## 16. 审计修复补充要求

回测必须防前视偏差：

- 使用 frozen_dataset_manifest。
- 所有输入必须满足 visibility_timestamp <= as_of_cutoff。
- 记录 parameter_hash、rule_version、code_version、random_seed。
- 同一 frozen dataset + 参数必须可复现。
- Agent 只能总结计算结果，不得生成或修改指标。

## 17. 未闭合项覆盖补充（Plan 不得遗漏）

执行 review / manual-review UX 相关计划前，必须读取 `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`，并核对：

| ID             | 归属阶段                                              | 本任务卡处理要求                                                                                                                  |
| -------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `R3-PARTIAL-4` | Batch5 evidence-chain conflict UX 或 Round4 review UX | failed reconcile 后 manual-review queue vs instant severe queue 行为需要 UX/ADR + pytest；若 023/016 处理，本任务必须 cross-ref。 |
