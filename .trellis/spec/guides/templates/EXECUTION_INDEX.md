# 执行索引 — {{任务标题}}

> **读者：Execute + Audit**（唯一人工索引）  
> **冻结任务卡：** `frozen/{{NNN}}_*.md`（Execute/Audit 正文 SSOT）  
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

## 1. 步骤（Execute · v4.1）

| Step | 任务卡锚点 | RED 命令（见切片/to-issues） | GREEN 命令  | 完成标记           |
| ---- | ---------- | ---------------------------- | ----------- | ------------------ |
| 9.0  | Boot       | `{{red}}`                    | `{{green}}` | frozen/INDEX `[x]` |
| 9.1  | §9.1       | 见切片                       | 见切片      | `[x]` + 代码/测试  |

> **v4.1 证据 = 代码 + 测试 + `uv run pytest -q`**；不列 `execute-evidence/*.txt`。  
> RED/GREEN 测试体在 `tests/`；正式流程 Read **`/test-driven-development`**（必做 · `trellis-execute/reference.md`）。  
> **Loop（`task_track: complex`）：** Plan freeze 产出 `context_pack.json` + `loop_manifest.json`；Execute handoff 须 `evidence_index.json` + `check_task_evidence` 绿（见 `AGENTS.md` §Loop engineering）。  
> **Legacy v4.0：** 可保留 txt 证据列（见 `plan.freeze.legacy-v3-v40.md`）。

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

## 5. Audit 追溯集（v4.1 · Plan 填写）

| 类别                 | 文件                                                         | 用途                                  |
| -------------------- | ------------------------------------------------------------ | ------------------------------------- |
| Execution Bundle     | `research/00-EXECUTION-ENTRY.md`                             | §1 AC · §2 约束 · §5.1 文件地图       |
| 切片 AC              | `research/to-issues-slices.md`                               | AC · 建议测试 · v4.1 验收=代码/测试   |
| 包外必读             | `research/EXTERNAL-INDEX.md`                                 | §A 活卡路径等                         |
| 活任务卡（只读对照） | `{{source_card}}`                                            | Plan 来源；Audit 对照 frozen 是否漏项 |
| frozen SSOT          | `frozen/{{NNN}}_*.md`                                        | Execute/Audit 正文锚点（薄指针）      |
| unresolved           | `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md` | A1/A8                                 |
| round map            | `{{ROUND*_BATCH_IMPLEMENTATION_MAP.md}}`                     | batch scope                           |
| integration-audit    | `research/integration-audit.md`                              | 包整合闭环                            |
| omission-check       | `research/project-map-omission-check.md`                     | 地图倒查                              |

---

## 6. 机器路由

由 `uv run python scripts/context_router.py --task <dir>` 写入 **`context_pack.json`**。  
Execute Boot：`frozen/*.md` → 本文 → `context_pack.json` → `trellis-execute/SKILL.md` → §3 `must-read` 行（经 `implement.jsonl`）。
