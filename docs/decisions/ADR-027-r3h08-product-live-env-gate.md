# ADR-027: R3H-08 Product Live Env Gate and Tier Router

- **Status:** Accepted (Plan freeze)
- **Date:** 2026-06-29
- **Context:** Wave 2 产品 live 与 rehearsal 分离；24 源 Tier A/B/C

## Decision

1. 产品 live 须经 `ProductLiveGate`（env `QMD_ALLOW_LIVE_FETCH=1` + ResourceGuard + 非 rehearsal）。
2. `LiveTierRouter.resolve_live_tier(source_id)` 映射 PASS §2.1；Tier B 仅 pilot/audit-sandbox。
3. Fetch 仅经 `DataSourceService`；禁止 ops pilot 作为产品 SSOT。
4. EasyXT 式 silent source fallback **禁止**。
5. Execute **每个切片 RED 前**必 Read `参考项目/**` 登记源码（`reference-adoption-r3h08.md` §7）；**禁止不参考从零造**；禁止 runtime import 参考树。

## Consequences

- 新增 `product_live_gate.py` · `live_tier_router.py`（薄模块）
- 契约测扩展 `test_production_live_pilot_policy` / 新 `test_r3h08_*`
- reconcile/probe defer 在 S08-05 闭合

## Binding slices

S08-BOOT · S08-05
