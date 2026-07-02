# ACC-LAYER-E2E-LIVE-001 — Layer4 US_EQ subset evidence

> **Task:** R3-DCP-08 S08-L4-E2E-LEDGER · **Date:** 2026-07-02

## L4 subset scope

| market_id | source_mode | clean inputs | snapshot |
|-----------|-------------|--------------|----------|
| US_EQ | tier_a_clean | security_bar_1d + us_trading_calendar SSOT | market_breadth_snapshot |

## Evidence chain

1. **Seed:** `tests/layer4_clean_e2e_support.py` — sandbox DuckDB + US_EQ instrument_registry + alpha_vantage replay bars
2. **Read:** `backend/app/layer4_markets/clean_read.py` — breadth aggregation + calendar row
3. **Build:** `MarketStructureBuilder.build(source_mode="tier_a_clean", clean_con=...)`
4. **Assert:** `tests/test_layer4_us_equity_clean_e2e.py` — advancers/decliners; no `staged_fixture` in source fields; lineage cites `security_bar_1d`

## Verification

```bash
uv run pytest tests/test_layer4_us_equity_clean_e2e.py -q
uv run pytest tests/test_layer4_clean_read.py -q
```

## Ledger status

- [x] L4 US_EQ clean → snapshot → lineage (pytest green)
- [ ] Full L1–L5 live chain — out of DCP-08 scope
