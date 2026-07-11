# Agent 工具链路由（quant-monitor-desk · 全员必读）

> **SSOT：** 本文件（仓库根 `agent-toolchain.md`）  
> **完整个人路由：** 桌面 `skill路由.txt`（本文件只收录**本仓库高频、高 context 加载**的 skill，降 cognitive load）  
> **task 目录指针：** `task/agent-toolchain.md`（勿在此重复维护）

## 禁止裸执行

非一问一答的仓库任务（写码、改码、审码、调试、关账、多步 task 等）**禁止裸执行**：

1. **必须先 Read** 本文件 `agent-toolchain.md`（或确认本会话已读过且任务类型未变）。
2. 按 **Step 1** 定分支，再 **按需 Read / @** 对应 skill（见下文索引）；用户已 `@` 的 skill 视同已选分支。
3. **禁止**跳过本文件、不加载 skill，直接凭直觉改仓库。

**完成条件**：能说出「本步走的分支、已加载的 skill、跳它会丢什么闸门」。

---

```
Task Progress:
- [ ] Step 1 定分支 — 能说清：澄清 / 规划 / 实现 / 查码 / 调试 / 审查 / 写 skill
- [ ] Step 2 走管线 — 按顺序 @ skill，不跳闸门
- [ ] Step 3 落 skill — 从下表选中一个并 @ 它（user-invoked 为主）
```

**完成条件**：能回答「我现在在第几步、下一个 skill 叫什么、跳它会丢什么」。

---

## 始终生效（任何 skill 之前）

来自 `using-agent-skills` + 本仓库 `project-global.md`：

| 行为        | 要求                                                               |
| ----------- | ------------------------------------------------------------------ |
| 假设外显    | 非平凡任务先列 ASSUMPTIONS，让用户纠错                             |
| 困惑即停    | 规格/边界矛盾 → 命名困惑点，禁止静默猜                             |
| 范围手术    | 只改本票允许触及；不顺手「清理」邻域                               |
| 验证关门    | `uv run pytest -q` exit 0；无「看起来对」                          |
| 权威 design | 规格以 `**/design/**` + `MIGRATION_MAP.md` 为准；runtime 非 design |

---

## Step 1：定分支（本仓库优先）

```
任务到达
    │
    ├── scope / AC / 边界说不清？ ───────→ grill-me / interview-me / grilling
    │
    ├── 多步 task、要落盘计划？ ─────────→ planning-with-files（task/*/三件套）
    │
    ├── 新功能 / 本票 R4 实现？ ─────────→ 【管线 A】见下
    │
    ├── 只查代码怎么工作？ ───────────────→ gitnexus-exploring（GitNexus 优先）
    │
    ├── 改 symbol、怕踩调用方？ ─────────→ gitnexus-impact-analysis → 再实现
    │
    ├── 出 bug / pytest 红？ ─────────────→ diagnosing-bugs → debugging-and-error-recovery → gitnexus-debugging
    │
    ├── 对照契约 / specs 实现？ ──────────→ source-driven-development
    │
    ├── 非平凡架构决策？ ─────────────────→ doubt-driven-development
    │
    ├── 审代码 / 关账 findings？ ─────────→ code-review-and-quality
    │
    ├── 写 / 改 agent skill？ ───────────→ create-skill → writing-great-skills → skill-creator
    │
    └── 完全不知道用哪个？ ─────────────→ using-agent-skills（全生命周期 meta）
```

---

## 管线 A：本仓库 task 票实现（01–19）

**Leading word — 垂直切片**：每票 `task-XX-*/` 独立 R4，先上游关账再下游。

```
planning-with-files          读/写 task_plan · findings · progress
    │
    ▼
grill-me（说不清时）          AC / 边界 / 范围问清再写码
    │
    ▼
spec-driven-development      验收标准先于代码（对齐 README 权威文件）
    │
    ▼
planning-and-task-breakdown  本票允许触及路径 + 依赖（GitNexus impact）
    │
    ▼
incremental-implementation   薄切片实现（ponytail）
    ├── source-driven-development   specs/contracts · design 对照
    ├── doubt-driven-development    非平凡决策对抗性复审（可选）
    └── context-engineering         长会话喂对上下文（可选）
    │
    ▼
test-driven-development      RED → GREEN；测试读 testing-guidelines
    │
    ▼
code-review-and-quality      findings ledger 关账前审查
    │
    ▼
uv run pytest -q             全绿 exit 0
```

**Matt 等价（可 cherry-pick）**：`implement` + `tdd` + `code-review` — 日常 TDD 循环更轻；Addy 管线闸门更全。

---

## 高频 · 高加载 Skill 索引

> 写法：`create-skill` 的 **WHAT + WHEN**（第三人称 description 体）；只列本仓库常 @ 的项。  
> **Invocation**：除 `using-agent-skills` 外均为 **user-invoked**（手动 @），避免 context 常驻。

### 澄清与规划

| skill                         | WHAT                                                             | WHEN                                                          |
| ----------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------- |
| `grill-me`                    | 在对话里追问 scope/AC/边界，澄清后再执行                         | scope、完成条件、规则约束任一说不清；**禁止**自问自答         |
| `interview-me`                | 从模糊意图抽出可验收需求                                         | 不知道「到底要什么」、尚无 spec                               |
| `grilling`                    | 持续追问逼清假设                                                 | 需求仍含未验证假设                                            |
| `planning-with-files`         | 用 `task_plan.md` / `findings.md` / `progress.md` 作磁盘工作记忆 | 多步 task、审计关账、跨会话接续；**本仓库每票目录已建三件套** |
| `planning-and-task-breakdown` | 拆成可验证小步 + 依赖                                            | 开工前收窄「允许触及」、排执行顺序                            |
| `spec-driven-development`     | 验收标准与假设先于代码                                           | 新行为、新票 R4、改 AC 前                                     |
| `using-agent-skills`          | 全生命周期 skill 发现与阶段闸门                                  | 完全不知道下一步该 @ 谁                                       |

### 实现与验证

| skill                           | WHAT                                | WHEN                                       |
| ------------------------------- | ----------------------------------- | ------------------------------------------ |
| `incremental-implementation`    | 薄垂直切片，每片可跑可验            | 正式写码；配合 ponytail + project-global   |
| `implement`                     | Matt 实现循环（内驱 tdd + review）  | 偏好 Matt 轻量循环、tracer bullet 切片     |
| `test-driven-development`       | 先红后绿再重构                      | 正式代码（非测试套测试）；五字段 docstring |
| `tdd`                           | Matt 系 TDD + tracer bullet         | 跟 `implement` 同窗口                      |
| `testing-guidelines`            | 本仓库测什么/不测什么/五字段/闸门   | **每个** `test_*` 写前必读                 |
| `source-driven-development`     | 对照官方文档与 specs 实现，非凭记忆 | `specs/contracts`、外部 API、design 新字段 |
| `doubt-driven-development`      | CLAIM→DOUBT→RECONCILE 对抗性复审    | 架构触点、破坏性变更、多方案取舍           |
| `context-engineering`           | 精简、相关、可执行的上下文          | 长会话、多文件 implement 前                |
| `debugging-and-error-recovery`  | 复现→定位→修复→护栏                 | pytest 红、运行时异常                      |
| `diagnosing-bugs`               | 五步系统化排错                      | 与上叠加；症状→根因                        |
| `browser-testing-with-devtools` | DevTools MCP 运行时验证             | 前端/浏览器行为验收                        |

### 审查与关账

| skill                     | WHAT                                   | WHEN                          |
| ------------------------- | -------------------------------------- | ----------------------------- |
| `code-review-and-quality` | 五轴审查（正确性/可读/架构/安全/性能） | findings 关账、PR、大 diff 前 |
| `code-review`             | Matt 双轴（Standards + Spec）          | `implement` 收尾或轻量审 PR   |
| `code-simplification`     | 行为不变降复杂度                       | review 后、ponytail 还债      |

### GitNexus（查码 · 改码 · 审码）

**Leading word — 知识图谱**：改前先查图。索引过期 → `node .gitnexus/run.cjs analyze`。

| skill                      | WHAT                                | WHEN                                               |
| -------------------------- | ----------------------------------- | -------------------------------------------------- |
| `gitnexus-guide`           | GitNexus 工具/MCP/子 skill 选型     | 不熟 GitNexus、不知调哪个工具                      |
| `gitnexus-cli`             | analyze / status / clean / wiki     | 首次进仓、索引 stale、大改后                       |
| `gitnexus-exploring`       | 架构、执行流、「X 怎么工作」        | 不熟模块、找入口；**优先于盲 grep**                |
| `gitnexus-impact-analysis` | 改前 blast radius、`detect_changes` | **改任何 function/class 前**；HIGH/CRITICAL 须警告 |
| `gitnexus-debugging`       | 症状→调用链→嫌疑 symbol             | 栈/流程对不上                                      |
| `gitnexus-refactoring`     | rename / extract / split（图感知）  | 结构变更；改前常叠 impact                          |
| `gitnexus-pr-review`       | PR diff→流程→风险                   | 与 code-review 叠加                                |

**查码顺序**：GitNexus（`query` / `context` / `impact`）→ 不够再 `grep` / Read。  
**禁止**：未查就猜接口；find-replace 改名。

| 场景            | 用                                          | 不用          |
| --------------- | ------------------------------------------- | ------------- |
| 不熟模块        | `query` + `gitnexus-exploring`              | 全库盲 grep   |
| 改函数/类前     | MCP `impact()` + `gitnexus-impact-analysis` | 直接改        |
| 提交前          | MCP `detect_changes()`                      | 只看 git diff |
| rename / 拆模块 | MCP `rename` + `gitnexus-refactoring`       | find-replace  |

### 写 Skill（三件套）

| skill                  | WHAT                                                  | WHEN                      |
| ---------------------- | ----------------------------------------------------- | ------------------------- |
| `create-skill`         | 目录结构、frontmatter、description、工作流模板        | 新建 skill 的第一份草稿   |
| `writing-great-skills` | predictability、leading word、router、invocation 取舍 | 写好、省 context、可发现  |
| `skill-creator`        | 草稿→eval→迭代→description 优化                       | 要验证 skill 触发率与质量 |

**顺序**：create-skill（怎么建）→ writing-great-skills（怎么写好）→ skill-creator（怎么验）。

### 本仓库横向（按需）

| skill                               | WHAT                     | WHEN                            |
| ----------------------------------- | ------------------------ | ------------------------------- |
| `deprecation-and-migration`         | 安全下线、双轨、迁移用户 | deprecate/remove、破坏性 API    |
| `observability-and-instrumentation` | 日志/RED/追踪/症状告警   | ops 写路径、pipeline AC 要审计  |
| `documentation-and-adrs`            | 记 why、ADR 留档         | 改 MIGRATION_MAP 索引、架构决策 |
| `git-workflow-and-versioning`       | 原子提交、干净历史       | 用户明确要求 commit 时          |

---

## 文档导航（本仓库）

| 场景                       | 先读                                                 |
| -------------------------- | ---------------------------------------------------- |
| 流水线顺序 / 每票边界      | `task/TASK_PIPELINE_INDEX.md`、各票 `README.md`      |
| Agent skill 路由（本文件） | `agent-toolchain.md`                                 |
| 不熟仓库                   | `openwiki/quickstart.md`                             |
| 契约 / schema / registry   | `specs/contracts/`、`specs/`（**权威**在 `design/`） |
| 模块设计                   | `docs/modules/design/`、`MIGRATION_MAP.md`           |
| 领域术语                   | `CONTEXT.md`、`docs/adr/`                            |

**优先级：** `MIGRATION_MAP` 索引 design > specs design > runtime 镜像 > 其他叙述。

---

## grill-gate（澄清门 · 硬约束）

scope / AC / 边界说不清 → Read `grill-me` → **对话里问用户** → 收到明确回复后再写码。

**禁止**：猜意图、自问自答、未问就写「用户认为…」。

---

## 同类区别（本仓库常混）

| 对比     | 选 A                                           | 选 B                                              |
| -------- | ---------------------------------------------- | ------------------------------------------------- |
| TDD      | `test-driven-development`（Addy / 全生命周期） | `tdd`（Matt / implement 循环）                    |
| 实现     | `incremental-implementation`（闸门全）         | `implement`（Matt 轻量）                          |
| 审查     | `code-review-and-quality`（五轴 + 关账）       | `code-review`（Matt 双轴）                        |
| 澄清     | `grill-me`（本仓库规则硬门）                   | `interview-me`（更早、更宽）                      |
| 计划落盘 | `planning-with-files`（三件套）                | `planning-and-task-breakdown`（拆步无强制三文件） |
| 调试     | `debugging-and-error-recovery`                 | `diagnosing-bugs` → 仍不明 + `gitnexus-debugging` |

---

## Invocation 备忘

| 类型          | 机制                                             | 本文件收录 skill                            |
| ------------- | ------------------------------------------------ | ------------------------------------------- |
| user-invoked  | 手动 `@` / `/`，`disable-model-invocation: true` | **绝大多数**（含 GitNexus、grill-me、TDD）  |
| model-invoked | description 常驻，agent 可自动发现               | `using-agent-skills`（全库 meta）；慎用增多 |
| router        | 本文件 + 桌面 `skill路由.txt`                    | 降 cognitive load，**不替代**具体 skill     |

---

## 一句话选型（本仓库）

- **开工某票**：`planning-with-files` → README 权威对齐 → `test-driven-development` + `testing-guidelines` → `gitnexus-impact-analysis`（改码前）
- **说不清**：`grill-me`（硬门）
- **查码**：`gitnexus-exploring` → `impact` → 再写
- **关账**：findings ledger 全 disposition + `uv run pytest -q`
- **写 skill**：`create-skill` + `writing-great-skills` + `skill-creator`
- **迷路**：`using-agent-skills` 或桌面完整 `skill路由.txt`
