# Context closure — B3V-OPS (Execute 6.pre 动态)

> Plan 占位；Execute boot 时 GitNexus `impact`/`context` 补全差集。

## Upstream wiring closure

| 符号                 | 预期 blast                        | Execute 结果                            |
| -------------------- | --------------------------------- | --------------------------------------- |
| `WriteManager.write` | HIGH — batch orchestration, smoke | **未改符号**；impact summaryOnly 已记录 |
| `KEY_TABLES`         | LOW — inspect + tests             | loader 从 YAML 加载；下游 import 不变   |

### 下游接线

| 下游                                                       | 接线                                                                                                         |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `KEY_TABLES` / `DEFERRED_ITEM_MAPPING`                     | module import 从 `ops_db_inspect_contract.yaml` 加载；`DbInspector.inspect` / `_build_deferred_mapping` 不变 |
| `mutation_proof` / `live_pilot_phase1` / `interface_probe` | 继续 `from db_inspector import KEY_TABLES` — 值来自契约                                                      |
| `WriteManager.SUPPORTED_MODES`                             | 与 `write_contract.yaml` `implemented_modes` parity 测锁定                                                   |
| `WriteManager.UNSUPPORTED_MODES`                           | 与 `reserved_modes` 一致（既有常量，未改符号）                                                               |
| drift 测                                                   | `tests/test_contract_drift_ops_write.py` 全量 key_tables + deferred + parity + reserved                      |

## Deferred (forbidden this task)

- B02-CLOSE-01 registry 三件套
- reserved 模式 runtime 实现
- validation_gate / RawStore / sync / layer5

## Execute 追加规则

- 改 `db_inspector` loader 前：`impact(KEY_TABLES)` + `context(inspect_db)` 流程
- 改 `write()` 早拒前：`impact(WriteManager)` summaryOnly 优先
