# 验收命令（Windows）

审计、CI 与 Round 交接的规范门禁命令。**D-01 默认路径：`uv sync` / `uv run`**；下列 `.venv\python` 为已激活 venv 时的等价写法。

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

# 等价（已有 .venv 时）
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.audit-sandbox\pytest-full
.\.venv\Scripts\python.exe -m pytest -q --cov=backend --cov-fail-under=85 --basetemp=.audit-sandbox\pytest-cov
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe scripts\production_gate.py

# 前端
cd frontend
npm run typecheck
npm run test
cd ..

# GitNexus 索引新鲜度
node .gitnexus\run.cjs status

# DB 初始化 + registry（新环境）
uv run python scripts\init_db.py
uv run python scripts\sync_registry.py
uv run python scripts\ci_ingestion_smoke.py
# 或：.\.venv\Scripts\python.exe scripts\init_db.py 等
```

## Round 3 门禁卫生

Round 3 合并评审的文档/协议门禁测试。**仅 staged** 证据不得解读为 **production-live** 就绪；通过这些测试 **不** 等于开放 production-live 访问。下列命令默认无网络。

| 门禁 ID                         | 目的                                             | 测试模块                                        |
| ------------------------------- | ------------------------------------------------ | ----------------------------------------------- |
| `audit-registry-alignment`      | Batch 2.5 / 2.75 registry 与任务卡对齐           | `tests/test_round3_audit_registry_alignment.py` |
| `unresolved-item-coverage`      | Plan 前未决 ID 已映射                            | `tests/test_unresolved_item_task_coverage.py`   |
| `batch25-staged-not-live`       | Batch 2.5 证据为 staged，非 production-live      | `tests/test_batch25_production_data_gate.py`    |
| `production-live-pilot-policy`  | Batch 2.75 fail-closed 试点策略文档              | `tests/test_production_live_pilot_policy.py`    |
| `batch3-staged-downstream-gate` | `R3-B3-STAGED-DOWNSTREAM-GATE` 闭环语义          | `tests/test_batch3_staged_downstream_gate.py`   |
| `fred-staged-semantics`         | `B2.5-O-05` FRED / macro_supplementary 仅 staged | `tests/test_fred_staged_semantics.py`           |

运行完整 Round 3 门禁卫生包（merge coordinator / PROMPT_05）：

```powershell
uv sync --locked --extra dev
uv run python -m pytest tests/test_round3_audit_registry_alignment.py -q
uv run python -m pytest tests/test_unresolved_item_task_coverage.py -q
uv run python -m pytest tests/test_batch25_production_data_gate.py -q
uv run python -m pytest tests/test_production_live_pilot_policy.py -q
uv run python -m pytest tests/test_batch3_staged_downstream_gate.py -q
uv run python -m pytest tests/test_fred_staged_semantics.py -q
uv run python -m pytest tests/test_round3_verification_command_matrix.py -q
```

关键闭环测试（Batch 3 运行前须保持绿）：

- `test_batch25_evidence_is_staged_not_production_live` — staged ≠ production-live
- `test_batch3_staged_gate_records_fail_closed_decisions` — Batch 3 门禁 fail-closed
- `test_policy_preservesSandboxAndRawOnlyControls` — 沙盒优先试点控制

**相关（非 Round 3 默认 CI）：** `tests/test_batch275_live_pilot_gate.py` 含 `@pytest.mark.network` live-fetch 用例。仅显式授权时运行：`uv run python -m pytest tests/test_batch275_live_pilot_gate.py -q -m "not network"`。

另见：[`production_live_pilot_policy.md`](../quality/production_live_pilot_policy.md)、[`staged_acceptance_policy.md`](../quality/staged_acceptance_policy.md)。

另见：[`ROUND3_HANDOFF.md`](../ROUND3_HANDOFF.md)、[`schema/MIGRATION_COVERAGE.md`](../schema/MIGRATION_COVERAGE.md)。
