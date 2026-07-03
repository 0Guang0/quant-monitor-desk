# First Batch Self-check — Round 3 Data Production Readiness

> Scope: static self-check for the first batch of task cards created under `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/`.  
> Checked files: README + five task cards.  
> Method: rule coverage review against `GLOBAL_TASK_TEMPLATE.md`, global execution/testing/resource rules, `/to-issues`, `/tdd`, `/ponytail`, source/production safety constraints, and project deferred registries.  
> Result: no critical planning loophole identified; remaining execution risks are explicitly named below.

---

## 1. Files checked

| File                                   | Status | Notes                                                                                   |
| -------------------------------------- | ------ | --------------------------------------------------------------------------------------- |
| `README.md`                            | PASS   | Defines package scope, order, global boundaries, closure report.                        |
| `R3D_model_input_whitelist.md`         | PASS   | Covers docs/spec scope, whitelist schema, forbidden source promotions, gates.           |
| `R3E_fred_authorized_sandbox_pilot.md` | PASS   | Covers FRED-only sandbox path, auth/no-production-write, failure taxonomy, B2.5-O-05.   |
| `R3E_tdx_manual_probe_addendum.md`     | PASS   | Covers manual authorization, raw-only validation candidate, TDX disabled/default rules. |
| `R3E_real_data_staged_pilot_v3.md`     | PASS   | Covers model-driven baostock/cninfo/akshare expansion, caps, role safety.               |
| `R3E_readonly_data_health_v2.md`       | PASS   | Covers read-only evidence checking, no fetch/no DB/no source_health_snapshot.           |

---

## 2. Template coverage check

Each full task card includes the required sections from `GLOBAL_TASK_TEMPLATE.md`:

| Required section                 | R3D whitelist | FRED pilot | TDX addendum | pilot v3 | data health v2 |
| -------------------------------- | ------------- | ---------- | ------------ | -------- | -------------- |
| 1. Task goal                     | PASS          | PASS       | PASS         | PASS     | PASS           |
| 2. Expected outcome              | PASS          | PASS       | PASS         | PASS     | PASS           |
| 3. Input files                   | PASS          | PASS       | PASS         | PASS     | PASS           |
| 4. Related code/output files     | PASS          | PASS       | PASS         | PASS     | PASS           |
| 5. Existing patterns/reference   | PASS          | PASS       | PASS         | PASS     | PASS           |
| 6. Technical constraints         | PASS          | PASS       | PASS         | PASS     | PASS           |
| 7. Resource constraints          | PASS          | PASS       | PASS         | PASS     | PASS           |
| 8. Boundary constraints          | PASS          | PASS       | PASS         | PASS     | PASS           |
| 9. Implementation steps          | PASS          | PASS       | PASS         | PASS     | PASS           |
| 10. Testing requirements         | PASS          | PASS       | PASS         | PASS     | PASS           |
| 11. Acceptance commands          | PASS          | PASS       | PASS         | PASS     | PASS           |
| 12. Done criteria                | PASS          | PASS       | PASS         | PASS     | PASS           |
| 13. Red Flags                    | PASS          | PASS       | PASS         | PASS     | PASS           |
| 14. Output requirements          | PASS          | PASS       | PASS         | PASS     | PASS           |
| 15. Audit repair mandatory items | PASS          | PASS       | PASS         | PASS     | PASS           |

---

## 3. Execution-discipline coverage

| Discipline             | Coverage decision | Evidence in cards                                                                       |
| ---------------------- | ----------------- | --------------------------------------------------------------------------------------- |
| `/to-issues`           | PASS              | README and every task require vertical slices before execution.                         |
| `/tdd`                 | PASS              | Code tasks require RED → GREEN tracer bullets and behavior-first tests.                 |
| `/ponytail`            | PASS              | Cards forbid broad abstractions, full-market scans, and drive-by refactors.             |
| `/karpathy-guidelines` | PASS              | README requires simple/direct/inspectable code; cards prefer narrow paths.              |
| `/testing-guidelines`  | PASS              | Cards require business-semantic assertions and test purpose annotations.                |
| No test-goal mutation  | PASS              | README and cards state tests must keep purpose/goal and cannot be changed only to pass. |

---

## 4. Source and production safety coverage

| Risk                                          | Covered? | Where covered                                                                                  |
| --------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------- |
| Production clean write accidentally enabled   | PASS     | README + all cards forbid it; data health v2 explicitly forbids source_health_snapshot writes. |
| Production-live readiness overclaim           | PASS     | README and all source cards forbid production-live language.                                   |
| Full-market/full-history accidental ingestion | PASS     | Whitelist, FRED, TDX, and pilot v3 define hard caps and forbid broad scans.                    |
| FRED misclosed by macro_supplementary         | PASS     | Whitelist, FRED, and data health v2 explicitly forbid this.                                    |
| AkShare promoted to Primary                   | PASS     | Whitelist, pilot v3, and data health v2 forbid this and require tests.                         |
| TDX promoted to production primary            | PASS     | TDX card and README forbid; tests require disabled/validation-only posture.                    |
| Live network without authorization            | PASS     | FRED and TDX cards require explicit authorization and dry-run/mocked fallback.                 |
| Production DB mutation hidden                 | PASS     | FRED/TDX/pilot v3 require no-mutation/no-open proof; data health v2 forbids DB writes.         |
| Source conflict auto-overwrite                | PASS     | pilot v3 requires dry-run conflict summary and forbids clean-table overwrite.                  |
| Fixture/staged data sold as production        | PASS     | README and data health v2 forbid production claims from staged/fixture evidence.               |

---

## 5. Gate coverage by task

### `R3D_model_input_whitelist.md`

Required gates:

- Required whitelist fields defined.
- Role/readiness semantics defined.
- AkShare/TDX/FRED forbidden promotions defined.
- Output files proposed.
- Docs/spec validation tests recommended.
- No implementation/fetch/DB mutation allowed.

Self-check result: PASS.

### `R3E_fred_authorized_sandbox_pilot.md`

Required gates:

- Registry/capability guard.
- Route preview guard.
- Mock fetch evidence.
- Failure taxonomy.
- Data health checks.
- `B2.5-O-05` close/re-defer logic.
- No production DB mutation.

Self-check result: PASS.

### `R3E_tdx_manual_probe_addendum.md`

Required gates:

- Manual authorization gate.
- Optional dependency failure handling.
- Equity/index/security-list probes capped.
- TDX remains disabled-by-default and validation-only.
- No closure of Eastmoney/AkShare rows without explicit alternate-path evidence.
- No production DB mutation.

Self-check result: PASS.

### `R3E_real_data_staged_pilot_v3.md`

Required gates:

- Depends on whitelist.
- baostock/cninfo/akshare caps.
- cninfo metadata-only.
- AkShare validation-only.
- source conflict dry-run only.
- source readiness matrix.
- no production DB mutation.

Self-check result: PASS.

### `R3E_readonly_data_health_v2.md`

Required gates:

- Reads evidence only.
- Does not fetch.
- Does not write DB.
- Does not implement `source_health_snapshot`.
- Distinguishes PASS/WARN/FAIL/BLOCKED.
- Checks FRED/TDX/AkShare role semantics.
- Checks sandbox-clean eligibility conservatively.

Self-check result: PASS.

---

## 6. Dependency and execution-order check

| Dependency                                               | Captured? | Notes                                                                                                |
| -------------------------------------------------------- | --------- | ---------------------------------------------------------------------------------------------------- |
| pilot v3 depends on model input whitelist                | PASS      | `R3E_real_data_staged_pilot_v3.md` blocks when `specs/model_inputs/**` does not exist.               |
| data health v2 depends on evidence from earlier tasks    | PASS      | `R3E_readonly_data_health_v2.md` checks FRED/TDX/v3 evidence and blocks on missing whitelist.        |
| sandbox clean-write must wait                            | PASS      | README states sandbox clean-write rehearsal must not start until first-batch gates and Layer5 close. |
| production clean write must wait                         | PASS      | README and source cards forbid production clean write.                                               |
| TDX addendum is not a replacement for 018C               | PASS      | TDX card explicitly references and extends 018C/reference landing.                                   |
| FRED task is distinct from macro_supplementary semantics | PASS      | FRED card explicitly forbids substitution.                                                           |

---

## 7. Remaining execution risks explicitly carried forward

These are not missing task-card requirements; they are real execution risks that must remain visible:

1. **FRED authorization/API access may be absent.**  
   Cards require mocked/dry-run tests plus explicit `FAIL_AUTH` / re-defer handling.

2. **TDX local connectivity may be unavailable.**  
   TDX card requires optional dependency and network failure taxonomy; default CI must not require live TDX.

3. **Model input whitelist may expose ambiguous business choices.**  
   Whitelist card requires P0/P1/P2/deferred classification and user decision if ambiguity remains.

4. **New docs/spec files may require docs index updates.**  
   Cards include `scripts/check_docs_specs_indexed.py` as a suggested docs/spec validation command.

5. **Source readiness does not equal production readiness.**  
   README and cards preserve this boundary; later `R3G` production-entry task cards are still needed.

---

## 8. Items intentionally not covered by this first batch

These remain out of scope and should be handled by later task-card batches:

- Full `023` Layer5 evidence chain execution.
- Batch6 migration 008.
- `qmd data` production CLI.
- `source_health_snapshot` table.
- Backfill/reconcile parity.
- Sandbox clean-write rehearsal.
- Pre-production adversarial audit.
- Limited production clean write.
- Round4 API/UI/notifications.
- Round5 release/security hardening.

This is intentional; including them here would make the first batch too broad and increase execution drift risk.

---

## 9. Final self-check verdict

**Verdict: PASS_FOR_PLANNING.**

The first-batch task cards are detailed enough for execution planning and contain the critical business goal, scope, forbidden scope, gate, test, and safety constraints. I did not identify a critical loophole that would let an executor legitimately claim production readiness, enable production clean write, run full-market ingestion, or promote validation-only sources from these cards.

Before implementation begins, each card must still be converted into concrete `/to-issues` vertical slices and assigned to a branch/worktree with allowed files, forbidden files, and merge-gate commands.
