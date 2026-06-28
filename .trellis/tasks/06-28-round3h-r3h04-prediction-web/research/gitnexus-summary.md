# GitNexus Summary — R3H-04（Plan 1b）

> Plan 1b 深度分析 · 改码前 Execute 须 `impact()`

## Query 摘要

`query("prediction market evidence adapter fetch port manual review staging")` 命中：

- `DataSourceService.fetch` — MEDIUM（所有 port 最终经 DSS）
- `BaseDataAdapter.fetch` / `fetch_port.FetchPayload` — LOW
- `layer5_evidence.foundation.EvidenceFoundationValidator` — LOW（manual_review 校验）
- `evidence_bundle.finalize_bundle` — LOW（哈希/证据字段）
- `route_planner` / `capability_registry` — MEDIUM（§9.5 registry 步）

## Impact 预判（Execute 每步前必跑）

| 符号 / 模块 | 风险 | 触发 Step |
| --- | --- | --- |
| `DataSourceService.fetch` | MEDIUM | 9.2–9.4 |
| `route_planner` | MEDIUM | 9.5 |
| `capability_registry` | MEDIUM | 9.5 |
| `EvidenceFoundationValidator` | LOW | 9.7 |
| `source_registry.yaml`（三行） | MEDIUM | 9.5 |
| `test_source_route_planner.py` | LOW | 9.5–9.6 |

**整体：** MEDIUM — 新模块为主，共享 registry 切片需 coordinator manifest。

## 不存在符号（须新建）

- `kalshi_port` / `polymarket_port` / `web_search_evidence_port`
- `probability_signal` normalizer
- `manual_review_staging`

## ponytail 备注

端口内 cap（`reject_over_cap`）即可；不扩 `resource_guard.py` 除非 Execute 发现共享 profile 真缺失——须回 Plan + BRANCH 授权。
