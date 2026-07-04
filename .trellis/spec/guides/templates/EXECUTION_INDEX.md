# 执行索引 — {{任务标题}}

> **读者：Execute + Audit**（机器索引 + 步骤/证据）  
> **v4.2 计划正文：** `EXECUTION_PLAN.md`（人读 SSOT）  
> **冻结任务卡：** `frozen/{{NNN}}_*.md`（薄指针 → `EXECUTION_PLAN.md`）  
> **审计矩阵：** `AUDIT.plan.md`（§2 维度验证）  
> **机器清单：** `implement.jsonl` / `audit.jsonl` / `check.jsonl` 由 `task.py generate-manifests` 从本文 §3 自动生成

---

## 0. 冻结元数据

| 字段         | 值                                                 |
| ------------ | -------------------------------------------------- |
| slug         | `{{slug}}`                                         |
| source_card  | `docs/implementation_tasks/{{ROUND}}/{{NNN}}_*.md` |
| frozen_card  | `frozen/{{NNN}}_*.md`                              |
| frozen_at    | `{{ISO8601}}`                                      |
| batch / item | `{{ROUND}}` / `{{item_id}}`                        |
| batch map    | `{{ROUND*_BATCH_IMPLEMENTATION_MAP.md}}`           |

### 0.1 血缘（Plan 填写）

| 任务卡 §2 AC | 索引 Step | 验证链 |
| ------------ | --------- | ------ |
| {{AC-1}}     | 9.1       | §2.1   |

---

## 1. 步骤（Execute · v4.2）

| Step | 计划内锚点 | RED 命令  | GREEN 命令  | 完成标记           |
| ---- | ---------- | --------- | ----------- | ------------------ |
| 9.0  | Boot       | `{{red}}` | `{{green}}` | frozen/INDEX `[x]` |
| 9.1  | §9.1       | 见切片    | 见切片      | `[x]` + 代码/测试  |

> **v4.2 证据 = 代码 + 测试 + `uv run pytest -q`**；切片 AC 见 `EXECUTION_PLAN.md`。

---

## 2. AC ↔ 测试 / 验收

| AC   | 测试 / 命令        | 通过条件 |
| ---- | ------------------ | -------- |
| AC-1 | `pytest tests/...` | 全绿     |

### 2.1 四层验收（Tier）

| 层  | 命令                         | 环境              |
| --- | ---------------------------- | ----------------- |
| A   | `uv run pytest -q tests/...` | local/ci          |
| B   | `{{prod-path cmd}}`          | Execute prod-path |

---

## 3. 必须读原文（manifest · 自动生成 jsonl）

> **规则：** 已无损并入冻结任务卡正文的来源标 `summary-ok`，**不得**列入本表。  
> `manifest`：`must-read` | `execute-required` | `audit-only` | `deferred`  
> `audience`：`execute` | `audit` | `both`

| path                                                  | manifest  | audience | extract          | for       |
| ----------------------------------------------------- | --------- | -------- | ---------------- | --------- |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md` | must-read | execute  | scope boundaries | §9.0 Boot |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`  | must-read | execute  | test semantics   | §2 / §2.1 |
| `specs/contracts/{{contract}}.yaml`                   | must-read | both     | contract SSOT    | AC-1 / A1 |

---

## 4. 已并入冻结任务卡（不必再读原文）

| 来源路径                     | 并入任务卡章节 | 摘要         |
| ---------------------------- | -------------- | ------------ |
| `docs/modules/{{module}}.md` | §5 / §6        | {{one-line}} |

---

## 5. Audit 追溯集（v4.2 · Plan 填写）

| 类别        | 文件                                                         | 用途                  |
| ----------- | ------------------------------------------------------------ | --------------------- |
| 计划正文    | `EXECUTION_PLAN.md`                                          | AC · 约束 · 切片/步骤 |
| manifest    | 本文 §3                                                      | 外部必读路由          |
| 活任务卡    | `{{source_card}}`                                            | Plan 来源对照         |
| frozen      | `frozen/{{NNN}}_*.md`                                        | 审计锚点（薄指针）    |
| unresolved  | `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md` | A1/A8                 |
| integration | `research/integration-audit.md`                              | 若 INDEX §3 登记      |

### v4.1 legacy（仅归档任务保留以下行）

| Execution Bundle | `research/00-EXECUTION-ENTRY.md` | legacy |
| 切片 AC | `research/to-issues-slices.md` | legacy |
| 包外必读 | `research/EXTERNAL-INDEX.md` | legacy |

---

## 6. 机器路由

由 `uv run python scripts/context_router.py --task <dir>` 写入 **`context_pack.json`**。  
Execute Boot：`frozen/*.md` → 本文 → `context_pack.json` → `trellis-execute/SKILL.md` → §3 `must-read` 行（经 `implement.jsonl`）。
