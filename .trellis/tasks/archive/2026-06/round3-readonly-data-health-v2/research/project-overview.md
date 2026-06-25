# Project overview — data health v2 (Plan 1a)

## 模块位置

- **包：** `backend/app/ops/`
- **核心：** `data_health.py`（v1 已实现 model/loader/rules/report/service）
- **CLI：** `data_health_cli.py`（`--evidence` 只读检查）
- **邻接：** `staged_pilot.py`（manifest 常量、`_equity_bar_rows`）、`source_registry.py`（role/disabled）

## v1 → v2 增量

| v1 已有                       | v2 新增                                                                                                         |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `staged_pilot_bundle` profile | `model_input_whitelist`, `fred_sandbox_pilot`, `tdx_manual_probe`, `staged_pilot_v3`, `source_readiness_rollup` |
| PASS/WARN/FAIL                | + `BLOCKED`（缺前置 artifact）                                                                                  |
| v2 archive integration 测     | 基线红：raw payload 路径断裂                                                                                    |

## GitNexus 查询建议（Execute）

- `query`: "data health evidence bundle check"
- `impact`: `DataHealthService`, `check_evidence_dir`, `_checks_from_bundle` before edits

## 风险

- 不得与 B01-FRED 争改 `data_health.py` 主体（FRED 分支只读）
- registry 三件套仅主会话批处理
