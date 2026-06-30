# GitNexus Summary — B3V-STOR

> Plan Phase 1b · `impact(RawStore, upstream)`

## Impact 分析

| 字段                   | 值                                                |
| ---------------------- | ------------------------------------------------- |
| Target                 | `Class:backend/app/storage/raw_store.py:RawStore` |
| Direction              | upstream                                          |
| Risk                   | **MEDIUM**                                        |
| Direct importers (d=1) | 6                                                 |
| Total impacted         | 18                                                |

### d=1 直接调用方（改 `save` 行为须回归）

| 文件                                           | 关系               |
| ---------------------------------------------- | ------------------ |
| `tests/test_raw_store.py`                      | 测试               |
| `backend/app/layer1_axes/ingestion.py`         | 生产落盘           |
| `backend/app/storage/file_registry.py`         | 注册邻接           |
| `backend/app/datasources/adapters/__init__.py` | adapter fetch 落盘 |
| `backend/app/ops/staged_pilot.py`              | staged pilot       |
| `backend/app/ops/interface_probe.py`           | probe              |

### d=2–3 间接（全量 pytest 覆盖）

`datasources/service.py` · `sync/runners.py` · `layer1_axes/ingestion_commit.py` · live_pilot\* · `scripts/run_staged_pilot.py`

## 变更策略

1. **最小面：** 在 `path_compat` 增加 `write_bytes_atomic`；`RawStore.save` 单行替换调用。
2. **保留** `write_bytes` 供非证据路径只读对照（若有）；不在本任务扩散替换全仓库。
3. Execute 前对 `write_bytes_atomic` 再跑 `impact()`；MEDIUM 风险 — 全量 `pytest -q` 为合并门禁。

## Context（RawStore）

- Methods: `__init__`, `save`
- `save` 出站：`mkdir_parents`, `write_bytes`, `sha256_hex`, `is_relative_to_data_root`

## 结论

blast radius 可控；无 HIGH/CRITICAL。禁止顺带改 FileRegistry / validation_gate。
