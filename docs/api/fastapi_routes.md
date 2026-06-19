# FastAPI 路由清单与实现契约

> 文件定位：API 路由级实现文件。本文是 `docs/modules/fastapi_backend.md` 的路由落地清单，供 Claude Code / Codex 逐路由实现。  
> 当前边界：API 默认只读 clean / snapshot / audit summary，不直接触发 FullLoad、Backfill、Reconcile，不直接写 DuckDB clean table。

---

# 1. 全局约束

所有 API 必须遵守：

```text
统一 Response Envelope
统一分页
统一 freshness / quality_flags / source_used 输出
统一错误码
禁止无分页大表返回
禁止 API router 直接拼接 SQL
禁止 API 请求绕过 Repository 读取 DuckDB
禁止 API 请求直接写 clean table
禁止输出交易动作语义
```

所有路由默认经过：

```text
Router
  → Request Schema / Query Params Validation
  → Service
  → ReadOnlyRepository
  → DuckDB / Parquet / Snapshot View
  → Response Envelope
```

---

# 2. 通用 Response Envelope

成功响应：

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
    "total": 1000,
    "query_cost_class": "LIGHT"
  },
  "errors": []
}
```

失败响应：

```json
{
  "ok": false,
  "data": null,
  "meta": {
    "generated_at": "2026-06-14T16:05:00"
  },
  "errors": [
    {
      "code": "QUERY_TOO_LARGE",
      "message": "Query exceeds local desktop resource limits.",
      "detail": {
        "suggestion": "Add date_range or reduce page_size."
      }
    }
  ]
}
```

---

# 3. 资源友好型 API 默认限制

因为系统运行在用户本机，API 不能默认占用过多内存、CPU 或磁盘 I/O。

| 项目 | 默认值 | 硬上限 | 说明 |
|---|---:|---:|---|
| page_size | 200 | 1000 | 以 `specs/contracts/api_security_contract.yaml` 为唯一权威 |
| Agent 查询行数 | 200 | 1000 | 以 `specs/contracts/api_security_contract.yaml` 为唯一权威，避免 Agent 一次吞太多上下文 |
| 普通 API date_range | 最近 90 天 | 1 年 | 超过需后台导出任务 |
| 分钟线 API date_range | 最近 5 个交易日 | 20 个交易日 | 大范围分钟线必须走后台任务 |
| 单请求超时 | 8 秒 | 30 秒 | 超时返回 `QUERY_TIMEOUT` |
| 单请求 query_cost | LIGHT/MEDIUM | HEAVY 禁止前台执行 | HEAVY 必须变成后台任务 |

触发下列情况必须拒绝前台执行：

```text
无 instrument_id 且无 date_range 查询分钟线
全市场全历史扫描
返回行数预估 > 5000
预估 DuckDB 扫描文件 > 2GB
CPU / memory guard 当前处于 WARN 或 PAUSE 状态
```

---

# 4. 路由组总览

```text
/api/market
/api/layer1
/api/layer2
/api/layer3
/api/layer4
/api/layer5
/api/evidence
/api/reports
/api/data-health
/api/agent-tools
/api/admin/jobs
```

---

# 5. Market 路由

## GET `/api/market/summary`

用途：市场总览页。

Query Params：

```text
market_id?: CN_A | US_EQ | HK_EQ | FUTURES | OPTIONS
as_of_date?: YYYY-MM-DD
```

返回字段：

```text
market_id
as_of_date
major_indices
turnover_summary
breadth_summary
risk_flags
quality_flags
```

## GET `/api/market/{market_id}/breadth`

用途：市场宽度页面。

必须分页，默认最近 60 个交易日。

---

# 6. Layer 1 路由

## GET `/api/layer1/state-snapshot`

返回五轴最新状态：

```text
axis_id
axis_name_cn
state_bucket
warning_level
summary_sentence
as_of_timestamp
quality_flags
```

## GET `/api/layer1/axis/{axis_id}`

返回某一轴的指标列表、观测值、标准化特征和解释。

## GET `/api/layer1/indicator/{indicator_id}`

返回单个指标详情。必须包含：

```text
raw_value
z_score
robust_z_score
percentile_rank
level_state
delta_state
boundary_reminder
source_used
quality_flags
```

禁止：返回买卖、加减仓、入场、出场等动作语义。

---

# 7. Layer 2 路由

## GET `/api/layer2/sensors`

返回跨资产传感器列表。

Query Params：

```text
asset_class?: FX | RATE | COMMODITY | VOL | ETF | SHIPPING
importance?: P0 | P1 | P2
```

## GET `/api/layer2/sensors/{sensor_id}`

返回单个传感器详情和最近序列。默认最多 180 天。

---

# 8. Layer 3 路由

## GET `/api/layer3/chains`

返回产业链列表。

必须包含：

```text
chain_id
chain_name_cn
chain_priority
chain_status
summary_cn
quality_flags
```

## GET `/api/layer3/chains/{chain_id}`

返回某条链的节点、锚点、边和最新快照。

## GET `/api/layer3/graph`

返回产业链图谱。

Query Params：

```text
chain_id?: string
include_cross_chain_edges?: boolean = true
priority?: P0 | P1 | P2
```

返回：

```text
chains[]
nodes[]
edges[]
anchors[]
cross_chain_edges[]
```

禁止：在该接口中读取全量 Layer 5 历史行情。价格、成交量、事件只来自最新 snapshot 或受限明细接口。

---

# 9. Layer 4 路由

## GET `/api/layer4/markets`

返回市场结构列表。

## GET `/api/layer4/markets/{market_id}`

返回单个市场结构详情：

```text
market_id
calendar_status
major_indices
sector_snapshot
breadth_snapshot
market_rule_events
quality_flags
```

## GET `/api/layer4/markets/{market_id}/rules`

返回市场规则，例如 A 股涨跌停、ST、港股南向、美股盘前盘后、期货主力合约切换等。

---

# 10. Layer 5 路由

## GET `/api/layer5/securities/{instrument_id}`

返回个股 / ETF / 期货 / 期权 / 商品合约详情。

## GET `/api/layer5/securities/{instrument_id}/bars`

默认日线，默认最近 90 天，分页或 date_range 必填。

## GET `/api/layer5/securities/{instrument_id}/events`

返回公告、新闻、财报、事件。

---

# 11. Evidence 路由

## GET `/api/evidence/{target_id}`

目标可以是：

```text
axis_id
sensor_id
chain_id
market_id
instrument_id
report_id
```

返回 evidence_chain，必须包含 source、timestamp、quality_flags。

---

# 12. Reports 路由

## GET `/api/reports/daily`

返回最新日报。

## GET `/api/reports/{report_id}`

返回指定报告。

## GET `/api/reports/manual-review`

返回人工确认清单。只能查看，不能自动处理。

---

# 13. Data Health 路由

## GET `/api/data-health`

返回系统健康总览：

```text
source_health
data_quality_summary
source_conflict_summary
resource_guard_status
latest_backup_status
```

## GET `/api/data-health/sources`

数据源健康列表。

## GET `/api/data-health/conflicts`

多源冲突列表。必须分页。

---

# 14. Agent Tool 路由

Agent 工具路由放在：

```text
/api/agent-tools/*
```

只允许返回受控结构化数据，不允许返回无限长文本，不允许自由 SQL。

详见：

```text
docs/api/agent_tool_contracts.md
docs/modules/agent_module.md
specs/contracts/agent_contract.yaml
```

---

# 15. Admin Job Request 路由

## POST `/api/admin/jobs/{job_type}/request`

该接口只创建任务请求，不直接执行重任务。

允许 job_type：

```text
incremental_update
backfill
revision_audit
reconcile
data_quality_check
snapshot_build
report_generate
```

返回：

```text
request_id
job_type
requested_by
status=REQUESTED
```

禁止：API 请求中同步执行回补或全量重建。

---

# 16. 错误码

| code | 含义 | 处理 |
|---|---|---|
| `BAD_REQUEST` | 参数错误 | 前端提示用户修正 |
| `QUERY_TOO_LARGE` | 查询超出本机资源限制 | 缩小范围或提交后台任务 |
| `QUERY_TIMEOUT` | 查询超时 | 返回部分提示，不重试无限次 |
| `DATA_STALE` | 数据滞后 | 展示 stale 标记 |
| `SOURCE_CONFLICT` | 多源冲突 | 展示人工确认状态 |
| `INSUFFICIENT_HISTORY` | 历史不足 | 不生成极端判断 |
| `RESOURCE_GUARD_PAUSED` | 本机资源保护触发 | 暂停非核心任务 |
| `INTERNAL_ERROR` | 未知错误 | 写 error log |

---

# 17. 路由验收测试

```text
所有列表接口必须分页
所有接口必须返回 Response Envelope
无 date_range 的大历史查询必须拒绝
Agent tool 不允许自由 SQL
Layer 3 graph 不允许读全量 Layer 5 历史行情
Data Health 能展示 resource_guard_status
错误响应必须有 code / message / detail
OpenAPI 能自动生成并通过 schema 校验
```

---

# 15. Notifications 路由

## GET `/api/notifications`

用途：通知中心读取盘中提醒、数据风险、系统风险和人工确认事项。

Query Params：

```text
severity?: INFO | WATCH | WARN | CRITICAL | DATA_RISK | OPS_RISK
source_layer?: Layer1 | Layer2 | Layer3 | Layer4 | Layer5 | OPS | DATA
status?: OPEN | ACKED | MUTED | EXPIRED
page?: number
page_size?: number
```

返回字段：

```text
notification_id
alert_id
severity
source_layer
target_id
title
summary
evidence_ids
quality_flags
dedup_key
cooldown_until
status
created_at
```

## POST `/api/notifications/{notification_id}/ack`

用途：用户确认已读。只更新 notification 状态，不改变原始事实和 evidence_chain。

## POST `/api/notifications/{notification_id}/mute`

用途：用户临时静音某类提醒。不得删除 alert_event，只写用户偏好。

---

# 16. Backtest / Review 路由

## GET `/api/backtest/scenarios`

用途：回测与复盘页读取可用场景。

返回字段：

```text
scenario_id
scenario_name
backtest_type
description
default_window_json
metric_set_json
resource_profile
```

## POST `/api/backtest/runs`

用途：用户主动启动一个回测/复盘 run。

必须经过 ResourceGuard。盘中轻量模式不得自动启动回测。

Request Body：

```json
{
  "scenario_id": "layer3_chain_review",
  "date_range_start": "2024-01-01",
  "date_range_end": "2026-06-14",
  "resource_mode": "normal",
  "universe": ["optional"]
}
```

## GET `/api/backtest/runs/{run_id}`

返回 run 状态、资源使用、样本数、质量标记。

## GET `/api/backtest/runs/{run_id}/events`

分页返回 event set。

## GET `/api/backtest/runs/{run_id}/metrics`

分页返回 metric snapshot。

## GET `/api/backtest/reports/{backtest_report_id}`

返回回测复盘报告。必须包含 limitations 和 no_action_semantics=true。

## 用户决策补充：API 安全模式

所有 FastAPI 路由必须遵守 D-02：dev 可关闭 token 但仅限 loopback；prod 必须启用 Bearer token。Admin job、backfill、full reload、manual override 等 mutation endpoint 在 prod 中必须要求认证和权限。


## API 安全与分页权威口径

`specs/contracts/api_security_contract.yaml` 是唯一机器契约。第一版采用本地 Bearer token：dev 可关闭但只能绑定 loopback；prod 必须启用 `QMD_API_TOKEN`，且单个本地 token 在第一版视为 `admin`。`viewer` 与 `agent_readonly` 角色保留为第二阶段能力，不得在第一版伪实现半套 RBAC。

分页统一口径：默认 `page_size=200`，绝对上限 `1000`，Agent tool 最大行数 `1000`，full-history 查询必须 admin。实现必须补 `test_pageSizeContract_matchesDocs`。
