# Integration Ledger — 022 Layer4 market structure

> Plan 5c · v3 context packing

## 打包策略

| 策略            | 含义                       |
| --------------- | -------------------------- |
| inline          | MASTER §0/§3 已摘要        |
| summary+pointer | MASTER 摘要 + 原稿         |
| pointer         | implement extract/for 精读 |

## ledger

| source                                               | category     | strategy        | master_anchor | execute_extract          | for_ac_step |
| ---------------------------------------------------- | ------------ | --------------- | ------------- | ------------------------ | ----------- |
| `research/integration-ledger.md`                     | rule         | inline          | MASTER §0.4   | v3 boot routing          | §8.0        |
| `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`        | rule         | summary+pointer | MASTER §SCI   | §3.1+§3.3 权威索引       | AC-022-8    |
| `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`      | decision     | summary+pointer | MASTER §0     | staged-only gate         | AC-022-6    |
| `specs/contracts/layer4_market_contract.yaml`        | contract     | pointer         | MASTER §6     | models + quality_rules   | AC-022-2,3  |
| `specs/contracts/snapshot_lineage_contract.yaml`     | contract     | pointer         | MASTER §6     | required_fields          | AC-022-4,5  |
| `docs/modules/layer4_market_structure.md`            | business     | pointer         | MASTER §4     | MarketAdapter + 表语义   | AC-022-1..3 |
| `docs/architecture/03_runtime_flows.md`              | architecture | pointer         | MASTER §4     | Layer4 运行链路          | §8.4        |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | rule         | summary+pointer | MASTER §5     | 语义断言                 | §8.\*       |
| `backend/app/layer3_chains/snapshot_builder.py`      | wiring       | pointer         | MASTER §6     | L3 snapshot/lineage 上游 | §8.6        |
| `backend/app/core/snapshot_lineage.py`               | wiring       | pointer         | MASTER §6     | lineage kernel           | §8.5        |
| `backend/app/db/write_manager.py`                    | wiring       | pointer         | MASTER §3.3   | clean 写必经             | defer       |

## inline 清单

- §0 staged limitations（BATCH3 gate + REQ2-EM DEFERRED）
- §3.2 register：`ADV-R3X-LINEAGE-001` L4 子集 / `R3Y-LINEAGE-VR-001` 边界
- forbidden：ops/staged 三文件、registry trio
- playbook §8.2 子 AC 已抄入 MASTER §2.1
