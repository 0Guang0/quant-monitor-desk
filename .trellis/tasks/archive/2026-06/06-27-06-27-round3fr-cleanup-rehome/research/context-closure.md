# Context closure — R3FR-07 (Execute 6.pre)

## Upstream wiring closure

| 符号               | 预期 blast           | Execute 结果                                                        |
| ------------------ | -------------------- | ------------------------------------------------------------------- |
| `check_daily_bars` | LOW — docstring only | redirect 指向 `run_data_health_profile` / `market_bar_p0`；行为不变 |
| `health_check`     | LOW — docstring only | 指向 `run_data_health_profile`                                      |
| TDX probe modules  | LOW — module doc     | delegate 边界说明；无 `tdx_pytdx_port` 改动                         |

## 下游接线

| 下游                                                | 接线                        |
| --------------------------------------------------- | --------------------------- |
| `tests/test_r3fr07_legacy_wrapper_cleanup.py`       | AC-07-01..08 文档 guardrail |
| `tests/test_reference_adoption_guardrails.py`       | inventory redirect 回归     |
| `PROJECT_IMPLEMENTATION_ROADMAP` / `ROUND3_HANDOFF` | 3F-R CLOSED → 3G next       |
| `tests/test_catalog.yaml`                           | 新测模块登记                |

## Deferred (forbidden this task)

- registry 三件套 reconcile
- `B2.5-O-05` 等 UNRESOLVED DEFERRED 项
- 归档 Trellis 证据删除
- production-live / clean write 启用
