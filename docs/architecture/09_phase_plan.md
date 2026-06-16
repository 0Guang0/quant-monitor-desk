# 分阶段实现计划

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 17 章

# 17. 分阶段实现计划

## Phase 1：本地数据底座

```text
DuckDB schema
本地文件系统目录
source_registry
QMT Adapter
日线 / 分钟线同步
FastAPI 基础查询
React 基础看板
```

## Phase 2：五层框架骨架

```text
Layer 1 axis_registry / axis_observation / axis_feature_snapshot
Layer 2 cross_asset_sensor
Layer 3 industry_chain_node / edge / industry_chain_instrument_view
Layer 4 market_registry / calendar / breadth / market_detail_view
Layer 5 evidence_chain
```

## Phase 3：多源与数据质量

```text
baostock
AkShare
巨潮
东方财富
Yahoo / 腾讯 / 百度 / 同花顺辅助源
source conflict validator
data_quality_log
```

## Phase 4：Agent 与日报

```text
daily_report_agent
news_event_agent
announcement_agent
cross_layer_explain_agent
agent_report
```

## Phase 5：复盘与提醒

```text
watchlist
strategy_review
notification
performance review
human review workflow
```

---
