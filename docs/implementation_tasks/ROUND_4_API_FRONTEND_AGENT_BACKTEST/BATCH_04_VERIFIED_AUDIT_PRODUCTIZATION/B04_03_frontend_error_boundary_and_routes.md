# B04_03 — Frontend ErrorBoundary and First API-Bound Page

> **Batch:** Batch 04 — Verified Audit Productization  
> **Owns:** `VR-FE-001`, `VR-FE-002`, loose historical cards `026_implement_frontend_shell.md`, `027_implement_frontend_layer_pages.md`  
> **Roadmap:** Round 4.3 track.  
> **Execution posture:** frontend read-only productization; no direct DB; no trading-action UI.

---

## 1. Business purpose

Move the frontend from placeholder-only shell to a safe, testable first user-visible vertical slice: root ErrorBoundary plus one API-bound source/readiness or data-health page/panel. Deferred route shells are allowed only for pages outside this owned first slice.

This task is not complete if it only adds ErrorBoundary and deferred pages.

---

## 2. Required QMD inputs

Read these **本项目** files before implementation:

```text
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/026_implement_frontend_shell.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/027_implement_frontend_layer_pages.md
specs/contracts/api_security_contract.yaml
specs/contracts/datasource_service_contract.yaml
specs/contracts/source_capability_contract.yaml
docs/modules/data_sources.md
docs/modules/source_route_plan.md
docs/modules/data_validation_and_conflict.md
```

Also inspect current frontend source before changing:

```text
frontend/package.json
frontend/src/main.tsx
frontend/src/App.*
frontend/src/routes/**
frontend/src/api/**
frontend/src/components/**
frontend/src/tests/**
```

If a listed path does not exist, create the narrow equivalent and document the mapping in the PR/task result.

---

## 3. Reference project source to inspect

Read these files under `参考项目/**` as UI/artifact references only:

```text
参考项目/agents-for-openbb/40-vanilla-agent-dashboard-widgets/vanilla_agent_dashboard_widgets/main.py
参考项目/agents-for-openbb/39-vanilla-agent-html-artifacts/vanilla_agent_html/main.py
参考项目/agents-for-openbb/34-vanilla-agent-tables/vanilla_agent_tables/main.py
参考项目/OpenBB/desktop/src/components/
参考项目/OpenBB/desktop/src/routes/
```

Useful ideas to adapt into QMD-owned frontend code:

- dashboard/widget summary shape: concise table/list of source/readiness facts;
- explicit loading/empty/error/success states;
- route-level separation and reusable components;
- sanitized descriptions and capped field length from agents-for-openbb examples.

Must not copy:

- OpenBB runtime UI source wholesale;
- OpenBB/agents dependencies;
- remote widget data fetch behavior;
- broad dashboard search;
- any UI element that implies buy/sell/order/position action.

---

## 4. Target QMD files

Create/update QMD-owned files only:

```text
frontend/src/App.tsx
frontend/src/main.tsx
frontend/src/api/client.ts
frontend/src/api/sources.ts
frontend/src/components/AppErrorBoundary.tsx
frontend/src/components/SourceReadinessPanel.tsx
frontend/src/routes/SourceReadinessPage.tsx
frontend/src/routes/DeferredRoute.tsx
frontend/src/tests/AppErrorBoundary.test.tsx
frontend/src/tests/SourceReadinessPage.test.tsx
frontend/src/tests/DeferredRoute.test.tsx
```

If final file names differ, the PR must document the mapping.

---

## 5. Implementation plan

1. **Error boundary**
   - Implement `AppErrorBoundary` with sanitized error summary, retry action, and no stack trace/token/path leak.
   - Wrap root app in the boundary.

2. **Typed API client**
   - Implement a typed client for the B04_01 source/capability/readiness endpoint.
   - The client must not embed production hostnames or tokens.
   - Fetch logic must surface HTTP/auth/schema errors distinctly.

3. **First API-bound page/panel**
   - Implement one page/panel such as `SourceReadinessPage` or `DataHealthReadinessPanel`.
   - It must render loading, error, empty, and success states.
   - Success state must display real fields from the B04_01 endpoint, including production posture and limitations.
   - Empty/deferred states must be visibly labeled; do not fake sample success data.

4. **Deferred routes**
   - Add deferred route shells for remaining page contracts only if they clearly show `DEFERRED_PAGE` / unavailable state.
   - Deferred routes must not call missing APIs or show hardcoded success fixtures.

5. **No-action UI guard**
   - UI copy must not contain trading-action language such as buy/sell/add/reduce/position instructions.
   - If source/readiness risks are shown, they should be risk/status/human-review language only.

---

## 6. Forbidden scope

- No direct DB access from frontend.
- No production write/fetch trigger.
- No trading action buttons or order semantics.
- No stack trace, token, local path, or secret leakage.
- No copied OpenBB/agents-for-openbb runtime code.
- No close-by-deferred-only implementation.

---

## 7. Tests / gates

Required commands:

```bash
cd frontend && npm ci && npm run test -- --run
cd frontend && npm run typecheck && npm run build
```

Test expectations:

- ErrorBoundary renders sanitized fallback and retry;
- API-bound page renders loading/error/empty/success states;
- success state uses fields returned by API mock, not hardcoded fake production readiness;
- deferred pages are visibly deferred;
- no trading action terms appear in owned UI strings;
- build/typecheck pass.

---

## 8. Done criteria

B04_03 is done only when at least one frontend page/panel is bound to a real read-only API/client contract with tested states. ErrorBoundary plus deferred route shells alone is not acceptable.
