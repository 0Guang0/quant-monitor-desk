# Verification Commands (Windows)

Canonical gate commands for audits, CI, and Round handoff. **D-01 默认路径：`uv sync` / `uv run`**；下列 `.venv\python` 为已激活 venv 时的等价写法。

> Phase 3 已关闭台账中的 8 项 pytest 口径差；全量 `pytest -q` 应为绿。修复包列出的 Round 4+ 命名契约测试见 `specs/contracts/api_security_contract.yaml` 等待办。

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk

# 推荐（uv 主路径）
uv sync --locked
uv run python -m pytest -q --basetemp=.audit-sandbox\pytest-full
uv run python -m pytest -q --cov=backend --cov-fail-under=85 --basetemp=.audit-sandbox\pytest-cov
uv run ruff check .
uv run ruff format --check .
uv run python scripts\production_gate.py
uv run python scripts\check_doc_links.py

# 等价（已有 .venv 时）
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.audit-sandbox\pytest-full
.\.venv\Scripts\python.exe -m pytest -q --cov=backend --cov-fail-under=85 --basetemp=.audit-sandbox\pytest-cov
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
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
uv run python scripts\init_db.py
uv run python scripts\sync_registry.py
uv run python scripts\ci_ingestion_smoke.py
# 或：.\.venv\Scripts\python.exe scripts\init_db.py 等
```

See also: [`ROUND3_HANDOFF.md`](../ROUND3_HANDOFF.md), [`schema/MIGRATION_COVERAGE.md`](../schema/MIGRATION_COVERAGE.md).
