# Adversarial Audit Phase 3 — Remediation Closure (A1 + A2)

> 2026-06-20 · 主会话逐项复核 Phase 3 对抗性审计 Agent1（A1-01..A1-15）+ Agent2（B25-A2-01..B25-A2-11）  
> 范围：Phase 0–3 已执行部分 · Phase 3 micro-fetch staging 对抗性审计后全量修补

## 闭合状态总览

| 范围                        | 项数   | CLOSED | WAIVED / OPEN(登记) | 阻断开放 |
| --------------------------- | ------ | ------ | ------------------- | -------- |
| Agent1 A1-01..A1-15         | 15     | 11     | 4                   | **0**    |
| Agent2 B25-A2-01..B25-A2-11 | 11     | 8      | 3                   | **0**    |
| **合计**                    | **26** | **19** | **7**               | **0**    |

**Phase 4 入口：** 全部 P1/P2 阻断项已闭合；§8.5 RED 可启动。  
**预期开放项（非阻断）：** 已 **追加** 登记至 `MASTER.plan.md` **§0.10**（勿覆盖 §0.9）。

---

## Agent 1 — 逐项闭合（A1-01..A1-15）

| ID    | Sev | 状态        | 修补证据                                                                                       |
| ----- | --- | ----------- | ---------------------------------------------------------------------------------------------- |
| A1-01 | P1  | CLOSED      | `capture_task_phase3_evidence` 使用 fresh `.phase3-micro-fetch-sandbox/`；`before_counts` 全零 |
| A1-02 | P1  | CLOSED      | 重生成 `phase3_micro_fetch_evidence.json`；`file_registry_delta=1` 与 `8.4-green.txt` 一致     |
| A1-03 | P1  | CLOSED      | `audit-ph-a3-staging.md` 独立 Audit PASS；本 remediation 文件 = 主会话复核轮次                 |
| A1-04 | P1  | CLOSED      | 沙箱 `phase3_data_root` 隔离；证据路径 `.trellis/.../sandbox/data`；无项目 `data/` 污染        |
| A1-05 | P2  | CLOSED      | `register_staged_file_registry_rows` 迁至 `backend/app/storage/staged_evidence.py`             |
| A1-06 | P2  | CLOSED      | `test_layer1Ingestion_phase3_taskEvidenceArtifacts` 覆盖任务证据路径                           |
| A1-07 | P2  | WAIVED→登记 | `fetch_log_delta=2` → `AUDIT_DEFERRED_REGISTRY` **B2.5-O-07**；MASTER §0.10                    |
| A1-08 | P2  | WAIVED      | Phase 1 自动分类 vs operator memo 噪声；operator gate 已闭合                                   |
| A1-09 | P2  | OPEN→登记   | `commit_clean_*` 待 §8.5 → **B2.5-O-04**；MASTER §0.10                                         |
| A1-10 | P2  | CLOSED      | `phase0_test_output.txt` 含 018A block + incremental 脚注                                      |
| A1-11 | P3  | WAIVED→登记 | 证据可用 `.venv` python；**G-07** 于 MASTER §0.10                                              |
| A1-12 | P3  | CLOSED      | B2.5-O-02..O-06 于 `AUDIT_DEFERRED_REGISTRY.md`                                                |
| A1-13 | P3  | OPEN→登记   | **AC-TRACE-1** 待 §8.5；MASTER §0.10                                                           |
| A1-14 | P3  | CLOSED      | `layer1-ingestion-gate-tests.md` 更新为 27 gate tests                                          |
| A1-15 | P3  | CLOSED      | 本阶段性 git commit（Phase 4 前，非 finish-work）                                              |

---

## Agent 2 — 逐项闭合（B25-A2-01..B25-A2-11）

| ID        | Sev | 状态        | 修补证据                                                                   |
| --------- | --- | ----------- | -------------------------------------------------------------------------- |
| B25-A2-01 | P1  | CLOSED      | 同 A1-02 GREEN/JSON 对齐                                                   |
| B25-A2-02 | P1  | CLOSED      | 同 A1-01 fresh sandbox + `evidence_baseline_strategy`                      |
| B25-A2-03 | P2  | CLOSED      | `storage/staged_evidence.py` + `staged_acceptance_policy.md` §6            |
| B25-A2-04 | P2  | WAIVED→登记 | 同 A1-07 → B2.5-O-07                                                       |
| B25-A2-05 | P2  | CLOSED      | `micro_fetch_staging` writer txn 内 `ResourceGuard(con=con).check()`       |
| B25-A2-06 | P2  | CLOSED      | `micro_fetch_staging`：preview_route → capability → guard(con) → fetch     |
| B25-A2-07 | P3  | CLOSED      | 外层 `preview_route` 为契约前置；内层 fetch 持久化 ROUTE_PLAN 已文档化     |
| B25-A2-08 | P3  | CLOSED      | `fetch_id`：`ORDER BY fetch_time DESC LIMIT 1`（service 行 authoritative） |
| B25-A2-09 | P3  | CLOSED      | `_relative_to_data_root` 规范化证据与 `file_registry.local_path`           |
| B25-A2-10 | P3  | OPEN→登记   | `commit_*` + §3.4 待 §8.5 → B2.5-O-04                                      |
| B25-A2-11 | P3  | OPEN→登记   | **AC-TRACE-1** 待 §8.5；MASTER §0.10                                       |

---

## 验证命令（2026-06-20 最终验收）

```text
ruff check backend/app/layer1_axes backend/app/datasources/service.py backend/app/storage/staged_evidence.py tests/test_layer1_*.py
pytest tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py -q
pytest tests/test_datasource_service.py tests/test_sync_orchestrator.py tests/test_vendor_fetch_e2e.py tests/test_sync_jobs.py -q
pytest -q
python scripts/production_equivalent_smoke.py --use-service-path
```
