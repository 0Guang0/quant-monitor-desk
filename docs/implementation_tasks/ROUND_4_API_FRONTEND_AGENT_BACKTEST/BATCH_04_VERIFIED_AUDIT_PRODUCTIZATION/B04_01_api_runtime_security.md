# B04_01 — API Runtime and Security Contract Implementation

> **Batch:** Batch 04 — Verified Audit Productization  
> **Owns:** `VR-API-001`, loose historical card `024_implement_fastapi_routes.md`  
> **Roadmap:** Round 4.1 track.  
> **Execution posture:** read-only API vertical slice; no write endpoint; no free SQL.

---

## 1. Business purpose

Turn API security contracts from YAML/docs-only checks into the first real read-only HTTP vertical slice. The first slice must expose authenticated source/capability/readiness posture for frontend and Agent consumers without allowing arbitrary SQL, direct DB mutation, or unbounded pagination.

This task is not complete if it only creates an empty FastAPI app or router shell.

---

## 2. Required QMD inputs

Read these **本项目** files before implementation:

```text
specs/contracts/api_security_contract.yaml
specs/contracts/datasource_service_contract.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/source_route_contract.yaml
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
docs/modules/data_sources.md
docs/modules/source_route_plan.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/024_implement_fastapi_routes.md
```

Reference projects are not required for this API security slice. If provider metadata is surfaced, use the QMD provider catalog produced by R3FR-05; do not read OpenBB runtime code in this task.

---

## 3. Target QMD files

Create or update QMD-owned files only:

```text
backend/app/api/__init__.py
backend/app/api/app.py
backend/app/api/auth.py
backend/app/api/security.py
backend/app/api/routes/sources.py
backend/app/api/schemas/sources.py
backend/app/datasources/service.py
backend/app/datasources/source_registry.py
backend/app/datasources/source_capabilities.py
backend/app/core/resource_guard.py
specs/contracts/api_security_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_api_security_contract.py
tests/test_api_sources.py
tests/test_catalog.yaml
```

If file names differ, the PR must document the mapping in the task result.

---

## 4. Implementation plan

1. **FastAPI app boundary**
   - If `backend/app/api/app.py` is absent, create a minimal app factory such as `create_app(settings) -> FastAPI`.
   - Register only read-only routers in this task.
   - Do not mount write, admin, source-fetch, or SQL routes.

2. **Auth/security middleware**
   - Implement token-based guard or existing project security guard from `api_security_contract.yaml`.
   - Production startup must fail closed if auth is disabled or token/config is missing.
   - Test unauthenticated request, invalid token, and valid token.

3. **Endpoint**
   - Add `GET /api/sources` or equivalent route.
   - Route must call QMD service/registry/capability code, not parse YAML directly in route handler except through an approved loader.
   - Route must include active, sandbox-candidate, and proposed-disabled sources so operators can see disabled posture without triggering fetch.
   - Route must return bounded, schema-validated response.

4. **Response fields**
   - Required fields per source/provider candidate:
     - `source_id`
     - `provider_id`
     - `source_type`
     - `license_type`
     - `domains`
     - `capabilities`
     - `route_status`
     - `status` such as `active`, `sandbox_candidate`, or `proposed_disabled_source`
     - `enabled_by_default`
     - `production_default_candidate`
     - `production_default_enabled`
     - `auth_required`
     - `quality_role`
     - `limits`
     - `limitations`
     - `evidence_or_contract_refs`
   - Do not expose secrets, credential paths, raw tokens, or local absolute paths.

5. **Pagination and budget**
   - Enforce default and maximum page size from `api_security_contract.yaml`.
   - ResourceGuard or equivalent query-budget check must reject unbounded requests.
   - No free-form SQL parameter is allowed.

6. **Contract coverage**
   - Update `specs/verification/contract_coverage.yaml` if new tests become canonical for API security/source list contract coverage.
   - Update `tests/test_catalog.yaml` if new test files are added.

---

## 5. Forbidden scope

- No free SQL endpoint.
- No write endpoints.
- No source fetch trigger.
- No production clean write.
- No direct mutation of registry/capability files from API.
- No OpenBB runtime dependency or copied OpenBB source.
- No frontend implementation in this task.

---

## 6. Tests / gates

Required commands:

```bash
uv sync --locked
uv run pytest tests/test_api_security_contract.py tests/test_api_sources.py -q
uv run pytest tests/test_source_capabilities.py tests/test_source_registry.py -q
uv run ruff check backend/app/api backend/app/datasources tests
```

Test expectations:

- unauthenticated request is rejected;
- valid token can read the bounded source/capability list;
- page-size overflow is rejected;
- free SQL parameter is rejected;
- production startup fails if auth is disabled or token missing;
- response includes `source_type`, `license_type`, source status, and production posture fields and does not leak secrets;
- proposed-disabled sources are visible as disabled/readiness entries but do not become fetchable;
- endpoint does not perform source fetch or DB write.

---

## 7. Done criteria

B04_01 is done only when the API package serves a real authenticated read-only source/capability/readiness endpoint and tests prove the security and budget contract. Router-only scaffolding is not acceptable.
