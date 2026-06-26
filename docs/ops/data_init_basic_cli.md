# QMD Data Init-Basic CLI Design

> Status: operator design for `qmd data init-basic` (Round 2.6+). Not runtime migration authority.
>
> Contract: `specs/contracts/data_cli_contract.yaml` → `qmd data init-basic`.

## 1. Decision summary

`qmd data init-basic` prepares a local DuckDB file with schema migrations and optional `source_registry` sync. It is **not** a data fetch or clean-write command.

Default posture: **dry-run only** — no filesystem or DB mutation unless the operator explicitly opts out of dry-run.

## 2. Command shape

```bash
qmd data init-basic --dry-run
qmd data init-basic --no-dry-run --db-path data/duckdb/quant_monitor.duckdb
```

Transitional packaging:

```bash
python -m backend.app.cli.init_db --db <path> --sync-registry
```

## 3. Arguments and behavior

| Mode            | `dry_run` | Behavior                                                                                                                       |
| --------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Default         | `true`    | Returns planned steps only; message points to `qmd-init-db`                                                                    |
| Confirmed write | `false`   | Creates parent dirs; opens `ConnectionManager.writer()`; runs `apply_migrations`; syncs registry with `tombstone_missing=True` |

Writes allowed when confirmed (contract): `schema`, `registry` only. No fetch, no clean-write, no live source enablement.

## 4. Safety invariants

1. Default `dry_run=True` in `data_commands.init_basic`.
2. Write path uses `ConnectionManager.writer()` — never bypass WriteManager for production tables beyond migration/registry bootstrap.
3. Operators must treat `--no-dry-run` as explicit confirmation; document rollback via backup policy (`docs/ops/backup_and_recovery.md`).
4. Failures must surface `error_code` + `docs_anchor` when routed through CLI envelopes (see `docs/ops/ERROR_CODE_GUIDE.md`).

## 5. Relationship to other tools

| Tool                  | Question                                        |
| --------------------- | ----------------------------------------------- |
| `qmd data init-basic` | Create/migrate DB + sync registry?              |
| `qmd ops db-inspect`  | Read-only metadata/evidence presence?           |
| `qmd data health`     | Domain quality rules on evidence (read-only)?   |
| `qmd data sync`       | Fetch + staged ingestion (ResourceGuard gated)? |

## 6. Implementation location

- `backend/app/cli/data_commands.py::init_basic`
- Tests: `tests/test_qmd_data_cli.py::test_initBasic_noDryRun_syncsRegistry`, `tests/test_data_cli_contract.py`
