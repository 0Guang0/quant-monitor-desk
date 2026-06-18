# Directory Structure

> How backend code is organized in this project (Round 0–2).

## Overview

Backend lives under `backend/app/` with layer packages reserved for Round 3+ modeling.
Scripts and tests are siblings at repo root.

## Directory Layout

```
backend/app/
├── core/           # ResourceGuard, api_limits
├── config.py       # PROJECT_ROOT, DATA_ROOT, profile helpers
├── datasources/    # SourceRegistry, adapters, fetch contracts
├── db/             # ConnectionManager, migrations, WriteManager, ValidationGate
├── storage/        # RawStore, FileRegistry, evidence ports
├── sync/           # DataSyncOrchestrator, jobs, pipeline ports
├── validators/     # DataQuality, SourceConflict, common helpers
├── layer1_axes/    # Round 3 placeholder
├── layer2_cross_asset/
├── layer3_shock_anchors/
├── layer4_markets/
└── layer5_evidence/
scripts/            # smoke, registry sync, production gate
tests/              # pytest suite + fixtures
frontend/src/       # React scaffold (Round 4 UI)
specs/              # contracts, schema authority
configs/            # runtime YAML (resource_limits)
```

## Module Organization

- **datasources** must not write clean tables; only fetch_log + raw evidence.
- **validators** are pure rule engines; persistence via explicit `validate_table`.
- **sync.orchestrator** coordinates state machine + pipeline ports; no direct SQL to clean.
- **db.write_manager** is the sole clean write entry.

## Adding New Modules

1. Place code in the matching package above; add empty `__init__.py` if new package.
2. Add migration under `backend/app/db/migrations/` with sequential prefix.
3. Add contract test or extend existing validator/orchestrator tests.
4. Update this file if a new top-level package is introduced.
