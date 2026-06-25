# Sync Crash-Window Recovery Runbook (B3V-SYNC / VR-SYNC-001)

**Owner:** Round 3F · `R3F-BR-03` follow-up for production ops  
**Scope:** ADR-001 intentional window — write commit before `COMPLETED`

## Symptom

- `data_sync_job.status = WRITING`
- `write_id` is non-null
- Process died after `WriteManager` commit, before `transition(COMPLETED)`

## Detection

```sql
SELECT job_id, status, write_id, updated_at
FROM data_sync_job
WHERE status = 'WRITING' AND write_id IS NOT NULL;
```

## Recovery (staged / operator)

1. Confirm clean table rows for `write_id` exist (no duplicate insert needed).
2. Call `DataSyncOrchestrator.recover_stuck_writing_job(job_id)`.
3. Verify `status = COMPLETED` and clean row count unchanged.

## Fail-closed guards

- Recovery **rejects** jobs not in `WRITING` with `write_id` set (`ValueError`).
- `post_write_pre_complete_hook` is **pytest-only**; production cannot inject crash hooks.

## Closure tests

- `test_syncJob_incremental_crashWindow_leavesWritingWithWriteId`
- `test_syncJob_incremental_recoverStuckWriting_completesWithoutDoubleWrite`
- `test_syncJob_recoverStuckWriting_rejectsInvalidState`
- `test_syncJob_incremental_hook_rejectedOutsidePytest`

## References

- `docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md`
- `specs/contracts/sync_job_contract.yaml` (`deferred_error` / support matrix)
