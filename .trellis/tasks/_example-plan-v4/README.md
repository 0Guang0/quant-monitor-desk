# Plan v4 执行计划样板（只读）

> **本目录是什么：** Trellis **单任务**的 v4 **执行计划**最小合格实例（`EXECUTION_INDEX` + `frozen` + `AUDIT` + 机器 jsonl）。  
> **本目录不是什么：** **Coordinator PLAYBOOK**（批次派发 / worktree / 合并顺序 / 文件锁）。二者职责不同，勿混用。

| 概念                     | 典型路径示例                                                   | 回答的问题                                                        |
| ------------------------ | -------------------------------------------------------------- | ----------------------------------------------------------------- |
| **执行计划（v4）**       | 本目录 `.trellis/tasks/<slug>/`                                | 这一个 Trellis 任务做什么、分几步、怎么验收、Execute 必读哪些原文 |
| **Coordinator PLAYBOOK** | `docs/implementation_tasks/**/BATCH_*_COORDINATOR_PLAYBOOK.md` | 主会话如何向多 agent **派发**、并行轨、合并顺序、谁锁哪些共享文件 |

PLAYBOOK 示例（仅供对照，**不是**执行计划模板）：

- `C:\Users\Guang\Desktop\quant-monitor-desk\docs\implementation_tasks\ROUND_3_SANDBOX_CLEAN_WRITE\BATCH_3G_SANDBOX_CLEAN_WRITE\BATCH_3G_COORDINATOR_PLAYBOOK.md`
- `C:\Users\Guang\Desktop\quant-monitor-desk\docs\quality\coordination\BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`

v3 遗留的「整包执行计划」是 `MASTER.plan.md`；**v4 新任务不再写 MASTER**，执行计划拆成下表三件套 + 自动生成 jsonl。

---

## 权威引用（读这条线即可）

| 顺序 | 文档                       | 绝对路径                                                                                                    |
| ---- | -------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 1    | Plan agent skill           | `C:\Users\Guang\Desktop\quant-monitor-desk\.cursor\skills\trellis-plan\SKILL.md`                            |
| 2    | 协议 v4 定义               | `C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\spec\guides\complex-task-planning-protocol.md` **§0.0** |
| 3    | 执行索引空白模板           | `C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\spec\guides\templates\EXECUTION_INDEX.md`               |
| 4    | 冻结卡空白模板             | `C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\spec\guides\templates\FROZEN_TASK_CARD.md`              |
| 5    | 审计矩阵空白模板           | `C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\spec\guides\templates\AUDIT.plan.md`                    |
| 6    | 冻结合并门清单             | `C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\spec\guides\templates\plan.freeze.md`（§3.0v4）         |
| 7    | 输入归并桥接               | `C:\Users\Guang\Desktop\quant-monitor-desk\docs\implementation_tasks\TASK_INPUT_CONTEXT_INDEX.md`           |
| 8    | **本样板（填好后的实例）** | `C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\tasks\_example-plan-v4\`                                |

---

## v4 执行计划长什么样（三层）

```text
docs/implementation_tasks/**/NNN_*.md     ← Plan 加固「活任务卡」（Execute 不读）
        │
        │  freeze-task-card
        ▼
frozen/<NNN>.md                             ← 正文 SSOT：边界、§9 步骤叙述、已内联设计
EXECUTION_INDEX.md                          ← 人工索引：§1 命令/证据、§2 AC、§3 必读 manifest
AUDIT.plan.md                               ← 薄审计矩阵
        │
        │  generate-manifests
        ▼
implement.jsonl / audit.jsonl / check.jsonl ← 机器清单（hook 强制 Read）
```

**对人：** 执行计划 = **`EXECUTION_INDEX.md` + `frozen/*.md`**（再加 `AUDIT.plan.md` 给 Audit）。  
**对机器：** `implement.jsonl` 等由索引 §3 与固定 Boot 槽位生成，**手改 jsonl 易在下次 generate 被覆盖**。

---

## 协议 v4 是什么

**定义位置：** `C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\spec\guides\complex-task-planning-protocol.md` **§0.0**（及 §0 文档分工表）。

**一句话：** 2026-06 起 `task.py create` 默认的 Plan 冻结协议——用 **冻结三件套** 替代 v3 的整包 `MASTER.plan.md`，Execute/Audit 不再读活任务卡。

| 项             | v4 约定                                                                                             |
| -------------- | --------------------------------------------------------------------------------------------------- |
| 版本标记       | `task.json` → `meta.plan_protocol_version: "4"`                                                     |
| 冻结产出       | `EXECUTION_INDEX.md` + `frozen/<NNN>.md` + `AUDIT.plan.md`                                          |
| 机械命令       | `freeze-task-card` → `generate-manifests` → `validate-plan-freeze` →（用户批准后）`start`           |
| Execute 读什么 | `frozen/*.md`（正文）+ `EXECUTION_INDEX.md`（索引）+ `implement.jsonl`（机器清单，含 §3 原文）      |
| Audit 读什么   | `AUDIT.plan.md` + `EXECUTION_INDEX.md` **§5** 追溯集 + `audit.jsonl`                                |
| 内联规则       | 可无损总结 → 并入 **frozen §5–§8**，并在索引 **§4** 登记；不可精简 → 只列索引 **§3**（`must-read`） |
| 明确不做       | 新任务**不写** `MASTER.plan.md`；Execute **不读** `docs/.../NNN_*.md` 活卡                          |

v3 遗留任务仍可用 `MASTER.plan.md` + `research/source-index.md`；与 v4 并存，靠目录里是否有 `EXECUTION_INDEX.md` + `frozen/` 区分。

---

## `EXECUTION_INDEX.md` 是什么

**定义位置：** 协议 **§0** 表（「唯一索引：步骤/证据、必读原文 manifest、Audit 追溯」）；空白结构见  
`C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\spec\guides\templates\EXECUTION_INDEX.md`。

**一句话：** 放在 Trellis 任务根目录的 **执行索引**——Execute + Audit 共用的**人工目录**，把「第几步、怎么验、还必须读哪些仓库原文」写在一处；**不是** Coordinator PLAYBOOK，也**不是** frozen 正文。

| 节           | 职责                                                                       | v3 大致对应                         |
| ------------ | -------------------------------------------------------------------------- | ----------------------------------- |
| 文首 **P0i** | 须含 **`索引完整`**（v4 输入清单门禁，替代 `source-index.md` §C）          | `source-index` / P0i                |
| **§0**       | slug、source_card、frozen_card、batch/item                                 | MASTER §0                           |
| **§0.1**     | 活任务卡 AC ↔ Step ↔ 验证链                                                | original-plan-trace                 |
| **§1**       | 每步 `9.x` 的 RED/GREEN 命令与证据路径                                     | MASTER §8                           |
| **§2**       | AC ↔ 测试/命令；**§2.1** Tier A/B                                          | MASTER §9 / §10                     |
| **§3**       | 必须读原文 manifest（`must-read` 等）→ **`generate-manifests` 写入 jsonl** | Source Context Index / implement 行 |
| **§4**       | 已无损并入 frozen 的来源（§3 **不得**重复列）                              | 内联对照表                          |
| **§5**       | Audit 追溯集（活卡对照、frozen、round map 等）                             | Audit Source Trace                  |
| **§6**       | 指向 `context_pack.json` 与 Boot 读序说明                                  | loop 路由                           |

**与 `frozen/*.md` 的分工：** frozen 存**叙述性**正文（边界、设计摘要、§9 步骤说明）；`EXECUTION_INDEX` 存**可机械校验**的表（命令、AC、manifest 路径）。Execute 两步都要读：正文在 frozen，「今天跑哪条 pytest」在索引 §1/§2。

**与本样板：**  
`C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\tasks\_example-plan-v4\EXECUTION_INDEX.md`

---

## 从零产出执行计划（逐步）

### 步骤 0 — 创建 Trellis 任务目录

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run python .trellis/scripts/task.py create "任务标题" --slug your-slug
```

默认 `task.json` → `meta.plan_protocol_version: "4"`。任务目录：`C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\tasks\your-slug\`。

**可复制本样板：** 复制 `_example-plan-v4` 整目录后改 `slug`、清空 §1/§2/§3 业务内容，比从空白拼凑更快。

### 步骤 1 — P0 读原计划包（禁止跳过就写步骤）

按 `complex-task-planning-protocol.md` **§0.1** 读 `docs/implementation_tasks/`（README → GLOBAL×4 → Round README/DECISIONS → 本批 `NNN_*.md`）。

产出（Plan-only，Execute 默认不读）：

| 文件                     | 路径模式                                      | 要求                                                                           |
| ------------------------ | --------------------------------------------- | ------------------------------------------------------------------------------ |
| `plan-boot.md`           | `.trellis/tasks/<slug>/research/plan-boot.md` | 含 `Phase P0 complete`                                                         |
| `plan-skill-reads.jsonl` | `.../research/plan-skill-reads.jsonl`         | 每条 skill Read 一行；覆盖 `plan-skill-paths.yaml` 的 `freeze_required_skills` |
| `context_pack.json`      | `.trellis/tasks/<slug>/context_pack.json`     | `uv run python scripts/context_router.py --task .trellis/tasks/<slug>`         |

### 步骤 2 — Plan 各 phase 加固活任务卡与草稿

**活任务卡（仓库内）：** `docs/implementation_tasks/<ROUND>/<NNN>_*.md`（结构见 `GLOBAL_TASK_TEMPLATE.md`）。

**Skill 注册表权威：** `C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\spec\guides\plan-skill-paths.yaml`  
每 Read 一行写入 `research/plan-skill-reads.jsonl`；冻结时 `freeze_required_skills` 必须全覆盖，Phase **3** 还须满足 `freeze_phase3_one_of`（三选一）。

#### 2.1 必做 phase（默认每个复杂任务都要走）

| Phase    | Skill                                                                  | 主要产出 / 写入位置                                                                               |
| -------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| boot     | `agent-toolchain`、`trellis-plan`                                      | `research/plan-boot.md`（含 `Phase P0 complete`）                                                 |
| P0-index | `trellis-plan`                                                         | `EXECUTION_INDEX.md` 草稿 + 文首 **`索引完整`**                                                   |
| 1a       | `gitnexus-plan-1a`                                                     | `research/project-overview.md`                                                                    |
| 1b       | `gitnexus-plan-1b`                                                     | `research/gitnexus-summary.md`                                                                    |
| 2a       | `trellis-brainstorm`                                                   | `prd.md`（薄索引，指向后续 frozen/索引）                                                          |
| 2b       | `spec-driven-development`                                              | 契约/范围收敛（并入活卡或 frozen 草稿）                                                           |
| **3**    | **三选一：** `grill-me` **或** `interview-me` **或** `grill-with-docs` | `research/grill-me-session.md` 等对应 session 文件                                                |
| 3.5      | `to-issues`                                                            | 活任务卡 **§9** 垂直切片 / 工单列表                                                               |
| 5a       | `planning-and-task-breakdown`                                          | 活任务卡 §9 + **`EXECUTION_INDEX` §1** 步骤行                                                     |
| 5b       | `writing-plans`                                                        | **`EXECUTION_INDEX` §1** RED/GREEN + **§2** 验收 / Tier                                           |
| 5c       | `trellis-before-dev`                                                   | `implement.jsonl` 草稿校对、`research/integration-ledger.md`（v3 打包地图；v4 仍可与 §3/§4 对照） |
| 5d       | `doubt-driven-development`                                             | `research/integration-audit.md`；**`AUDIT.plan.md` §1/§2**；**`EXECUTION_INDEX` §3** manifest     |

#### 2.2 条件 / 可选 phase（按任务启用，启用则必须 Read 并记入 plan-skill-reads）

| Phase | Skill                                                                                            | 何时启用                                      | 主要产出 / 写入位置                                            |
| ----- | ------------------------------------------------------------------------------------------------ | --------------------------------------------- | -------------------------------------------------------------- |
| 2     | `domain-modeling`                                                                                | 无 `CONTEXT.md` 或领域术语模糊                | 术语表 / 领域边界 → 活卡或 frozen §5–§6                        |
| **4** | **按需选一或多项：** `brainstorming`、`api-and-interface-design`、`codebase-design`、`prototype` | 新 API/模块设计、深度重构、需可丢弃原型验证时 | 设计结论 → **frozen §5–§8** 或索引 **§4**；新契约路径 → **§3** |
| 4     | `api-and-interface-design`                                                                       | 新 HTTP/CLI/契约面                            | 接口表 → frozen / §3 契约路径                                  |
| 4     | `codebase-design`                                                                                | 新模块或大范围重构                            | 模块边界 → frozen §6、§8                                       |
| 4     | `prototype`                                                                                      | 高风险设计需先验证                            | `research/*` 原型笔记；**不**替代 §1 正式 RED/GREEN            |

> **Phase 4 规则：** `plan-skill-paths.yaml` 定义为 `skills_any`——**没有固定必做项**；但若本任务启用了其中任一 skill，须写入 `plan-skill-reads.jsonl` 并把结论归并进 frozen / `EXECUTION_INDEX`，不能只跑 skill 不落盘。

#### 2.3 内联规则（协议 §0.0）

可无损总结的契约/设计 → 写入将冻结的 **§5–§8**；不可精简的 → 只列 **`EXECUTION_INDEX` §3**（`manifest=must-read`），并在 **§4** 记录已内联项。

#### 2.4 步骤 2 与后续步骤的分界

| 仍在步骤 2（Plan 草稿）       | 步骤 3 起（执行索引定稿）           |
| ----------------------------- | ----------------------------------- |
| 活任务卡 §1–§13 加固          | 从模板补全 `EXECUTION_INDEX` 各节表 |
| `prd.md`、`research/*` 分析稿 | `§1`/`§2` 与 frozen §9 逐步对齐     |
| Phase 4 可选设计结论          | `§3` manifest 定稿（驱动 jsonl）    |

---

### 步骤 3 — 定稿执行索引 `EXECUTION_INDEX.md`

从模板复制到任务根目录，按节填写（含义见上文「`EXECUTION_INDEX.md` 是什么」）：

| 节   | 执行计划职责                               | 对照本样板文件                         |
| ---- | ------------------------------------------ | -------------------------------------- |
| 文首 | **P0i：`索引完整`**（v4 输入清单门禁）     | 本目录 `EXECUTION_INDEX.md` 第 3 行    |
| §0   | slug、source_card、frozen_card、batch/item | 同上 §0 表                             |
| §0.1 | 活任务卡 AC ↔ Step ↔ 验证链                | 模板有表头；本样板仅演示可省略         |
| §1   | 每步 RED/GREEN 命令 + 证据路径（`9.x`）    | 本样板 §1 一行 `9.0`                   |
| §2   | AC ↔ pytest/命令；§2.1 Tier A/B            | 本样板 §2                              |
| §3   | 必须读原文 manifest（驱动 jsonl）          | 本样板 §3 一行 `GLOBAL_TESTING_POLICY` |
| §4   | 已并入 frozen 的来源                       | 可空                                   |
| §5   | Audit 追溯集                               | 本样板 §5                              |

模板：`C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\spec\guides\templates\EXECUTION_INDEX.md`

### 步骤 4 — 审计与冻结自检

| 文件                            | 作用                                                         |
| ------------------------------- | ------------------------------------------------------------ |
| `AUDIT.plan.md`                 | 薄矩阵；须引用 `EXECUTION_INDEX`；无 `{{占位符}}`            |
| `plan.freeze.md`                | §3.0v4 全 `[x]` 后再 `start`                                 |
| `research/integration-audit.md` | Plan 5d：`六类`、`doc-gap`、`adversarial`、`closure`、`PASS` |

### 步骤 5 — 冻结三件套（机械门）

```powershell
uv run python .trellis/scripts/task.py freeze-task-card .trellis/tasks/your-slug `
  --source docs/implementation_tasks/<ROUND>/<NNN>_*.md
uv run python .trellis/scripts/task.py generate-manifests .trellis/tasks/your-slug
uv run python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/your-slug
```

`validate-plan-freeze` **exit 0** 后，用户批准才可：

```powershell
uv run python .trellis/scripts/task.py start .trellis/tasks/your-slug
```

### 步骤 6 — Execute（冻结后）

Execute agent 读：`frozen/*.md` + `EXECUTION_INDEX.md` + **`implement.jsonl` 每一行** + `context_pack.json`。  
按 frozen **§9** 逐步 TDD；证据写入 `research/execute-evidence/<step>-{red,green}.txt`（路径与索引 §1 一致）。

---

## 活任务卡 ↔ 执行计划对照表

| 活任务卡 `NNN_*.md`       | v4 执行计划落点                                                |
| ------------------------- | -------------------------------------------------------------- |
| §2 预期结果 / AC          | `EXECUTION_INDEX.md` **§2**、§0.1 血缘                         |
| §5–§8 设计/约束（可总结） | `frozen/*.md` 正文；**§4** 登记已内联                          |
| §9 实现步骤（叙述）       | `frozen/*.md` **§9**；**§1** 写 RED/GREEN/证据                 |
| §10–§11 测试与验收命令    | **§2**、§2.1 Tier                                              |
| 契约/模块原文（不可精简） | **§3** manifest → `implement.jsonl`                            |
| Plan 范围输入             | `research/plan-boot.md`、`context_pack.json`（非执行计划正文） |

---

## 本样板目录文件清单（核实用）

根目录：`C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\tasks\_example-plan-v4\`

| 绝对路径                              | 角色                                                      |
| ------------------------------------- | --------------------------------------------------------- |
| `...\README.md`                       | 本文：v4 执行计划产出说明                                 |
| `...\task.json`                       | `status: completed`（只读）；`plan_protocol_version: "4"` |
| `...\EXECUTION_INDEX.md`              | 执行索引 SSOT                                             |
| `...\AUDIT.plan.md`                   | 薄审计矩阵                                                |
| `...\plan.freeze.md`                  | 冻结合并门                                                |
| `...\context_pack.json`               | loop 路由（可为空数组）                                   |
| `...\implement.jsonl`                 | Execute 机器清单（自动生成）                              |
| `...\audit.jsonl`                     | Audit 机器清单                                            |
| `...\check.jsonl`                     | trellis-check 追溯                                        |
| `...\loop_manifest.json`              | complex 轨道 loop 元数据                                  |
| `...\evidence_index.json`             | loop 证据索引（本样板为空壳）                             |
| `...\frozen\GLOBAL_TASK_TEMPLATE.md`  | 冻结任务卡（Execute 正文）                                |
| `...\research\plan-boot.md`           | P0 boot                                                   |
| `...\research\plan-skill-reads.jsonl` | Plan skill 读审计                                         |
| `...\research\integration-audit.md`   | Plan 5d                                                   |

**刻意没有：** `MASTER.plan.md`（v4 不用）、`research/execute-evidence/`（未进入 Execute）。

**引用但不在本目录的仓库文件：**

- `C:\Users\Guang\Desktop\quant-monitor-desk\docs\implementation_tasks\GLOBAL_TASK_TEMPLATE.md`（`source_task_card`）
- `C:\Users\Guang\Desktop\quant-monitor-desk\docs\implementation_tasks\GLOBAL_TESTING_POLICY.md`（索引 §3）

---

## 自检命令

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/_example-plan-v4
```

预期：无错误。仓库测试 `tests/test_execution_index_protocol.py::test_examplePlanV4_passesValidatePlanFreeze` 锁定同一门禁。

---

## 与 Coordinator PLAYBOOK 如何配合

1. **PLAYBOOK** 决定：本 Batch 有哪些 Task ID、建议 branch、并行轨、合并顺序、共享文件锁。
2. **每个被派发的 Trellis 任务** 各自在 `.trellis/tasks/<slug>/` 产出 **v4 执行计划**（本 README 流程）。
3. PLAYBOOK **不替代** `EXECUTION_INDEX`；执行 agent **不默认读** PLAYBOOK，除非 PLAYBOOK 或任务卡显式写入 §3 manifest。

---

## 状态说明

- 本目录 **`status: completed`**：仅供对照与复制结构，**不要** `task.py start`。
- 新建任务请设 `status: planning`，走完上表步骤后再 `start`。
