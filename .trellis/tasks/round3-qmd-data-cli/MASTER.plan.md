# MASTER — B3F-CLI `round3-qmd-data-cli`

> Playbook: B3F-CLI · Branch: `feature/round3-qmd-data-cli` · Baseline: `7f628c9`

## 0.1 状态

| 字段 | 值 |
| ---- | --- |
| 轨道 | complex |
| Roadmap | R3F-CLI-01..05 |
| 禁止 | production clean write；默认 live；`source_health_snapshot` 建表 |

## 8. Execute 垂直切片

### 8.1 R3F-CLI-01 — qmd data CLI smoke

| 字段 | 值 |
| ---- | --- |
| AC | dry-run / route-preview / error_code+docs_anchor |
| RED | `research/execute-evidence/8.1-red.txt` |
| GREEN | `research/execute-evidence/8.1-green.txt` |
| 已执行 | [x] |

### 8.2 R3F-CLI-02 — console_scripts smoke

| 字段 | 值 |
| ---- | --- |
| AC | `qmd-data` / `qmd-ops` entrypoints importable |
| RED | `research/execute-evidence/8.2-red.txt` |
| GREEN | `research/execute-evidence/8.2-green.txt` |
| 已执行 | [x] |

### 8.3 R3F-CLI-03 — init_db --sync-registry

| 字段 | 值 |
| ---- | --- |
| AC | CI one-liner `qmd-init-db --sync-registry` loads registry |
| RED | `research/execute-evidence/8.3-red.txt` |
| GREEN | `research/execute-evidence/8.3-green.txt` |
| 已执行 | [x] |

### 8.4 R3F-CLI-04 — packaging (remove sys.path.insert)

| 字段 | 值 |
| ---- | --- |
| AC | `sync_registry.py` / `ci_ingestion_smoke.py` without sys.path.insert |
| RED | `research/execute-evidence/8.4-red.txt` |
| GREEN | `research/execute-evidence/8.4-green.txt` |
| 已执行 | [x] |

### 8.5 R3F-CLI-05 — staging E2E runbook

| 字段 | 值 |
| ---- | --- |
| AC | `docs/ops/staging_data_e2e_runbook.md` no-default-live + CI one-liner |
| RED | `research/execute-evidence/8.5-red.txt` |
| GREEN | `research/execute-evidence/8.5-green.txt` |
| 已执行 | [x] |

## 10. 验证

```bash
uv sync --locked
uv run pytest tests/test_sync_jobs.py tests/test_qmd_data_cli.py -q
uv run ruff check backend/app/cli scripts/init_db.py scripts/sync_registry.py scripts/qmd_ops.py
uv run pytest -q
```

## 11. Execute → Audit DoD

- [x] §8.1–8.5 RED/GREEN 证据齐全（§8.3 含真实 pytest transcript）
- [x] Playbook §8.3 / MASTER §10 scoped pytest+ruff 绿（`test_sync_jobs` + `test_qmd_data_cli` + `test_data_cli_contract`）
- [x] 无 `source_health_snapshot` migration
- [x] 无默认 live fetch
- [x] `validate-execute-handoff` exit 0
- [x] `AUDIT.plan.md` + `audit.report.md` 已提交

> 全量 `uv run pytest -q` 归 **integration/round3-batch3f** 主会话轨；本分支 Repair 不宣称。

## 12. Skill 表

| Skill | 绑定步骤 | 状态 |
| ----- | -------- | ---- |
| test-driven-development | §8.x | 必做 | [x] |
| incremental-implementation | §8.x 末尾 | 必做 | [x] |
| karpathy-guidelines | GREEN 前 | 必做 | [x] |
| testing-guidelines | 测试编写 | 必做 | [x] |
