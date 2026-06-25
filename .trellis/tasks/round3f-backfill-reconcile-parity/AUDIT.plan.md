# Audit 计划 — B3F-BR

| 字段 | 值 |
|------|-----|
| slug | `round3f-backfill-reconcile-parity` |
| audit.jsonl | 第一条 = 本文件 |

## 0.1 Trace Authority Set

| 类别 | 文件 | 用途 |
|------|------|------|
| Roadmap | `PROJECT_IMPLEMENTATION_ROADMAP.md` 3F.4 | R3F-BR-01..05 |
| Playbook | `BATCH_3F_COORDINATOR_PLAYBOOK.md` §8.5 | PASS |
| source-index | `research/source-index.md` | 血缘 |

## Audit Source Trace

| 类别 | 路径 | Audit 用途 |
|------|------|------------|
| MASTER | §2 §5 §9 | A5 AC |
| diff | `orchestrator.py` · closure tests · `test_sync_runners.py` | A1/A4 |
| 测试 | `test_r3f_br_backfill_reconcile_closure.py` | A8 |
| forbidden | 无 crash-window 新实现 | A5 |

## 1. 验证覆写

| 维 | 本任务 | 命令 | 通过 |
|----|--------|------|------|
| A3 | 必做 | diff 无 WriteManager / write_contract 语义变更 | 零写模式改动 |
| A5 | 必做 | R3F-BR-01..05 closure + §8.5 绿 | 五则 closure + playbook |
| A6 | **SKIP** — 无 hot path SLA | — | 记录 SKIP |
| A8 | 必做 | Playbook §8.5 pytest 子集 + `pytest -q` | exit 0 |

## 2. DoD

- [ ] A1–A8 报告
- [ ] 对抗性零 OPEN
- [ ] PASS 前不 finish-work
