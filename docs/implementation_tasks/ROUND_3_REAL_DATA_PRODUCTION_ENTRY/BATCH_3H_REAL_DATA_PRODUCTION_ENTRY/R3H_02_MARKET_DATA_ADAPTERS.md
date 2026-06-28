# R3H-02 — Market Data Adapters

## 1. Goal

Close every cross-asset / US market / crypto market source before Round4. This is not a one-provider sample.

Required source coverage:

```text
alpha_vantage
stooq
yahoo_finance
deribit
coingecko
```

Each listed source must end as `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`.

### 1.1 Plan architecture decisions（2a brainstorm + 3 grill-me · 已内联）

| 选项                                              | 结论                                                 |
| ------------------------------------------------- | ---------------------------------------------------- |
| A. 只做 yahoo 3G fixture 迁移，其余留 proposed    | **否决** — Batch 3H hardening 五源全闭环             |
| B. 统一 `market_data`/`crypto_market` normalizer  | **采纳**                                             |
| C. yahoo 升格为 US equity primary                 | **否决** — registry validation_only 不变             |
| D. 本卡写主库验证                                 | **否决** — 路线图 §5.0                               |
| E. 本卡实现完整 TradingCalendar（G2 EasyXT 拷改） | **否决** — ponytail 自然日窗；G2 SSOT 与 R3H-03 协调 |

| 风险                                        | 缓解                                                              |
| ------------------------------------------- | ----------------------------------------------------------------- |
| registry 与 R3H-01/03/04 并行冲突           | §9.6 coordinator manifest；只改五源行                             |
| `YahooFinanceAdapter` skeleton 与 port 双轨 | §9.4 迁 `yahoo_finance_port.py`；adapter 薄 re-export 或弃用      |
| 期权链/衍生品默认全量扫描                   | ResourceGuard 硬 cap；§7 表                                       |
| G16 yahoo 仍 fixture                        | §9.4 replay 迁 `tests/fixtures/replay/market_data/yahoo_finance/` |

| grill 锁定项      | 决定                                                                                                                                                               |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 3G yahoo fixture  | **≠** READY；须 fetch port + route + evidence                                                                                                                      |
| 主库              | **禁止**写 `quant_monitor.duckdb`                                                                                                                                  |
| yahoo 角色        | **永久 validation-only**（除非书面 ADR 改 registry，本卡不做）                                                                                                     |
| alpha_vantage     | Primary 候选；`ALPHA_VANTAGE_API_KEY` + route 未授权 DISABLED                                                                                                      |
| stooq / coingecko | validation/aggregator；不得 silent primary                                                                                                                         |
| deribit           | 交易所级 crypto 衍生品；**禁止**账户/交易语义                                                                                                                      |
| 五源终态          | READY_WITH_EVIDENCE **或** ADR_DISABLED（禁止含糊 defer）                                                                                                          |
| Layer             | §9.7 L2/L4/L5 smoke only；**禁止** R3H-05                                                                                                                          |
| G2 交易日窗       | ponytail：自然日 `MAX_WINDOW_DAYS` + `window_kind: calendar_days`；**CN 完整日历 → R3H-03（Q12 已闭合）**；**US 节假日 SSOT → R3H-05**（路线图 §5.0.1 **CAL-US**） |
| 切片顺序          | 9.1 契约 → 9.2 AV → 9.3 stooq → 9.4 yahoo → 9.5 crypto → 9.6 → 9.7 → 9.8                                                                                           |

### 2.8 Plan vs Execute gates

1. **R3H-01 CLOSED** does not substitute for R3H-02; five market sources remain open until §9.2–9.5 pass.
2. **No main DB writes**; sandbox/replay/`.audit-sandbox` only.
3. **Coordinator review** before merging shared registry/capability/route files (§9.6).
4. **R3H-05 forbidden**; Layer work is §9.7 smoke only.
5. **alpha_vantage live** requires `ALPHA_VANTAGE_API_KEY`; mock/replay is test default.
6. **yahoo_finance** must remain `validation_only: true` in registry after closure.

### 1.2 ADR 收窄策略（grill-me Q8 · 已内联）

| 源              | ADR 允许？   | 说明                                                                 |
| --------------- | ------------ | -------------------------------------------------------------------- |
| `alpha_vantage` | **禁止**     | registry Primary 承诺域；须 `READY_WITH_EVIDENCE`                    |
| `deribit`       | **禁止**     | 交易所级衍生品主源候选；须 port + replay                             |
| `yahoo_finance` | **禁止升格** | 不得 ADR 改 primary；允许 **完全禁用** ADR（须 `docs/adr/` + route） |
| `stooq`         | 候选         | 仅 Execute 真受阻时；默认须 validation READY                         |
| `coingecko`     | 候选         | 仅 Execute 真受阻时；默认须 aggregator validation READY              |

书面 ADR 路径：`docs/adr/ADR-*-{source_id}-*.md` + registry `ADR_DISABLED_OUT_OF_SCOPE` + route DISABLED reason。

---

## 2. QMD files to read

```text
PROJECT_IMPLEMENTATION_ROADMAP.md
MODULE_COMPLETION_RATING.md
docs/modules/data_sources.md
docs/modules/source_route_plan.md
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/datasource_service_contract.yaml
specs/contracts/data_quality_rules.yaml
specs/contracts/resource_limits.yaml
specs/contracts/layer5_evidence_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_source_registry.py
tests/test_source_capabilities.py
tests/test_source_route_planner.py
tests/test_catalog.yaml
```

---

## 3. Reference project use

Use OpenBB provider packaging/catalog layout only as architecture reference:

```text
参考项目/OpenBB/openbb_platform/providers/
```

Use JQ2PTrade/EasyXT only for read-only loader/report constraints if this task touches frozen market datasets:

```text
参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py
参考项目/JQ2PTrade/ptrade_local/engine/report.py
参考项目/JQ2PTrade/api_mapping.json
参考项目/EasyXT/data_manager/data_integrity_checker.py
```

Forbidden:

- copying OpenBB runtime provider code;
- using JQ2PTrade order/trade/portfolio APIs;
- broad default scans;
- full option-chain scans by default;
- crypto account/trading semantics.

---

## 4. Target QMD files

Implement or update QMD-owned files such as:

```text
backend/app/datasources/fetch_ports/alpha_vantage_port.py
backend/app/datasources/fetch_ports/stooq_port.py
backend/app/datasources/fetch_ports/yahoo_finance_port.py
backend/app/datasources/fetch_ports/deribit_port.py
backend/app/datasources/fetch_ports/coingecko_port.py
backend/app/datasources/normalizers/market_data.py
backend/app/datasources/normalizers/crypto_market.py
backend/app/core/resource_guard.py
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/resource_limits.yaml
specs/verification/contract_coverage.yaml
tests/test_market_data_adapters.py
tests/test_crypto_market_adapters.py
tests/test_source_route_planner.py
tests/test_source_capabilities.py
tests/fixtures/replay/market_data/**
tests/fixtures/replay/crypto_market/**
```

Do not create a generic catch-all `market_adapter.py` that hides per-source auth, caps, and evidence rules.

### 4.1 Data flow and impact targets (Plan 1b)

```text
FetchRequest → fetch_ports/*_port.py (mock default, live opt-in)
  → market_data.py / crypto_market.py normalizer  ← SSOT
  → evidence bundle (source_fetch_id, content_hash, schema_hash, schema_version)
route_planner + capability_registry → READY / DISABLED / validation-only block
rehearsal_loader (3G yahoo bundle) → migrate reader to replay/market_data/yahoo/
Layer2 sensor / Layer4 market / Layer5 evidence ← smoke consumers only
```

**GitNexus impact before edit（Execute 每步前 `impact()`）：**

| 符号 / 模块                                       | 风险   | 触发 Step     |
| ------------------------------------------------- | ------ | ------------- |
| `YahooFinanceAdapter`                             | LOW    | 9.4           |
| `adapters/__init__.py` 注册表                     | LOW    | 9.4           |
| `DataSourceService.fetch`                         | MEDIUM | 9.2–9.5       |
| `route_planner` / `capability_registry`           | MEDIUM | 9.6           |
| `resource_guard` / `reject_over_cap`              | LOW    | 9.2–9.5       |
| `rehearsal_loader` yahoo bundle 路径              | MEDIUM | 9.4           |
| `limited_production_entry` yahoo validation op    | LOW    | 9.4           |
| `sandbox_clean_write/limited_production_entry.py` | LOW    | 9.4           |
| `staged_pilot` / `live_pilot_phase3` 源列表       | MEDIUM | 9.4, 9.8 回归 |
| `test_round3g_limited_production_clean_write`     | MEDIUM | 9.8           |

**ponytail:** shared OHLCV normalizer for equity/ETF/FX/commodity; separate `crypto_market` for deribit/coingecko instrument semantics.

### 4.2 Baseline state（Plan 1a · 开工前）

| 维度            | 当前                                                                    |
| --------------- | ----------------------------------------------------------------------- |
| `yahoo_finance` | skeleton adapter；3G fixture `r3g01/yahoo_finance`；validation_only     |
| `alpha_vantage` | registry + capabilities `proposed_disabled_source`；**无** fetch port   |
| `stooq`         | registry `validation_only`；**无** port                                 |
| `deribit`       | registry Primary candidate；capabilities proposed_disabled；**无** port |
| `coingecko`     | registry validation_only；**无** port                                   |
| normalizers     | **无** `market_data.py` / `crypto_market.py`                            |
| replay fixtures | **无** `tests/fixtures/replay/market_data/**`                           |

**3H 目标流：** mock/replay-first fetch port → normalizer evidence v1 → route READY + negative tests → registry 五源终态。

### 4.3 GitNexus Execute boot（Plan 1b）

- 改码前：`impact()` 锚定 `YahooFinanceAdapter`、`DataSourceService.fetch`、`route_planner`、`resource_guard`、`rehearsal_loader` yahoo paths。
- **风险预判：** yahoo 3G fixture 迁移 + 五 port 新增 = **MEDIUM**（触及 route/capabilities/staged pilot 测）；不触及 R3H-05 全层路径。

---

## 5. Required implementation per source

For each source, implement:

1. adapter/fetch port with explicit source_id;
2. auth/license/rate-limit decision;
3. ResourceGuard caps for symbol count, window, rows, option-chain breadth, and crypto instrument count;
4. route planner READY test and DISABLED/unauthorized/rate-limited negative tests;
5. replay fixture or sandbox sample;
6. fetch_log/content_hash/schema_hash/source_fetch_id evidence;
7. data health checks for OHLCV/date/freshness/field completeness;
8. Layer2/Layer4/Layer5 binding where this source feeds market data or evidence.

Minimum domain expectations:

| Source          | Domains                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------- |
| `alpha_vantage` | US equity daily bar, ETF daily bar, US option chain, FX/commodity/macro/crypto references |
| `stooq`         | global daily bar, FX daily bar, commodity daily bar                                       |
| `yahoo_finance` | validation-only US equity/ETF/option-chain posture unless ADR changes scope               |
| `deribit`       | crypto derivatives, futures term structure, options surface                               |
| `coingecko`     | crypto spot market and asset reference as aggregator/validation                           |

### 5.1 Contract schema and spec→test map（Plan 2b · 已内联）

**权威契约（原文仍在 §3 manifest）：** `source_capability_contract.yaml`, `source_route_contract.yaml`, `datasource_service_contract.yaml`, `data_quality_rules.yaml`, `layer5_evidence_contract.yaml`, `reference_adoption_guardrails.yaml`, `resource_limits.yaml`.

**本任务新增契约面：**

1. `market_data_evidence_v1` — `market_data.py`；OHLCV 字段对齐 `source_capabilities` daily bar operations。
2. `crypto_market_evidence_v1` — `crypto_market.py`；每 instrument 记录须含：
   - 共有：`source_fetch_id`, `content_hash`, `schema_hash`, `retrieved_at`, `source_used`
   - deribit surface：`instrument_name`, `expiration_timestamp`, `strike`, `option_type`, `mark_iv`（cap 下）
   - coingecko spot：`asset_id`, `symbol`, `price_usd`, `volume_24h_usd`（对齐 capabilities）
3. registry — 五源 `status` → `READY_WITH_EVIDENCE` 或 ADR；yahoo **保持** `validation_only: true`。
4. route — 每源 READY 正例 + `enabled_by_default: false` DISABLED 负例；validation-only 源不得被选为 primary route。

| 契约 / AC              | 测试锚点（INDEX §2）                                |
| ---------------------- | --------------------------------------------------- |
| market evidence fields | `test_market_data_adapters -k evidence_contract`    |
| alpha_vantage port     | `-k alpha_vantage` + route                          |
| stooq validation       | `-k stooq` + `test_advR3xRoute001` 类 primary block |
| yahoo validation-only  | `-k yahoo` + route 不得 primary                     |
| crypto ports           | `test_crypto_market_adapters -q`                    |
| 五源 registry          | `test_source_capabilities` + §9.6 manifest          |
| Layer smoke            | `-k layer`                                          |

---

## 6. Done criteria

- Every listed source is `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`.
- Aggregators cannot silently become primary where official/exchange-grade source is required.
- Option-chain and crypto derivatives paths have strict caps.
- Layer2/Layer4/Layer5 can consume the declared real market-data/evidence envelope.
- Tests and contract coverage are updated.

---

## 7. ResourceGuard and caps

Per-source caps align with `source_capabilities.yaml` and `GLOBAL_RESOURCE_LIMITS.md`. Defaults for this card:

| Source          | Cap dimension              | Default cap (production-entry)      |
| --------------- | -------------------------- | ----------------------------------- |
| `alpha_vantage` | symbols / days / rows      | 5 symbols / 120 days / 500 rows     |
| `alpha_vantage` | option strikes per request | 20 strikes max                      |
| `stooq`         | symbols / days             | 5 symbols / 120 days                |
| `yahoo_finance` | symbols / option strikes   | 3 symbols / 10 strikes (validation) |
| `deribit`       | instruments / surface rows | 5 instruments / 50 surface rows     |
| `coingecko`     | assets                     | 10 assets per request               |

- No full-market scan.
- No full-history daily pull.
- No minute-level default.
- No full option-chain scan by default.
- ponytail: window caps use **calendar days** for **US/global** sources until NYSE/Nasdaq SSOT lands → R3H-05 §5.0.1 **CAL-US**；**CN 日历已闭合 @ R3H-03**（Q12）。Evidence must record `window_kind: calendar_days` where applicable.

---

## 8. Boundary constraints

**Must not:**

- Write `data/duckdb/quant_monitor.duckdb` without Batch 3H production-entry gate / ADR.
- Runtime import or copy from `参考项目/**` or OpenBB AGPL providers.
- Promote yahoo to primary without ADR + registry + route trifecta change.
- Implement R3H-05 layer-binding audit or cross-source clean DDL (G3/G4).
- Mark any owned source READY without adapter + auth + ResourceGuard + route + replay + evidence fields.
- Change shared registry files without coordinator review manifest (§9.6).
- Add crypto trading/account APIs.

**Must:**

- Migrate 3G yahoo fixture semantics into replay-first `yahoo_finance_port`.
- Record per-source final status in registry notes and route tests.
- Block validation-only sources from primary route selection (existing R3X tests must stay green).
- Preserve G13 semantics: validation-only 源不得冒充 primary clean-write 主值（pilot 隔离库除外）。

**3G mass rehearsal index:** `R3G_MASS_REHEARSAL_OPEN_GAPS.md` §2 G2, G13, G16 (yahoo fixture/live) — **G2（US）仍开放** → R3H-05 **CAL-US**。

**归档追溯：** Trellis `06-28-round3h-r3h02-market-data` · 五源 `READY_WITH_EVIDENCE` · yahoo 永久 `validation_only`。

### 8.1 Execute stop conditions

Stop and escalate if:

1. Any step requires writing `quant_monitor.duckdb` to proceed.
2. yahoo `validation_only` flag removed without coordinator ADR.
3. Shared registry conflict with R3H-01/03/04 branch without coordinator merge.
4. Full pytest red after GREEN and root cause is outside current §9 slice.
5. Attempt to implement R3H-05 layer audit or domain-split clean DDL.
6. OpenBB or `参考项目/**` import appears in `backend/` runtime paths.
7. ADR 无 `docs/adr/` 书面文件或 registry/route 未同步 DISABLED。

---

## 9. Implementation steps

**垂直切片（Plan 3.5 to-issues）：** S0=9.0 … S8=9.8。依赖：S1(9.1) 阻塞 S2–S4/S7；S5(9.5) 可在 S1 后并行；S6(9.6) 须 S2–S5 + coordinator；S8(9.8) 最后。

1. **boot_test_skeleton** — Create `tests/test_market_data_adapters.py` and `tests/test_crypto_market_adapters.py` with five-field module docstrings; RED: import normalizer modules that do not exist. Evidence: `execute-evidence/9.0-{red,green}.txt`.

2. **market_data_evidence_contract** — Add `backend/app/datasources/normalizers/market_data.py`:
   - `schema_version: market_data_evidence_v1`
   - Canonical OHLCV + `trade_date` fields per capabilities
   - `build_daily_bar_evidence_bundle()` / `read_daily_bar_evidence_bundle()` / `finalize_bundle` via `evidence_bundle` SSOT
   - ponytail preview helpers（对齐 R3H-01 `ingestion_evidence` 模式）：`market_data_bundle_layer2_preview()`, `market_data_bundle_layer4_preview()`, `market_data_bundle_layer5_provenance()`
   - Tests: fixture round-trip with `content_hash` / `source_fetch_id` / `schema_hash`

3. **alpha_vantage_port** — `backend/app/datasources/fetch_ports/alpha_vantage_port.py`:
   - Mock + authorized live behind `FetchPort`
   - API key gate in port（ponytail：auth 逻辑内联 port；`license_gate.py` 仅当复用需求出现再提取）
   - US equity/ETF daily bar + capped option chain operation
   - Replay: `tests/fixtures/replay/market_data/alpha_vantage/`
   - Route READY + unauthorized DISABLED tests

4. **stooq_port** — `backend/app/datasources/fetch_ports/stooq_port.py`:
   - validation-only posture; global/FX/commodity daily bar
   - Replay fixture; route tests prove not primary where exchange-grade required

5. **yahoo_finance_port** — `backend/app/datasources/fetch_ports/yahoo_finance_port.py`:
   - Migrate from `YahooFinanceAdapter` skeleton + 3G `r3g01/yahoo_finance` bundle
   - Update `adapters/__init__.py` 注册指向 port 边界（或 thin re-export + deprecation 注释）
   - **Keep validation_only**; replay under `tests/fixtures/replay/market_data/yahoo_finance/`
   - Route tests: READY for validation op; blocked as primary（`test_advR3xRoute001` 保持绿）
   - 回归：`test_round3g_limited_production_clean_write` yahoo bundle 路径仍绿

6. **deribit_coingecko_ports** — `deribit_port.py`, `coingecko_port.py`, `crypto_market.py` normalizer:
   - deribit: derivatives + term structure + capped options surface; no trading scope
   - coingecko: spot reference + asset metadata; validation/aggregator only
   - Replay: `tests/fixtures/replay/crypto_market/{deribit,coingecko}/`
   - If blocked: ADR with registry + route reason (no vague defer)

7. **registry_capability_route_coordinator** — Coordinator-reviewed PR:
   - Update five sources in `source_registry.yaml` / `source_capabilities.yaml`（清除 `proposed_disabled_source` 或 ADR）
   - Update `source_route_contract.yaml` / `contract_coverage.yaml`
   - 产出 **`execute-evidence/9.6-manifest.md`** 表（PLAYBOOK §3 列）：

     | source_id | domain | operation | old route | new route | final decision | auth/license | ResourceGuard cap | replay fixture | test command | Layer binding |

   - 同步 `tests/test_provider_catalog.py` 五源 status 期望（若 catalog 断言 proposed_disabled）

8. **layer2_layer4_layer5_market_smoke** — Minimal binding tests only (not R3H-05):
   - 参照 `tests/test_official_macro_adapters.py` 的 `-k layer_smoke` 五字段模板
   - L2：`market_data_bundle_layer2_preview()` 非空 `source_fetch_id` / `content_hash`
   - L4：`market_data_bundle_layer4_preview()` 产出 market structure 样本字段（不含 Layer5 历史 OHLCV 禁止字段）
   - L5：`market_data_bundle_layer5_provenance()` + `EvidenceFoundationValidator` factual_source smoke
   - crypto：至少一条 deribit 或 coingecko replay 的 Layer5 provenance smoke

9. **merge_gate** — `uv run pytest -q`; `uv run python scripts/loop_maintain.py`; update `tests/test_catalog.yaml` for new modules; `tests/test_r3h_source_final_decisions.py` 仍绿；五源 closure evidence in `execute-evidence/9.8-full.txt`.

---

## 10. Tests / gates

```bash
uv run pytest tests/test_market_data_adapters.py -q
uv run pytest tests/test_crypto_market_adapters.py -q
uv run pytest tests/test_source_route_planner.py -q -k "alpha_vantage or stooq or yahoo or deribit or coingecko"
uv run pytest tests/test_source_capabilities.py -q
uv run pytest tests/test_r3x_residual_open_items_closure.py -q -k validation
```

### 10.1 Per-step adversarial focus

| Step | Must prove                                                     |
| ---- | -------------------------------------------------------------- |
| 9.1  | OHLCV evidence end-to-end; `trade_date` not alias-hacked       |
| 9.2  | Unauthorized AV blocks; cap overflow blocks                    |
| 9.3  | stooq cannot become silent primary                             |
| 9.4  | yahoo validation-only route; 3G fixture migrated               |
| 9.5  | deribit no account scope; coingecko not exchange-grade primary |
| 9.6  | No READY without replay path in registry notes                 |
| 9.7  | Layer smoke fails if evidence missing provenance fields        |
| 9.8  | Full suite green; no main DB mutation tests                    |

### 10.2 Plan 对抗性审计闭包（5d · Execute 不读 research）

| 攻击面                    | 对策（frozen/INDEX）                      |
| ------------------------- | ----------------------------------------- |
| yahoo 升格 primary        | §2.8 #6；§9.4；`test_advR3xRoute001`      |
| aggregator silent primary | §9.3 stooq 负例；R3X route block          |
| 全期权链/全市场扫描       | §7 cap；`reject_over_cap`                 |
| OpenBB/参考项目 runtime   | §13；`test_reference_adoption_guardrails` |
| 主库写入                  | §8；INDEX §2.1 Tier D                     |
| registry 并行污染         | §9.6 coordinator manifest；只改五源行     |
| Layer smoke 范围蔓延      | §8.1 #5；§9.7 仅 preview/provenance 测    |
| ADR 偷懒 defer            | §1.2；§8.1 #7；`docs/adr/` 三门齐         |

**Plan 已知 Execute GAP（9.0 关闭）：** 测试模块、replay fixtures、`9.6-manifest.md` 尚不存在 — 属预期 RED 起点，非 Plan 遗漏。

Test bodies must use five-field comments per `GLOBAL_TESTING_POLICY.md`.

---

## 11. Acceptance commands

```bash
uv sync --locked
uv run pytest tests/test_market_data_adapters.py tests/test_crypto_market_adapters.py -q
uv run pytest tests/test_source_route_planner.py -q -k market
uv run pytest -q
uv run python scripts/loop_maintain.py
uv run ruff check backend/app/datasources/fetch_ports backend/app/datasources/normalizers
```

---

## 12. Completion standard

R3H-02 is done only when:

1. All five sources have documented final status (`READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`).
2. `market_data_evidence_v1` / `crypto_market_evidence_v1` normalizers are SSOT for ports.
3. Five fetch ports live under `datasources/fetch_ports/` with route + replay evidence.
4. yahoo remains `validation_only: true`; aggregators cannot silent-primary.
5. Coordinator-reviewed registry/capability/route diff merged.
6. Layer2/L4/L5 market smoke tests pass.
7. Full pytest + loop_maintain exit 0.
8. No main DB write; no reference-project runtime import.

---

## 13. Red flags

Stop and fix if:

- Marking READY from registry note only (no adapter/replay).
- Promoting yahoo/coingecko/stooq to primary without ADR.
- Full option-chain or full-market scan defaults.
- Crypto trading/account API surface introduced.
- Leaving any of five sources as `proposed_disabled_source` without ADR.
- Starting R3H-05 audit inside this card.

---

## 14. reference_project

```yaml
reference_project:
  path: 参考项目/OpenBB/openbb_platform/providers/
  qmd_target_files:
    - backend/app/datasources/fetch_ports/alpha_vantage_port.py
    - backend/app/datasources/normalizers/market_data.py
  direct_copy_allowed: false
  rewrite_required: true
  adoption_ladder: L2_copy_and_rewrite
  notes: Provider catalog layout only; QMD-owned urllib/mock ports; no AGPL runtime.
```

---

## 15. Execute skill freeze

| Skill                      | Binding | Step       | 触发                                 |
| -------------------------- | ------- | ---------- | ------------------------------------ |
| test-driven-development    | 必做    | 9.0–9.8    | 每 §9.x RED→GREEN                    |
| karpathy-guidelines        | 必做    | 9.x        | 正式代码                             |
| testing-guidelines         | 必做    | 9.x        | 测试五字段                           |
| incremental-implementation | 必做    | post-GREEN | 每步 GREEN 后全量 pytest             |
| gitnexus-impact-analysis   | 必做    | 9.2–9.6    | 改 port/route/registry 前 `impact()` |
