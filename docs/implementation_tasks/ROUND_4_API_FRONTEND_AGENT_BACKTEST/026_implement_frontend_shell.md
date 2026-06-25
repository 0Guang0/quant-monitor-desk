# 026_implement_frontend_shell 实现前端 shell

> **Historical input notice:** canonical Round4 execution now starts from `BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/README.md`. This loose card remains source material for `B04_03_frontend_error_boundary_and_routes.md`; do not execute it as the default entrypoint without checking the Batch 04 manifest.

## 1. 任务目标

创建 Vite/React/TS 骨架、API client、全局状态和通用组件。

## 2. 预期结果

完成后，Claude Code / Codex 应能在不依赖上下文记忆的情况下，依据本任务和输入文件完成对应模块的可运行实现或可验证骨架。

## 3. 输入文件

- `docs/modules/frontend_dashboard.md`
- `specs/frontend/page_contracts.yaml`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `specs/contracts/runtime_versions.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/ops/frontend_security_policy.md`

## 4. 相关代码 / 输出文件

- `frontend/src/`
- `frontend/package.json`

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

- 页面布局仅占位
- 正式实现前提醒用户确认设计
- 类型生成
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

本任务涉及前端。验收命令：

```bash
uv sync --locked
uv run pytest -q tests/test_api_contracts.py
cd frontend && npm ci && npm audit --audit-level=high && npm run typecheck && npm run build
```

注意：前端页面布局仍为占位，正式 UI 实现前必须提醒用户确认。

复审修复要求：不得使用 会吞掉失败结果的 shell 容错短路写法 掩盖 contract 测试失败；如果 `tests/test_api_contracts.py` 在该阶段尚未存在，本任务必须先创建最小 API/frontend contract smoke test，再运行该测试。

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

## 15. Round2.6 补充：前端 Diagnostics 与 Local-only 提示

执行本任务前必须读取：

- `docs/ops/privacy_data_flow.md`
- `specs/contracts/user_input_privacy_contract.yaml`
- `specs/contracts/diagnostics_api_contract.yaml`
- `docs/ops/ERROR_CODE_GUIDE.md`

新增要求：

- `frontend/src/**` 当前阶段不改；后续实现 shell 时必须预留只读 Diagnostics 入口，但最终布局需用户确认。
- 前端导入文本/策略片段必须默认 local-only，并显示保存为 evidence 的确认边界。
- API client 需要支持 `error_code`、`docs_anchor`、`route_status`、`quality_flags` 字段显示。
- `package.json` / `package-lock.json` 只有在真实前端功能需要且用户确认依赖后才可改。

必须补测试：`test_frontendShowsErrorCodeDocAnchor`、`test_localOnlyDisclosureVisibleBeforeEvidenceSave`、`test_diagnosticsNavIsReadOnlyPlaceholder`。

## 16. 审计修复补充要求

前端 shell 必须实现安全和稳定性基线：CSP、错误边界、分页、缓存 freshness 标签、secret 不落 localStorage。页面布局仍仅为参考，正式 UI 需用户确认。

### 用户决策补充：D-08

用户已拍板：正式实现前端前必须提醒用户确认 UI 信息架构和交互；当前页面布局仅占位，不得写死。

## 17. 未闭合项覆盖补充（Plan 不得遗漏）

执行 frontend shell / navigation 相关计划前，必须读取 `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`，并核对：

| ID        | 归属阶段               | 本任务卡处理要求                                                                                           |
| --------- | ---------------------- | ---------------------------------------------------------------------------------------------------------- |
| `R4-FE-2` | Round4 tasks 026 + 028 | Notification Center `/notifications` page shell/nav 入口；028 负责通知数据与状态机，026 不得漏掉页面入口。 |
