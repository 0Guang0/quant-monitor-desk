# PERF-AUD — 只读评估（Phase B3）

> 模板：`agents/performance-engineer.md` | 证据：`perf-AUD-pytest.txt`

## Baseline

```powershell
uv run pytest tests/test_audit_remediation.py tests/test_audit_fixes.py -q --durations=20
```

- **22 passed**；Top call **2.26s** `test_partialSuccess_eachItemWritesAuditEvent`

## Top 6 + 判定

| 用例                                      | call  | 判定                    |
| ----------------------------------------- | ----- | ----------------------- |
| `partialSuccess_eachItemWritesAuditEvent` | 2.26s | ❌ events≥3，3-shard    |
| `jobEventLog_payloadSchema`               | 0.99s | ❌ 全事件 schema        |
| `validationReport_persistsRuleVersion`    | 0.97s | ❌ 完整 incremental E2E |
| `backfillShard_successPath`               | 0.91s | ⚠️                      |
| `incrementalJob_emitsItemSuccess`         | 0.90s | ❌                      |
| `sourceConflict_persistsTolerance`        | 0.86s | ⚠️                      |

## B3 实施

**无 AUD 文件内 ✅ 项**（6 慢测均注释锁死）。跨文件优化仅 MERGE-C 提案：共享 `migrated_cm` / `_orch_stack` bootstrap，本阶段未改 DS 文件。
