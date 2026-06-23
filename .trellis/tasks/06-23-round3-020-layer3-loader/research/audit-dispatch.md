# 020 Layer3 loader — Audit 并行派发 v1

> 协调者：主会话 · **composer-2.5**（非 fast）· 2026-06-23  
> Execute handoff：`validate-execute-handoff` exit 0

## 环境信封（所有 agent 强制）

| 项 | 值 |
| -- | -- |
| Worktree（cwd） | `C:\Users\Guang\Desktop\quant-monitor-desk-wt-020-layer3-loader` |
| 分支 | `feature/round3-020-layer3-loader` |
| 任务目录 | `.trellis/tasks/06-23-round3-020-layer3-loader` |
| 禁止 | `git commit` / `git push` / 改生产 `data/duckdb/` |
| 审阅 diff 范围 | `backend/app/layer3_chains/**`、`tests/test_layer3_loader.py`、`tests/fixtures/layer3_*`、`tests/test_catalog.yaml`、`scripts/check_test_catalog.py` |

## 产出约定（必须落盘，禁止只输出聊天）

| 维 | Agent 模板（全文注入 prompt） | 必须写入 |
| -- | ----------------------------- | -------- |
| A1 | `agents/audit-a1-spec.md` | `research/audit-sections/A1.md` |
| A2 | `agents/audit-a2-ponytail.md` | `research/audit-sections/A2.md` |
| A3 | `agents/security-auditor.md` + also_read `sql-pro.md` | `research/audit-sections/A3.md` |
| A4 | `agents/code-reviewer.md` | `research/audit-sections/A4.md` |
| A5 | `agents/audit-a5-completion.md` | `research/audit-sections/A5.md` |
| A6 | **SKIP** | — |
| A7 | `agents/database-administrator.md`（Audit 模式） | `research/audit-sections/A7.md` |
| A8 | `agents/qa-expert.md` | `research/audit-sections/A8.md` |
| A9 | 主会话 | `audit_matrix.json` + `audit.report.md` |

每文件首行：`# A{n} — <title>` + **`Result: PASS | WARN | FAIL`**。

## 必读（任务内）

- `AUDIT.plan.md` §2 本任务矩阵
- `MASTER.plan.md` §2 AC、`research/execute-evidence/*`
- `audit.jsonl` 每一条
- Execute 证据路径：**`research/execute-evidence/`**（非根目录 `execute-evidence/`）

## AUDIT §2 任务专条

| 维 | 命令 / 检查 |
| -- | ----------- |
| A1 | 对照 `layer3_loader_contract.yaml`、`layer3_industry_shock_anchor.md`、MASTER §2/§3 |
| A2 | `git diff --stat` `backend/app/layer3_chains/`；ponytail-review |
| A3 | `rg` 直写 DB / forbidden 路径 |
| A4 | loader 校验链、`IndustryChainLoadError` 一致性 |
| A5 | AC-020-1..6 ↔ §8 evidence；抽检 2 个 `research/execute-evidence/*-green.txt`；`AUDIT_PROD_ROOT=.audit-sandbox/r3-020-audit-prod-equiv` |
| A7 | 无 migration/DB 写；`data/duckdb/` hash 审计前后不变 |
| A8 | 补边界：**空 bundle**（MASTER §5.3 未列）；复跑 `test_batch3_staged_downstream_gate.py` |

## A9 合成（等 A1–A8 落盘后）

1. 读 `research/audit-sections/A*.md`
2. 写 `audit_matrix.json`（模板：`.trellis/spec/guides/templates/audit_matrix.json`）
3. 写 `audit.report.md`（§3.1–§3.8 汇总 + §4.3 开放项）
4. 7.pre `research/gitnexus-audit-summary.md` 若缺失由 A9 补
