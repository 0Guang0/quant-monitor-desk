# A8 测试与质量审计 — B3V-SYNC

**Verdict:** **PASS**  
**Task:** `round3v-sync-support-matrix-recovery`  
**Role:** Audit-A8 · `qa-expert.md` + `test-automator.md`  
**Date:** 2026-06-28  
**Worktree:** `C:\Users\Guang\Desktop\quant-monitor-desk-wt-b3v-sync`  
**Authority:** `AUDIT.plan.md` §1 A8 · `agents/audit-adversarial-authority.md` · `B02_04` · `MASTER.plan.md` §5/§7

---

## 1. 强制命令复跑（AUDIT.plan §1 A8）

### 1.1 B3V slice — 10 项（矩阵 + deferred + crash/recovery）

```bash
uv run pytest \
  tests/test_sync_orchestrator.py::test_syncJobContract_implementedTypes_matchRuntimeCallables \
  tests/test_sync_orchestrator.py::test_syncJobContract_deferredErrorYaml_parityWithRuntimeConstants \
  tests/test_sync_orchestrator.py::test_syncJob_reservedFullLoad_returnsDeferredJobTypeError \
  tests/test_sync_orchestrator.py::test_syncJob_reservedDataQuality_completesJob \
  tests/test_sync_orchestrator.py::test_syncJob_reservedRevisionAudit_completesJob \
  tests/test_sync_orchestrator.py::test_syncJob_incremental_crashWindow_leavesWritingWithWriteId \
  tests/test_sync_orchestrator.py::test_syncJob_incremental_recoverStuckWriting_completesWithoutDoubleWrite \
  tests/test_sync_orchestrator.py::test_syncJob_incremental_hook_rejectedOutsidePytest \
  tests/test_sync_orchestrator.py::test_syncJob_recoverStuckWriting_rejectsInvalidState \
  tests/test_r3x_residual_open_items_closure.py::test_advA3_016_orchestratorDeferredRunners \
  -v --basetemp=.trellis/tasks/round3v-sync-support-matrix-recovery/.audit-sandbox/pytest
```

**Result:** **10 passed** in 5.30s · **exit 0**

> **注：** 当前代码中 `data_quality` / `revision_audit` 已迁入 `implemented_job_types`（R3F-SH 合并后），对应测名为 `*_completesJob`，非 MASTER §5.3 冻结的 `*_returnsDeferredJobTypeError`（见 §5 计划外发现 A8-01）。

### 1.2 Playbook §8.4 子集

```bash
uv run pytest tests/test_sync_orchestrator.py tests/test_sync_runners.py -q
uv run pytest tests/test_write_manager.py -q
```

**Result:** **56 passed** · **exit 0**（2026-06-28 A8 复跑）

### 1.3 全量回归

```bash
uv run pytest -q
```

**Result:** **exit 0**（全绿；含 skip 项与既有 catalog 一致）

---

## 2. §3.8 Red Flag / AC 覆盖矩阵

| Red Flag / AC                      | 场景          | 测试                                                                                                   | 状态            |
| ---------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------ | --------------- |
| **VR-SYNC-002** 契约矩阵 parity    | S1            | `test_syncJobContract_implementedTypes_matchRuntimeCallables`                                          | PASS            |
| deferred_error 单源                | S2 元数据     | `test_syncJobContract_deferredErrorYaml_parityWithRuntimeConstants`                                    | PASS            |
| reserved `full_load` 稳定 deferred | S2            | `test_syncJob_reservedFullLoad_returnsDeferredJobTypeError`                                            | PASS            |
| `data_quality` 已实现可完成        | S2 更新       | `test_syncJob_reservedDataQuality_completesJob` + `test_b3fQualityRunners_dataQuality_notDeferred`     | PASS            |
| `revision_audit` 已实现可完成      | S2 更新       | `test_syncJob_reservedRevisionAudit_completesJob` + `test_b3fQualityRunners_revisionAudit_notDeferred` | PASS            |
| 无裸 `NotImplementedError`         | §5.0          | `backend/app/sync/**` grep 0 命中                                                                      | PASS            |
| 调用方不得误以为 full_load 已实现  | advA3_016     | `test_advA3_016_orchestratorDeferredRunners`                                                           | PASS            |
| **VR-SYNC-001** 写后 crash 窗口    | S3            | `test_syncJob_incremental_crashWindow_leavesWritingWithWriteId`                                        | PASS            |
| recovery 无重复写                  | S4            | `test_syncJob_incremental_recoverStuckWriting_completesWithoutDoubleWrite`                             | PASS            |
| hook 生产 fail-closed              | ZO-07         | `test_syncJob_incremental_hook_rejectedOutsidePytest`                                                  | PASS            |
| recovery 非法状态 fail-closed      | ZO-07         | `test_syncJob_recoverStuckWriting_rejectsInvalidState`                                                 | PASS            |
| runner 接线回归                    | Playbook §8.4 | `test_syncRunners_orchestratorWiresRunnerAttributes`                                                   | PASS            |
| WriteManager 写模式未改            | A3 只读       | `tests/test_write_manager.py` 全绿                                                                     | PASS            |
| 与 OPS 并发改 write 契约           | MASTER §7     | 本分支无 `write_contract` diff                                                                         | PASS（A3 口径） |
| 只关 matrix 不关 VR-SYNC-001       | MASTER §7     | §9.5–9.7 crash+recovery 同分支绿测                                                                     | PASS            |

**VR-SYNC-001 关闭路径：** **路径 A**（crash-window pytest + `recover_stuck_writing_job`）；`research/sync-001-handoff.md` **不存在**。

---

## 3. Crash-window recovery 专项审查

| 检查项           | 期望                                              | 实测                                                                          |
| ---------------- | ------------------------------------------------- | ----------------------------------------------------------------------------- |
| ADR-001 窗口语义 | 写事务提交后、COMPLETED 前可观测 WRITING+write_id | hook 在 writer 事务外调用；`write_id` 事务内落库 — **符合**                   |
| 注入点仅测试     | 生产不可注入 `post_write_pre_complete_hook`       | `sync_adapter_bypass_allowed()==False` → `ValueError(pytest-only)` — **PASS** |
| 恢复入口         | `recover_stuck_writing_job` 仅 WRITING+write_id   | 正向 + 负向测均绿                                                             |
| 无二次写入       | recovery 后 clean 行数不变                        | `rows_after == rows_before` 断言 — **PASS**                                   |
| 运维闭环         | runbook 指向 closure tests                        | `repair-evidence/sync-crash-window-runbook.md` 四测齐全 — **PASS**            |

**判定：** crash-window recovery 有语义断言、负向 guard、runbook 三联证据，满足 AUDIT.plan A5「§9.7 pytest 路径 A」与 Playbook §8.4 crash-window 行。

---

## 4. 测试契约质量（qa-expert checklist）

| 项                                     | 结论                                                                                                                  |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 五字段注释（覆盖/对象/目的/验证/失败） | 10 项 slice 均具备                                                                                                    |
| 无 tautological 断言                   | deferred 测检查 code/owner/phase/docs_anchor；crash 测检查 status+write_id；recovery 测检查行数 — **非空断言**        |
| sandbox 隔离                           | `--basetemp=<task>/.audit-sandbox/pytest` 可用（Windows 需先 `mkdir -p` 父目录）                                      |
| purpose 未为绿削弱                     | `test_advA3_016` 仍断言 `DeferredJobTypeError`（非 NIE）；dq/ra purpose 已随契约正当更新为 COMPLETED                  |
| test catalog                           | `tests/test_catalog.yaml` 已登记 `test_sync_orchestrator.py` / `test_sync_runners.py` / `test_b3f_quality_runners.py` |
| flaky                                  | 全模块串行 `-q` 绿；共享 basetemp 下 Windows DuckDB lock 可能偶发 — **环境项，非 B3V 逻辑缺陷**                       |

---

## 5. DOUBT 对抗追问

| 问题                                      | 搜索范围                                         | 结论                                                                                                  |
| ----------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| 每个 Red Flag 是否有测或 explicit defer？ | §2 矩阵                                          | **已覆盖**                                                                                            |
| 仅 matrix 关闭、crash 静默跳过？          | handoff 文件、§9.6–9.8 证据                      | **否** — 路径 A 显式                                                                                  |
| reserved 仍泄漏 NIE？                     | `backend/app/sync` grep                          | **0 命中**                                                                                            |
| dq/ra defer 测删了但无替代？              | `test_b3f_quality_runners.py` + `*_completesJob` | **有替代**                                                                                            |
| audit-failure 窗口（B02_04 §6 原文）      | 全 `tests/` + `runners.py` hook 点               | **未单独 pytest** — MASTER §3 仅冻结 S3/S4（ADR-001 写→COMPLETED 窗）；见 §6 A8-04 **ACCEPTED defer** |

---

## 6. 计划外发现

> 对抗性搜索已完成；下列项已按权威层级（契约/任务卡 > MASTER §5）裁定。

| ID    | 严重度       | 发现                                                                                                                                                                                                                                                          | 处置                                                                                                                   |
| ----- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| A8-01 | NON-BLOCKING | `MASTER.plan.md` §5.3、`repair-evidence/playbook-8.4-green.txt`、`research/adversarial-audit-report.md` §6.1 仍引用已删除的 `test_syncJob_reservedDataQuality_returnsDeferredJobTypeError` / `test_syncJob_reservedRevisionAudit_returnsDeferredJobTypeError` | **DOC DRIFT** — 应以当前 selector（`*_completesJob`）为准；A8 复跑已用正确名称 10/10 绿                                |
| A8-02 | NON-BLOCKING | `adversarial-audit-report.md` §3.1 表仍写「三 reserved → DeferredJobTypeError」，与 `sync_job_contract.yaml`（仅 `full_load` reserved）矛盾                                                                                                                   | 文档未随 R3F-SH 合并更新；**不影响测试真实性**                                                                         |
| A8-03 | —            | `tests/test_b3f_quality_runners.py` 在 slice 10 项外补充 dq/ra/full_load 三角验证                                                                                                                                                                             | **正向** — 加强 W-A8-05 full_load 仍 defer                                                                             |
| A8-04 | NON-BLOCKING | B02_04 §6「audit-failure windows」无独立 pytest                                                                                                                                                                                                               | **ACCEPTED** — 本任务 MASTER §3 场景矩阵仅 S3/S4；`registry_proposed_delta.yaml` 将 R3-PARTIAL-5 按 ADR-001 写后窗关闭 |
| A8-05 | —            | `tests/test_sync_jobs.py` 骨架测可在 StateMachine 层达 STAGED/COMPLETED，不经 `run_*`                                                                                                                                                                         | **ACCEPTED**（scope 外，prior adversarial ADV-01 同裁）                                                                |

**显式声明：** 已搜索 handoff 旁路、NIE 泄漏、hook 生产注入、recovery 误用、弱断言、冻结 selector 失效 — **无 BLOCKING OPEN**。

---

## 7. §4.3 OPEN 清单

| ID  | Severity | Status     |
| --- | -------- | ---------- |
| —   | —        | **0 OPEN** |

（A8-01/A8-02 为证据文档漂移，不阻塞 finish-work；建议主会话合并时刷新 playbook 证据 selector 一行。）

---

## 8. 签核

| 门控                               | 结果                                          |
| ---------------------------------- | --------------------------------------------- |
| B3V slice 10 tests                 | **PASS**                                      |
| Playbook §8.4 sync + write_manager | **PASS**                                      |
| Full `pytest -q`                   | **PASS**                                      |
| VR-SYNC-001 路径 A                 | **PASS**                                      |
| VR-SYNC-002 矩阵 + deferred        | **PASS**                                      |
| A6                                 | **SKIP**（AUDIT.plan 记录 — 无 hot path SLA） |

**Audit-A8: PASS** — 准许与 A1–A7 汇总进 `audit.report.md` / `finish-work` 门控。
