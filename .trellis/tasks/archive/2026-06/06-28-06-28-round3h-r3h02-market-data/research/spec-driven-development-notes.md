# Spec-Driven Development Notes — R3H-02（Plan 2b）

> 契约面收敛 · 2026-06-28

## 权威契约（Execute 须 Read 原文 — INDEX §3）

| 契约文件                             | 本任务用法                       |
| ------------------------------------ | -------------------------------- |
| `source_capability_contract.yaml`    | FetchPort 操作与 fields 对齐     |
| `source_route_contract.yaml`         | READY/DISABLED/validation-only   |
| `datasource_service_contract.yaml`   | DSS fetch 边界                   |
| `data_quality_rules.yaml`            | OHLCV 完整性 / freshness         |
| `layer5_evidence_contract.yaml`      | §9.7 smoke provenance            |
| `resource_limits.yaml`               | ResourceGuard 默认               |
| `reference_adoption_guardrails.yaml` | L2 迁 port；禁止参考项目 runtime |

## 本任务新增契约面

### market_data_evidence_v1

```yaml
schema_version: market_data_evidence_v1
required_fields:
  - instrument_id
  - trade_date
  - open
  - high
  - low
  - close
  - volume
  - source_used
  - source_fetch_id
  - content_hash
  - schema_hash
  - retrieved_at
optional_fields:
  - window_kind # ponytail: calendar_days until TradingCalendar SSOT
```

### crypto_market_evidence_v1

分 instrument 记录；deribit surface / coingecko spot reference 字段对齐 capabilities。

## spec → test 映射

| AC                | pytest 锚点                                      |
| ----------------- | ------------------------------------------------ |
| evidence contract | `test_market_data_adapters -k evidence_contract` |
| alpha_vantage     | `-k alpha_vantage`                               |
| stooq             | `-k stooq`                                       |
| yahoo validation  | `-k yahoo` + `test_advR3xRoute001`               |
| crypto            | `test_crypto_market_adapters`                    |
| registry          | `test_source_capabilities` + route planner       |
| layer smoke       | `-k layer`                                       |

**Phase 2b complete**
