# Integration Ledger — B-19 staged pilot v2

> Plan 5c · v3 context packing

## 打包策略

| 策略            | 含义                       |
| --------------- | -------------------------- |
| inline          | MASTER §0/§3 已摘要        |
| summary+pointer | MASTER 摘要 + 原稿         |
| pointer         | implement extract/for 精读 |

## ledger

| source                                                                                          | category     | strategy        | master_anchor | execute_extract    | for_ac_step       |
| ----------------------------------------------------------------------------------------------- | ------------ | --------------- | ------------- | ------------------ | ----------------- |
| `research/integration-ledger.md`                                                                | rule         | inline          | MASTER §0.4   | v3 boot routing    | §8.0              |
| `R3Y-AUD-08-go-no-go.md`                                                                        | decision     | summary+pointer | MASTER §0     | AUD-08 controls    | 全 AC             |
| `docs/quality/production_live_pilot_policy.md`                                                  | rule         | summary+pointer | MASTER §0     | fail-closed staged | AC-SP2-08         |
| `specs/contracts/source_route_contract.yaml`                                                    | contract     | pointer         | MASTER §6     | route status 枚举  | AC-SP2-05         |
| `specs/contracts/data_quality_rules.yaml`                                                       | contract     | pointer         | MASTER §6     | validation 字段    | AC-SP2-06         |
| `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_real_data_staged_pilot_v2.md` | business     | pointer         | MASTER §2     | Q1–Q9 扩样问题     | AC-SP2-01..09     |
| `docs/modules/data_validation_and_conflict.md`                                                  | architecture | pointer         | MASTER §4     | conflict 比较      | AC-SP2-07         |
| `backend/app/ops/staged_pilot.py`                                                               | wiring       | pointer         | MASTER §4     | v1 orchestration   | §8.2–8.7          |
| `backend/app/ops/mutation_proof.py`                                                             | wiring       | pointer         | MASTER §8.8   | proof_status 语义  | R3Y-MUT-PROOF-001 |
| `tests/test_staged_pilot.py`                                                                    | wiring       | pointer         | MASTER §5     | RED/GREEN 基线     | §8 全步           |

## inline 清单

- §0 staged-only + REQ2-EM DEFERRED + AUD-08 控件
- §3.2 defer：TDX live、QMT、yahoo default、FRED live、production clean write
- forbidden：full market scan、unbounded network
