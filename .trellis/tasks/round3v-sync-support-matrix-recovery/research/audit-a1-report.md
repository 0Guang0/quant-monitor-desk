# A1 Spec / Trace 审计报告 — B3V-SYNC `round3v-sync-support-matrix-recovery`

| 字段     | 值                                         |
| -------- | ------------------------------------------ |
| 维度     | A1（Spec / Trace / trellis-check）         |
| 分支     | `fix/round3v-sync-support-matrix-recovery` |
| Worktree | `quant-monitor-desk-wt-b3v-sync`           |
| 模型     | composer-2.5                               |
| 审计员   | Audit-A1（只读）                           |
| 日期     | 2026-06-28                                 |
| **裁决** | **PASS**                                   |

---

## 1. 裁决摘要

SYNC-BOOT..06C 垂直切片在代码库中已闭环：**路径 A**（`recover_stuck_writing_job` + crash-window pytest + `registry_proposed_delta.yaml`）。`sync_job_contract.yaml` 与 runtime parity、`DeferredJobTypeError`、incremental `post_write_pre_complete_hook`、orchestrator recovery 与 ADR-001 写提交→COMPLETED 分离语义一致。`write_contract.yaml` / WriteManager **零 diff**。Playbook §8.4 子集 **10 passed**；本审计会话全量 `pytest -q` **exit 0**（含未提交 `conftest.py` R3G bootstrap 修复）。

实现提交 `fb1cf4c6` 已经 `af081770 merge(batch3v)` 进入 `master` 祖先链；当前分支 `master..HEAD` 仅含 Plan QC 文档与 worktree bootstrap，属协调/Plan 轨道增量，**不削弱**已合并实现。

**0 BLOCKING · 4 NON-BLOCKING**（证据陈旧、GitNexus 索引滞后、MASTER §9.1 冻结文案漂移、B02_04 audit-failure 窗口未单测）。

---

## 2. trellis-check 步骤证据（§3.1）

| 检查项          | 结果                     | 证据                                                                                                                                                                                                                                                                |
| --------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 变更范围      | PASS（分支增量）         | `git diff master...HEAD --stat`：23 files；主要为 `.trellis/tasks/round3v-sync-support-matrix-recovery/**`、`WAVE0_BATCH3V_TO_ISSUES_INDEX.md`、`tests/conftest.py`；**无** `write_contract.yaml` / `backend/app/sync/**` / `sync_job_contract.yaml` 在分支 diff 中 |
| 2 任务工件      | PASS                     | `AUDIT.plan.md` §0.1、`MASTER.plan.md` §2/§8/§9、`research/source-index.md` §A–§C、`B02_04` §2–§8 已对照                                                                                                                                                            |
| 3 包上下文      | PASS                     | `python .trellis/scripts/get_context.py --mode packages` → `Spec layers: backend`                                                                                                                                                                                   |
| 4 Spec Quality  | PASS（无 sync 层 index） | `.trellis/spec/backend/sync/` 不存在；契约 SSOT 为 `specs/contracts/sync_job_contract.yaml` + parity 测试防漂移                                                                                                                                                     |
| 5 项目检查      | PASS                     | Playbook §8.4 子集 10 passed；`uv run ruff check backend/app/sync` All checks passed；`uv run pytest -q` exit 0（2026-06-28 本审计，~1778 tests）                                                                                                                   |
| 6 跨层链        | PASS                     | incremental：`runners.py:501-518` 写事务提交后 → hook → `transition(COMPLETED)`；recovery：`orchestrator.py:281-297` 仅 status 转换；WriteManager 只读依赖未改                                                                                                      |
| 7 manifest 对账 | PASS                     | 实现文件 ⊆ `implement.jsonl` 点名；`audit.jsonl` 3 行；`check.jsonl` 1 行（AUDIT.plan）；分支 diff **无** forbidden registry 三件套直接 commit                                                                                                                      |

---

## 3. Trace Authority（AUDIT.plan §0.1）

| 条目                  | 结果          | 证据                                                                                                               |
| --------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------ |
| 原始任务卡 `B02_04`   | PASS          | scope VR-SYNC-001/002 → MASTER §2 AC-SYNC-\*；§4 forbidden → MASTER §1.3/§1.5                                      |
| Playbook §8.4         | PASS          | `BATCH_3V_COORDINATOR_PLAYBOOK.md` §8.4 命令与子集测试绿                                                           |
| source-index          | PASS          | `research/source-index.md` §A–§C 索引完整；`tests/test_sync_runners.py` 纠偏至 `test_sync_orchestrator.py`         |
| ADR-001               | PASS          | COMPLETED 在写提交后；hook 注入点与 ADR 决策 #3 一致                                                               |
| WAVE0 / SYNC-06 拆票  | PASS          | `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §6 + `research/vertical-slices.md` 06A/B/C ↔ MASTER §9.6–9.8                    |
| integration-ledger    | PASS          | `research/integration-ledger.md` 锚点与 §8 切片序一致                                                              |
| omission-check        | PASS          | §C 六类覆盖全 [x]；registry 闭合 explicit defer 至主会话 §7.3                                                      |
| unresolved / registry | PASS（defer） | `research/registry_proposed_delta.yaml` + `repair-evidence/registry-ready.md`；分支禁止直接 commit registry 三件套 |

---

## 4. SYNC-BOOT..06C 切片对账

| 切片      | MASTER §9 | 交付物 / 证据                                                           | 结果 |
| --------- | --------- | ----------------------------------------------------------------------- | ---- |
| SYNC-BOOT | 9.0       | `execute-evidence/9.0-red.txt` / `9.0-green.txt`                        | PASS |
| SYNC-01   | 9.1       | `sync_job_contract.yaml` implemented/reserved/utility/deferred_error    | PASS |
| SYNC-02   | 9.2       | parity 测试 GREEN（并入 9.1 证据链）                                    | PASS |
| SYNC-03   | 9.3       | `run_full_load` → `DeferredJobTypeError`；dq/ra 已实现（R3F-SH）        | PASS |
| SYNC-04   | 9.4       | `registry_proposed_delta.yaml`；`test_advA3_016` → DeferredJobTypeError | PASS |
| SYNC-05   | 9.5       | `post_write_pre_complete_hook` pytest-only；`runners.py:501-506`        | PASS |
| SYNC-06A  | 9.6       | `orchestrator.py:281-297` `recover_stuck_writing_job`                   | PASS |
| SYNC-06B  | 9.7       | crash + recovery pytest；`9.7-red.txt` / `9.7-green.txt`                | PASS |
| SYNC-06C  | 9.8       | `registry_proposed_delta.yaml` VR-SYNC-001 路径 A 关账提案              | PASS |

**路径门控：** 路径 A 已选（非 handoff）；`research/sync-001-handoff.md` 不存在，符合 MASTER §9.8 路径 A。

---

## 5. `sync_job_contract.yaml` 对账（VR-SYNC-002）

| 字段                    | 契约 YAML                                                      | Runtime                                                             | 结果 |
| ----------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------- | ---- |
| `implemented_job_types` | incremental, backfill, reconcile, data_quality, revision_audit | `contract.py:14-16` `IMPLEMENTED_JOB_TYPES`                         | PASS |
| `reserved_job_types`    | full_load                                                      | `RESERVED_JOB_TYPES`；`run_full_load` deferred                      | PASS |
| `utility_operations`    | recover_stuck_writing_job                                      | `orchestrator.py:47-48` kind=utility                                | PASS |
| `deferred_error`        | code/owner/phase/docs_anchor                                   | `test_syncJobContract_deferredErrorYaml_parityWithRuntimeConstants` | PASS |
| run\_\* parity          | —                                                              | `test_syncJobContract_implementedTypes_matchRuntimeCallables`       | PASS |

**注：** MASTER §9.1 冻结 RED 行仍写 reserved=`full_load,data_quality,revision_audit`；执行后 dq/ra 由 R3F-SH 实现，已在 `registry_proposed_delta.yaml` 与测试 docstring 诚实记录（NON-BLOCKING 计划文案漂移）。

---

## 6. Orchestrator recovery 对账（VR-SYNC-001）

| 行为                                 | 实现                                                         | 测试                                                                       | 结果 |
| ------------------------------------ | ------------------------------------------------------------ | -------------------------------------------------------------------------- | ---- |
| 写提交后 crash → WRITING+write_id    | `IncrementalJobRunner.run` hook 在 writer 块外、COMPLETED 前 | `test_syncJob_incremental_crashWindow_leavesWritingWithWriteId`            | PASS |
| recovery → COMPLETED 无 double write | `recover_stuck_writing_job` 仅 `transition`                  | `test_syncJob_incremental_recoverStuckWriting_completesWithoutDoubleWrite` | PASS |
| hook 生产 fail-closed                | `sync_adapter_bypass_allowed()`                              | `test_syncJob_incremental_hook_rejectedOutsidePytest`                      | PASS |
| 非法状态 fail-closed                 | `ValueError` if not WRITING+write_id                         | `test_syncJob_recoverStuckWriting_rejectsInvalidState`                     | PASS |
| 不重复写 clean 表                    | recovery 不改 WriteManager                                   | 行数 `rows_after == rows_before` 断言                                      | PASS |

---

## 7. GitNexus

| 动作                                                        | 结果                                                                                         |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `query("sync job crash window recovery orchestrator")`      | 命中 `orchestrator.py` / `test_sync_orchestrator.py` / `runners.py` 等相关符号               |
| `context("recover_stuck_writing_job")`                      | **未命中**（索引未收录该符号）                                                               |
| `context("DataSyncOrchestrator.recover_stuck_writing_job")` | **未命中**                                                                                   |
| 索引新鲜度                                                  | **WARN**：工作区已有 `orchestrator.py:281` 实现；建议合并前 `node .gitnexus/run.cjs analyze` |

**替代证据：** 源码 `backend/app/sync/orchestrator.py:281-297`、`runners.py:501-518` + 10 条 slice pytest。

---

## 8. Findings

### BLOCKING

无。

### NON-BLOCKING

| ID     | 位置                                              | 发现                                                                                                                                                                   |
| ------ | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A1-N01 | `research/execute-evidence/full-pytest-green.txt` | 已提交证据仍记 `34 failed, exit 1`；本审计会话在 `conftest.py` R3G bootstrap 后全量 **exit 0**。建议 Execute 刷新证据或 commit conftest 修复                           |
| A1-N02 | GitNexus                                          | `recover_stuck_writing_job` 未入索引（§7）                                                                                                                             |
| A1-N03 | `MASTER.plan.md` §9.1                             | 冻结 RED 描述 reserved 含 dq/ra，与当前 R3F 实现矩阵不一致；registry delta 已说明                                                                                      |
| A1-N04 | `B02_04` §6                                       | 「audit-failure window」无独立 pytest；MASTER §3 仅 S3–S4（write-success/status-failure）。ADR-001 窗口聚焦写后→COMPLETED；可接受 scoped closure，但任务卡字面未全覆盖 |

---

## 9. 计划外发现（对抗性搜索）

> 已对照 `agents/audit-adversarial-authority.md` A1：设计边界 + 契约 scope vs diff + Red Flags + 计划外 defer。

| ID     | 严重度       | 发现                                                   | 说明                                                          |
| ------ | ------------ | ------------------------------------------------------ | ------------------------------------------------------------- |
| ADV-01 | NON-BLOCKING | backfill shard 无 `post_write_pre_complete_hook`       | incremental 专属；OP-01 同 A4                                 |
| ADV-02 | NON-BLOCKING | `recover_stuck_writing_job` 不校验 clean 表行是否存在  | runbook 要求运维先确认；`orchestrator.py:291-297`             |
| ADV-03 | NON-BLOCKING | 分支 diff 含 `tests/conftest.py` R3H/R3G bootstrap     | 非 B3V-SYNC 业务；改善 worktree 全量 pytest                   |
| ADV-04 | INFO         | `master..HEAD` 无 sync 实现文件 diff                   | 实现已在 `fb1cf4c6` / `af081770`；本分支为 Plan QC + 协调工件 |
| ADV-05 | INFO         | diff 无 `write_contract` / WriteManager 写模式语义变更 | AUDIT.plan A3 前置满足                                        |

**显式声明：** 已对抗搜索；未发现计划外 forbidden 路径改动；未发现削弱 advA3_016 / crash-window 测试 purpose。

---

## 10. A1 Checklist

- [x] trellis-check 步骤 1–7 有证据（§2 表）
- [x] diff vs audit/check manifest（§2 行 7）
- [x] Trace Authority 已继承或 explicit defer（§3）
- [x] 无 Plan omission（source-index §C 全 [x]）
- [x] GitNexus 已查；索引滞后已 WARN + 源码/file:line 补证

---

## 11. DOUBT（原始 scope / Red Flags）

| Claim                                | 攻击                                                         | 结果         |
| ------------------------------------ | ------------------------------------------------------------ | ------------ |
| VR-SYNC-002 矩阵 + deferred          | parity + full_load DeferredJobTypeError + advA3_016          | **成立**     |
| VR-SYNC-001 须 pytest **或** handoff | 路径 A：9.7 两测绿 + registry delta                          | **成立**     |
| 禁改 write 模式契约                  | `git diff master -- write_contract.yaml write_manager.py` 空 | **成立**     |
| 禁裸 NIE 到边界                      | reserved full_load + advA3_016                               | **成立**     |
| 全库 pytest 绿为 DoD                 | 本审计 exit 0；提交证据仍 exit 1（A1-N01）                   | **部分成立** |

---

## 12. 门控结论

| 项           | 值                                                                                                             |
| ------------ | -------------------------------------------------------------------------------------------------------------- |
| 维度         | A1 Spec / Trace                                                                                                |
| 结论         | **PASS**                                                                                                       |
| BLOCKING     | 0                                                                                                              |
| NON-BLOCKING | 4                                                                                                              |
| 建议跟进     | 刷新 `full-pytest-green.txt`；commit `conftest.py` bootstrap；GitNexus re-analyze；主会话 §7.3 registry 批闭合 |

_审计时间：2026-06-28 · composer-2.5 · 只读 · 未修改生产代码_
