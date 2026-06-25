# Batch 3V 主会话协调手册

> **性质：** 主会话（merge coordinator）操作剧本，**不替代**任务卡与 `BATCH_3V_TASK_CARD_MANIFEST.md` 中的 allowed/forbidden SSOT。  
> **适用：** Round 3V verified audit cleanup — 六路并行（四正式线 + 两精简线）。  
> **父路线图：** `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3V。  
> **批次入口：** `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md`。  
> **审计来源：** `quant_monitor_desk_verified_audit_report_2026-06-25_v3`。  
> **基线：** `master` 最新已合并状态（post Batch 01）；**本 playbook 须已提交后再开 worktree**。

---

## 0. 范围边界（必读）

| 包                  | 包含                           | 合并轨道           | 说明                                           |
| ------------------- | ------------------------------ | ------------------ | ---------------------------------------------- |
| **Batch 3V 协调包** | `B3V-C01`..`C06`（六张任务卡） | §7 **Track A + B** | manifest SSOT；关闭或精确 re-defer 本批 `VR-*` |
| **路由外**          | Round 3F / 4 / 5 的 `VR-*`     | 不在本包           | 只更新 routing note，不在本批实现              |

**并行开发：** 六路 Execute 可同时开工（§2.5 文件锁 + registry 主会话排队）。  
**合并开发：** 按 §7 顺序 FF merge 到 `integration/round3-batch3v`（建议）再合 `master`。

**共同边界：** 不 production clean write；不 live fetch；不声称 production-ready；不实现 Round 4/5 产品化项。

---

## 1. 这份文件是什么

`BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` 的 **Batch 3V 扩展版**。

| 角色         | 职责                                                                                   |
| ------------ | -------------------------------------------------------------------------------------- |
| **主会话**   | 开 worktree、派发 agent、锁定共享文件组、跑全量测试、§7 合并、**批处理 registry 闭合** |
| **子 agent** | **单一分支 + 单一核心文件组**；**模型固定 `composer-2.5`**（§2.3）                     |
| **权威边界** | 任务卡 + `BATCH_3V_TASK_CARD_MANIFEST.md` §3 + **本手册 §2.5 / §2.6**                  |
| **权威输入** | 任务卡 + **`docs/` + `specs/`** → **§3**                                               |

### 1.1 分支业务目的（人话）

| Playbook ID  | Manifest  | 分支                                           | 业务目的                                            |
| ------------ | --------- | ---------------------------------------------- | --------------------------------------------------- |
| **B3V-OPS**  | `B3V-C01` | `fix/round3v-contract-drift-write-modes`       | 文档说的和代码做的要对得上（db-inspect、写模式）    |
| **B3V-DATA** | `B3V-C02` | `fix/round3v-schema-hash-fail-closed`          | 数据格式不对必须拒绝，不能悄悄放过                  |
| **B3V-STOR** | `B3V-C03` | `fix/round3v-rawstore-atomic-write`            | 原始证据文件写到一半断电不能留烂尾                  |
| **B3V-SYNC** | `B3V-C04` | `fix/round3v-sync-support-matrix-recovery`     | 同步任务：已实现 vs 预留要说清楚                    |
| **B3V-REG**  | `B3V-C05` | `fix/round3v-registry-manifest-consistency`    | 迁移台账、README/MANIFEST 和真实文件树对齐          |
| **B3V-L5R**  | `B3V-C06` | `review/round3v-layer5-model-schema-reconcile` | 核对 Layer5/模型表：已修好就关账，没修好精确排到 3F |

---

## 2. 全局铁律

### 2.1 闭环原则

- **阻塞与非阻塞一律修完**，或主会话书面 **re-defer**（owner、phase、closure test）。
- **不得扩大范围**；`UNRESOLVED` / `RESOLVED` / `AUDIT_DEFERRED` 由主会话批处理，子 agent **禁止并发直接 commit 闭合**。
- **Batch 3V 硬停：** `BATCH_3V_HARDENING_RULES.md` §1–§7。

### 2.2 实现与测试（**MUST · 无例外**）

> **Skill 路径：** `karpathy-guidelines` · `testing-guidelines` · `test-driven-development`（见 `execute-skill-paths.yaml`）。  
> **中文五字段注释**不受 ponytail「少注释」约束；**测试与正式代码的实现风格**仍须 ponytail。

| 规则                    | 要求                                                                                                                                |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **karpathy-guidelines** | **所有**正式代码与测试代码：Execute **GREEN 前必读**；先理解再最小实现                                                              |
| **testing-guidelines**  | **所有**测试：语义断言、mock 边界、覆盖须够；**禁止**为过关而弱化断言或改测试目的                                                   |
| **TDD**                 | **正式代码**：先 RED（须 FAIL）→ Read karpathy + testing-guidelines → 再 GREEN；`execute-evidence/{step}-red.txt` / `-green.txt`    |
| **Ponytail**            | **`backend/`、`scripts/`、`tests/`** 全程遵守；最小 diff、无投机抽象、无新依赖（中文注释除外）                                      |
| **五字段注释**          | **每个** `test_*` 须有五字段 docstring — §2.2.1；缺一则 **BLOCKING**                                                                |
| **全量测试**            | 任意代码修复后 **`uv run pytest -q` 全绿**；仅跑子集不算 Done                                                                       |
| **测试目的不可削弱**    | 可改实现、可改断言细节；**不可**修改目的/目标使测试变弱或绕过业务保障                                                               |
| **查代码优先级**        | **GitNexus** 与 **codebase-memory MCP** **同级**：二者交叉核实；结论一致再改码；冲突须记录并主会话裁定；**禁止**跳过二者直接盲 grep |

#### 2.2.1 五字段 docstring（**每个 test\_\* 必填**）

| 字段          | 要求                   |
| ------------- | ---------------------- |
| **覆盖范围**  | 场景人话               |
| **测试对象**  | 符号/模块/路径         |
| **目的/目标** | 通俗中文               |
| **验证点**    | 具体断言               |
| **失败含义**  | 变红时业务失去什么保障 |

#### 2.2.2 测试 ponytail

先复用 `conftest.py` / `contract_gate_support.py`；最小 diff；无新依赖；不脆化；RED 后 GREEN 前瘦身 fixture。金样：`tests/test_layer3_snapshot_builder.py`。

### 2.3 Agent 模型

**全部 agent 使用 `composer-2.5`**；**禁止 `composer-2.5-fast`**；派发记录 `model=composer-2.5`。

### 2.4 工具与 Skill

| 时机              | 动作                                                                                                                                      |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Boot              | **`agent-toolchain.md`** + Trellis plan/execute skill；**Read `karpathy-guidelines` + `testing-guidelines`**                              |
| 查代码            | **GitNexus**（`query`/`context`/`impact`）与 **codebase-memory MCP** **同级交叉核实**；二者结论一致再改码；仅在前两者不足时用 grep 补盲区 |
| 编辑符号前        | GitNexus `impact()`；HIGH/CRITICAL 须警告并获主会话确认                                                                                   |
| RED 后 GREEN 前   | **必读** `karpathy-guidelines` + `testing-guidelines`                                                                                     |
| 提交前            | `detect_changes()`；`uv run pytest -q` 全绿；`loop_maintain.py`（`--fix` 若触达 docs/backend）                                            |
| Plan（正式线）    | `trellis-plan` + `complex-task-planning-protocol.md`                                                                                      |
| Plan（精简线）    | `DEBT.plan.md` / `research/worktree-slices.md` — Phase 8D · `.trellis/spec/guides/round3-repair-debt-worktree-plan.md` §8                 |
| Execute（正式线） | `trellis-execute` + 逐行 `implement.jsonl`                                                                                                |
| Done              | commit 规则 + 全量 pytest                                                                                                                 |
| 全部 Done         | §7 合并                                                                                                                                   |

### 2.5 核心文件锁（主会话强制执行）

| 核心文件组                                                                         | 独占写权限                | 其它分支                                       |
| ---------------------------------------------------------------------------------- | ------------------------- | ---------------------------------------------- |
| `specs/contracts/ops_db_inspect_contract.yaml` + `backend/app/ops/db_inspector.py` | **B3V-OPS**               | 只读                                           |
| `specs/contracts/write_contract.yaml` + `WriteManager` 写模式语义                  | **B3V-OPS**               | B3V-SYNC 只读（crash-window 不得改 mode 契约） |
| `backend/app/db/validation_gate.py` + adapter `schema_hash` 路径                   | **B3V-DATA**              | 只读                                           |
| `specs/contracts/data_adapter_contract.md`（schema_hash 段）                       | **B3V-DATA**              | 只读                                           |
| `backend/app/storage/raw_store.py` + `path_compat.py`                              | **B3V-STOR**              | 只读                                           |
| `specs/contracts/sync_job_contract.yaml` + `backend/app/sync/**`                   | **B3V-SYNC**              | 只读                                           |
| `docs/schema/MIGRATION_COVERAGE.md` + README/MANIFEST/registry 文档行              | **B3V-REG**               | 只读                                           |
| `backend/app/layer5_evidence/**`（runtime）                                        | **禁止 B3V-L5R 默认修改** | 核对分支只读；runtime 缺口 → 独立 follow-up    |
| Registry 三件套 / `UNRESOLVED` / `RESOLVED`                                        | **主会话**                | agent 仅 proposed delta                        |

### 2.6 Per-branch allowed / forbidden（SSOT 摘要）

> 完整以任务卡 §4 + manifest §3 为准；Execute 前须抄入 `MASTER`/`DEBT.plan` Boundary 表。

| ID           | Owns（可写）                                                          | Must not own                                                |
| ------------ | --------------------------------------------------------------------- | ----------------------------------------------------------- |
| **B3V-OPS**  | db-inspect 契约/漂移测试；write 模式 implemented/reserved             | `manual_patch` 等 reserved 模式实现；production clean write |
| **B3V-DATA** | schema_hash 契约、ValidationGate fail-closed、相关测试                | 全文件扫描；production clean write                          |
| **B3V-STOR** | RawStore 原子写、crash/idempotency 测试                               | FileRegistry 语义变更（除非测试证明必需）                   |
| **B3V-SYNC** | sync support matrix、deferred error、crash-window 测试或 3F.4 handoff | CLI 发布；裸 `NotImplementedError` 泄漏                     |
| **B3V-REG**  | migration 009 覆盖矩阵、manifest/doc/registry 对齐                    | 无证明重写 migration 009；伪造 FINAL_AUDIT_REPORT           |
| **B3V-L5R**  | 核对矩阵、registry/docs 更新、targeted pytest                         | 默认改 `layer5_evidence/**`；production-ready 声称          |

### 2.7 `/to-issues` 与切片证据

- **正式线：** Plan 冻结前 `/to-issues`；每切片 RED/GREEN + `execute-evidence`。
- **精简线：** `DEBT.plan.md` vertical slices 表（Source ID、AC、allowed、verification）。
- **不得**单块水平实现跨越多个 `VR-*` 而无切片边界。

---

## 3. 权威必读索引

### 3.0 六路分支一览

| Playbook ID | Manifest | 分支                                           | Worktree（建议）                    | Trellis task-dir（建议）                | 轨道      | 流水线 | 必读      |
| ----------- | -------- | ---------------------------------------------- | ----------------------------------- | --------------------------------------- | --------- | ------ | --------- |
| B3V-OPS     | C01      | `fix/round3v-contract-drift-write-modes`       | `../quant-monitor-desk-wt-b3v-ops`  | `round3v-contract-drift-write-modes`    | complex   | §4     | §3.1+§3.2 |
| B3V-DATA    | C02      | `fix/round3v-schema-hash-fail-closed`          | `../quant-monitor-desk-wt-b3v-data` | `round3v-schema-hash-fail-closed`       | complex   | §4     | §3.1+§3.3 |
| B3V-STOR    | C03      | `fix/round3v-rawstore-atomic-write`            | `../quant-monitor-desk-wt-b3v-stor` | `round3v-rawstore-atomic-write`         | complex   | §4     | §3.1+§3.4 |
| B3V-SYNC    | C04      | `fix/round3v-sync-support-matrix-recovery`     | `../quant-monitor-desk-wt-b3v-sync` | `round3v-sync-support-matrix-recovery`  | complex   | §4     | §3.1+§3.5 |
| B3V-REG     | C05      | `fix/round3v-registry-manifest-consistency`    | `../quant-monitor-desk-wt-b3v-reg`  | `round3v-registry-manifest-consistency` | debt-lite | §5.1   | §3.1+§3.6 |
| B3V-L5R     | C06      | `review/round3v-layer5-model-schema-reconcile` | `../quant-monitor-desk-wt-b3v-l5r`  | `round3v-layer5-model-schema-reconcile` | debt-lite | §5.2   | §3.1+§3.7 |

### 3.1 共用底座（每分支 Plan 前 Read + 摘要）

| 类别             | 路径                                                                                                                                                                        |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **协调**         | 本 playbook · `BATCH_3V_VERIFIED_AUDIT_CLEANUP/**` · 父 `../README.md`                                                                                                      |
| **协调**         | `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3V · `complex-task-planning-protocol.md` Phase 8D · **`agent-toolchain.md`** · `round3-repair-debt-worktree-plan.md`              |
| **审计**         | `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` · `BATCH_3V_HARDENING_RULES.md` · `BATCH_3V_ADVERSARIAL_AUDIT.md` · `BATCH_3V_SELF_CHECK.md` |
| **Coordination** | `docs/quality/coordination/BATCH_3V_COORDINATOR_PLAYBOOK_POINTER.md` · `BATCH_3V_ZERO_OPEN_CLOSURE_POLICY.md` · `BATCH_3V_PLAYBOOK_ADVERSARIAL_AUDIT.report.md`             |
| **Registry**     | `AUDIT_DEFERRED` / `UNRESOLVED` / `RESOLVED` · `UNRESOLVED_ITEM_TASK_COVERAGE.md`                                                                                           |
| **Handoff**      | `ROUND3_HANDOFF.md` · post Batch 01 checkpoint                                                                                                                              |
| **全局**         | `GLOBAL_EXECUTION_RULES.md` · `GLOBAL_TESTING_POLICY.md` · `GLOBAL_RESOURCE_LIMITS.md` · **`GLOBAL_TASK_TEMPLATE.md`**                                                      |
| **契约**         | `write_contract.yaml` · `runtime_versions.md` · `resource_limits.yaml`                                                                                                      |
| **架构**         | `MIGRATION_MAP.md` · `specs/context/authority_graph.yaml`                                                                                                                   |

### 3.2 B3V-OPS — Contract / Write Modes

**任务卡：** `B02_01_contract_drift_and_write_modes.md`

| 路径                                                                           | 用途                               |
| ------------------------------------------------------------------------------ | ---------------------------------- |
| `specs/contracts/ops_db_inspect_contract.yaml`                                 | db-inspect SSOT                    |
| `docs/modules/ops_db_inspect.md` · `docs/ops/db_inspect_cli.md`                | CLI/模块文档（漂移对照）           |
| `backend/app/ops/db_inspector.py`                                              | 运行时                             |
| `specs/contracts/write_contract.yaml`                                          | 写模式契约                         |
| `backend/app/db/write_manager.py`                                              | WriteManager                       |
| `tests/test_ops_db_inspector.py` · `test_write_manager.py`                     | 测试基线                           |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | `VR-OPS-001` / `VR-WRITE-001` 路由 |

### 3.3 B3V-DATA — Schema Hash Fail-closed

**任务卡：** `B02_02_schema_hash_fail_closed.md`

| 路径                                                                                                    | 用途                                 |
| ------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| `specs/contracts/data_adapter_contract.md`                                                              | 结构化 schema_hash 要求              |
| `backend/app/datasources/adapters/skeleton_base.py`                                                     | adapter 路径                         |
| `backend/app/db/validation_gate.py`                                                                     | fail-closed                          |
| `backend/app/datasources/adapters/registry.py`                                                          | adapter 注册（schema_hash 路径邻接） |
| `specs/contracts/data_quality_rules.yaml`                                                               | 质量规则                             |
| `tests/test_db_validation_gate.py` · `test_data_adapter_contract.py` · `test_data_quality_validator.py` | 测试基线                             |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md`                          | `VR-DATA-001` 路由                   |

### 3.4 B3V-STOR — RawStore Atomic Write

**任务卡：** `B02_03_rawstore_atomic_write.md`

| 路径                                                                           | 用途                   |
| ------------------------------------------------------------------------------ | ---------------------- |
| `backend/app/storage/raw_store.py`                                             | **独占**               |
| `backend/app/storage/path_compat.py`                                           | 路径辅助               |
| `specs/contracts/snapshot_lineage_contract.yaml`                               | 证据链邻接（只读对照） |
| `tests/test_raw_store.py`                                                      | 测试基线               |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | `VR-STOR-001` 路由     |

### 3.5 B3V-SYNC — Sync Support Matrix

**任务卡：** `B02_04_sync_job_support_and_recovery.md`

| 路径                                                                           | 用途                               |
| ------------------------------------------------------------------------------ | ---------------------------------- |
| `specs/contracts/sync_job_contract.yaml`                                       | implemented vs reserved            |
| `backend/app/sync/orchestrator.py` · `runners.py`                              | 运行时                             |
| `docs/modules/sync_jobs.md`                                                    | support matrix 文档锚点            |
| `backend/app/db/write_manager.py`                                              | crash-window（只读协调 B3V-OPS）   |
| `tests/test_sync_orchestrator.py` · `test_sync_runners.py`                     | 测试基线                           |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | `VR-SYNC-001` / `VR-SYNC-002` 路由 |

### 3.6 B3V-REG — Registry / Manifest

**任务卡：** `B02_05_migration_registry_and_manifest_consistency.md`

| 路径                                                                           | 用途                             |
| ------------------------------------------------------------------------------ | -------------------------------- |
| `backend/app/db/migrations/009_status_check_constraints.sql`                   | migration 009                    |
| `docs/schema/MIGRATION_COVERAGE.md`                                            | 覆盖文档                         |
| `README.md` · `MANIFEST.json` · `docs/quality/final_package_rules.md`          | 文档一致性                       |
| `scripts/check_manifest_files.py` · `tests/test_manifest_files_check.py`       | manifest 存在性（**须 TDD**）    |
| `tests/test_unresolved_item_task_coverage.py`                                  | registry 测试                    |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | `VR-REG-001` / `VR-DOC-001` 路由 |

### 3.7 B3V-L5R — Layer5 / Model Reconcile

**任务卡：** `B03_01_layer5_model_schema_reconcile.md`

| 路径                                                                            | 用途                              |
| ------------------------------------------------------------------------------- | --------------------------------- |
| `023_implement_layer5_evidence_chain.md` · `023A_layer5_evidence_foundation.md` | 023 权威（只读对照）              |
| `docs/modules/layer5_evidence_chain.md`                                         | Layer5 模块文档                   |
| `backend/app/layer5_evidence/`                                                  | **默认只读**                      |
| `tests/test_layer5_evidence_chain.py` · `test_migration_coverage.py`            | **强制** targeted pytest          |
| `specs/schema/schema.sql` · `docs/schema/MIGRATION_COVERAGE.md`                 | 表状态矩阵                        |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md`  | `VR-L5-001` / `VR-MODEL-001` 路由 |

### 3.8 Plan 质检 checklist（复杂任务 Agent-2）

- [ ] §3.1 + 分支 §3.x **每一行** 已入 `MASTER`/`implement.jsonl` 或 `DEBT.plan` 无损摘要
- [ ] `authority_graph.yaml` 模块已核对
- [ ] `GLOBAL_TASK_TEMPLATE.md` **15 节**与任务卡 Red Flags 已覆盖
- [ ] `BATCH_3V_HARDENING_RULES.md` §3–§7、§2.5/§2.6 边界已写入
- [ ] 任务卡 §必读 与 PROMPT §5（若有）**无缺口**
- [ ] `/to-issues` 或 debt slices 表已冻结
- [ ] 每个 owned `VR-*` 有 closure test 或 re-defer 路径
- [ ] `uv run python scripts/check_docs_specs_indexed.py` **exit 0**（规划门禁）
- [ ] `BATCH_3V_SELF_CHECK.md` verdict **PASS_FOR_DISPATCH**（见该文件 §9）
- [ ] 遗漏项已写回 MASTER/DEBT 并修复，**复检零遗留**

### 3.9 Plan 追溯规则（复杂任务 Agent-2 · debt-lite Plan质检 同用）

| 规则         | 要求                                                                           |
| ------------ | ------------------------------------------------------------------------------ |
| **索引行**   | §3.x 表格每一路径须在 `MASTER`/`implement.jsonl` 或 `DEBT.plan` §必读 有对应行 |
| **VR 追溯**  | 每个 owned `VR-*` 须在 Plan 有 Source ID → AC → verification 三联              |
| **负向边界** | Plan Boundary 表须抄 §2.6 **Must not own** + 本节 §8.x **未改什么**            |
| **切片垂直** | 每 `/to-issues` 或 debt slice **仅一个** `VR-*` 或一个可测子 AC；禁止水平合并  |
| **证据路径** | RED/GREEN 或 reconcile 矩阵须预定 `execute-evidence/` 或 `research/` 落盘路径  |
| **复检**     | Plan质检 agent 须输出 §3.10 表且 **遗漏风险列全为「无」或已修复**              |

### 3.10 Plan 质检输出格式（Agent-2 必填）

| 路径 | 已入 MASTER/implement 或 DEBT.plan | 摘要一句 | 遗漏风险 |
| ---- | ---------------------------------- | -------- | -------- |

---

## 4. 轨道 A — 四条正式线（complex）

**适用：** B3V-OPS、B3V-DATA、B3V-STOR、B3V-SYNC。

### 4.1 Agent 流水线

```
Plan → Plan质检 → Execute → Audit(A1–A8) → Repair → 对抗性审计 → 主会话提交
```

| 步骤       | Agent          | 产出与门禁                                                         |
| ---------- | -------------- | ------------------------------------------------------------------ |
| 1 Plan     | `composer-2.5` | `MASTER.plan.md`、`implement.jsonl`、`validate-plan-freeze` exit 0 |
| 2 Plan质检 | `composer-2.5` | §3.9/§3.10 零遗留                                                  |
| 3 Execute  | `composer-2.5` | TDD §8.x；RED/GREEN 证据；`validate-execute-handoff`               |
| 4 Audit ×8 | `composer-2.5` | `audit-skill-paths.yaml` 路由                                      |
| 5 Repair   | `composer-2.5` | 阻塞+非阻塞全修                                                    |
| 6 对抗性   | `composer-2.5` | `agents/audit-adversarial-authority.md`                            |
| 7 主会话   | —              | §6 + §8.x PASS + commit                                            |

### 4.2 Audit 派发（一维一 agent）

| 维  | 模板                                                                                    |
| --- | --------------------------------------------------------------------------------------- |
| A1  | `agents/audit-a1-spec.md`                                                               |
| A2  | `agents/audit-a2-ponytail.md`                                                           |
| A3  | `agents/security-auditor.md` + `sql-pro.md`                                             |
| A4  | `agents/code-reviewer.md`                                                               |
| A5  | `agents/audit-a5-completion.md` + `quant-analyst.md` + `risk-manager.md`                |
| A6  | `agents/performance-engineer.md`（SKIP 须记录）                                         |
| A7  | `agents/database-administrator.md` + `sre-engineer.md` + `devops-incident-responder.md` |
| A8  | `agents/qa-expert.md` + `test-automator.md`                                             |

路由：`.trellis/spec/guides/audit-skill-paths.yaml`。

### 4.3 正式线 Audit 单队列

- Execute 可并行；**Audit→Repair→对抗性→提交** 同一时刻 **仅一条正式线**。
- 建议 Audit 顺序（完成先后）：**OPS → DATA → STOR → SYNC**。

### 4.4 正式线派发清单

| #    | 角色     | Prompt 要点                                             |
| ---- | -------- | ------------------------------------------------------- |
| 1    | Plan     | 任务卡 + `trellis-plan` + §3 + hardening + `/to-issues` |
| 2    | Plan质检 | §3.9–§3.10 + §2.5/§2.6 + 零遗留                         |
| 3    | Execute  | `implement.jsonl` 逐行 + TDD + impact                   |
| 4a–h | A1–A8    | `agents/` 全文 + diff + AC                              |
| 5    | Repair   | 全 findings 修复 + pytest                               |
| 6    | 对抗性   | `audit-adversarial-authority.md`                        |
| 7    | 主会话   | §6 + §8 + commit                                        |

---

## 5. 轨道 B — 两条精简线（debt-lite）

### 5.1 B3V-REG

```
轻量Plan → Plan质检 → 编写/修复 → 对抗性审计 → 主会话
```

| 步骤      | 要求                                                                                                             |
| --------- | ---------------------------------------------------------------------------------------------------------------- |
| 轻量 Plan | `DEBT.plan.md`；allowed §2.6；**切片表每行一个 `VR-*`**                                                          |
| Plan质检  | §3.6 全文索引；manifest C05；§3.9 追溯                                                                           |
| 编写      | registry/docs/manifest 对齐；**`check_manifest_files` 须 TDD**（`tests/test_manifest_files_check.py` RED→GREEN） |
| 对抗性    | `audit-adversarial-authority.md`                                                                                 |
| 主会话    | §6 + §8.5                                                                                                        |

### 5.2 B3V-L5R

```
轻量Plan → Plan质检 → 核对/补证据 → 对抗性 → 主会话
```

| 步骤     | 要求                                                                                                                                |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Plan     | 映射 `VR-L5-001` / `VR-MODEL-001`；reconcile-first；**每 VR 独立切片 + 证据文件**                                                   |
| Plan质检 | §3.7 全文；§3.9；禁止水平关账                                                                                                       |
| 核对     | post Batch 01 master；矩阵落盘 `research/l5-reconcile-matrix.md`；**强制** `test_layer5_evidence_chain` + `test_migration_coverage` |
| 禁止     | 默认改 `layer5_evidence/**`；无 targeted pytest 的 stale close；production-ready 声称                                               |
| 主会话   | §6 + §8.6                                                                                                                           |

### 5.3 精简线派发表

| 分支 | 1        | 2        | 3    | 4      | 5      |
| ---- | -------- | -------- | ---- | ------ | ------ |
| REG  | 轻量Plan | Plan质检 | 编写 | 对抗性 | 主会话 |
| L5R  | 轻量Plan | Plan质检 | 核对 | 对抗性 | 主会话 |

---

## 6. 单分支 Done — 主会话验收

- [ ] 任务卡 §8 + playbook §8.x 验收命令全绿
- [ ] `uv run pytest -q` 全绿
- [ ] `loop_maintain.py`（需时 `--fix`）
- [ ] `detect_changes()`；符合 §2.5/§2.6
- [ ] 测试五字段 + ponytail
- [ ] Trellis 证据（complex：`validate-execute-handoff`；debt：merge gate）
- [ ] **无 production DB 写入** / **无 live fetch**
- [ ] 分支 worktree commit
- [ ] **Closure report 九项**（父 README §5）

---

## 7. 全部 Done — 合并

### 7.1 推荐：integration 预合并

```bash
git checkout master && git pull
git checkout -b integration/round3-batch3v
# 按 §7.2 顺序 merge 各分支
uv run pytest -q
uv run python scripts/loop_maintain.py --fix
# FF merge integration/round3-batch3v → master
```

### 7.2 合并顺序

| 序  | ID       | 分支                                           | 前提                   |
| --- | -------- | ---------------------------------------------- | ---------------------- |
| 1   | B3V-REG  | `fix/round3v-registry-manifest-consistency`    | —                      |
| 2   | B3V-L5R  | `review/round3v-layer5-model-schema-reconcile` | 可与 1 交换            |
| 3   | B3V-OPS  | `fix/round3v-contract-drift-write-modes`       | —                      |
| 4   | B3V-DATA | `fix/round3v-schema-hash-fail-closed`          | —                      |
| 5   | B3V-STOR | `fix/round3v-rawstore-atomic-write`            | —                      |
| 6   | B3V-SYNC | `fix/round3v-sync-support-matrix-recovery`     | B3V-OPS 已合并（推荐） |

### 7.3 合并后主会话（一次协调提交）

1. 批处理 **owned `VR-*`** → RESOLVED 或 precise re-defer（manifest §4）
2. 更新 **`docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`**
3. 全量 pytest + `loop_maintain --fix`
4. 更新 `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3V checkpoint、`ROUND3_HANDOFF.md`
5. GitNexus `node .gitnexus/run.cjs analyze`（勿覆盖 `AGENTS.md` 定制段）
6. 更新 `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md` §8

---

## 8. 各分支 PASS 条件与验收命令

> §6 + 本节**同时满足**方可 Done。

### 8.1 B3V-OPS

```bash
uv sync --locked
uv run pytest tests/test_ops_db_inspector.py -q
uv run pytest tests/test_write_manager.py tests/test_db_validation_gate.py -q
uv run ruff check backend/app/ops backend/app/db tests
uv run pytest -q && uv run ruff check .
```

| 维度   | PASS                                                |
| ------ | --------------------------------------------------- |
| 契约   | db-inspect YAML 与 runtime 漂移可测                 |
| 写模式 | `implemented_modes == WriteManager.SUPPORTED_MODES` |
| 关闭   | `VR-OPS-001`、`VR-WRITE-001` 有证据或 re-defer      |

**未改什么（负向边界）：** `validation_gate.py`、RawStore、sync runners、migration 009、registry 三件套、`layer5_evidence/**`。

### 8.2 B3V-DATA

```bash
uv sync --locked
uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py -q
uv run pytest tests/test_data_quality_validator.py -q
uv run ruff check backend/app/datasources backend/app/db tests
uv run pytest -q && uv run ruff check .
```

| 维度        | PASS                              |
| ----------- | --------------------------------- |
| fail-closed | 缺 schema_hash 的结构化结果被拒绝 |
| 关闭        | `VR-DATA-001` 有证据或 re-defer   |

**未改什么：** db-inspect 契约、WriteManager 模式表、RawStore、sync 矩阵、registry 行、Layer5 runtime。

### 8.3 B3V-STOR

```bash
uv sync --locked
uv run pytest tests/test_raw_store.py -q
uv run ruff check backend/app/storage tests/test_raw_store.py
uv run pytest -q && uv run ruff check .
```

| 维度   | PASS                            |
| ------ | ------------------------------- |
| 原子性 | 写失败无半拉子目标文件          |
| 关闭   | `VR-STOR-001` 有证据或 re-defer |

**未改什么：** ValidationGate fail-closed 语义、sync/orchestrator、write 模式、migration/registry。

### 8.4 B3V-SYNC

```bash
uv sync --locked
uv run pytest tests/test_sync_orchestrator.py tests/test_sync_runners.py -q
uv run pytest tests/test_write_manager.py -q
uv run ruff check backend/app/sync backend/app/db tests
uv run pytest -q && uv run ruff check .
```

| 维度         | PASS                                                                                                               |
| ------------ | ------------------------------------------------------------------------------------------------------------------ |
| 矩阵         | implemented/reserved 与 runtime 一致                                                                               |
| 错误         | reserved 返回稳定 deferred，非裸 `NotImplementedError`                                                             |
| crash-window | **`VR-SYNC-001` 关闭须** crash-window **pytest** 或书面 **3F.4 handoff**（owner、entrypoints、closure tests 路径） |
| 关闭         | `VR-SYNC-002` 须有关闭证据；`VR-SYNC-001` 仅允许上列二选一                                                         |

**未改什么：** write 模式契约（B3V-OPS 独占）、schema_hash、RawStore、registry 批闭合、Layer5。

### 8.5 B3V-REG

```bash
uv sync --locked
uv run pytest tests/test_unresolved_item_task_coverage.py tests/test_manifest_files_check.py -q
uv run python scripts/check_docs_specs_indexed.py
uv run python scripts/check_manifest_files.py
uv run pytest -q
```

| 维度                   | PASS                                                                                                          |
| ---------------------- | ------------------------------------------------------------------------------------------------------------- |
| 文档                   | README/MANIFEST/allowlist 与文件树一致                                                                        |
| manifest TDD           | `tests/test_manifest_files_check.py` 绿；禁止无测试的 manifest 行编辑                                         |
| 关闭                   | `VR-REG-001`、`VR-DOC-001`                                                                                    |
| manifest **Done 门禁** | `check_manifest_files.py` **exit 0**（restore-or-replace `FINAL_AUDIT_REPORT.md` 或更新 MANIFEST 移除幽灵行） |
| manifest **规划期**    | 允许 `FINAL_AUDIT_REPORT.md` missing **仅当** `DEBT.plan` 记录 restore-or-replace 切片与 owner                |

**未改什么：** `validation_gate`、RawStore、sync runtime、`layer5_evidence/**`、production DB。

### 8.6 B3V-L5R

```bash
uv sync --locked
uv run pytest tests/test_layer5_evidence_chain.py -q
uv run pytest tests/test_migration_coverage.py -q
uv run python scripts/check_docs_specs_indexed.py
```

| 维度         | PASS                                                                                               |
| ------------ | -------------------------------------------------------------------------------------------------- |
| 核对         | L3/L4/L5 designed/implemented/deferred 矩阵落盘 `research/l5-reconcile-matrix.md`                  |
| pytest       | **`test_layer5_evidence_chain` + `test_migration_coverage` 必须绿**（禁止仅只读 report 关 `VR-*`） |
| 关闭         | `VR-L5-001`、`VR-MODEL-001` 各须独立证据；stale 须指 post-B01 commit + 测试指针                    |
| runtime 缺口 | **新分支** follow-up；本分支 **未改** `layer5_evidence/**`                                         |
| 禁止         | 无 production-ready 声称                                                                           |

**未改什么：** sync/write/validation/rawstore runtime、migration 009 语义、主会话 registry 直接 commit。

### 8.7 口诀

| 类型   | Done 当且仅当                        |
| ------ | ------------------------------------ |
| 正式线 | §6 + §8.1–§8.4 + 已提交              |
| 精简线 | §6 + §8.5–§8.6 + 对抗性闭环 + 已提交 |

---

## 9. 开波检查清单

- [ ] 本 playbook + `BATCH_3V_HARDENING_RULES.md` + manifest + **SELF_CHECK + ADVERSARIAL_AUDIT** 已提交
- [ ] 已读 `docs/quality/coordination/BATCH_3V_ZERO_OPEN_CLOSURE_POLICY.md`
- [ ] 已读父 README · **`agent-toolchain.md`**
- [ ] 六分支 owner、worktree、§2.5 锁已登记
- [ ] **确认无 live fetch 授权需求**（本批禁止）
- [ ] `composer-2.5 only`；registry **仅主会话批处理**
- [ ] integration 分支策略已选（§7.1）

### 9.1 Worktree 创建模板

```bash
cd C:/Users/Guang/Desktop/quant-monitor-desk
git fetch origin
git worktree add -b fix/round3v-registry-manifest-consistency ../quant-monitor-desk-wt-b3v-reg master
git worktree add -b review/round3v-layer5-model-schema-reconcile ../quant-monitor-desk-wt-b3v-l5r master
git worktree add -b fix/round3v-contract-drift-write-modes ../quant-monitor-desk-wt-b3v-ops master
git worktree add -b fix/round3v-schema-hash-fail-closed ../quant-monitor-desk-wt-b3v-data master
git worktree add -b fix/round3v-rawstore-atomic-write ../quant-monitor-desk-wt-b3v-stor master
git worktree add -b fix/round3v-sync-support-matrix-recovery ../quant-monitor-desk-wt-b3v-sync master
```

每 worktree 内首次验证：

```bash
uv sync --locked
uv run pytest -q --tb=no -x
```

---

## 10. 快速对照

| 原意              | 章节 |
| ----------------- | ---- |
| 正式复杂流程      | §4   |
| debt-lite         | §5   |
| 六路文件锁        | §2.5 |
| allowed/forbidden | §2.6 |
| `/to-issues`      | §2.7 |
| 合并顺序          | §7   |
| closure 九项      | §6   |

---

## 11. Playbook 对抗性审计修复闭环

| 处置                    | 章节                                                                           |
| ----------------------- | ------------------------------------------------------------------------------ |
| 禁止 fast 模型          | §2.3                                                                           |
| Plan 质检输出表         | §3.10                                                                          |
| A1–A8 模板              | §4.2                                                                           |
| 六分支策略              | §3.0、manifest §3                                                              |
| check_manifest_files    | §8.5、`scripts/check_manifest_files.py`                                        |
| verified audit INDEX    | `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` |
| SELF_CHECK / card audit | 批次包内两文件                                                                 |
| ZERO_OPEN               | `docs/quality/coordination/BATCH_3V_ZERO_OPEN_CLOSURE_POLICY.md`               |
| coordination pointer    | `BATCH_3V_COORDINATOR_PLAYBOOK_POINTER.md`                                     |
| GitNexus merge          | §7.3                                                                           |
| 对抗性审计原文          | `docs/quality/coordination/BATCH_3V_PLAYBOOK_ADVERSARIAL_AUDIT.report.md`      |

---

_文档版本：2026-06-25 rev.2 · 对抗性审计 hardened · 模板来源 `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`_
