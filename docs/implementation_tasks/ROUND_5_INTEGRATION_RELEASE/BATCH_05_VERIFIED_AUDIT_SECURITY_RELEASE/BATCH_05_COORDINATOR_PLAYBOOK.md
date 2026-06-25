# Batch 05 Coordinator Playbook

## 0. Scope

Coordinate Round5 security, integration, resource, release, and packaging gates from the canonical Batch 05 folder. Loose `031`–`036` files are historical inputs only.

Batch 05 must not implement product features that belong to Round 3G or Round4. It turns completed capabilities into release gates.

## 1. Dispatch tracks

| Track                            | Card                                             | Suggested branch                          | Can run in parallel?                 |
| -------------------------------- | ------------------------------------------------ | ----------------------------------------- | ------------------------------------ |
| Security CI release gate         | `B05_01_security_ci_release_gate.md`             | `chore/round5-security-ci-release-gate`   | first                                |
| Integration/resource smoke       | `B05_02_integration_and_resource_smoke.md`       | `chore/round5-integration-resource-smoke` | after enough runtime artifacts exist |
| Release manifest/package cleanup | `B05_03_release_manifest_and_package_cleanup.md` | `chore/round5-release-manifest-cleanup`   | last                                 |

## 2. Required cross-reading

Every Batch 05 branch must read:

- `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 5+
- `BATCH_05_TASK_CARD_MANIFEST.md`
- `BATCH_05_HARDENING_RULES.md`
- the relevant `B05_*` card
- mapped loose historical cards
- `docs/implementation_tasks/BATCH_FOLDER_REHOME_PLAN.md`

## 3. File locks

Avoid concurrent edits to:

- release manifest files
- docs consistency test specs
- package cleanup include/exclude lists
- CI workflow files
- `tests/test_catalog.yaml`

## 4. Release posture rule

Batch 05 must never claim readiness beyond proven gates.

If production-live, production clean write, limited source enablement, reference adoption status, or unresolved registry status is incomplete, the release manifest must say so explicitly.

## 5. Batch close criteria

Batch 05 closes only when:

- security gates are runnable and documented;
- integration/resource smoke tests are bounded;
- final manifest states source and write posture accurately;
- cleanup preserves formal task cards and evidence;
- roadmap and implementation README agree on canonical entrypoints;
- loose cards are either retained with pointer notices or fully rehomed with reference audit.
