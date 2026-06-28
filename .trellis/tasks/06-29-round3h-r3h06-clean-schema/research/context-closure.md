# R3H-06 Execute Context Closure

## Upstream / wiring closure

- **Upstream:** Batch 3V write_mode CLOSED; R3H-01–04 adapters CLOSED; Wave 1 blocks Wave 3 clean writes.
- **Wiring:** `clean_write_targets.py` routes bar/disclosure/macro; promote via `limited_production_entry`; rehearsal_runner aligned for cninfo/fred domains.
- **Parallel:** Single branch `feature/round3h-r3h06-clean-schema`; no R3H-07/08 migration overlap.

## Scope

- Task: `06-29-round3h-r3h06-clean-schema`
- Migrations 013/014; pilot path `security_bar_1d` / `cn_announcement_clean` / `axis_observation`
- SSOT: `frozen/R3H_06_CLEAN_SCHEMA.md` + `EXECUTION_INDEX.md`

## Out of scope

- Main DB `quant_monitor.duckdb` writes
- registry 三件套 edits
- R3H-05 audit / R3H-08 live fetch
