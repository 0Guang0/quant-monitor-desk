# Context closure — B3F-HYG hygiene / perf

## Upstream wiring

- `scripts/production_equivalent_smoke.py` — bounded service-path smoke
- `specs/contracts/production_equivalent_smoke_budget.yaml` — threshold SSOT
- `backend/app/layer1_axes/sandbox_bootstrap.py` — PR-R2b shared DB/data_root bootstrap
- `backend/app/layer1_axes/ingestion_evidence.py` — phase evidence (imports sandbox_bootstrap)
- `docs/architecture/layer1_ingestion_refactor_rollback_plan.md` — R2a/R2b status

## Out of branch (unchanged wiring)

- migration columns — **B3F-MIG** read-only
- live source / production clean write — hardening forbidden
- registry 三件套 — `research/registry_proposed_delta.yaml` only

## VR / roadmap closure (branch)

- **R3F-HYG-06:** smoke budget artifact + threshold tests GREEN
- **R3F-HYG-07:** R2b `sandbox_bootstrap` + rollback plan R2b DONE
- **R3F-HYG-08:** ResourceGuard tests verify-only PASS
