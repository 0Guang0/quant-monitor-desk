# B3V-SYNC 对抗性审计报告（Post Zero-Open Repair）

**Branch:** `fix/round3v-sync-support-matrix-recovery`  
**Worktree:** `quant-monitor-desk-wt-b3v-sync`  
**Date:** 2026-06-25  
**Authority:** `agents/audit-adversarial-authority.md` · `repair-evidence/zero-open-signoff.md` · A1/A2–A8 reports  
**Verdict:** **PASS** · **0 OPEN** · **0 BLOCKING**

---

## 1. 审计范围与对抗命题

| 命题 | 对抗问题 | 结论 |
|------|----------|------|
| VR-SYNC-001 路径 A | 是否以 handoff 静默跳过 crash-window 关闭？ | **否** — 路径 A 显式闭合 |
| Matrix + Recovery | 是否只关 matrix、不关 crash recovery？ | **否** — VR-SYNC-002 与 VR-SYNC-001 同分支闭合 |
| Commit 完整性 | 交付物与 evidence 是否未入库或半入库？ | **完整** — 两 commit 覆盖生产代码 + 任务证据 |

---

## 2. VR-SYNC-001 路径 A — 非静默 handoff

### 2.1 门控证据链（MASTER §9.6）

| 检查项 | 期望 | 实测 |
|--------|------|------|
| 路径 B handoff 文件 | 仅路径 B 时存在 `research/sync-001-handoff.md` | **不存在**（全仓 0 命中） |
| 路径 A crash 测试 | `test_syncJob_incremental_crashWindow_leavesWritingWithWriteId` GREEN | **PASS** |
| 路径 A recovery 测试 | `test_syncJob_incremental_recoverStuckWriting_completesWithoutDoubleWrite` GREEN | **PASS** |
| 负向 guard | hook 非 pytest / recovery 非法状态 fail-closed | **PASS**（ZO-07 两测绿） |
| Runtime 恢复入口 | `DataSyncOrchestrator.recover_stuck_writing_job` | **已实现** |
| ADR-001 窗口 | 写提交后、COMPLETED 前可观测 WRITING+write_id | **符合** — hook 在 `with cm.writer()` **之外**（`runners.py` L501–518），write_id 在事务内 L339 落库 |

**判定：** VR-SYNC-001 经 **路径 A** 关闭，非路径 B re-defer，**无静默 handoff**。`registry_proposed_delta.yaml` 将 `R3-PARTIAL-5` 标为 `CLOSED_BRANCH`；`repair-evidence/sync-crash-window-runbook.md` 提供运维闭环。

### 2.2 对抗追问：hook 是否能在生产注入？

- `post_write_pre_complete_hook` 在 `sync_adapter_bypass_allowed()` 为 False 时抛 `ValueError`（含 `pytest-only`）。
- `test_syncJob_incremental_hook_rejectedOutsidePytest` 在 monkeypatch 关闭 bypass 后验证拒绝。
- **结论：** 生产路径无法滥用 hook 伪造 crash 窗口 — **ACCEPTED**。

---

## 3. Matrix（VR-SYNC-002）与 Crash Recovery — 非「只关一半」

### 3.1 VR-SYNC-002（support matrix）

| 能力 | 实现 | 测试 |
|------|------|------|
| 契约分裂 implemented/reserved | `specs/contracts/sync_job_contract.yaml` | `test_syncJobContract_implementedTypes_matchRuntimeCallables` |
| deferred_error 单源 | YAML `deferred_error` + `contract.py` 常量 | `test_syncJobContract_deferredErrorYaml_parityWithRuntimeConstants` |
| reserved 稳定错误 | `run_full_load` / `run_data_quality` / `run_revision_audit` → `DeferredJobTypeError` | 3× reserved 测试 + `test_advA3_016_orchestratorDeferredRunners` |
| 无裸 NIE | `backend/app/sync/**` 无 `NotImplementedError` | grep 0 命中 |

### 3.2 VR-SYNC-001（crash-window）

| 场景 | MASTER 场景# | 测试 | 状态 |
|------|--------------|------|------|
| 写后 crash → WRITING+write_id | S3 | `test_syncJob_incremental_crashWindow_leavesWritingWithWriteId` | GREEN |
| recovery → COMPLETED 无重复写 | S4 | `test_syncJob_incremental_recoverStuckWriting_completesWithoutDoubleWrite` | GREEN |

**判定：** §9.1–9.3（matrix/deferred）与 §9.5–9.6（crash/recovery）均在同一分支交付并绿测，**不满足**「只关 matrix 不关 VR-SYNC-001」红标（MASTER §7）。

### 3.3 B3V-OPS 边界（只读依赖）

- `git diff master...HEAD` 对 `write_contract.yaml` / `write_manager.py`：**无 diff**。
- WriteManager 写模式语义未被本分支修改 — **PASS**。

---

## 4. Commit 完整性

### 4.1 分支 commit 清单

| Commit | 摘要 | 关键路径 |
|--------|------|----------|
| `fb1cf4c6` | `feat(sync): B3V-SYNC support matrix, deferred errors, and crash-window recovery` | `contract.py`, `orchestrator.py`, `runners.py`, `sync_job_contract.yaml`, `tests/test_sync_orchestrator.py`, `tests/test_r3x_residual_open_items_closure.py`, 任务目录 evidence |
| `4d4640e1` | `chore(loop): refresh test catalog and docs index for B3V-SYNC` | `tests/test_catalog.yaml`, `docs/generated/docs_specs_index.generated.md` |

### 4.2 ZO 闭合对照

| ZO ID | 对抗复检 | 状态 |
|-------|----------|------|
| ZO-01 | `contract.py` + sync 改动已 commit | **CLOSED** |
| ZO-02 | `.trellis/tasks/round3v-sync-support-matrix-recovery/` 已 commit | **CLOSED** |
| ZO-03 | `sync_job_contract.yaml` + `backend/app/sync/**` 已 commit | **CLOSED** |
| ZO-04 | registry 三件套 **按策略未 commit**；`registry-ready.md` 交接协调员 | **CLOSED（政策内 defer）** |
| ZO-05..10 | repair 增补测 + runbook + loop + playbook | **CLOSED** |

**工作区：** `git status --porcelain` 干净（无未提交生产改动）。

**判定：** 不存在「代码在 worktree、证据未入库」类半交付 — **PASS**。

---

## 5. 计划外发现

> 对抗性搜索已完成；下列项经权威层级（设计/契约 > 任务卡 > MASTER）裁定，**均不列为 OPEN**。

| ID | 严重度 | 发现 | 对抗结论 | 处置 |
|----|--------|------|----------|------|
| ADV-01 | — | `tests/test_sync_jobs.py` 骨架测仍可使 `revision_audit`/`data_quality` 在 **StateMachine** 层达 STAGED/COMPLETED | 任务 AC 边界为 **orchestrator `run_*` 入口** + 契约矩阵；reserved 入口已 deferred；骨架测不经过 `run_*` | **ACCEPTED**（scope 外） |
| ADV-02 | — | `D2-P1-1` registry 行 `PARTIALLY_CLOSED`（runner 实现仍 defer Round3F） | `registry_proposed_delta.yaml` + `registry-ready.md` 显式保留 `OPEN_RUNNER_IMPL` | **ACCEPTED**（协调员 merge 后闭合） |
| ADV-03 | — | registry 三件套未在本分支 commit | Playbook §2.5 / ZO-04 政策禁止分支直改 | **ACCEPTED**（COORDINATOR-QUEUED） |
| ADV-04 | — | 全库 `ruff check backend/app/db tests` 有历史 I001/E501 | 与 B3V diff 无关；`ruff check backend/app/sync` 绿 | **ACCEPTED**（pre-existing） |

**显式声明：** 已对抗搜索路径 B handoff、半关 matrix、NIE 泄漏、write 契约越界、hook 生产注入、recovery 误用、commit 缺口 — **无新增 BLOCKING/NON-BLOCKING OPEN**。

---

## 6. 验证复跑（本审计）

### 6.1 B3V slice pytest（10 项）

```text
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
  tests/test_r3x_residual_open_items_closure.py::test_advA3_016_orchestratorDeferredRunners -v

Result: 10 passed in 4.87s
```

### 6.2 其他门控

| Gate | Result |
|------|--------|
| `validate-execute-handoff` | **PASS** (exit 0) |
| `ruff check backend/app/sync` | **PASS** |

---

## 7. OPEN 清单

| ID | Severity | Status |
|----|----------|--------|
| — | — | **0 OPEN** |

---

## 8. 签核

| VR / 批次 | 关闭路径 | 证据 |
|-----------|----------|------|
| VR-SYNC-002 | CLOSED_BRANCH | 契约矩阵 + deferred + advA3_016 |
| VR-SYNC-001 | CLOSED_BRANCH **路径 A** | crash + recovery pytest + runbook |
| Zero-Open Repair | 0 OPEN | `repair-evidence/zero-open-signoff.md` 对抗复检通过 |

**Adversarial re-audit: PASS** — 准许进入协调员 registry §7.3 merge 队列。
