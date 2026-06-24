# Integration Ledger — read-only data health v1

> Plan 5c · v3 context packing

## 打包策略

| 策略            | 含义                       |
| --------------- | -------------------------- |
| inline          | MASTER §0/§3 已摘要        |
| summary+pointer | MASTER 摘要 + 原稿         |
| pointer         | implement extract/for 精读 |

## ledger

| source                                               | category     | strategy        | master_anchor | execute_extract  | for_ac_step |
| ---------------------------------------------------- | ------------ | --------------- | ------------- | ---------------- | ----------- |
| `research/integration-ledger.md`                     | rule         | inline          | MASTER §0.4   | v3 boot routing  | §8.0        |
| `docs/quality/production_live_pilot_policy.md`       | decision     | summary+pointer | MASTER §0     | REQ2-EM DEFERRED | AC-DH-BOUND |
| `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`        | rule         | summary+pointer | MASTER §0     | Wave C 铁律      | AC-DH-TEST  |
| `R3Y_readonly_data_health_v1.md`                     | business     | pointer         | MASTER §2     | 九切片 AC        | AC-DH-\*    |
| `specs/contracts/data_quality_rules.yaml`            | contract     | pointer         | MASTER §6     | rule_id 子集     | AC-DH-RULES |
| `docs/ops/data_health_cli.md`                        | architecture | pointer         | MASTER §6     | report schema    | AC-DH-BIZ   |
| `docs/modules/data_validation_and_conflict.md`       | architecture | pointer         | MASTER §4     | validator 边界   | §8.3–8.5    |
| `backend/app/ops/db_inspector.py`                    | wiring       | pointer         | MASTER §6     | read_only mode   | §8.2        |
| `backend/app/ops/staged_pilot.py`                    | wiring       | pointer         | MASTER §6     | manifest 常量    | §8.2, §8.9  |
| `backend/app/validators/data_quality.py`             | wiring       | pointer         | MASTER §6     | validate_rows    | §8.3–8.6    |
| `archive/.../staged-pilot-v2/execute-evidence/`      | business     | pointer         | MASTER §8.9   | v2 evidence 根   | AC-DH-BIZ   |
| `research/vertical-slices.md`                        | rule         | inline          | MASTER §8     | R3Y-DH-01..09    | §8.1–8.9    |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | rule         | summary+pointer | MASTER §5     | 语义断言         | AC-DH-TEST  |
| `docs/quality/ROUND3_TEST_DOCSTRING_HYGIENE_PLAN.md` | rule         | summary+pointer | MASTER §5.0   | 五字段 docstring | AC-DH-TEST  |

## inline 清单

- §0 staged-only + `R3-B2.75-REQ2-EM` DEFERRED
- forbidden：layer4、staged_evidence、registry 三件套、prod write、live fetch
- playbook §8.1 子 AC 已抄入 MASTER §2
