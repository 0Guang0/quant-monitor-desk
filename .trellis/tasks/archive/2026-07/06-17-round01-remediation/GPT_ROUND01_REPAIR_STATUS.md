# GPT Round 0/1 复审 — Repair 状态（2026-06-17）

> 对照 GPT 上传 zip 复审清单逐项核对。  
> **结论：** Round 0/1 准入门禁 **已关闭**（本地验收通过）；Round 2 Batch A migration 序号顺延为 **004**（003 已用于 `resource_guard_metrics`）。

---

## P0

| ID   | GPT 问题                   | 修复                                                                                                              | 状态       |
| ---- | -------------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------- |
| P0-1 | clean checkout pytest 失败 | `REQUIRED_DIRS` 无 `data/duckdb`；`test_initDb_createsDuckDbDirectory`；README 顺序                               | **已修复** |
| P0-2 | Vite/esbuild CVE           | `vite@^8.0.16`、`@vitejs/plugin-react@^6.0.2`；`npm audit --audit-level=high` → 0                                 | **已修复** |
| P0-3 | reader 未应用 pragmas      | `reader()` 调用 `_apply_pragmas`；`test_reader_appliesThreadsAndMemoryLimit` / `test_reader_appliesTempDirectory` | **已修复** |
| P0-4 | ResourceGuard 阈值未全接入 | `ResourceSnapshot` + `evaluate()` 全信号；`003_resource_guard_metrics.sql`；log INSERT 扩展列 + 测试              | **已修复** |

---

## P1 / P2（GPT 新挖 + 建议）

| ID                            | 问题                                                                                                 | 修复                                                                              | 状态               |
| ----------------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------ |
| docs 坏链                     | INDEX.md 错误路径                                                                                    | 已指向 `01_context_and_scope` / `09_phase_plan`；`test_docsIndex_relativeLinks_*` | **已修复**         |
| 空 env 路径                   | `QMD_DATA_ROOT=` → `Path("")`                                                                        | `_path_env` + `expanduser`；`tests/test_config.py`                                | **已修复**         |
| configs vs specs              | 阈值语义混乱                                                                                         | `docs/ops/performance_limits.md` 权威表                                           | **已修复**         |
| WriteManager 外部事务失败审计 | `own_transaction=False` 校验失败 → 同连接 audit；SQL 错误 → FAILED 无第二连接（DuckDB 无 SAVEPOINT） | **已修复**                                                                        |
| FileRegistry 并发重复         | 竞态 duplicate                                                                                       | `test_register_duplicateHashViaConstraint_*`（002 UNIQUE index）                  | **已修复**         |
| `.trellis/.cursor`            | 边界未明                                                                                             | 方案 A：`docs/ops/agent_workflow_boundaries.md`                                   | **已修复（文档）** |

---

## 验收命令（GPT §七）

```bash
pip install -e ".[dev]"
python scripts/init_db.py
pytest -q
ruff check .
python -m compileall -q backend scripts tests

cd frontend
npm ci
npm audit --audit-level=high
npm run typecheck
npm run build
```

**本地结果（2026-06-17 收尾）：** 上述命令 **全部 exit 0**；`pytest -q --cov=backend --cov-fail-under=75` → **114 passed，94% coverage**；`ruff check .` → All checks passed；`QMD_DATA_ROOT` bootstrap ×2 idempotent。

---

## 未修复 / 延后（明确标注）

| 项                                        | 原因                                   |
| ----------------------------------------- | -------------------------------------- |
| Batch A `004_ingestion_sources`           | 属 Round 2 Execute，非 Round 1 repair  |
| ResourceGuard + ingestion 交叉 smoke      | Batch D（见 Batch A remediation P3-6） |
| `verify_applied_checksums` dedicated 测试 | 已知限制；003 列由 contract 测试覆盖   |

---

## 变更文件（Repair PR 范围）

```
backend/app/config.py
backend/app/core/resource_guard.py
backend/app/db/connection.py          # reader pragmas（既有）
backend/app/db/migrations/003_resource_guard_metrics.sql
backend/app/db/write_manager.py
frontend/package.json                 # vite 8（既有）
frontend/package-lock.json
docs/INDEX.md                         # 坏链（既有）
docs/ops/performance_limits.md
README.md
tests/test_project_scaffold.py
tests/test_config.py
tests/test_resource_guard.py
tests/test_duckdb_connection.py
tests/test_documentation_index.py
tests/test_schema_migration.py
tests/test_schema_contract.py
tests/test_write_manager.py
```

**Batch A 计划同步：** `MASTER.plan.md` 中 ingestion migration 改为 **`004_ingestion_sources.sql`**。
