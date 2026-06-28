# Batch 3H Task Card Manifest

> **Batch:** Round 3H Real Data Production Entry  
> **Runtime posture:** real data production-entry preparation; capped and gated only; no full-market/full-history default.  
> **Structure rule:** one source/domain family = one executable task card. Shared registry/capability/route updates are coordinated, not hidden inside one giant adapter PR.  
> **Completion rule:** every target source in `source_registry.yaml` / `source_capabilities.yaml` must be closed by implementation or ADR scope narrowing before Round4.

---

## 1. Task summary

| Task ID  | Active card                                          | Required source coverage                                                                                                      | Module movement                                                                                                                       | Completion rule                                                                                                                         |
| -------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `R3H-01` | `R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md`       | `fred`, `us_treasury`, `sec_edgar`, `cftc_cot`, `bis`, `world_bank`                                                           | Official macro/disclosure sources move from staged/proposed-disabled to capped READY/sandbox/limited-production entry or ADR-disabled | Every listed source has adapter/gate/replay/route/evidence or an ADR that excludes it from the current product promise                  |
| `R3H-02` | `R3H_02_MARKET_DATA_ADAPTERS.md`                     | `alpha_vantage`, `stooq`, `yahoo_finance`, `deribit`, `coingecko`                                                             | Market data sources move from scaffold/proposed-disabled to capped READY/sandbox/validation entry or ADR-disabled                     | Every listed source has adapter/gate/replay/route/evidence or an ADR that excludes it from the current product promise                  |
| `R3H-03` | `R3H_03_CN_MARKET_ADAPTERS.md`                       | `baostock`, `akshare`, `cninfo`, `tdx_pytdx`, `mootdx`, `eastmoney`, `sina_finance`, `ths_ifind`, `qmt_xtdata`, `qmt_xqshare` | CN market and validation/authorized sources close primary/validation/authorized-disabled posture                                      | Every listed source is implemented to its declared role or remains disabled with tested route reason and authorization/license boundary |
| `R3H-04` | `R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md`     | `kalshi`, `polymarket`, `web_search`                                                                                          | Probability/web evidence sources move from generic web risk to typed probability/evidence/manual-review outputs                       | Every listed source has an executable evidence/probability path or ADR-disabled status; none writes clean factual tables                |
| `R3H-05` | `R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md` | All above sources plus Layer1–5 declared production-entry envelope                                                            | Layer1–5 and data governance close real-data entry before Round4                                                                      | Round4 is blocked unless all target sources are implemented or ADR-disabled and layer/evidence gates pass                               |

**R3H-04 追溯注记（`web_search`）：** 真搜索 API **故意延后**；Execute 交付为 **mock stub** `READY_WITH_EVIDENCE`（Grill-me Q4）。R3H-05 须记 `release limitation`，不得将 mock-only 误判为真网搜索能力。见 `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0.1 **WEB-SEARCH-LIVE**。

**R3H-03 追溯注记（交易日历）：** **CN G2/G17 已闭合** @ Grill-me Q12（`cn_trading_calendar`）；**美股日历未在本卡** → 路线图 §5.0.1 **CAL-US** → R3H-05。

**R3H-01/02 追溯注记：** **CLOSED** @ 2026-06-28；G10/G14（FRED）已闭合；R3H-02 五源 READY，**US 日历** → R3H-05 **CAL-US**。Trellis：`06-28-round3h-r3h01-official-macro` · `06-28-round3h-r3h02-market-data`。

**R3H-05 当前入口：** 须对照路线图 §5.0.1 与 `R3H_05_*.md` §3.1 闭合全部开放项后方可 Round4。

---

## 2. Cross-task constraints

- `R3H-01` through `R3H-04` can branch in parallel after registry/capability freeze.
- Parallel branches must not modify the same adapter module. Shared registry/capability/route/test catalog changes must go through coordinator review.
- `R3H-05` must run last and must not implement missing adapters; it can only pass, block, or require ADR scope narrowing.
- No task may mark a source READY without adapter + auth/license + ResourceGuard + route + replay evidence.
- No task may close Round3 by only adding registry notes.

---

## 3. Shared files

Changes to these files require coordinator review:

```text
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/datasource_service_contract.yaml
specs/verification/contract_coverage.yaml
docs/modules/data_sources.md
docs/modules/source_route_plan.md
tests/test_catalog.yaml
```

---

## 4. Batch-level acceptance

Batch 3H is complete only if:

1. Every target source has one of two final statuses: `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`.
2. DataSourceService / SourceRoutePlanner / provider ports have moved beyond facade-only for every source that remains in scope.
3. Vendor adapter/provider fetch ports reach at least `R5_LIMITED_PRODUCTION_ENTRY` for the declared selected scope, or the source is ADR-disabled.
4. Layer1–5 have real-data/evidence paths for the declared production-entry envelope.
5. Newly enabled sources have replay/sandbox evidence and bounded production-entry evidence where approved.
6. All not-enabled sources remain `DISABLED_SOURCE` with explicit route reasons and release limitations.
7. Round4 can consume real source/readiness/evidence APIs rather than only proposed-disabled metadata.
