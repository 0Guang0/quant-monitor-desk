# GitNexus Audit Summary — R3H-03 Repair

**日期：** 2026-06-28 · **索引：** `node .gitnexus/run.cjs analyze`（Repair 后刷新）

## 新建/变更符号（CN 轨）

| 符号 | 模块 | Repair 变更 |
| --- | --- | --- |
| `check_license_gate` | `auth/license_gate.py` | 路由层 `_platform_allows` 上游调用 |
| `cn_market_bundle_layer3_preview` | `normalizers/cn_market.py` | 新增 Layer3 smoke |
| `cn_validation_mock_fetch_payload` | `fetch_ports/cn_validation_mock.py` | ponytail 去重 |
| `qmt_mock_fetch_payload` | `fetch_ports/qmt_mock_common.py` | ponytail 去重 |
| `reject_over_cap` / `reject_window_span_over_cap` | port 层 | cap 对抗测补强 |
| `tdx_fetch_guards.*` | `fetch_ports/tdx_fetch_guards.py` | mootdx 公共 caps |

## detect_changes（Repair 后）

- 范围：CN fetch_ports + route_planner + platform_matrix + tests
- 风险：LOW（新增测试与共享 helper；无 R3H-04 源触碰）

## 注记

Repair 前索引滞后（A1-003）；analyze 后主会话 merge 前可再跑 `detect_changes(compare, master)` 复核。
