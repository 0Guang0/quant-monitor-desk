# Module Boundary Matrix

## 1. 目的

系统会持续增加 Layer、API、Agent、Backtest、Frontend 模块。为避免隐式耦合，本矩阵把 EasyXT 的低耦合模块理念转为本项目的 import boundary contract。

机器契约见：`specs/contracts/module_boundary_contract.yaml`。

## 2. 总原则

1. Data source 模块只能提供 raw/staging/fetch_log，不写 clean 表。
2. Sync 模块可协调 validation/write，但不得依赖 API/Agent/Frontend。
3. API 层不得直接 import vendor adapter。
4. Agent 层只读，不得 import WriteManager、sync runners 或 vendor adapters。
5. Layer 模块只消费由 WriteManager 治理的可信最终库或连续监控视图、lineage 与完整来源/质量标签，不直接抓外部源。
6. Review/backtest 模块只做复盘评估，不做交易执行。

## 3. 关键禁止边界

| 模块                      | 禁止                                                                               |
| ------------------------- | ---------------------------------------------------------------------------------- |
| `backend.app.datasources` | import `backend.app.api`, `backend.app.agents`, `backend.app.db.write_manager`     |
| `backend.app.api`         | import `backend.app.datasources.adapters`                                          |
| `backend.app.agents`      | import `backend.app.db.write_manager`, `backend.app.sync.runners`, vendor adapters |
| `backend.app.layer*`      | direct adapter factory / raw vendor classes · `backend.app.datasources.service`    |
| `frontend`                | 被 backend import                                                                  |

## 4. 检查脚本

```bash
python scripts/check_module_boundaries.py
python -m pytest tests/test_module_boundaries.py -q
```

## 5. Layer 数据源边界

`module_boundary_contract.yaml` 要求：`layer1_axes`…`layer5_evidence` 的 `must_not_import` 含 `backend.app.datasources.service`。

- `layer1_axes/ingestion*.py` 不得直连 `DataSourceService`。
- Layer 需要抓取或同步数据时，必须经 `sync_indicator` 或同等 sync seam。
- 全树边界扫描必须保持绿色；任何例外必须写入执行计划，不得写入本矩阵作为永久放行。

## ADR-017 数据读取边界

Layer、API、Agent 与前端只可读取由 WriteManager 治理的可信最终库视图或连续监控视图，仍不得
直连数据源、raw 或 staging。连续监控视图的每个结果必须保留来源／质量／人工复核／RoutePlan
字段；审计归档区不进入默认读取或默认回测。
