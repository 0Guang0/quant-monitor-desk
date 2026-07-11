# Model Input Whitelist — specs/model_inputs

Batch 01 Track A (`B01-WL`) machine-readable **whitelist-driven** model input catalog.

## Files

| File                                 | Layer  | Purpose                                                           |
| ------------------------------------ | ------ | ----------------------------------------------------------------- |
| `layer1_source_whitelist.yaml`       | Layer1 | P0 FRED macro series (`sandbox_candidate`); deferred/P2 remainder |
| `layer2_source_whitelist.yaml`       | Layer2 | Cross-asset staged/fixture assets vs sandbox candidates           |
| `layer3_anchor_source_plan.yaml`     | Layer3 | Industry-chain anchor → `source_id` / `operation`                 |
| `layer4_market_source_plan.yaml`     | Layer4 | Market structure inputs (`CN_A` first-batch)                      |
| `layer5_instrument_source_plan.yaml` | Layer5 | Instrument bar / metadata / validation-only evidence              |

Machine-readable rows live under the YAML files listed below.

## Posture (Batch 01)

- **Allowed:** `sandbox_candidate`, `staged_only`, `fixture_only`, `validation_only`, `deferred`
- **Forbidden claims:** `production-live ready`, full-market / full-history default paths
- **No live fetch** from this package — docs/spec only
- **Registry:** read `source_registry.yaml` for role alignment; WL does **not** modify registry rows

## Row schema

Each `rows[]` entry follows task card `R3D_model_input_whitelist.md` §6 (`input_id`, `layer`, `business_purpose`, `data_domain`, `source_id`, `operation`, `role`, `readiness`, caps, authorization, `forbidden_claims`, `closure_test`, `notes`).

## Registry alignment (read-only)

WL **does not** modify `source_registry.yaml`. Whitelist `source_id` values are planning labels aligned to registry where rows exist.

| `source_id`                                  | Registry status                      | Closure owner                            |
| -------------------------------------------- | ------------------------------------ | ---------------------------------------- |
| `baostock`, `cninfo`, `akshare`, `tdx_pytdx` | Present in registry                  | —                                        |
| `fred`                                       | **Not registered** (master baseline) | **B01-FRED** — registry row + live pilot |
| `staged_fixture`, `none`                     | N/A (fixture/deferred)               | —                                        |

`fred` rows in this package use `sandbox_candidate` + `requires_user_authorization: true` as **planning posture only** until B01-FRED registers the source and closes live pilot gates.

## Runtime live auth gate (CLOSED-deferred)

Hardening §3 requires user authorization YAML before any `fred` or `tdx_pytdx` live fetch. **WL scope is docs/spec only** — no runtime `FAIL_AUTH` / `BLOCKED_AUTH` path in this branch.

| Concern                            | Owner card                                                  | Closure test                                            |
| ---------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------- |
| FRED live fetch without auth       | `B01-FRED` (`feature/round3-fred-authorized-sandbox-pilot`) | `tests/test_fred_staged_semantics.py` + FRED pilot gate |
| TDX live manual probe without auth | `B01-TDX` / `018C`                                          | `tests/test_tdx_live_manual_probe_authorization.py`     |

WL supplies spec-level `requires_user_authorization` + negative role checks in
`phase-scripts/check_model_input_whitelist.py`; runtime loader smoke remains in
`tests/test_model_input_whitelist.py`. Runtime enforcement remains downstream.

- `B01-FRED` — Layer1 P0 macro + L5 FRED macro daily
- `B01-SP3` — staged pilot v3 whitelist scope
- `B01-DH2` — data health v2 profile inputs

## Verification

```bash
uv run python phase-scripts/check_model_input_whitelist.py --strict
uv run pytest tests/test_model_input_whitelist.py -q
```
