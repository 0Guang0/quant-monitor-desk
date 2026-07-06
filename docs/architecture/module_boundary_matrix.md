# Module Boundary Matrix（Round2.6）

## 1. 目的

Round3/4 会快速增加 Layer、API、Agent、Backtest、Frontend 模块。为避免隐式耦合，本矩阵把 EasyXT 的低耦合模块理念转为本项目的 import boundary contract。

机器契约见：`specs/contracts/module_boundary_contract.yaml`。

## 2. 总原则

1. Data source 模块只能提供 raw/staging/fetch_log，不写 clean 表。
2. Sync 模块可协调 validation/write，但不得依赖 API/Agent/Frontend。
3. API 层不得直接 import vendor adapter。
4. Agent 层只读，不得 import WriteManager、sync runners 或 vendor adapters。
5. Round3 Layer 模块消费 clean snapshots、lineage、quality flags，不直接抓外部源。
6. Review/backtest 模块只做复盘评估，不做交易执行。

## 3. 关键禁止边界

| 模块                      | 禁止                                                                               |
| ------------------------- | ---------------------------------------------------------------------------------- |
| `backend.app.datasources` | import `backend.app.api`, `backend.app.agents`, `backend.app.db.write_manager`     |
| `backend.app.api`         | import `backend.app.datasources.adapters`                                          |
| `backend.app.agents`      | import `backend.app.db.write_manager`, `backend.app.sync.runners`, vendor adapters |
| `backend.app.layer*`      | direct adapter factory / raw vendor classes · `backend.app.datasources.service`    |
| `frontend`                | 被 backend import                                                                  |

## 4. 后续检查脚本

```bash
python scripts/check_module_boundaries.py
python -m pytest tests/test_module_boundaries.py -q
```

## 5. 当前阶段说明（M-G1-03）

`module_boundary_contract.yaml` 已收紧：`layer1_axes`…`layer5_evidence` 的 `must_not_import` 含 `backend.app.datasources.service`（P1-03/04）。

- **S01（P1-04）：** `layer1_axes/ingestion*.py` 仍直连 `DataSourceService` — `check_module_boundaries.py` 与 `test_layer1Axes_detectsDatasourceServiceImport` 须检出（RED）；全树扫描 `test_productionBackend_passesModuleBoundaryScan` 为 **xfail** 直至 P1-14。
- **P1-14 后：** ingestion 改经 `sync_indicator`；全树边界须转绿。
