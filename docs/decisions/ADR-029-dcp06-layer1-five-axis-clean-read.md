# ADR-029: DCP-06 Layer1 five-axis clean read bindings

**Status:** Accepted (Plan freeze)  
**Date:** 2026-07-02  
**Context:** R3-DCP-05 closed Tier A incremental clean writes. DCP-06 must prove G12 five-axis PASS using **Tier A clean** inputs, not `staged_fixture_only`. Layer1 ingestion bridge (018A/Batch 2.5) still defaults to staged micro-fetch for `ENV-E1-DGS10`.

## Decision

1. Add a **QMD-owned clean read path** (`Layer1CleanObservationReader` or equivalent in `backend/app/layer1_axes/`) that loads P0 anchor observations from:
   - `axis_observation` for macro/COT series (fred, cftc_cot domains per ADR-028)
   - `security_bar_1d` for bar-derived liquidity proxy (alpha_vantage canonical domain)
2. **P0 anchor per axis** (one pytest-green vertical per axis minimum):

| axis_id       | indicator_id                 | clean_table      | tier_a_source | notes                                           |
| ------------- | ---------------------------- | ---------------- | ------------- | ----------------------------------------------- |
| ENVIRONMENT   | ENV-E1-DGS10                 | axis_observation | fred          | series DGS10                                    |
| CREDIT_STRESS | CRD.CS1.BAA10Y               | axis_observation | fred          | series BAA10Y                                   |
| RISK_APPETITE | RA.R1.VIXCLS_30D_IMPLIED_VOL | axis_observation | fred          | series VIXCLS                                   |
| LIQUIDITY     | LIQ.B-I1.AMIHUD_ILLIQ        | security_bar_1d  | alpha_vantage | SPY symbol; **ponytail** vs tiingo spec primary |
| SENTIMENT     | SEN-S1-COT_LF_NET            | axis_observation | cftc_cot      | cot_positioning domain                          |

3. **Liquidity ponytail:** Spec primary is `tiingo_eod_*` (not Tier A). DCP-06 uses Amihud from `security_bar_1d` as bounded proxy. Upgrade path: tiingo/FMP port + validation when registered (Batch 6 or later wave).
4. **No new migration.** Watermark/seed uses replay fixtures aligned with DCP-05 e2e patterns (`tmp_path` isolated DB).
5. **ACC-LAYER-E2E-LIVE-001:** DCP-06 closes L1 five-axis + non-fixture layer smoke; L3–L5 full chain remains **阶段外置** to DCP-07/08/10 + `R3H-05-GATE`.

## Alternatives considered

- **Staged fixture for liquidity/sentiment only:** Rejected — violates §3.5.1「非 staged fixture」PASS 语义。
- **Live fetch inside Layer1 ingestion:** Rejected — data plane stays DCP-05; Layer1 reads clean only.
- **Implement all YAML indicators:** Rejected — ponytail P0 anchors; full catalog is Batch 6+.

## Consequences

- Execute extends `layer1_axes` read/compute paths; impact LOW on `Layer1ObservationIngestionService` (parallel path, not replace staged bridge).
- K1 whitelist `readiness` may move P0 rows from `sandbox_candidate` → `clean_replay_proven` (not `production-live ready`).
- `B2.5-O-05` remains open; DCP-06 must not claim FRED live primary closure.
