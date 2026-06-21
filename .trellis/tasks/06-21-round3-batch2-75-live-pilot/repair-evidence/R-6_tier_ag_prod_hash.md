# R-6 Tier A-G / Prod Hash Repair Evidence

Status: CLOSED

Tool limitations:

- `uv` is not on PATH; exact `uv run ...` commands were run as direct venv equivalents.
- GitNexus CLI impact attempt failed because the local runner tried npm registry access and network is blocked: `EACCES registry.npmjs.org`.
- Pytest default temp under `C:\Users\Guang\AppData\Local\Temp` is blocked; all passing pytest commands used `--basetemp` in `.audit-sandbox`.

MASTER §10 verification:

| Tier | Command run                                                                                                                                                                                                                                                                      | Result                                                                          |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| A    | `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.audit-sandbox\pytest-tier-a tests/test_batch275_live_pilot_gate.py tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py tests/test_round3_audit_registry_alignment.py -q` | `43 passed, 1 skipped`                                                          |
| B    | `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.audit-sandbox\pytest-tier-b tests/test_datasource_service.py tests/test_source_route_planner.py tests/test_ops_db_inspector.py -q`                                                                         | `38 passed, 1 skipped`                                                          |
| C    | `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.audit-sandbox\pytest-full-final -q`                                                                                                                                                                        | `656 passed, 2 skipped`                                                         |
| D    | `.\.venv\Scripts\python.exe -m ruff check .` / `.\.venv\Scripts\python.exe -m ruff format --check .`                                                                                                                                                                             | PASS / `142 files already formatted`                                            |
| E    | `.\.venv\Scripts\python.exe -m compileall -q backend scripts tests`                                                                                                                                                                                                              | PASS                                                                            |
| F    | `.\.venv\Scripts\python.exe scripts\production_gate.py` / `.\.venv\Scripts\python.exe scripts\check_doc_links.py`                                                                                                                                                                | `production_gate: PASS` / `OK: checked links in 176 markdown files under docs/` |
| G    | `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.audit-sandbox\pytest-tier-g -q --cov=backend --cov-fail-under=85`                                                                                                                                          | `656 passed, 2 skipped`; coverage `88.76%`                                      |

Prod-equivalent path:

- Created `.audit-sandbox/batch275-prod-equiv/` from `data/`.
- Ran Tier B with `$env:QMD_DATA_ROOT='.audit-sandbox\batch275-prod-equiv'`.
- Result: `38 passed, 1 skipped`.

Production DB hash proof:

- File: `data/duckdb/quant_monitor.duckdb`
- Session before hash: `5EB65E0EDAAAB223A77C5A5D2660603383836704B4C0ECE1EB4AEBB047F1682E`
- Session after hash: `5EB65E0EDAAAB223A77C5A5D2660603383836704B4C0ECE1EB4AEBB047F1682E`
- File timestamp remained `2026-06-20 14:46`.
- Conclusion: production DB was not mutated.
