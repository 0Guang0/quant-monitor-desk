# GitNexus summary — B3V-OPS (Phase 1b)

## Query 锚点

- db-inspect contract drift：`KEY_TABLES`、`DEFERRED_ITEM_MAPPING` vs YAML
- WriteManager write modes：`SUPPORTED_MODES` / `UNSUPPORTED_MODES` vs `write_contract.yaml`

## Impact 预研

| 符号 | direction | risk | 摘要 |
| ---- | --------- | ---- | ---- |
| `KEY_TABLES` (`db_inspector.py`) | upstream | LOW | 直接依赖主要在 inspect 路径与测试 |
| `WriteManager` | upstream | **HIGH** | 15 direct / 31 total upstream — 编排、batch 流、smoke 均调用 `write()` |

**Execute 警告：** 修改 `WriteManager.write` 早拒分支前必须 `impact(WriteManager)`；优先只改契约 YAML + 新增漂移测试，运行时改动限于 loader 与错误消息稳定性。

## Codebase-memory 交叉核实

- `test_layer1_ingestion_gates.test_dbInspect_keyTables_includeLayer1AxisTables` 已对照 contract `key_tables`（轴表子集）。
- `test_write_manager` / `test_r3x_ponytail_structural_bucket_b` 已覆盖 `replace_partition` / `manual_patch` 早拒。
- **缺口：** 无 `deferred_item_mapping` 漂移测；无 `implemented_modes` 契约/runtime parity 测。

## 复用策略

- 漂移测集中在新文件 `tests/test_contract_drift_ops_write.py`（避免散落弱断言）。
- db-inspect loader：模块内 `_load_ops_inspect_contract()` 读 YAML，导出 `KEY_TABLES` / `DEFERRED_ITEM_MAPPING`（删除重复字面量）。

## 按切片分组

| 切片 | 触点 | 改动面 |
| ---- | ---- | ------ |
| OPS-01/02 | `db_inspector.py` + contract yaml | 低~中 |
| WRITE-01/02/03 | `write_contract.yaml` + `write_manager.py`（消息） | 中（WriteManager HIGH） |
