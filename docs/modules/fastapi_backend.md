# FastAPI 后端模块

> 文件定位：实现级模块设计。本文从原 `fastapi_and_frontend.md` 拆出后端 API 部分，作为后续 Claude Code / Codex 实现 FastAPI 服务的权威文件。  
> 边界：FastAPI 只读访问 clean/snapshot 表；写入必须通过受控后台任务和 `DuckDBWriteManager`，前端与 Agent 不直接连接 DuckDB。

---

# 1. 模块目标

FastAPI 后端负责把 DuckDB / Parquet / 本地文件索引 / Agent 报告以稳定 API 暴露给前端和 Agent 工具层。

它承担：

```text
统一数据读取入口
统一分页、过滤、排序
统一 freshness / quality_flags 输出
统一错误码
统一 OpenAPI 文档
前端和 Agent 的权限边界
```

不承担：

```text
直接抓取数据
绕过 WriteManager 写库
在请求期间执行全库重计算
输出交易动作
```

FastAPI 官方定位是基于 Python 类型提示构建 API 的高性能 Web 框架，并支持自动生成交互式 API 文档；因此本系统继续使用 FastAPI 作为第一阶段后端 API 层。

---

# 2. 服务结构

推荐目录：

```text
src/quant_monitor/api/
  main.py
  deps.py
  errors.py
  pagination.py
  response.py
  routers/
    market.py
    layer1.py
    layer2.py
    layer3.py
    layer4.py
    layer5.py
    evidence.py
    reports.py
    data_health.py
    agent_tools.py
  schemas/
    common.py
    layer1.py
    layer2.py
    layer3.py
    layer4.py
    layer5.py
    reports.py
  services/
    read_repository.py
    snapshot_service.py
    evidence_service.py
    data_health_service.py
```

---

# 3. 只读边界

默认 API 只能读取：

```text
clean tables
snapshot tables
audit summary
file_registry index
agent report tables
```

禁止：

```text
API 请求中执行 FullLoad / Backfill / Reconcile
API 请求中直接写 clean table
API 请求中读取无限大历史并返回
API 请求中让 Agent 自由 SQL
```

允许的例外：

```text
POST /api/admin/jobs/{job_type}/request
```

该接口只写“任务请求表”，不直接执行写库任务；真正执行仍由 DataSyncOrchestrator 管理。

---

# 4. 通用 Response Envelope

所有 API 使用统一响应：

```json
{
  "ok": true,
  "data": {},
  "meta": {
    "as_of_timestamp": "2026-06-14T16:00:00",
    "generated_at": "2026-06-14T16:05:00",
    "data_lag_days": 0,
    "quality_flags": [],
    "source_used": "duckdb_snapshot",
    "page": 1,
    "page_size": 200,
    "total": 1000
  },
  "errors": []
}
```

错误响应：

```json
{
  "ok": false,
  "data": null,
  "meta": {
    "generated_at": "2026-06-14T16:05:00"
  },
  "errors": [
    {
      "code": "DATA_STALE",
      "message_cn": "数据已过期，请检查数据同步任务。",
      "details": {}
    }
  ]
}
```

---

# 5. 分页与限制

默认：

| 场景 | 限制 |
|---|---:|
| 普通表格 | `page_size=200`，绝对最大 1000；以 `specs/contracts/api_security_contract.yaml` 为权威。 |
| Agent 查询 | 默认 200 行，最大 1000；不得绕过 `api_security_contract.yaml`。 |
| 前端图谱 | 最大 200 nodes / 500 edges。 |
| 历史曲线 | 默认最近 1 年，必须传 date_range 才能查更长。 |
| 原始明细 | 必须指定 market / instrument_id / date_range。 |

禁止 API 返回全市场全历史未分页结果。

---

# 6. 路由清单

## 6.1 Market

```text
GET /api/market/summary
GET /api/market/{market_id}/breadth
GET /api/market/{market_id}/calendar
```

## 6.2 Layer 1

```text
GET /api/layer1/axes
GET /api/layer1/state-snapshot
GET /api/layer1/axis/{axis_id}
GET /api/layer1/indicator/{indicator_id}
GET /api/layer1/quality
```

## 6.3 Layer 2

```text
GET /api/layer2/assets
GET /api/layer2/sensors
GET /api/layer2/asset/{asset_id}
GET /api/layer2/divergence
GET /api/layer2/quality
```

## 6.4 Layer 3

```text
GET /api/layer3/chains
GET /api/layer3/chain/{chain_id}
GET /api/layer3/anchors
GET /api/layer3/graph
GET /api/layer3/cross-chain-edges
GET /api/layer3/quality
```

## 6.5 Layer 4

```text
GET /api/layer4/markets
GET /api/layer4/market/{market_id}
GET /api/layer4/market/{market_id}/sectors
GET /api/layer4/market/{market_id}/breadth
```

## 6.6 Layer 5

```text
GET /api/layer5/securities/{instrument_id}
GET /api/layer5/securities/{instrument_id}/bars
GET /api/layer5/securities/{instrument_id}/events
GET /api/layer5/securities/{instrument_id}/evidence
```

## 6.7 Evidence / Reports / Health

```text
GET /api/evidence/{target_id}
GET /api/reports/daily
GET /api/reports/weekly
GET /api/data-health
GET /api/data-health/source-conflicts
GET /api/data-health/manual-review-queue
```

---

# 7. Pydantic Schema 原则

所有 response schema 必须显式定义：

```text
field name
field type
nullable
中文说明
前端展示建议
quality_flags
```

禁止返回动态字段名作为核心结构，例如：

```json
{"eastmoney_main_inflow": 1, "ths_main_inflow": 2}
```

口径差异字段应使用长表结构：

```json
{
  "metric_id": "main_inflow",
  "source": "eastmoney",
  "value": 1.23,
  "unit": "CNY"
}
```

---

# 8. 错误码

| code | 含义 |
|---|---|
| `INVALID_REQUEST` | 请求参数错误。 |
| `DATA_NOT_FOUND` | 数据不存在。 |
| `DATA_STALE` | 数据过期。 |
| `QUALITY_BLOCKED` | 数据质量不允许展示。 |
| `SOURCE_CONFLICT` | 多源冲突未解决。 |
| `INSUFFICIENT_HISTORY` | 历史样本不足。 |
| `MANUAL_REVIEW_REQUIRED` | 需要人工确认。 |
| `QUERY_TOO_LARGE` | 查询范围过大。 |
| `INTERNAL_ERROR` | 系统内部错误。 |

---

# 9. Repository 规则

所有 SQL 通过 repository 层执行：

```text
Layer1Repository
Layer2Repository
Layer3Repository
Layer4Repository
Layer5Repository
EvidenceRepository
DataHealthRepository
```

禁止在 router 中直接拼 SQL。

所有 repository 方法必须有：

```text
输入参数类型
SQL 文件或 SQL builder
返回 schema
limit / offset
日期范围检查
异常处理
```

---

# 10. Agent Tool API

Agent 使用专用只读端点，不直接访问前端 API 的全部数据：

```text
GET /api/agent-tools/layer1-summary
GET /api/agent-tools/layer3-chain-summary/{chain_id}
GET /api/agent-tools/security-evidence/{instrument_id}
GET /api/agent-tools/data-quality-summary
```

Agent Tool 输出必须短小、结构化、带来源和质量标记。

---

# 11. OpenAPI 合同

后端必须生成 OpenAPI，并把稳定版本保存到：

```text
specs/api/openapi_contract.md
```

每次 API 字段变化都要更新：

```text
Pydantic schema
OpenAPI contract
frontend TypeScript type
测试用例
```

---

# 12. 测试清单

| 测试 | 预期 |
|---|---|
| API 无 date_range 查询大历史 | 返回 `QUERY_TOO_LARGE`。 |
| source_conflict 未解决 | 响应带 `SOURCE_CONFLICT`。 |
| 数据过期 | 响应带 `DATA_STALE`。 |
| Agent 尝试写库 | 拒绝。 |
| Router 直接 SQL | lint / review 阻断。 |
| Response 缺 meta.quality_flags | 测试失败。 |
| OpenAPI 未更新 | CI 失败。 |

---

# 13. 实现任务拆分

```text
1. 创建 FastAPI app skeleton
2. 实现 response envelope
3. 实现 pagination / date_range guard
4. 实现 repository 层
5. 实现 Layer 1-5 routers
6. 实现 data-health routes
7. 实现 agent-tool routes
8. 生成 OpenAPI contract
9. 编写 API tests
```

## 用户决策补充：API 鉴权模式

落实 D-02：第一版采用本地 Bearer token 模式，不做完整 OAuth。

```text
dev：允许关闭 token，但只能绑定 127.0.0.1 / localhost。
prod：必须启用 token；没有 QMD_API_TOKEN 直接启动失败。
prod：禁止 0.0.0.0 且关闭鉴权。
```


## API 安全与分页权威口径

`specs/contracts/api_security_contract.yaml` 是唯一机器契约。第一版采用本地 Bearer token：dev 可关闭但只能绑定 loopback；prod 必须启用 `QMD_API_TOKEN`，且单个本地 token 在第一版视为 `admin`。`viewer` 与 `agent_readonly` 角色保留为第二阶段能力，不得在第一版伪实现半套 RBAC。

分页统一口径：默认 `page_size=200`，绝对上限 `1000`，Agent tool 最大行数 `1000`，full-history 查询必须 admin。实现必须补 `test_pageSizeContract_matchesDocs`。

---

# 14. Round2.6 补充：Diagnostics 边界

Diagnostics 只做本地只读状态预览，覆盖 source route、registry validation、ResourceGuard snapshot 与配置路径摘要。它不能启动数据同步，也不能写入项目数据表或文件产物。

权威契约：`specs/contracts/diagnostics_api_contract.yaml`、`specs/contracts/datasource_service_contract.yaml`、`specs/contracts/source_route_contract.yaml`。

错误响应必须包含 `error_code` 与 `docs_anchor`，并链接到 `docs/ops/ERROR_CODE_GUIDE.md`。

必须补测试：`test_diagnosticsEndpointsReadOnly`、`test_apiRoutes_followModuleBoundary`、`test_sourceRoutePreviewDoesNotFetch`。
