# B04_03 — Frontend ErrorBoundary and Deferred Routes

> Owns: `VR-FE-001`, `VR-FE-002`.  
> Roadmap: Round 4.3.  
> Suggested branch: `feature/round4-frontend-error-boundary-routes`.  
> Parallel: can run with API work if route shells use deferred states and do not fake API data.

---

## Goal

Move frontend from placeholder-only shell toward safe, testable route structure: minimal ErrorBoundary first, then deferred route shells for page contracts.

## Scope

- Implement minimal `AppErrorBoundary` with generic summary, retry, and sanitized error display.
- Wrap root App in ErrorBoundary.
- Add deferred route shells for page_contracts routes only if they do not call missing APIs.
- Add Vitest for fallback/retry/sanitization and deferred page rendering.

## Forbidden scope

- Do not finalize UI layout without user confirmation.
- Do not leak stack traces, tokens, absolute paths, or secrets.
- Do not call production APIs directly from route shells.
- Do not implement trading action UI.

## Gates

```bash
cd frontend && npm ci && npm run test -- --run
cd frontend && npm run typecheck && npm run build
```

## Done criteria

- `VR-FE-001` and `VR-FE-002` are resolved or precisely re-deferred.
- Placeholder App no longer lacks root error handling.
- Page contracts are not misrepresented as fully implemented pages.
