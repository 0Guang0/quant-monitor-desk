# Model Input Readiness Matrix

> Batch 01 (`B01-WL`) · Round 3D.2 · **docs/spec only** — no production-live claim.

This matrix summarizes what may enter **raw/staging sandbox pilot**, what remains **fixture/staged only**, and what is **deferred**. Machine-readable rows live under `specs/model_inputs/`.

## Legend

| `readiness` | Meaning |
| --- | --- |
| `sandbox_candidate` | Eligible for authorized sandbox/raw pilot with caps — **not** production-live |
| `staged_only` / `staged_fixture` | Staged bundle only; no default live fetch |
| `fixture_only` | Display or contract fixture; not a live model input |
| `validation_only` | Cross-check source (e.g. akshare, tdx_pytdx) — never Primary |
| `deferred` | Out of first-batch scope; requires future card + closure_test |

## Layer1 — Macro / risk axes

| Input | Series | Source | Role | Readiness | Next gate |
| --- | --- | --- | --- | --- | --- |
| L1-ENV-DGS10 | DGS10 | fred | primary_candidate | sandbox_candidate | raw_staging_pilot (auth required) |
| L1-ENV-T10Y3M | T10Y3M | fred | primary_candidate | sandbox_candidate | raw_staging_pilot (auth required) |
| L1-RA-VIXCLS | VIXCLS | fred | primary_candidate | sandbox_candidate | raw_staging_pilot (auth required) |
| L1-RA-SP500 | SP500 | fred | primary_candidate | sandbox_candidate | raw_staging_pilot (auth required) |
| L1-ENV-DFII10 | DFII10 | fred | primary_candidate | sandbox_candidate | raw_staging_pilot (auth required) |
| L1-MACRO-SUPP-VALIDATION | staged_sample | akshare | validation_only | sandbox_candidate | none |
| Other ENV/RA indicators | various | fred | deferred | deferred | none |

**Notes:** `macro_supplementary` (akshare) is **validation_only** and cannot substitute FRED P0 primary paths (`B2.5-O-05`). Layer2 VIX/HYG remain `fixture_only` display assets.

## Layer2 — Cross-asset sensor

| Asset | Readiness | Notes |
| --- | --- | --- |
| L2-VIX, L2-HYG | fixture_only | display_only; Layer1 axis guard |
| L2-COPPER, L2-HG-MAIN | staged_fixture | staged pilot v3 candidate shape |
| L2-NO-CHANNEL | deferred | no accepted channel |

## Layer3 — Industry chain anchors

| Anchor | Readiness | Notes |
| --- | --- | --- |
| MSFT, OPENAI | staged_only | `layer3_staged_bundle` fixture |
| NVDA, TSMC (planned) | deferred | missing live source_keys |

## Layer4 — Market structure

| Market | Inputs | Readiness |
| --- | --- | --- |
| CN_A | calendar, breadth | sandbox_candidate (capped) |
| US, HK, FUT, OPTIONS | — | deferred |

## Layer5 — Instrument / evidence

| Source | Domain | Role | Readiness |
| --- | --- | --- | --- |
| baostock | cn_equity_daily_bar | primary_candidate | sandbox_candidate |
| cninfo | cn_filings / cn_announcements | primary_candidate | sandbox_candidate |
| fred | us_macro_series | primary_candidate | sandbox_candidate (auth) |
| tdx_pytdx | daily bar / index / security_list | validation_only | sandbox_candidate (auth, disabled-default) |

**No row** in Batch 01 uses `production_candidate`.

## Forbidden role transitions (hardening §8)

- `akshare` → not `primary_candidate`
- `tdx_pytdx` → not production primary; `validation_only` only
- `fred` → not `production_candidate` until FRED-only pilot closes
- `macro_supplementary` → cannot close FRED primary readiness

## Authorization

Any `fred` or `tdx_pytdx` live path requires user authorization YAML per `BATCH_01_HARDENING_RULES.md` §3. Without it: `FAIL_AUTH` / `BLOCKED_AUTH`.

## Deferred (explicit)

- Full Layer1 P2 indicators (EFFR, WRESBAL, M2SL, …)
- US/HK/FUT/OPTIONS market structure
- Layer3 anchors without staged source_keys
- Production registry closure (`AUDIT_DEFERRED` rows) — **not** in WL scope
- `fred` **source_registry.yaml** row — **B01-FRED** (WL documents whitelist only; see `specs/model_inputs/README.md` Registry alignment)

## Verification

```bash
uv run pytest tests/test_model_input_whitelist.py -q
```
