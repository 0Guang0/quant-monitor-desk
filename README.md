# Quant Monitor Desk

Local-first quantitative monitoring console: trusted data, five-layer modeling, evidence-chain monitoring, read-only Agent explanation, human confirmation.

**Not** an auto-trading system on day one. The workflow is:

```text
Trusted data → Multi-layer modeling → Evidence monitoring → Agent summary → Human review
```

## Stack


| Layer    | Technology                                                             |
| -------- | ---------------------------------------------------------------------- |
| Backend  | Python, FastAPI, Pydantic, DuckDB, Parquet, Polars Lazy                |
| Frontend | Vite, React, TypeScript (layout is placeholder until user confirms UI) |
| Specs    | YAML / JSON / SQL contracts under `specs/`                             |


## Repository layout

```text
quant-monitor-desk/
  backend/          Application code
  frontend/         Dashboard shell (placeholder UI)
  scripts/          CLI entry points (Round 1+)
  tests/            pytest suite
  configs/          Local configuration templates
  data/             Runtime data (gitignored)
  docs/             Architecture, modules, ops, implementation tasks
  specs/            Machine-readable contracts and domain specs
  MIGRATION_MAP.md  Project navigation map
```

## Getting started

1. Read `MIGRATION_MAP.md` and `docs/INDEX.md`.
2. Read global rules under `docs/implementation_tasks/GLOBAL_*.md`.
3. Copy `.env.example` to `.env` and adjust paths if needed (empty `QMD_DATA_ROOT` uses `<repo>/data`).
4. Install backend: `pip install -e ".[dev]"`
5. Initialize runtime DB: `python scripts/init_db.py` (creates `data/duckdb/` automatically)
6. Run tests: `pytest -q`
7. Install frontend: `cd frontend && npm ci`
8. Run checks: `ruff check . && python -m compileall backend scripts tests`
9. Verify docs links: `python scripts/check_doc_links.py`

Recommended first-time verification (matches Round 1 repair gate):

```bash
pip install -e ".[dev]"
python scripts/init_db.py
pytest -q
ruff check .
python -m compileall -q backend scripts tests
cd frontend && npm ci && npm audit --audit-level=high && npm run typecheck && npm run build
```

`pytest -q` passes on a clean checkout **without** pre-creating `data/duckdb/`; `init_db.py` is still required for prod-path CLI and Tier B acceptance.

### Agent / Trellis workflow

This repo intentionally tracks `.cursor/` (IDE hooks) and `.trellis/` (task specs and workflow scripts) for AI-assisted development. Trust boundaries and clean-checkout steps are documented in [`docs/ops/agent_workflow_boundaries.md`](docs/ops/agent_workflow_boundaries.md).

## Implementation rounds

Execute `docs/implementation_tasks/` in order:

Round 0 (scaffold) → Round 1 (data foundation) → … → Round 5 (release).

## Resource profile

Default mode is `**eco**`. See `configs/resource_limits.yaml` and `docs/ops/performance_limits.md`.



## Rules

文档类文件请尽量用中文来撰写



