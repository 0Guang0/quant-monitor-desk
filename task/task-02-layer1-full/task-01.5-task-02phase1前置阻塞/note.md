# task-01.5 · 计划外决策与偏离记账

> **定位：** 执行计划（`task_plan.md`）· `TEMP` 用户决议 · MIGRATION_MAP 权威**均未写**，但在**切片实现过程中**才暴露的问题、**偏离**与**决策**。  
> **记账规则 SSOT：** `task_plan.md` §每切片关账 AC · **AC-CLOSE-2**

---

## 与 `findings.md` 的分工（勿混）

| 文件                    | 记什么                                                             | 典型例子              |
| ----------------------- | ------------------------------------------------------------------ | --------------------- |
| **`findings.md`**       | TEMP A/B 项 disposition · GitNexus 爆炸半径 · **计划阶段**用户决议 | B19 与 design 分歧    |
| **`task_plan.md`**      | S1–S7 切片 AC · AD-01～06                                          | AD-06 交易日 backfill |
| **`note.md`（本文件）** | **执行时**才出现的取舍                                             | 本页 CLI 锚点 hygiene |

---

## N/A 索引

| 切片    | AC-CLOSE-2 | 说明                    |
| ------- | ---------- | ----------------------- |
| S1      | N/A        | 2026-07-09              |
| S2      | N/A        | 2026-07-09              |
| S7      | N/A        | 2026-07-09              |
| S7+     | 见下 §S7+  | 2026-07-09              |
| Hygiene | 见下       | 2026-07-09 CLI 锚点清理 |

---

## 记账正文

### Hygiene · CLI docs_anchor 与模块注释清理 · 2026-07-09

| 项                                   | 内容                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **暴露的问题**                       | 正式 CLI 代码里 `docs_anchor` 和注释混用三类来源：(1) 已删除/阶段性 ADR；(2) `R3*` 任务卡号；(3) `docs/ops/` 下**非 design** 的一次性运维稿（如 `data_sync_quick_reference.md`）。用户明确：**只有 `**/design/**` 与保留 ADR 才是权威**；`docs/ops/*.md`（非 design 子目录）不算设计 SSOT。                                                                                                                                                                                                                                                                                                                                       |
| **计划外点**                         | task-01.5 S1 只修了断链 ADR 指针，未建立「锚点集中表」；也未区分 ops 阶段性文件 vs design 权威。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **决策（api-and-interface-design）** | ① **保留** `error_code` + `docs_anchor` 失败信封（frozen contract / Hyrum：用户会依赖可排障输出）。② **集中 SSOT**：`backend/app/cli/errors.py` 模块级常量 `DOCS_ANCHOR_*`，禁止在业务函数里散落路径字符串。③ **锚点只指向**：`docs/**/design/**`、保留 `docs/decisions/ADR-*`。④ **不再指向** `docs/ops/data_sync_quick_reference.md`、`docs/ops/data_health_cli.md`、旧 `docs/ops/ERROR_CODE_GUIDE.md`（无 design 镜像者）。⑤ **模块 docstring** 去掉 `R3F-CLI-01` / `R3H-08` / `R3H_PASS_EXECUTION_PLAN` 等任务卡号，改业务白话 + design/ADR 链。⑥ **行为不变**：锚点字符串变更仅修正「指路牌」目标；live 门、分档表逻辑未改。 |
| **实现**                             | `errors.py`：`DOCS_ANCHOR_*` 全集（design ERROR_CODE_GUIDE、incident_playbook、orchestrator §13.7、data_validation、ADR-011/015）。`data_commands.py` / `incremental_sync_router.py` / `main.py` / `phase1_acceptance.py` / `indicator_binding.py` 改引常量。`live_tier_router.py` 等去任务号注释。                                                                                                                                                                                                                                                                                                                               |
| **验证**                             | `test_qmdData_liveFetch_withoutOptIn_pointsToLiveEnvGateDoc`（五字段）锁 live-fetch → ADR-015 锚点；`test_indicator_binding_registry` 更新为 design ERROR_CODE_GUIDE；`uv run pytest -q` 全绿。                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **后续**                             | ① `specs/contracts/data_cli_contract.yaml` 内 `docs_anchor` 仍写旧 `docs/modules/data_sync_orchestrator.md`（无 design 前缀）— **单独票**对齐 promote/契约。② 全仓 80+ 文件 `R3*` 模块头 — **单独 hygiene 票**。③ S4 rename `live_tier_router` 不变。                                                                                                                                                                                                                                                                                                                                                                             |

### Hygiene · phase1_acceptance docs_anchor 统一 · 2026-07-09

| 项             | 内容                                                                                                                                                                                                                                                                                                          |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **暴露的问题** | `phase1_acceptance.py` 仍混用 `specs/contracts/data_cli_contract.yaml` 与 `specs/layer1_axes/indicator_binding_registry.yaml` 作 `docs_anchor`；与用户「仅 design/保留 ADR」原则不一致。                                                                                                                      |
| **决策**       | 退役 legacy / 隔离库失败 → `DOCS_ANCHOR_LIVE_ENV_GATE`（ADR-015）；缺 Tier A fetch op → `DOCS_ANCHOR_DATA_SYNC_CLI`（orchestrator §13.7）；缺 indicator binding → `DOCS_ANCHOR_LAYER1_INDICATOR_BINDING`（`layer1_global_regime_panel.md` design）。机器可读 YAML 仍由代码 **读取**，但不作为用户可见指路牌。 |
| **验证**       | `test_phase1Acceptance_requireLiveRoot_rejectsGenericSandbox` 断言 ADR-015 锚点；`test_dataCliContract_sandboxCleanWriteRetired` 断言退役命令同锚点；`uv run pytest -q` 全绿。                                                                                                                                |

### 权威分层（用户 2026-07-09 拍板 · 记入本 note）

```text
MIGRATION_MAP 索引的 **/design/**  >  保留 docs/decisions/ADR  >  specs/contracts
docs/ops/*.md（非 ops/design）     =  阶段性/一次性运维稿，不得作 docs_anchor SSOT
```

**运维排障读法：** CLI 失败 JSON 里的 `docs_anchor` 应领人去 **design 或 ADR**；若需操作步骤，由 design 文档内交叉引用 ops 稿，而不是代码直接绑 staging 路径。

### S7+ · 可观测性 P2/P3 + 安全体检 · 2026-07-09

| 项             | 内容                                                                                                                                                                                                                                                                                                                                                            |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **暴露的问题** | S7 重构后写入审计已有 `run_id`，但 CLI 入口发号不统一、`requested_by` 硬编码 `orchestrator`；本地批处理无可 grep 的成败信号；`require_enabled` 主源 disabled 缺行为测。                                                                                                                                                                                         |
| **计划外点**   | `task_plan.md` S7 未列 P2/P3；安全扫描为会话内追加（非 TEMP 项）。                                                                                                                                                                                                                                                                                              |
| **决策**       | ① **P2**：`run_context.new_cli_run_id` / `cli_requested_by` 在 CLI 边界发号；`SyncJobSpec.requested_by` 贯通至 `write_audit_log`。② **P3**：`write_telemetry` 白名单 JSON → stderr；`QMD_WRITE_TELEMETRY=0` 关闭。③ **安全**：静态读码 + GitNexus；0 可报告漏洞，报告落 `security-scan-s7/`。④ **不**引入 OpenTelemetry/RED metrics（CLI 批处理，无证据需改）。 |
| **实现**       | `run_context.py` · `write_telemetry.py` · `jobs.py` · `runners.py` · `phase1_acceptance.py` · `binding_executor.py` · `data_commands.py`（rev-audit/dq）；`test_cli_run_context` · `test_write_telemetry` · orchestrator `requested_by` 测。                                                                                                                    |
| **验证**       | `uv run pytest -q` exit 0。                                                                                                                                                                                                                                                                                                                                     |
| **后续**       | 结构化 `event=` 日志扩展（非 stderr）— **阶段外**；待 S3–S6 完成后再评 Phase F。                                                                                                                                                                                                                                                                                |
