# Project Overview — R3FR-03 (Phase 1a)

## 任务在系统中的位置

Round 3F-R 在 Batch 3F 完成之后、Round 3G sandbox clean-write 之前，负责把「薄自研轮子」换成受 QMD 契约约束的参考项目思路适配实现。R3FR-03 专管 **TDX/pytdx** 这一条 validation-only 源。

```text
SourceRoutePlanner / DataSourceService  （生产路由 — 不变）
        │
        ▼
tdx_pytdx  (disabled-by-default, validation-only)
        │
        ├── fetch_ports/tdx_pytdx_port.py   ← 新建：连接/操作/caps/错误
        ├── normalizers/tdx.py              ← 新建：raw → manifest
        ├── adapters/tdx_pytdx.py           ← 扩展：adapter 边界
        └── ops/tdx_manual_probe.py         ← 编排：mocked CI + opt-in live
```

## 参考与 QMD 边界

| 侧           | 内容                                                                                                  |
| ------------ | ----------------------------------------------------------------------------------------------------- |
| 参考（只读） | EasyXT `tdx_provider.py` — MIT；借鉴 optional import、server 抽象、生命周期、错误分类、代码规范化思路 |
| QMD 自有     | 授权门、`PortError` 状态、`content_hash`/`schema_hash` evidence、registry caps、no-mutation proof     |
| 禁止复制     | auto server scan、auto login、trading/account、runtime `参考项目/**` import                           |

## 关键既有文件

| 路径                                                 | 角色                                  |
| ---------------------------------------------------- | ------------------------------------- |
| `backend/app/ops/interface_probe_fetch_ports.py`     | 含 `TdxPytdxProbeFetchPort`（待瘦身） |
| `backend/app/ops/tdx_manual_probe.py`                | B01-TDX 探针编排                      |
| `backend/app/ops/tdx_live_manual_probe_gate.py`      | live 授权 fail-closed                 |
| `backend/app/datasources/adapters/fetch_port.py`     | `FetchPort` 协议与 `PortError`        |
| `specs/datasource_registry/source_registry.yaml`     | `tdx_pytdx` 行                        |
| `specs/datasource_registry/source_capabilities.yaml` | domains/operations                    |

## 支持操作（disabled/raw-only）

- `security_list` / `fetch_security_list`
- `cn_equity_daily_bar` / `fetch_daily_bar`
- `cn_index_daily_bar` / `fetch_index_daily_bar`

Route 状态须保持 `DISABLED_SOURCE`、`USER_AUTH_REQUIRED` 或 raw-only pass，直至未来授权任务显式变更。
