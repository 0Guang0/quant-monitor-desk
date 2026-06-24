# GitNexus Summary — B01-FRED (Phase 1b)

## Query 摘要

| 概念 | 发现 |
| ---- | ---- |
| FRED deferred | `live_pilot_constants.py` · `FRED_PRIMARY_DEFERRED_NOTE` · phase2/3/4 标记 `fred_primary_deferred` |
| staged pilot | `staged_pilot.py` 含 `fred` 在 skip/disabled 列表；无 live FRED fetch port |
| macro route | `macro_supplementary` domain → akshare primary（registry） |
| tests | `test_fred_staged_semantics.py` 唯一 FRED 专用测试模块 |

## Impact 预判（Execute 前须正式 `impact()`）

| 符号/模块 | 变更类型 | 风险 |
| --------- | -------- | ---- |
| `source_registry.yaml` fred 行 | 新增 | LOW — 独占写 |
| `route_planner.py` | 窄改 | MEDIUM — 共享路由 |
| `staged_pilot_fetch_ports.py` | 增 port | MEDIUM — SP3 只读邻接 |
| 新建 `fred_*` ops 模块 | 新增 | LOW |

## 建议

- 优先新建 `fred_fetch_ports.py` + `fred_sandbox_pilot.py`，避免扩大 `staged_pilot.py` 主体
- Execute 每步改 symbol 前跑 `impact()` + `detect_changes()`
