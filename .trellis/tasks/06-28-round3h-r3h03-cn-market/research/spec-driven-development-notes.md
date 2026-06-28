# Spec-Driven Development Notes — R3H-03（Plan 2b）

> 契约 → 测试映射 · 2026-06-28

## 权威契约（原文见 INDEX §3）

- `source_capability_contract.yaml` — FetchPort 形状
- `source_route_contract.yaml` — READY/DISABLED/validation_only
- `datasource_service_contract.yaml` — orchestrator 顺序
- `data_quality_rules.yaml` — DQ + ops_cli_profiles
- `source_conflict_rules.yaml` — eastmoney/sina vs primary
- `layer5_evidence_contract.yaml` — §9.9 smoke
- `reference_adoption_guardrails.yaml` — L2 迁 staged pilot

## 本任务新增契约面

1. **`cn_market_evidence_v1`** — `normalizers/cn_market.py`；对齐 `source_capabilities` 各 CN domain fields（`trade_date`/`observation_date`, hashes, `source_fetch_id`）。
2. **`license_gate` 决策枚举** — `AUTHORIZED` / `DISABLED_NO_ARTIFACT` / `DISABLED_ENV_MISSING`；QMT/iFinD/xqshare 须负例测试。
3. **registry 十源终态** — `READY_WITH_EVIDENCE` 或 ADR 文件 + route reason。

| 契约 / AC              | 测试锚点                                              |
| ---------------------- | ----------------------------------------------------- |
| cn_market evidence     | `test_cn_market_adapters -k evidence_contract`        |
| baostock primary       | `-k baostock_port` + route `-k baostock`             |
| cninfo filings         | `-k cninfo`                                           |
| akshare validation     | `-k akshare` + 负例 primary                           |
| TDX family             | `test_tdx_provider_port` + `-k mootdx`                |
| auth-gated             | `-k "ifind or qmt or xqshare"` unauthorized                      |
| source conflict        | `-k conflict` + `source_conflict_rules`               |
| 十源 registry          | `test_source_capabilities` + §9.8 manifest            |
| Layer CN smoke         | `-k layer_cn`                                         |

**Phase 2b complete**
