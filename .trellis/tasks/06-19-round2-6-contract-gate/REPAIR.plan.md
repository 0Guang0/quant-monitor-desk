# Repair 计划 — Round2.6 Phase B Contract Gate

> **输入:** `audit.report.md` §4.3  
> **原则:** 修根因，不兜底；全部 P1/P3 项关闭后才 `finish-work`

---

## 0. 元信息

| 字段 | 值 |
|---|---|
| slug | `06-19-round2-6-contract-gate` |
| Audit 报告 | `audit.report.md` |
| Verdict (post-repair) | **PASS** |

---

## 1. 修复项清单

| ID | 维度 | 问题 | 根因修复 | 验证命令 | 通过条件 | 已修复 |
|---|---|---|---|---|---|---|
| R-01 | A4 | `test_datasourcesExtra` tautology | Parse `[project].dependencies` only; separate extras block | `pytest tests/test_dependency_extras_contract.py -q` | exit 0 | [x] |
| R-02 | A5 | `8.9/8.10-green.txt` placeholders | Re-captured `rg` / `Test-Path` stdout | `validate-execute-handoff` | evidence has real output | [x] |
| R-03 | A7 | `init_db --db` ignored / pytest argv leak | `main(argv)` + `--db` path; `test_project_scaffold` calls `main([])` | `python scripts/init_db.py --db .audit-sandbox/contract-gate/duckdb/quant_monitor.duckdb` | DB under sandbox; full pytest green | [x] |
| R-04 | A2 | Test bloat (embedded planner, duplicate AST) | `tests/contract_gate_support.py`; slimmed route/boundary/service tests | contract gate pytest bundle | shared helpers; dead fixture removed | [x] |
| R-05 | A3/A8 | Missing guardrail + service-order tests | `test_reference_adoption_guardrails.py`; `test_serviceBuildsRouteBeforeFetch` + runner scans | `pytest tests/test_reference_adoption_guardrails.py tests/test_datasource_service.py -q` | exit 0 | [x] |
| R-06 | A4 | Layer modules skip checker | `module_boundary_contract.yaml` `layer1_axes`–`layer5_evidence` + `test_layerModules_forbidAdapterImports` | `pytest tests/test_module_boundaries.py -q` | exit 0 | [x] |
| R-07 | A7 | `production_gate` omits boundary checker | `check_module_boundaries()` in `scripts/production_gate.py` | `python scripts/production_gate.py` | PASS | [x] |
| R-08 | A1 | `implement.jsonl` gaps (016A–016D docs) | Patched module/ops paths + boot-reads alignment | `validate-execute-handoff` | E17 pass | [x] |
| R-09 | A8 | `qmt_xqshare` planner `missing_env` | Reordered gating: capability → platform → registry | `pytest tests/test_platform_source_matrix.py -q` | exit 0 | [x] |
| R-10 | A3 | `order` false-positive in guardrail scan | High-signal patterns (exclude bare `order`) | `pytest tests/test_reference_adoption_guardrails.py -q` | exit 0 | [x] |
| R-11 | A4 | Weak Task2 CLI deferral test | Assert contract YAML + contract-gate `implement.jsonl` anchor | `pytest tests/test_data_cli_contract.py -q` | exit 0 | [x] |

---

## 2. Intentionally deferred to Task 2 (production code — not contract debt)

| Item | Hook |
|---|---|
| Runtime `DataSourceService` fetch-gate enforcement | Task 2 §8.4 |
| Production `SourceRoutePlanner` replacing test planner | Task 2 |
| Remove `ADAPTER_DOMAIN_COMPATIBILITY_MAP` after adapter domain alignment | Task 2 §8.2 |
| `sync.runners` migration to service-based fetch | Task 2 / Round 4 |
| AST checker dynamic-import bypass (documented `BOUNDARY_CHECK_ABORTED`) | Task 2 hardening |

---

## 3. Repair DoD

- [x] R-01..R-11 fixed + evidence
- [x] Full `pytest -q` → exit 0
- [x] `python scripts/production_gate.py` → PASS
- [x] `research/execute-evidence/8.9-green.txt`, `8.10-green.txt`, `9-pipeline.txt` re-captured
- [x] `audit.report.md` §5 re-verification updated → **PASS**
- [x] `task.py validate-execute-handoff` exit 0
- [ ] `finish-work` (user handoff)
