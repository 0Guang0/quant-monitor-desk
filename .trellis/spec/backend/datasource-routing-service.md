# Datasource Routing Service (Round 2.6)

> Executable contracts for `CapabilityRegistry` → `SourceRoutePlanner` → `DataSourceService` → sync runners.

---

## Scenario: Production fetch via DataSourceService

### 1. Scope / Trigger

- Changes to `backend/app/datasources/{capability_registry,route_planner,route_models,service}.py`
- Sync incremental path using `datasource_service` / `fetch_callable` in `orchestrator.py` / `runners.py`
- Route plan events in `job_event_log.payload_json`

### 2. Signatures

```python
class DataSourceService:
    def preview_route(
        self, *, data_domain: str, operation: str, run_id: str = "preview", job_id: str = "preview", ...
    ) -> SourceRoutePlan: ...

    def fetch(
        self,
        req: FetchRequest,
        *,
        con,
        job_id: str | None = None,
        operation: str | None = None,
        on_enter_fetching: Callable[[], None] | None = None,
    ) -> FetchResult: ...

class SourceRoutePlanner:
    def plan(
        self, *, data_domain: str, operation: str, run_id: str, job_id: str, ...
    ) -> SourceRoutePlan: ...
```

`FetchCallable = Callable[..., FetchResult]` — service wrapper may accept `operation=` kwarg.

### 3. Contracts

| Step                   | Rule                                                                                                                                                                                                                                      |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Gate order             | route plan → ResourceGuard → capability assert → `on_enter_fetching()` → `create_adapter` (internal) → adapter.fetch → fetch_log                                                                                                          |
| fetch_log single-write | When adapter is `BaseDataAdapter`, service passes `record_fetch_log=False` to `adapter.fetch`; service writes the sole `fetch_log` row. Subclasses that override `fetch` must accept and forward `record_fetch_log` to `super().fetch()`. |
| ROUTE_PLAN event       | Emitted when `job_id` is set; payload includes `run_id`, `job_id`, `route_plan_id`, `route_status`, `candidates`, `created_at`                                                                                                            |
| Guard block            | Re-emit ROUTE_PLAN with `route_status=RESOURCE_GUARD_PAUSED`, `selected_source_id=null`; raise `ResourceGuardBlockedError` with `format_pause_event` message                                                                              |
| Non-READY route        | Return `FetchResult(status=DISABLED_SOURCE)` **and** write fetch_log (never skip fetch_log on disabled paths)                                                                                                                             |
| Capability             | `is_capability_declared` must use `resolve_registry_domain` (legacy adapter domain → registry domain)                                                                                                                                     |
| USER_AUTH_REQUIRED     | Planner sets when skip_reason contains `user_authorization` **or** starts with `missing_env:`                                                                                                                                             |
| Module boundary        | Only `DataSourceService` may call `create_adapter` in production code; sync runners use `fetch_callable`                                                                                                                                  |

**Deferred (Round 3):** `run_backfill` / `run_reconcile` still require direct `adapter`; validation-source clean-table write rule not enforced in sync write path.

### 4. Validation & Error Matrix

| Condition                        | Behavior                                                                |
| -------------------------------- | ----------------------------------------------------------------------- |
| `ResourceGuard` PAUSE/HARD_STOP  | `FAILED_RETRYABLE` via runner; message contains `RESOURCE_GUARD_PAUSED` |
| `route_status != READY`          | `DISABLED_SOURCE` fetch result + fetch_log row                          |
| Unknown capability at fetch time | `DISABLED_SOURCE` + fetch_log                                           |
| Guard block before adapter       | No fetch_log row (adapter never entered)                                |
| `preview_route`                  | No DB writes, no adapter, no fetch_log                                  |

### 5. Good / Base / Bad Cases

**Good:** `orch.run_incremental(spec, datasource_service=service, clean_table=...)` — ROUTE_PLAN before FETCHING, full validation/write pipeline.

**Base:** `service.fetch(req, con=con, job_id=job_id)` with monkeypatched `ResourceGuard.check → OK`.

**Bad:** Tests import `create_adapter` from sync runners; duplicate contract-only `ContractSourceRoutePlanner` in tests; bypass service with custom fetch that skips route plan.

### 6. Tests Required

| Focus                     | Assertion points                                                              |
| ------------------------- | ----------------------------------------------------------------------------- |
| Gate order                | guard before `on_enter_fetching` before adapter                               |
| Disabled route            | fetch_log status `DISABLED_SOURCE`, row_count 0                               |
| Guard block               | 2 ROUTE_PLAN events; second `RESOURCE_GUARD_PAUSED`; fetch_log count 0        |
| USER_AUTH                 | route payload `USER_AUTH_REQUIRED`; fetch_log `DISABLED_SOURCE`               |
| Orchestrator service path | guard block → `FAILED_RETRYABLE`; disabled route → `FAILED_FINAL`             |
| Smoke                     | `--use-service-path` emits `shard_count_benchmark`, `guard_status=observable` |

### 7. Wrong vs Correct

#### Wrong

```python
# Skip fetch_log on disabled route
if plan.route_status != "READY":
    return FetchResult(..., status="DISABLED_SOURCE")

# Guard block with raw reason string only
raise ResourceGuardBlockedError(reason or decision.value)
```

#### Correct

```python
if plan.route_status != "READY":
    result = FetchResult(..., status="DISABLED_SOURCE", ...)
    self._fetch_log.write(con, result, req=req, job_id=job_id)
    return result

message = format_pause_event(decision, reason, snap, guard.profile)
raise ResourceGuardBlockedError(message, decision=decision)
```

---

## Test helpers

- `tests/service_path_support.py`: `production_route_planner()`, `plan_route()`, `patch_create_test_adapter_for_staging()` — use instead of duplicate contract planners.
- Platform matrix tests must call production planner, not legacy test-only planner.

---

## Anti-patterns

| Don't                                                | Why                                                                |
| ---------------------------------------------------- | ------------------------------------------------------------------ |
| `ContractSourceRoutePlanner` in tests                | Duplicates production logic; use `service_path_support.plan_route` |
| `ServiceWithStaging` fetch override                  | Bypasses real service gate order                                   |
| `del fetch_operation` in runners                     | Pass `operation=` through to service fetch wrapper                 |
| Treat `missing_env:*` as generic NO_AVAILABLE_SOURCE | Should map to `USER_AUTH_REQUIRED` for operator clarity            |
