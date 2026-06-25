# Audit 计划 — B3F-CLI `round3-qmd-data-cli`

| 字段 | 值 |
| ---- | -- |
| slug | `round3-qmd-data-cli` |
| Playbook ID | B3F-CLI |
| audit.jsonl | 第一条 = 本文件 |
| AUDIT_PROD_ROOT | N/A（staged/tmp_path / audit-sandbox only） |

## 0.1 Trace Authority Set

| 类别 | 文件 | 用途 |
| ---- | ---- | ---- |
| 协调包 | `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.4 / §8.3 | scope / PASS 命令 |
| MASTER | `MASTER.plan.md` §8–§11 | Execute 证据与验收 |
| 契约 | `specs/contracts/data_cli_contract.yaml` | A4/A8 |
| CLI 语义 | `docs/ops/data_sync_quick_reference.md` · `staging_data_e2e_runbook.md` | A7 |
| context | `research/context-closure.md` · `implement.jsonl` | A5 |

## 1. 维度 — Skill 冻结

| 维 | Agent | 本任务 | 已执行 |
| -- | ----- | ------ | ------ |
| A1 | audit-a1-spec | 必做 | [x] |
| A2 | audit-a2-ponytail | 必做 | [x] |
| A3 | security-auditor | 必做 | [x] |
| A4 | code-reviewer | 必做 | [x] |
| A5 | audit-a5-completion | 必做 | [x] |
| A6 | audit-perf | **SKIP** — 无 perf AC | [x] |
| A7 | database-administrator + sre-engineer | 必做 | [x] |
| A8 | qa-expert | 必做 | [x] |

## 2. 验证矩阵

| 维 | 验证类型 | 命令 / 检查 | 环境 | 通过条件 | 已执行 |
| -- | -------- | ----------- | ---- | -------- | ------ |
| A1 | read-only | `git diff 7f628c9..HEAD` vs R3F-CLI-01..05 + playbook §8.3 | local | 无 scope creep；交付物已 commit | [x] |
| A2 | review-only | ponytail-review `init-basic` / `health` 占位 | local | 无阻塞 bloat | [x] |
| A3 | static | `rg` 密钥/SQL 拼接/默认 live/`source_health_snapshot` migration | local | 零越界 | [x] |
| A4 | review-only | CLI fail-closed + packaging 一致性 | local | init_basic sync 闭合 | [x] |
| A5 | trace-ac | §8.3 execute-evidence 真实 pytest 输出 | local | RED/GREEN 可复现 | [x] |
| A6 | — | **SKIP** | — | 记录 SKIP | [x] |
| A7 | cli-sandbox | 见 §2.1 A7 冻结命令 | audit-sandbox | init 幂等；`--sync-registry` 绿 | [x] |
| A8 | pytest-isolated | `tests/test_qmd_data_cli.py` + `test_sync_jobs.py` + contract | audit-sandbox | 五字段齐全；AC 子集锁死 | [x] |

### 2.1 A7 冻结命令（运维面）

```bash
uv sync --locked
QMD_DATA_ROOT=.trellis/tasks/round3-qmd-data-cli/.audit-sandbox/a7-cli/data \
  uv run python scripts/init_db.py --db .trellis/tasks/round3-qmd-data-cli/.audit-sandbox/a7-cli/data/duckdb/quant_monitor.duckdb
QMD_DATA_ROOT=.trellis/tasks/round3-qmd-data-cli/.audit-sandbox/a7-cli/data \
  uv run python scripts/init_db.py --db .trellis/tasks/round3-qmd-data-cli/.audit-sandbox/a7-cli/data/duckdb/quant_monitor.duckdb
QMD_DATA_ROOT=.trellis/tasks/round3-qmd-data-cli/.audit-sandbox/a7-cli/data \
  uv run python scripts/init_db.py --db .trellis/tasks/round3-qmd-data-cli/.audit-sandbox/a7-cli/data/duckdb/quant_monitor.duckdb --sync-registry
QMD_DATA_ROOT=.trellis/tasks/round3-qmd-data-cli/.audit-sandbox/a7-cli/data \
  uv run python scripts/init_db.py --db .trellis/tasks/round3-qmd-data-cli/.audit-sandbox/a7-cli/data/duckdb/quant_monitor.duckdb --sync-registry
uv run pytest tests/test_qmd_data_cli.py tests/test_sync_jobs.py tests/test_data_cli_contract.py -q
uv run ruff check backend/app/cli scripts/init_db.py scripts/sync_registry.py scripts/qmd_ops.py scripts/ci_ingestion_smoke.py
uv run python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/round3-qmd-data-cli
```

| 步骤 | 通过条件 |
| ---- | -------- |
| init 第 1/2 次 | exit 0；第二遍 `applied none (up to date)` |
| init+sync 第 1/2 次 | exit 0；`sync_registry rows=`；第二遍 rows 稳定 |
| Playbook §8.3 scoped pytest | exit 0 |
| scoped ruff | exit 0 |
| handoff | exit 0 |

**禁止项（A7）：** production clean write；`source_health_snapshot` 建表；默认 live fetch。

### 2.2 Playbook §8.3 scoped 验收（A5/A7 共用）

```bash
uv sync --locked
uv run pytest tests/test_sync_jobs.py tests/test_qmd_data_cli.py tests/test_data_cli_contract.py -q
uv run ruff check backend/app/cli scripts/init_db.py scripts/sync_registry.py scripts/qmd_ops.py scripts/ci_ingestion_smoke.py
```

> 全量 `uv run pytest -q && uv run ruff check .` 归 **integration/round3-batch3f** 主会话轨；本分支 MASTER §11 仅勾选 scoped 子集。

## 3. Audit DoD

- [x] A1–A8 报告汇总至 `audit.report.md`
- [x] `audit_matrix.json` 无 OPEN BLOCK/WARN
- [x] A6 SKIP 已记录
- [x] PASS 前 Repair 已 commit
