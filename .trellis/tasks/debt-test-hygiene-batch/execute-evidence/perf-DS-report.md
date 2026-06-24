# PERF-DS — 只读评估 + B3 实施（Phase B3）

> 模板：`agents/performance-engineer.md` | 串行 pytest | baseline：`phaseB2-pytest-durations.txt`

## Baseline

```powershell
uv run pytest tests/test_sync_orchestrator.py tests/test_batch_d_orchestration_flow.py tests/test_vendor_fetch_e2e.py -q --durations=20
```

- **29 passed**，~25s（2026-06-24，integration）
- 原始证据：`perf-DS-pytest.txt`

## Top 5 耗时 + 资源（推断）

| 用例                              | call  | 判定 | 备注                 |
| --------------------------------- | ----- | ---- | -------------------- |
| `eachShard_callsResourceGuard`    | 2.25s | ❌   | ≥3 分片 + guard 计数 |
| `largeRange_splitsIntoTasks`      | 2.19s | ❌   | ≥3 分片              |
| `repeatRun_noDuplicatePrimaryKey` | 1.74s | ❌   | 双次 incremental     |
| `midShardFailure`                 | 1.28s | ⚠️   | 已 2 分片            |
| vendor E2E ×2                     | ~1.0s | ⚠️   | bootstrap 已 lean    |

Top5 RSS（agent 会话）：backfill 3-shard ~105–108 MB；repeatRun ~103 MB。瓶颈在 **分片循环 + migrate**，非内存尖峰。

## B3 已实施（§1.1）

**无 DS 文件改动** — `plannedJob` 的 `bootstrap_vendor_e2e_db` 在全 suite 下反而更慢（多 `sync_to_db`），已回滚（ponytail: 不测的价值不加）。

## 未做（❌ / MERGE-C 提案）

- `_orch_stack` module-scoped migrate（需 conftest，batch_d 写路径隔离）
- 缩 ≥3 分片 / 减 repeatRun 次数
