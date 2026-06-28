# R3H-03 — CN Market Adapters

## 1. Goal

Close every China-market primary, validation, and authorization-gated source before Round4. This is not only a baostock/cninfo sample task.

Required source coverage:

```text
baostock
akshare
cninfo
tdx_pytdx
mootdx
eastmoney
sina_finance
ths_ifind
qmt_xtdata
qmt_xqshare
```

Each listed source must end as `READY_WITH_EVIDENCE`, validation-only READY, authorization-disabled with tested route reason, or `ADR_DISABLED_OUT_OF_SCOPE`.

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
specs/contracts/source_conflict_rules.yaml
specs/contracts/layer5_evidence_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_source_registry.py
tests/test_source_capabilities.py
tests/test_source_route_planner.py
tests/test_catalog.yaml
```

---

## 3. Reference project use

Use EasyXT for data health and TDX lifecycle adaptation:

```text
参考项目/EasyXT/data_manager/data_integrity_checker.py
参考项目/EasyXT/data_manager/smart_data_detector.py
参考项目/EasyXT/easy_xt/realtime_data/providers/tdx_provider.py
```

Allowed ideas:

- TDX connection lifecycle;
- server selection/failover shape;
- security list / daily/index quote parsing;
- OHLCV/data-integrity checks.

Forbidden:

- auto-login/account-control/trading;
- full-market/full-history/minute default scan;
- hardcoded DB/table;
- SQL interpolation;
- runtime import from `参考项目/**`.

---

## 4. Target QMD files

Implement or update QMD-owned files such as:

```text
backend/app/datasources/fetch_ports/baostock_port.py
backend/app/datasources/fetch_ports/akshare_port.py
backend/app/datasources/fetch_ports/cninfo_port.py
backend/app/datasources/fetch_ports/tdx_pytdx_port.py
backend/app/datasources/fetch_ports/mootdx_port.py
backend/app/datasources/fetch_ports/eastmoney_port.py
backend/app/datasources/fetch_ports/sina_finance_port.py
backend/app/datasources/fetch_ports/ths_ifind_port.py
backend/app/datasources/fetch_ports/qmt_xtdata_port.py
backend/app/datasources/fetch_ports/qmt_xqshare_port.py
backend/app/datasources/normalizers/cn_market.py
backend/app/datasources/auth/license_gate.py
backend/app/core/resource_guard.py
backend/app/ops/data_health_profiles/cn_market.py
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/source_conflict_rules.yaml
specs/verification/contract_coverage.yaml
tests/test_cn_market_adapters.py
tests/test_tdx_provider_port.py
tests/test_source_route_planner.py
tests/test_source_capabilities.py
tests/fixtures/replay/cn_market/**
```

---

## 5. Required implementation per source

For each source, implement:

1. adapter/fetch port or explicit authorization-disabled adapter boundary;
2. auth/license decision, especially for QMT/xqshare/iFinD;
3. ResourceGuard caps for symbols/window/rows and no full-market defaults;
4. route planner READY/validation-only/disabled tests;
5. replay fixture or sandbox sample where allowed;
6. fetch_log/content_hash/schema_hash/source_fetch_id evidence;
7. data health and source conflict checks;
8. Layer3/Layer4/Layer5 binding where this source feeds CN market/evidence paths.

Minimum role expectations:

| Source                       | Expected role                                                                     |
| ---------------------------- | --------------------------------------------------------------------------------- |
| `baostock`                   | CN daily-bar primary candidate for bounded production entry                       |
| `cninfo`                     | announcement/disclosure metadata primary candidate                                |
| `akshare`                    | validation-only unless explicit contract says otherwise                           |
| `tdx_pytdx` / `mootdx`       | raw/validation-only or authorization-gated candidate; no silent fallback          |
| `eastmoney` / `sina_finance` | validation/fallback with source conflict evidence                                 |
| `ths_ifind`                  | authorized validation/research/concept source only after license gate             |
| `qmt_xtdata` / `qmt_xqshare` | local authorized terminal sources; default disabled until user environment exists |

---

## 6. Done criteria

- Every listed source has final decision and tests.
- No CN source silently replaces another source as Primary.
- QMT/iFinD/xqshare remain disabled unless explicit user authorization and environment proof exist.
- Layer3/Layer4/Layer5 have real CN data/evidence paths for declared scope.
- Tests and contract coverage are updated.

---

## 7. ResourceGuard and caps

Per-source caps align with `source_capabilities.yaml` and `GLOBAL_RESOURCE_LIMITS.md`. Production-entry defaults:

| Source                       | Cap dimension              | Default cap (production-entry)         |
| ---------------------------- | -------------------------- | -------------------------------------- |
| `baostock`                   | symbols / rows / window    | 5 symbols / 500 rows / 120 days        |
| `cninfo`                     | filings / PDF bytes        | 5 issuers / 20 filings / 5 MB each     |
| `akshare`                    | symbols / rows             | 3 symbols / 200 rows (validation)      |
| `tdx_pytdx` / `mootdx`       | symbols / rows / net calls | 20 list rows / 3 bars / 5 calls        |
| `eastmoney` / `sina_finance` | symbols / rows             | 3 symbols / 200 rows                   |
| `ths_ifind`                  | concepts / reports         | disabled-by-default; 5 rows if auth    |
| `qmt_xtdata` / `qmt_xqshare` | symbols / minute bars      | disabled-by-default; no minute default |

- No full-market scan, full-history pull, or minute-level default.
- Aggregators (`akshare`, `eastmoney`, `sina_finance`) must emit `quality_flags` and never silently replace `baostock`/`cninfo` primary roles.
- QMT / iFinD / xqshare require `license_gate` + user authorization artifact before any READY route.

---

## 8. Boundary constraints

**Must not:**

- Write `data/duckdb/quant_monitor.duckdb` without Batch 3H production-entry gate / ADR.
- Runtime import or copy from `参考项目/**` (EasyXT ideas only via L2 rewrite).
- Auto-login, account control, trading APIs, or SQL interpolation.
- Mark any owned source READY without adapter + auth + ResourceGuard + route + replay + evidence fields.
- Change shared registry rows for R3H-01/02/04 sources or modify R3H-04 adapter modules.
- Implement R3H-05 full cross-layer audit (Layer smoke only in §9.9).

**Must:**

- Absorb 3G G11 (baostock productized fetch→evidence) and G16 (cninfo/akshare closure).
- Migrate staged pilot fetch (`ops/staged_pilot_fetch_ports.py`) patterns into `datasources/fetch_ports/*` per `reference_adoption_guardrails.yaml`.
- Record per-source final status in registry + coordinator manifest (§9.8).

**3G index:** `R3G_MASS_REHEARSAL_OPEN_GAPS.md` §2 G11, G16; **G2/G17（CN）已闭合** @ Grill-me Q12（`cn_trading_calendar` + `calendar_authority=True`）；**美股/全球交易日历不在本卡** → `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0.1 **CAL-US** → R3H-05。

**归档追溯：** `R3H_03_REFERENCE_ADOPTION_AUDIT.md` · Trellis `06-28-round3h-r3h03-cn-market` · `R3H_REFERENCE_ADOPTION_INDEX.md` §1。

**STAGED-PILOT-SSOT（延后）：** 产品 fetch = `datasources/fetch_ports/*`；`ops/staged_pilot_fetch_ports.py` 仅 3G/`--live-wire` — post-R3H-05 debt-lite 收敛，见索引 §3。

### 8.1 Execute stop conditions

1. Step requires main DB write to proceed.
2. Shared registry conflict with parallel R3H-04 branch without coordinator merge.
3. Full pytest red after GREEN and root cause outside current §9 slice.
4. Attempt to enable QMT/iFinD/xqshare without tested authorization-disabled negative path.
5. Silent primary replacement detected in route planner tests.

---

## 9. Implementation steps

**垂直切片（Plan 3.5 to-issues）：** S0=9.0 … S10=9.10。依赖：S1(9.1) 阻塞 S2–S4/S9；S5–S7(9.5–9.7) 可在 S1 后并行；S8(9.8) 须 S2–S7 + coordinator；S10(9.10) 最后。

1. **boot_test_skeleton** — `tests/test_cn_market_adapters.py` + extend `tests/test_tdx_provider_port.py`; RED: missing `cn_market` normalizer.

2. **cn_market_evidence_contract (G11/G16)** — `backend/app/datasources/normalizers/cn_market.py` + `backend/app/datasources/auth/license_gate.py`:
   - `cn_market_evidence_v1` bundle (`observation_date`/`trade_date`, `source_fetch_id`, hashes)
   - L2 migrate baostock/cninfo staged pilot shapes from `ops/staged_pilot_fetch_ports.py`
   - Remove long-term DH sidecar dependency for baostock pilot path where normalizer suffices

3. **baostock_port** — `fetch_ports/baostock_port.py`; Primary `cn_equity_daily_bar`; mock/replay default; optional authorized live behind gate; route READY + DISABLED tests; `tests/fixtures/replay/cn_market/baostock/`.

4. **cninfo_port** — `fetch_ports/cninfo_port.py`; Primary filings/announcements; metadata + optional PDF cap; replay fixture; route tests.

5. **akshare_validation_port** — `fetch_ports/akshare_port.py`; **validation_only** permanent; `quality_flags` on all rows; no primary route upgrade.

6. **tdx_family_ports** — Harden `tdx_pytdx_port.py`; add `mootdx_port.py`; shared TDX lifecycle ideas from EasyXT (no runtime import); `tests/test_tdx_provider_port.py` + replay under `cn_market/tdx/`.

7. **eastmoney_sina_ports** — `eastmoney_port.py`, `sina_finance_port.py`; validation/fallback with `source_conflict_rules` evidence; disabled-by-default route negative tests.

8. **auth_gated_ports** — `ths_ifind_port.py`, `qmt_xtdata_port.py`, `qmt_xqshare_port.py`; default **authorization-disabled**; READY only with `license_gate` + env proof tests; no silent enable.

9. **registry_coordinator** — Update owned rows only in shared YAML + `contract_coverage.yaml`; manifest table per `BATCH_3H_COORDINATOR_PLAYBOOK.md` §3.

10. **layer_cn_smoke** — Minimal Layer3/Layer4/Layer5 CN evidence binding (not R3H-05 full audit).

11. **merge_gate** — Full pytest + `loop_maintain.py`; catalog update for new test modules.

---

## 10. Tests / gates

```bash
uv run pytest tests/test_cn_market_adapters.py -q
uv run pytest tests/test_tdx_provider_port.py -q
uv run pytest tests/test_source_route_planner.py -q -k "baostock or cninfo or akshare or tdx or mootdx or eastmoney or sina or ifind or qmt"
uv run pytest tests/test_source_capabilities.py -q
```

Five-field test comments per `GLOBAL_TESTING_POLICY.md`. Adversarial: unauthorized QMT/iFinD blocks; akshare cannot become primary; cap overflow blocks.

---

## 11. Acceptance commands

```bash
uv sync --locked
uv run pytest tests/test_cn_market_adapters.py tests/test_tdx_provider_port.py -q
uv run pytest -q
uv run python scripts/loop_maintain.py
```

---

## 12. Completion standard

Ten sources each `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE` with registry + route + replay path documented. Coordinator manifest attached for shared file PR.

---

## 13. Red flags

- Registry note without port implementation.
- `akshare` promoted to primary for any CN equity domain.
- QMT enabled without authorization tests.
- Runtime `参考项目` import in `backend/`.

---

## 14. Reference project (EasyXT)

Allowed: TDX connection lifecycle, server failover shape, security list / daily bar parsing, OHLCV integrity checks (L2 rewrite into `cn_market` / TDX ports).

Forbidden: auto-login, full-market scan, hardcoded DB/table, SQL interpolation, runtime import.

---

## 15. Execute Skill freeze

| Skill                      | 本任务 | 绑定 Step |
| -------------------------- | ------ | --------- |
| test-driven-development    | 必做   | 每 §9.x   |
| karpathy-guidelines        | 必做   | 每步      |
| testing-guidelines         | 必做   | 每步      |
| incremental-implementation | 必做   | 每 GREEN  |
| gitnexus-impact-analysis   | 必做   | 改符号前  |
