# 复杂任务规划协议

> **读者：Plan / 规划 agent**（复杂任务启动时读本文精简版）  
> **Execute agent** — 只读 `MASTER.plan.md` + `implement.jsonl`  
> **Audit 编排器 / 维度 agent** — 读 `AUDIT.plan.md` + `audit.jsonl` + MASTER **§2**（A5 追溯）+ Execute **§10 证据只读**  
> **定位**：Trellis 管任务状态、hooks、验收门；**本协议管 Plan 阶段**流程、产出物、Skill 注册表。  
> **语言**：计划与验收用中文；代码标识符、命令、路径保持英文。

---

## 0. 文档分工（必读）


| 文档                                                           | 谁读             | 放什么                                             |
| ------------------------------------------------------------ | -------------- | ----------------------------------------------- |
| **本文** | Plan agent | 流程、产出物、冻结合并、Plan DoD、Skill 注册表 |
| **`MASTER.plan.md`** | Execute | §8 步骤+证据、§9 四层测试、§10 Tier、§11 交接、§12 Execute Skill |
| **`AUDIT.plan.md`** | Audit agent | §1 Skill 冻结 + **§2 维度验证矩阵**；§3 工具/7.pre |
| **`audit.jsonl`** | Audit hook | 第一条 = AUDIT.plan.md；**不含** implement/plan.freeze |
| **`audit.report.md`** | Audit 产出 / Repair 输入 | 各维度结论 + §4.3 修复项 |
| **`REPAIR.plan.md`** | Repair 执行者 | Audit 后修复清单 + Skill 冻结 |
| **`plan.freeze.md`** | Plan | 冻结自检 |
| **`implement.jsonl`** | Execute hook | 第一条 = MASTER |
| **`check.jsonl`** | A1 audit-spec | Spec 合规维度 |
| **execute-skill-registry.md** | Plan 填 §12 | Execute 不读 |
| **audit-skill-registry.md** | Plan 填 AUDIT **§1 + §2** | Audit 不读 |
| **repair-skill-registry.md** | Plan / Audit 后填 REPAIR | Repair 不读词典全文 |


**原则：** Execute → **MASTER**；Audit → **AUDIT.plan.md**；Repair → **REPAIR.plan.md**；Plan 自检 → **plan.freeze.md**。

### 0.1 原计划包（`docs/implementation_tasks/`）— Plan 硬门禁

> **定位：** `docs/implementation_tasks/` = **范围与契约权威**（做什么、边界、输入文件）；`MASTER.plan.md` = **实现方案与验收细节**（怎么做、怎么验）。**禁止**在未读原计划前编写 MASTER §8 或扩大/缩小范围。

**Plan Phase P0（`trellis-plan`）必须按序读取：**

1. `docs/implementation_tasks/README.md`
2. `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
3. `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
4. `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
5. `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md`
6. `docs/implementation_tasks/ROUND_*/README.md`（本任务所属 Round）
7. `docs/implementation_tasks/ROUND_*/DECISIONS.md`（本 Round 已确认决策）
8. 本批 `NNN_*.md` 正式任务卡（及任务卡 §3「输入文件」列出的 specs / architecture / modules 文档）

**Plan 产出（冻结前必存在）：**

- `research/original-plan-trace.md` — 任务编号 ↔ MASTER §2 AC ↔ 引用文档对照表
- `research/plan-boot.md` — 含「原计划已读」摘要 + `Phase P0 complete`
- `MASTER.plan.md` §0「原计划任务」字段 + §1.3「原计划归并表」
- `implement.jsonl` — 必须列入 GLOBAL 四文件 + 本批 `NNN_*.md`（路径须存在；`validate-plan-freeze` 校验）
- 可选 `docs/implementation_tasks/ROUND_*/plans/*.plan.md` — **仅索引**，指向 Trellis `MASTER.plan.md`（Execute 不读 plans 正文）

**冲突处理：** MASTER 与 DECISIONS / 任务卡冲突 → **先更新 DECISIONS 并获用户确认**，再改 MASTER；禁止 silent override。

**祖父条款：** 2026-06-18 前已归档的 Trellis 任务（`.trellis/tasks/archive/`）若无 `original-plan-trace.md`，视为历史交付；**新任务与重新 Plan 的任务**必须遵守本节。

---

## 1. 何时启用

满足 **任意一条** 即走本协议：


| 触发条件         | 示例                    |
| ------------ | --------------------- |
| 跨 2+ 模块/目录   | migration + init + 测试 |
| 有业务规则或数据契约   | schema、审计表            |
| 重构/优化既有逻辑    | 改 migrate runner      |
| 验收需可运行命令     | pytest、dry-run        |
| 预估 ≥ 3 个独立步骤 | —                     |
| 用户要求「深度计划」   | —                     |


**简单任务**（单文件 typo、一行改动）：不启用；无需 `MASTER.plan.md`。

---

## 2. 核心原则

1. **Plan 多文件草稿 → Execute 双入口**：冻结后只认 `MASTER.plan.md` + `implement.jsonl`。
2. **分析先于争论**：GitNexus 摘要后再调 planning skill。
3. **多 skill 分轮、禁止同轮双主笔**（避免 prd 被改乱）。
4. **计划可验收**：无 §10 命令 + DoD → 禁止 `task.py start`。
5. **skill 只贡献章节**，合并进 MASTER；禁止平行任务树。
6. **冻结合并门**：`start` 前完成 MASTER 全文 + 薄索引 + jsonl。

### 2.1 文件策略


| 阶段      | 策略                                                            |
| ------- | ------------------------------------------------------------- |
| Plan 草稿 | 允许多文件：`research/*`、`design.md` / `implement.md` 草稿            |
| 冻结门     | 全文并入 **MASTER**；`prd` / `design` / `implement` 改为 **≤15 行索引** |
| Execute | 必读 MASTER 全文 + implement.jsonl 每条路径                           |



| 薄文件            | 索引内容                      |
| -------------- | ------------------------- |
| `prd.md`       | 「见 MASTER §1–3」+ 3 bullet |
| `implement.md` | 「见 MASTER §8」+ 步骤标题       |
| `design.md`    | 「见 MASTER §4–6」或 N/A      |


`research/`：Execute **默认不读** Plan 分析溯源；**例外：** `research/gitnexus-execute-summary.md`（6.pre 必读）。Audit **例外：** `research/gitnexus-audit-summary.md`。

### 2.2 Execute 契约（Plan 写入 MASTER §0，Execute 不读协议）

Execute agent 须：**Read trellis-execute/SKILL.md** → Phase 0 Boot → 读 MASTER §8–§12 + implement.jsonl → 逐步 §8（execute-evidence）→ §9–§10 证据 → §11 交接 Audit（**不 finish-work**）。

jsonl **第一条必须是 `MASTER.plan.md`**；Plan 应在 implement.jsonl **第二条**追加 `trellis-execute/SKILL.md`（`task.py start` 后 hook 可读）。

用户 Execute 开场白（可复制进 MASTER §0）：

```text
进入 Execute。MUST Read .cursor/skills/trellis-execute/SKILL.md。
Phase 0 Boot（gitnexus-execute-summary + execute-boot + skill-reads）
→ Phase 1 严格 §8.x（execute-evidence/{step}-red/green.txt）
→ §9/§10 → validate-execute-handoff → §11 Audit。勿 finish-work。
```

### 2.3 批次：多简单任务合并为一轮

**可以**，若：共享上下文、单一 §10 验收门、§8 可排序、用户确认合并。

- MASTER §1.3 子交付物表 + §8.1 / §8.2 分节
- 不适用：可独立上线、跨 package、验收无法合并

示范：`.trellis/tasks/06-16-005-schema-init/`

### 2.4 Execute Skill 冻结契约

Plan 冻结时在 **MASTER §12** 写死 Execute 可用 skill；Execute **不得**按 registry 或自觉自选。

| 列 | 含义 |
|----|------|
| Skill | 名称 |
| 本任务 | **必做** / **条件** / **不用**（三选一，禁止留空） |
| 绑定 §8 | 步骤编号或「收尾门禁」 |
| 触发（写死） | 条件 skill 须可判定；必做 skill 填「每步」等 |
| `@` 指令 | 可复制给 agent 的一句话 |
| 已执行 | Execute 逐步勾选 |

**Execute 规则：**

1. 只许 §12 中 **必做** 或 **已触发条件** 的 skill。
2. 禁止 **不用** 或未列入的 skill。
3. §8 每步 Skill 列须与 §12 一致。
4. `execute-skill-registry.md` 仅 Plan 填 §12 时用；Execute **不读**。

**Plan 门禁：** §12 覆盖 registry 默认栈；plan.freeze §3 全勾 → `task.py start`。

### 2.5 Audit 冻结契约

- **A1–A8：一维一子 agent**；Skill 写全；不得自选。
- **A9 风险汇总：主会话编排器执行**（不派发 audit-risk 子 agent）。
- **7.pre（主会话）：** GitNexus/CodeGraph 刷新 → `research/gitnexus-audit-summary.md`；**然后**才派发 A1–A8。
- A1–A8 agent **必须**使用 GitNexus/CodeGraph；**必须**执行 **AUDIT.plan §2** 本维冻结验证（非 MASTER §10 复跑）。
- **ponytail-review** 仅 A2；Execute 禁止。
- 产出 audit.report；**PASS（无 §4.3）** → Phase 9 Finish；**PASS_WITH_FIXES/FAIL** → REPAIR.plan → Phase 8 Repair。

### 2.6 Repair 原则

1. audit.report §4.3 **全部关闭**（或 §4.4 Deferred 且用户批准）。
2. **修根因，不兜底**（禁止 wrapper/假绿/静默降级代替修复）。
3. Repair Skill **必要且精简**（repair-skill-registry）；主会话或 repair-agent 执行。

### 2.7 什么叫「任务完成」

```text
Execute §11 交接 → Audit（7.pre→A1–A8→A9 主会话）→ Repair（若有 §4.3）→ **MASTER §10** 复验 → Finish
```

### 2.8 §10 Tier 与 Audit 验证分工

| 层级 | Execute | Audit |
|------|---------|-------|
| **§10 Tier 表** | **回归门禁**：跑命令、填证据、勾 Execute 列 | **audit-sandbox：默认不复跑同一命令**（正交验证）；**audit-prod-path：例外**——在独立数据副本（`AUDIT_PROD_ROOT`）上复跑 §9 全套 + §10 B/C，验证 Execute 声称在真实数据形状下是否成立；A5 **必**抽检 Execute 证据最弱的 2 行 + 2 个证据文件 |
| **维度验证** | 不做 | **AUDIT.plan §2 冻结**（Skill 见 §1；完整双契约见 **§2.9–§2.10**） |
| **§2 预期结果** | 实现时对照 | A5 逐条 **追溯** 验证链是否成立 |

Audit 的价值在于 **正交维度**（Spec、安全、测缺口、过度工程等），不是重复 Execute 已绿的 pytest。

### 2.9 Execute 验收 vs Audit 维度验证（双契约 · 新增）

Plan 阶段 **同时冻结两套契约**；Execute 侧 **§2.8 与 MASTER §8–§10 不变**。

| | **Execute 验收契约** | **Audit 维度验证契约** |
|--|----------------------|------------------------|
| **冻结位置** | `MASTER.plan.md` §8 / §9 / §10 | `AUDIT.plan.md` §1（Skill）+ **§2 维度验证矩阵** |
| **执行角色** | Execute | A1–A8 各子 agent |
| **核心问题** | 按计划实现了吗？回归绿了吗？ | 从本维度能否证明/否证？Execute 漏了什么？ |
| **与 MASTER §10** | **拥有并执行** §10 | **默认不跑** §10 同行命令 |
| **环境** | §9/§10：local/ci + Execute **prod-path** | §2 各行：**local / audit-sandbox / review-only** |
| **污染控制** | Execute 证据写入正式验收 `DATA_ROOT` | 写库/CLI 维 **必须 audit-sandbox**（见 §2.10） |
| **产出** | §8 证据 + §10 Execute 勾 | `audit.report.md` §2 汇总 + §3.1–§3.8 |
| **Repair 复验** | **复跑 MASTER §10** | 不重跑 §2（除非用户要求复 Audit） |

**A1–A8 维度验证职责（Plan 写入 AUDIT §2 时对照 [audit-skill-registry.md](./audit-skill-registry.md) §2）：**

| 维 | 验证焦点 | 典型验证类型 | 默认环境 |
|----|----------|--------------|----------|
| A1 Spec | diff vs spec；未声明依赖 | static + read-only | local |
| A2 过度工程 | bloat / 可删项 | review-only | — |
| A3 安全 | 威胁面、注入、密钥 | static | local |
| A4 代码质量 | 多轴 review | review-only | — |
| A5 完成情况 | §2 AC 追溯；Execute 证据可信性 + **必做**证据复跑 + 证据文件真实性 + audit-prod-path 完整复验 | trace-ac + cli-sandbox + read-only + audit-prod-path | local / audit-sandbox / audit-prod-path |
| A6 性能 | 资源/延迟/Profiling + 真实数据量级复验 | cli-sandbox + audit-prod-path | audit-sandbox / audit-prod-path |
| A7 运维 | 幂等、日志、回滚 + 真实数据副本验证 | cli-sandbox + audit-prod-path | audit-sandbox / audit-prod-path |
| A8 测试缺口 | 边界/Red Flags **补测** + 真实数据形状验证 | pytest-isolated + audit-prod-path | audit-sandbox / audit-prod-path |

### 2.10 Audit 环境隔离（不污染正式项目）

| 环境档 | 用途 | 谁用 |
|--------|------|------|
| **local/ci** | 单测、lint、静态 grep、review | Execute Tier A；Audit A1–A4 |
| **Execute prod-path** | 项目验收 `DATA_ROOT`；Execute §9 B/C、§10 B/C 证据 | **仅 Execute** |
| **audit-sandbox** | 与 prod **同代码路径与配置加载**，但 `AUDIT_DATA_ROOT` / `.audit-sandbox/` / pytest `tmp_path`；**禁止**写 Execute 证据库或生产库 | **Audit A5（抽检）、A6、A7、A8** |
| **audit-prod-path** | **与生产同配置 + 独立数据副本** `AUDIT_PROD_ROOT`（`cp -r $DATA_ROOT $AUDIT_PROD_ROOT`）；跑完整 §9 单元+集成+管道+E2E + §10 B/C；只读验证，事后清理 | **Audit A5（完整验证）、A6、A7、A8** |

- Audit §2 凡涉及写库/CLI，Plan **必须**写死隔离路径，且 ≠ Execute §10 的 `DATA_ROOT`。
- **禁止** Audit 常规流程直接使用 Execute 已写入的正式验收库做破坏性复跑。
- **audit-prod-path 操作规范：** ① 复制（非共享）生产数据到 `AUDIT_PROD_ROOT`；② 对副本跑 §9 全套 + §10 B/C；③ 使用独立配置环境变量 `AUDIT_PROD_ROOT`，其余配置与生产一致；④ 审计完成后清理 `$AUDIT_PROD_ROOT`。

---

## 3. 流程总览

```text
Phase 0  建任务（task.py create）
Phase 1a 项目轻量概览（GitNexus → research/project-overview.md，≤1 页）
Phase 2  需求与规格（trellis-brainstorm → spec-driven-development；条件 domain-modeling）
Phase 3  质疑补洞（grill-me 或 interview-me，必须二选一；更强替代 grill-with-docs）
Phase 3.5 需求垂直切片（to-issues → 切片工单列表）
Phase 1b 需求聚焦代码分析（GitNexus → research/gitnexus-summary.md，锚定需求）
Phase 4  技术设计（brainstorming 和/或 api-and-interface-design；条件性，跳过须书面理由）
Phase 5  拆解 + 计划（planning-and-task-breakdown → writing-plans → trellis-before-dev → doubt-driven-development）
Phase 5b 冻结合并 MASTER + AUDIT.plan.md + plan.freeze + jsonl（implement / check / audit）
Phase 6  Execute：6.pre GitNexus → MASTER + implement.jsonl；§0.1 门控
Phase 7  Audit：7.pre GitNexus → A1–A8 子 agent → **A9 主会话** → audit.report
Phase 8  Repair（若有 §4.3；REPAIR.plan.md + 必要 skill → 复验 §10）
Phase 9  Finish（audit.report §5 PASS → update-spec / archive）
```

Trellis 命令与 hook 细节见 `.trellis/workflow.md`；`task.py start` = Plan → Execute 评审门。

**与 Trellis workflow 对齐：** `.trellis/workflow.md` Phase 2/3 已映射 Phase 6–9；复杂任务跳过 2.2/3.1 trellis-check，改走 Audit。

---

## 4. 各 Phase：Skill 与产出（禁止跳步）

### Phase 0 — 建任务

- **命令：** `task.py create "<标题>" --slug <短名>`
- **产出：** `task.json`（planning）、种子 `prd.md`
- **下一步 MUST Read：** `.cursor/skills/trellis-plan/SKILL.md`（Phase P0 Boot，含 **P0o 原计划包** `docs/implementation_tasks/`）

### Phase 1a — 项目轻量概览（新 · 在需求分析前）

- **工具：** GitNexus / CodeGraph `query` + `context`（非 skill，必须使用）
- **产出：** `research/project-overview.md`（≤1 页）
- **目的：** 了解技术栈、关键模块、项目结构，给 Phase 2 需求分析提供"这个项目能做什么"的技术可行性基线。**不是深度分析**——深度分析移到 Phase 1b。
- **豁免：** 单文件且路径明确 → MASTER §0 `analysis_waiver: true`（同 Phase 1b 豁免）

### Phase 2 — 需求与规格


| 顺序  | Skill                         | 产出章节              |
| --- | ----------------------------- | ----------------- |
| 2a  | trellis-brainstorm            | MASTER §1–3、§7 初稿 |
| 2b  | spec-driven-development（addy） | MASTER §2 可验证规格   |
| 条件 | **domain-modeling**（mattpocock） | `CONTEXT.md`、`docs/adr/` |

**domain-modeling 触发条件：** 项目缺少 `CONTEXT.md` 或用户使用的领域术语模糊、存在歧义时启用。目的：建立统一领域词汇表，为后续 Phase 的规格和设计提供术语锚点。


### Phase 3 — 质疑与补洞（必须二选一，禁止跳过）

- `grill-me`（mattpocock）或 `interview-me`（addy）→ MASTER §3 边界、§7 Red Flags
- **更强替代：** `grill-with-docs`（mattpocock）——当项目已有领域模型（`CONTEXT.md`/`ADR`）时，以模型为锚点质问计划，产出同上 + 更新 `CONTEXT.md`/`ADR`
- **硬门禁：** Phase 3 必须产出质疑记录（`research/grill-me-session.md` 或等价），此项在 `plan.freeze.md` 中检查

### Phase 3.5 — 需求垂直切片（新 · to-issues）

- **Skill：** `to-issues`（mattpocock）
- **产出：** 垂直切片工单列表（每个切片 = 贯穿所有层的完整通路 + AC + 显式依赖声明）
- **核心价值：** 在技术设计之前，将每个功能需求拆成可独立 demo 的垂直切片，显式声明切片间依赖。防止"执行阶段只设计了一小部分"——每个切片如果不可独立 demo，说明不完整
- **产出流向：** 切片工单列表 → 反哺 Phase 5a `planning-and-task-breakdown` 生成 MASTER §8 步骤

### Phase 1b — 需求聚焦代码分析

- **工具：** GitNexus / CodeGraph `query` + `impact` + `context`（非 skill，必须使用）
- **产出：** `research/gitnexus-summary.md`（需求锚定的摘要，按 Phase 3.5 切片分组）
- **与 Phase 1a 的区别：** Phase 1a 回答"项目是什么？"（轻量，≤1 页）；Phase 1b 回答"现有代码能复用多少？哪些要重构？哪些要新写？"（深度，聚焦需求）
- **豁免：** Phase 1a 豁免者同步豁免 Phase 1b → MASTER §0 `analysis_waiver: true`

### Phase 4 — 技术设计（条件性 · 跳过须书面理由）


| 条件                    | Skill                              | 产出                      |
| --------------------- | ---------------------------------- | ----------------------- |
| 一般复杂                  | Superpowers `brainstorming`        | design 草稿 → MASTER §4–6 |
| **API / 模块边界 / 公共契约** | **api-and-interface-design**（addy） | MASTER §6 接口契约          |
| 模块级设计（条件） | **codebase-design**（mattpocock） | 深度模块接口设计 |
| 高风险设计验证（条件） | **prototype**（mattpocock） | 可丢弃原型 + 设计决策记录 |
| 可跳过                   | —                                  | §8 已足够清晰                |

**跳过条件（以下三条全部满足才可跳过，须在 MASTER §0 注明）：**

1. 任务**不创建**新的模块/package 目录
2. 任务**不定义**会被 ≥2 个 caller 调用的新公共函数/类/接口
3. 任务**不涉及**数据 schema（表结构/migration）变更

任一条件不满足 → Phase 4 必须执行。跳过时在 MASTER §0 写：`skip_phase4_reason: 三条全满足 — 无新模块/无新公共接口/无 schema 变更`。

**codebase-design 触发条件：** 需设计新的模块接口或对现有模块进行深度重构时启用。核心概念：Depth（接口小、实现深）、Seam（可替换点）、Leverage（调用方获得的能力密度）。

**prototype 触发条件：** 设计中有高风险不确定项（数据模型是否正确？状态机逻辑是否合理？）需要可丢弃原型验证时启用。


### Phase 5 — 拆解、jsonl 与 Execute Skill 冻结

| 顺序 | Skill | 产出 |
| --- | --- | --- |
| 5a | planning-and-task-breakdown（addy） | MASTER §8 依赖与切片 |
| 5b | writing-plans（Superpowers） | MASTER §8 逐步 + **RED/GREEN 命令与证据列**（**禁止**内嵌完整测试；放 `research/`） |
| 5c | trellis-before-dev | MASTER §5–6；`implement.jsonl` / `check.jsonl` |
| **5d** | **doubt-driven-development**（addy，**必做**，主会话） | 对抗审查 §6–8；修订 MASTER §7/§8/§12 + **AUDIT §1/§2**；记录 **plan.freeze.md** |

**5d 必做说明：** 冻结前 fresh-context 对抗审查（CLAIM → DOUBT → RECONCILE）。须主会话；子 agent 不可执行 5d。

**Phase 5b 冻结（必做）：**

1. design/implement 草稿并入 MASTER
2. 薄索引 prd / design / implement
3. 填写 **MASTER §8–§12、§9 四层、§10 Tier**
4. 填写 **`AUDIT.plan.md` §1**（Skill）+ **§2 维度验证矩阵**（A1–A8 全覆盖）+ **`audit.jsonl`**
   - **人工：** 将 §2 中所有 `{{}}` 换成本任务真实命令/路径（见 AUDIT 模板 **§2.1**）；无性能要求则 A6 按 **§2.2** 写 SKIP，勿留 perf 占位
5. 填写 **`plan.freeze.md`**（含 **§3.0 双契约 one-pager** 全勾）
6. `implement.jsonl` 第一条 = MASTER（**勿**含 AUDIT / plan.freeze）
7. plan.freeze §3 全勾 → **`task.py validate-plan-freeze`** exit 0 → 用户批准 → `task.py start`

**Plan protocol v2（机械门禁）：** Phase P0 → `plan-boot.md` + `plan-skill-reads.jsonl` + `gitnexus-summary.md`；详见 `.cursor/skills/trellis-plan/SKILL.md` 与 `plan-skill-paths.yaml`。

### Phase 6 — Execute

| 步骤 | 执行者 | 内容 |
|------|--------|------|
| **6.pre** | **主会话或 Execute** | GitNexus/CodeGraph 刷新 → `research/gitnexus-execute-summary.md` |
| 6.x | Execute | MASTER §0.1 逐步循环 + implement.jsonl；§8 RED/GREEN 证据、§9/§10；`validate-execute-handoff`；§11 交接 Audit |

**6.pre：** 聚焦 implement.jsonl 触点；Execute 读摘要 + 至少 1 次 GitNexus/CodeGraph 查询；`analysis_waiver` 可豁免。

### Phase 7 — Audit

| 步骤 | 执行者 | 内容 |
|------|--------|------|
| **7.pre** | **主会话** | GitNexus/CodeGraph 刷新 → `research/gitnexus-audit-summary.md` |
| 7.0 | 主会话 | 汇总 **AUDIT §2 各维证据** + Execute §10 证据索引（只读）→ audit.report §2 |
| 7.1–7.8 | **A1–A8 子 agent** | 执行 **AUDIT.plan §2** 本维验证 + GitNexus/CodeGraph → audit.report §3.x |
| **7.9 A9** | **主会话** | 汇总风险、§4 结论、§4.3 修复项（**非子 agent**） |
| 7.out | 主会话 | PASS（无 §4.3）→ Phase 9；PASS_WITH_FIXES/FAIL → 写 **REPAIR.plan.md** → Phase 8 |

### Phase 8 — Repair

- **输入：** audit.report §4.3 + **REPAIR.plan.md**（主会话 Audit 后编写）
- **执行：** 主会话或 `repair-agent`；Skill 见 REPAIR.plan §2（systematic-debugging + TDD + verification 等）
- **原则：** §2.6 修根因；Deferred 仅 §4.4
- **产出：** audit.report §5 复验 **MASTER §10** → Phase 9

### Phase 9 — Finish

audit.report §5 PASS + 无未关 §4.3 → trellis-update-spec → archive → finish-work。

---

## 5. planning-with-files

**默认不启用。** 仅 Plan 会话极长时用 `research/findings.md` 作缓冲，结论合并进 MASTER。**禁止**用 `task_plan.md` 替代 MASTER。

---

## 6. 文件清单

### Plan 草稿（合并前）


| 文件                              | 用途             |
| ------------------------------- | -------------- |
| `research/*` | 溯源；Execute 默认不读 | 例外见 §2.1（gitnexus-*-summary.md） |
| `design.md` / `implement.md` 草稿 | 合并进 MASTER     |
| `acceptance.feature`            | 可选 → MASTER §2 |


### Plan 冻结专用（Execute 不读）


| 文件 | 读者 | 说明 |
|------|------|------|
| **`plan.freeze.md`** | Plan agent | Skill 记录、贡献溯源、**冻结自检**（`task.py start` 前全勾） |
| `research/*` | Plan 溯源；Execute 默认不读 | 例外：`gitnexus-execute-summary.md`（6.pre）；`gitnexus-audit-summary.md`（7.pre） |


### Execute 入口

| 文件 | 读者 | 说明 |
|------|------|------|
| `MASTER.plan.md` | Execute | §0.1 门控、§8–§12、§9–§10 |
| `implement.jsonl` | Execute hook | 第一条 = MASTER |

### Audit / Repair 入口

| 文件 | 读者 | 说明 |
|------|------|------|
| `AUDIT.plan.md` | Audit 编排 + A1–A8 | §1 Skill + **§2 维度验证矩阵**；A9=主会话 |
| `audit.jsonl` | Audit hook | 第一条 = AUDIT.plan.md |
| `audit.report.md` | Audit/Repair/Finish | §3 维度 + §4.3 修复项 + §5 复验 |
| `REPAIR.plan.md` | Repair（Audit 后按需） | 修复清单 + Skill 冻结 |
| `check.jsonl` | A1 audit-spec | Spec 路径 |


### 6.1 implement.jsonl 约定

每行 JSON：`{"file": "<路径>", "reason": "<原因>"}`；目录加 `"type": "directory"`。

最小示例（完整示范见 `.trellis/tasks/06-16-005-schema-init/implement.jsonl`）：

```jsonl
{"file": ".trellis/tasks/<slug>/MASTER.plan.md", "reason": "【必读·第1条】执行全文"}
{"file": "docs/DECISIONS.md", "reason": "范围决策"}
{"file": "backend/app/db/migrate.py", "reason": "实现触点"}
```

追加：`python .trellis/scripts/task.py add-context <slug> implement <path> "<reason>"`

---

## 7. Skill 注册表

> **地位**（稳定）。**Execute 用哪些 skill → Plan 冻结写死 MASTER §12；§8 逐步与 §12 对齐。**

### 7.1 Plan 阶段


| Skill                              | 地位              | Phase            |
| ---------------------------------- | --------------- | ---------------- |
| trellis-brainstorm                 | 需求主笔            | 2                |
| spec-driven-development（addy）      | 可验证规格           | 2                |
| **domain-modeling**（mattpocock）    | **领域词汇表**       | 2（条件）           |
| grill-me / interview-me            | 质疑补洞            | 3                |
| **grill-with-docs**（mattpocock）    | **以模型锚点质问**    | 3（更强替代）        |
| **to-issues**（mattpocock）          | **需求垂直切片**      | **3.5（必做）**     |
| Superpowers brainstorming          | 技术设计草稿          | 4                |
| **api-and-interface-design**（addy） | **API/模块契约**    | 4（条件）            |
| **codebase-design**（mattpocock）    | **深度模块接口设计**   | 4（条件）            |
| **prototype**（mattpocock）          | **可丢弃原型验证**    | 4（条件）            |
| planning-and-task-breakdown（addy）  | 原子任务与依赖         | 5                |
| writing-plans（Superpowers）         | 可执行步骤           | 5                |
| trellis-before-dev                 | 对齐 spec、写 jsonl | 5                |
| **doubt-driven-development**（addy） | **§6–8 对抗审查（必做）** | **5d** |
| planning-with-files                | 调研缓冲            | 可选               |


**Plan 不要启用：** Superpowers 全套编排、Execute 用 brainstorming。

**context-engineering（addy）：** 不单独 invoke；jsonl 策展 + MASTER 单源即其落地。

**始终 User Rule：** karpathy-guidelines、testing-guidelines

### 7.2 Execute 阶段（Plan 填 §12 时的候选池）

> **Execute 不自选。** 下表供 Plan 冻结 §12 时查阅；每 skill 须在 §12 标 **必做 / 条件 / 不用**。

| Skill | 典型绑定 | Plan 默认建议 |
| ----- | -------- | ------------- |
| test-driven-development | §8 每步写代码 | 复杂任务 → **必做** |
| incremental-implementation | §8 多文件切片 | 跨文件 → **必做** |
| source-driven-development | §8 框架 API 步 | 有 DuckDB/React 等 → **条件**（写死步骤） |
| systematic-debugging | 测试失败 | **条件**（触发=RED 未通过） |
| trellis-implement | 派发子 agent | **必做** 或 inline **不用** |

**Execute 不含：** trellis-check、ponytail-review、verification-before-completion（→ Audit：**Skill** 在 AUDIT §1，**验证** 在 AUDIT §2）

候选词典 → [execute-skill-registry.md](./execute-skill-registry.md)

### 7.3 Audit 阶段（Plan 填 AUDIT.plan.md §1 + §2）

> **一维一 agent。** §1 = Skill；**§2 = 维度验证矩阵**（A1–A8 全覆盖，与 MASTER §10 分离）。

| 维度 | 典型 Agent | 冻结位置 |
|------|------------|----------|
| A1–A8 | audit-* 子 agent | AUDIT §1 Skill + **§2 验证行** |
| **A9** | **主会话** | 汇总 §3 → §4 |

候选词典 → [audit-skill-registry.md](./audit-skill-registry.md) §1–§2

### 7.4 Repair 阶段（Audit 后 · REPAIR.plan.md）

| Skill | Repair 默认 |
|-------|-------------|
| systematic-debugging | 有缺陷时 **必做** |
| test-driven-development | **必做** |
| verification-before-completion | 收尾 **必做** |
| incremental / source-driven / security | **条件**（写进 REPAIR.plan §2） |

词典 → [repair-skill-registry.md](./repair-skill-registry.md)

---

## 8. Plan 完成定义（`task.py start` 前）

> 逐项勾选：**`plan.freeze.md` §3**（**§3.0 one-pager** 优先扫）

- [ ] MASTER **§0.1 门控** + §8–§12、§9 四层必做、§10 Tier 含 B/C prod-path
- [ ] **§8 每步含 RED/GREEN 命令与证据列**；完整测试正文在 `research/`，不在 MASTER
- [ ] **`python .trellis/scripts/task.py validate-plan-freeze <dir>`** exit 0
- [ ] **AUDIT.plan.md §1** Skill + **§2 维度验证矩阵**（A1–A8；**§2 无 `{{}}`** 或 A6 已 §2.2 SKIP）
- [ ] **Plan 人工：** AUDIT §2 占位已按真实任务替换；无 perf 则 A6 SKIP（见 `plan.freeze.md` §2.5）
- [ ] Repair 模板路径已知（Audit 后按需生成 REPAIR.plan.md）
- [ ] **audit.jsonl** 第一条 = AUDIT.plan.md
- [ ] implement.jsonl 第一条 = MASTER；三者不含 plan.freeze
- [ ] Phase 5d 完成；plan.freeze §3 全勾；用户批准

---

## 9. 相关文档


| 文档               | 路径                                                                           |
| ---------------- | ---------------------------------------------------------------------------- |
| MASTER 模板 | [templates/MASTER.plan.md](./templates/MASTER.plan.md) |
| **AUDIT 模板** | [templates/AUDIT.plan.md](./templates/AUDIT.plan.md) |
| audit.report 模板 | [templates/audit.report.md](./templates/audit.report.md) |
| Plan 冻结自检 | [templates/plan.freeze.md](./templates/plan.freeze.md) |
| Execute Skill 词典 | [execute-skill-registry.md](./execute-skill-registry.md) |
| **Audit Skill 词典** | [audit-skill-registry.md](./audit-skill-registry.md) |
| **Repair 模板/词典** | [templates/REPAIR.plan.md](./templates/REPAIR.plan.md) · [repair-skill-registry.md](./repair-skill-registry.md) |
| Trellis 工作流      | `.trellis/workflow.md`                                                       |
| 冻结合并示范           | `.trellis/tasks/06-16-005-schema-init/`                                      |
| ROUND 源计划        | `docs/implementation_tasks/ROUND_1_DATA_FOUNDATION/plans/005_schema.plan.md` |


---

**核心原则**：Plan 阶段宁可多写可验收的一页，Execute 阶段少返工一小时。