# A3 audit-security — B3V-SYNC Sync Support Matrix & Crash-window Recovery

> **维度：** A3 · security-auditor + security-and-hardening + doubt-driven-development  
> **任务：** `round3v-sync-support-matrix-recovery`（B3V-SYNC · Manifest `B3V-C04`）  
> **Worktree：** `quant-monitor-desk-wt-b3v-sync` · branch `fix/round3v-sync-support-matrix-recovery`  
> **日期：** 2026-06-28  
> **模式：** Audit（只读，无 commit、无改码、无写 `data/`）

---

## 总判定

| 项                   | 值                                                                          |
| -------------------- | --------------------------------------------------------------------------- |
| **verdict**          | **PASS**                                                                    |
| **BLOCKING**         | 0                                                                           |
| **NON-BLOCKING**     | 2（P3 hygiene）                                                             |
| **AUDIT.plan §1 A3** | **PASS** — `write_contract.yaml` / `WriteManager` 相对 `master` **零 diff** |

---

## 审计范围

| 来源             | 路径 / 动作                                                                                                                                                 |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AUDIT.plan Trace | `specs/contracts/sync_job_contract.yaml` · `backend/app/sync/**` · `tests/test_sync_orchestrator.py` · forbidden: `write_contract.yaml`                     |
| 任务卡           | `B02_04_sync_job_support_and_recovery.md` §4 Forbidden                                                                                                      |
| diff vs `master` | 生产 sync 代码已在 `master`（`fb1cf4c6` 等）；本分支相对 `master` 主要为 Plan/docs；工作区另有未提交 `tests/conftest.py` bootstrap                          |
| 静态命令         | `rg` 基线（`backend/app/sync/`）+ `git diff master -- write_contract.yaml write_manager.py`                                                                 |
| GitNexus         | `query({query: "sync job write path security guard adapter bypass"})` — 1 次；`context(recover_stuck_writing_job)` 符号未索引（索引滞后，以源码 + rg 补证） |

---

## AUDIT.plan §1 A3 门控

| 检查项                                 | 命令 / 证据                                              | 结果        |
| -------------------------------------- | -------------------------------------------------------- | ----------- |
| `write_contract.yaml` 无写模式语义变更 | `git diff master -- specs/contracts/write_contract.yaml` | **空 diff** |
| `WriteManager` 无写模式语义变更        | `git diff master -- backend/app/db/write_manager.py`     | **空 diff** |
| forbidden 面未触碰                     | 同上 + A1 交叉确认                                       | **PASS**    |

---

## §3.3 威胁面与发现

| 威胁                    | 发现                                                                                                                                                           | 等级                    | 证据                                                                                                                  |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------- | ---------- | ---------- | ---------- |
| 未授权写库 / 写契约绕过 | 本任务未改 `write_contract` / `WriteManager`；写路径仍经 `SyncWritePipeline` → `WriteManager` + validation gate                                                | —                       | `git diff` 空；`write_contract.yaml` `implemented_modes` 未变                                                         |
| 保留 job 误当已实现     | `run_full_load` 抛 `DeferredJobTypeError`（稳定 code/owner/phase/docs_anchor）；`backend/app/sync/**` 无 `NotImplementedError`                                 | —                       | `orchestrator.py` L269–271 · `contract.py` L24–46 · rg `NotImplementedError` 0 命中                                   |
| 生产 adapter 旁路       | `guard_production_adapter_bypass` / `guard_runner_direct_adapter_bypass`；仅 `PYTEST_CURRENT_TEST` 可 bypass                                                   | —                       | `runners.py` L36–71 · `orchestrator.py` L184–187                                                                      |
| crash-window hook 注入  | `post_write_pre_complete_hook` 非 pytest 抛 `ValueError`（`pytest-only`）                                                                                      | —                       | `runners.py` L501–505 · `test_syncJob_incremental_hook_rejectedOutsidePytest`                                         |
| 恢复入口滥用            | `recover_stuck_writing_job` 要求 `status=WRITING` 且 `write_id` 非空，否则 `ValueError`；`kind=utility` 不在 `implemented_job_types` / schedulable `job_types` | P3                      | `orchestrator.py` L281–297 · `sync_job_contract.yaml` L13–14 · `test_syncJob_recoverStuckWriting_rejectsInvalidState` |
| 运维恢复无二次写校验    | 恢复仅 `transition(COMPLETED)`，不重复 `WriteManager.write`（设计意图）；依赖操作员按 runbook 确认 clean 行已存在                                              | P3                      | `repair-evidence/sync-crash-window-runbook.md` §Recovery · ADR-001 有意窗口                                           |
| 明文密钥 / token        | `backend/app/sync/` rg `api_key                                                                                                                                | secret                  | token                                                                                                                 | password      | https?://` | —          | **0 命中** |
| live 源默认开启         | rg `enable.qmt                                                                                                                                                 | enable.xqshare` in sync | —                                                                                                                     | **0 命中**    |
| 命令执行面              | rg `subprocess                                                                                                                                                 | os.system               | eval                                                                                                                  | exec` in sync | —          | **0 命中** |
| YAML 任意加载           | 契约路径固定 + `yaml.safe_load`                                                                                                                                | —                       | `contract.py` L19–42                                                                                                  |
| SQL 拼接（继承）        | `ReconcileJobRunner` 对 `compare_table` / `fetch_result.staging_table` 使用 f-string DDL/DML，未走 `quote_ident`                                               | P3（继承）              | `runners.py` L924–1030 · 对比 `write_manager.py` L76–77 已用 `quote_ident`                                            |

**结论：** 无 P0/P1；B3V-SYNC 新增/触及的信任边界（deferred 错误、crash hook guard、utility 恢复）均为 **fail-closed** 或 **运维文档化**；写契约未被削弱。

---

## DOUBT 三类对抗（须有发现或「无发现 + 范围」）

| 类                    | 搜索范围                                                                           | 结论                                                                                                                                                                                                 |
| --------------------- | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----- | ---------------- |
| 1. 硬编码 URL 变体    | `backend/app/sync/` · `sync_job_contract.yaml` · `tests/test_sync_orchestrator.py` | **无发现** — rg `https?://` 0 命中                                                                                                                                                                   |
| 2. JWT / API key 模式 | 同上 + `contract.py`                                                               | **无发现** — rg `api[_-]?key                                                                                                                                                                         | secret | token | password` 0 命中 |
| 3. SQL 拼接           | `backend/app/sync/`                                                                | **有发现（继承）** — `runners.py` L955–1030 f-string 表名；**非本分支引入**；`compare_table` 取自 `conflict_id[:8]`，`staging_table` 来自 adapter 返回值，信任边界在 adapter/DB 行而非 HTTP 用户输入 |

---

## 计划外发现

| ID        | 级别              | 描述                                                                                            | 证据                                          | 处置                                                              |
| --------- | ----------------- | ----------------------------------------------------------------------------------------------- | --------------------------------------------- | ----------------------------------------------------------------- |
| A3-OOB-01 | NON-BLOCKING (P3) | `ReconcileJobRunner` reconcile 路径 f-string SQL 未统一 `quote_ident` 白名单                    | `runners.py` L955–1030                        | 继承债务；B3V-SYNC 未扩大该面；后续 Round 3F reconcile 硬化可跟进 |
| A3-OOB-02 | NON-BLOCKING (P3) | 工作区未提交 `tests/conftest.py` 将 fixture 模板物化到 `.audit-sandbox/**`（R3H/R3G auth YAML） | `git diff master -- tests/conftest.py` L39–81 | 非 B3V-SYNC 核心 diff；模板非生产密钥；仅 pytest bootstrap        |
| —         | —                 | **已对抗搜索、无额外 BLOCKING**                                                                 | 全表扫描 sync trace + AUDIT forbidden 面      | —                                                                 |

---

## 任务卡安全约束对照（B02_04 §4）

| 约束                                   | 状态     | 证据                                                                                               |
| -------------------------------------- | -------- | -------------------------------------------------------------------------------------------------- |
| 不得将 reserved job 暴露为可用 CLI/API | **满足** | `full_load` → `DeferredJobTypeError`；`utility_operations` 与 `job_types` 分离（`test_r3fBr07_*`） |
| 不得 production clean write            | **满足** | 测试用 tmp DB；无 `--write` / migrate 新增                                                         |
| 不得用泛化异常隐藏 defer               | **满足** | 专用 `DeferredJobTypeError`；无裸 NIE                                                              |

---

## Checklist（security-auditor.md）

- [x] 范围 = AUDIT Trace + diff forbidden 面
- [x] DOUBT 三类已查并记录
- [x] 发现附 `file:line` 或 rg 输出
- [x] 建议可执行（OOB-01 → reconcile 路径 `quote_ident`；OOB-02 → 保持 template-only bootstrap）
- [x] 不以自述为 PASS（`git diff` + rg + 测试名交叉）

---

## 建议（非阻断）

1. **A3-OOB-01：** 若 touch `ReconcileJobRunner`，将 `compare_table` 生成改为 `quote_ident` 或固定前缀 + UUID hex，并对 `fetch_result.staging_table` 做 identifier 校验（与 `WriteManager` 对齐）。
2. **恢复审计：** 可选在 `recover_stuck_writing_job` 的 `transition` message 中固定 event_type（如 `CRASH_WINDOW_RECOVERY`）便于 ops 日志检索——当前已有 message `recovered after crash-window`。

---

_Audit A3 · B3V-SYNC · 静态只读 · 2026-06-28_
