# B05_02 — Integration and Resource Smoke Gates

> **Batch:** Batch 05 — Verified Audit Security and Release Gates  
> **Owns:** production-scale/resource-smoke continuation, loose historical cards `031_implement_integration_smoke_tests.md`, `032_implement_resource_limit_tests.md`  
> **Roadmap:** Round 5.2.  
> **Execution posture:** bounded release gate only; no live source enablement and no production mutation.

---

## 1. Business purpose

Turn integration and resource-limit checks into bounded, repeatable release gates after Round 3F-R / 3G / Round4 artifacts are stable enough to test.

This task must not implement missing product features. If a dependency artifact is missing, the smoke gate should skip/fail with explicit reason according to contract, not create the feature.

---

## 2. Required QMD inputs

Read these **本项目** files before implementation:

```text
PROJECT_IMPLEMENTATION_ROADMAP.md
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/031_implement_integration_smoke_tests.md
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/032_implement_resource_limit_tests.md
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/BATCH_05_HARDENING_RULES.md
specs/contracts/resource_limits.yaml
specs/contracts/production_equivalent_smoke_budget.yaml
specs/contracts/runtime_flow_contract.yaml
specs/contracts/sandbox_clean_write_contract.yaml
specs/contracts/api_security_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_catalog.yaml
```

No reference-project source is required for this card. `参考项目/**` must not be treated as runtime workload input for smoke tests.

---

## 3. Target QMD files

Create/update QMD-owned files only:

```text
tests/test_integration_smoke.py
tests/test_resource_limits.py
tests/test_production_equivalent_smoke_budget.py
tests/test_catalog.yaml
scripts/run_integration_smoke.py
scripts/run_resource_smoke.py
docs/ops/integration_resource_smoke.md
docs/ops/release_verification.md
specs/contracts/production_equivalent_smoke_budget.yaml
specs/verification/contract_coverage.yaml
```

If final file names differ, the PR must document the mapping.

---

## 4. Implementation plan

1. **Smoke scenario inventory**
   - Define a small set of release smoke scenarios and their prerequisites.
   - Candidate scenarios:
     - API source/readiness endpoint smoke from B04_01;
     - Agent read-only tool smoke from B04_02;
     - Round3G sandbox-clean-write contract validation smoke if artifacts exist;
     - data-health profile smoke from 3F-R;
     - ResourceGuard rejection smoke.
   - Each scenario must declare whether missing dependency means `SKIP_WITH_REASON` or `FAIL_RELEASE_GATE`.

2. **Resource caps**
   - Use `resource_limits.yaml` and `production_equivalent_smoke_budget.yaml` to set row/window/memory/time caps.
   - No full-market, full-history, or minute-level default scans.
   - No uncontrolled network/live source access.

3. **Command wrapper**
   - Add a script or documented command that runs only bounded smoke tests.
   - Command must print scenario name, caps, result, and failure meaning.

4. **Test catalog**
   - Register new tests in `tests/test_catalog.yaml` with purpose and failure meaning.
   - Keep failure messages actionable: correctness vs resource budget vs missing dependency vs environment.

5. **Release posture**
   - Smoke gate must not claim production readiness beyond proven artifacts.
   - If production clean write is not enabled, tests should state that rather than attempting production mutation.

---

## 5. Forbidden scope

- No production clean write.
- No live source enablement.
- No full-market scan.
- No full-history scan.
- No minute-bar default scan.
- No use of `参考项目/**` as runtime workload.
- No release claim exceeding current production posture.
- No product feature implementation to make smoke pass.

---

## 6. Tests / gates

Required command set:

```bash
uv sync --locked
uv run pytest tests/test_integration_smoke.py tests/test_resource_limits.py tests/test_production_equivalent_smoke_budget.py -q
```

If exact test files differ, update this card, docs, and `tests/test_catalog.yaml`.

Test expectations:

- every smoke scenario has explicit caps;
- over-budget scenario fails closed;
- missing dependency has explicit skip/fail semantics;
- no live source/network is used unless explicitly authorized by environment and contract;
- production mutation is never performed;
- failure messages explain whether the issue is correctness, resource budget, environment, or missing dependency.

---

## 7. Done criteria

B05_02 is done only when bounded integration/resource smoke gates are runnable and documented. It must not close by adding prose-only smoke plans or by implementing missing product features.
