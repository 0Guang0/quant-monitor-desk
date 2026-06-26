# Batch 3F-R — Mature Reference Adoption Refactor

> **Canonical status:** **CLOSED** (R3FR-01..07 complete).  
> **Placement:** completed between Batch 3F and Round 3G.  
> **Next batch:** `ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/README.md`.

---

## 0. Non-negotiable posture

Batch 3F-R is a refactor gate, not a production-live enablement gate.

Forbidden in this batch:

- production clean write
- default live source enablement
- full-market / full-history / minute-level default scans
- QMT / xqshare default enablement
- copying OpenBB AGPL runtime source into QMD
- copying EasyXT/JQ2PTrade trading APIs into QMD runtime
- silent fallback or auto source switching without `SourceRoutePlan`
- importing `参考项目/**` from `backend/app/**` runtime code

Required in this batch:

- preserve 3F green baseline
- keep `DataSourceService` and `SourceRoutePlanner` as the only production source route path
- keep `WriteManager`, `DbValidationGate`, and `ResourceGuard` as write/resource boundaries
- adapt reference code only through QMD contracts and tests
- add attribution/notes for copied or heavily adapted MIT/Apache code

---

## 1. Batch tasks

| Task ID   | Card                                              | Primary outcome                                                                                  | Existing wheel affected                                                                                                           | Reference source                                         |
| --------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `R3FR-01` | `R3FR_01_REFERENCE_RULES_AND_LICENSE_GATE.md`     | re-execute task-local reference governance; production-completion plan remains coverage map only | `reference_adoption_guardrails.yaml`, docs indices, `MODULE_COMPLETION_RATING.md`, `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` | all local `参考项目/**`                                  |
| `R3FR-02` | `R3FR_02_EASYXT_DATA_HEALTH_REFACTOR.md`          | EasyXT-style global data health profiles                                                         | `backend/app/ops/data_health.py::check_daily_bars`                                                                                | EasyXT `data_manager/data_integrity_checker.py`          |
| `R3FR-03` | `R3FR_03_TDX_PROVIDER_REFACTOR.md`                | pytdx provider refactor behind QMD authorization gates                                           | `TdxPytdxProbeFetchPort` and future TDX adapter internals                                                                         | EasyXT `easy_xt/realtime_data/providers/tdx_provider.py` |
| `R3FR-04` | `R3FR_04_JQ2PTRADE_BACKTEST_ADOPTION_PLAN.md`     | Round4 backtest avoids from-scratch engine                                                       | Round4 `029`, `B04_05` planning                                                                                                   | JQ2PTrade `ptrade_local/**`, `api_mapping.json`          |
| `R3FR-05` | `R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md`    | provider catalog and optional extras contract                                                    | ad hoc provider/plugin planning                                                                                                   | OpenBB provider structure, no source copy                |
| `R3FR-06` | `R3FR_06_QMD_DATA_HEALTH_CLI_RUNTIME.md`          | **Done** — `qmd data health` → `run_data_health_profile` read-only runtime                       | ~~CLI placeholder~~ (closed @ `ecf64f06`)                                                                                         | EasyXT report shape + QMD data health                    |
| `R3FR-07` | `R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md` | **Done** — legacy wrapper redirect docs + 3F-R batch close                                       | loose cards and thin wrapper docstrings                                                                                           | QMD tests + task-local reference adoption rules          |

---

## 2. Required execution order

1. `R3FR-01` first and re-execute it after the production-completion plan change. No code adoption before task-local reference rules and license gate are updated; do not create a central executable reference inventory, and do not treat `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` as a standalone execution card.
2. `R3FR-02` and `R3FR-06` next as one vertical slice: data health engine + CLI runtime.
3. `R3FR-03` after data health, because TDX output must feed the new profile checks.
4. `R3FR-04` and `R3FR-05` may run in parallel because they mostly update future Round4/provider planning.
5. `R3FR-07` last. Cleanup only after new tests pass.

---

## 3. Done criteria

Batch 3F-R is **closed** when (all satisfied):

- `PROJECT_IMPLEMENTATION_ROADMAP.md` names Round 3G as the next executable entrypoint.
- Reference adoption rules require executable details to live inside the relevant task card and distinguish direct adaptation vs architecture-only reference.
- `qmd data health` uses `run_data_health_profile` for supported read-only profiles (R3FR-06 @ `ecf64f06`).
- EasyXT-derived OHLCV/calendar/data-integrity checks are represented in QMD profile modules and tests.
- TDX provider internals are separated from probe orchestration and cannot default-enable live/raw fetch.
- Round4 backtest cards explicitly require JQ2PTrade/EasyXT adaptation rather than from-scratch engine design.
- OpenBB is recorded as architecture-only because the main repository is AGPLv3.
- Legacy thin wrappers have redirect notes or are wrapped by new profile/provider implementations.
- No backend runtime imports from `参考项目/**`.

---

## 4. Suggested verification commands

Use targeted commands first, then full test only at batch end:

```bash
uv run python -m pytest tests/test_reference_adoption_guardrails.py -q
uv run python -m pytest tests/test_ops_data_health.py tests/test_qmd_data_cli.py -q
uv run python -m pytest tests/test_tdx_manual_probe.py tests/test_tdx_live_manual_probe_authorization.py -q
uv run python -m pytest tests/test_dependency_extras_contract.py tests/test_source_capabilities.py -q
uv run pytest -q
```

If new tests are added, register them in `tests/test_catalog.yaml` with purpose and failure meaning.
