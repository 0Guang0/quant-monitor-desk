# GitNexus Execute Summary — R3G-01

## Boot impact targets

| Symbol                                        | Risk   | Notes                                               |
| --------------------------------------------- | ------ | --------------------------------------------------- |
| `run_sandbox_clean_write_rehearsal`           | LOW    | New greenfield orchestrator; sandbox-only           |
| `validate_fred_authorization`                 | LOW    | Reuses `fred_sandbox_pilot.load_authorization_yaml` |
| `sandbox_clean_write_rehearse` (CLI)          | MEDIUM | Append to `data_commands.py` / `main.py`            |
| `staged_pilot._staged_conflict_check_summary` | LOW    | Read-only import; no `staged_pilot.py` edits        |

## detect_changes scope

- New: `backend/app/ops/sandbox_clean_write/**`
- Narrow: `backend/app/cli/data_commands.py`, `backend/app/cli/main.py`
- Tests: `test_round3g_sandbox_*`, `test_reference_adoption_guardrails.py` (r3g01)
- Catalog: `scripts/check_test_catalog.py` CURATED entries

## Forbidden blast radius

- `staged_pilot.py` behavior — **not modified**
- `layer1_axes/ingestion.py` write path — **not called**
- production clean write / R3G-03 gate — **not opened**
