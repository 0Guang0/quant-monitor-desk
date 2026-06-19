# Verification Commands (Windows)

Canonical gate commands for audits, CI, and Round handoff. Use project `.venv` and in-repo basetemp on Windows.

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk

# Backend tests + coverage gate (Round 2 baseline: fail_under=85)
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.audit-sandbox\pytest-full
.\.venv\Scripts\python.exe -m pytest -q --cov=backend --cov-fail-under=85 --basetemp=.audit-sandbox\pytest-cov

# Lint + format
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .

# Production gate + doc links
.\.venv\Scripts\python.exe scripts\production_gate.py
.\.venv\Scripts\python.exe scripts\check_doc_links.py

# Frontend
cd frontend
npm run typecheck
npm run test
cd ..

# Trellis execute handoff (archived Round 2 tasks)
.\.venv\Scripts\python.exe .trellis\scripts\task.py validate-execute-handoff .trellis\tasks\archive\2026-06\06-17-round2-batch-c-validation-conflict
.\.venv\Scripts\python.exe .trellis\scripts\task.py validate-execute-handoff .trellis\tasks\archive\2026-06\06-18-round2-batch-d-orchestrator

# GitNexus index freshness
node .gitnexus\run.cjs status

# DB init + registry (new environment)
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe scripts\sync_registry.py
.\.venv\Scripts\python.exe scripts\ci_ingestion_smoke.py
```

See also: [`ROUND3_HANDOFF.md`](../ROUND3_HANDOFF.md), [`schema/MIGRATION_COVERAGE.md`](../schema/MIGRATION_COVERAGE.md).
