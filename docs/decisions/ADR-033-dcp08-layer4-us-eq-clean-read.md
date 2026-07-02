# ADR-033: DCP-08 Layer4 US_EQ Tier A Clean Read

**Status:** Accepted (Plan freeze 2026-07-02)  
**Date:** 2026-07-02  
**Context:** R3-DCP-08 · Wave 4 G4 · `.trellis/tasks/07-02-wave4-r3-dcp-08-layer4/`  
**Numbering:** ADR-030/031 reserved on `master` for R3-DCP-09/10; ADR-032 taken by R3-DCP-07; DCP-08 takes ADR-033.

## Context

Layer4 (022) ships `MarketStructureBuilder` with **staged fixture only** (`source_mode=staged_fixture_only`). Wave 4 requires one P0 `market_id` to read from **Tier A clean** + real trading calendar. R3H-07 delivers `us_trading_calendar` SSOT already wired for `US_EQ` non-trading rejection. DCP-05 delivers `us_equity_daily_bar` → `security_bar_1d` clean write path.

Parallel registry debt:

- `ACC-MOOTDX-DRYRUN-ROUTE-001` — dry-run JSON `selected_source_id` ≠ `--source-id mootdx`
- `ACC-EASTMONEY-TAXONOMY-001` — product path / taxonomy notes (does **not** close `R3-B2.75-REQ2-EM`)

## Decision

1. **P0 `market_id` = `US_EQ`** for the Layer4 vertical slice (not `CN_A` in this ticket).
2. Add `source_mode="tier_a_clean"` to `MarketStructureBuilder` alongside existing staged path; **do not** remove staged manifest gate for 022 tests.
3. Implement `USEquityCleanMarketAdapter` reading `security_bar_1d` + `us_trading_calendar`; ponytail breadth aggregation (advancers/decliners/total_amount/breadth_label only).
4. **No new DB migration** — read-only aggregation; snapshot remains in-memory / test-asserted in e2e.
5. **Mootdx registry reconcile (dual-primary semantics):**
   - Default domain primary for `cn_equity_daily_bar` remains **baostock**.
   - Explicit `qmd data sync --source-id mootdx` uses **mootdx as effective primary**; dry-run JSON must emit `selected_source_id: mootdx`.
   - Registry: mootdx `validation_only: false` when documented for explicit sync; remove runtime `object.__setattr__` hack after registry apply.
6. **Eastmoney:** extend registry/capabilities notes + ops SSOT only; **do not** enable hist live or close REQ2-EM.

## Alternatives Considered

| Alternative | Rejected because |
|-------------|------------------|
| CN_A as P0 | Card §4 architecture anchors R3H-07 US calendar; CN calendar + breadth adds cross-domain scope; registry slices orthogonal |
| Replace baostock with mootdx globally | Breaks DCP-05 product bar path and operator expectations |
| Write market_breadth to DB in this ticket | Scope creep; 022 lineage in-memory sufficient for AC |
| Copy breadth logic from 参考项目 | No safe L1 module found; L3 greenfield |

## Consequences

- **Positive:** Closes L4 subset of ACC-LAYER-E2E-LIVE-001; leverages R3H-07 + DCP-05 investments; staged 022 AC preserved.
- **Negative:** CN_A Layer4 clean slice deferred; index/sector snapshots still future work.
- **Follow-up:** CN_A vertical slice Wave 5+; REQ2-EM remains Batch 6.

## Bindings

- S08-E2E · S08-REG-MOOTDX · S08-REG-EM · `research/registry_proposed_delta.yaml`
