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

## Round 3 gate hygiene

Document/protocol gate tests for Round 3 merge review. **Staged-only** evidence must not be read as **production-live** readiness; passing these tests **does not open production-live** access. These commands are network-free by default.

| Gate ID                         | Purpose                                            | Test module                                     |
| ------------------------------- | -------------------------------------------------- | ----------------------------------------------- |
| `audit-trace-authority`         | Trellis Batch 2.75 audit trace authority files     | `tests/test_trellis_audit_trace_authority.py`   |
| `audit-registry-alignment`      | Batch 2.5 / 2.75 registry and task-card alignment  | `tests/test_round3_audit_registry_alignment.py` |
| `unresolved-item-coverage`      | Unresolved IDs mapped before Plan                  | `tests/test_unresolved_item_task_coverage.py`   |
| `batch25-staged-not-live`       | Batch 2.5 evidence is staged, not production-live  | `tests/test_batch25_production_data_gate.py`    |
| `production-live-pilot-policy`  | Batch 2.75 fail-closed pilot policy docs           | `tests/test_production_live_pilot_policy.py`    |
| `batch3-staged-downstream-gate` | `R3-B3-STAGED-DOWNSTREAM-GATE` closure semantics   | `tests/test_batch3_staged_downstream_gate.py`   |
| `fred-staged-semantics`         | `B2.5-O-05` FRED / macro_supplementary staged-only | `tests/test_fred_staged_semantics.py`           |

Run the full Round 3 gate hygiene bundle (merge coordinator / PROMPT_05):

```powershell
uv sync --locked --extra dev
uv run python -m pytest tests/test_trellis_audit_trace_authority.py -q
uv run python -m pytest tests/test_round3_audit_registry_alignment.py -q
uv run python -m pytest tests/test_unresolved_item_task_coverage.py -q
uv run python -m pytest tests/test_batch25_production_data_gate.py -q
uv run python -m pytest tests/test_production_live_pilot_policy.py -q
uv run python -m pytest tests/test_batch3_staged_downstream_gate.py -q
uv run python -m pytest tests/test_fred_staged_semantics.py -q
uv run python -m pytest tests/test_round3_verification_command_matrix.py -q
uv run python scripts/check_doc_links.py
```

Key closure tests (must stay green before Batch 3 runtime):

- `test_batch25_evidence_is_staged_not_production_live` — staged ≠ production-live
- `test_batch3_staged_gate_records_fail_closed_decisions` — Batch 3 gate fail-closed
- `test_policy_preservesSandboxAndRawOnlyControls` — sandbox-first pilot controls

**Related (not default Round 3 CI):** `tests/test_batch275_live_pilot_gate.py` includes `@pytest.mark.network` live-fetch cases. Run only with explicit authorization: `uv run python -m pytest tests/test_batch275_live_pilot_gate.py -q -m "not network"`.

See also: [`production_live_pilot_policy.md`](../quality/production_live_pilot_policy.md), [`staged_acceptance_policy.md`](../quality/staged_acceptance_policy.md).

See also: [`ROUND3_HANDOFF.md`](../ROUND3_HANDOFF.md), [`schema/MIGRATION_COVERAGE.md`](../schema/MIGRATION_COVERAGE.md).
