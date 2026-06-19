# Phase A Self-Check — migrated to Trellis research

> Migrated from root `ROUND2_6_PHASE_A_SELF_CHECK.md` for Task `06-19-round2-6-contract-gate` (AC-B10).
> Root file cleanup deferred to Task 2 (`06-19-round2-6-routing-service-gate`).

## adapter-domain residual gap documented

During Phase A review, `source_registry.yaml` uses concrete registry domains (`cn_equity_daily_bar`, `cn_filings`, …) while production adapters still declare legacy `supported_domains` (`market_bar_1d`, `fundamental`, `announcement`, …).

Phase A did not modify adapter code. Phase B (this task) adds:

- `tests/test_source_capabilities.py::test_adapterSupportedDomains_reconciledToCapabilityRegistryOrCompatibilityMap`
- Explicit `ADAPTER_DOMAIN_COMPATIBILITY_MAP` tested in contract gate

Task 2 must either align adapter domains to registry vocabulary or promote the compatibility map into `SourceCapabilityRegistry` enforcement.

## Cleanup decision

| Artifact | Decision |
|---|---|
| `ROUND2_6_PHASE_A_SELF_CHECK.md` (root) | Keep until Task 2 final cleanup gate (AC-D4) |
| Contract tests | Implemented in Phase B Execute |
| Production `DataSourceService` | Task 2 scope |

## Key Phase A boundaries (unchanged)

- No `backend/app/**` production implementation in Phase A
- No dependency file changes
- No schema migrations
- qmt_xtdata / qmt_xqshare remain disabled by default

## Residual gaps → Task hooks

| Gap | Task hook |
|---|---|
| DataSourceService | `06-19-round2-6-routing-service-gate` §8.4 |
| SourceRoutePlanner production | Task 2 §8.3 |
| Module boundary production refactor | Task 2 §8.6 |
| Production CLI `qmd data` | Task 2 / Round 3 ops |
| Prod-equivalent benchmark | Task 2 §8.9 (`016F`, `production_equivalent_smoke.py`) |
| Live QMT/Yahoo/xqshare | User-authorized staging only |
