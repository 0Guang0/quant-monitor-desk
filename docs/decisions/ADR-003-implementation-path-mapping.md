# ADR-003: Implementation Path Mapping

## Status

Accepted (2026-06-19)

## Context

Early Round2 task documents reference `backend/sources/*` while the implemented layout is `backend/app/datasources/*`.

## Mapping

| Task / doc path | Actual code path |
|-----------------|------------------|
| `backend/sources/registry` | `backend/app/datasources/source_registry.py` |
| `backend/sources/adapters/*` | `backend/app/datasources/adapters/*` |
| `backend/sources/fetch_log` | `backend/app/datasources/fetch_log.py` |
| `backend/sync/orchestrator` | `backend/app/sync/orchestrator.py` |
| `backend/validators/*` | `backend/app/validators/*` |
| `backend/db/migrations` | `backend/app/db/migrations` |

## DB naming note

| Layer | Field |
|-------|-------|
| YAML | `allowed_domains` (list) |
| Python | `SourceRecord.allowed_domains` (`frozenset`) |
| DB | `allowed_domain` (JSON array string, singular column name) |
| DB alias | `allowed_domains_json` (mirror of `allowed_domain`, migration 008) |

## Consequences

New modules must follow `backend/app/<layer>/` layout. Task docs should cite this ADR instead of legacy `backend/sources` paths.
