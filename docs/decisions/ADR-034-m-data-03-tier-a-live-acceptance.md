# ADR-034: M-DATA-03 Tier A Live Acceptance in Isolated Sandbox

- **Status:** Accepted (Plan freeze M-DATA-03)
- **Date:** 2026-07-02
- **Context:** Wave 4 DCP-05 delivered replay-primary e2e for 11 Tier A sources. Roadmap v2 requires **live network** acceptance before PASS. Module rating must not claim **R4** while tests are mock-only（R4 = 声明 scope 能力真落地，见 MCR §1.2）.

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
- MCR: C3, D1, E1, E2, F0, B2 may move to **R4** when live evidence proves **declared-scope capability landed**（`MODULE_COMPLETION_RATING.md` §1.2）
- Blocks M-G1-03 until macro/market clean inputs are live-verified

## Acceptance environment boundary（2026-07-03 · MCR 对齐 @ 2026-07-04）

**本 ADR 验收通过的含义**（与 `MODULE_COMPLETION_RATING.md` §1.2 **R4/R5/R6** 一致）：

1. **环境（验收边界）：** 仅在用户指定的隔离 `DATA_ROOT`（典型路径 `.audit-sandbox/m-data-03/*`）内执行；**禁止**指向 canonical 生产 DuckDB。隔离库是 **R4 能力证明环境**，不是把 R4 定义为「仅彩排、不算落地」。
2. **评级 — R4：** 相关模块（C3, D1, E1, E2, F0, B2 等）可标 **`R4_SANDBOX_REAL_DATA_OR_REHEARSAL`** — 规划语义 = 声明 scope 内 **能力/功能/机制真实落地**（真网 sync→clean→inspect 等同库真链），**不是** staged/mock 冒充。
3. **评级 — 非 R4 即 R5/R6：** 本 ADR **不**授予 **R5**（运维、监控、使用/运行手册收尾）或 **R6**（完整商业可发布 / Batch05 manifest）。**禁止**将 M-DATA-03 关账写成 R5/R6。
4. **幂等：** 同一 sandbox 连续 `--report` 应 exit 0；行数允许合法增量追加（如 bis 月频第二行），不得 duplicate 炸库。
5. **Tier B/C：** 并行契约轨同样在隔离 `DATA_ROOT` 验收；`FAIL_EXTERNAL`+ADR 表示外部/产品边界，非 pipeline 假绿。

**明确否定的表述：**

- 「M-DATA-03 完成 = 可以写生产主库」→ **否**（属 **R5/R6**，非本 ADR）
- 「R4 = sandbox only / 仅彩排、能力未落地」→ **否**（与 MCR §1.2 冲突；隔离库可证明 **R4**）

## Tier B FAIL_EXTERNAL bindings（2026-07-04 · 网络路径二）

**证据 SSOT：** `.trellis/tasks/archive/2026-07/m-data-03-tier-a-live/research/archive/non-plan/execute/tier-b-network-path2-evidence.md`

**Amendment @ 2026-07-04（用户确认 · 当前阶段）：** Tier B **沙箱关账**口径 — **10/10 源均有验收结论**（6 `PASS` + 4 `FAIL_EXTERNAL`+本 ADR）。允许写「**Tier B 沙箱验收完成**」；**禁止**写「10/10 真网 fetch SUCCESS」。后续若重构 validation_fetch / CN hist 策略，须 **修订本 ADR**（非口头 defer）。

| source_id      | 路径                 | 客观原因                                                                                          | 状态                                                           |
| -------------- | -------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `stooq`        | **路径二（已接受）** | Stooq CSV 端点返回 HTML + JavaScript PoW 反爬；直连/系统代理/7897 均不可绕过                      | `FAIL_EXTERNAL` + 本 ADR · 台账 `M-DATA-03-STOOQ-EXTERNAL-001` |
| `akshare`      | **路径二（已接受）** | `push2his.eastmoney.com` API 间歇 TLS 断开；Clash DIRECT + 代码 bypass 已就位，非 7897 误路由主因 | `FAIL_EXTERNAL` + 本 ADR · 台账 `M-DATA-03-TIERB-CN-HIST-001`  |
| `eastmoney`    | **路径二（已接受）** | 与 akshare 同 `stock_zh_a_hist` / push2his 链                                                     | 同上                                                           |
| `sina_finance` | **路径二（已接受）** | 同上（含 sina；与 akshare/eastmoney 同 push2his 链）                                              | 同上                                                           |

**规则：**

1. **stooq + CN 三源（akshare / eastmoney / sina_finance）：** 允许 sandbox `tier_b_live_acceptance --report` 在 `FAIL_EXTERNAL`+`adr_ref=ADR-034` 下 exit 0；**不得**伪造 CSV、mock HTML 或静默 PASS 替代客观外因。
2. **诚实口径：** CLI/report exit 0 **不等于** 该源真网 fetch `SUCCESS`；`FAIL_EXTERNAL` 行须保留在报告 JSON（`disposition=fail` + `failure_class=FAIL_EXTERNAL`）。
3. **升级路径（后续阶段）：** 替代 CSV 源、baostock hist 链切换、或 nightly 非封锁 IP 连续 PASS — 实现后 **修订本 ADR** 并更新 MCR/台账。

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

R1 slices remain **baseline delivered**; R2 slices are mandatory for honest **R4** close（能力落地；R5/R6 → Batch05）.
