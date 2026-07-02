# Execute reference read evidence — Infra (`feature/m-data-03-infra`)

> Per `parallel-dispatch-protocol.md` §3 · RED before harness code · 2026-07-02

## Agent scope

| Field    | Value                       |
| -------- | --------------------------- |
| Agent    | Execute Agent 1 (Infra)     |
| Slices   | S00-ELIGIBILITY · S00-INFRA |
| 借鉴等级 | L3 + forbidden              |

## L3 — OpenBB fetcher three-phase pipeline (concept only)

**Read:** `参考项目/OpenBB/.../fetcher.py` L36–85 (via `reference-adoption-m-data-03.md` §2.1)

| OpenBB stage      | QMD harness alignment                                     |
| ----------------- | --------------------------------------------------------- |
| `transform_query` | watermark → incremental window (ops runners; not harness) |
| `extract_data`    | `*_port.py` live HTTP with `gate_live_fetch_port`         |
| `transform_data`  | normalizer → staging → clean                              |

**Harness action:** No OpenBB code copy. Negative tests assert live ports call `gate_live_fetch_port` / `ProductLiveGateError`, not mock substitution.

## forbidden — EasyXT silent fallback

**Read:** `参考项目/EasyXT/.../unified_data_interface.py` L172–244 (via `reference-adoption-m-data-03.md` §2.3)

**Forbidden pattern:** DuckDB miss → online silent source swap without operator opt-in.

**Harness action:** `test_tier_a_live_harness.py` asserts `create_fred_fetch_port(use_mock=False)` without `QMD_ALLOW_LIVE_FETCH` raises `ProductLiveGateError` (`LIVE_FETCH_REJECTED`), never returns `FredMockFetchPort`.

## ADR-034 — isolated sandbox acceptance

**Read:** `docs/decisions/ADR-034-m-data-03-tier-a-live-acceptance.md`

| Decision                                               | Harness implementation                                               |
| ------------------------------------------------------ | -------------------------------------------------------------------- |
| Dedicated `DATA_ROOT` under `.audit-sandbox/m-data-03` | `assert_isolated_live_data_root` + `isolated_live_data_root` fixture |
| Canonical main DB forbidden                            | `is_canonical_main_db_path` / `is_canonical_main_data_root`          |
| `QMD_ALLOW_LIVE_FETCH` required                        | `validate_live_acceptance_env` → CLI exit 2                          |
| Dual-track: default pytest skips network               | Reuse `conftest.py` `--run-network` + `@pytest.mark.network`         |

## Reused in-repo patterns (direct reuse, not 借鉴梯)

| Pattern                 | Path                                                     |
| ----------------------- | -------------------------------------------------------- |
| Isolated sandbox layout | `scripts/wave3_isolated_production_acceptance.py`        |
| Product live gate       | `backend/app/datasources/product_live_gate.py`           |
| Live port factory       | `backend/app/datasources/product_live_ports.py`          |
| Canonical DB rejection  | `limited_production_entry._assert_production_db_allowed` |
| Tier A source list      | `live_tier_router.TIER_A_SOURCES`                        |

## S00-ELIGIBILITY doc review

`research/tier-a-live-eligibility.md`: 11/11 须真网 · KEY 槽位 (`FRED_API_KEY`, `ALPHA_VANTAGE_API_KEY`) · 无 ADR 例外 — **AC satisfied, no doc edit**.
