# Plan 加固 — context-engineering

## 执行包阅读规则

- **切片开工前必读：** `research/` 全部 10 份 + `EXTERNAL-INDEX.md` §A → 见 `00-EXECUTION-ENTRY.md` §5.2
- **执行中情境路由：** 见 `00-EXECUTION-ENTRY.md` §5.3

---

## Level 1 — 常驻 Rules（不重复加载）

- `AGENTS.md` / `CLAUDE.md` — Trellis Execute gate、GitNexus impact、ponytail
- `specs/contracts/reference_adoption_guardrails.yaml` — L1/L2/L3、forbidden_semantics
- `agent-toolchain.md` — 工具路由

---

## Level 2 — 本任务 Spec（按切片选读）

| 切片      | 必读                                                                             |
| --------- | -------------------------------------------------------------------------------- |
| **ALL**   | `research/to-issues-slices.md` 对应 §                                            |
| **ALL**   | `research/bypass-baseline-matrix.md`                                             |
| S10-01    | `docs/decisions/ADR-025-*.md`                                                    |
| S10-02    | `specs/contracts/datasource_service_contract.yaml`（路径以仓库为准）             |
| S10-03    | `docs/**/production_live_pilot_policy.md`                                        |
| S10-04/05 | `research/reference-adoption-r3h10.md` §4.2 反模式清单                           |
| S10-05    | `research/reference-adoption-r3h10.md` §4.1 OpenBB↔QMD 对照（architecture_only） |

**勿整包加载：** `reference-adoption-r3h10.md` 全文仅 Plan 读；Execute 按上表节选。

---

## Level 3 — 源码（按切片）

### S10-BOOT

- `backend/app/datasources/service.py`（门面链）
- `backend/app/sync/orchestrator.py`
- `backend/app/sync/runners.py`（`guard_production_adapter_bypass`）

### S10-01

- 上列 + `tests/test_sync_orchestrator.py`（`test_r3ySync001_*`）
- 模式样例：`tests/test_vendor_fetch_e2e.py`（金路径 `datasource_service=`）

### S10-02

- `backend/app/cli/data_commands.py` 或等价 `qmd data` 入口
- `tests/test_data_cli_contract.py`
- `tests/test_datasource_service.py`（contract gate）

### S10-03

- `backend/app/ops/staged_pilot.py`（rehearsal 入口 docstring）
- `backend/app/ops/live_pilot_phase2.py`
- `tests/test_production_live_pilot_policy.py`

### S10-04

- `backend/app/ops/interface_probe.py`
- `tests/test_datasource_service.py`（`scan_package_for_create_adapter`）

### S10-05

- `backend/app/ops/staged_pilot_fetch_ports.py`
- `backend/app/ops/live_pilot_fetch_ports.py`
- `backend/app/datasources/fetch_ports/`
- `tests/test_staged_pilot.py` · `tests/test_batch275_live_pilot_gate.py`

---

## Level 4 — 工具上下文

| 时机                             | 工具                                                                    |
| -------------------------------- | ----------------------------------------------------------------------- |
| 改 `DataSourceService` / sync 前 | GitNexus `impact({target: "DataSourceService", direction: "upstream"})` |
| commit 前                        | `detect_changes()`                                                      |
| 触 backend/docs/specs            | `uv run python scripts/loop_maintain.py`                                |

---

## PROJECT CONTEXT 块（复制给 Execute agent）

```text
TASK: R3H-10 / S10-XX
MODULE: C2 + E4
GOAL: 生产 fetch 仅经 DataSourceService；消 staged/live 双轨
ADR: fail-closed — 无 datasource_service= 则报错（ADR-025）
FORBIDDEN: 默认构造 service；runtime 参考项目；silent fallback
VERIFY: uv run pytest -q + execute-evidence/9.x-green.txt
SLICE SSOT: .trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot/research/to-issues-slices.md
```

---

## context-engineering 验证清单

- [x] 分层清单已写
- [x] 单切片必读 <10 文件
- [ ] formal freeze 后：`context_pack.json` 由 `context_router.py` 生成（`trellis-plan` P0）
