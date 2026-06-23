# Integration Ledger — 021 Layer3 snapshot builder

> Plan 5c · v3 context packing

## 打包策略

| 策略            | 含义                       |
| --------------- | -------------------------- |
| inline          | MASTER §0/§3 已摘要        |
| summary+pointer | MASTER 摘要 + 原稿         |
| pointer         | implement extract/for 精读 |

## ledger

| source                                                            | category     | strategy        | master_anchor | execute_extract         | for_ac_step |
| ----------------------------------------------------------------- | ------------ | --------------- | ------------- | ----------------------- | ----------- |
| `research/integration-ledger.md`                                  | rule         | inline          | MASTER §0.4   | v3 boot routing         | §8.0        |
| `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`                   | decision     | summary+pointer | MASTER §0     | staged-only gate        | AC-021-6    |
| `specs/contracts/snapshot_lineage_contract.yaml`                  | contract     | pointer         | MASTER §6     | required_fields         | AC-021-2/3  |
| `docs/modules/layer3_industry_shock_anchor.md`                    | architecture | pointer         | MASTER §4     | §8.12.6 snapshot 流程   | AC-021-1/4  |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`              | rule         | summary+pointer | MASTER §5     | 语义断言                | §8.\*       |
| `backend/app/layer3_chains/loader.py`                             | wiring       | pointer         | MASTER §6     | IndustryChainLoadResult | §8.3        |
| `backend/app/layer2_sensors/snapshot_builder.py`                  | wiring       | pointer         | MASTER §6     | L2 snapshot 模式        | §8.3        |
| `backend/app/core/snapshot_lineage.py`                            | wiring       | pointer         | MASTER §6     | lineage kernel          | §8.2        |
| `tests/fixtures/layer3_staged_bundle/layer3_anchor_registry.json` | business     | pointer         | MASTER §4     | anchor ticker 形态      | AC-021-1    |

## inline 清单

- §0 staged limitations（BATCH3 gate + REQ2-EM DEFERRED）
- §3.2 register：`ADV-R3X-LINEAGE-001` / `R3Y-LINEAGE-VR-001` 边界
- forbidden：layer2/4/5 runtime、lineage contract 写、三 registry 写
