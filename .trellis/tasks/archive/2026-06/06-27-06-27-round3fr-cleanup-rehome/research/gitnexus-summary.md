# GitNexus Summary — R3FR-07

> Phase 1b · query + context

## Query: cleanup wrappers

| Symbol / 流程             | 角色                                                | R3FR-07 处置                         |
| ------------------------- | --------------------------------------------------- | ------------------------------------ |
| `check_daily_bars`        | `data_health._checks_from_bundle` 证据路径日 K 扫描 | 保留 shim；加 canonical redirect     |
| `health_check`            | `data_commands` → `run_data_health_profile`         | 已实现；文档对齐                     |
| `TdxPytdxProbeFetchPort`  | `interface_probe._resolve_fetch_port` 步骤          | 已委托 `TdxPytdxFetchPort`；注释加固 |
| `run_data_health_profile` | `market_bar_p0` runner                              | canonical（R3FR-02+06）              |
| `TdxPytdxFetchPort`       | R3FR-03 port                                        | canonical（勿在 probe 文件增长）     |

## Impact 注记

- `check_daily_bars`：GitNexus impact 未索引；grep 显示调用方：`data_health._checks_from_bundle`、`tests/test_ops_data_health.py`
- 修改 `check_daily_bars` 为 DRY 委托时：**LOW** 风险，direct callers 2 处 + 测试；须先 `test_ops_data_health` 全绿

## 禁止触碰（高扇出）

- `SourceRegistry` / `WriteManager` / `DataSourceService` — 本任务不修改
- `backend/app/datasources/fetch_ports/tdx_pytdx_port.py` — R3FR-03 已结案，仅文档引用

## 测试锚点（replacement stronger than wrapper）

| 前置任务   | 证明替换已更强的测试                                                               |
| ---------- | ---------------------------------------------------------------------------------- |
| R3FR-02+06 | `test_ops_data_health.py` · `test_qmd_data_cli.py`（无 `not_implemented_phase_c`） |
| R3FR-03    | `test_tdx_pytdx_port.py` · `test_tdx_manual_probe.py`                              |
| R3FR-05    | `test_provider_catalog.py`                                                         |
| R3FR-01    | `test_reference_adoption_guardrails.py`                                            |
