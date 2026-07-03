# R3-DCP-08 Plan Spec

> Phase 5a' · spec-driven-development

## Objective

Deliver Layer4 **US_EQ** vertical slice: Tier A clean bars + US trading calendar → market breadth snapshot with lineage; close registry hygiene items for mootdx/eastmoney without closing REQ2-EM.

## Tech Stack

Python 3.12 · DuckDB clean tables · pytest · existing `MarketStructureBuilder` / `Layer4LineageBuilder` · `us_trading_calendar` SSOT

## Commands

```bash
uv run pytest tests/test_layer4_us_equity_clean_e2e.py -q
uv run pytest tests/test_layer4_market_structure.py -q
uv run pytest tests/test_qmd_data_sync_tier_a_router.py -k mootdx -q
uv run pytest -q
uv run python scripts/loop_maintain.py
```

## Project Structure

```text
backend/app/layer4_markets/
  clean_read.py          # NEW — bar → breadth
  market_structure.py    # EXT — USEquityCleanMarketAdapter, tier_a_clean
tests/
  layer4_clean_e2e_support.py
  test_layer4_clean_read.py
  test_layer4_us_equity_clean_e2e.py
specs/datasource_registry/
  (proposed delta — coordinator merge)
```

## Code Style

ponytail · karpathy-guidelines · 五字段 docstring on every `test_*`

## Testing Strategy

TDD RED→GREEN per slice; staged 022 tests must stay green; new e2e proves `source` ≠ `staged_fixture`

## Boundaries

**Always:** WriteManager for any DB write; sandbox DATA_ROOT for replay  
**Never:** Eastmoney hist live; new migration without ADR; delete staged path; CN_A full slice in this ticket

## Success Criteria

- [ ] `US_EQ` clean e2e green
- [ ] ACC-MOOTDX dry-run aligned
- [ ] ACC-EASTMONEY notes complete (REQ2-EM still open)
- [ ] ACC-LAYER-E2E-LIVE-001 L4 subset documented
- [ ] `validate-plan-freeze` exit 0

## ASSUMPTIONS

- P0 market_id = **US_EQ** (Plan frozen)
- alpha_vantage replay fixtures sufficient for US bar seed in sandbox
- No schema change required for breadth aggregation (read-only from existing `security_bar_1d`)
