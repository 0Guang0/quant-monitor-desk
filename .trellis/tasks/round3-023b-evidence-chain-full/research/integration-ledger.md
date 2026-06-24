# Integration Ledger — 023b Layer5 evidence chain

> Plan 5c · v3 context packing

## 打包策略

| 策略 | 含义 |
| --- | --- |
| inline | MASTER §0/§3 已摘要 |
| summary+pointer | MASTER 摘要 + 原稿 |
| pointer | implement extract/for 精读 |

## ledger

| source | category | strategy | master_anchor | execute_extract | for_ac_step |
| --- | --- | --- | --- | --- | --- |
| `research/integration-ledger.md` | rule | inline | MASTER §0.4 | v3 boot routing | §9.0 |
| `docs/quality/coordination/BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` | rule | summary+pointer | MASTER §SCI | §3.2 + playbook §8.4 | AC-023-6 |
| `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md` | decision | summary+pointer | MASTER §0 | staged-only gate | AC-023-6 |
| `docs/adr/ADR-023-layer5-conflict-review-path.md` | decision | inline | MASTER §8#4 / §9.4 | R3-PARTIAL-4 路径 | AC-023-4 |
| `docs/architecture/03_runtime_flows.md` | architecture | pointer | MASTER §4 | Layer5 运行链路 | §9.3 |
| `docs/architecture/module_boundary_matrix.md` | architecture | pointer | MASTER §SCI | layer5 边界 | AC-023-5 |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_HARDENING_RULES.md` | rule | summary+pointer | MASTER §0 | §1–§3 硬停 | AC-023-6 |
| `specs/contracts/layer5_evidence_contract.yaml` | contract | pointer | MASTER §6 | models + deferred_to_023b | AC-023-1..3 |
| `specs/contracts/snapshot_lineage_contract.yaml` | contract | pointer | MASTER §6 | required_fields | AC-023-2,3 |
| `docs/modules/layer5_security_evidence.md` | business | pointer | MASTER §4 | evidence_chain 表语义 | AC-023-3 |
| `docs/modules/data_validation_and_conflict.md` | business | pointer | MASTER §8#4 / §9.4 | manual_review_queue | AC-023-4 |
| `backend/app/layer5_evidence/foundation.py` | wiring | pointer | MASTER §6 | 023A 复用 | AC-023-1,3 |
| `backend/app/layer3_chains/snapshot_builder.py` | wiring | pointer | MASTER §6 | upstream_snapshot_ids | AC-023-3 |
| `backend/app/layer4_markets/market_structure.py` | wiring | pointer | MASTER §6 | upstream L4 | AC-023-3 |
| `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md` | rule | pointer | MASTER §3.2 | R3-PARTIAL-4 / R2-RISK-2 | AC-023-4,5 |

## inline 清单

- §0 Track B 分轨 + §16 gate
- §3.2 register：`R3-PARTIAL-4` ADR / `R2-RISK-2` 条件 port
- forbidden：live、registry trio、L3/L4 写
- playbook §8.4 子 AC 已抄入 MASTER §2.1
