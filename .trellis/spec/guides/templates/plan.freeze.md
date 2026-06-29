# Plan 冻结记录 — {{任务标题}}

> **协议：** Plan **v4.1** Execution Bundle  
> **读者：** Plan agent · Execute / Audit **不读**本文件 · 勿写入 implement.jsonl / audit.jsonl

---

## 1. Plan 阶段 Skill 执行记录（v4.1）

| Phase  | Skill                          | 产出                                                                                        | 已完成 |
| ------ | ------------------------------ | ------------------------------------------------------------------------------------------- | ------ |
| boot   | agent-toolchain · trellis-plan | `research/plan-boot.md`                                                                     | [ ]    |
| 1a     | gitnexus-plan-1a               | `research/project-overview.md`                                                              | [ ]    |
| 1b     | gitnexus-plan-1b               | `research/gitnexus-summary.md`                                                              | [ ]    |
| 1–4    | **trellis-research**（必做）   | `research/<topic>.md` 或 `reference-adoption-*.md`                                          | [ ]    |
| 2b     | spec-driven-development        | `research/plan-spec*.md`                                                                    | [ ]    |
| 3      | 澄清类（**仅**需求不明时）     | grill-me / interview-me / idea-refine / trellis-brainstorm → `research/*-session.md` 或 ADR | [ ]    |
| 3.5    | to-issues                      | `research/to-issues-slices.md`                                                              | [ ]    |
| 5a     | planning-and-task-breakdown    | `research/plan-task*.md`                                                                    | [ ]    |
| 5b     | context-engineering            | `research/plan-context*.md`                                                                 | [ ]    |
| 5c     | doubt-driven-development       | `research/plan-doubt-review.md`                                                             | [ ]    |
| 5c'    | documentation-and-adrs         | `docs/decisions/ADR-*.md` + ENTRY §4                                                        | [ ]    |
| **5e** | trellis-plan                   | `00-EXECUTION-ENTRY` · `EXTERNAL-INDEX` · `plan-consolidation` · `EXECUTION_PLAN.md`        | [ ]    |

契约：`.trellis/spec/guides/plan-skill-outputs.yaml` · 路径：`.trellis/spec/guides/plan-skill-paths.yaml`

---

## 2. Plan 贡献溯源

| 来源                 | 落点                                 |
| -------------------- | ------------------------------------ |
| Skill 产出对照       | `research/plan-consolidation.md`     |
| 切片 AC（唯一 SSOT） | `research/to-issues-slices.md`       |
| Execute 路由         | `research/00-EXECUTION-ENTRY.md`     |
| 架构决策             | `docs/decisions/ADR-*.md` + ENTRY §4 |

### 2.1 AUDIT 人工填写（模板 ≠ 终稿）

| 须做什么           | 在哪改                                   |
| ------------------ | ---------------------------------------- |
| 替换 `{{}}` 占位符 | `AUDIT.plan.md` §2（留 `{{}}` = 未冻结） |
| 无性能要求         | A6 SKIP + 理由                           |
| 有性能要求         | §2 填 perf；§1 A6 标必做                 |

---

## 3. 冻结自检（`task.py start` 前全勾）

### 3.0v4.1 Execution Bundle one-pager

| ✓   | Execute 验收                                                                 | ✓   | Audit                                         |
| --- | ---------------------------------------------------------------------------- | --- | --------------------------------------------- |
| [ ] | `research/00-EXECUTION-ENTRY.md` §1–§5 齐全；`meta.execute_entry` 指向 ENTRY | [ ] | `AUDIT.plan.md` 无 `{{}}`                     |
| [ ] | `research/EXTERNAL-INDEX.md` 含 §A / §B / §C                                 | [ ] | `audit.jsonl` 第一条 = `AUDIT.plan.md`        |
| [ ] | `research/plan-consolidation.md` 含 **`Phase 5e complete`**                  | [ ] | 追溯 `EXECUTION_INDEX.md` §5                  |
| [ ] | GitNexus 1a+1b + trellis-research 已 Read 并落盘                             | [ ] | A6：perf 或 SKIP + 理由                       |
| [ ] | `validate-plan-phase … 5e` exit 0                                            | [ ] | 7.pre → `gitnexus-audit-summary.md`（若适用） |

**Execute 读入口：** `research/00-EXECUTION-ENTRY.md`（implement slot2）— **不是** frozen 全文。

### 3.0b 原计划包门禁

| ✓   | 检查项                                                              |
| --- | ------------------------------------------------------------------- |
| [ ] | 已读 `docs/implementation_tasks/` 本任务活卡 + 相关 `GLOBAL_*.md`   |
| [ ] | 活卡 **未迁入** `research/`（包外路径在 `EXTERNAL-INDEX.md` §A）    |
| [ ] | `research/plan-boot.md` 含 **Phase P0 complete**                    |
| [ ] | `research/plan-skill-reads.jsonl` 覆盖 `freeze_required_skills_v41` |

### 3.0c 薄三件套 + manifest（v4.1）

| ✓   | 检查项                                                                                  |
| --- | --------------------------------------------------------------------------------------- |
| [ ] | `task.py freeze-task-card` 已执行 → `frozen/*.md` 为 **薄指针**（见下节）               |
| [ ] | `EXECUTION_INDEX.md` §0/§1/§3/§5 已填；§1 含 RED/GREEN                                  |
| [ ] | `task.py generate-manifests` → slot1=`frozen/` · slot2=`research/00-EXECUTION-ENTRY.md` |
| [ ] | `prd.md` 薄索引（`thin-index: true` 或 ≤25 行且含 `frozen/` 或 ENTRY）                  |
| [ ] | `context_pack.json` 有效（complex 任务）                                                |

**frozen 薄指针约定（v4.1 · 勿删文件）：**

- **保留** `frozen/*.md`：审计追溯 + implement slot1 + Wave 名片锚点
- **禁止** 复制活卡/`to-issues-slices`/research 全文进 frozen
- `freeze-task-card` 对 v4.1 **自动生成瘦 frozen**；规格只在 ENTRY + `research/`

### 3.0d 澄清门禁（仅当有未决 Open Questions）

| ✓   | 检查项                                                                                                         |
| --- | -------------------------------------------------------------------------------------------------------------- |
| [ ] | `plan-spec*.md` / `plan-task*.md` 无未勾选的 Open Questions **或** 已有 `research/*-session.md` / ADR 记录决策 |

### 3.0e Execution Bundle 机械自检（Plan · 必做）

| ✓   | 检查项                                                                          |
| --- | ------------------------------------------------------------------------------- |
| [ ] | ENTRY §5.1 = 磁盘 `research/*.md`（除 plan-boot）∪ consolidation 对照表 done 行 |
| [ ] | ENTRY §5.2 名单 = §5.1 + EXTERNAL §A + 当前切片 §                               |
| [ ] | `plan-consolidation.md` 含 **Phase 5e complete**                                |

### 3.1 AUDIT.plan.md

- [ ] §1 A1–A8 + A9 主会话；§2 无 `{{}}`
- [ ] `audit.jsonl` 第一条 = `AUDIT.plan.md`（且不含 plan.freeze / implement.jsonl）

### 3.2 jsonl

- [ ] `implement.jsonl` slot1 = `frozen/` · slot2 = `research/00-EXECUTION-ENTRY.md`
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

## 4. 修订记录

| 版本   | 日期     | 变更                                                               |
| ------ | -------- | ------------------------------------------------------------------ |
| v4.1   | {{date}} | 仅 v4.1 Execution Bundle；废止 MASTER / Triad / writing-plans 门禁 |
| legacy | —        | v3 / v4.0 见 `templates/plan.freeze.legacy-v3-v40.md`              |
