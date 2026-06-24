# Batch 01 Task Card Manifest

> Batch: `BATCH_01_MODEL_SOURCE_READINESS`  
> Scope: first execution batch for model-input whitelist, controlled source pilots, and source-readiness health checks.  
> This manifest is the batch-level source of truth for which task cards are included. It does not move legacy cards; it binds them into this batch while preserving canonical historical paths.

---

## 1. Included forward cards

| ID        | Canonical card                            | Required predecessor                     | Main output                                                | Execution status                                 |
| --------- | ----------------------------------------- | ---------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------ |
| `B01-C01` | `../R3D_model_input_whitelist.md`         | `PROJECT_IMPLEMENTATION_ROADMAP.md`      | `specs/model_inputs/**`, `model_input_readiness_matrix.md` | First task                                       |
| `B01-C02` | `../R3E_fred_authorized_sandbox_pilot.md` | `B01-C01` P0/P1 macro whitelist          | `fred` sandbox/raw pilot evidence                          | After or alongside whitelist close               |
| `B01-C03` | `../R3E_tdx_manual_probe_addendum.md`     | User authorization policy; legacy `018C` | TDX raw-only probe evidence or re-defer status             | Parallel with FRED if authorized                 |
| `B01-C04` | `../R3E_real_data_staged_pilot_v3.md`     | `B01-C01` model input whitelist          | v3 staged/raw evidence and source readiness matrix         | After whitelist                                  |
| `B01-C05` | `../R3E_readonly_data_health_v2.md`       | Evidence from C01–C04 as available       | PASS/WARN/FAIL/BLOCKED source-readiness report             | After evidence exists; can develop with fixtures |

### Parallel Wave D / hygiene (not forward cards; playbook SSOT)

| ID        | Branch / scope                                                       | Canonical authority                                                                | Main output                                           | Notes                                                                                                  |
| --------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `B01-LIN` | `fix/round3-batch6-lineage-and-layer3-hygiene` · roadmap Batch 3D.3  | `PROJECT_IMPLEMENTATION_ROADMAP.md` 3D.3 · `ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` | lineage/L3 hygiene tests + registry deltas (proposed) | debt-lite; must not touch `layer5_evidence/**`                                                         |
| `B01-023` | `feature/round3-023b-evidence-chain-full` · Wave D (serial mainline) | `023_implement_layer5_evidence_chain.md` · MAP §2.3                                | full Layer5 evidence chain                            | **Parallel worktree OK**; **separate merge track** from Batch 01 package (see coordinator playbook §0) |

---

## 2. Included legacy/original cards

| ID        | Canonical legacy card                                                                | Included for                           | Batch-level interpretation                                                                             |
| --------- | ------------------------------------------------------------------------------------ | -------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `B01-L01` | `../../ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md`                     | TDX sidecar-probe boundaries           | Superseded only where `R3E_tdx_manual_probe_addendum.md` is stricter; otherwise remains authoritative. |
| `B01-L02` | `../../ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_real_data_staged_pilot_v2.md`          | v2 staged pilot patterns               | Historical predecessor; v3 must not reuse v2 to bypass whitelist.                                      |
| `B01-L03` | `../../ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_readonly_data_health_v1.md`            | Read-only health patterns              | Historical predecessor; v2 must not write `source_health_snapshot`.                                    |
| `B01-L04` | `../../ROUND_3_PARALLEL_PROMPTS/PROMPT_04_debt_r3b275_fred_staged_semantics.md`      | FRED staged semantics                  | Macro supplementary remains not-FRED.                                                                  |
| `B01-L05` | `../../ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md`                   | Production-live/sandbox boundary       | Does not authorize production clean write for Batch 01.                                                |
| `B01-L06` | `../../ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_staged_pilot_v2_execution_addendum.md` | v2 discipline/test-quality constraints | Still applies to v3 unless stricter Batch 01 rules override.                                           |

---

## 3. Dependency graph

```text
PROJECT_IMPLEMENTATION_ROADMAP
  -> B01-C01 model input whitelist
      -> B01-C02 FRED sandbox pilot
      -> B01-C04 real-data staged pilot v3
      -> B01-C05 read-only data health v2

B01-L01 legacy TDX 018C
  -> B01-C03 TDX manual probe addendum
      -> B01-C05 read-only data health v2

B01-L02 staged pilot v2
  -> B01-C04 pilot v3

B01-L03 data health v1
  -> B01-C05 data health v2
```

---

## 4. Merge and branch ownership

Recommended branch ownership:

| Branch                                         | Owns                                                                       | Must not own                                          |
| ---------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------- |
| `chore/round3-model-input-whitelist`           | `specs/model_inputs/**`, `docs/quality/model_input_readiness_matrix.md`    | runtime fetch code, DB migration                      |
| `feature/round3-fred-authorized-sandbox-pilot` | `fred` registry/capability sandbox entries, FRED pilot code/tests/evidence | production clean write, non-FRED macro substitution   |
| `debt/round3-tdx-manual-probe`                 | TDX probe addendum execution artifacts and narrow probe code/tests         | production primary/fallback, Layer2 production source |
| `feature/round3-real-data-staged-pilot-v3`     | whitelist-driven baostock/cninfo/akshare v3 pilot                          | FRED/TDX/QMT/Yahoo production enablement              |
| `feature/round3-readonly-data-health-v2`       | read-only evidence health profiles                                         | fetch code, source_health_snapshot writer, migration  |
| `fix/round3-batch6-lineage-and-layer3-hygiene` | lineage/L3 hygiene per roadmap 3D.3                                        | `layer5_evidence/**`, schema expansion                |

> **Wave D (separate merge track):** `feature/round3-023b-evidence-chain-full` — see `docs/quality/coordination/BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §0.

---

## 5. Registry ownership

No card may close a deferred registry row by implication. Closure requires exact evidence and must update the relevant registry row in the same branch or explicitly re-defer.

| Registry row / family         | Closure owner in Batch 01 | Required evidence                                                               |
| ----------------------------- | ------------------------- | ------------------------------------------------------------------------------- |
| `B2.5-O-05` FRED semantics    | `B01-C02`                 | FRED-only sandbox evidence; macro supplementary is insufficient.                |
| `R3-PROMPT14-AKSHARE-VAL-01`  | `B01-C04` or later        | AkShare validation-only evidence or explicit re-defer with taxonomy.            |
| `R3-B2.75-REQ2-EM`            | Not closable by TDX alone | Eastmoney hist closure requires exact Eastmoney/approved alternate-path policy. |
| TDX disabled-candidate status | `B01-C03`                 | Raw-only authorized probe or re-defer; never production primary.                |
| Data health v2 readiness      | `B01-C05`                 | Read-only report; does not create production readiness.                         |

---

## 6. Execution guardrail

If a future executor finds a conflict between a legacy card and a new Batch 01 card:

1. Apply the stricter safety rule.
2. Preserve old path as historical record.
3. Record the conflict in task evidence.
4. Do not silently reinterpret legacy scope as production authorization.
5. Ask for user/coordinator approval if the conflict affects source enablement, clean write, or live network behavior.
