# Plan Boot — round3-023b-evidence-chain-full (B01-023)

## 用户目标

在 `023A` 最小 evidence foundation 之上，交付完整 Layer5 evidence chain（instrument registry、bar/event/financial/valuation 模型骨架、evidence chain builder、冲突复核 ADR），支撑 Layer3/4 溯源展开；**Wave D Track B 单独合并**。

## 依赖与 gate

| 项 | 状态 | 说明 |
| --- | --- | --- |
| `023A` foundation | **基线已存在** | `backend/app/layer5_evidence/{foundation,models,lineage}.py` + `test_layer5_evidence_foundation.py` |
| `021` Layer3 snapshot | **基线已存在** | `layer3_chains/snapshot_builder.py` |
| `022` Layer4 market | **基线已存在** | `layer4_markets/market_structure.py` |
| 任务卡 §16 | **Plan 前提满足** | 022 + L3/L4 集成代码已在 worktree；Execute 前须全量 pytest 绿 |
| Batch 01 六卡 | **并行开发 OK** | 不得混 PR；registry 三件套仅主会话 |

## AC 草稿（→ MASTER §2）

| Roadmap ID | 草稿 AC |
| --- | --- |
| `R3D-023-01` | instrument_registry 唯一性 + evidence identity 延续 023A |
| `R3D-023-02` | bar/event/financial/valuation staged 模型校验 + no-future-data |
| `R3D-023-03` | evidence_chain builder 串联 L3/L4/L5 context；Agent 文本非事实源 |
| `R3D-023-04` | `R3-PARTIAL-4` ADR：severe → manual-review queue（非 instant severe UI） |
| `R3D-023-05` | 若触及 storage：最小 `EvidenceReadPort` injection；否则 explicit re-defer `R2-RISK-2` |

## 边界（playbook §2.5/§2.6）

- **Owns:** `backend/app/layer5_evidence/**`、`specs/contracts/layer5_evidence_contract.yaml`、L5 测试
- **Must not:** live source、production 写入、registry 三件套并发闭合

## 原计划已读

- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md`（含 §16、§17）
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/023A_layer5_evidence_foundation.md`（归档对照）
- `PROJECT_IMPLEMENTATION_ROADMAP.md` Batch 3D.1（`R3D-023-01`..`05`）
- `docs/quality/coordination/BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §0、§2.5–§2.7、§3.2、§4、§8.4

**Phase P0 complete**
