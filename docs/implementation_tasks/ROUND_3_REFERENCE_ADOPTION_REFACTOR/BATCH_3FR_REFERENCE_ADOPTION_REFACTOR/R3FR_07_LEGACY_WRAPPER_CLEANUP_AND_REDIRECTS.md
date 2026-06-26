# R3FR-07 — Legacy Wrapper Cleanup and Redirects

> **Batch:** Batch 3F-R — Mature Reference Adoption Refactor  
> **Module movement:** Remove or redirect thin wrappers only after replacement implementations are stronger and tested.  
> **Execution posture:** cleanup/hardening only; no new feature scope; no evidence deletion.

---

## 1. Purpose

Close Batch 3F-R by removing stale task paths, wrappers, and placeholder narratives that would let future work continue tiny self-built slices. Cleanup happens only after R3FR-02/R3FR-03/R3FR-05/R3FR-06 replacement tests pass.

```yaml
reference_project:
  path: n/a
  license: n/a
  allowed_use: forbidden_until_review
  qmd_target_files: []
  direct_copy_allowed: false
  rewrite_required: []
  forbidden_semantics:
    - new_runtime_adoption_during_cleanup
  attribution_required: false
```

---

## 2. Cleanup targets

Review and update:

```text
backend/app/ops/data_health.py::check_daily_bars
backend/app/cli/data_commands.py::health_check
backend/app/ops/interface_probe_fetch_ports.py
backend/app/ops/tdx_manual_probe.py
docs/implementation_tasks/README.md
docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/*.md
docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/*.md
PROJECT_IMPLEMENTATION_ROADMAP.md
MODULE_COMPLETION_RATING.md
```

---

## 3. Required cleanup behavior

- Old wrappers may remain only as compatibility redirects to the new QMD-owned profile/provider implementation.
- Historical task cards may remain only with redirect notes if their old instruction is obsolete.
- No `reference_adoption_inventory.md` may become an execution dependency.
- No production claims may be introduced by cleanup.
- No historical evidence file may be deleted without redirect/index update.
- No design/contract/architecture file should be polluted with current completion ratings; completion rating belongs in root `MODULE_COMPLETION_RATING.md` and planning/task cards.

---

## 4. Overengineering stop gate

Before closing this task, verify that follow-up work is not split into repeated micro-slices. For each affected module, remaining work must be one of:

```text
complete next batch
full-stable closure batch
hardening/regression batch
```

If a proposed follow-up only adds one flag, one metric, one registry note, or one narrow guard without moving the module to the next rating level, it must be merged into the active batch or rejected.

---

## 5. Tests / gates

Required verification:

```bash
uv run pytest tests/test_reference_adoption_guardrails.py -q
uv run pytest tests/test_qmd_data_cli.py tests/test_ops_data_health.py -q
uv run pytest tests/test_tdx_manual_probe.py tests/test_tdx_live_manual_probe_authorization.py -q
uv run pytest tests/test_documentation_index.py tests/test_docs_specs_indexed.py -q
```

---

## 6. Done criteria

R3FR-07 is done when:

- obsolete 3F-R reference-inventory task path is redirected;
- data health and CLI placeholders are replaced or clearly redirected to real implementations;
- TDX probe wrappers point to the new provider-port boundary;
- Round 3G entry criteria reference the completed 3F-R outputs;
- future planning uses the three-batch full-stable rule from `MODULE_COMPLETION_RATING.md`.
