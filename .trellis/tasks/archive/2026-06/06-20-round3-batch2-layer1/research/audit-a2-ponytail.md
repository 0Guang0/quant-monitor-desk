# A2 Ponytail Audit — §3.2

> **Task:** `06-20-round3-batch2-layer1`  
> **Agent:** audit-ponytail (A2)  
> **Scope:** `backend/app/layer1_axes/` (~1,104 LOC across 7 files)  
> **Skills:** ponytail-review + doubt-driven-development (skill file absent in workspace; applied §5 ladder inline)

---

## Verdict: **PASS**

Layer 1 axis code is **appropriately scoped** for AC-017/018/LINEAGE: frozen dataclasses mirror contract DDL, module split matches the vertical slice (loader → feature → interpretation → lineage), and there are **no factory layers, plugin registries, or speculative generalization** beyond what tests and contracts require. Remaining issues are **optional shrink** (dead constants, one-line wrappers, duplicated row construction)—consistent with Round 1 A2 precedent: optional ponytail trim, **not** blocking §4.3.

---

## DOUBT answer

| Claim                                     | Attack                                            | Reconcile                                                                                                                                    |
| ----------------------------------------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| “Five-axis loader is minimal”             | 352-line `axis_loader.py` with many helpers       | Helpers (`_classify_indicator`, `_coerce_rules`, `_build_indicator_records`) map 1:1 to AC-017 contract checks; no alternate loader backends |
| “models.py is over-modeled”               | 11 dataclasses / 176 LOC                          | Field sets align with migration 011 + module §5–7.1; no behavior classes or inheritance trees                                                |
| “guardrails.py should inline into loader” | Extra module for 56 LOC                           | SHADOW/forbidden-substitute rules are isolated and directly tested; split is justified                                                       |
| “Interpretation engine is a framework”    | `templates` dict + forbidden-term scan            | `templates` used by AC-018-3 test; default path is a single f-string—no template registry                                                    |
| “Lineage builder is premature”            | `SnapshotLineageBuilder` + `Layer1SnapshotWriter` | Required for AC-LINEAGE-\* and AC-WRIT-1; `parameter_hash_for` is a pure function, not a strategy pattern                                    |

---

## Findings (ID | Sev | Finding | §4.3?)

| ID    | Sev        | Finding                                                                                                                                                                                                                                                                                            | §4.3? |
| ----- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| A2-01 | Suggestion | `lineage.py:20-38` — `LINEAGE_REQUIRED_FIELDS` tuple is **never referenced** (dead contract mirror; tests inline their own field lists).                                                                                                                                                           | No    |
| A2-02 | Suggestion | `axis_loader.py:350-351` — `build_guardrail_validator()` is a **one-line** `AxisEngineeringGuardrailValidator(...)` wrapper. Tests could call the constructor directly.                                                                                                                            | No    |
| A2-03 | Suggestion | `axis_loader.py:145-146` — `load_from_config()` is a **one-line** alias for `load()` with no production callers (only docs/gitnexus summary).                                                                                                                                                      | No    |
| A2-04 | Important  | `feature_engine.py:93-120` vs `152-179` — **~25 identical `FeatureSnapshotRow` kwargs** duplicated between `insufficient_history` early-return and success path (~28 net duplicate LOC). Largest ponytail in the package.                                                                          | No    |
| A2-05 | Suggestion | `axis_loader.py:325-337` — profile `physical_meaning_static` and `financial_meaning_static` both copy `plain_summary`; `penetration_power_static=""`, `display_template=""` are schema placeholders. Acceptable for Batch 2 fixture loader but inflates profile rows without spec-sourced content. | No    |
| A2-06 | Suggestion | `axis_loader.py:115-121` — `AxisEngineeringGuardrail` sets `forbidden_labels` and `forbidden_substitutes` to the **same** `axis_forbidden` tuple; validator merges both sets anyway (`guardrails.py:25-28`).                                                                                       | No    |
| A2-07 | Suggestion | `interpretation.py:91-96` — `guard_layer2_writeback` is a **write-path** guard on `AxisInterpretationEngine`; conceptually belongs with lineage/write integration, not interpretation text generation.                                                                                             | No    |

**Adversarial checks (MASTER §7 Red Flags vs ponytail):**

| Red-flag class                                                | Ponytail read                                                                                                                                                                 |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Premature Layer2/API framework                                | **Not present** — `guard_layer2_writeback` is a static one-liner, not a layer framework                                                                                       |
| Unbounded rolling / ResourceGuard wrapper                     | **Justified** — `WINDOW_POLICY` + injected `ResourceGuard`; no scan abstraction layer                                                                                         |
| Duplicated logic across loader/feature/interpretation/lineage | **Partial** — classification logic stays in loader; feature stats stay in engine; **only** A2-04 (row duplication) and A2-06 (twin forbidden tuples) are internal duplication |
| Unnecessary classes                                           | **Borderline only** — `AxisSpecLoader` could be module functions, but matches project service-class style; not §4.3                                                           |

---

## Concrete refactor suggestions (do not apply in Audit)

1. **A2-01:** Delete `LINEAGE_REQUIRED_FIELDS` or use it in `SnapshotLineageBuilder.build` / a single `assert_lineage_complete(envelope)` helper consumed by tests (one source of truth).
2. **A2-02 / A2-03:** Remove `build_guardrail_validator` and `load_from_config`; update tests/docs to call `AxisEngineeringGuardrailValidator(result.guardrails)` and `loader.load()` directly (−4 LOC).
3. **A2-04:** Extract `_feature_row_base(as_of, obs, *, flags, state_bucket, z_score=None, …)` or a small `_snapshot_row(...)` builder inside `feature_engine.py` so insufficient-history and success paths share one field block (−~25 LOC).
4. **A2-05:** Defer until user-guide MD parsing lands; document in loader that static profile fields are intentionally stubbed from indicator YAML only.
5. **A2-06:** Store one `forbidden_terms` on `AxisEngineeringGuardrail` or drop `forbidden_labels` if substitutes are the only runtime check.
6. **A2-07:** Move `guard_layer2_writeback` + `LAYER1_TABLES` to `lineage.py` (next to `Layer1SnapshotWriter`) or a 10-line `write_guards.py` if interpretation must stay text-only.

**Estimated net shrink if A2-01–04 applied:** ~35–45 LOC (~3–4% of package).

---

## What's done well

- **Module boundaries** match Execute vertical slice: spec load → compute → interpret → persist; no circular imports.
- **`models.py`** uses frozen dataclasses only—no ORM, no mutable domain services.
- **`AxisFeatureEngine`** uses stdlib `statistics` + explicit `WINDOW_POLICY`; no pandas/sklearn/plugin pipeline.
- **`AxisInterpretationEngine`** default path is one template string + forbidden-term scan; `reject_if_forbidden` is a separate explicit API for AC-018-3.
- **`Layer1SnapshotWriter`** reuses WriteManager staging pattern without a new write framework.
- **No speculative config/framework layers** beyond `configs/layer1_axes.yml` pointer (required by AC-017-1).

---

## §4.3 repair queue (A2 contribution)

| ID  | Priority | Action   | Blocks finish-work? |
| --- | -------- | -------- | ------------------- |
| —   | —        | **None** | No                  |

All A2 findings are optional shrink (P3) or AC-driven placeholders (A2-05). Per Round 1 foundation A2 precedent, optional ponytail trim does not enter §4.3 unless promoted by A9.

**§4.3 count (A2): 0**

---

## Verification story

| Check            | Result                                                                                                                                                                                                                  |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tests reviewed   | **Yes** — loader/guardrail tests (`test_layer1_axis_loader.py`) and feature/interpretation/lineage tests (`test_layer1_interpretation.py`) confirm intended minimal APIs; no tests require factory/registry indirection |
| Build verified   | **No** (A2 review-only)                                                                                                                                                                                                 |
| Security checked | **N/A** (A3 dimension)                                                                                                                                                                                                  |
| LOC vs value     | **~1,104 LOC** for 5-axis loader + §7.1 feature fields + interpretation + lineage + WriteManager hook — proportional to MASTER §8.2–8.5 scope                                                                           |
