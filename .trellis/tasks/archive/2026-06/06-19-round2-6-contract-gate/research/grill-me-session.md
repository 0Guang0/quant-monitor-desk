# Grill-Me Session — Contract Gate

## Doubt 1: Are we accidentally implementing Phase C in Task 1?

Reconcile: no. Task 1 may add tests and a static checker. It must not add `DataSourceService`, `SourceRoutePlanner`, or production route persistence. Contract tests may fail initially and be satisfied only by minimal test scaffolding if explicitly scoped; production implementation belongs to Task 2.

## Doubt 2: Is `qmt_xqshare` required before Round3?

Reconcile: no. The pre-Round3 gate only requires platform matrix and disabled-source contract tests. The adapter/source enablement is deferred until user authorization.

## Doubt 3: Could stale deferred registry rows mislead Round3?

Reconcile: yes. This task must reconcile `docs/AUDIT_DEFERRED_REGISTRY.md`; implemented items should move to RESOLVED or be rewritten with current task hooks.

## Doubt 4: Could tests assert internals instead of business behavior?

Reconcile: use business assertions: route_status, selected_source_id nullness, disabled_reason, quality_flags, domain coverage, import violation detection, dry-run no write, default dependency exclusion.

## Doubt 5: Should root `ROUND2_6_PHASE_A_SELF_CHECK.md` be deleted now?

Reconcile: not until its content is migrated into Trellis research and MASTER/AUDIT. Task 1 can migrate it to research and either keep it for Task 2 or mark removal as Task 2 cleanup.
