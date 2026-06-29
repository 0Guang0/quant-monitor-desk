# Audit Boot — Plan v4.1（Execution Bundle）

> **Leading word — v4.1：** 规格在 **`research/00-EXECUTION-ENTRY.md` + `research/*` 包**；`frozen/*.md` 为薄指针；**无 `MASTER.plan.md`**。  
> **读者：** A9 主会话 · A1–A8 子 agent（派发前 **全文 Read**）。

## 协议

| 字段         | 值                                                                                                |
| ------------ | ------------------------------------------------------------------------------------------------- |
| `task.json`  | `meta.plan_protocol_version` 须为 **`"4.1"`**（活跃复杂任务）                                     |
| Execute 验收 | `EXECUTION_INDEX.md` §1 `[x]` + §2 AC + §2.1 Tier + **代码/测试**（v4.1 无 execute-evidence txt） |
| Audit 编排   | `AUDIT.plan.md` + `audit.jsonl` + 本 Boot                                                         |
| 切片 AC SSOT | `research/to-issues-slices.md`                                                                    |
| legacy       | v3 `MASTER.plan.md` 仅 `tasks/archive/` 只读；**Audit 活跃任务不读**                              |

## Boot 读序（按序 · 不得跳）

| #   | 文件                                    | 用途                                       |
| --- | --------------------------------------- | ------------------------------------------ |
| 1   | `agent-toolchain.md`                    | 工具路由                                   |
| 2   | `agents/audit-adversarial-authority.md` | 对抗权威                                   |
| 3   | 本文件                                  | Boot checklist                             |
| 4   | `agents/audit-finding-schema.md`        | findings 关账                              |
| 5   | `agents/audit-coverage-model.md`        | 两条链·三类缺口（**Audit only**）          |
| 5   | `<task>/task.json`                      | 确认 `plan_protocol_version: "4.1"`        |
| 6   | `<task>/AUDIT.plan.md`                  | §0.1 Trace Authority + §1 覆写             |
| 7   | `<task>/audit.jsonl`                    | **全文**（第一条 = AUDIT.plan）            |
| 8   | `<task>/EXECUTION_INDEX.md`             | §5 Audit 追溯 → §3 audit/both → §1/§2      |
| 9   | `<task>/research/00-EXECUTION-ENTRY.md` | §1 目的/AC · §2 约束 · §5.1 文件地图       |
| 10  | `<task>/research/EXTERNAL-INDEX.md`     | §A 包外必读（活卡路径等）                  |
| 11  | `<task>/research/to-issues-slices.md`   | 切片 AC · 建议测试 · 证据路径              |
| 12  | `<task>/frozen/*.md`                    | 审计锚点（薄指针；不替代 ENTRY/包）        |
| 13  | **ENTRY §5.1 登记的全部 `research/*`**  | Plan skill 产出；freeze 后仍读原文         |
| 14  | `<task>/implement.jsonl`                | A5 **全读**；他维按 Trace + 疑点           |
| 15  | `research/gitnexus-audit-summary.md`    | 7.pre（派发 A1–A8 前）                     |
| 16  | GitNexus                                | ≥1 `query` / `context`（维度 yaml 定必用） |

### ENTRY §5.1 包内必读（默认全读）

`00-EXECUTION-ENTRY.md` §5.1 文件地图登记的 **每一份** `research/*`（通常含）：

- `to-issues-slices.md` · `plan-consolidation.md` · `plan-doubt-review.md` · `plan-spec-gap.md`（或等价 spec 产出）
- `plan-context-pack.md` · `plan-task-sizing.md` · `integration-audit.md` · `reference-adoption-*.md`（若有）
- `project-overview.md` · `gitnexus-summary.md` · `source-index.md`（若有）
- `gitnexus-execute-summary.md`（若存在；v4.1 Execute 不强制）

**不读：** `research/plan-boot.md`（Plan-only）· `plan.freeze.md`（Plan 自检）· v4.1 不要求 `context-closure.md`

### EXECUTION_INDEX §3 / §5 增量

- §3 行 `audience=audit|both` → **必读**
- §5 Audit 追溯集 → **必读**（含 `integration-audit.md`、`project-map-omission-check.md` 等点名项）

### Execute 证据（A5 必触 · v4.1）

- **git diff** + **独立 pytest / INDEX §2.1 复跑**（不信文档自述）
- v4 遗留任务：若存在 `execute-evidence/*` 可对照，**非 v4.1 必触**
- AUDIT §2 冻结的 audit-sandbox / audit-prod-path 命令

## v4.1 术语对照（禁止再写 MASTER）

| 旧（v3/v4.0）                   | v4.1 Audit 读                                                   |
| ------------------------------- | --------------------------------------------------------------- |
| `MASTER.plan.md`                | `EXECUTION_INDEX.md` + `00-EXECUTION-ENTRY.md`                  |
| MASTER §2 AC                    | ENTRY §1 + `to-issues-slices.md` + INDEX §2                     |
| MASTER §5 测试矩阵              | `to-issues-slices.md` 建议测试 + INDEX §2                       |
| MASTER §8 步骤                  | INDEX §1                                                        |
| MASTER §10 Tier                 | INDEX §2.1 + 步末 `uv run pytest -q`                            |
| `research/source-index.md` 唯一 | ENTRY §5.1 + `EXTERNAL-INDEX.md`；有 `source-index.md` 则作补位 |

## Boot 完成条件（派发 A1–A8 前）

- [ ] `plan_protocol_version` = `"4.1"`（否则退回 Plan 升级 Bundle）
- [ ] 上表 #5–#15 已 Read；#13 覆盖 ENTRY §5.1 全部登记文件
- [ ] `AUDIT.plan` Trace Authority 每一行在 audit.jsonl 或 §5/§3 有对应路径
- [ ] `gitnexus-audit-summary.md` 已产出（7.pre）
- [ ] 未以「frozen 已够」跳过 ENTRY §5.1 登记文（Audit 读全包建上下文；验证只信代码+跑测）

## A9 合并

读 A1–A8 `research/audit-a{n}-report.md` → `audit.report.md` §4.1 · `audit_matrix.json` · `research/audit-repair-ledger.md`（schema 见 `audit-finding-schema.md`）。
