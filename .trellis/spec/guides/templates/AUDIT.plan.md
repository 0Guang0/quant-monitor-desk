# Audit 计划 — {{任务标题}}

> **读者：** 主会话 + A1–A8  
> **冻结元数据：** `audit-skill-paths.yaml` + `agents/audit-a*.md` 及维度模板（skill / 派发 — **Plan 不手填**）  
> **编排：** `complex-task-planning-protocol.md` Phase 7  
> **本文只写本任务可变内容：** Trace Authority + §1 任务专属验证行

| 字段         | 值                                                   |
| ------------ | ---------------------------------------------------- |
| slug         | `{{slug}}`                                           |
| audit.jsonl  | 第一条 = 本文件                                      |
| 默认验证矩阵 | `audit-skill-registry.md` §2（未在下表覆写则用默认） |

**判定口径：** diff、`detect_changes()`、pytest 输出、spec 对照；不以自述为 PASS。`manifest-amend.md` 存在时 A5 对照 diff + `implement.jsonl` + 代码。

---

## 0.1 Trace Authority Set（必填 · 写入 `audit.jsonl`）

| 类别                | 文件                                                         | 用途                         |
| ------------------- | ------------------------------------------------------------ | ---------------------------- |
| 原始任务卡          | `{{docs/implementation_tasks/.../NNN_task.md}}`              | scope / AC / Red Flags       |
| task README         | `docs/implementation_tasks/README.md`                        | 入口合规                     |
| task input index    | `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`      | 必读上下文                   |
| unresolved coverage | `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md` | 未闭合项                     |
| project map         | `MIGRATION_MAP.md`                                           | docs/specs 边界              |
| round map           | `{{ROUND*_BATCH_IMPLEMENTATION_MAP.md}}`                     | batch / out-of-scope         |
| entry               | `EXECUTION_PLAN.md`                                          | v4.2 计划正文 / AC / 约束    |
| execution-index     | `EXECUTION_INDEX.md`                                         | §1/§2/§3/§5 索引             |
| entry_v41           | `research/00-EXECUTION-ENTRY.md`                             | **仅 v4.1 legacy**           |
| slices_v41          | `research/to-issues-slices.md`                               | **仅 v4.1 legacy**           |
| external-index_v41  | `research/EXTERNAL-INDEX.md` §A                              | **仅 v4.1 legacy**           |
| omission-check      | `research/project-map-omission-check.md`                     | 地图倒查（若 INDEX §3 登记） |
| integration-ledger  | `research/integration-ledger.md`                             | context packing              |

缺失或未解释差异 → A1/A5 列入 `audit.report.md` §4.3。

---

## 1. 本任务验证覆写（仅差异行 · 留空则用 registry 默认）

> 验证类型：`static` | `read-only` | `review-only` | `trace-ac` | `pytest-isolated` | `cli-sandbox`  
> 写库/CLI 用 **audit-sandbox**；正交于 Execute INDEX §2.1（A5 抽检除外）。

| 维  | 本任务        | 命令 / 检查（仅任务专属）                                     | 环境          | 通过条件 | 已执行 |
| --- | ------------- | ------------------------------------------------------------- | ------------- | -------- | ------ |
| A3  | {{必做/不用}} | {{威胁面补充 rg 或 SKIP 理由}}                                | local         |          | [ ]    |
| A6  | {{必做/不用}} | `{{perf 命令}}` 阈值 `{{}}`；或 **SKIP** — {{理由}}           | audit-sandbox |          | [ ]    |
| A7  | {{必做/不用}} | `{{init/migrate CLI}}` + 1 异常场景                           | audit-sandbox |          | [ ]    |
| A8  | 必做          | `pytest {{tests/… 或 -k}}` `--basetemp=.audit-sandbox/pytest` | audit-sandbox |          | [ ]    |

### 1.1 占位符（须替换后 `task.py start`）

| 占位                   | 填什么         |
| ---------------------- | -------------- |
| `{{init/migrate CLI}}` | 本任务真实 CLI |
| `{{tests/…}}`          | A8 补测选择器  |
| `{{perf 命令}}` / 阈值 | 仅 A6 必做时   |

---

## 2. DoD（主会话）

- [ ] 7.pre → `gitnexus-audit-summary.md`
- [ ] 按 `audit-skill-paths.yaml` 派发 A1–A8 → `audit.report.md`
- [ ] 汇总各维 `result` / `evidence` → `audit_matrix.json`（模板：`.trellis/spec/guides/templates/audit_matrix.json`）
- [ ] PASS / FAIL（任维 fail 或 findings 非空 → FAIL → REPAIR.plan）
