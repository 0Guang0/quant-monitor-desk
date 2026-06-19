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

| 模块 | 禁止 |
|---|---|
| `backend.app.datasources` | import `backend.app.api`, `backend.app.agents`, `backend.app.db.write_manager` |
| `backend.app.api` | import `backend.app.datasources.adapters` |
| `backend.app.agents` | import `backend.app.db.write_manager`, `backend.app.sync.runners`, vendor adapters |
| `backend.app.layer*` | direct adapter factory / raw vendor classes |
| `frontend` | 被 backend import |

## 4. 后续检查脚本

```bash
python scripts/check_module_boundaries.py
python -m pytest tests/test_module_boundaries.py -q
```

## 5. 当前阶段说明

本文件只定义设计边界，不修改代码。若后续检查发现当前代码有违规 import，应按最小重构修复并记录在 Round2.6 自检报告。
