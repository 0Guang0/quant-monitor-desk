# Context closure — R3H-01

## Upstream wiring

- Batch 3G `rehearsal_loader` + `live_evidence_bridge` — G10 promote path now via `official_macro` normalizer (9.1)
- R3E `fred_fetch_ports` / `fred_sandbox_pilot` — L2 migrated to `datasources/fetch_ports/fred_port.py` (9.2)
- `implement.jsonl` + frozen §9 + `EXECUTION_INDEX.md` §1–§3 — Execute SSOT
- Six-source registry/capability/route — coordinator batch in 9.6 (`execute-evidence/9.6-manifest.md`)

## Deferred / out of scope

- `live_pilot_phase3.capture_phase3_raw_evidence` direct v1 write — locked: bridge→normalizer until future port consolidation
- Legacy `fred_evidence.json` `"date"` field bulk rewrite — breaks 3G data-health fixtures; read-time normalize only
- R3H-05 full five-layer production-entry audit — forbidden; 9.7 smoke only
- Main DB `quant_monitor.duckdb` writes — forbidden

## Slice boundary

- Mock-first fetch ports; live API gates where env/auth required
- `fred` remains `enabled_by_default: false`
- ADR not used for fred/us_treasury/sec_edgar; bis/world_bank implemented mock-first in 9.5
