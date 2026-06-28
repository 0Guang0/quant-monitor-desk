# MASTER 计划 — B3V-SYNC Sync Job Support Matrix & Crash-window Recovery

> **Execute 入口** — staged/sandbox only；**不得** production clean write。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`  
> **合并建议**：在 **B3V-OPS** 之后 FF merge（`write_contract` 只读依赖）。

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| 任务 slug | `round3v-sync-support-matrix-recovery` |
| Playbook ID | B3V-SYNC · Manifest B3V-C04 |
| 分支 | `fix/round3v-sync-support-matrix-recovery` |
| Worktree | `../quant-monitor-desk-wt-b3v-sync` |
| 模型 | `composer-2.5` |
| 前置 | master post Batch 01；**只读依赖** B3V-OPS `write_contract.yaml` / `WriteManager` |
| manifest_protocol_version | `3` |
| analysis_waiver | `false` |
| 原计划 | `research/source-index.md` · `research/original-plan-trace.md` |

### Batch 3V 边界（Playbook §2.5 / §2.6）

| Owns | Must not |
|------|----------|
| `specs/contracts/sync_job_contract.yaml` | `write_contract.yaml` / WriteManager **写模式语义**（B3V-OPS 独占） |
| `backend/app/sync/**` deferred errors、crash hook/recovery | CLI 发布；production clean write |
| crash-window pytest **或** `research/sync-001-handoff.md` | 裸 `NotImplementedError` 泄漏到边界 |
| registry **proposed delta**（D2-P1-1 / R3-PARTIAL-5） | 主会话外直接 commit registry 闭合 |

### 0.1 Execute 必读

Phase 0 **逐条 Read `implement.jsonl`**（清单以文件为准）。

### 0.3 Execute 强制必读 manifest（E4）

Boot 前 Read **`research/integration-ledger.md`**；Phase 0 **逐条 Read `implement.jsonl`**；动态闭包见 `research/context-closure.md`（Execute 创建）。

### 0.3a Ponytail

MUST Read `.cursor/rules/ponytail.mdc`；复用 `WriteManager` deferred 文案模式；最小 diff。

### 0.3b 测试纪律

五字段 docstring；RED 必须先 FAIL；禁止为绿削弱 `test_advA3_016` 业务保障（可改断言类型）。

### Source Context Index（Playbook §3.1 + §3.5）

#### §3.1 共用底座

| 路径 | 摘要 | implement |
|------|------|-----------|
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` | §2.5 锁、§7 合并、§8.4 PASS | [x] |
| `BATCH_3V_TASK_CARD_MANIFEST.md` | C04 依赖 B3V-C01 recommended | [x] |
| `BATCH_3V_HARDENING_RULES.md` | 禁 production write/live | [x] |
| `BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md` | Batch 入口 | [x] |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | VR-SYNC 路由 | [x] |
| `GLOBAL_EXECUTION_RULES.md` 等 ×3 | 全局纪律 | [x] |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3V | R3V-B02-SYNC | [x] |
| Registry 三件套 | **只读**；proposed delta | [x] |
| `write_contract.yaml` · `runtime_versions.md` | **只读**（OPS 契约） | [x] |

#### §3.5 B3V-SYNC

| 路径 | 摘要 | implement |
|------|------|-----------|
| `B02_04_sync_job_support_and_recovery.md` | 权威 AC | [x] |
| `specs/contracts/sync_job_contract.yaml` | implemented/reserved SSOT | [x] |
| `backend/app/sync/orchestrator.py` · `runners.py` | runtime | [x] |
| `backend/app/db/write_manager.py` | crash-window **只读** | [x] |
| `docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md` | COMPLETED 顺序 | [x] |
| `tests/test_sync_orchestrator.py` | 主测试文件 | [x] |
| `tests/test_write_manager.py` | 回归（只读模式参考） | [x] |
| `docs/modules/data_sync_orchestrator.md` | 模块文档锚点（若存在） | [x] |

---

## 1. 目标与约束

### 1.1 目标

显式 sync job support matrix；reserved 返回稳定 `DEFERRED_JOB_TYPE` 风格错误；关闭 `VR-SYNC-002`；`VR-SYNC-001` 经 crash-window pytest **或** Round 3F.4 handoff 关闭/精确 re-defer。

### 1.3 约束

- 无 production DB mutation；无 live fetch
- **只读依赖** B3V-OPS write 模式契约；Execute 不得修改 `write_contract.yaml` 或 WriteManager `SUPPORTED_MODES`/`UNSUPPORTED_MODES` 语义
- 任务卡引用的独立 runners 测试模块未入库 — 用 `tests/test_sync_orchestrator.py`（§5.1）

### 1.5 停止条件

| # | 事件 | 处理 |
|---|------|------|
| 1 | Plan 未 freeze | 禁止 start |
| 2 | 修改 `write_contract.yaml` 或 WriteManager 写模式 | 中止；退回 Plan |
| 3 | production clean write / live fetch | 中止 |
| 4 | SYNC-06* 需同事务 COMPLETED 且触及 ADR/WriteManager | 走路径 B handoff；停止实现 |
| 5 | RED 非本步全库红 | 停当前 §9 步 |
| 6 | 为绿将 deferred 测改回静默成功 | 停止 |

### 1.6 原计划归并

| 来源 | 内容 |
|------|------|
| `B02_04` §5 | B02-SYNC-01..06 → §8 SYNC-BOOT..05 + 06A/B/C |
| `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §0.2 + §6 | SYNC-06 拆 06A/B/C → §9.6–9.8 |
| Playbook §8.4 | PASS 子 AC |
| ADR-001 | COMPLETED 在写提交后 — crash 恢复而非盲目同事务 |

---

## 2. 架构与设计

**2.1** 契约 YAML 分裂 `implemented_job_types` / `reserved_job_types`；runtime 模块常量 + orchestrator `run_*` 方法集 parity。

**2.2** Reserved：`DeferredJobTypeError`（或等价）含 `code=DEFERRED_JOB_TYPE`、`owner`、`phase`、`docs_anchor`（对齐 `D2-P1-1` / Round 3F `R3F-SH-*`）。

**2.3** 新增薄入口 `run_revision_audit` → deferred（`revision_audit` 无 runner）。

**2.4** Crash-window：`IncrementalJobRunner.run` 写事务提交后、COMPLETED 前注入 hook（测试用）；可选 `recover_stuck_writing_job(job_id)` 当 `status=WRITING` 且 `write_id` 非空时 transition COMPLETED（ponytail：单函数，无框架）。

**2.5** Registry：Execute 产出 `research/registry_proposed_delta.yaml`；主会话批闭合。

---

## 3. 需求与场景矩阵

| 场景# | Given | When | Then | AC | 测试 | Tier |
|-------|-------|------|------|-----|------|------|
| S1 | 契约已分裂 | 加载契约 + runtime 常量 | implemented 集合相等 | AC-SYNC-002 | parity | B |
| S2 | reserved job | 调用 `run_full_load` 等 | `DeferredJobTypeError` 含 code/owner | AC-SYNC-002 | deferred | B |
| S3 | incremental 成功写 | 注入 crash 在 COMPLETED 前 | job=WRITING 且 write_id 已设 | AC-SYNC-001 | crash | B |
| S4 | WRITING+write_id | 调用 recovery | status=COMPLETED；无重复写 | AC-SYNC-001 | recovery | B |

**3.1** 能做：矩阵、deferred、crash 检测/恢复。不能做：实现 reserved runners、改 write 模式、CLI 发布。

**3.2** in：`sync_job_contract.yaml`、`backend/app/sync/**`、相关 tests。out：WriteManager 模式契约、CLI、production write。

---

## 4. 预期结果（AC）

| ID | 预期 | 验证链 |
|----|------|--------|
| AC-SYNC-PLAN | `validate-plan-freeze` exit 0 | freeze |
| AC-SYNC-002 | 契约==runtime；reserved deferred | S1–S2 → §9.1–9.3 |
| AC-SYNC-001 | crash pytest **或** handoff 文件 | S3–S4 → §9.5–9.8 |
| AC-SYNC-REG | D2-P1-1 proposed delta | §9.4 |
| AC-SYNC-TEST | 五字段 + 语义断言 | §5 |
| AC-SYNC-PLAYBOOK | Playbook §8.4 命令绿 | §10 |
| AC-SYNC-CLOSE | VR-SYNC-002 关闭；VR-SYNC-001 二选一完成 | Audit A5 |

---

## 5. 测试契约

> **测试文件路径** · **测试目的** · **成功怎么测** · **失败怎么测** — 下表冻结；Execute 不得改 purpose。

### 5.0 规范

1. 五字段注释模板
2. 禁止裸 `NotImplementedError` 到达测试边界（除 RED 基线阶段）
3. 改 `test_advA3_016` 时保留「调用方不得误以为已实现」目的

### 5.1 测试文件路径

| 测试文件路径 | 测试目的 | 成功怎么测 | 失败怎么测 | §9 |
|--------------|----------|------------|------------|-----|
| `tests/test_sync_orchestrator.py` | 契约 parity；reserved deferred；crash/recovery | 集合相等；DeferredJobTypeError；WRITING+write_id；recovery→COMPLETED | 断言失败；NIE；过早 COMPLETED | 9.1–9.3, 9.5–9.8 |
| `tests/test_r3x_residual_open_items_closure.py` | advA3_016：调用方不得误以为 reserved 已实现 | `pytest.raises(DeferredJobTypeError)` | 仍断言 NIE 或静默返回 | 9.4 |
| `tests/test_write_manager.py` | WriteManager 回归（本任务不改写模式 purpose） | 既有用例 exit 0 | 回归红 | 9.0 green |

> 任务卡 runners 专用测试模块未入库 — **substitution**：上表 `test_sync_orchestrator.py`。

### 5.2 成功/失败语义

| 能力 | 成功 | 失败 | 场景 |
|------|------|------|------|
| Parity | 集合相等 | 断言不等 | S1 |
| Deferred | raises DeferredJobTypeError + code | NIE 或普通 Exception | S2 |
| Crash | WRITING + write_id | COMPLETED 过早 | S3 |
| Recovery | COMPLETED 且无二次 insert | 仍 WRITING | S4 |

### 5.3 用例设计

| 测试文件 | test_* | 断言语义 | 场景 | RED 命令 |
|----------|--------|----------|------|----------|
| `test_sync_orchestrator.py` | `test_syncJobContract_implementedTypes_matchRuntimeCallables` | YAML implemented == `IMPLEMENTED_JOB_TYPES` == run_* 集 | S1 | `pytest tests/test_sync_orchestrator.py::test_syncJobContract_implementedTypes_matchRuntimeCallables -v` |
| 同上 | `test_syncJob_reservedFullLoad_returnsDeferredJobTypeError` | code DEFERRED_JOB_TYPE；含 D2-P1-1 anchor | S2 | 同上前缀 |
| 同上 | `test_syncJob_reservedDataQuality_completesJob` | R3F-SH 后 implemented；job 可完成 | S2 | 同上 |
| 同上 | `test_syncJob_reservedRevisionAudit_completesJob` | 同上 | S2 | 同上 |
| 同上 | `test_syncJob_incremental_crashWindow_leavesWritingWithWriteId` | 注入 hook 抛错后 status=WRITING 且 write_id 非空 | S3 | 同上 |
| 同上 | `test_syncJob_incremental_recoverStuckWriting_completesWithoutDoubleWrite` | recovery 后 COMPLETED；clean 行数不变 | S4 | 同上 |
| `test_r3x_residual_open_items_closure.py` | `test_advA3_016_orchestratorDeferredRunners` | DeferredJobTypeError（非 NIE） | S2 | `pytest tests/test_r3x_residual_open_items_closure.py::test_advA3_016_orchestratorDeferredRunners -v` |

### 5.4 四层测试

| 层 | 命令 | 通过 |
|----|------|------|
| 单元 | `uv run pytest tests/test_sync_orchestrator.py tests/test_r3x_residual_open_items_closure.py::test_advA3_016_orchestratorDeferredRunners -q` | exit 0 |
| 集成 | `uv run pytest tests/test_write_manager.py -q` | exit 0 |
| 管道 | `uv run pytest -q` | exit 0 |
| E2E | N/A（无 CLI 发布） | — |

---

## 6. 验证

| Tier | 命令 | 场景 | 勾 |
|------|------|------|-----|
| A | Playbook §8.4 子集 | S1–S4 | [ ] |
| B | `uv run pytest -q` | 全库 | [ ] |
| C | `uv run ruff check backend/app/sync backend/app/db tests` | 静态 | [ ] |

**6.1 交接**：§9 证据齐；S3–S4 有对应用例 **或** `research/sync-001-handoff.md` 已填 owner/entrypoints/closure tests。

---

## 7. Red Flags

| 风险 | 预防 |
|------|------|
| 与 OPS 并发改 write 契约 | 只读 + 合并顺序 |
| 只关 matrix 不关 VR-SYNC-001 | §9.6–9.8 门控 |
| 隐藏 NIE | SYNC-03 专用异常 |

---

## 8. 实现顺序

| 序 | ID | 交付物 | 依赖 | AC |
|----|-----|--------|------|-----|
| 0 | SYNC-BOOT | RED 基线证据 | — | PLAN |
| 1 | SYNC-01 | 契约分裂 + loader/常量 | BOOT | 002 |
| 2 | SYNC-02 | parity 测试 GREEN | 01 | 002 |
| 3 | SYNC-03 | deferred API GREEN | 02 | 002 |
| 4 | SYNC-04 | advA3_016 + registry delta | 03 | REG |
| 5 | SYNC-05 | crash hook + 审查笔记 | 03 | 001 |
| 6 | SYNC-06A | 最小 recovery 实现 **或** handoff 草稿 | 05 | 001 |
| 7 | SYNC-06B | crash-window pytest WRITING→COMPLETED | 06A | 001 |
| 8 | SYNC-06C | VR-SYNC-001 关账 **或** handoff 定稿 | 06B 或 06A(B) | CLOSE |

---

## 9. 实现步骤

### 9.0 Boot

> 必读：**§0.3** + `research/integration-ledger.md` + 逐行 `implement.jsonl`（E4）。

| RED/GREEN | 证据 | Skill | [ ] |
|-----------|------|-------|-----|
| `uv run pytest tests/test_sync_orchestrator.py -q` | `9.0-red.txt` / `9.0-green.txt` | trellis-execute · impact | [ ] |

### 9.1 SYNC-01 — 契约分裂

| 字段 | 内容 |
|------|------|
| RED | `test_syncJobContract_implementedTypes_matchRuntimeCallables` FAIL |
| GREEN | 更新 `sync_job_contract.yaml`；`backend/app/sync/contract.py`（或内联常量，ponytail 最小） |
| 通过 | implemented=`incremental,backfill,reconcile`；reserved=`full_load,data_quality,revision_audit` |

### 9.2 SYNC-02 — Parity

| RED/GREEN | parity 测试 GREEN |
|-----------|-------------------|

### 9.3 SYNC-03 — Deferred

| RED/GREEN | 三 reserved 入口 deferred；`DeferredJobTypeError` 稳定字段 |
|-----------|-----------------------------------------------------------|

### 9.4 SYNC-04 — Registry / advA3_016

| 交付 | `research/registry_proposed_delta.yaml`；更新 `test_advA3_016` |
|------|----------------------------------------------------------------|

### 9.5 SYNC-05 — Crash hook

| 交付 | `IncrementalJobRunner` 可注入 `post_write_pre_complete_hook`（仅 PYTEST）；文档 ADR-001 窗口 |
|------|---------------------------------------------------------------------------------------------|

### 9.6 SYNC-06A — VR-SYNC-001 最小恢复实现

| 字段 | 内容 |
|------|------|
| 交付 | `recover_stuck_writing_job`（或等价）+ SYNC-05 hook 接线；**不改** `write_contract` / ADR / WriteManager 写模式语义 |
| 路径 B | 写 `research/sync-001-handoff.md` 草稿（不实现恢复）→ 06B **skip** |
| RED/GREEN | smoke 可调用恢复路径；证据 `9.6-red.txt` / `9.6-green.txt` |

### 9.7 SYNC-06B — crash-window pytest WRITING→COMPLETED

| 字段 | 内容 |
|------|------|
| RED | `test_syncJob_incremental_crashWindow_leavesWritingWithWriteId` FAIL |
| GREEN | `test_syncJob_incremental_recoverStuckWriting_completesWithoutDoubleWrite` GREEN |
| 证据 | `9.7-red.txt` / `9.7-green.txt`（retroactive：可与既有 `9.6-*` 同绿，见 `research/sync-06-split-alignment.md`） |
| 路径 B | **skip**（handoff 票代替关账路径） |

### 9.8 SYNC-06C — VR-SYNC-001 关账或 handoff 闭合

| 路径 A | `research/registry_proposed_delta.yaml` 完整 + 06B 绿 → 关闭 VR-SYNC-001（**主会话** registry 批闭合） |
|--------|-------------------------------------------------------------------------------------------------------------|
| 路径 B | `research/sync-001-handoff.md` 定稿（owner Round 3F · R3F-BR-03 · entrypoints · closure tests）→ VR-SYNC-001 精确 re-defer |
| 交付 | `repair-evidence/registry-ready.md` · `repair-evidence/sync-crash-window-runbook.md` |

---

## 10. Execute 交接 DoD

- [x] §9 证据齐 · §5.4+§6 · `validate-execute-handoff` 0 · VR-SYNC-002 关闭证据 · VR-SYNC-001 二选一（路径 A · §9.6–9.8）

---

## 11. Execute Skill 冻结

| Skill | 绑定 | [ ] |
|-------|------|-----|
| trellis-execute | Boot | [x] |
| test-driven-development | §9 RED | [x] |
| incremental-implementation | §8 SLICE | [x] |
| karpathy-guidelines | GREEN | [x] |
| testing-guidelines | 写测 | [x] |
| gitnexus-impact | 改 symbol 前 | [x] |
| trellis-check | **不用** → Audit A1 | — |

路径：`execute-skill-paths.yaml`。
