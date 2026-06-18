# EXECUTE READY — Round 2 Batch D

> **下一会话入口** · Plan 收尾完成 · `task.json` status = `in_progress` · 2026-06-18

## 立即开始（复制给 Execute agent）

```text
Round 2 Batch D Execute：MUST read .cursor/skills/trellis-execute/SKILL.md
任务目录：.trellis/tasks/06-18-round2-batch-d-orchestrator
分支：feat/round2-batch-d-orchestrator（勿在 master 直接开发）

Phase 0 Boot（MASTER §8.0）— 完成前禁止修改 backend/tests/scripts 业务逻辑：
  1. mkdir execute-evidence/
  2. Read integration-ledger.md → implement.jsonl 全 68 条（§0.3/§0.4）
  3. 6.pre → gitnexus-execute-summary.md + context-closure.md
  4. validate-execute-boot → exit 0
  5. execute-boot.md 末尾写 Phase 0 complete

然后严格按 MASTER §8.1 → §8.11 逐步 RED/GREEN。
不要 finish-work；完成后交接 Audit。
```

## 机械自检（Plan 已跑通）

```bash
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-18-round2-batch-d-orchestrator
python .trellis/scripts/task.py suggest-implement-context .trellis/tasks/06-18-round2-batch-d-orchestrator
```

## 关键文件

| 用途 | 路径 |
|------|------|
| 执行契约 | `MASTER.plan.md` |
| Boot 清单 | `implement.jsonl`（68） |
| v3 读法 | `research/integration-ledger.md` |
| 测试正文 | `research/orchestrator-tests.md` |
| 审计 | `AUDIT.plan.md` + `audit.jsonl` |

## Plan 已完成 · Execute 未做

- `execute-evidence/` — 空（§8.0 创建）
- `research/execute-boot.md` — 待写
- `research/gitnexus-execute-summary.md` — 6.pre 待写
- `research/context-closure.md` — 6.pre 待写
- `backend/app/sync/*` — 待建（trace manifest = deferred）

## 禁止

- Round 3+ Layer 建模 / API·前端 / Agent / 真实 vendor Port
- `finish-work`（Audit 前）
- 跳过 implement.jsonl 任一条 Boot Read
