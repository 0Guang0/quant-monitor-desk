# Worktree slices — C-20 data health

| 字段     | 值                                        |
| -------- | ----------------------------------------- |
| 分支     | `feature/round3-readonly-data-health-v1`  |
| Worktree | `../quant-monitor-desk-wt-r3-data-health` |
| 基线     | `master` @ Wave C                         |
| 并行     | 022, α-3, β-2                             |

## Allowed（MAP §2.2）

- `backend/app/ops/data_health*.py`
- `tests/test_ops_data_health.py`
- `.trellis/tasks/round3-readonly-data-health-v1/**`
- `tests/fixtures/data_health/**`（最小 fixture）

## Forbidden

- `backend/app/layer4_markets/**`
- `backend/app/storage/staged_evidence.py`
- registry 三件套
- production DB write / live fetch

## 文件锁

本 worktree **独占** `data_health*` 核心组；不得与 022（layer4）或 β-2（staged_evidence）并发改同一文件。
