# Known Pytest Skips

> Operator reference for CI triage. Full audit context: `docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md` §4.

| Test                                                                               | Skip condition                            | Platform                   | Mitigation                                              |
| ---------------------------------------------------------------------------------- | ----------------------------------------- | -------------------------- | ------------------------------------------------------- |
| `tests/test_ops_db_inspector.py::test_dbInspect_symlinkOutsideDataRoot_notCounted` | `symlinks not supported on this platform` | Windows (typical)          | Run on Linux CI; symlink path containment covered there |
| `tests/test_raw_store.py::test_save_windowsLongPath_writesSuccessfully`            | `Windows long-path regression only`       | non-Windows                | Windows agent / dev machine covers MAX_PATH             |
| `tests/test_path_compat.py::*`                                                     | `Windows-only`                            | non-Windows                | Same as above                                           |
| `tests/test_batch25_production_data_gate.py` (conditional)                         | missing local production DB or `data/raw` | dev without prod artifacts | Expected; gate tests local readiness only               |

**Full suite expectation:** `pytest -q` → 1 skip on Windows is normal (symlink test).

## Quick CI profile

```bash
# Full suite (default local / nightly)
pytest -q

# Quick profile — exclude tests marked @pytest.mark.slow
pytest -q -m "not slow"
```

Slow-marked tests today: phase3/phase4 evidence artifact tests in `tests/test_layer1_observation_ingestion.py` (see `test_layer1Ingestion_phase3_taskEvidenceArtifacts`, `test_layer1Ingestion_phase4_taskEvidenceArtifacts`).

Marker registered in `pyproject.toml` `[tool.pytest.ini_options].markers`.
