# Research: WAVE0 §0.2 SYNC-06 quiz 裁决摘录

- **Query**: WAVE0 INDEX §0.2 + §6 SYNC-06 拆 3 票规则
- **Scope**: internal（摘录自主仓 `WAVE0_BATCH3V_TO_ISSUES_INDEX.md`）
- **Date**: 2026-06-28

## Findings

### §0.2 粒度 quiz（2026-06-28）

| 卡 | 裁决 | GitHub issue 数 |
| -- | ---- | --------------- |
| **B3V-C04 SYNC** | **SYNC-06 拆 3 票**：实现 → 测试 → 关账（路径 B 时实现票改为 handoff 文档票） | **+2**（相对原单票 SYNC-06；SYNC-BOOT..05 仍各 1 Step） |

### §6 SYNC-06 三票摘要

| ID | 标题 | 交付物 | 路径 B |
| -- | ---- | ------ | ------ |
| **SYNC-06A** | VR-SYNC-001 最小恢复实现 | `recover_stuck_writing_job` + hook 接线 | → `research/sync-001-handoff.md` 草稿 |
| **SYNC-06B** | crash-window pytest WRITING→COMPLETED | 注入失败 + recovery 断言 COMPLETED | **skip** |
| **SYNC-06C** | VR-SYNC-001 关账或 handoff 闭合 | proposed delta 或 handoff 定稿 | 同左 |

### 测试路径替换（§6 末表）

| 任务卡引用 | 实际 |
| ---------- | ---- |
| `tests/test_sync_runners.py` | **不存在** → `tests/test_sync_orchestrator.py` + 可选 `tests/test_sync_job_contract.py` |

### Related Specs

- `B02_04_sync_job_support_and_recovery.md` §5 B02-SYNC-06 — 原单票来源
- `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.5 · §8.4 — C04 必读与 PASS 命令

## Caveats / Not Found

- worktree 内 **无** `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` 文件副本；Plan commit 前应自主仓引入
