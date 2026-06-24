# Bucket L1 — Phase A align-ponytail checklist

**Branch:** `debt/test-hygiene/bucket-l1-layer1`  
**Worktree:** `quant-monitor-desk-worktrees/bucket-l1-layer1`  
**Verify:** 153 passed (incl. 2 slow), 0 failed

## Module summary

| Module                                   | Tests | Align | Ponytail | Notes                                                                 |
| ---------------------------------------- | ----- | ----- | -------- | --------------------------------------------------------------------- |
| `test_layer1_axis_loader.py`             | 17    | Y     | Y        | Removed redundant `rule_version` assert; deduped orphan shadow lookup |
| `test_layer1_interpretation.py`          | 20    | Y     | Y        | Dropped unused `migrated_con`; reused `_insert_validation_report`     |
| `test_layer1_ingestion_gates.py`         | 35    | Y     | Y        | Added missing `source_content_hashes` contract type assert            |
| `test_layer1_observation_ingestion.py`   | 53    | Y     | Y        | Removed duplicate datetime import                                     |
| `test_observation_mapper.py`             | 11    | Y     | Y        | Added happy-path mapping test per module docstring                    |
| `test_ingestion_validation_migration.py` | 17    | Y     | Y        | Replaced local `_fresh_con` with conftest `migrated_con`              |

## Code fixes (comment → code)

| Location                                                | Issue                                                                                    | Fix                                               |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `test_layer1Lineage_phase0_ddlStoresSerializedFetchIds` | Docstring 验证点要求两列 contract 类型均为 `list[string]`，代码只断言 `source_fetch_ids` | 补充 `source_content_hashes` 类型断言             |
| `test_observation_mapper` module docstring              | 声明覆盖「合法数据映射」，缺专用 happy-path 用例                                         | 新增 `test_mapMicroFetch_mapsValidFixturePayload` |

## Ponytail (value conserved)

| Change                                                        | Rationale                                                         |
| ------------------------------------------------------------- | ----------------------------------------------------------------- |
| Remove `assert "rule_version" in cols`                        | Already covered by `AXIS_SNAPSHOT_LINEAGE_COLUMNS.issubset(cols)` |
| Reuse `orphan` vs second `next(...)`                          | Same indicator lookup; no coverage loss                           |
| Remove unused `migrated_con` on lineage writer tests          | `_persist_lineage` owns DB setup per docstring                    |
| Inline validation_report INSERT → `_insert_validation_report` | Same rows/fields; less duplication                                |
| `_fresh_con` → `migrated_con` fixture                         | conftest ladder #2; identical migration path                      |
| Drop redundant `from datetime import` in one test             | Module-level import already present                               |

## Per-module五问 (all Y unless noted)

### test_layer1_axis_loader.py — Y

1. 被测对象 = `AxisSpecLoader` / `AxisEngineeringGuardrailValidator` / migration DDL — **Y**
2. 验证点均被 assert/raises 覆盖 — **Y**
3. 失败含义与断言粒度一致 — **Y**
4. 无注释未声称的额外行为（已删冗余 assert） — **Y**
5. 使用 `migrated_con` — **Y**

### test_layer1_interpretation.py — Y

1. Feature/interpretation/lineage/WriteManager 路径 — **Y**
2. 血缘必填字段、哈希、WM 审计等验证点 — **Y**
3. ResourceGuard mock 仅用于注释声明的 HARD_STOP — **Y**
4. 移除未用 fixture — **Y**
5. `_insert_validation_report` 复用 — **Y**

### test_layer1_ingestion_gates.py — Y

1. Phase0 gate：契约 YAML、迁移、路由、文档 — **Y**
2. 契约对齐验证点 — **Y**（补全 lineage 双列类型）
3. 委托 `test_noSilentFallbackCopied` 符合注释 — **Y**
4. 无额外 production-live 断言 — **Y**
5. `migrated_con` + `contract_gate_support` — **Y**

### test_layer1_observation_ingestion.py — Y

1. Phase1–4 摄取全流程 + evidence — **Y**
2. 只读/试路由/staging/clean write 验证点 — **Y**
3. mock 仅用于注释允许的 route/fetch/guard 注入 — **Y**
4. 无注释外弱化 — **Y**
5. 与 conftest 模式一致（未改 conftest） — **Y**

### test_observation_mapper.py — Y

1. `map_micro_fetch_to_observation_row` / `observation_row_to_domain` — **Y**
2. 拒绝路径 + 合法映射验证点 — **Y**
3. 语义断言 on 业务字段 — **Y**
4. helpers `_micro`/`_write_raw` 仅支撑声明场景 — **Y**
5. 夹具路径与 ingestion 桶一致 — **Y**

### test_ingestion_validation_migration.py — Y

1. migration 005 表与 CHECK 约束 — **Y**
2. DDL 拒绝/接受验证点 — **Y**
3. `duckdb.Error` 粒度匹配 — **Y**
4. 删除未用 `MIGRATIONS_DIR` — **Y**
5. `migrated_con` 替代重复 `_fresh_con` — **Y**

## Phase B perf notes (no changes in Phase A)

- `test_layer1_observation_ingestion.py` — phase3/phase4 task evidence marked `@pytest.mark.slow`; candidate for fixture scope only in Phase B.
- `test_layer1_ingestion_gates.py` — many `read_text` gate scans; Phase B may share module-scope text loads if value checklist passes.
