# Execute Handoff — Round 3 Batch 2.5 Layer 1 Observation Ingestion Bridge

> **§8.2 Phase 1 COMPLETE · PH-A1 PASS · 下一会话直接从 §8.3 Phase 2 开始**  
> 记录时间：2026-06-20

## 当前进度

| 步   | 018A 阶段                   | 状态     | Audit          | 关键证据                                                                   |
| ---- | --------------------------- | -------- | -------------- | -------------------------------------------------------------------------- |
| §8.0 | Boot                        | **DONE** | —              | `research/execute-boot.md`, `execute-evidence/8.0-*.txt`                   |
| §8.1 | Phase 0 DB/contract gate    | **DONE** | **PH-A0 PASS** | `phase0_*`, `research/audit-ph-a0-phase0-gate.md`                          |
| §8.2 | Phase 1 read-only inventory | **DONE** | **PH-A1 PASS** | `phase1_before_ingestion_inventory.*`, `research/audit-ph-a1-inventory.md` |
| §8.3 | Phase 2 route dry-run       | **NEXT** | PH-A2 待做     | —                                                                          |
| §8.4 | Phase 3 micro-fetch         | pending  | PH-A3          | —                                                                          |
| §8.5 | Phase 4 clean write         | pending  | PH-A4          | —                                                                          |
| §8.6 | Final regression + closeout | pending  | PH-A5          | —                                                                          |

**本会话已完成：** §8.2 Phase 1 read-only inventory + PH-A1 签字。  
**下一会话禁止：** 重跑 Boot/Phase 0/Phase 1、Plan freeze、对抗审计。  
**下一会话入口：** §8.3 Phase 2 route dry-run（`ingestion.py` 本阶段开始需要）。

## 下一会话开场（复制）

```text
继续 Batch 2.5 Execute（06-20-round3-batch2-5-layer1-obs-ingest）。
§8.2 Phase 1 已完成；PH-A1 PASS（见 research/audit-ph-a1-inventory.md）。
勿重跑 Boot / Phase 0 / Phase 1 / Plan / 对抗审计。
直接从 §8.3 Phase 2 route dry-run 开始：读 MASTER §8.3 + research/layer1-ingestion-pipeline-tests.md §Phase 2。
RED → GREEN → 全量 pytest；完成后 PH-A2。勿 finish-work 直至 §8.6 + Audit 全 PASS。
```

## §8.3 Phase 2 第一步清单

1. **Read** `MASTER.plan.md` §8.3（AC-P2-0..3）
2. **Read** `research/layer1-ingestion-pipeline-tests.md` §Phase 2
3. GitNexus `impact()` — 将新建/修改 `ingestion.py` 与 route 符号
4. **RED：** `uv run pytest tests/test_layer1_observation_ingestion.py::test_layer1Ingestion_routePreview_noMutation tests/test_layer1_observation_ingestion.py::test_layer1Ingestion_noSilentFallback -q`
5. **GREEN：** 产出 `phase2_route_preview.json/.md` + `phase2_no_mutation_proof.md`
6. 全量 `uv run pytest -q`
7. 写 `research/audit-ph-a2-route.md` → **PH-A2 PASS** 后方可 §8.4

## Phase 1 交付物索引（已闭合，勿重复）

| 产物           | 路径                                                          |
| -------------- | ------------------------------------------------------------- |
| Inventory 模块 | `backend/app/layer1_axes/ingestion_inventory.py`              |
| Pipeline 测试  | `tests/test_layer1_observation_ingestion.py` (Phase 1 四测)   |
| Inventory 证据 | `execute-evidence/phase1_before_ingestion_inventory.json/.md` |
| GREEN 证据     | `execute-evidence/8.2-green.txt`                              |
| PH-A1 审计     | `research/audit-ph-a1-inventory.md`                           |
| 数据分类 memo  | `execute-evidence/phase1_data_classification.md`              |

**基线分类：** `fixture_or_staged_evidence`（`axis_observation`=0，`fetch_log`=0；data-root `raw=1`/`parquet=1` 为 `.gitkeep` 占位，见 inventory JSON `data_root_file_samples`）

**权威来源：** 以 `execute-evidence/phase1_before_ingestion_inventory.json` 为准；本 handoff 摘要不得覆盖 JSON 中的 `db_evidence_classification` / `phase2_gate`。

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
| **8.3** | **Phase 2 route dry-run**                 | **PH-A2**  | `layer1-ingestion-pipeline-tests.md` §Phase 2 |
| 8.4     | Phase 3 micro-fetch staging               | PH-A3      | pipeline-tests §Phase 3                       |
| 8.5     | Phase 4 clean write + snapshots + lineage | PH-A4      | pipeline-tests §Phase 4                       |
| 8.6     | Tier A/B + registry + Batch 3 handoff     | PH-A5      | MASTER §9–§10                                 |

## 实现落点（Execute 将创建/扩展）

| 路径                                         | 阶段     | 说明                        |
| -------------------------------------------- | -------- | --------------------------- |
| `backend/app/layer1_axes/ingestion.py`       | §8.3–8.5 | B2.5-O-04；**下一会话开始** |
| `tests/test_layer1_observation_ingestion.py` | §8.3+    | Phase 2–4 管道语义          |
| `execute-evidence/phase2_route_preview.*`    | §8.3     | route dry-run               |

## 禁止（仍适用）

- Layer1 `import create_adapter` 或具体 vendor adapter
- Phase 2 DB/raw/clean mutation
- 绕过 WriteManager / validator 写 clean `axis_observation`
- 默认 live FRED/QMT/Yahoo（须用户授权证据）
- 跨 §8 步批量实现；跳过 RED
- Execute 期间 `trellis-check`（Audit 维度替代）
