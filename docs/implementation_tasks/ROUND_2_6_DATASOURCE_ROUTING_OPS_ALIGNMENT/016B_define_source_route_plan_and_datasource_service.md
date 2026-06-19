# 016B — Define SourceRoutePlan and DataSourceService

## Scope

Design/spec only. Do not change code.

## Inputs

- `docs/modules/source_route_plan.md`
- `docs/modules/datasource_service.md`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/datasource_service_contract.yaml`

## Required design updates

1. Generate `SourceRoutePlan` before adapter construction.
2. Persist or expose route decisions with `route_status`, selected source, skipped sources, and disabled reasons.
3. Introduce `DataSourceService` as the production facade.
4. Restrict direct `create_adapter()` calls to DataSourceService and tests.
5. Ensure API/Agent only access read-only route preview or service outputs.

## Future implementation tasks

- Add `backend/app/datasources/route_models.py`.
- Add `backend/app/datasources/route_planner.py`.
- Add `backend/app/datasources/service.py`.
- Refactor sync runners to depend on service/fetch callable.

## Acceptance commands

```bash
python -m pytest tests/test_source_route_planner.py tests/test_datasource_service.py tests/test_sync_orchestrator.py tests/test_vendor_fetch_e2e.py -q
```

## Residual risk

Current code still accepts direct adapter injection in orchestrator tests and runner paths. It is verified as working but should be narrowed in the future implementation phase.
