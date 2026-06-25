# B04_01 — API Runtime and Security Contract Implementation

> Owns: `VR-API-001`.  
> Roadmap: Round 4.1.  
> Suggested branch: `feature/round4-backend-api-security`.  
> Parallel: can run before frontend pages; Agent endpoints wait for Agent policy runtime.

---

## Goal

Turn API security contracts from YAML-only checks into minimal HTTP runtime behavior, starting with read-only source/capability APIs.

## Scope

- Implement minimal FastAPI app/router if still absent.
- Add `GET /api/sources` or equivalent source capability list endpoint.
- Enforce auth/page-size/query budget from `api_security_contract.yaml`.
- Prod startup must fail if auth is disabled or token missing.
- Add HTTP pytest for unauthenticated request, page size overflow, token mapping, and deferred role behavior.

## Forbidden scope

- No free SQL endpoint.
- No write endpoints.
- No frontend implementation in this branch.
- No production clean write.

## Gates

```bash
uv sync --locked
uv run pytest tests/test_api_security_contract.py tests/test_api_sources.py -q
uv run ruff check backend/app/api tests
```

## Done criteria

- `VR-API-001` resolved or precisely re-deferred.
- backend API package is no longer only an empty shell for the owned endpoint.
- HTTP runtime behavior maps to contract tests.
