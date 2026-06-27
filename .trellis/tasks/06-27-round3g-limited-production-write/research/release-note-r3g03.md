## R3G-03 — Limited Production Clean Write (2026-06-27)

**Scope:** First capped production clean-write entry via `qmd data sandbox-clean-write promote`.

| Field    | Value                       |
| -------- | --------------------------- |
| source   | `baostock`                  |
| domain   | `cn_equity_daily_bar`       |
| symbols  | `sh.600000` (fixture pilot) |
| window   | `2026-05-01` → `2026-05-30` |
| max_rows | 100                         |

**Limitations:**

- Default `dry_run`; production mutation requires explicit `--execute --no-dry-run` plus §6 approval YAML and aligned `audit_decision.json`.
- Promote reads `audit_decision.json` only (`PASS_ALLOW_LIMITED_PROD_WRITE` or `WARN_ALLOW_WITH_MANUAL_APPROVAL`).
- Target DB = `production_db_path` from approval (not sandbox DB).
- Rollback plan is identify-only dry-run; no automatic production DELETE.
- No agent-triggered writes; `no_agent_triggered_write` and `no_cap_expansion` must be true.
- Tier B prod-path not run in CI — coordinator §6 approval required.
