# Project Overview — R3H-03（Plan 1a）

> ≤1 页 · 2026-06-28

## 模块地图

```text
DataSourceService.fetch
  → route_planner / capability_registry
  → fetch_ports/*_port.py  ← R3H-03 主交付
  → normalizers/cn_market.py  ← 证据 SSOT
  → auth/license_gate.py  ← QMT/iFinD/xqshare
```

## 本轨十源现状

| source_id     | adapter/port 现状                         | registry 姿态              |
| ------------- | ----------------------------------------- | -------------------------- |
| baostock      | skeleton adapter；staged pilot ops        | enabled Primary candidate  |
| cninfo        | skeleton；staged pilot                    | enabled Primary filings    |
| akshare       | skeleton                                  | validation_only            |
| tdx_pytdx     | **port 存在**（R3FR-03）                  | disabled validation        |
| mootdx        | 无 port                                   | disabled validation        |
| eastmoney     | 无                                        | disabled validation        |
| sina_finance  | 无                                        | disabled validation        |
| ths_ifind     | 无                                        | disabled + auth_required   |
| qmt_xtdata    | skeleton adapter                          | disabled + user_setup      |
| qmt_xqshare   | 无                                        | disabled + user_setup      |

## 共享依赖（只读/本轨行）

- `source_registry.yaml` / `source_capabilities.yaml` — 仅改十源行
- `route_planner.py` / `capability_registry.py` / `resource_guard.py`
- `tests/test_source_route_planner.py` / `test_source_capabilities.py`

## 3H 闭环含义

非「样例 baostock」任务：Batch hardening 要求十源终态 + coordinator manifest，否则 Round4 `BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE`。
