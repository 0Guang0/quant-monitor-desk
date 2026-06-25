# Audit 计划 — B3V-SYNC

| 字段 | 值 |
|------|-----|
| slug | `round3v-sync-support-matrix-recovery` |
| audit.jsonl | 第一条 = 本文件 |

## 0.1 Trace Authority Set

| 类别 | 文件 | 用途 |
|------|------|------|
| 任务卡 | `B02_04_sync_job_support_and_recovery.md` | scope / VR |
| Playbook | `BATCH_3V_COORDINATOR_PLAYBOOK.md` §8.4 | PASS |
| source-index | `research/source-index.md` | 血缘 |
| ADR-001 | `docs/decisions/ADR-001-*.md` | crash-window 设计 |

## Audit Source Trace

| 类别 | 路径 | Audit 用途 |
|------|------|------------|
| 任务卡 | `B02_04` | A5 AC |
| MASTER | §2 §5 §9 | A5 抽检 |
| diff | `sync_job_contract.yaml` · `backend/app/sync/**` | A1/A4 |
| 测试 | `test_sync_orchestrator.py` | A8 |
| handoff | `research/sync-001-handoff.md`（若存在） | A5 VR-SYNC-001 |
| forbidden | `write_contract.yaml` diff 应为空 | A3 |

## 1. 验证覆写

| 维 | 本任务 | 命令 | 通过 |
|----|--------|------|------|
| A3 | 必做 | diff 无 `write_contract` / WriteManager 写模式语义变更 | 零写模式契约改动 |
| A5 | 必做 | VR-SYNC-002 关闭；VR-SYNC-001 pytest **或** handoff | 二选一证据 |
| A6 | **SKIP** — 无 hot path SLA | — | 记录 SKIP |
| A8 | 必做 | Playbook §8.4 pytest 子集 + 全量 `pytest -q` | exit 0 |

## 2. DoD

- [ ] A1–A8 报告
- [ ] 对抗性零 OPEN
- [ ] PASS 前不 finish-work
