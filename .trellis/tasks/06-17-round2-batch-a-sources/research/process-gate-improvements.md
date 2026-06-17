# 流程防跳步改造建议 — Plan + Execute 双端

> **读者：** 维护 Trellis 工作流 / 写下一批 MASTER 的 Plan agent / Execute agent  
> **背景：** Batch A 在 Plan 与 Execute 均出现「交付正确但流程欠账」——根因是**契约写了、门禁没 enforce**。

---

## 1. 根因（为什么 Plan 和 Execute 都会跳步）

```text
Plan 产出「可复制的实现规格书」(§8 TDD 全文)
        ↓
Agent 把 §8 当「一次性粘贴清单」而非「逐步门禁」
        ↓
§12 Skill / User Rule / GitNexus 与 MASTER 优先级冲突 → Agent 选最快的路（全量实现 + pytest 绿）
        ↓
plan.freeze §3.1 要求 §8「证据列」但 task.py start 不校验 → 带缺陷的 MASTER 也能开工
        ↓
Execute 复杂任务故意不用 trellis-check → 主会话 inline 无 hook 注入 Execute 循环协议
```

| 层级 | 已有设计 | 实际缺口 |
|------|----------|----------|
| **模板** | `templates/MASTER.plan.md` §8 有 **证据 / Skill / 环境** 列 | Batch A MASTER 用旧式「Step + 验证」表，**无证据列、无 RED 命令** |
| **Plan 冻结** | `plan.freeze.md` §3.1 勾选项 | **`task.py start` 不跑冻结校验**，Plan 可跳过 5d/证据列 |
| **Execute 协议** | §0.1「无证据 = 未执行」 | **无脚本/hook 阻止**未填证据就 finish-work |
| **Skill 路由** | `execute-skill-registry.md` 分工清晰 | **User Rule**（Karpathy/testing）与 **AGENTS.md**（GitNexus impact）**未写入 §12**，Agent 不知道在复杂任务里谁优先 |
| **Hook** | `inject-subagent-context.py` 注入 implement | **主会话 inline Execute 不走 hook**；`build_implement_prompt` **未注入 §12 逐步协议** |
| **§8 内容形态** | TDD 要求垂直切片 | Plan 把 **整文件测试正文** 放进 §8 → **鼓励水平切片**（与 `tdd` skill 直接冲突） |

---

## 2. 改造原则（三条）

1. **规格与流程分离：** §8 只写 *tracer 测试名 + 通过条件*；完整测试正文放 `plans/` 或 `research/`，Execute **逐步**展开。  
2. **门禁工具化：** 能脚本检查的（证据文件、RED 日志、`{{}}` 占位）在 `task.py start` / `task.py validate` 硬失败。  
3. **主会话与 sub-agent 同协议：** inline Execute 与 `trellis-implement` 收到**同一份** §8 逐步循环注入（session hook 或 AGENTS.md）。

---

## 3. 按文件修改清单（优先级 P0 → P2）

### P0 — 不改则下一批仍会跳步

#### 3.1 `.trellis/spec/guides/templates/MASTER.plan.md`

**改什么：**

| 位置 | 修改 |
|------|------|
| **§8 每步表格** | 强制列：`RED 命令` · `RED 证据路径` · `GREEN 命令` · `GREEN 证据路径` · `绑定 §12 Skill` · `已执行` |
| **§8 顶部说明** | 新增：**禁止**在 MASTER 内嵌 >1 个完整测试函数；仅允许 tracer 测试名 + 「详见 `research/§8.x-tests.md`」 |
| **§0.1** | 增加 **Execute 逐步循环**（见 §5 模板文案） |
| **§12 表格** | 增加列：`证据文件`；必做行须含 `karpathy-guidelines` · `testing-guidelines` · `gitnexus-impact`（或写进 §0.1 User Rule 映射） |

**目的：** 新任务 Plan 不再产出「一次性粘贴型」§8。

---

#### 3.2 `.trellis/spec/guides/complex-task-planning-protocol.md`

**改什么：**

| Phase | 修改 |
|-------|------|
| **Phase 5 writing-plans** | 明确：**§8 ≠ 测试源码仓库**；完整 pytest 放 `research/` 或分批 RED 时写 |
| **§8 Plan 完成定义** | 增加：`python task.py validate-freeze <dir>` exit 0 |
| **§7.2 Execute Skill** | 补充：User Rule 两 skill **必须**在 §12 或 §0.1 显式列出，不得仅依赖 Cursor 全局 rule |

---

#### 3.3 `.trellis/scripts/task.py` + **新建** `validate_plan_freeze.py`

**改什么：**

- `cmd_start`：若存在 `MASTER.plan.md`，start 前调用 `validate_plan_freeze`；失败则 **拒绝** `planning → in_progress`（可 `--force` 给人工 override）。
- **校验项（机器可读）：**
  - §8 每步含 `RED`/`GREEN`/`证据` 关键字或 frontmatter
  - §10 无 `{{`
  - `implement.jsonl` 第一条指向 MASTER
  - `plan.freeze.md` §3 全 `[x]`（或 §3.0 one-pager 全勾）
  - AUDIT.plan §2 无 `{{`

**目的：** Plan 阶段欠账在 **start 前** 挡住（Batch A 若在 start 前有此脚本，MASTER 缺证据列会被拒）。

---

#### 3.4 `.cursor/agents/trellis-implement.md`

**改什么：**

在 **Workflow** 增加 **Execute 逐步协议**（与 §5 相同），并写明：

1. 读 MASTER **§0.1 + §12**（不只 §8 代码块）
2. 每 §8 步：**先 RED 命令 → 粘贴/写入证据 → 再 GREEN**
3. 改 symbol 前 **GitNexus impact**；提交前 **detect_changes**
4. 复杂任务 **禁止** dispatch trellis-check；§11 交接 Audit
5. 开工前读 **Karpathy + testing-guidelines**（User Rule 落地）

**目的：** sub-agent 路径有硬协议。

---

#### 3.5 `.cursor/hooks/inject-subagent-context.py`

**改什么：**

| 函数 | 修改 |
|------|------|
| `get_implement_context` | 若存在 `{task}/MASTER.plan.md`，**始终注入**（不仅靠 implement.jsonl 第一条） |
| `build_implement_prompt` | 追加 **Execute 逐步循环** + 「禁止水平切片：一次只完成当前 §8.x 步」 |
| （可选） | 注入 `research/execute-red-evidence*.md` 路径约定 |

**目的：** hook 注入与 trellis-implement.md 一致。

---

#### 3.6 `AGENTS.md`（Trellis 块）或 `.cursor/hooks/session-start.py`

**改什么：**

当 `task.json` status=`in_progress` 且任务目录有 `MASTER.plan.md` 时，SessionStart / workflow-state 注入：

```text
Execute 门禁：严格 §8.x 逐步；每步 RED 证据非空；§12 Skill 逐步 @；勿 finish-work。
复杂任务：trellis-check → Audit；Execute 不做 A1。
```

**目的：** **主会话 inline**（Batch A 实际路径）与 sub-agent 同门禁。

---

### P1 — 强烈建议（减少 Execute 欠账）

#### 3.7 `.trellis/workflow.md`

| 块 | 修改 |
|----|------|
| `[workflow-state:in_progress]` | 复杂任务增加 **逐步 Execute 循环**（引用 MASTER §8 当前步，而非「读完整 §8 开写」） |
| `[workflow-state:in_progress-inline]` | 同上 + 显式读 Karpathy/testing-guidelines |
| **Guardrails** | 新增：「§8 含完整测试正文」= Plan 缺陷，Execute 仍须逐步 RED |

---

#### 3.8 `.trellis/spec/guides/execute-skill-registry.md`

| 修改 |
|------|
| §1 增加 **User Rule 映射表**：karpathy / testing-guidelines → MASTER §12 必做行 |
| §4 禁止事项增加：**禁止**未跑 RED 就勾选 §8 已执行 |
| 澄清：`trellis-before-dev` = Plan 5c；Execute 读 **implement.jsonl + 已冻结 spec 路径** |

---

#### 3.9 **新建** `.trellis/scripts/validate_execute_handoff.py`

Execute 交接 Audit 前运行（可挂 `task.py` 子命令或 CI optional）：

- 检查 `{task}/research/execute-evidence/` 或 MASTER §8 证据列非空
- 检查 §12 必做 Skill 对应 `research/execute-skill-evaluation.md` 或 MASTER 勾选
- 缺则 exit 1

**目的：** §11 DoD 工具化。

---

#### 3.10 `.trellis/tasks/<slug>/` 任务内约定（Batch A retrofit 示范）

对 **已有** Batch A（可选文档债，不改代码）：

| 文件 | 修改 |
|------|------|
| `MASTER.plan.md` §8 各步 | 补 **RED/GREEN 证据** 列，链到 `research/execute-red-evidence-and-guidelines.md` |
| `MASTER.plan.md` §12 | `[x]` + 链到 `research/execute-skill-evaluation.md` |
| `prd.md` L18 | `migration 003` → **`004_ingestion_sources`**（与 DECISIONS 一致） |

---

### P2 — 体验与 Plan 质量

#### 3.11 `.trellis/spec/guides/templates/plan.freeze.md`

- §3.1 增加：`validate-freeze` 命令输出粘贴区
- Phase 5d 增加：对抗审计后 **§8 不得保留完整测试函数体** 的自检行

#### 3.12 `.cursor/skills/trellis-before-dev/SKILL.md`

- 顶部注明：**Plan Phase 5c 专用**；Execute 复杂任务 **不重复跑**，改读 implement.jsonl 列出的 spec

#### 3.13 `.cursor/skills/trellis-check/SKILL.md`

- 顶部注明：**Audit A1 / 简单任务 Execute**；复杂任务 Execute **禁止**（链 execute-skill-registry）

#### 3.14 `implement.jsonl` 种子模板（`task.py create`）

默认增加条目：

```json
{"file": ".claude/skills/.../karpathy-guidelines/SKILL.md", "reason": "Execute User Rule"}
{"file": ".claude/skills/testing-guidelines/SKILL.md", "reason": "Execute User Rule"}
```

（路径按仓库实际 plugin 缓存或 `.agents/skills` 稳定路径）

---

## 4. 不建议改 / 易误导的改法

| 做法 | 为何不做 |
|------|----------|
| 让 Execute 再跑完整 `trellis-check` | 与双契约冲突；应加强 Audit A1 |
| 在 §8 里写更多完整代码 | 加剧水平切片；应 **减** 而非 **加** |
| 强制每步 git commit | Windows/Agent 环境摩擦大；用 **证据文件** 代替 |
| 派发 trellis-implement 代替 inline | 不解决主会话路径；应 **hook 对齐** |

---

## 5. 建议写入模板的「Execute 逐步循环」文案（可复制）

```markdown
### Execute 逐步循环（每 §8.x 步强制执行）

1. **读** 本步「绑定 §12 Skill」对应 SKILL.md 相关章节
2. **RED**：只写/启用本步 tracer 测试 → 跑「RED 命令」→ **必须 FAIL** → 输出写入「RED 证据路径」
3. **GREEN**：最小实现 → 跑「GREEN 命令」→ **必须 PASS** → 输出写入「GREEN 证据路径」
4. **勾** 本步「已执行」；**禁止**未填证据勾选
5. **incremental**：全库 pytest 仍绿后再进入 §8.(x+1)
6. 若 RED 失败不符合预期 → **systematic-debugging**（条件 Skill），不得直接改实现猜修复

**Red Flag：** 单次编辑跨多个 §8 步 / >100 行且无 pytest → 停止，回退到当前步。
```

---

## 6. Batch A 是否需要再改代码？

**结论：不需要。** 行为已 GREEN；欠账在 **流程与 Plan 形态**。

若坚持工具化交接，仅建议：

- 更新任务内 `MASTER.plan.md` §12 勾选 + 证据链接（文档）
- 不在此任务重跑 TDD 重写代码

---

## 7. 实施顺序建议

```text
P0: templates/MASTER.plan.md §8 表格
  → validate_plan_freeze.py + task.py start 挂钩
  → trellis-implement.md + inject-subagent-context.py
  → AGENTS.md / session-start Execute 门禁
P1: workflow.md + execute-skill-registry + validate_execute_handoff
P2: plan.freeze / skill 头注 / implement.jsonl 种子
```

---

## 8. 与上一会话 Plan 欠账的对应

| Plan 欠账 | 应用哪条改造 |
|-----------|--------------|
| §8 TDD 全文可复制 | §3.1 禁止内嵌完整测试 + Phase 5 writing-plans |
| plan.freeze 未机械校验 | §3.3 validate_plan_freeze |
| §12 写了但未 enforce | §3.4–3.6 + §5 逐步循环 |
| 对抗审计后仍 start | §3.3 start 前校验 plan.freeze §3 |

---

**下一步：** 若你确认，可按 P0 顺序提交一组 Trellis 基础设施 PR（不涉及 Batch A 业务代码）。
