# Project map omission check — 019 Layer 2

对照 `MIGRATION_MAP.md` § Layer 2：

| 映射项   | 计划覆盖 | 实现路径                                      |
| -------- | -------- | --------------------------------------------- |
| 模块设计 | ✅       | `docs/modules/layer2_cross_asset_sensor.md`   |
| 契约     | ✅ 只读  | `specs/contracts/layer2_sensor_contract.yaml` |
| 任务卡   | ✅       | `019_implement_layer2_cross_asset_sensor.md`  |
| 实现目录 | ✅       | `backend/app/layer2_sensors/`                 |
| 测试     | ✅       | `tests/test_layer2_sensor_loader.py`          |

## 有意 filtered-out / deferred

| 项                                  | 原因                                                   |
| ----------------------------------- | ------------------------------------------------------ |
| `configs/layer2_sensors.yml`        | staged fixture 在 `tests/fixtures/`；生产 config defer |
| DuckDB migration `cross_asset_*`    | MASTER 非目标；sandbox DDL in `schema_ddl.py`          |
| FastAPI `/api/layer2/*`             | 任务卡非目标；Round 4+                                 |
| `cross_asset_signal_snapshot`       | 模块 §12 后续子任务                                    |
| `snapshot_lineage_contract.yaml` 写 | 023A 拥有写权限                                        |

## 遗漏检查结论

无未记录的实现目录遗漏；deferred 项已写入 MASTER §2 与 merge report。
