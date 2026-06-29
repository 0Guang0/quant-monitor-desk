# R3H-10 外部索引 — 非 `research/` 路径

> **角色：** 包外路径表。  
> **§A** = 每切片开工前必读（与 `research/` 全部文件并列硬门禁）。  
> **§B** = 执行中按情境打开。  
> **§C** = 源码/测试字典（仅情境路由引用，非每次全文必读）。

---

## §A — 切片开工前必读（外部）

每一次 S10-xx 开工前，与 `research/` 10 份文件一并 **Read 全文**：

| #   | 路径                                                                                                                                 | 内容                                                   |
| --- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ |
| A1  | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_10_DATASOURCE_SERVICE_SSOT.md` | **活卡**：Wave 级目标 · 不在范围 · 阻塞 · Execute 指针 |
| A2  | `docs/implementation_tasks/.../WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md`                                                            | Wave 1 串行门控 · §1 Acceptance criteria               |
| A3  | `docs/decisions/ADR-025-r3h10-sync-fail-closed-datasource-service.md`                                                                | fail-closed 架构决策                                   |
| A4  | `specs/contracts/reference_adoption_guardrails.yaml`                                                                                 | L1/L2/L3 · forbidden_semantics                         |
| A5  | `specs/contracts/datasource_service_contract.yaml`                                                                                   | DataSourceService 契约（路径以仓库为准）               |
| A6  | `AGENTS.md`                                                                                                                          | Trellis Execute gate · GitNexus · 参考树禁令           |

**说明：** `task.json`、路线图、PASS 计划为 Plan/Wave 上下文；若 A2 已覆盖 AC，A6 已由 IDE 规则加载，仍须在开工 checklist 中确认已读。

---

## §B — 执行情境路由（外部文档）

| 情境                            | 路径                                                                   |
| ------------------------------- | ---------------------------------------------------------------------- |
| Rehearsal vs 产品 live 政策全文 | `docs/**/production_live_pilot_policy.md`                              |
| STAGED-PILOT 审计登记           | `docs/quality/round3h_real_data_production_entry_audit.md`             |
| 参考采纳 Batch 追溯             | `docs/implementation_tasks/.../R3H_REFERENCE_ADOPTION_INDEX.md`        |
| 模块轨 / PASS 大图              | `PROJECT_IMPLEMENTATION_ROADMAP.md` · `R3H_PASS_EXECUTION_PLAN.md`     |
| Trellis 任务元数据              | `.trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot/task.json` |
| ADR 全目录                      | `docs/decisions/README.md`                                             |
| Agent 工具链细节                | `agent-toolchain.md` · `CLAUDE.md`                                     |

---

## §C — 源码 · 测试字典（情境路由用）

| 模块              | 路径                                                                                                                                                                                                                    |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DataSourceService | `backend/app/datasources/service.py`                                                                                                                                                                                    |
| Sync orchestrator | `backend/app/sync/orchestrator.py`                                                                                                                                                                                      |
| 生产旁路守卫      | `backend/app/sync/runners.py`                                                                                                                                                                                           |
| staged pilot      | `backend/app/ops/staged_pilot.py` · `ops/staged_pilot_fetch_ports.py`                                                                                                                                                   |
| live pilot        | `backend/app/ops/live_pilot_phase2.py` · `ops/live_pilot_fetch_ports.py`                                                                                                                                                |
| interface probe   | `backend/app/ops/interface_probe.py`                                                                                                                                                                                    |
| 产品 fetch_ports  | `backend/app/datasources/fetch_ports/`                                                                                                                                                                                  |
| 核心测试          | `tests/test_sync_orchestrator.py` · `tests/test_datasource_service.py` · `tests/test_staged_pilot.py` · `tests/test_batch275_live_pilot_gate.py` · `tests/test_data_cli_contract.py` · `tests/test_vendor_fetch_e2e.py` |

---

## 参考项目（禁止 runtime · 结论在包内）

| 说明                       | 路径                                   |
| -------------------------- | -------------------------------------- |
| 参考树根（gitignore 本地） | `参考项目/**`                          |
| 已消化结论 SSOT            | `research/reference-adoption-r3h10.md` |
