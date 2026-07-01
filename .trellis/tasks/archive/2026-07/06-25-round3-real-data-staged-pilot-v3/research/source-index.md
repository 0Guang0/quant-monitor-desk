# Source Index — B01-C04 staged pilot v3

## §A 血缘 / 纠偏

| 声称路径                                                | 实际                  | 处置                                      |
| ------------------------------------------------------- | --------------------- | ----------------------------------------- |
| v2 `APPROVED_PILOT_V2_REQUEST_ENVELOPES` 硬编码 symbols | v3 须 WL 驱动         | SP3-01 替换 envelope 为 whitelist loader  |
| `specs/model_inputs/**`                                 | Plan 时不存在         | Execute 硬停；见 MASTER §1.5 #5           |
| `R3-PROMPT14-AKSHARE-VAL-01`                            | manifest §5 owner C04 | closeout 证明 validation-only 或 re-defer |
| Registry 三件套直接 commit                              | playbook §2.1         | agent 仅 proposed delta；主会话排队       |
| v2 `PILOT_ID_V2`                                        | v3 新 ID              | `r3e-staged-pilot-v3-20260625`            |

## §B Manifest（required）

| 路径                                                                                                     | 类型          | 用途         |
| -------------------------------------------------------------------------------------------------------- | ------------- | ------------ |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_real_data_staged_pilot_v3.md`           | original-task | AC 源        |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3D_model_input_whitelist.md`               | original-task | WL 前置      |
| `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_real_data_staged_pilot.md`             | original-task | v1 基线      |
| `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_real_data_staged_pilot_v2.md`          | original-task | v2 模式      |
| `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_staged_pilot_v2_execution_addendum.md` | original-task | TDD/ponytail |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md`                   | original-task | sandbox 边界 |
| `docs/quality/coordination/BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`                                | rule          | 文件锁       |
| `docs/implementation_tasks/GLOBAL_*.md`                                                                  | rule          | GLOBAL×4     |
| `backend/app/ops/staged_pilot.py`                                                                        | wiring        | v2→v3 主实现 |
| `backend/app/ops/staged_pilot_fetch_ports.py`                                                            | wiring        | fetch ports  |
| `backend/app/storage/staged_evidence.py`                                                                 | wiring        | 窄改         |
| `tests/test_staged_pilot.py`                                                                             | test          | v2 回归      |
| `.trellis/tasks/archive/2026-06/06-24-round3-real-data-staged-pilot-v2/`                                 | evidence      | v2 SSOT      |

## §C 六类关键信息 — **索引完整**

| 类别         | 代表路径                                                                                                     | MASTER 锚点 |
| ------------ | ------------------------------------------------------------------------------------------------------------ | ----------- |
| decision     | `BATCH_01_HARDENING_RULES.md`, `018B`, live 授权 2026-06-24                                                  | §0 / §1.5   |
| contract     | `source_route_contract.yaml`, `source_conflict_rules.yaml`, `data_quality_rules.yaml`, `write_contract.yaml` | §6          |
| business     | `R3E_real_data_staged_pilot_v3.md` §2–§14                                                                    | §2 AC       |
| architecture | `data_validation_and_conflict.md`, `write_manager.md`, `MIGRATION_MAP.md`                                    | §4          |
| rule         | GLOBAL×4, `staged_acceptance_policy.md`, `production_live_pilot_policy.md`                                   | §0/§7       |
| wiring       | `staged_pilot*.py`, `staged_evidence.py`, `data_quality.py`                                                  | §4/§8       |

## §D 路由

- Execute Boot → `implement.jsonl` + `research/integration-ledger.md`
- WL 门禁 → MASTER §1.5 #5；Boot `tests/fixtures` 不得冒充 WL
- Audit → `AUDIT.plan.md` + `audit.jsonl`
- 动态闭包 → `research/context-closure.md`（Execute 6.pre）

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。
