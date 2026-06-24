# Project overview — ops read-only data health

## 模块语境

- **域：** `backend/app/ops/` — 与 `db_inspector`、`staged_pilot`、`mutation_proof` 邻接
- **目标：** 机器可读 data health report，输入为 staged pilot evidence bundle，**非** Batch6 全平台
- **权威设计：** `docs/ops/data_health_cli.md`（Batch6 设计）；本任务实现 **v1 子集** + evidence-path 模式

## 关键邻接符号

| 符号                      | 路径                                        | 用途                           |
| ------------------------- | ------------------------------------------- | ------------------------------ |
| `DbInspector`             | `backend/app/ops/db_inspector.py`           | 只读 DB 打开与 key_tables 模式 |
| `StagedPilotRunner`       | `backend/app/ops/staged_pilot.py`           | evidence 文件名/manifest 形态  |
| `DataQualityValidator`    | `backend/app/validators/data_quality.py`    | rule_id 语义                   |
| `SourceConflictValidator` | `backend/app/validators/source_conflict.py` | conflict 只读摘要              |
| `DbValidationGate`        | `backend/app/db/validation_gate.py`         | validation_report 语境         |

## Wave C 边界

- **Allowed:** `backend/app/ops/data_health*.py`, `tests/test_ops_data_health.py`
- **Forbidden:** `layer4_markets/**`, `staged_evidence.py`, registry 三件套, prod DB write, live fetch

## GitNexus 探索结论（Plan 1a）

- 仓库尚无 `data_health*.py` — greenfield，应复用 ops/validators 模式而非新框架
- `db_inspector.InspectReport` 可作为 report envelope 参考（status/generated_at/mode）
- staged pilot v2 evidence 在 archive：`06-24-round3-real-data-staged-pilot-v2/execute-evidence/`
