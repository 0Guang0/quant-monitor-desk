# Orchestrator Tests Plan — Batch D（writing-plans Phase 5b）

> 完整 `def test_*` 放本文件；MASTER §8 仅列 tracer 名 + 命令。

## 8.1 migration 006

```python
def test_migration006_freshDb_createsSyncTables(migrated_con):
    """tables data_sync_job and job_event_log exist with expected columns."""

def test_migration006_initDbTwice_isIdempotent(migrated_con):
    """second init_db does not fail."""

def test_migration006_doesNotModify004Or005Checksum():
    """004/005 migration files unchanged."""
```

## 8.2 Job state machine

```python
def test_syncJob_transition_createdToPlanned_recordsEvent():
    """CREATED→PLANNED writes job_event_log with old/new status."""

def test_syncJob_invalidTransition_raises():
    """CREATED→WRITING is rejected."""

def test_syncJob_terminalState_cannotTransition():
    """COMPLETED cannot go to FETCHING."""

def test_syncJob_fullLoad_createdToPlanned_recordsEvent():
    """job_type=full_load: CREATED→PLANNED writes job_event_log; persists job_type."""

def test_syncJob_incremental_createdToPlanned_recordsEvent():
    """job_type=incremental: CREATED→PLANNED skeleton (AC-2); full E2E in §8.5."""

def test_syncJob_revisionAudit_skeletonReachesStaged():
    """job_type=revision_audit: mock fetch → STAGED only (not VALIDATING); per MASTER §4.2 AC-2 boundary."""

def test_syncJob_dataQuality_skeletonCompletesOrManualReview():
    """job_type=data_quality: PLANNED→VALIDATING→COMPLETED or MANUAL_REVIEW_REQUIRED via DataQualityValidator delegate."""
```

## 8.3 Orchestrator core

```python
def test_orchestrator_createJob_persistsDataSyncJob():
    """create_job inserts row with run_id, job_type, status=CREATED."""

def test_orchestrator_emitEvent_linksRunJobTask():
    """event_id, run_id, job_id, task_id populated."""
```

## 8.4 ResourceGuard

```python
def test_orchestrator_fetchBlockedWhenGuardPaused_setsFailedRetryable():
    """Decision.PAUSE → job status FAILED_RETRYABLE; job_event_log.message contains RESOURCE_GUARD_PAUSED; not a job status enum value."""

def test_orchestrator_fetchBlockedOnHardStop_setsFailedRetryable():
    """Decision.HARD_STOP → FAILED_RETRYABLE + RESOURCE_GUARD_PAUSED in message."""

def test_orchestrator_fetchAllowedWhenGuardOk_proceedsToFetching():
    """check() ok → status FETCHING."""
```

## 8.5 Incremental E2E

```python
def test_incrementalJob_happyPath_writesCleanAndCompletes():
    """FakeAdapter SUCCESS → adapter.fetch(con=writer, job_id) → fetch_log row → validators PASS → gate allow → WriteManager → COMPLETED."""

def test_incrementalJob_validationFailed_doesNotWriteClean():
    """staging bad data → VALIDATING fail → no clean row."""

def test_incrementalJob_repeatRun_noDuplicatePrimaryKey():
    """second incremental same cursor does not duplicate PK."""
```

## 8.6 Backfill

```python
def test_backfillJob_largeRange_splitsIntoTasks():
    """90-day range in eco → ≥3 task shards max 31 days each."""

def test_backfillJob_recordsTriggerReason():
    """trigger_reason persisted in job_event_log.payload_json (event_type BACKFILL_SHARD); not data_sync_job column."""

def test_backfillJob_eachShard_callsResourceGuardBeforeFetching():
    """multi-shard backfill: ResourceGuard.check before each shard FETCHING (MASTER §4.4)."""

def test_backfillJob_midShardFailure_preservesCompletedTasks():
    """3-shard backfill: shard 2 fails → shards 1 remain COMPLETED; job FAILED_RETRYABLE; no rollback of shard 1 clean writes."""
```

## 8.7 Reconcile

```python
def test_reconcileJob_severeConflict_entersWaitingReconcile():
    """severe conflict → WAITING_RECONCILE not READY_TO_WRITE."""

def test_reconcileJob_afterReconcile_resolvesOrManualReview():
    """reconcile-first policy matches Batch C behavior."""
```

## 8.8 Registry bootstrap

```python
def test_syncRegistry_cli_syncsYamlToDb(tmp_path):
    """scripts/sync_registry.py upserts source_registry rows."""

def test_orchestratorBootstrap_callsSyncToDb():
    """bootstrap() syncs registry when enabled."""
```

## 8.9 Smoke

```python
# Extend scripts/ci_ingestion_smoke.py (not pytest module):
# 1. assert schema_version contains 006_ingestion_sync
# 2. assert tables data_sync_job + job_event_log exist
# 3. run minimal orchestrator incremental smoke (FakeAdapter / tmp_path)
# 4. stdout must contain: orchestrator_smoke: ok
```

Evidence: `8.9-smoke.txt`（MASTER §8.9）

## Tier commands（→ MASTER §9–10）

```bash
pytest tests/test_sync_migration.py tests/test_sync_jobs.py tests/test_sync_orchestrator.py -q
pytest tests/test_batch_d_orchestration_flow.py -q
QMD_DATA_ROOT=data python scripts/ci_ingestion_smoke.py
```
