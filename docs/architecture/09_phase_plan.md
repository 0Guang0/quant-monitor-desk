# 产品能力分组

> 文件定位：产品能力分组参考。本文不定义交付顺序；具体批次、gate 和执行安排只能写入 `task/` 下的执行计划。
> 来源：原设计文档能力清单

# 17. 产品能力分组

## 本地数据底座

```text
DuckDB schema
本地文件系统目录
source_registry
QMT Adapter
日线 / 分钟线同步
FastAPI 基础查询
React 基础看板
```

## 五层框架骨架

```text
Layer 1 axis_registry / axis_observation / axis_feature_snapshot
Layer 2 cross_asset_sensor
Layer 3 industry_chain_node / edge / industry_chain_instrument_view
Layer 4 market_registry / calendar / breadth / market_detail_view
Layer 5 evidence_chain
```

## 多源与数据质量

```text
baostock
AkShare
巨潮
东方财富
Yahoo / 腾讯 / 百度 / 同花顺辅助源
source conflict validator
data_quality_log
```

## Agent 与日报

```text
daily_report_agent
news_event_agent
announcement_agent
cross_layer_explain_agent
agent_report
```

## 复盘与提醒

```text
watchlist
strategy_review
notification
performance review
human review workflow
```

---
