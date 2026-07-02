# ADR-032: DCP-07 Layer2 P0 cross-asset clean read (L2-VIX / VIXCLS)

**Status:** Accepted  
**Date:** 2026-07-02  
**Context:** R3-DCP-07 requires one P0 cross-asset sensor to read Tier A clean (not staged_fixture_only). Layer2 registry staged fixture lists multiple assets; Wave 4 scope is a single vertical slice. **Numbering:** ADR-030/031 reserved on `master` for R3-DCP-09/10; DCP-07 takes ADR-032.

## Decision

1. **P0 anchor asset:** `L2-VIX` (Volatility group, `instrument_id` label `FRED:VIXCLS`).
2. **Clean SSOT:** `axis_observation` rows with `indicator_id = 'VIXCLS'` (fred / `macro_series` domain from DCP-05).
3. **Read path:** new `Layer2CleanObservationReader` maps clean macro rows → `CrossAssetObservation` list; `CrossAssetSnapshotBuilder` + `Layer2LineageBuilder` unchanged in contract semantics.
4. **Replay default:** tmp_path isolated DB seeded from fred incremental e2e pattern (`test_fred_macro_incremental_e2e.py`); no live FRED primary (`B2.5-O-05` remains open).
5. **Registry mode:** extend loader to accept `production_clean_replay` (or equivalent) for P0 asset only; keep staged_fixture path for other registry rows in tests.
6. **Double-count:** `L2-VIX` remains `is_axis_input=true`, `display_only=true` per registry fixture — Layer2 snapshot is旁证，不回写 Layer1.

## Alternatives Considered

| Alternative | Rejected because |
|-------------|------------------|
| L2-HYG via `security_bar_1d` | Valid but weaker DCP-05/06 replay precedent; ETF bar seed not yet wired to Layer2 registry |
| L2-COPPER futures | futures roll + commodity bar mapping adds scope beyond single-sensor竖切 |
| Live network fetch in e2e | Violates replay-first policy; conflicts with `B2.5-O-05` |

## Consequences

- Execute adds `tests/test_layer2_vix_clean_e2e.py` (or equivalent) proving non-fixture clean read.
- `ACC-LAYER-E2E-LIVE-001` **L2 subset** closes in S02; L3–L5 remain 阶段外置 to DCP-08/10 + `R3H-05-GATE`.
- No new migration DDL (R3H-06 + 015 frozen).
