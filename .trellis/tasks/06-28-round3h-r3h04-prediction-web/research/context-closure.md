# Context closure — R3H-04

## Upstream wiring

- R3H-02 `coingecko_port.py` + `crypto_market.py` + `evidence_bundle.finalize_bundle` — mock port / normalizer pattern for 9.1–9.4
- R3H-01 `test_official_macro_adapters.py` — layer5 smoke + route enable helper pattern for 9.7
- `implement.jsonl` + frozen §9 + `EXECUTION_INDEX.md` §1–§3 — Execute SSOT
- Three-source registry/capability/route — coordinator slice in 9.5 (`execute-evidence/9.5-manifest.md`)

## Deferred / out of scope

- R3H-05 full layer production-entry audit — forbidden; 9.7 smoke only
- Main DB `quant_monitor.duckdb` writes — forbidden
- R3H-03 CN market sources/registry rows — forbidden (parallel branch owns)
- `resource_guard.py` modification — forbidden
- OpenBB / `参考项目/**` runtime import — forbidden
- kalshi/polymarket live API — user gate + API key; default mock/replay

## Slice boundary

- mock/replay-first READY for kalshi, polymarket, web_search
- probability_signal_evidence_v1 + web_evidence_staging_v1 schemas
- web_search always manual_review staging; prediction markets never factual resolution

## GitNexus blast radius (boot)

| Symbol / module | Risk | Notes |
| --- | --- | --- |
| `DataSourceService.fetch` | MEDIUM | not modified; new ports standalone |
| `route_planner` / `capability_registry` | MEDIUM | 9.5 three-source registry slice only |
| `EvidenceFoundationValidator` | LOW | 9.7 smoke read-only validation |
| `source_registry.yaml` (3 rows) | MEDIUM | notes + coordinator manifest |
| `evidence_bundle.finalize_bundle` | LOW | reused, not edited |
