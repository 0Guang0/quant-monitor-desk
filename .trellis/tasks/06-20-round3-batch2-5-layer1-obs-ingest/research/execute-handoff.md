# Execute Handoff — Round 3 Batch 2.5 Layer 1 Observation Ingestion Bridge

> **§8.3 Phase 2 COMPLETE · PH-A2 PASS (remediated) · 对抗性审计 A1/A2 全闭合 · 下一会话 §8.4**  
> 记录时间：2026-06-20

## 当前进度

| 步   | 018A 阶段                   | 状态     | Audit          | 关键证据                                                                   |
| ---- | --------------------------- | -------- | -------------- | -------------------------------------------------------------------------- |
| §8.0 | Boot                        | **DONE** | —              | `research/execute-boot.md`, `execute-evidence/8.0-*.txt`                   |
| §8.1 | Phase 0 DB/contract gate    | **DONE** | **PH-A0 PASS** | `phase0_*`, `research/audit-ph-a0-phase0-gate.md`                          |
| §8.2 | Phase 1 read-only inventory | **DONE** | **PH-A1 PASS** | `phase1_before_ingestion_inventory.*`, `research/audit-ph-a1-inventory.md` |
| §8.3 | Phase 2 route dry-run       | **DONE** | **PH-A2 PASS** | `phase2_route_preview.*`, `research/audit-ph-a2-route.md`                  |
| §8.4 | Phase 3 micro-fetch         | **NEXT** | PH-A3 待做     | —                                                                          |
| §8.5 | Phase 4 clean write         | pending  | PH-A4          | —                                                                          |
| §8.6 | Final regression + closeout | pending  | PH-A5          | —                                                                          |

**本会话已完成：** §8.3 Phase 2 route dry-run + PH-A2 签字。  
**下一会话禁止：** 重跑 Boot/Phase 0/Phase 1/Phase 2、Plan freeze、对抗审计。  
**下一会话入口：** §8.4 Phase 3 micro-fetch staging（`ingestion.py` 扩展 micro_fetch）。

## 下一会话开场（复制）

```text
继续 Batch 2.5 Execute（06-20-round3-batch2-5-layer1-obs-ingest）。
§8.3 Phase 2 已完成；PH-A2 PASS（见 research/audit-ph-a2-route.md）。
勿重跑 Boot / Phase 0 / Phase 1 / Phase 2 / Plan / 对抗审计。
直接从 §8.4 Phase 3 micro-fetch 开始：读 MASTER §8.4 + research/layer1-ingestion-pipeline-tests.md §Phase 3。
RED → GREEN → 全量 pytest；完成后 PH-A3。勿 finish-work 直至 §8.6 + Audit 全 PASS。
```

## §8.4 Phase 3 第一步清单

1. **Read** `MASTER.plan.md` §8.4（AC-P3-1..3）
2. **Read** `research/layer1-ingestion-pipeline-tests.md` §Phase 3
3. **Read** `docs/quality/staged_acceptance_policy.md` + `docs/ops/data_sync_command_matrix.md`（A2-16 boot gate）
4. GitNexus `impact()` — `micro_fetch_staging` / `DataSourceService.fetch`
5. **RED：** five `test_layer1MicroIngestion_*` tests per pipeline-tests §Phase 3
6. **GREEN：** `micro_fetch_staging` with **injected FetchPort only** — **禁止** Layer1 设置 `file_registry_factory`（A2-05/A2-26）
7. 使用 `tests/fixtures/layer1_macro_observation_fixture.json`（已就绪）
8. 产出 `phase3_micro_fetch_evidence.json` + `phase3_no_clean_write_proof.md`
9. 全量 `uv run pytest -q`
10. 写 `research/audit-ph-a3-staging.md` → **PH-A3 PASS** 后方可 §8.5

**AC-TRACE-1：** 仍为 open（route→fetch→…→lineage 未完整）；勿在 Phase 3 handoff 宣称 trace PASS。

## Phase 2 交付物索引（已闭合，勿重复）

| 产物           | 路径                                                                          |
| -------------- | ----------------------------------------------------------------------------- |
| Ingestion 服务 | `backend/app/layer1_axes/ingestion.py` (`preview_routes`)                     |
| Pipeline 测试  | `tests/test_layer1_observation_ingestion.py` (Phase 2 十五测 + task evidence) |
| 对抗性闭合     | `research/adversarial-audit-phase2-remediation.md`                            |
| Route 证据     | `execute-evidence/phase2_route_preview.json/.md`                              |
| 无变更证明     | `execute-evidence/phase2_no_mutation_proof.md`                                |
| GREEN 证据     | `execute-evidence/8.3-green.txt`                                              |
| PH-A2 审计     | `research/audit-ph-a2-route.md`                                               |

**冻结路由：** `ENV-E1-DGS10` → `macro_supplementary.fetch_macro_series` / `series_id=DGS10`；`route_status=READY`（`akshare`）；FRED live **DEFERRED** (B2.5-O-05)。

## 任务元信息

| 项                 | 值                                                         |
| ------------------ | ---------------------------------------------------------- |
| Task slug          | `06-20-round3-batch2-5-layer1-obs-ingest`                  |
| Item ID            | `R3-B2.5-L1-OBS-INGEST`                                    |
| `task.json.status` | `in_progress`                                              |
| 冻结摄取指标       | `ENV-E1-DGS10` → staged `macro_supplementary`（B2.5-O-05） |

## §8 顺序（剩余 · 串行 + Audit 门控）

| 步      | 内容                                      | Audit 门控 | 测试设计                                      |
| ------- | ----------------------------------------- | ---------- | --------------------------------------------- |
| **8.4** | **Phase 3 micro-fetch staging**           | **PH-A3**  | `layer1-ingestion-pipeline-tests.md` §Phase 3 |
| 8.5     | Phase 4 clean write + snapshots + lineage | PH-A4      | pipeline-tests §Phase 4                       |
| 8.6     | Tier A/B + registry + Batch 3 handoff     | PH-A5      | MASTER §9–§10                                 |

## 实现落点（Execute 将扩展）

| 路径                                                   | 阶段     | 说明                                |
| ------------------------------------------------------ | -------- | ----------------------------------- |
| `backend/app/layer1_axes/ingestion.py`                 | §8.4–8.5 | 扩展 `micro_fetch_staging` / commit |
| `tests/fixtures/layer1_macro_observation_fixture.json` | §8.4     | staged payload                      |
| `execute-evidence/phase3_*`                            | §8.4     | micro-fetch 证据                    |

## 禁止（仍适用）

- Layer1 `import create_adapter` 或具体 vendor adapter
- Phase 3 写 clean `axis_observation`
- 绕过 WriteManager / validator 写 clean `axis_observation`
- 默认 live FRED/QMT/Yahoo（须用户授权证据）
- 跨 §8 步批量实现；跳过 RED
- Execute 期间 `trellis-check`（Audit 维度替代）
