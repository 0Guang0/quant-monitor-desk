# Staging Data E2E Runbook (R3F-CLI-05)

> **Scope:** user-authorized **staging** soak for vendor fetch gaps (`R3-AUDIT-DEF-02`).  
> **Default:** mock/fixture or dry-run only — **no default live fetch**.  
> **Not in scope:** production-live readiness, `source_health_snapshot` writes, QMT/Yahoo/xqshare auto-enable.

---

## 1. Preconditions

| Check                     | Command / artifact                                           |
| ------------------------- | ------------------------------------------------------------ |
| Editable install          | `uv sync --locked`                                           |
| DB + registry             | `uv run qmd-init-db --sync-registry`                         |
| Route preview (read-only) | `uv run qmd-data data route-preview --domain market_bar_1d`  |
| Sync dry-run              | `uv run qmd-data data sync --domain market_bar_1d --dry-run` |

## 2. Authorized live staging (opt-in only)

Live vendor fetch requires **explicit** operator authorization YAML (see `production_live_pilot_policy.md`).  
**B3F-CLI does not perform live fetch by default.**

When authorization is present:

1. Export required env (e.g. `FRED_API_KEY` for macro-only pilots — not general `qmd data`).
2. Run route-preview and confirm `route_status=READY`.
3. Use fixture-backed tests in CI: `uv run pytest tests/test_vendor_fetch_e2e.py -q`.
4. Capture evidence under `.audit-sandbox/staging-e2e/` — no production DB mutation.

## 3. CI one-liner (no live)

```powershell
uv sync --locked
uv run qmd-init-db --sync-registry
uv run pytest tests/test_qmd_data_cli.py tests/test_vendor_fetch_e2e.py -q
```

## 4. Failure handling

CLI failures must print `error_code`, `message`, `docs_anchor` per `docs/ops/ERROR_CODE_GUIDE.md`.

## 5. Negative guarantees

- No `source_health_snapshot` table creation in this runbook.
- No `--no-dry-run` sync without separate operator approval workflow.
- Staged evidence ≠ production-live.

## 6. R3G-03 limited production promote (operator CLI)

> **CLI:** `uv run qmd-data data sandbox-clean-write promote` (not `qmd`).  
> **Default:** `--dry-run` — no production mutation unless `--execute --no-dry-run`.

| Gate           | Requirement                                                                                                                                            |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Quadruple-lock | `--approval-file`, `--audit-decision`, `--before-proof`, `--rollback-plan` paths must match approval YAML `audit_decision_file` / `rollback_plan_path` |
| Production DB  | `production_db_path` under `DATA_ROOT` or `.audit-sandbox` only                                                                                        |
| Execute        | non-empty `backup_or_snapshot_pointer` in before_proof                                                                                                 |
| FRED live      | `--allow-live-fetch` + `--fred-authorization` only when approval sets `live_fetch_authorized: true`                                                    |

Dry-run verification:

```powershell
uv run pytest tests/test_round3g_limited_production_clean_write.py `
  tests/test_round3g_limited_production_rollback.py `
  tests/test_reference_adoption_guardrails.py -k r3g03 -q --basetemp=.audit-sandbox/pytest
```
