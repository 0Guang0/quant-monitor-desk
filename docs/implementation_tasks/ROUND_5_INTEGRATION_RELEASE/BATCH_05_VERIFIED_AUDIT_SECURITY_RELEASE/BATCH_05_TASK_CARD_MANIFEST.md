# Batch 05 Task Card Manifest — Security / Scale / Release Hardening

> **Canonical batch folder:** `docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/`  
> **Roadmap:** `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 5+.  
> **Historical input cards:** loose `031`–`036` files remain source material, not the default execution entrypoint.

---

## 1. Canonical Batch 05 cards

| Card                                             | Round segment | Owns / source                        | Business outcome                                          | Loose-card inputs                                                                                                           |
| ------------------------------------------------ | ------------- | ------------------------------------ | --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `B05_01_security_ci_release_gate.md`             | Round 5.1     | `VR-SEC-001`                         | security scanning / release CI gate                       | `033_implement_security_and_boundary_tests.md`, `034_implement_docs_consistency_check.md`                                   |
| `B05_02_integration_and_resource_smoke.md`       | Round 5.2     | production scale budget continuation | integration smoke and resource-limit budget               | `031_implement_integration_smoke_tests.md`, `032_implement_resource_limit_tests.md`                                         |
| `B05_03_release_manifest_and_package_cleanup.md` | Round 5.3     | release runbook / final packaging    | release manifest, final package cleanup, docs consistency | `035_implement_final_package_cleanup.md`, `036_create_final_release_manifest.md`, `034_implement_docs_consistency_check.md` |

---

## 2. Historical loose task mapping

| Loose card                                     | Canonical Batch 05 owner                                                                  | Status           |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------- | ---------------- |
| `031_implement_integration_smoke_tests.md`     | `B05_02_integration_and_resource_smoke.md`                                                | historical input |
| `032_implement_resource_limit_tests.md`        | `B05_02_integration_and_resource_smoke.md`                                                | historical input |
| `033_implement_security_and_boundary_tests.md` | `B05_01_security_ci_release_gate.md`                                                      | historical input |
| `034_implement_docs_consistency_check.md`      | `B05_01_security_ci_release_gate.md` and `B05_03_release_manifest_and_package_cleanup.md` | historical input |
| `035_implement_final_package_cleanup.md`       | `B05_03_release_manifest_and_package_cleanup.md`                                          | historical input |
| `036_create_final_release_manifest.md`         | `B05_03_release_manifest_and_package_cleanup.md`                                          | historical input |

---

## 3. Canonical-card status

All Batch 05 canonical cards now exist. Do not treat the loose `031`–`036` cards as active implementation entrypoints; they are inputs for the three B05 cards above.

Do not delete the loose `031`–`036` cards until path references are audited and redirect/pointer notes are added.

---

## 4. Required execution order

1. `B05_01` security/release CI gate.
2. `B05_02` integration/resource smoke after Round3F-R, 3G, 3H, and Round4 artifacts stabilize enough to test.
3. `B05_03` release manifest/package cleanup last.

---

## 5. Anti-overengineering release rule

Batch 05 is not a product feature batch. It must not create new API/frontend/Agent/backtest/data-source capabilities to compensate for incomplete Round3H/Round3G/Round4 work. If a required capability is missing, Batch 05 must fail the release gate or list it explicitly in the release manifest with owner, phase, closure test, source limitation, and route/evidence status.

---

## 6. Batch 05 acceptance

Batch 05 is complete only when:

- security CI gates exist and are documented;
- integration smoke/resource-limit tests are bounded and runnable;
- release manifest includes production posture, source posture, unresolved/deferred item status, and Round3H source final decisions: `READY_WITH_EVIDENCE`, `ADR_DISABLED_OUT_OF_SCOPE`, or `DISABLED_SOURCE`;
- final package cleanup does not delete historical evidence without redirect;
- root roadmap and implementation README agree on canonical entrypoints;
- no Round5 card is being used as a backdoor product-feature implementation batch.
