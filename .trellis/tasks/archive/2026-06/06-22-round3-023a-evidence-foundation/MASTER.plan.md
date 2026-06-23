# MASTER 计划 — Round 3 Batch 5A `023A` Layer5 Evidence Foundation

> **Execute 入口** — 最小 evidence foundation；**不得**实现完整 `023` 或 production-live 抓取。

## 0. 元信息

| 字段      | 值                                        |
| --------- | ----------------------------------------- |
| 任务 slug | `06-22-round3-023a-evidence-foundation`   |
| 分支      | `feature/round3-023a-evidence-foundation` |
| 基分支    | `master` @ `76ea3471`                     |
| 前置 gate | `R3-B3-STAGED-DOWNSTREAM-GATE` **CLOSED** |
| 目标合并  | `integration/round3`                      |

### Contract 所有权

- `snapshot_lineage_contract.yaml` — **只读**（`019` 为 owner）
- `layer5_evidence_contract.yaml` — 023A 可增补 foundation 字段

### 019/020/021 兼容性

| 分支  | 对接点                                                               |
| ----- | -------------------------------------------------------------------- |
| `019` | `InstrumentEvidenceRef` + `layer5_instrument_id`；lineage 字段集一致 |
| `020` | `target_type` / `target_id` 供 chain anchor                          |
| `021` | `upstream_snapshot_ids` 可引用 Layer4 snapshot                       |

## 1. 目标

evidence identity、instrument ref、fetch/hash provenance、manual-review、Agent-text-not-fact-source 测试。

## 2. 非目标

完整 `023`、bars/events/financials ingestion、production DB、network fetch。

## 5. 验收命令

见 `AUDIT.plan.md`；foundation pytest + registry alignment gates。
