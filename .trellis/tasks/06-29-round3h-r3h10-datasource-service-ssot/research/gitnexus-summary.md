# GitNexus Summary — R3H-10（1b impact）

**Targets：** `DataSourceService` · `guard_production_adapter_bypass` · `run_incremental`

## Blast radius

| Symbol                                                | 直接调用方                                 | 风险                        |
| ----------------------------------------------------- | ------------------------------------------ | --------------------------- |
| `DataSourceService.fetch`                             | Sync orchestrator · CLI data paths · tests | **HIGH** — 产品 fetch 入口  |
| `guard_production_adapter_bypass`                     | `runners.py` production sync               | **HIGH** — fail-closed 守卫 |
| `staged_pilot_fetch_ports` / `live_pilot_fetch_ports` | pilot ops · rehearsal                      | **MEDIUM** — E4 双轨收敛    |

## Affected execution flows

- Sync incremental / full run（`orchestrator` → `runners`）
- `qmd data` CLI 契约路径（`test_data_cli_contract.py`）
- staged/live pilot 彩排（`test_staged_pilot.py` · `test_batch275_live_pilot_gate.py`）

## Change guidance

- 单一修复点优先：`runners.py` 共享守卫 + service 注入，避免 per-caller 补丁
- commit 前 `detect_changes({scope: "compare", base_ref: "master"})`

**Risk level：** HIGH（触及生产 Sync 入口）
