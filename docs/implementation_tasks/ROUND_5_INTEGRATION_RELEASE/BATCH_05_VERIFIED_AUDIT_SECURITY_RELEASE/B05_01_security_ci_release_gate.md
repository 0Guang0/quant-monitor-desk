# B05_01 — Security CI Release Gate

> **Batch:** Batch 05 — Verified Audit Security and Release Gates  
> **Owns:** `VR-SEC-001`, loose historical cards `033_implement_security_and_boundary_tests.md`, `034_implement_docs_consistency_check.md`  
> **Roadmap:** Round 5.1.  
> **Execution posture:** release gate only; no product feature implementation.

---

## 1. Business purpose

Integrate secret scanning and backend/frontend dependency/security checks into release CI so security posture is enforced by runnable gates, not only documented as future work.

This task must not implement API/frontend/Agent/backtest/data-source features. If a product capability is missing, record it as a release blocker or manifest limitation; do not add it here.

---

## 2. Required QMD inputs

Read these **本项目** files before implementation:

```text
PROJECT_IMPLEMENTATION_ROADMAP.md
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/033_implement_security_and_boundary_tests.md
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/034_implement_docs_consistency_check.md
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/BATCH_05_HARDENING_RULES.md
docs/implementation_tasks/GLOBAL_TESTING_POLICY.md
docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md
specs/contracts/api_security_contract.yaml
specs/contracts/module_boundary_contract.yaml
specs/contracts/dependency_extras_contract.yaml
specs/contracts/user_input_privacy_contract.yaml
tests/test_catalog.yaml
```

No reference-project source is needed for this card. `参考项目/**` must not be scanned as if it were QMD runtime unless the scan tool is explicitly configured to treat it as reference-only and not product code.

---

## 3. Target QMD files

Create/update QMD-owned files only:

```text
.github/workflows/security.yml
.github/workflows/ci.yml
pyproject.toml
uv.lock
package.json
frontend/package.json
docs/ops/security_release_gate.md
docs/ops/release_verification.md
specs/verification/contract_coverage.yaml
tests/test_catalog.yaml
```

If the project uses a different CI path, document the mapping in the PR/task result.

---

## 4. Implementation plan

1. **Secret scanning gate**
   - Add gitleaks or equivalent secret scanning command.
   - Configure allowlist for known false positives only with explicit comments.
   - Ensure `参考项目/**` is handled deliberately: either included as reference scan with separate findings, or excluded with documented reason.

2. **Python/backend security scan**
   - Add at least one backend/Python security/dependency check, such as `pip-audit`, `bandit`, or semgrep.
   - Start report-only if baseline findings require triage; record when it becomes hard-fail.
   - Do not make the job green by disabling relevant findings silently.

3. **Frontend/dependency scan**
   - If frontend package exists, add bounded npm audit or equivalent dependency scan.
   - Do not treat npm audit alone as complete security closure.

4. **Module/security boundary tests**
   - Ensure existing boundary tests remain part of release gate:
     - API security contract;
     - module boundary contract;
     - dependency extras contract;
     - privacy/no-free-web source policy where tests exist.

5. **Documentation**
   - Record exact commands, expected failure meaning, and staged rollout status in `docs/ops/security_release_gate.md` or equivalent.
   - Update `tests/test_catalog.yaml` for new security test/gate entries.

---

## 5. Forbidden scope

- No product feature implementation.
- No source enablement.
- No production clean write.
- No new API/frontend/Agent/backtest capability.
- No committing sample secrets or real credentials.
- No disabling existing tests to make security CI green.
- No deleting historical task/evidence files.

---

## 6. Tests / gates

Required command set should include:

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
# plus configured security jobs, for example:
gitleaks detect --no-git
uv run pip-audit
uv run bandit -r backend/app
```

If exact tools differ, update this card, CI config, and ops docs with the final commands.

Test/gate expectations:

- secret scan command is runnable;
- backend security/dependency scan command is runnable;
- CI exposes security gate as distinct job or documented stage;
- report-only exceptions are listed with owner and closure gate;
- `VR-SEC-001` is resolved or precisely re-deferred.

---

## 7. Done criteria

B05_01 is done only when security gates are runnable, documented, and wired into CI/release verification. It must not close by only adding prose.
