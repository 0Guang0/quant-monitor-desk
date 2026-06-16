# Agent 工具契约

> 文件定位：Agent 工具 API 与数据边界实现文件。本文与 `docs/modules/agent_module.md`、`specs/contracts/agent_contract.yaml` 配套。  
> 核心原则：Agent 只能读取受控、分页、带来源和质量标记的数据；不能自由 SQL，不能直接写库，不能自由上网，不能输出交易动作。

---

# 1. Agent 工具总边界

允许：

```text
读取 Layer 1-5 snapshot
读取 evidence_chain
读取 report_registry / report_section
读取 data_health summary
读取人工确认清单
生成结构化解释文本到 agent_output_staging
```

禁止：

```text
自由 SQL
直接写 clean table
绕过 FastAPI / Repository 访问 DuckDB
自由联网抓新闻
执行 FullLoad / Backfill / Reconcile
输出买、卖、加仓、减仓、入场、出场等动作语义
返回无来源、无 timestamp、无 quality_flags 的结论
```

---

# 2. 工具调用路径

Agent 只能调用：

```text
GET /api/agent-tools/layer1/context
GET /api/agent-tools/layer2/context
GET /api/agent-tools/layer3/context
GET /api/agent-tools/layer4/context
GET /api/agent-tools/layer5/context
GET /api/agent-tools/evidence/context
GET /api/agent-tools/data-health/context
POST /api/agent-tools/explain/submit-staging
```

其中 `submit-staging` 只写入 `agent_output_staging`，不写 clean table；正式报告生成仍由报告模块读取 staging 后进行校验和入库。

---

# 3. 通用 Tool Response

```json
{
  "tool_name": "layer3_context",
  "target_id": "ai_compute_accelerator",
  "as_of_timestamp": "2026-06-14T16:00:00",
  "data": {},
  "evidence_refs": [],
  "quality_flags": [],
  "boundary_reminders": [],
  "row_count": 100,
  "truncated": false
}
```

必须字段：

```text
tool_name
target_id
as_of_timestamp
data
evidence_refs
quality_flags
boundary_reminders
row_count
truncated
```

---

# 4. 每个工具的最大返回量

| 工具 | 默认行数 | 硬上限 | 说明 |
|---|---:|---:|---|
| layer1_context | 50 | 200 | 指标解释和状态 |
| layer2_context | 50 | 200 | 跨资产传感器 |
| layer3_context | 100 | 300 | chain / node / edge / anchor 摘要 |
| layer4_context | 100 | 300 | 市场结构摘要 |
| layer5_context | 100 | 300 | 个股/合约证据摘要 |
| evidence_context | 100 | 500 | 证据链 |
| data_health_context | 100 | 300 | 数据质量和冲突 |

超过硬上限必须返回：

```text
truncated=true
boundary_reminders 包含 “结果已截断”
```

---

# 5. Tool: Layer 1 Context

## GET `/api/agent-tools/layer1/context`

Query Params：

```text
axis_id?: string
indicator_id?: string
as_of_date?: YYYY-MM-DD
include_history?: false
```

返回：

```text
axis state
indicator profile
latest observation
feature snapshot
interpretation snapshot
quality flags
boundary reminder
```

禁止：Agent 自己重新计算 z_score、percentile、state_bucket。

---

# 6. Tool: Layer 3 Context

## GET `/api/agent-tools/layer3/context`

Query Params：

```text
chain_id?: string
anchor_id?: string
include_edges?: true
include_layer5_latest?: true
```

返回：

```text
chain summary
nodes
edges
anchors
cross_chain_edges
latest snapshot
source_validation_status
impact_explanation_cn
```

禁止：返回全量 Layer 5 历史行情。

---

# 7. Tool: Evidence Context

## GET `/api/agent-tools/evidence/context`

Query Params：

```text
target_id: string
evidence_type?: filing | news | price | volume | financial | quality | conflict | report
```

返回证据链摘要。

Agent 的每句话解释必须能追溯到至少一个 evidence_ref，除非该句是明确的边界提醒。

---

# 8. Tool: Submit Staging

## POST `/api/agent-tools/explain/submit-staging`

用途：提交结构化解释结果到 staging，不直接发布。

Request：

```json
{
  "agent_name": "cross_layer_explain_agent",
  "target_id": "NVDA",
  "output_type": "cross_layer_explanation",
  "structured_output": {},
  "evidence_refs": [],
  "no_action_semantics_passed": true
}
```

校验：

```text
必须符合 agent_contract.yaml
必须通过 no_action_semantics_guard
必须有 evidence_refs
必须写 agent_run_log
```

---

# 9. No Action Semantics Guard

禁止词：

```text
买入
卖出
加仓
减仓
满仓
空仓
入场
出场
止盈
止损
抄底
逃顶
做多
做空
long
short
buy
sell
```

出现禁止词时：

```text
reject output
write agent_run_log
needs_human_review=true
```

---

# 10. Agent 工具验收测试

```text
Agent tool 不能自由 SQL
Agent tool 不能返回无来源结论
Agent tool 不能返回超过硬上限行数
submit-staging 不写 clean table
含动作语义输出必须被拒绝
Layer 3 tool 不返回全量 Layer 5 历史行情
data_health tool 能返回 RESOURCE_GUARD_PAUSED 状态
```
