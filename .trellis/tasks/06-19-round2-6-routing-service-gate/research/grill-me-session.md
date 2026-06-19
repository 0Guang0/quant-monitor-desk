# Grill-Me Session — Routing Service Gate

## Doubt 1: Should this task add a `source_route_log` migration?

Reconcile: default no. Use existing `job_event_log.payload_json` first. If insufficient, Execute must stop, write ADR draft, and ask user before adding migration.

## Doubt 2: Should this task implement qmt_xqshare adapter?

Reconcile: no. It remains proposed disabled source until user authorizes remote host/port and QMT permissions.

## Doubt 3: Could runner refactor become too large?

Reconcile: keep runners split. Inject `DataSourceService` or a narrow `fetch_callable`; do not redesign orchestration state machine.

## Doubt 4: What is minimum before Round3?

Reconcile: capability/domain alignment, explicit route plan before fetch, service facade production path, module boundary green, fixture-scale service-path E2E, production-equivalent smoke, clean deferred registry.
