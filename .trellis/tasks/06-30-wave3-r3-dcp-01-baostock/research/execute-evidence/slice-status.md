# Execute 切片完成表 — R3-DCP-01

| Slice | 状态 | 证据 |
|-------|------|------|
| S01-WATERMARK | [x] | `research/execute-evidence/s01-s05-green.txt` (watermark pytest) |
| S02-RUNNER-WIRE | [x] | `tests/test_sync_runners.py::test_incrementalRunner_injectsDateWindowIntoFetchRequest` |
| S03-E2E-INCR | [x] | `tests/test_baostock_incremental_e2e.py` |
| S04-IDEMPOTENT | [x] | `test_baostockIncremental_repeatRun_noRowGrowth` |
| S05-CLI | [x] | `tests/test_qmd_data_sync_baostock.py` |
| S06-REGISTRY | [x] | `loop_maintain.py --fix` → `tests/test_catalog.yaml`（coordinator merge） |

## 靶向命令

```text
uv run pytest tests/test_baostock_incremental_watermark.py tests/test_baostock_incremental_e2e.py tests/test_qmd_data_sync_baostock.py tests/test_sync_runners.py::test_incrementalRunner_injectsDateWindowIntoFetchRequest -q
→ 12 passed
```

## 全量 pytest

```text
uv run pytest -q → 2 failed（环境 canonical data/ 污染，非本轨逻辑）
  - test_batch25_production_data_gate::*（fetch_log/raw 含早先未 patch DATA_ROOT 的 CLI smoke 残留）
```

清理 canonical `data/duckdb` fetch_log + `data/raw` 非 staged_fixture 文件后可全绿。
