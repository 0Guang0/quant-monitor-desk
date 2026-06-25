# Context closure — B3F-CLI

## Upstream wiring

- `DataSourceService.preview_route` + `SourceRoutePlanner` — route-preview read-only path
- `scripts/init_db.py` + `SourceRegistry.sync_to_db` — `--sync-registry` one-liner
- `specs/contracts/data_cli_contract.yaml` — dry-run / error_code contract
- `tests/test_vendor_fetch_e2e.py` — staging E2E fixture path (runbook reference, no default live)

## Delivered

- `backend/app/cli/*` — `qmd data` route-preview / sync dry-run / error envelope
- `init_db --sync-registry` — R2-GAP-1 CI one-liner
- `pyproject.toml` console_scripts — R3F-CLI-02/04
- `docs/ops/staging_data_e2e_runbook.md` — R3F-CLI-05 no-default-live

## Out of scope

- `source_health_snapshot` table (B3F-SH)
- production live fetch default
- registry RESOLVED 闭合（主会话批处理）
