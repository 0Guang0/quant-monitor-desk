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

## Sandbox boundary（2026-07-03 grill 关账增补）

**本 ADR 验收通过的含义：**

1. **环境：** 仅在用户指定的隔离 `DATA_ROOT`（典型路径 `.audit-sandbox/m-data-03/*`）内执行；**禁止**指向 canonical 生产 DuckDB。
2. **评级：** MODULE_COMPLETION_RATING 中相关模块可标 **R4_SANDBOX_REAL_DATA_OR_REHEARSAL** — 表示「沙箱真网彩排过关」，**不是** `R5_LIMITED_PRODUCTION_ENTRY` 或主库写就绪。
3. **幂等：** 同一 sandbox 连续 `--report` 应 exit 0；行数允许合法增量追加（如 bis 月频第二行），不得 duplicate 炸库。
4. **CI：** nightly/quick 与 `workflow_dispatch` 全量跑使用相同 secrets gate；本地过关不替代 GitHub 实跑日志（见 execute 证据 AC-4）。
5. **Tier B/C：** 并行契约轨同样仅 sandbox scope；`FAIL_EXTERNAL`+ADR 表示产品/外部边界，非 pipeline 假绿。

**明确否定的表述：**「M-DATA-03 完成 = 可以写生产主库」。

## Tier B FAIL_EXTERNAL bindings（2026-07-04 · 网络路径二）

**证据 SSOT：** `.trellis/tasks/m-data-03-tier-a-live/research/archive/non-plan/execute/tier-b-network-path2-evidence.md`

| source_id      | 路径                 | 客观原因                                                                                          | 状态                                                           |
| -------------- | -------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `stooq`        | **路径二（已接受）** | Stooq CSV 端点返回 HTML + JavaScript PoW 反爬；直连/系统代理/7897 均不可绕过                      | `FAIL_EXTERNAL` + 本 ADR · 台账 `M-DATA-03-STOOQ-EXTERNAL-001` |
| `akshare`      | **条件路径二**       | `push2his.eastmoney.com` API 间歇 TLS 断开；Clash DIRECT + 代码 bypass 已就位，非 7897 误路由主因 | 缺口开放 · `M-DATA-03-TIERB-CN-HIST-001`                       |
| `eastmoney`    | **条件路径二**       | 与 akshare 同 `stock_zh_a_hist` / push2his 链                                                     | 同上                                                           |
| `sina_finance` | **条件路径二**       | 同上                                                                                              | 同上                                                           |

**规则：**

1. **stooq：** 允许 sandbox `tier_b_live_acceptance --report` 在 `FAIL_EXTERNAL`+`adr_ref=ADR-034` 下 exit 0；**不得**伪造 CSV 或 mock 过关。
2. **CN 三源：** 在完成路径一剩余动作（关 TUN 复测、交易时段、换网、或改 baostock hist 链）前，**不得**与 stooq 同级宣称「已接受路径二」；对外不得写 Tier B「10/10 真网 PASS」。
3. CLI exit 0 与 `disposition=pass` 不等价；`FAIL_EXTERNAL` 行须保留在报告 JSON。

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
