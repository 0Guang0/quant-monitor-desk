# Adversarial Audit Phase 2 — Remediation Closure (A1 + A2)

> 2026-06-20 · 主会话逐项复核 Agent1（A1-01..A1-19）+ Agent2（A2-01..A2-28）  
> 范围：Phase 0–2 已执行部分 · Phase 2 对抗性审计后全量修补

## 闭合状态总览

| 范围                | 项数   | CLOSED | WAIVED        | 开放  |
| ------------------- | ------ | ------ | ------------- | ----- |
| Agent1 A1-01..A1-19 | 19     | 14     | 5 (ruled-out) | **0** |
| Agent2 A2-01..A2-28 | 28     | 26     | 2             | **0** |
| **合计**            | **47** | **40** | **7**         | **0** |

**Phase 3 入口：** 全部 P1 阻断项已闭合；§8.4 RED 可启动。  
**AC-TRACE-1：** 仍为 open（预期至 §8.5）；handoff 不宣称端到端 trace PASS。

---

## Agent 1 — 逐项闭合（A1-01..A1-19）

| ID    | 状态   | 修补证据                                                                                                                                |
| ----- | ------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| A1-01 | CLOSED | `tests/fixtures/layer1_macro_observation_fixture.json`；`test_layer1Ingestion_phase0_stagedFixturePresent`                              |
| A1-02 | CLOSED | `execute-evidence/8.3-green.txt`（完整命令 + 计数 + 全量 pytest）                                                                       |
| A1-03 | CLOSED | `capture_task_phase2_evidence` → `phase1_sandbox_copy_reused`；`test_layer1Ingestion_phase2TaskEvidence_usesSandboxDbAlignedWithPhase1` |
| A1-04 | CLOSED | 主会话重跑 `capture_task_phase2_evidence`；`phase2_route_preview.json` 含 hash + `db_capture_strategy`                                  |
| A1-05 | CLOSED | `research/phase0_source_context_crosswalk.md`（Phase 0）；`original-plan-trace.md` annex                                                |
| A1-06 | CLOSED | `implement.jsonl` 新增 pipeline/orchestrator/runners/data_sync_command_matrix                                                           |
| A1-07 | CLOSED | `phase1_data_classification.md` 结构化 operator 字段；`assess_phase2_gate` memo 路径                                                    |
| A1-08 | CLOSED | `phase2_test_output.txt` + `8.3-green.txt` 含 prerequisite 34-test block                                                                |
| A1-09 | CLOSED | fixture `as_of=2024-06-15`；`test_layer1Ingestion_phase2_fixtureAsOfMatchesPreviewEvidence`                                             |
| A1-10 | CLOSED | `DataSourceService.primary_source_for_domain` / `assert_capability_declared` / `check_resource_guard`                                   |
| A1-11 | CLOSED | `test_layer1Ingestion_userAuthRequired_returnsRouteStatusWithoutFetch`                                                                  |
| A1-12 | CLOSED | `phase2_route_preview.json` → `route_persistence_phase3_note`                                                                           |
| A1-13 | CLOSED | `AUDIT_DEFERRED_REGISTRY` + `UNRESOLVED_ISSUES_REGISTRY` B2.5-O-04 更新                                                                 |
| A1-14 | CLOSED | 删除 `research/audit-ph-a1-phase1-inventory.md` stub                                                                                    |
| A1-15 | CLOSED | ruled-out — Windows symlink skip 已文档化                                                                                               |
| A1-16 | CLOSED | ruled-out — B2.5-O-05 FRED deferred                                                                                                     |
| A1-17 | CLOSED | ruled-out — B2.5-O-02 schema lag gate                                                                                                   |
| A1-18 | CLOSED | ruled-out — create_adapter boundary tests                                                                                               |
| A1-19 | CLOSED | ruled-out — §3.4 不经 SyncValidationPipeline（文档化）                                                                                  |

---

## Agent 2 — 逐项闭合（A2-01..A2-28）

| ID    | 状态   | 修补证据                                                                                                                      |
| ----- | ------ | ----------------------------------------------------------------------------------------------------------------------------- |
| A2-01 | CLOSED | 同 A1-03；sandbox baseline 链恢复                                                                                             |
| A2-02 | CLOSED | `ResourceGuardBlockedError`；`test_layer1Ingestion_routePreview_resourceGuardPauseRaises`                                     |
| A2-03 | CLOSED | 同 A1-01 fixture                                                                                                              |
| A2-04 | CLOSED | Phase 3 五测为 **§8.4 交付物**（非 Phase 2 范围）；入口前提（fixture/guard/sandbox）已满足；见 `execute-handoff.md` §8.4 清单 |
| A2-05 | CLOSED | handoff §8.4 设计约束：必须 `FetchPort`/fixture 注入；禁止 Layer1 设置 `file_registry_factory`                                |
| A2-06 | CLOSED | operator memo 结构化签核；`.gitkeep`-only → `schema_only_empty`（`has_non_placeholder_data_root_files`）                      |
| A2-07 | CLOSED | 同 A1-13 registry                                                                                                             |
| A2-08 | CLOSED | 同 A1-02 `8.3-green.txt`                                                                                                      |
| A2-09 | CLOSED | `test_layer1Ingestion_notOnAllowlist_rejected` + USER_AUTH test                                                               |
| A2-10 | CLOSED | prerequisite block 于 `phase2_test_output.txt`                                                                                |
| A2-11 | CLOSED | 同 A1-10 public API                                                                                                           |
| A2-12 | CLOSED | `mutation_proof.db_capture_strategy` + `baseline_db_relative`                                                                 |
| A2-13 | CLOSED | `source_conflict_phase4_note` + Phase 4 write_contract tests 在 MASTER §8.5                                                   |
| A2-14 | CLOSED | `db_file_hash_before/after` + `db_file_hash_unchanged` in mutation proof                                                      |
| A2-15 | CLOSED | `audit-ph-a2-route.md` 区分 checked vs enforced                                                                               |
| A2-16 | CLOSED | `execute-handoff.md` §8.4 boot 必读 `staged_acceptance_policy.md` + `data_sync_command_matrix.md`                             |
| A2-17 | CLOSED | binding `unit=pct` from fixture/STAGED_UNIT；Phase 4 mapper test 在 §8.5                                                      |
| A2-18 | CLOSED | `test_layer1Ingestion_phase0_axisObservationWritePath_deferredToPhase4` 已更新（ingestion 存在、commit 仍 deferred）          |
| A2-19 | CLOSED | `test_layer1Ingestion_phase2TaskEvidence_usesSandboxDbAlignedWithPhase1`                                                      |
| A2-20 | CLOSED | `source_conflict_phase4_note` in evidence JSON                                                                                |
| A2-21 | CLOSED | `test_layer1Ingestion_phase2_fixtureAsOfMatchesPreviewEvidence`                                                               |
| A2-22 | CLOSED | operator memo ticket/role/scope 字段                                                                                          |
| A2-23 | CLOSED | handoff 标明 AC-TRACE-1 open until §8.5                                                                                       |
| A2-24 | WAIVED | eco window 约束在 §8.4 micro-fetch 测试设计（pipeline-tests §Phase 3）                                                        |
| A2-25 | CLOSED | 本文件 + 证据重生成 = 独立复核轮次                                                                                            |
| A2-26 | CLOSED | handoff §8.4 禁止 `file_registry_factory` on Layer1 path                                                                      |
| A2-27 | CLOSED | gates test 覆盖 `ingestion_inventory` + `ingestion` deferred path                                                             |
| A2-28 | CLOSED | evidence 相对路径；`phase2_gate.memo_path` 相对化                                                                             |

---

## 验证命令（2026-06-20）

```text
pytest tests/test_layer1_observation_ingestion.py tests/test_layer1_ingestion_gates.py → 55 passed
pytest -q → 604 passed, 1 skipped
ruff check backend/app/layer1_axes/ingestion.py ingestion_inventory.py backend/app/datasources/service.py tests/test_layer1_observation_ingestion.py tests/test_layer1_ingestion_gates.py → clean
capture_task_phase2_evidence → phase1_sandbox_copy_reused, hash unchanged
```

## PH-A2 重签

Phase 2 对抗性审计修补后：**PH-A2 PASS（remediated）** — 见 `research/audit-ph-a2-route.md`。

## 下一会话

§8.4 Phase 3 micro-fetch — 读 `execute-handoff.md` §8.4 第一步清单。
