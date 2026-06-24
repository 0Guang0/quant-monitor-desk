# Source Index — B-19 staged pilot v2

## §A 血缘 / 纠偏

| 声称路径                                    | 实际                          | 处置                                                   |
| ------------------------------------------- | ----------------------------- | ------------------------------------------------------ |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.4.2 | 索引表当前为 §2.2 PROMPT 索引 | Plan 以 PROMPT_19 + R3Y 任务卡为准；§2.4.2 待 map 增补 |
| v1 `PILOT_ID=r3x-staged-pilot-20260622`     | v2 新 ID                      | `r3y-staged-pilot-v2-20260624`                         |
| AUD-04 `proof_status=VERIFIED` 过宽         | `mutation_proof.py:76`        | R3Y-MUT-PROOF-001 在 SP2-08 闭合                       |

## §B Manifest（required）

| 路径                                                                                            | 类型          | 用途          |
| ----------------------------------------------------------------------------------------------- | ------------- | ------------- |
| `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_19_*.md`                             | original-task | Plan trace    |
| `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_real_data_staged_pilot_v2.md` | original-task | AC 源         |
| `docs/implementation_tasks/GLOBAL_*.md`                                                         | rule          | GLOBAL×4      |
| `backend/app/ops/staged_pilot.py`                                                               | wiring        | 主实现        |
| `backend/app/ops/mutation_proof.py`                                                             | wiring        | MUT-PROOF-001 |
| `tests/test_staged_pilot.py`                                                                    | test          | §5 契约       |
| `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/*`                       | evidence      | v1 基线       |

## §C 六类关键信息 — **索引完整**

| 类别         | 代表路径                                                                       | MASTER 锚点 |
| ------------ | ------------------------------------------------------------------------------ | ----------- |
| decision     | `R3Y-AUD-08-go-no-go.md`, `staged_acceptance_policy.md`                        | §0 AUD-08   |
| contract     | `source_route_contract.yaml`, `write_contract.yaml`, `data_quality_rules.yaml` | §6          |
| business     | `R3Y_real_data_staged_pilot_v2.md` §3 Q1–Q9                                    | §2 AC       |
| architecture | `data_validation_and_conflict.md`, `write_manager.md`, `duckdb_and_parquet.md` | §4          |
| rule         | GLOBAL×4, `production_live_pilot_policy.md`                                    | §0/§7       |
| wiring       | `staged_pilot.py`, `staged_pilot_fetch_ports.py`, `DataSourceService`          | §4/§8       |

## §D 路由

- Execute Boot → `implement.jsonl` + `integration-ledger.md`
- 动态闭包 → `research/context-closure.md`（Execute 6.pre）
- Audit → `AUDIT.plan.md` + `audit.jsonl`
