# Batch 3F-R Task Card Manifest

> **Batch:** Round 3F-R Reference Adoption Refactor  
> **Runtime posture:** read-only/refactor-only by default; no production clean write; no default live source.  
> **Structure rule:** one Task ID = one executable task card. Reference adoption details live inside the relevant task card, not in a central execution inventory.

---

## 1. Task summary

| Task ID   | Active card                                       | Module movement                                                                                                           | Primary files                                                                                                                             | Completion rule                                                       |
| --------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `R3FR-01` | `R3FR_01_REFERENCE_RULES_AND_LICENSE_GATE.md`     | Reference-adoption governance is re-executed after production-completion planning; task-local execution remains mandatory | `reference_adoption_guardrails.yaml`, roadmap/task indices, `MODULE_COMPLETION_RATING.md`, `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` | No central executable inventory; production plan is coverage map only |
| `R3FR-02` | `R3FR_02_EASYXT_DATA_HEALTH_REFACTOR.md`          | Data health moves from minimal checks to complete supported-profile engine                                                | `backend/app/ops/data_health_profiles/**`, `data_health.py`, `data_quality_rules.yaml`                                                    | Complete `market_bar_p0`, not one-rule increments                     |
| `R3FR-03` | `R3FR_03_TDX_PROVIDER_REFACTOR.md`                | TDX moves from ad hoc probe to QMD-owned disabled/raw-only provider port                                                  | `tdx_pytdx_port.py`, TDX normalizer/probe tests, source registries                                                                        | Complete disabled/raw-only provider shape                             |
| `R3FR-04` | `R3FR_04_JQ2PTRADE_BACKTEST_ADOPTION_PLAN.md`     | Round4 backtest planning moves from blank-engine risk to reference-adapted vertical-slice plan                            | Round4 `B04_05`, backtest/review contracts                                                                                                | Round4 must fit ≤3 implementation batches to full stable scope        |
| `R3FR-05` | `R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md`    | Provider metadata moves from ad hoc notes to QMD provider catalog for every active/proposed source                        | `provider_catalog.yaml`, provider catalog tests, source contracts, schema CHECK enum alignment                                            | Catalog fields and all registry entries in one batch                  |
| `R3FR-06` | `R3FR_06_QMD_DATA_HEALTH_CLI_RUNTIME.md`          | `qmd data health` moves from placeholder to real profile runtime                                                          | CLI command files, data CLI contract/tests                                                                                                | Same batch as R3FR-02; no message-only wrapper                        |
| `R3FR-07` | `R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md` | Thin wrappers/obsolete cards are redirected only after replacements pass                                                  | wrapper docs/tests, task indices, roadmap                                                                                                 | Cleanup cannot create more micro-slices                               |

Redirected historical card:

```text
R3FR_01_REFERENCE_INVENTORY_AND_LICENSE_MATRIX.md
```

Do not implement the redirected card directly.

---

## 2. Cross-task constraints

- `R3FR-01` must merge before code adaptation.
- `R3FR-02` and `R3FR-06` are one vertical slice: profile engine + CLI runtime.
- `R3FR-03` must preserve disabled-by-default and raw-only TDX posture.
- `R3FR-04` is planning-only in 3F-R but must rewrite Round4 cards enough that the first Round4 implementation batch is executable.
- `R3FR-05` must not import or copy OpenBB runtime source.
- `R3FR-07` runs last and cannot close until replacements are stronger than old thin wrappers.

---

## 3. Batch-level acceptance

Batch 3F-R is not complete unless:

1. `MODULE_COMPLETION_RATING.md` exists and is referenced only by planning/task files.
2. Design/contract/architecture files describe complete product shape and are not downgraded with current-completion labels.
3. No executable reference details are moved into a central inventory file.
4. `market_bar_p0` data health profile is complete enough for Round 3G admission.
5. `qmd data health` has a real read-only path for supported profiles.
6. TDX has a QMD-owned disabled/raw-only provider-port boundary.
7. Provider catalog covers every source in `source_registry.yaml`, preserves proposed-disabled posture, and distinguishes production candidate vs production enabled.
8. Round4 backtest/review planning requires JQ2PTrade/EasyXT-informed QMD-owned implementation.
9. No backend runtime imports from `参考项目/**`.
10. No module is planned to need more than three implementation batches to reach full stable production shape for its declared scope.
