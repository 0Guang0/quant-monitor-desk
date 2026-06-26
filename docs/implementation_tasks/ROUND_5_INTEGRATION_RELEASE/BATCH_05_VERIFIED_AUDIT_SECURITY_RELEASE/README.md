# Batch 05 — Verified Audit Security and Release Gates

> Roadmap: `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 5.  
> Scope: release/security findings from verified audit that should not be mixed into Round 3V or Round4 product work.  
> Canonical batch package: this folder. Loose `031`–`036` cards are historical inputs unless explicitly referenced by a Batch 05 card.

---

## Owned findings

| Card                                             | Owns                             | Round5 batch |
| ------------------------------------------------ | -------------------------------- | ------------ |
| `B05_01_security_ci_release_gate.md`             | `VR-SEC-001`                     | 5.1          |
| `B05_02_integration_and_resource_smoke.md`       | production/resource continuation | 5.2          |
| `B05_03_release_manifest_and_package_cleanup.md` | release manifest/package cleanup | 5.3          |

---

## Boundary

This batch may depend on artifacts from Round 3F performance budget, Round3G clean write, Round3H real-data source admission, and Round4 API/frontend work, but it should not implement those features. It turns security/release checks into CI gates.

Batch 05 must not become a cleanup bucket for unfinished product capabilities. If a Round3H/Round3G/Round4 capability is absent, Batch 05 should fail or document the limitation in the release manifest with owner, phase, and closure test; it should not add a new feature micro-slice.

Release output must preserve Round3H source posture exactly: `READY_WITH_EVIDENCE`, `ADR_DISABLED_OUT_OF_SCOPE`, `DISABLED_SOURCE`, source limitation, and route/evidence status. Batch05 must not convert missing source adapters into release-ready claims.
