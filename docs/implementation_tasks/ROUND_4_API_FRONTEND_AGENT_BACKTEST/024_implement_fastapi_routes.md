# 024_implement_fastapi_routes 实现 FastAPI 路由

## 1. 任务目标

实现统一 response envelope、Layer1-5、reports、notifications、backtest API。

## 2. 预期结果

完成后，Claude Code / Codex 应能在不依赖上下文记忆的情况下，依据本任务和输入文件完成对应模块的可运行实现或可验证骨架。

## 3. 输入文件

- `docs/modules/fastapi_backend.md`
- `docs/api/fastapi_routes.md`
- `specs/api/openapi_contract.md`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `specs/contracts/runtime_versions.md`
- `docs/quality/staged_acceptance_policy.md`
- `specs/contracts/api_security_contract.yaml`

## 4. 相关代码 / 输出文件

- `backend/api/`
- `tests/test_api_routes.py`

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

- 分页与错误码
- QUERY_TOO_LARGE
- OpenAPI 可生成
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

## 15. Round2.6 补充：只读 Diagnostics API 与 DataSourceService 边界

执行本任务前必须读取：

- `docs/modules/datasource_service.md`
- `docs/modules/source_route_plan.md`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/diagnostics_api_contract.yaml`
- `specs/contracts/module_boundary_contract.yaml`

新增要求：

- API 层不得直接 import vendor adapter 或 `create_adapter()`。
- Diagnostics endpoints 只能做 route preview、source registry validation、ResourceGuard snapshot、redacted config path report。
- Diagnostics endpoints 不得 fetch 外部数据、不得写 raw/clean/snapshot。
- API 失败响应必须包含 `error_code` 与 docs anchor，对应 `docs/ops/ERROR_CODE_GUIDE.md`。

必须补测试：`test_diagnosticsEndpointsReadOnly`、`test_apiRoutes_doNotImportAdapterFactory`、`test_sourceRoutePreview_returnsDisabledReasonWithoutFetch`。

## 16. 审计修复补充要求

API 必须实现最小安全基线：

- 本地版可配置 auth，但生产模式必须启用 auth。
- 第一版仅实现单本地 Bearer token = admin；`viewer` / `agent_readonly` 仅保留为 Phase 2 deferred role，不得在第一版实现半套 RBAC。
- 必须补测试：`test_singleLocalToken_mapsToAdmin`、`test_viewerAgentRoles_areDeferredInPhase1`、`test_prodAdminMutationWithoutToken_returnsAuthRequired`。
- 所有列表 API 必须分页，默认 page_size = 200，绝对上限 = 1000；唯一机器权威为 `specs/contracts/api_security_contract.yaml`。
- 必须补测试：`test_apiSecurityContract_isSingleAuthorityForQueryBudget`、`test_resourceLimitsApiLimits_matchApiSecurityContract`、`test_frontendPageContracts_doNotUseStale500Limit`。
- 大查询返回 `QUERY_TOO_LARGE`；资源不足返回 `RESOURCE_GUARD_PAUSED`。
- API 必须有 rate limit 与 query budget。

### 用户决策补充：D-02

用户已拍板：API dev 可关闭 token 但只允许 loopback；prod 必须启用 Bearer token，缺少 QMD_API_TOKEN 或关闭鉴权必须启动失败。

## 17. 未闭合项覆盖补充（Plan 不得遗漏）

执行 FastAPI / security / query budget 相关计划前，必须读取 `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`，并核对：

| ID                               | 归属阶段               | 本任务卡处理要求                                                     |
| -------------------------------- | ---------------------- | -------------------------------------------------------------------- |
| `R2-GAP-2`                       | Round4 task 024        | source capability list HTTP API 或 documented deferral to task 025。 |
| `R4-API-SEC-3` / `R4-API-SEC-10` | Round4 task 024        | page_size above absolute limit 必须返回 `QUERY_TOO_LARGE`。          |
| `R4-API-SEC-4`                   | Round4 task 024        | page_size contract 必须与 docs / `api_security_contract.yaml` 一致。 |
| `R4-API-SEC-5`                   | Round4 tasks 024 + 027 | frontend/API stale page-size contract test。                         |
| `R4-API-SEC-6`                   | Round4 task 024        | unauthenticated request auth-required test。                         |
| `R4-API-SEC-7`                   | Round4 task 024        | prod without token fails-startup test。                              |
| `R4-API-SEC-8`                   | Round4 task 024        | prod disabled auth fails-startup test。                              |
| `R4-API-SEC-9`                   | Round4 task 024        | dev disabled auth only allowed on loopback test。                    |
| `R4-API-SEC-11`                  | Round4 task 024        | single local token maps to admin test。                              |
| `R4-API-SEC-12`                  | Round4 task 024        | viewer / agent_readonly roles deferred in Phase 1 tests。            |
| `R4-API-SEC-13`                  | Round4 task 024        | production admin mutation without token test。                       |
