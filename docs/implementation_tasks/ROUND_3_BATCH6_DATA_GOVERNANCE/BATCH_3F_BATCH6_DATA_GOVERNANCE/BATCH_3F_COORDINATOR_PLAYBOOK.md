# Batch 3F 主会话协调手册

> **性质：** 主会话（merge coordinator）操作剧本，**不替代** `BATCH_3F_TASK_CARD_MANIFEST.md`、`PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3F 中的 allowed/forbidden SSOT。  
> **适用：** Round 3F / Batch6 Data Governance — **八路并行（六复杂 + 两精简）**。  
> **父路线图：** `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3F。  
> **批次入口：** `BATCH_3F_BATCH6_DATA_GOVERNANCE/README.md`。  
> **对抗性审计：** `BATCH_3F_PLAYBOOK_ADVERSARIAL_AUDIT.report.md`（修补闭环见 **§11**）。  
> **基线：** `master` @ post-Batch 3V（`2aeb6f0` 或更新）；**本 playbook 须已提交后再开 worktree**。

---

## 0. 范围边界（必读）

| 包                  | 包含                                                                     | 合并轨道       | 说明                                                        |
| ------------------- | ------------------------------------------------------------------------ | -------------- | ----------------------------------------------------------- |
| **Batch 3F 协调包** | `B3F-LIN`、`B3F-MIG`、`B3F-CLI`、`B3F-SH`、`B3F-BR`、`B3F-HYG`（六复杂） | §7 **Track A** | 运行时 / migration / CLI / pipeline / hygiene 实现          |
| **Batch 3F 精简包** | `B3F-REG`、`B3F-CI`（两精简）                                            | §7 **Track B** | registry/docs/CI 对齐；**不得**默认改 `backend/` 业务主路径 |
| **路由外**          | Round 3G clean write、Round 4 API/FE、Round 5 release gate               | 不在本包       | 只更新 routing note，不在本批实现                           |

**并行开发：** 八路 Execute 可同时开工（§2.5 文件锁 + registry 主会话排队）。  
**合并开发：** 建议 `integration/round3-batch3f` 预合并后 FF 入 `master`（§7.1）。

**共同边界：** 不 production clean write；不声称 production-live；不默认启用 FRED/TDX/QMT/xqshare/Yahoo；不全市场/全历史默认扫描。

**3D.3 误读防护：** Batch 01 `B01-LIN` 仅完成 **partial hygiene**；`ADV-R3X-LINEAGE-001`、`R3Y-LINEAGE-VR-001`、`R3-B6-021-O-01/02` 的 **registry 全闭合** 归 **B3F-LIN**，不得因 3D.3 已合并而跳过。

---

## 1. 这份文件是什么

`BATCH_3V_COORDINATOR_PLAYBOOK.md` 的 **Batch 3F 扩展版**（规模更大：六复杂 + 两精简 + migration/lineage 串行锁）。

| 角色         | 职责                                                                                              |
| ------------ | ------------------------------------------------------------------------------------------------- |
| **主会话**   | 开 worktree、派发 agent、§2.5 文件锁、全量 pytest、§7 合并、**批处理 registry 三件套 + COVERAGE** |
| **子 agent** | **单一分支 + 单一核心文件组**；**模型固定 `composer-2.5`**（§2.3）                                |
| **权威边界** | manifest + roadmap Round 3F + **本手册 §2.5 / §2.6**                                              |
| **权威输入** | manifest + `**docs/` + `specs/`** → **§3\*\*（不得只读 manifest）                                 |

### 1.1 八路分支业务目的（人话）

| Playbook ID | 轨道          | 分支                                                 | 业务目的（人话）                                           |
| ----------- | ------------- | ---------------------------------------------------- | ---------------------------------------------------------- |
| **B3F-LIN** | **complex**   | `fix/round3f-batch6-lineage-layer3-registry-closure` | 把 3D.3 没关干净的「血缘 + Layer3 卫生」在 registry 上关账 |
| **B3F-MIG** | **complex**   | `feature/round3f-migration-residual-checks`          | 数据库迁移残余、CHECK、列生命周期（009 残余 + 008 路由）   |
| **B3F-CLI** | **complex**   | `feature/round3-qmd-data-cli`                        | 统一运维入口：`qmd data`、打包脚本、init 一键化            |
| **B3F-SH**  | **complex**   | `feature/round3-source-health-and-quality-runners`   | 数据健康快照表、质量任务 runner、FRED live 关闭路径跟踪    |
| **B3F-BR**  | **complex**   | `feature/round3-backfill-reconcile-parity`           | 回填/对账与 orchestrator 行为一致，不绕过校验              |
| **B3F-HYG** | **complex**   | `chore/round3-batch6-technical-debt`                 | 代码卫生、性能预算、ingestion 拆分、ResourceGuard          |
| **B3F-REG** | **debt-lite** | `chore/round3f-registry-batch-closeout`              | 三份 registry + COVERAGE 收口；已 RESOLVED 项只核对不重做  |
| **B3F-CI**  | **debt-lite** | `chore/round3-ci-gate-hardening`                     | CI / verification 命令矩阵；PROMPT_05 handoff              |

**轨道统计：** **6 条复杂任务分支** + **2 条精简分支** = **8 路并行**。

---

## 2. 全局铁律

### 2.1 闭环原则

- **阻塞与非阻塞一律修完**，或主会话书面 **re-defer**（owner、phase、closure test）。
- **不得扩大范围**；registry 三件套 + `**UNRESOLVED_ITEM_TASK_COVERAGE.md`** 由主会话批处理；**B3F-REG** 可拟 proposed delta，**禁止\*\*八路 agent 并发直接 commit 闭合 RESOLVED。
- **Batch 3F 硬停：** `BATCH_3F_HARDENING_RULES.md` §1–§6；冲突取更严规则。
- **已 RESOLVED 不重开：** `R3-PARTIAL-5`、`R2-RISK-3`、`R3-AUDIT-DEF-03` — 仅 regression 或 registry 对齐（§5.1）。

### 2.2 实现与测试（**MUST · 无例外**）

| 规则                    | 要求                                                                                                                             |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **karpathy-guidelines** | **所有**正式代码与测试：Execute **GREEN 前必读**                                                                                 |
| **testing-guidelines**  | 语义断言；**禁止**为过关削弱测试目的                                                                                             |
| **TDD**                 | **复杂线正式代码**：RED（须 FAIL）→ Read karpathy + testing-guidelines → GREEN；`execute-evidence/{step}-red.txt` / `-green.txt` |
| **Ponytail**            | `backend/`、`scripts/`、`tests/` 全程遵守（中文注释除外）                                                                        |
| **五字段注释**          | **每个** `test_*` 须五字段 docstring — §2.2.1；缺一则 **BLOCKING**                                                               |
| **全量测试**            | 修复后 `**uv run pytest -q` 全绿\*\*                                                                                             |
| **查代码优先级**        | **GitNexus** 与 **codebase-memory MCP** **同级交叉核实**；禁止跳过二者直接盲改                                                   |

#### 2.2.1 五字段 docstring

| 字段          | 要求      |
| ------------- | --------- |
| **覆盖范围**  | 场景人话  |
| **测试对象**  | 符号/路径 |
| **目的/目标** | 通俗中文  |
| **验证点**    | 具体断言  |
| **失败含义**  | 业务保障  |

#### 2.2.2 测试 ponytail

先复用 `conftest.py` / `contract_gate_support.py`；最小 diff；无新依赖；金样：`tests/test_layer3_snapshot_builder.py`。

### 2.3 Agent 模型

**全部 agent 使用 `composer-2.5`**；**禁止 `composer-2.5-fast`**。

### 2.4 工具与 Skill

| 时机       | 复杂线（§4）                                                           | 精简线（§5）                                                               |
| ---------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Boot       | `agent-toolchain.md` + `trellis-plan` / `trellis-execute`              | 同左 + `round3-repair-debt-worktree-plan.md` §8                            |
| 查代码     | GitNexus + codebase-memory 交叉核实                                    | 同左                                                                       |
| 编辑符号前 | `impact()`；HIGH/CRITICAL 须主会话确认                                 | 若只改 docs/tests 仍须核对无 runtime 误触                                  |
| Plan       | `MASTER.plan.md` + `validate-plan-freeze` exit 0                       | `DEBT.plan.md` + Phase 8D 切片表                                           |
| Execute    | 逐行 `implement.jsonl` + TDD                                           | 编写/修复 + 最小 pytest                                                    |
| 提交前     | `detect_changes()` + `loop_maintain.py`（`--fix` 若触达 docs/backend） | 同左                                                                       |
| Audit      | A1–A8（§4.2）                                                          | 对抗性 `audit-adversarial-authority.md`（无 A1–A8 全维，除非触及 runtime） |
| 全部 Done  | §7 合并                                                                | §7 合并（REG/CI 建议靠后）                                                 |

### 2.5 核心文件锁（主会话强制执行）

| 核心文件组                                                                     | 独占写权限                    | 其它分支                                              |
| ------------------------------------------------------------------------------ | ----------------------------- | ----------------------------------------------------- |
| `backend/app/db/migrations/**`（新 SQL + 009 残余编辑）                        | **B3F-MIG**                   | B3F-SH 只读；须先协调表 migration 归属                |
| `docs/schema/MIGRATION_COVERAGE.md`、`MIGRATION_008_PLAN.md` 路由章节          | **B3F-MIG**                   | B3F-REG 只读对照                                      |
| `source_health_snapshot` migration + writer 路径                               | **B3F-SH**                    | B3F-MIG 可前置共享 migration 文件但 **SH 拥有表语义** |
| `backend/app/ops/data_health.py` 持久化 writer 扩展                            | **B3F-SH**                    | B3F-CLI 不得建表；DH2 路径只读                        |
| `qmd` / console_scripts / `init_db` / packaging `pyproject` entrypoints        | **B3F-CLI**                   | B3F-HYG 仅 `sys.path` 相关须与 CLI 协调               |
| `backend/app/sync/orchestrator.py` handler registry / reconcile 闭包           | **B3F-BR**                    | B3F-HYG 若 C901 重构须 **只读** 或排他分支            |
| `backend/app/layer1_axes/ingestion*.py` R2b–R2d 拆分                           | **B3F-HYG**                   | **禁止**与 live-source 分支同 sprint                  |
| `backend/app/layer3_chains/`\*\* lineage + manifest fail-closed                | **B3F-LIN**                   | 与 B3F-SH 不混同一 PR 除非主会话书面协调              |
| `backend/app/layer2_sensor/`\*\* VR/fetch_log binding（`R3Y-LINEAGE-VR-001`）  | **B3F-LIN**                   | 只读其它                                              |
| ResourceGuard / Layer1 perf hot paths                                          | **B3F-HYG**                   | B3F-SH 只读                                           |
| `tests/test_round3_verification_command_matrix.py`、`verification_commands.md` | **B3F-CI**                    | 其它只读                                              |
| Registry 三件套 / `UNRESOLVED` / `RESOLVED` / `AUDIT_DEFERRED` 闭合行          | **主会话** + **B3F-REG** 草案 | 六复杂线仅 proposed delta                             |

**Live 联网：** 仅 **B3F-SH** 的 `R3F-SH-06`（FRED live primary）在 **用户授权 YAML** 存在时可 live；**B3F-CLI** 的 `R3F-CLI-05` 为 runbook/mock 优先，不得默认 live。

### 2.6 Per-branch allowed / forbidden（SSOT 摘要）

> 完整以 roadmap Round 3F 行 + manifest §1–§4 为准；Execute 前须抄入 `MASTER`/`DEBT.plan` Boundary 表。

| ID          | Owns（可写）                                                                           | Must not own                                                                         |
| ----------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **B3F-LIN** | L3/L4 snapshot lineage pytest；L2 VR binding；L3 manifest fail-closed；registry 行草案 | production clean write；live source 默认启用；宣称 3D.3 已全关                       |
| **B3F-MIG** | 009 残余 migration；008 路由文档；`registry_generation` 列 migration                   | 重复实现 009 已关 CHECK（`R3F-MIG-01` verify only）；`source_health_snapshot` 表语义 |
| **B3F-CLI** | `qmd data`、console script、`init_db --sync-registry`、staging E2E runbook             | production clean write；默认 live；`source_health_snapshot` 建表                     |
| **B3F-SH**  | `source_health_snapshot`、quality runners、readiness rollup、FRED live 跟踪            | DH2 只读路径建表；Eastmoney/AkShare false-close；无授权 live                         |
| **B3F-BR**  | backfill/reconcile parity；handler registry；`R3-PARTIAL-4` registry 链 ADR            | 重开 `R3-PARTIAL-5` crash-window 实现；production write                              |
| **B3F-HYG** | C901、ingestion R2b–R2d、perf budget、ResourceGuard、adapter port、PROMPT_03           | 与 B3F-MIG 同改 migration 列；live pilot；Round4 UI                                  |
| **B3F-REG** | registry/docs/COVERAGE 对齐；Wave-B 残余 reconcile；no-reopen guards                   | 无证据 RESOLVED；重写 migration 009；改 `backend/` 业务逻辑（除非回归测试）          |
| **B3F-CI**  | pytest markers、verification_commands、CI doc、gate 测试                               | `backend/app/`\*\* 业务行为变更；production DB 写入                                  |

### 2.7 `/to-issues` 与切片证据

- **复杂线：** Plan 冻结前 `/to-issues`；每切片独立 RED/GREEN + `execute-evidence`。
- **精简线：** `DEBT.plan.md` vertical slices 表（Source ID、AC、allowed、verification）。
- **禁止**单 PR 水平吞并多个 `R3F-*` 段而无切片边界。

---

## 3. 权威必读索引

### 3.0 八路分支一览

| Playbook ID | 分支                                                 | Worktree（建议）                   | Trellis task-dir（建议）                   | 轨道          | 流水线 | 必读      |
| ----------- | ---------------------------------------------------- | ---------------------------------- | ------------------------------------------ | ------------- | ------ | --------- |
| B3F-LIN     | `fix/round3f-batch6-lineage-layer3-registry-closure` | `../quant-monitor-desk-wt-b3f-lin` | `round3f-batch6-lineage-layer3-closure`    | **complex**   | §4     | §3.1+§3.2 |
| B3F-MIG     | `feature/round3f-migration-residual-checks`          | `../quant-monitor-desk-wt-b3f-mig` | `round3f-migration-residual-checks`        | **complex**   | §4     | §3.1+§3.3 |
| B3F-CLI     | `feature/round3-qmd-data-cli`                        | `../quant-monitor-desk-wt-b3f-cli` | `round3-qmd-data-cli`                      | **complex**   | §4     | §3.1+§3.4 |
| B3F-SH      | `feature/round3-source-health-and-quality-runners`   | `../quant-monitor-desk-wt-b3f-sh`  | `round3-source-health-and-quality-runners` | **complex**   | §4     | §3.1+§3.5 |
| B3F-BR      | `feature/round3-backfill-reconcile-parity`           | `../quant-monitor-desk-wt-b3f-br`  | `round3-backfill-reconcile-parity`         | **complex**   | §4     | §3.1+§3.6 |
| B3F-HYG     | `chore/round3-batch6-technical-debt`                 | `../quant-monitor-desk-wt-b3f-hyg` | `round3-batch6-technical-debt`             | **complex**   | §4     | §3.1+§3.7 |
| B3F-REG     | `chore/round3f-registry-batch-closeout`              | `../quant-monitor-desk-wt-b3f-reg` | `round3f-registry-batch-closeout`          | **debt-lite** | §5     | §3.1+§3.8 |
| B3F-CI      | `chore/round3-ci-gate-hardening`                     | `../quant-monitor-desk-wt-b3f-ci`  | `round3-ci-gate-hardening`                 | **debt-lite** | §5     | §3.1+§3.9 |

### 3.1 共用底座（每分支 Plan 前 Read + 摘要）

| 类别         | 路径                                                                                                                                       |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **协调**     | 本 playbook · `BATCH_3F_*` 包 · `BATCH_3F_PLAYBOOK_ADVERSARIAL_AUDIT.report.md` · `BATCH_3F_HARDENING_RULES.md`                            |
| **协调**     | `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3F · `complex-task-planning-protocol.md` Phase 8D · `**agent-toolchain.md`\*\*                   |
| **协调**     | `round3-repair-debt-worktree-plan.md` §6–§8 · `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.3（历史索引）                                        |
| **Registry** | `AUDIT_DEFERRED` / `UNRESOLVED` / `RESOLVED` · `UNRESOLVED_ITEM_TASK_COVERAGE.md`                                                          |
| **待办台账** | `ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` · `ROUND3_BATCH25_PENDING_FIX_REGISTRY.md` · `ROUND3_BATCH6_021_PENDING_FIX_REGISTRY.md`（若存在） |
| **Handoff**  | `ROUND3_HANDOFF.md` · post Batch 3V checkpoint                                                                                             |
| **质量门**   | `staged_acceptance_policy.md` · `production_live_pilot_policy.md` · `docs/ops/verification_commands.md`                                    |
| **全局**     | `GLOBAL_EXECUTION_RULES.md` · `GLOBAL_TESTING_POLICY.md` · `GLOBAL_RESOURCE_LIMITS.md` · `**GLOBAL_TASK_TEMPLATE.md`\*\*                   |
| **架构**     | `MIGRATION_MAP.md` · `specs/context/authority_graph.yaml`                                                                                  |

### 3.2 B3F-LIN — Lineage / Layer3 Registry Closure

**Roadmap：** `R3F-LIN-01..03`、`R3F-L3-01..02`

| 路径                                                                     | 用途             |
| ------------------------------------------------------------------------ | ---------------- |
| `docs/quality/ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` §2                  | 开放项来源       |
| `backend/app/layer3_chains/snapshot_builder.py`                          | L3 manifest 边界 |
| `backend/app/layer2_sensor/` · `layer4_markets/`                         | lineage 邻接     |
| `specs/contracts/snapshot_lineage_contract.yaml`                         | 契约             |
| `tests/test_layer3_snapshot_builder.py` · `test_layer2_sensor_loader.py` | 基线             |
| `docs/adr/ADR-023-layer5-conflict-review-path.md`                        | 只读（L5 邻接）  |

### 3.3 B3F-MIG — Migration Residuals

**Roadmap：** `R3F-MIG-01..06`

| 路径                                                           | 用途                     |
| -------------------------------------------------------------- | ------------------------ |
| `docs/schema/MIGRATION_008_PLAN.md` · `MIGRATION_COVERAGE.md`  | 008/009 路由             |
| `backend/app/db/migrations/009_status_check_constraints.sql`   | 009 已关部分（只读对照） |
| `docs/decisions/ADR-002-db-check-vs-app-validation.md`         | CHECK 策略               |
| `tests/test_schema_contract.py` · `test_migration_coverage.py` | 基线                     |

### 3.4 B3F-CLI — Ops CLI & Packaging

**Roadmap：** `R3F-CLI-01..05`

| 路径                                                                    | 用途                   |
| ----------------------------------------------------------------------- | ---------------------- |
| `docs/ops/data_sync_quick_reference.md` · `data_sync_command_matrix.md` | CLI 语义               |
| `specs/contracts/data_cli_contract.yaml`                                | 契约                   |
| `scripts/init_db.py` · `pyproject.toml`                                 | 打包入口               |
| `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`                  | `R3-AUDIT-DEF-02` 邻接 |
| `tests/test_sync_jobs.py` · vendor E2E 基线                             | staging skeleton       |

### 3.5 B3F-SH — Source Health & Runners

**Roadmap：** `R3F-SH-01..07` · 任务卡 `R3F_verified_audit_ops_perf_hygiene.md`（`VR-DATAHEALTH-001`）

| 路径                                                             | 用途             |
| ---------------------------------------------------------------- | ---------------- |
| `backend/app/ops/data_health.py`                                 | v2 只读基线      |
| `docs/ops/data_health_cli.md` · `ops_health_check_contract.yaml` | 契约             |
| `014_implement_data_sync_orchestrator.md`                        | runner 矩阵      |
| `tests/test_ops_data_health.py` · `test_data_health_v2.py`       | 基线             |
| `PROMPT_04_debt_r3b275_fred_staged_semantics.md`                 | `B2.5-O-05` 边界 |

### 3.6 B3F-BR — Backfill / Reconcile Parity

**Roadmap：** `R3F-BR-01..05`

| 路径                                                       | 用途                         |
| ---------------------------------------------------------- | ---------------------------- |
| `backend/app/sync/orchestrator.py` · `runners.py`          | 独占协调                     |
| `specs/contracts/sync_job_contract.yaml`                   | 矩阵                         |
| `016_implement_source_conflict_validator.md`               | reconcile 邻接               |
| `tests/test_sync_orchestrator.py` · `test_sync_runners.py` | 基线                         |
| `docs/adr/ADR-023-layer5-conflict-review-path.md`          | `R3-PARTIAL-4` registry 关账 |

### 3.7 B3F-HYG — Hygiene / Perf / Ingestion Split

**Roadmap：** `R3F-HYG-01..13` · `R3F_verified_audit_ops_perf_hygiene.md`（`VR-RG-001`、`VR-L1PERF-001`、`VR-PERF-001`）

| 路径                                                           | 用途                       |
| -------------------------------------------------------------- | -------------------------- |
| `docs/architecture/layer1_ingestion_refactor_rollback_plan.md` | R2b–R2d                    |
| `scripts/production_equivalent_smoke.py`                       | perf budget                |
| `docs/ops/performance_limits.md` · `resource_limits.yaml`      | ResourceGuard              |
| `PROMPT_03` · `PROMPT_05`                                      | perf registry / CI handoff |
| `tests/test_round3_audit_registry_alignment.py`                | registry 对齐门            |

### 3.8 B3F-REG — Registry Batch Closeout（精简线）

| 路径                                                                                      | 用途                                    |
| ----------------------------------------------------------------------------------------- | --------------------------------------- |
| manifest §2–§4                                                                            | 中央化 ID                               |
| `tests/test_unresolved_item_task_coverage.py` · `test_round3_audit_registry_alignment.py` | 对齐测试                                |
| `MANIFEST.json` · `scripts/check_manifest_files.py`                                       | manifest 漂移                           |
| `WAVE-B-HYG-01/02/03`                                                                     | 文档措辞（`R3F-HYG-13` 部分可移交 REG） |

### 3.9 B3F-CI — CI Gate Hardening（精简线）

| 路径                                                       | 用途        |
| ---------------------------------------------------------- | ----------- |
| `docs/ops/verification_commands.md` § Round 3 gate hygiene | SSOT        |
| `tests/test_round3_verification_command_matrix.py`         | 矩阵测试    |
| `PROMPT_05_chore_round3_ci_gate_hardening.md`              | 历史 PROMPT |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.6                  | gate 索引   |

### 3.10 Plan 质检 checklist（复杂线 Agent-2 · 精简线同用 §3.9 追溯）

- [ ] §3.1 + 分支 §3.x **每一行** 已入 `MASTER`/`implement.jsonl` 或 `DEBT.plan`
- [ ] `authority_graph.yaml` 已核对
- [ ] `GLOBAL_TASK_TEMPLATE.md` Red Flags 已覆盖
- [ ] `BATCH_3F_HARDENING_RULES.md` 已写入 Plan Boundary
- [ ] 每个 owned `R3F-`\* / registry ID 有 closure test 或 re-defer
- [ ] `/to-issues` 或 debt slices 表已冻结
- [ ] `uv run python scripts/loop_maintain.py` exit 0（规划触达 docs 时 `--fix`）
- [ ] 对抗性审计 **§1 BLOCKING** 项已在 Plan 中体现缓解
- [ ] 遗漏项已写回 Plan 并复检零遗留

### 3.11 Plan 追溯规则

| 规则         | 要求                                                      |
| ------------ | --------------------------------------------------------- |
| **索引行**   | §3.x 每路径须在 Plan 必读表有对应行                       |
| **R3F 追溯** | 每个 owned `R3F-`\* 须 Source ID → AC → verification 三联 |
| **负向边界** | Plan 须抄 §2.6 **Must not own** + §8.x **未改什么**       |
| **切片垂直** | 每切片仅一个 `R3F-`\* 或可测子 AC                         |
| **复检**     | Plan 质检输出 §3.12 表且遗漏风险列全为「无」或已修复      |

### 3.12 Plan 质检输出格式（Agent-2 必填）

| 路径 | 已入 MASTER/implement 或 DEBT.plan | 摘要一句 | 遗漏风险 |
| ---- | ---------------------------------- | -------- | -------- |

---

## 4. 轨道 A — 六条复杂任务分支（complex）

**适用：** B3F-LIN、B3F-MIG、B3F-CLI、B3F-SH、B3F-BR、B3F-HYG。

### 4.1 Agent 流水线

```
Plan → Plan质检 → Execute → Audit(A1–A8) → Repair → 对抗性审计 → 主会话提交
```

| 步骤       | 产出与门禁                                                         |
| ---------- | ------------------------------------------------------------------ |
| 1 Plan     | `MASTER.plan.md`、`implement.jsonl`、`validate-plan-freeze` exit 0 |
| 2 Plan质检 | §3.11–§3.12 零遗留                                                 |
| 3 Execute  | TDD §8.x；`validate-execute-handoff`                               |
| 4 Audit×8  | `audit-skill-paths.yaml`                                           |
| 5 Repair   | 阻塞+非阻塞全修                                                    |
| 6 对抗性   | `agents/audit-adversarial-authority.md`                            |
| 7 主会话   | §6 + §8.x PASS + commit                                            |

### 4.2 Audit 派发（一维一 agent）

| 维  | 模板                                                            |
| --- | --------------------------------------------------------------- |
| A1  | `agents/audit-a1-spec.md`                                       |
| A2  | `agents/audit-a2-ponytail.md`                                   |
| A3  | `agents/security-auditor.md` + `sql-pro.md`                     |
| A4  | `agents/code-reviewer.md`                                       |
| A5  | `agents/audit-a5-completion.md`                                 |
| A6  | `agents/performance-engineer.md`（SKIP 须记录；B3F-HYG 建议跑） |
| A7  | `agents/database-administrator.md` + `sre-engineer.md`          |
| A8  | `agents/qa-expert.md` + `test-automator.md`                     |

### 4.3 正式线 Audit 单队列

- **Execute 可八路并行**；**Audit→Repair→对抗性→提交** 同一时刻**可以多条复杂线，但是不要超出agent派发上限**（最多可以三条复杂线同时进入八维度8agent）
- **建议 Audit 顺序（完成先后）：** MIG → LIN → CLI → SH → BR → HYG（可按 §7.2 合并前提调整）。

### 4.4 复杂线约束（相对精简线的额外要求）

| 约束                   | 说明                                                     |
| ---------------------- | -------------------------------------------------------- |
| **Plan 冻结**          | `validate-plan-freeze` exit 0 后才 Execute               |
| **implement.jsonl**    | 第一行 `MASTER.plan.md`；不得默认塞满 registry           |
| **GitNexus**           | 改符号前 `impact()`；合并前 `detect_changes()`           |
| **全量 pytest**        | 每 §8.x 末尾含 `uv run pytest -q`                        |
| **无 production 写入** | 每分支 closure report 须 no-mutation 声明                |
| **Live**               | 仅 B3F-SH 在授权下；须 `production_live_pilot_policy.md` |

### 4.5 复杂线派发清单

| #    | 角色     | Prompt 要点                                        |
| ---- | -------- | -------------------------------------------------- |
| 1    | Plan     | roadmap `R3F-*` 行 + §3 + hardening + `/to-issues` |
| 2    | Plan质检 | §3.11–§3.12 + §2.5/§2.6                            |
| 3    | Execute  | `implement.jsonl` 逐行 + TDD + impact              |
| 4a–h | A1–A8    | `agents/` + diff + AC                              |
| 5    | Repair   | 全 findings + pytest                               |
| 6    | 对抗性   | `audit-adversarial-authority.md`                   |
| 7    | 主会话   | §6 + §8 + commit                                   |

---

## 5. 轨道 B — 两条精简分支（debt-lite）

**适用：** B3F-REG、B3F-CI。  
**共同特征：** `DEBT.plan.md` + Phase 8D；**默认不改** `backend/app/`\*\* 业务主逻辑；无 A1–A8 全维 Audit（除非 PR 意外触及 runtime）。

### 5.1 B3F-REG — Registry Batch Closeout

```
轻量Plan → Plan质检 → 编写/核对 → 对抗性审计 → 主会话
```

| 步骤      | 要求                                                                                          |
| --------- | --------------------------------------------------------------------------------------------- |
| 轻量 Plan | `DEBT.plan.md`；切片表：**每行一个 registry ID 或一个 reconcile 主题**                        |
| Plan质检  | §3.8 全文；manifest §3 已 RESOLVED 项标「verify-only」                                        |
| 编写      | 三 registry + `UNRESOLVED_ITEM_TASK_COVERAGE.md` + Wave-B 残余；**TDD** 对齐测试 RED→GREEN    |
| 禁止      | 重开 `R3-PARTIAL-5` / `R2-RISK-3` / `R3-AUDIT-DEF-03` 实现；无 targeted pytest 的 stale close |
| 对抗性    | `audit-adversarial-authority.md`                                                              |
| 主会话    | §6 + §8.7；与 §7.3 registry 批处理合并                                                        |

**Owned IDs（verify / closeout）：** `R3F-LIN-03`、`R3F-BR-05`、`R3F-MIG-01/06`、`R3F-BR-03`、`R3F-HYG-11`、`R3F-HYG-13`（文档部分）、`WAVE-B-HYG-01/02/03`。

### 5.2 B3F-CI — CI Gate Hardening

```
轻量Plan → Plan质检 → 编写 → 对抗性 → 主会话
```

| 步骤   | 要求                                                                            |
| ------ | ------------------------------------------------------------------------------- |
| Plan   | 映射 `R3F-HYG-12` / PROMPT_05；allowed = tests + docs + scripts 门              |
| 编写   | `verification_commands.md` 与 `test_round3_verification_command_matrix.py` 同步 |
| 禁止   | 改 sync/orchestrator 业务语义；改 ResourceGuard 默认阈值（属 B3F-HYG）          |
| 主会话 | §6 + §8.8                                                                       |

### 5.3 精简线派发表

| 分支 | 1        | 2        | 3    | 4      | 5      |
| ---- | -------- | -------- | ---- | ------ | ------ |
| REG  | 轻量Plan | Plan质检 | 编写 | 对抗性 | 主会话 |
| CI   | 轻量Plan | Plan质检 | 编写 | 对抗性 | 主会话 |

### 5.4 精简线约束（相对复杂线的简化）

| 项目            | 精简线                         | 复杂线                               |
| --------------- | ------------------------------ | ------------------------------------ |
| Plan 产物       | `DEBT.plan.md`                 | `MASTER.plan.md` + `implement.jsonl` |
| Plan 冻结       | Phase 8D 切片表即可            | `validate-plan-freeze`               |
| Execute         | 直接编写 + 最小 pytest         | 逐步 §8 RED/GREEN                    |
| Audit           | 对抗性为主                     | A1–A8 全维                           |
| 范围            | docs/registry/tests/scripts 门 | backend 运行时                       |
| Trellis handoff | merge gate 文档                | `validate-execute-handoff`           |

---

## 6. 单分支 Done — 主会话验收

- [ ] roadmap 所属 `R3F-*` 行 + playbook §8.x 验收命令全绿
- [ ] `uv run pytest -q` 全绿
- [ ] `loop_maintain.py`（需时 `--fix`）
- [ ] `detect_changes()`；符合 §2.5/§2.6
- [ ] 测试五字段 + ponytail
- [ ] Trellis 证据（complex：`validate-execute-handoff`；debt-lite：merge gate + `DEBT.plan` 切片表）
- [ ] **无 production DB 写入** / **无未授权 live fetch**
- [ ] 分支 worktree commit
- [ ] **Closure report 九项**（父 README §5 同 Batch 01）

---

## 7. 全部 Done — 合并

### 7.1 推荐：integration 预合并

```bash
git checkout master && git pull
git checkout -b integration/round3-batch3f
# 按 §7.2 顺序 merge 各分支
uv run pytest -q
uv run python scripts/loop_maintain.py --fix
# FF merge integration/round3-batch3f → master
```

### 7.2 合并顺序（八路）

| 序  | ID      | 分支                                                 | 轨道      | 前提                                                        |
| --- | ------- | ---------------------------------------------------- | --------- | ----------------------------------------------------------- |
| 1   | B3F-MIG | `feature/round3f-migration-residual-checks`          | complex   | —                                                           |
| 2   | B3F-LIN | `fix/round3f-batch6-lineage-layer3-registry-closure` | complex   | 可与 1 并行开发；**合并建议在 1 后**（无 migration 冲突时） |
| 3   | B3F-CLI | `feature/round3-qmd-data-cli`                        | complex   | —                                                           |
| 4   | B3F-SH  | `feature/round3-source-health-and-quality-runners`   | complex   | **B3F-MIG 已合并**（若 SH 依赖 migration）                  |
| 5   | B3F-BR  | `feature/round3-backfill-reconcile-parity`           | complex   | 推荐在 B3F-CLI 后（orchestrator 邻接）                      |
| 6   | B3F-HYG | `chore/round3-batch6-technical-debt`                 | complex   | 避免与 1–5 同文件冲突                                       |
| 7   | B3F-CI  | `chore/round3-ci-gate-hardening`                     | debt-lite | 可在 6 后或并行                                             |
| 8   | B3F-REG | `chore/round3f-registry-batch-closeout`              | debt-lite | **六复杂线 evidence 已齐**                                  |

### 7.3 合并后主会话（一次协调提交）

1. 批处理 Batch 3F owned registry 行 → RESOLVED 或 precise re-defer
2. 更新 `**docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`\*\*（新增 §9 Batch 3F 表）
3. 更新 `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3F checkpoint、`ROUND3_HANDOFF.md`
4. 全量 pytest + `loop_maintain --fix`
5. GitNexus `node .gitnexus/run.cjs analyze`（勿覆盖 `AGENTS.md` 定制段）
6. 运行 Batch 3F closeout audit（§12）

---

## 8. 各分支 PASS 条件与验收命令

> §6 + 本节**同时满足**方可 Done。

### 8.1 B3F-MIG（complex）

```bash
uv sync --locked
uv run pytest tests/test_schema_contract.py tests/test_migration_coverage.py -q
uv run ruff check backend/app/db docs/schema tests
uv run pytest -q && uv run ruff check .
```

| 维度 | PASS                                                              |
| ---- | ----------------------------------------------------------------- |
| 009  | 不重复实现已关 CHECK；`R3F-MIG-01` verify-only                    |
| 残余 | `priority` CHECK 或 ADR；`fetch_log`/`manual_review_queue` 显式列 |
| 路由 | `MIGRATION_COVERAGE.md` 更新 008→009→3F 桶                        |

**未改什么：** `source_health_snapshot` 表语义；sync 业务重构；registry 三件套直接闭合。

### 8.2 B3F-LIN（complex）

```bash
uv sync --locked
uv run pytest tests/test_layer3_snapshot_builder.py tests/test_layer2_sensor_loader.py -q
uv run pytest tests/test_round3_audit_registry_alignment.py -q -k lineage
uv run pytest -q && uv run ruff check .
```

| 维度    | PASS                                                    |
| ------- | ------------------------------------------------------- |
| Lineage | L3/L4 snapshot lineage pytest；registry 行草案          |
| L3      | malformed `bars[]` fail-closed；full row tuple 重建测试 |
| VR      | synthetic ID 不得冒充 VR binding                        |

**未改什么：** production clean write；live source；宣称 3D.3 已全关 without registry。

### 8.3 B3F-CLI（complex）

```bash
uv sync --locked
uv run pytest tests/test_sync_jobs.py -q
uv run ruff check scripts backend/app/sync pyproject.toml
uv run pytest -q && uv run ruff check .
```

| 维度 | PASS                                                            |
| ---- | --------------------------------------------------------------- |
| CLI  | dry-run / route-preview / error_code 锚点                       |
| 打包 | console script smoke；`init_db --sync-registry` 或 CI one-liner |
| E2E  | `R3F-CLI-05` runbook；**无默认 live**                           |

**未改什么：** `source_health_snapshot` 建表；ResourceGuard 默认放宽。

### 8.4 B3F-SH（complex）

```bash
uv sync --locked
uv run pytest tests/test_ops_data_health.py tests/test_data_health_v2.py -q
uv run ruff check backend/app/ops backend/app/sync
uv run pytest -q && uv run ruff check .
```

| 维度   | PASS                                                       |
| ------ | ---------------------------------------------------------- |
| 表     | `source_health_snapshot` migration + writer（非 DH2 路径） |
| Runner | `run_revision_audit` / `run_data_quality` job pytest       |
| 硬约束 | `R3F-SH-07` no-false-close；`B2.5-O-05` 仅授权 live 关闭   |

**未改什么：** Batch 01 DH2 只读路径建表；Eastmoney/AkShare 误关闭。

### 8.5 B3F-BR（complex）

```bash
uv sync --locked
uv run pytest tests/test_sync_orchestrator.py tests/test_sync_runners.py -q
uv run pytest -q && uv run ruff check .
```

| 维度    | PASS                                                                       |
| ------- | -------------------------------------------------------------------------- |
| Parity  | backfill / reconcile re-fetch pytest 或 ADR                                |
| Handler | orchestrator handler registry                                              |
| 关账    | `R3-PARTIAL-4` registry 链 ADR-023；`R3-PARTIAL-5` **仅** regression guard |

**未改什么：** 重开 B3V crash-window 实现；production write。

### 8.6 B3F-HYG（complex）

```bash
uv sync --locked
uv run python scripts/production_equivalent_smoke.py --use-service-path --data-root .audit-sandbox/r3b275-audit
uv run pytest tests/test_resource_guard.py -q
uv run ruff check backend/app
uv run pytest -q && uv run ruff check .
```

| 维度      | PASS                                   |
| --------- | -------------------------------------- |
| Perf      | bounded smoke threshold artifact       |
| Ingestion | R2b–R2d 回滚检查表                     |
| Port      | `R2-RISK-2` port injection 或 re-defer |

**未改什么：** migration 列（属 MIG）；live source；ingestion 与 live 同 sprint。

### 8.7 B3F-REG（debt-lite）

```bash
uv sync --locked
uv run pytest tests/test_unresolved_item_task_coverage.py tests/test_round3_audit_registry_alignment.py -q
uv run python scripts/check_manifest_files.py
uv run pytest -q
```

| 维度     | PASS                                                       |
| -------- | ---------------------------------------------------------- |
| Registry | 三 registry + COVERAGE 无矛盾                              |
| 防重开   | `R3-PARTIAL-5`、`R2-RISK-3`、`R3-AUDIT-DEF-03` verify-only |
| Wave-B   | `R3F-LIN-03` reconcile                                     |

**未改什么：** 无证据改 `backend/` 业务逻辑。

### 8.8 B3F-CI（debt-lite）

```bash
uv sync --locked
uv run pytest tests/test_round3_verification_command_matrix.py -q
uv run pytest -q && uv run ruff check .
```

| 维度 | PASS                                 |
| ---- | ------------------------------------ |
| CI   | verification_commands 与矩阵测试同步 |
| 范围 | tests/docs only                      |

**未改什么：** orchestrator / WriteManager 业务语义。

### 8.9 口诀

| 类型       | Done 当且仅当                        |
| ---------- | ------------------------------------ |
| **复杂线** | §6 + §8.1–§8.6 对应节 + 已提交       |
| **精简线** | §6 + §8.7–§8.8 + 对抗性闭环 + 已提交 |

---

## 9. 开波检查清单

- [ ] 本 playbook + `BATCH_3F_PLAYBOOK_ADVERSARIAL_AUDIT.report.md` 已提交
- [ ] 已读 manifest · hardening · **父 README** · `**agent-toolchain.md`\*\*
- [ ] **八路** owner、worktree、§2.5 锁已登记
- [ ] `composer-2.5 only`；registry **仅主会话 + B3F-REG 收口**
- [ ] integration 策略已选（§7.1）
- [ ] **六复杂 + 两精简** 轨道已写入派发记录
- [ ] FRED live（若做 `R3F-SH-06`）**用户授权**已确认

### 9.1 Worktree 创建模板

**前置：** 每分支 `DEBT.plan`/`MASTER` 含 allowed、forbidden、verification、merge gate。

```bash
cd C:/Users/Guang/Desktop/quant-monitor-desk
git fetch origin
git worktree add -b fix/round3f-batch6-lineage-layer3-registry-closure ../quant-monitor-desk-wt-b3f-lin master
git worktree add -b feature/round3f-migration-residual-checks ../quant-monitor-desk-wt-b3f-mig master
git worktree add -b feature/round3-qmd-data-cli ../quant-monitor-desk-wt-b3f-cli master
git worktree add -b feature/round3-source-health-and-quality-runners ../quant-monitor-desk-wt-b3f-sh master
git worktree add -b feature/round3-backfill-reconcile-parity ../quant-monitor-desk-wt-b3f-br master
git worktree add -b chore/round3-batch6-technical-debt ../quant-monitor-desk-wt-b3f-hyg master
git worktree add -b chore/round3f-registry-batch-closeout ../quant-monitor-desk-wt-b3f-reg master
git worktree add -b chore/round3-ci-gate-hardening ../quant-monitor-desk-wt-b3f-ci master
```

每 worktree 内首次验证：

```bash
uv sync --locked
uv run pytest -q --tb=no -x
```

---

## 10. 快速对照

| 原意              | 章节           |
| ----------------- | -------------- |
| 八路并行          | §0、§1.1、§3.0 |
| 六复杂 + 两精简   | §0、§4、§5     |
| 复杂任务全流程    | §4             |
| 精简分支流程      | §5             |
| 文件锁            | §2.5           |
| allowed/forbidden | §2.6           |
| 合并顺序          | §7.2           |
| closure 九项      | §6             |

---

## 11. Playbook 对抗性审计修复闭环

| 处置                   | 章节                                            |
| ---------------------- | ----------------------------------------------- |
| 八路轨道声明           | §0、§1.1、§3.0                                  |
| 六复杂 / 两精简流水线  | §4、§5                                          |
| 3D.3 / lineage 误读    | §0、§1.1 B3F-LIN                                |
| migration / SH 串行锁  | §2.5、§7.2                                      |
| D2-P3-1 双 owner       | §2.5 B3F-MIG                                    |
| 已 RESOLVED 防重开     | §2.1、§5.1、§8.7                                |
| Plan 质检 / 追溯       | §3.10–§3.12                                     |
| 每分支 PASS + 负向边界 | §8.1–§8.8                                       |
| worktree 八行命令      | §9.1                                            |
| 对抗性报告全文         | `BATCH_3F_PLAYBOOK_ADVERSARIAL_AUDIT.report.md` |

---

## 12. Batch 3F 关账审计（Round 3G 前必跑）

在进入 Round 3G 之前，主会话必须确认：

- [ ] roadmap Round 3F 每个 `R3F-*` 行：**RESOLVED** 或 **re-defer**（owner/phase/closure test）
- [ ] `B2.5-O-05` live FRED：**未**在无用户授权下关闭
- [ ] `R3-B2.75-REQ2-EM` / `R3-PROMPT14-AKSHARE-VAL-01`：**未** false-close
- [ ] `ADV-R3X-LINEAGE-001` / `R3Y-LINEAGE-VR-001` / `R3-B6-021-O-`\*：**registry 已闭合** 或明确 re-defer
- [ ] `R3-PARTIAL-5`、`R2-RISK-3`、`R3-AUDIT-DEF-03`：**未**被重开为实现任务
- [ ] 全量 pytest + `loop_maintain` + `ROUND3_HANDOFF` 已更新

---

_协调手册版本：2026-06-25 rev.1 · 八路并行 dispatch-ready_
