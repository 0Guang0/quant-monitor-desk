# Project overview — B3V-OPS (Phase 1a)

## 技术栈触点

- **Ops：** `backend/app/ops/db_inspector.py` — 只读 DuckDB inspect CLI 内核；硬编码 `KEY_TABLES` / `DEFERRED_ITEM_MAPPING`。
- **DB 写：** `backend/app/db/write_manager.py` — `SUPPORTED_MODES=(append_only, upsert_by_pk)`；`UNSUPPORTED_MODES` 三模式早拒。
- **契约：** `specs/contracts/ops_db_inspect_contract.yaml`、`write_contract.yaml`（Round 1 P0）。

## 与本任务相关模块

| 模块                                   | 角色                                         |
| -------------------------------------- | -------------------------------------------- |
| `db_inspector`                         | inspect 报告模型；须与 YAML 对齐             |
| `write_manager`                        | 写路径；须与 write_contract 语义对齐         |
| `tests/test_ops_db_inspector.py`       | 只读/无变异回归                              |
| `tests/test_write_manager.py`          | 写模式行为                                   |
| `tests/test_layer1_ingestion_gates.py` | 已有 key_tables 子集对照（非本任务 SSOT 测） |

## 风险摘要

- `WriteManager` GitNexus upstream **HIGH**（31 符号）— 仅改模式常量/早拒消息时仍须 impact。
- 禁止触及 `validation_gate`、RawStore、sync、layer5、registry 文件组。
