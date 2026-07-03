# ADR-034: M-DATA-03 Tier A Live Acceptance in Isolated Sandbox

- **Status:** Accepted (Plan freeze M-DATA-03)
- **Date:** 2026-07-02
- **Context:** Wave 4 DCP-05 delivered replay-primary e2e for 11 Tier A sources. Roadmap v2 requires **live network** acceptance before PASS. Module rating must not claim R4 while tests are mock-only.

## Decision

1. **Acceptance environment:** All M-DATA-03 live runs use a dedicated `DATA_ROOT` (under `.audit-sandbox/m-data-03/` or equivalent). **Canonical main DB paths are forbidden** in live acceptance tests and `tier_a_live_acceptance.py`.
2. **Env gate:** Live fetch requires `QMD_ALLOW_LIVE_FETCH=1` (ADR-027). Tests without opt-in must skip or fail-closed, never silently use mock while claiming live.
3. **Dual-track tests:** Default `uv run pytest -q` runs replay/mock paths (skipped network). Live proof uses `@pytest.mark.network` and/or `scripts/tier_a_live_acceptance.py`.
4. **Per-source AC:** Each of 11 sources must demonstrate: live sync → clean upsert → inspect/health non-blocker in isolated DB, with idempotent second run.
5. **No new DDL:** Migration 015 (ADR-028) remains SSOT; schema gaps defer to Batch6.
6. **Reference adoption:** 借鉴 L1/L2/L3 **仅** `参考项目/**`（见下）；QMD 仓内代码标 **直接复用**，禁止标 L 梯。
   - **L1** 直接拷贝外部源码 → 本票 **无**
   - **L2** 拷贝后 **必须** 改写（唯一：`digital-oracle/bis.py` 窗参数 → 仓内 `bis_incremental_*`）
   - **L3** 禁止拷贝，仅概念/架构（OpenBB 三阶段、EasyXT 反例等）

## Alternatives Considered

| Alternative                            | Rejected because                            |
| -------------------------------------- | ------------------------------------------- |
| "3 live + 8 replay SLA" as PASS        | Roadmap §3.1 explicitly forbidden           |
| Live tests against main `data/duckdb/` | Violates MAIN-DB-GATE / user isolation rule |
| Delete replay tests                    | Breaks keyless CI and fast PR feedback      |
| Separate Trellis ticket per source     | Violates v2 one-module-one-ticket rule      |

## Consequences

- New: `scripts/tier_a_live_acceptance.py`, `tests/test_tier_a_live_harness.py`, live variants in 11 e2e modules
- MCR: C3, D1, E1, E2, F0, B2 may move to R4 when live evidence exists
- Blocks M-G1-03 until macro/market clean inputs are live-verified

## Binding slices

S00-INFRA · S-LIVE-\* (all) · S-ACCEPT

## Plan R2 Amendment（2026-07-03）

Supersedes R1 acceptance semantics for Execute close-out. **SSOT:** `research/plan-revision-r2.md` §2 · `specs/contracts/live_tier_a_evidence_v1.yaml`.

| R2 binding    | Requirement                                                                                                           |
| ------------- | --------------------------------------------------------------------------------------------------------------------- |
| S-R2-EVIDENCE | `live_tier_a_evidence_v1` manifest per source                                                                         |
| S-R2-F0       | Four profiles: `market_bar_p0`, `layer1_observation_p0`, `disclosure_p0`, `crypto_derivative_p0`; **no SKIP as pass** |
| S-R2-B2       | `DataQualityValidator.validate_table` main path per `source_bindings`                                                 |
| S-R2-DISPATCH | Deduped live gold path; mootdx in `platform_source_matrix.yaml`                                                       |
| S-R2-ACCEPT   | E2 `DbInspector.inspect()` non-FAIL; unified `--report` JSON; 11/11 live                                              |
| S-R2-CI       | nightly `--quick` + `workflow_dispatch` + failure artifacts                                                           |

R1 slices remain **baseline delivered**; R2 slices are mandatory for module R4 honest close.
