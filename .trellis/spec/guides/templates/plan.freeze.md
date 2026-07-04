# Plan 冻结记录 — {{任务标题}}

> **协议：** Plan **v4.2** Slim Plan（默认）· legacy v4.1 见 §3.0v4.1  
> **读者：** Plan agent · Execute / Audit **不读**本文件 · 勿写入 implement.jsonl / audit.jsonl

---

## 1. Plan 阶段 Skill 执行记录（v4.2）

> Skill 由 **用户手动调用**；产出合入 `EXECUTION_PLAN.md`；路由同步 `EXECUTION_INDEX.md` §3。
> 登记实际 Read 的 skill → `research/plan-skill-reads.jsonl`。

| Phase  | Skill（用户选用）              | 典型合入位置                                  | 已完成 |
| ------ | ------------------------------ | --------------------------------------------- | ------ |
| boot   | agent-toolchain · trellis-plan | `research/plan-boot.md`                       | [ ]    |
| 1a     | gitnexus-plan-1a               | `research/project-overview.md`                | [ ]    |
| 1b     | gitnexus-plan-1b               | `research/gitnexus-summary.md`                | [ ]    |
| 1–4    | **trellis-research**           | `research/<topic>.md` 等                      | [ ]    |
| 2–5    | 用户选用的加固 skill           | **`EXECUTION_PLAN.md`**                       | [ ]    |
| **5e** | trellis-plan                   | `EXECUTION_PLAN.md` · `EXECUTION_INDEX.md` §3 | [ ]    |

契约：`.trellis/spec/guides/plan-skill-outputs.yaml` · 路径：`.trellis/spec/guides/plan-skill-paths.yaml`

---

## 2. Plan 贡献溯源（v4.2）

| 来源         | 落点                          |
| ------------ | ----------------------------- |
| 执行计划正文 | `EXECUTION_PLAN.md`           |
| 机器索引     | `EXECUTION_INDEX.md` §1/§3/§5 |
| 架构决策     | `docs/decisions/ADR-*.md`     |

### 2.1 AUDIT 人工填写（模板 ≠ 终稿）

| 须做什么           | 在哪改                                         |
| ------------------ | ---------------------------------------------- |
| 替换 `{{}}` 占位符 | `AUDIT.plan.md` §2（留 `{{}}` = 未冻结）       |
| Trace Authority    | `AUDIT.plan.md` §0.1（v4.2：`EXECUTION_PLAN`） |
| 无性能要求         | A6 SKIP + 理由                                 |

---

## 3. 冻结自检（`task.py start` 前全勾）

### 3.0v4.2 Slim Plan one-pager

| ✓   | Execute 验收                                                              | ✓   | Audit                                                |
| --- | ------------------------------------------------------------------------- | --- | ---------------------------------------------------- |
| [ ] | `EXECUTION_PLAN.md` 含用户确认的完成条件；`meta.execute_entry` 指向该文件 | [ ] | `AUDIT.plan.md` 无 `{{}}`；Trace 含 `EXECUTION_PLAN` |
| [ ] | `EXECUTION_INDEX.md` §3 manifest 已从计划摘录外部必读                     | [ ] | `audit.jsonl` 第一条 = `AUDIT.plan.md`               |
| [ ] | GitNexus 1a+1b + trellis-research 已 Read 并落盘                          | [ ] | A6：perf 或 SKIP + 理由                              |
| [ ] | `validate-plan-phase … 5e` exit 0                                         | [ ] | 7.pre → `gitnexus-audit-summary.md`                  |

**Execute 读入口：** `EXECUTION_PLAN.md`（implement slot2）— **不是** frozen 全文。

### 3.0b 原计划包门禁

| ✓   | 检查项                                                                |
| --- | --------------------------------------------------------------------- |
| [ ] | 已读 `docs/implementation_tasks/` 本任务活卡 + 相关 `GLOBAL_*.md`     |
| [ ] | 活卡 **未迁入** `research/`（外部路径登记在 `EXECUTION_INDEX.md` §3） |
| [ ] | `research/plan-boot.md` 含 **Phase P0 complete**                      |
| [ ] | `research/plan-skill-reads.jsonl` 覆盖 `freeze_required_skills_v42`   |

### 3.0c 薄三件套 + manifest（v4.2）

| ✓   | 检查项                                                                            |
| --- | --------------------------------------------------------------------------------- |
| [ ] | `task.py freeze-task-card` → `frozen/*.md` 为 **薄指针** → `EXECUTION_PLAN.md`    |
| [ ] | `EXECUTION_INDEX.md` §0/§1/§3/§5 已填；§1 含 RED/GREEN                            |
| [ ] | `task.py generate-manifests` → slot1=`frozen/` · slot2=`EXECUTION_PLAN.md`        |
| [ ] | `prd.md` 薄索引（`thin-index: true` 或 ≤25 行且含 `frozen/` 或 `EXECUTION_PLAN`） |
| [ ] | `context_pack.json` 有效（complex 任务）                                          |

### 3.0d 澄清门禁（仅当有未决 Open Questions）

| ✓   | 检查项                                                                            |
| --- | --------------------------------------------------------------------------------- |
| [ ] | 计划/Open Questions 无未勾选项 **或** 已有 `research/*-session.md` / ADR 记录决策 |

### 3.1 AUDIT.plan.md

- [ ] §1 A1–A8 + A9 主会话；§2 无 `{{}}`；§0.1 Trace 含 `EXECUTION_PLAN.md`
- [ ] `audit.jsonl` 第一条 = `AUDIT.plan.md`

### 3.2 jsonl

- [ ] `implement.jsonl` slot1 = `frozen/` · slot2 = `EXECUTION_PLAN.md`（v4.2）或 `research/00-EXECUTION-ENTRY.md`（v4.1 legacy）
- [ ] `validate-plan-freeze` exit 0

```bash
python .trellis/scripts/task.py freeze-task-card .trellis/tasks/<slug>
python .trellis/scripts/task.py generate-manifests .trellis/tasks/<slug>
python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/<slug> 5e
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/<slug>
```

**粘贴最近一次 `validate-plan-freeze` 输出：**

```text
(paste exit 0 output)
```

### 3.3 批准

- [ ] 用户「计划批准」→ `task.py start`

---

## 附录 A · v4.1 Execution Bundle（legacy · 在途/归档只读）

> 新复杂任务 **不得** 使用 v4.1。在途任务：`meta.plan_protocol_version: "4.1"` · Boot `agents/audit-boot-v4.1.md` · slot2 = `research/00-EXECUTION-ENTRY.md` · 完整自检见 `tasks/archive/` 范例任务 `plan.freeze.md`。

---

## 4. 修订记录

| 版本   | 日期     | 变更                                                       |
| ------ | -------- | ---------------------------------------------------------- |
| v4.2   | {{date}} | Slim Plan：仅 EXECUTION_PLAN + EXECUTION_INDEX；无固定模板 |
| v4.1   | —        | Execution Bundle；归档任务只读                             |
| legacy | —        | v3 / v4.0 见 `templates/plan.freeze.legacy-v3-v40.md`      |
