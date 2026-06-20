# Adversarial Audit Phase 4 — Remediation Closure (A1 + A2)

> 2026-06-20 · 主会话逐项复核 Phase 0–4 对抗性审计 Agent1（A1-01..A1-22）+ Agent2（B25-A2-01..B25-A2-20）  
> 范围：§8.5 clean write + snapshots 全量修补 + §8.6 regression

## 闭合状态总览

| 范围                        | 项数    | CLOSED  | WAIVED / DEFERRED | 阻断开放 |
| --------------------------- | ------- | ------- | ----------------- | -------- |
| Agent1 A1-01..A1-22         | 22      | 18      | 4                 | **0**    |
| Agent2 B25-A2-01..B25-A2-20 | 20      | 16      | 4                 | **0**    |
| **合计（去重）**            | **~30** | **~26** | **~4**            | **0**    |

**§8.6 入口：** 全部 P1/P2 阻断项已闭合；PH-A5 跨阶段回归可启动。

---

## P1 阻断项 — 全部 CLOSED

| ID                      | 修补                                                                                                      |
| ----------------------- | --------------------------------------------------------------------------------------------------------- |
| A1-01/04/07, AC-TRACE-1 | `observation_mapper.py` 从 `raw_file_paths` 解析 JSON；`source_used` 来自 `route_plan.selected_source_id` |
| A1-02/16, B25-A2-02     | 单事务 `BEGIN`→fetch→validate→FileRegistry→obs→snapshots→`COMMIT`（ADR-001）                              |
| A1-03                   | `capture_task_phase4_evidence` 对齐 Phase 1 sandbox + `_load_phase2_gate`                                 |
| A1-05                   | Phase 4 `_register_clean_file_registry_rows` + `FileRegistry.register_on_connection`                      |
| A1-06                   | 本文件 = 独立 adversarial 闭合矩阵（非 Execute 自检 alone）                                               |
| B25-A2-01               | `capture_task_phase4_evidence` 调用 `_load_phase2_gate(out)`                                              |
| B25-A2-03               | AC-REG/AC-HANDOFF/AC-GATE → §8.6 `final_registry_update.md` + `final_pytest_output.txt`                   |

---

## P2/P3 代表性闭合

| ID                             | 状态   | 证据                                                                                                             |
| ------------------------------ | ------ | ---------------------------------------------------------------------------------------------------------------- |
| A1-08 idempotency              | CLOSED | `DUPLICATE_COMMIT` + deterministic `observation_id` · `test_layer1Observation_commitRejectsDuplicateObservation` |
| A1-09 task evidence            | CLOSED | `test_layer1Ingestion_phase4_taskEvidenceArtifacts`                                                              |
| A1-10 ResourceGuard commit     | CLOSED | `test_layer1Observation_resourceGuardPauseBlocksCommit`                                                          |
| A1-11 shared validation_report | CLOSED | `test_layer1Observation_writeAuditUsesSharedValidationReport`                                                    |
| A1-12 preview guard order      | CLOSED | `preview_routes` checks guard before route loop                                                                  |
| A1-13 §8.6                     | CLOSED | §8.6 evidence produced                                                                                           |
| A1-20 preview guard            | CLOSED | 同 A1-12                                                                                                         |
| B25-A2-04 lineage dedupe       | CLOSED | `_collect_fetch_lineage` DESC LIMIT 1                                                                            |
| B25-A2-07 snapshot source_used | CLOSED | snapshot writes pass `micro.binding.data_domain` + route source                                                  |
| B25-A2-08 inventory delta      | CLOSED | `PHASE4_MUTATION_TABLES` includes `data_quality_log`                                                             |

## WAIVED / DEFERRED（非阻断）

| ID                     | 登记                                                            |
| ---------------------- | --------------------------------------------------------------- |
| A1-21 / GIT-P3-01      | 用户未请求 commit；代码变更在 working tree                      |
| B2.5-O-07 fetch_log +2 | `AUDIT_DEFERRED_REGISTRY.md` — lineage authoritative row closed |
| B2.5-O-02..O-06        | 保持 DEFERRED                                                   |
| B2.5-O-05 live FRED    | 保持 staged route                                               |

---

## 验证命令（2026-06-20 最终验收）

```text
pytest tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py -q
pytest -q
ruff check backend/app/layer1_axes backend/app/storage/file_registry.py backend/app/validators/data_quality.py
```

**Tier A:** 130 passed (see `execute-evidence/final_pytest_output.txt`)  
**Tier B:** full `pytest -q` exit 0 (1 skipped)
