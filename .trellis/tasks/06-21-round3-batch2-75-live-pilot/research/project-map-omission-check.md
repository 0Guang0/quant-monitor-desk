# Project Map Omission Check — Batch 2.75

> MASTER 冻结前回查 `MIGRATION_MAP.md` — 2026-06-21

## Covered in MASTER §0.6

- Batch 2.75 policy + 018B task card index
- datasource service / route / capability modules
- db inspect CLI
- `backend/app/ops/` live pilot (new)
- `scripts/production_equivalent_smoke.py`
- Registries for closeout

## No omission requiring MASTER amendment

- Layer1 `ingestion.py` listed as **filtered** (staged only)
- Migration 008 / Batch 6 CLI correctly out of scope
- Frontend paths N/A

## Implementation directory confirmation

All runtime changes under `backend/app/ops/`, `backend/app/datasources/` (narrow), `tests/` — not `docs/`/`specs/`.
