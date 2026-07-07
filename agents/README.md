# agents/ — 可派发子 agent 模板

| 路径                           | 说明                                          |
| ------------------------------ | --------------------------------------------- |
| `_upstream/*.md`               | VoltAgent 原文（只读存档）                    |
| `*.md`                         | 改造后可派发 prompt（**model 由派发者指定**） |
| 桌面 `~/Desktop/subagent模板/` | 跨项目整包素材库                              |

## 改造原则

1. **本项目实践优先** — checklist + QMD 路径、sandbox 命令、任务卡产出表
2. **架构可扩展** — 写清当前默认形态（pipeline / DuckDB / layer1–5），roadmap 拆服务/API 时沿用同一套评审与关联技法
3. **正面表述** — `note_model: 派发者指定`；不写死 model；无「与上游对比」类 meta
4. **Skill 注入** — 「你还应该遵循的 Skill」+「启动」；派发者全文注入 subagent

## Audit 八维映射

| 维  | 主模板                      | also_read                                         |
| --- | --------------------------- | ------------------------------------------------- |
| A1  | `audit-a1-spec.md`          | —                                                 |
| A2  | `audit-a2-ponytail.md`      | —                                                 |
| A3  | `security-auditor.md`       | `sql-pro.md`                                      |
| A4  | `code-reviewer.md`          | —                                                 |
| A5  | `audit-a5-completion.md`    | `quant-analyst.md`, `risk-manager.md`             |
| A6  | `performance-engineer.md`   | —                                                 |
| A7  | `database-administrator.md` | `sre-engineer.md`, `devops-incident-responder.md` |
| A8  | `qa-expert.md`              | `test-automator.md`                               |

机器路由：`audit-skill-paths.yaml`

**Findings SSOT：** `agents/audit-finding-schema.md`（P0–P3 双表 · 有 finding 即维 **FAIL**）

**Source-route acceptance SSOT（task-01 / ADR-016）：** 22 源矩阵权威入口为 `uv run python scripts/qmd_ops.py accept-source-route-db` + `scripts/production_gate.py`；legacy `production_equivalent_smoke.py` / tier harness 仅作迁移期参考，不得替代 matrix closure 关账。

**Boot SSOT（v4.2）：** `agents/audit-boot-v4.2.md` + `agents/audit-coverage-model.md`（v4.1 legacy：`audit-boot-v4.1.md`）

**Repair Boot SSOT（v4.1）：** `agents/repair-boot-v4.1.md`

Audit 协调者将各维 agent 产出合并为任务根目录 `audit_matrix.json`（`result`: `pass` | `fail` | `skip` | `fail_then_fixed`；`evidence` → `research/audit-a{n}-report.md`）。各维须含 §维度裁决 + §计划内问题 + §计划外发现；矩阵字段由当前任务卡或 `agents/audit-finding-schema.md` 指定。

## 模板分类（行数 ≈ 2026-06 加厚后）

| 类别           | 文件                                                                                                                                                                           |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Audit 专用     | `audit-a1-spec.md` (~83), `audit-a2-ponytail.md` (~75), `audit-a5-completion.md` (~102)                                                                                        |
| Audit 维度     | `security-auditor.md`, `code-reviewer.md`, `performance-engineer.md` (~117), `qa-expert.md` (~114), `test-automator.md` (~122), `sql-pro.md` (~123)                            |
| 数据/库/可靠性 | `data-engineer.md` (~142), `database-administrator.md`, `database-optimizer.md` (~101), `sre-engineer.md`, `devops-incident-responder.md` (~150), `error-detective.md` (~120)  |
| 量化           | `quant-analyst.md` (~102), `risk-manager.md` (~116)                                                                                                                            |
| Plan           | `api-designer.md` (~122), `architect-reviewer.md` (~85), `git-workflow-manager.md` (~85)                                                                                       |
| Execute        | `backend-developer.md` (~113), `fastapi-developer.md` (~127), `frontend-developer.md` (~73), `cli-developer.md` (~61), `debugger.md` (~123), `refactoring-specialist.md` (~71) |
| 工具/文档/MCP  | `tooling-engineer.md` (~83), `mcp-developer.md` (~72), `documentation-engineer.md` (~86), `readme-generator.md` (~81), `ai-writing-auditor.md` (~102)                          |

Channel 运行时使用本目录 agent 模板；不得恢复已删除的工作流脚本作为活流程。
