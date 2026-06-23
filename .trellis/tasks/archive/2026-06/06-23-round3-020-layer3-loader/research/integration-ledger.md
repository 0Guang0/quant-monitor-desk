# Integration Ledger — 020 Layer3 loader

> Plan 5c · v3 context packing

## 打包策略

| 策略            | 含义                       |
| --------------- | -------------------------- |
| inline          | MASTER §0/§3 已摘要        |
| summary+pointer | MASTER 摘要 + 原稿         |
| pointer         | implement extract/for 精读 |

## ledger

| source                                                                                             | category     | strategy        | master_anchor | execute_extract                 | for_ac_step |
| -------------------------------------------------------------------------------------------------- | ------------ | --------------- | ------------- | ------------------------------- | ----------- |
| `research/integration-ledger.md`                                                                   | rule         | inline          | MASTER §0.4   | v3 boot routing                 | §8.0        |
| `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`                                                    | decision     | summary+pointer | MASTER §0     | staged-only gate                | AC-020-5    |
| `specs/contracts/layer3_loader_contract.yaml`                                                      | contract     | pointer         | MASTER §6     | hard_validation_rules           | AC-020-2/4  |
| `docs/modules/layer3_industry_shock_anchor.md`                                                     | architecture | pointer         | MASTER §4     | §8.5 表结构边界                 | AC-020-1    |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                                               | rule         | summary+pointer | MASTER §5     | 语义断言                        | §8.\*       |
| `.cursor/rules/ponytail.mdc`                                                                       | rule         | pointer         | MASTER §0.3a  | lazy ladder；复用 sensor_loader | §8 全步     |
| `backend/app/layer2_sensors/sensor_loader.py`                                                      | wiring       | pointer         | MASTER §6     | staged_fixture 模式             | §8.2        |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_node_registry.json` | business     | pointer         | MASTER §4     | node 字段形态                   | AC-020-2    |

## inline 清单

- §0 staged limitations（BATCH3 gate + REQ2-EM DEFERRED）
- §3.2 defer：`021` snapshot、lineage 写、production registry
- forbidden：layer2/4/5、lineage contract 写、production DB
