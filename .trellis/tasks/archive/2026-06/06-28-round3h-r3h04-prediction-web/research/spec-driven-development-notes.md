# Spec-driven Development Notes — R3H-04（Plan 2b）

## 契约面 → 测试映射

| 契约 | 本任务新增/触及 | 测试锚点 |
| --- | --- | --- |
| `source_capability_contract.yaml` | 三源 operations/fields | `test_source_capabilities -k kalshi` 等 |
| `source_route_contract.yaml` | web_search evidence-only route | `test_source_route_planner` |
| `layer5_evidence_contract.yaml` | manual_review_state | `test_prediction_market_adapters -k layer` |
| `user_input_privacy_contract.yaml` | web evidence 不得 clean write | `test_no_clean_write_for_web_evidence` |
| `datasource_service_contract.yaml` | DSS.fetch 证据路径 | port 集成测 |

## 新增 schema（Plan 命名 · Execute 实现）

1. `probability_signal_evidence_v1` — kalshi/polymarket bundle
2. `web_evidence_staging_v1` — web_search bundle + staging metadata

**必填证据字段（两 schema 共有）：** `source_fetch_id`, `content_hash`, `schema_hash`, `schema_version`, `fetch_log`, `source_id`, `retrieved_at`

**probability 专有：** `market_ticker`/`market_slug`, `yes_bid`, `yes_ask`, `probability`, `volume`, `liquidity`（polymarket 还须 `spread`, `resolution_source` 占位 **非事实**）

**web 专有：** `query`, `results[]`, `need_human_review=true`, `manual_review_state=queued`

## 禁止字段（Red Flag）

`resolved_outcome`, `fact_confirmed`, `clean_write_target`, `factual_resolution`
