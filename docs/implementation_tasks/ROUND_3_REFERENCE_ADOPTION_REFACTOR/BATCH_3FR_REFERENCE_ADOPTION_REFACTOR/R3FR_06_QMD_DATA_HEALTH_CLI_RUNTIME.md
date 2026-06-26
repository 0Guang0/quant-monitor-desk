# R3FR-06 — `qmd data health` Runtime

> **Status:** **Done** (merged @ `ecf64f06`); historical narrative below preserved for traceability.  
> **Canonical runtime:** `run_data_health_profile` in `backend.app.ops.data_health_profiles`.  
> **Do not re-implement:** this card is completed; redirect/cleanup notes live in R3FR-07.

> **Batch:** Batch 3F-R — Mature Reference Adoption Refactor  
> **Module movement:** Data CLI health must move from placeholder to real read-only profile runtime for supported profiles.  
> **Execution posture:** read-only; no live fetch; no clean write.

---

## 1. Purpose

Replace `not_implemented_phase_c` in `qmd data health` with a real read-only execution path backed by R3FR-02 profiles. This task closes the CLI/runtime part in the same batch as the engine refactor; it must not become another placeholder layer.

```yaml
reference_project:
  path: 参考项目/EasyXT/data_manager/data_integrity_checker.py
  license: MIT
  allowed_use: direct_adaptation
  qmd_target_files:
    - backend/app/cli/data_commands.py
  direct_copy_allowed: false
  rewrite_required:
    - remove_runtime_import_from_reference_project
  forbidden_semantics:
    - production_clean_write
    - live_fetch_default
  attribution_required: true
```

---

## 2. Dependency

R3FR-06 depends on R3FR-02 profile runner. The two should be implemented as one vertical slice if possible:

```text
EasyXT-informed QMD profile runner → qmd data health CLI → JSON/table report → tests
```

---

## 3. Target files

Update/create:

```text
backend/app/cli/data_commands.py
backend/app/cli/main.py
backend/app/ops/data_health_cli.py
backend/app/ops/data_health.py
backend/app/ops/data_health_profiles/**
docs/ops/data_health_cli.md
specs/contracts/data_cli_contract.yaml
specs/contracts/data_quality_rules.yaml
tests/test_qmd_data_cli.py
tests/test_data_cli_contract.py
tests/test_data_health_easyxt_profiles.py
```

---

## 4. Required CLI shape

Support at least:

```bash
qmd data health \
  --domain market_bar_1d \
  --profile market_bar_p0 \
  --evidence-dir <path> \
  --format json
```

Optional:

```bash
qmd data health --db-path <sandbox-or-readonly-db> --domain market_bar_1d --profile market_bar_p0
```

The command must fail closed if caller requests live fetch, clean write, full-market scan, or missing profile.

---

## 5. Required output fields

JSON output must include:

```yaml
command: health
dry_run: true
side_effects_allowed: false
domain: market_bar_1d
profile: market_bar_p0
status: PASS | WARN | FAIL
rules_run: []
issue_counts_by_severity: {}
row_count_checked: 0
window: { start: "", end: "" }
source_ids: []
content_hash_coverage: {}
schema_hash_coverage: {}
report_path: optional
limitations: []
```

---

## 6. Forbidden scope

- No `not_implemented_phase_c` for supported profiles.
- No live fetch.
- No production DB write.
- No full-market/full-history default scan.
- No runtime import from `参考项目/**`.
- No ad hoc CLI-only health rules separate from R3FR-02 profile runner.

---

## 7. Tests / gates

Required verification:

```bash
uv run pytest tests/test_qmd_data_cli.py tests/test_data_cli_contract.py -q
uv run pytest tests/test_data_health_easyxt_profiles.py tests/test_ops_data_health.py -q
```

Tests must prove:

- supported profile does not return `not_implemented_phase_c`;
- invalid profile returns documented error;
- CLI invokes profile runner;
- no side effects occur;
- JSON output has required fields;
- live/clean-write/full-scan requests are rejected.

---

## 8. Done criteria

R3FR-06 is done when `qmd data health` is a real bounded read-only command for `market_bar_p0` and shares the same implementation as R3FR-02. A CLI wrapper that only changes the message text is not acceptable.
