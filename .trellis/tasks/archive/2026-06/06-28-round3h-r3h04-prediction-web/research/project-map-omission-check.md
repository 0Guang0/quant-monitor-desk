# Project Map Omission Check — R3H-04

> Plan 冻结前对照 `check_docs_specs_indexed.py` 精神自检

## 新建文件（Execute 须创建）

```text
backend/app/datasources/fetch_ports/kalshi_port.py
backend/app/datasources/fetch_ports/polymarket_port.py
backend/app/datasources/fetch_ports/web_search_evidence_port.py
backend/app/datasources/normalizers/probability_signal.py
backend/app/evidence/manual_review_staging.py
tests/test_prediction_market_adapters.py
tests/test_web_evidence_adapter.py
tests/test_no_clean_write_for_web_evidence.py
tests/fixtures/replay/prediction_market/kalshi/sample_replay.json
tests/fixtures/replay/prediction_market/polymarket/sample_replay.json
tests/fixtures/replay/web_evidence/sample_replay.json
```

## 共享文件 touch（仅三源行）

```text
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/source_capability_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_catalog.yaml
```

## omission 结论

无未索引的 docs/specs 输入；活卡 §2 清单已纳入 INDEX §3 或 §4。
