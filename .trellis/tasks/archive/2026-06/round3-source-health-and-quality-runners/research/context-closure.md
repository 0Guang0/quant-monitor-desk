# Context closure — B3F-SH source health & quality runners

## Upstream wiring

- DH2 `data_health.py` — read-only profiles unchanged; `DH2_FORBIDS_SNAPSHOT_DDL` guard added
- `fred_sandbox_pilot.py` — reused `load_authorization_yaml` for SH-06 gate
- `tdx_manual_probe.OPEN_REGISTRY_ROWS` pattern — SH-07 `b3f_sh_registry_guard.py`
- `sync_job_contract.yaml` — `data_quality` / `revision_audit` moved to implemented

## Deferred (unchanged)

- `backend/app/db/migrations/**` for `source_health_snapshot` (B3F-MIG)
- registry 三件套 direct RESOLVED commit
- production clean write / default live fetch

## Slice boundary

- writer + isolated pytest; orchestrator quality runners; rollup persist API
- forbidden: DH2 path CREATE snapshot; AkShare/EM false-close; unauthorized FRED live
