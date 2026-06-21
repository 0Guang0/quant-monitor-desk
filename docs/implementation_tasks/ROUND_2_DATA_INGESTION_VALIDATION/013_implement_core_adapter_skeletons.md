# 013_implement_core_adapter_skeletons 实现核心数据源 adapter skeleton

## 1. 任务目标

创建 QMT/baostock/AkShare/CNINFO/Yahoo adapter skeleton。

## 2. 预期结果

完成后，Claude Code / Codex 应能在不依赖上下文记忆的情况下，依据本任务和输入文件完成对应模块的可运行实现或可验证骨架。

## 3. 输入文件

- `docs/modules/data_sources.md`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `specs/contracts/runtime_versions.md`
- `docs/quality/staged_acceptance_policy.md`

## 4. 相关代码 / 输出文件

- `backend/sources/adapters/`
- `tests/test_adapter_skeletons.py`

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

- 不要求真实接通所有源
- 保留 TODO 与验收边界
- 禁止硬编码 secret
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

### 用户决策补充：D-11

用户已拍板：QMT 第一版默认禁用，用户确认本机授权与配置后再启用。

## 15. 数据源默认禁用与 domain gating 补充要求

落实 D-11：`qmt_xtdata` 与 `yahoo_finance` 默认禁用。实现 `SourceRegistry` 和 adapter skeleton 时必须识别 `domain_enabled_by_default=false` / `disabled_until_configured=true`，并在调度或 adapter factory 前返回 `DISABLED_SOURCE`，不得尝试连接未授权 QMT 或默认禁用的 Yahoo 源。

新增测试：

```text
test_disabledPrimaryDomain_returnsDisabledSource
test_fallbackDisabledByDefault_isSkippedUntilConfigured
```

## 16. 未闭合项覆盖补充（Plan 不得遗漏）

执行 adapter skeleton / metadata 后续计划前，必须读取 `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`，并核对：

| ID         | 归属阶段                        | 本任务卡处理要求                                                                                  |
| ---------- | ------------------------------- | ------------------------------------------------------------------------------------------------- |
| `R2-HYG-5` | Batch6 adapter contract hygiene | metadata fields 必须暴露并补 skeleton metadata pytest；若不在本任务处理，必须 explicit re-defer。 |
