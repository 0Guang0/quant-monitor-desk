# Merge Gate Report — debt/round3-ponytail-low-touch (PROMPT_17)

## Scope

| Field | Value |
| ----- | ----- |
| Branch | `debt/round3-ponytail-low-touch` |
| Base | `master` @ b200e03c |
| Worktree | `quant-monitor-desk-wt-debt-r3-ponytail-low-touch` |
| Authority | `PONYTAIL_MODULE_SCAN_20260622.md` §4.7–4.8, `R3X_ponytail_low_touch_bucket_c.md` |

## Items closed

| ID | Action |
| -- | ------ |
| VA-01 | Removed `data_quality.py` thin wrappers; direct `common` helpers |
| VA-02 | Removed `source_conflict.py` thin wrappers; inlined `as_text(x) or ""` |
| VA-07 | Documented YAML/Python `rule_id` dual track in `rule_contract.py` |
| VA-08 | Removed dead `quote_ident` side effect in `_table_exists` |
| SC-03 | `resource_guard.evaluate()` → `_ThresholdSignal` data-driven loop |
| SC-04 | Added `get_resource_profile` valid/invalid tests in `test_config.py` |
| SC-05 | Kept `error_redaction.py` (live imports in db/sync/datasources); doc only |
| SC-06 | `api_limits` uses `config.CONFIGS_ROOT` single source |

## Changed files (in-scope)

- `backend/app/validators/data_quality.py`
- `backend/app/validators/source_conflict.py`
- `backend/app/validators/rule_contract.py`
- `backend/app/core/resource_guard.py`
- `backend/app/core/api_limits.py`
- `backend/app/util/error_redaction.py`
- `tests/test_config.py`
- `.trellis/tasks/debt-round3-ponytail-low-touch/execute-evidence/**`

## Out of scope (untouched)

- `backend/app/ops/**`, `datasources/**`, `storage/**`, `db/**`, `sync/**`, layer1/2
- Production DB writes, live network, vendor calls
- Registry files

## Tests

| Command | Result |
| ------- | ------ |
| `pytest tests/test_data_quality_validator.py tests/test_source_conflict_validator.py tests/test_resource_guard.py tests/test_config.py -q` | PASS |
| `pytest tests/test_api_security_contract.py -q` | PASS (SC-06) |
| `pytest -q` (full) | PASS |

Evidence: `execute-evidence/targeted-pytest-green.txt`, `full-pytest-green.txt`, per-item `*-red.txt` / `*-green.txt`.

## Data safety

No production DB mutation. Refactors are import/signature-neutral for runtime callers.

## Registry

Untouched.

## GitNexus impact

- `evaluate` (resource_guard): LOW risk, 4 upstream
- `DataQualityValidator`: LOW risk, 8 upstream imports (no API change)

## Deferred / blockers

- **Commit:** implement agent does not commit; parent session must create single commit excluding unrelated worktree dirt (`.trellis/tasks/06-21-round3-batch2-75-live-pilot/*` pre-existing mods).
- **SC-05:** scan “no references” was stale; deletion would break forbidden modules — closed via documentation.

## Semantics

No staged/live pilot behavior change; ponytail maintainability only.
