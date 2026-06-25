# MASTER 计划 — B3F-BR Backfill/Reconcile Parity

> **Execute 入口** — staged/sandbox only；**不得** production clean write。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`  
> **补冻结**：Execute 已交付 orchestrator registry + 2 测试文件；本 Plan 追溯 `R3F-BR-01..05` 与 Playbook §8.5。

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| 任务 slug | `round3f-backfill-reconcile-parity` |
| Playbook ID | B3F-BR · Manifest Batch 3F.4 |
| 分支 | `feature/round3-backfill-reconcile-parity` |
| Worktree | `../quant-monitor-desk-wt-b3f-br` |
| 模型 | `composer-2.5` |
| 前置 | B3V-SYNC deferred matrix + crash handoff |
| manifest_protocol_version | `3` |
| analysis_waiver | `false` |
| 原计划 | `research/source-index.md` · `research/original-plan-trace.md` |

### Batch 3F 边界（Playbook §2.5 / §3.6）

| Owns | Must not |
|------|----------|
| `backend/app/sync/orchestrator.py` handler registry | 重开 B3V crash-window 实现 |
| `tests/test_r3f_br_backfill_reconcile_closure.py` | production write |
| `tests/test_sync_runners.py` runner 接线 | 改 WriteManager 写模式 |
| R3-PARTIAL-4/5 关账链测试 | 无证据改 UNRESOLVED 为 RESOLVED |

### 0.1 Execute 必读

Phase 0 **逐条 Read `implement.jsonl`**（清单以文件为准）。动态闭包：`research/context-closure.md`（Execute 创建）。

### 0.3 Execute 强制必读 manifest（E4）

Boot 前 Read **`research/integration-ledger.md`**；Phase 0 **逐条 Read `implement.jsonl`**。

### Source Context Index（Playbook §3.1 + §3.6）

#### §3.1 共用底座

| 路径 | 摘要 | implement |
|------|------|-----------|
| `BATCH_3F_COORDINATOR_PLAYBOOK.md` | §3.6 路径 + §8.5 PASS | [x] |
| `BATCH_3F_TASK_CARD_MANIFEST.md` | B3F-BR ownership | [x] |
| `BATCH_3F_HARDENING_RULES.md` | 禁 production write | [x] |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3F.4 | R3F-BR-01..05 | [x] |
| `GLOBAL_EXECUTION_RULES.md` 等 ×3 | 全局纪律 | [x] |

#### §3.6 B3F-BR

| 路径 | 摘要 | implement |
|------|------|-----------|
| `backend/app/sync/orchestrator.py` · `runners.py` | handler registry + runner 接线 | [x] |
| `specs/contracts/sync_job_contract.yaml` | job 矩阵 SSOT | [x] |
| `016_implement_source_conflict_validator.md` | reconcile 邻接 | [x] |
| `docs/adr/ADR-023-layer5-conflict-review-path.md` | R3-PARTIAL-4 | [x] |
| `tests/test_sync_orchestrator.py` | backfill severeConflict 锚点 | [x] |
| `tests/test_audit_remediation.py` | reconcile re-fetch 锚点 | [x] |

---

## 1. 目标与约束

### 1.1 目标

关闭 `R3F-BR-01..05`：backfill/reconcile parity 叙事、handler registry、R3-PARTIAL-4/5 关账链；Playbook §8.5 验证绿。

### 1.3 约束

> **must read original**：`016_implement_source_conflict_validator.md`（reconcile 邻接，只读对照 BR-02）

- 无 production DB mutation；无 live fetch
- `R3-PARTIAL-5` **仅** regression guard（B3V 已闭合 crash-window）
- 主会话外不直接改 registry RESOLVED 行

### 1.5 停止条件

| # | 事件 | 处理 |
|---|------|------|
| 1 | Plan 未 freeze | 禁止 start |
| 2 | 触及 production clean write | 中止 |
| 3 | 重开 crash-window 实现代码 | 中止；退回 Plan |
| 4 | RED 非本步全库红 | 停当前 §9 步 |
| 5 | 改 `write_contract.yaml` 或 WriteManager 写模式 | 中止 |
| 6 | 无 ADR 链即声称 R3-PARTIAL-4 已 RESOLVED | 停止；仅 honest DEFERRED |

### 1.6 原计划归并

| 来源 | 内容 |
|------|------|
| `PROJECT_IMPLEMENTATION_ROADMAP.md` 3F.4 | R3F-BR-01..05 → §8 BR-01..05 |
| Playbook §3.6 | 路径索引 |
| Playbook §8.5 | PASS 子命令 → §10 |
| `016_implement_source_conflict_validator.md` | reconcile 邻接 → BR-02 |

---

## 2. 架构与设计

**2.1** `OrchestratorJobHandler` 冻结 job_type → entrypoint/kind/runner_attr 映射；`orchestrator_handler_registry()` 返回副本防变异。

**2.2** Closure 测试不重复实现业务 — 锚定既有 `test_sync_orchestrator` / `test_audit_remediation` + registry 文档链。

**2.3** `test_sync_runners.py` 验证 runner 实例接线与 backfill 分片上限。

---

## 3. 需求与场景矩阵

| 场景# | Given | When | Then | AC | 测试 | Tier |
|-------|-------|------|------|-----|------|------|
| S1 | registry 叙事 | 读 AUDIT_DEFERRED/UNRESOLVED | 无 skip-validator 声称 | AC-BR-01 | BR-01 | B |
| S2 | audit_remediation | 搜索 reconcile 族 | match/mismatch/fail 锚点存在 | AC-BR-02 | BR-02 | B |
| S3 | B3V 已闭合 | 读 UNRESOLVED | 无 R3-PARTIAL-5 DEFERRED 重开 | AC-BR-03 | BR-03 | B |
| S4 | contract 矩阵 | 读 handler registry | 覆盖 IMPLEMENTED+RESERVED | AC-BR-04 | BR-04 | B |
| S5 | ADR-023 | 读 ADR + UNRESOLVED | R3-PARTIAL-4 链 + Round4 defer | AC-BR-05 | BR-05 | B |

**3.1** 能做：parity 叙事、registry、关账链测试。不能做：crash-window 新实现、review UI、production write。

**3.2** in：orchestrator registry、closure tests、runners 接线。out：WriteManager、CLI 发布、registry 主会话批改。

---

## 4. 预期结果（AC）

| ID | 预期 | 验证链 |
|----|------|--------|
| AC-BR-PLAN | `validate-plan-freeze` exit 0 | freeze |
| AC-BR-01 | backfill 不跳过 validator 叙事 | S1 → §9.1 |
| AC-BR-02 | reconcile re-fetch pytest 锚点 | S2 → §9.2 |
| AC-BR-03 | R3-PARTIAL-5 regression guard | S3 → §9.3 |
| AC-BR-04 | handler registry 覆盖矩阵 | S4 → §9.4 |
| AC-BR-05 | ADR-023 + R3-PARTIAL-4 链 | S5 → §9.5 |
| AC-BR-PLAYBOOK | Playbook §8.5 命令绿 | §10 |
| AC-BR-TEST | 五字段 + 语义断言 | §5 |

---

## 5. 测试契约

> **测试文件路径** · **测试目的** · **成功怎么测** · **失败怎么测** — 下表冻结。

### 5.0 规范

1. 五字段注释模板
2. closure 测试锚定既有模块，不重复实现 runner 业务

### 5.1 测试文件路径

| 测试文件路径 | 测试目的 | 成功怎么测 | 失败怎么测 | §9 |
|--------------|----------|------------|------------|-----|
| `tests/test_r3f_br_backfill_reconcile_closure.py` | R3F-BR-01..05 closure guards | 五则 test_r3fBr* 全绿 | 叙事/registry 断言失败 | 9.1–9.5 |
| `tests/test_sync_runners.py` | runner 接线 + backfill 分片 | isinstance 接线正确；分片 ≤ ECO_MAX | AttributeError；分片过大 | 9.4 |
| `tests/test_sync_orchestrator.py` | backfill severeConflict（只读锚点） | 含 severeConflict 测试名 | 锚点缺失 | 9.1 |
| `tests/test_audit_remediation.py` | reconcile re-fetch（只读锚点） | 含 run_reconcile 族 | 锚点缺失 | 9.2 |

### 5.2 成功/失败语义

| 能力 | 成功 | 失败 | 场景 |
|------|------|------|------|
| Backfill parity | 无 skip-validator；有 severeConflict 测试 | 旧叙事残留 | S1 |
| Reconcile | re-fetch 三路径 token 存在 | token 缺失 | S2 |
| Partial-5 guard | 无 DEFERRED 重开行 | 重开 | S3 |
| Registry | 超集覆盖；runner_attr 可解析 | 缺 job 类型 | S4 |
| ADR chain | ADR-023 + UNRESOLVED 行一致 | 脱节 | S5 |

### 5.3 用例设计

| 测试文件 | test_* | 断言语义 | 场景 | RED 命令 |
|----------|--------|----------|------|----------|
| `test_r3f_br_backfill_reconcile_closure.py` | `test_r3fBr01_backfillParity_registryDocumentsValidateWritePath` | 无 skip-validator 叙事 | S1 | `uv run pytest tests/test_r3f_br_backfill_reconcile_closure.py::test_r3fBr01_backfillParity_registryDocumentsValidateWritePath -v` |
| 同上 | `test_r3fBr02_reconcileRefetch_testsExistInAuditRemediation` | reconcile token 存在 | S2 | 同上前缀 Br02 |
| 同上 | `test_r3fBr03_r3Partial5_regressionGuard_noReopenInUnresolved` | 无重开 DEFERRED | S3 | 同上前缀 Br03 |
| 同上 | `test_r3fBr04_orchestratorHandlerRegistry_coversContractMatrix` | registry 超集 | S4 | 同上前缀 Br04 |
| 同上 | `test_r3fBr05_r3Partial4_adr023LinksRegistryDeferredRow` | ADR-023 链 | S5 | 同上前缀 Br05 |
| `test_sync_runners.py` | `test_syncRunners_orchestratorWiresRunnerAttributes` | runner isinstance | S4 | `uv run pytest tests/test_sync_runners.py -v` |

### 5.4 四层测试

| 层 | 命令 | 通过 |
|----|------|------|
| 单元 | `uv run pytest tests/test_r3f_br_backfill_reconcile_closure.py tests/test_sync_runners.py -q` | exit 0 |
| 集成 | `uv run pytest tests/test_sync_orchestrator.py tests/test_audit_remediation.py -q` | exit 0 |
| 管道 | `uv run pytest -q` | exit 0 |
| E2E | N/A | — |

---

## 6. 验证

| Tier | 命令 | 场景 | 勾 |
|------|------|------|-----|
| A | Playbook §8.5 子集（含 closure） | S1–S5 | [x] |
| B | `uv run pytest -q` | 全库 | [x]¹ |
| C | `uv run ruff check backend/app/sync tests/test_r3f_br_backfill_reconcile_closure.py tests/test_sync_runners.py` | BR 触及面 | [x] |

¹ **Tier B 诚实勾选（Repair）：** 全库 pytest 在 master 基线存在既有失败（live_pilot/layer1 等，与 BR diff 无因果）；证据见 `execute-evidence/8.5-playbook-full-pytest-repair.txt`。BR 合并门禁以 Tier A 子集 42 tests 绿 + Tier C scoped ruff 为准。全库 `ruff check .` 见 `8.5-playbook-ruff-full.txt`（既有债务，非 BR 引入）。

**6.1 交接**：§9 证据齐；S1–S5 有对应用例；§8.5 子集（orchestrator + runners + closure）42 tests 绿。

---

## 7. Red Flags

| 风险 | 预防 |
|------|------|
| 重开 crash-window | BR-03 guard only |
| registry 无 ADR | BR-05 |
| handler 与 contract 漂移 | BR-04 超集断言 |

---

## 8. 实现顺序

| 序 | ID | 交付物（完标准） | 依赖 | AC |
|----|-----|------------------|------|-----|
| 0 | BR-BOOT | RED 基线证据 | — | PLAN |
| 1 | BR-01 | backfill parity closure GREEN | BOOT | AC-BR-01 |
| 2 | BR-02 | reconcile re-fetch closure GREEN | BOOT | AC-BR-02 |
| 3 | BR-03 | R3-PARTIAL-5 regression guard GREEN | BOOT | AC-BR-03 |
| 4 | BR-04 | handler registry + runners 接线 GREEN | BR-01 | AC-BR-04 |
| 5 | BR-05 | ADR-023 链 + Playbook §8.5 40 tests 绿 | BR-04 | AC-BR-05 |

---

## 9. 实现步骤

### 9.0 Boot

> 必读：**§0.3** + `research/integration-ledger.md` + 逐行 `implement.jsonl`。

| RED 命令 | GREEN 命令 | 证据 | 绑定 Execute Skill | 已执行 |
|----------|------------|------|-------------------|--------|
| `uv run pytest tests/test_r3f_br_backfill_reconcile_closure.py tests/test_sync_runners.py -q` | 同上 | `9.0-red.txt` / `9.0-green.txt` | trellis-execute · gitnexus-impact | [x] |

### 9.1 BR-01 — Backfill parity

| 字段 | 内容 |
|------|------|
| 切片 | BR-01（§8 序 1） |
| RED / GREEN | `uv run pytest tests/test_r3f_br_backfill_reconcile_closure.py::test_r3fBr01_backfillParity_registryDocumentsValidateWritePath -v` |
| 证据 | `9.1-red.txt` / `9.1-green.txt` |
| 绑定 Execute Skill | test-driven-development · karpathy-guidelines · testing-guidelines |
| 通过 | RED FAIL；GREEN 0；§5.2 S1 |
| 已执行 | [x] |

### 9.2 BR-02 — Reconcile re-fetch

| 字段 | 内容 |
|------|------|
| 切片 | BR-02 |
| RED / GREEN | `uv run pytest tests/test_r3f_br_backfill_reconcile_closure.py::test_r3fBr02_reconcileRefetch_testsExistInAuditRemediation -v` |
| 证据 | `9.2-red.txt` / `9.2-green.txt` |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 通过 | §5.2 S2 |
| 已执行 | [x] |

### 9.3 BR-03 — R3-PARTIAL-5 guard

| 字段 | 内容 |
|------|------|
| 切片 | BR-03 |
| RED / GREEN | `uv run pytest tests/test_r3f_br_backfill_reconcile_closure.py::test_r3fBr03_r3Partial5_regressionGuard_noReopenInUnresolved -v` |
| 证据 | `9.3-red.txt` / `9.3-green.txt` |
| 绑定 Execute Skill | test-driven-development |
| 通过 | §5.2 S3 |
| 已执行 | [x] |

### 9.4 BR-04 — Handler registry

| 字段 | 内容 |
|------|------|
| 切片 | BR-04 |
| RED / GREEN | `uv run pytest tests/test_r3f_br_backfill_reconcile_closure.py::test_r3fBr04_orchestratorHandlerRegistry_coversContractMatrix tests/test_sync_runners.py -v` |
| 证据 | `9.4-red.txt` / `9.4-green.txt` |
| 绑定 Execute Skill | test-driven-development · gitnexus-impact |
| 通过 | registry 超集 + runner 接线 |
| 已执行 | [x] |

### 9.5 BR-05 — ADR chain + §8.5

| 字段 | 内容 |
|------|------|
| 切片 | BR-05 · Playbook §8.5 |
| RED / GREEN | `uv run pytest tests/test_sync_orchestrator.py tests/test_sync_runners.py tests/test_r3f_br_backfill_reconcile_closure.py -q` |
| 证据 | `9.5-red.txt` / `9.5-green.txt` |
| 绑定 Execute Skill | incremental-implementation |
| 通过 | 40 tests 绿；scoped ruff 绿 |
| 已执行 | [x] |

---

## 10. Execute 交接 DoD

- [x] §9 证据齐 · §5.4+§6 证据 · `validate-execute-handoff` 0 · 未 finish-work

---

## 11. Execute Skill 冻结

| Skill | 本任务 | 绑定 | 已读 | 已执行 |
|-------|--------|------|------|--------|
| trellis-execute | 必做 | Boot | [x] | [x] |
| test-driven-development | 必做 | §9 RED | [x] | [x] |
| incremental-implementation | 必做 | §9 BR-05 | [x] | [x] |
| karpathy-guidelines | 必做 | GREEN | [x] | [x] |
| testing-guidelines | 必做 | 写测 | [x] | [x] |
| gitnexus-impact | 必做 | BR-04 | [x] | [x] |
| systematic-debugging | 条件 | DEBUG | [ ] | [ ] |
| trellis-implement | inline | Execute | [x] | [x] |
| trellis-check | **不用** | → Audit A1 | — | — |

路径见 `execute-skill-paths.yaml`。Audit → `AUDIT.plan.md`。
