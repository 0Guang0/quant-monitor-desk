<!-- FROZEN: Plan protocol v4 · do not edit · source: docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_03_CN_MARKET_ADAPTERS.md · frozen_at: 2026-06-28T07:08:32Z -->

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

### 1.1 Plan architecture decisions（2a brainstorm + 3 grill-me · 已内联）

| 选项 | 结论 |
| ---- | ---- |
| A. 单文件 `cn_adapter.py` 十源 catch-all | **否决** — 隐藏 auth/cap/evidence |
| B. 每源独立 port + `cn_market` normalizer | **采纳** — 对齐 R3H-01/02 |
| C. 仅 registry 笔记 closure | **否决** — BATCH_3H_HARDENING_RULES §3 |
| D. 保留 ops staged pilot 为长期路径 | **否决** — G11 产品化要求 |
| E. QMT 默认 READY 加速 demo | **否决** — 活卡 §6 + D11 |

| 风险 | 缓解 |
| ---- | ---- |
| registry 与 R3H-04 并行冲突 | §9.8 coordinator manifest；**仅改十源行**；禁止 kalshi/polymarket/web_search |
| TDX 双源 tdx_pytdx/mootdx 重复 | 共享 normalizer 片段；独立 source_id；无 silent fallback |
| 工期十源膨胀 | replay-first；live 仅用户显式授权子集 |
| G2/G17 交易日历 | §9.9 最小 profile 或登记 R3H-05 交接（**须用户确认 Q12**） |

| grill 锁定项 | 决定 |
| ------------ | ---- |
| 3G baostock `--live-wire` | **≠** baostock READY；G11 本卡闭合 |
| 主库 | **禁止**写 `quant_monitor.duckdb` |
| staged pilot | L2 迁入 `fetch_ports/`；ops 仅 orchestration |
| akshare | **validation_only 永久**；禁止 silent primary |
| QMT/iFinD/xqshare | **authorization-disabled 默认**；READY 须 `license_gate` + 负例 |
| Layer | §9.9 smoke only；**禁止** R3H-05 |
| 切片顺序 | 9.1 证据 → 9.2–9.4 primary/validation → 9.5–9.7 并行 → 9.8 registry → 9.9 layer → 9.10 merge |

### 1.2 ADR 收窄策略（grill-me Q8 · 已内联）

| 源 | ADR 允许？ | 说明 |
| -- | ---------- | ---- |
| `baostock` / `cninfo` | **禁止** | Primary 承诺域；须 `READY_WITH_EVIDENCE` |
| `akshare` | **禁止升格** | validation_only 永久；允许完全禁用 ADR |
| `tdx_pytdx` | **禁止** | 已有 port；须 hardened + replay |
| `ths_ifind` / `qmt_xtdata` | **禁止默认 READY** | disabled-by-default；授权正例 + 负例齐全 |
| `mootdx` | 候选 | 与 tdx_pytdx 重叠；仅 Execute 真受阻时 |
| `qmt_xqshare` | 候选 | 远程终端边缘；仅 Execute 真受阻时 |
| `eastmoney` / `sina_finance` | 候选 | 默认 validation READY；受阻可 ADR |

书面 ADR 路径：`docs/adr/ADR-*-{source_id}-*.md` + registry `ADR_DISABLED_OUT_OF_SCOPE` + route DISABLED reason。

### 2.8 Plan vs Execute gates

1. **R3H-01/02 CLOSED** does not substitute for R3H-03; ten CN sources remain open until §9.2–9.8 pass.
2. **No main DB writes**; sandbox/replay/`.audit-sandbox` only unless a future Batch 3H gate explicitly authorizes `quant_monitor.duckdb`.
3. **Coordinator review** required before merging shared registry/capability/route files (see §9.8 manifest table).
4. **R3H-05 is forbidden** in this branch; Layer work is §9.9 smoke only.
5. **QMT / iFinD / xqshare** default **authorization-disabled**; READY only with `license_gate` + user env proof + tested unauthorized negative path.
6. **akshare** must remain `validation_only: true` in registry after closure.
7. **R3H-04 sources forbidden:** do not edit registry rows or adapters for `kalshi`, `polymarket`, `web_search`.

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

Do not create a generic catch-all `cn_adapter.py` that hides per-source auth, caps, and evidence rules.

### 4.1 Data flow and impact targets (Plan 1b)

```text
FetchRequest → fetch_ports/*_port.py (mock/replay default, live opt-in)
  → cn_market.py normalizer  ← G11/G16 证据 SSOT
  → license_gate.py  ← QMT/iFinD/xqshare 三门
  → evidence bundle (source_fetch_id, content_hash, schema_hash, trade_date/observation_date)
route_planner + capability_registry → READY / DISABLED / validation-only block
staged_pilot_fetch_ports (baostock/cninfo) → L2 migrate → replay/cn_market/**
Layer3/4/5 CN evidence ← §9.9 smoke consumers only
```

**GitNexus impact before edit（Execute 每步前 `impact()`）：**

| 符号 / 模块 | 风险 | 触发 Step |
| ----------- | ---- | --------- |
| `cn_market` normalizer（新建） | MEDIUM | 9.1 |
| `staged_pilot_fetch_ports` baostock/cninfo | MEDIUM | 9.1–9.3 |
| `tdx_pytdx_port` | LOW–MEDIUM | 9.5 |
| `route_planner` CN domain rows | MEDIUM | 9.6–9.8 |
| `license_gate`（新建） | LOW | 9.1, 9.7 |
| `qmt_xtdata` skeleton adapter | LOW | 9.7 |

**索引滞后：** `tdx_pytdx_port` 可能未入 GitNexus 符号表；Execute boot 建议 `node .gitnexus/run.cjs analyze` 后重跑 `impact()`。

### 4.2 Baseline state（Plan 1a · 开工前）

| source_id | adapter/port 现状 | registry 姿态 |
| --------- | ----------------- | ------------- |
| baostock | skeleton + staged pilot ops | enabled Primary candidate |
| cninfo | skeleton + staged pilot | enabled Primary filings |
| akshare | skeleton | validation_only |
| tdx_pytdx | **port 存在**（R3FR-03） | disabled validation |
| mootdx | **无 port** | disabled validation |
| eastmoney | **无 port** | disabled validation |
| sina_finance | **无 port** | disabled validation |
| ths_ifind | **无 port** | disabled + auth_required |
| qmt_xtdata | skeleton adapter | disabled + user_setup |
| qmt_xqshare | **无 port** | disabled + user_setup |

**3H 目标流：** mock/replay-first fetch port → `cn_market` evidence v1 → route READY + negative tests → registry 十源终态。

### 4.3 GitNexus Execute boot（Plan 1b）

- 改码前：`impact()` 锚定 `DataSourceService.fetch`、`route_planner`、`staged_pilot_fetch_ports`、`tdx_pytdx_port`、`resource_guard`。
- **禁止触碰（他轨）：** `fred_port`, `yahoo_finance_port`, `kalshi`, `polymarket`, `web_search` 等 R3H-01/02/04 符号（registry 行亦禁止）。

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

### 5.1 Contract schema and spec→test map（Plan 2b · 已内联）

**权威契约（原文仍在 INDEX §3 manifest）：** `source_capability_contract.yaml`, `source_route_contract.yaml`, `datasource_service_contract.yaml`, `data_quality_rules.yaml`, `source_conflict_rules.yaml`, `layer5_evidence_contract.yaml`, `reference_adoption_guardrails.yaml`.

**本任务新增契约面：**

1. `cn_market_evidence_v1` — `cn_market.py`；对齐 `source_capabilities` CN domain fields（`trade_date`/`observation_date`, hashes, `source_fetch_id`）。
2. `license_gate` 决策枚举 — `AUTHORIZED` / `DISABLED_NO_ARTIFACT` / `DISABLED_ENV_MISSING`；QMT/iFinD/xqshare 须负例测试。
3. registry — 十源 `READY_WITH_EVIDENCE` 或 ADR；akshare **保持** `validation_only: true`。

| 契约 / AC | 测试锚点（INDEX §2） |
| --------- | -------------------- |
| cn_market evidence | `-k evidence_contract` |
| baostock primary | `-k baostock` + route |
| cninfo filings | `-k cninfo` |
| akshare validation-only | `-k akshare` + primary 负例 |
| TDX family | `-k "tdx or mootdx"` + `test_tdx_provider_port` |
| eastmoney/sina conflict | `-k "eastmoney or sina or conflict"` |
| auth-gated | `-k "ifind or qmt or xqshare"` unauthorized |
| 十源 registry | `test_source_capabilities` + §9.8 manifest |
| Layer CN smoke | `-k layer_cn` |

**十源 × 八项闭环（每源须 adapter + auth + ResourceGuard + route + replay + evidence + health/conflict + layer 绑定 where applicable）：**

| source_id | Step | `-k` 锚点 | port | auth/RG | route | replay | evidence |
| --------- | ---- | --------- | ---- | ------- | ----- | ------ | -------- |
| baostock | 9.2 | baostock | ✓ | ✓ | ✓ | ✓ | ✓ |
| cninfo | 9.3 | cninfo | ✓ | ✓ | ✓ | ✓ | ✓ |
| akshare | 9.4 | akshare | ✓ | validation | ✓ | ✓ | ✓ |
| tdx_pytdx | 9.5 | tdx | ✓ | gate | ✓ | ✓ | ✓ |
| mootdx | 9.5 | mootdx | ✓ | gate | ✓ | ✓ | ✓ |
| eastmoney | 9.6 | eastmoney | ✓ | ✓ | ✓ | ✓ | ✓ |
| sina_finance | 9.6 | sina | ✓ | ✓ | ✓ | ✓ | ✓ |
| ths_ifind | 9.7 | ifind | ✓ | license_gate | ✓ | ✓ | ✓ |
| qmt_xtdata | 9.7 | qmt | ✓ | license_gate | ✓ | ✓ | ✓ |
| qmt_xqshare | 9.7 | xqshare | ✓ | license_gate | ✓ | ✓ | ✓ |

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

| Source                       | Cap dimension              | Default cap (production-entry)        |
| ---------------------------- | -------------------------- | ------------------------------------- |
| `baostock`                   | symbols / rows / window    | 5 symbols / 500 rows / 120 days       |
| `cninfo`                     | filings / PDF bytes        | 5 issuers / 20 filings / 5 MB each    |
| `akshare`                    | symbols / rows             | 3 symbols / 200 rows (validation)   |
| `tdx_pytdx` / `mootdx`       | symbols / rows / net calls | 20 list rows / 3 bars / 5 calls       |
| `eastmoney` / `sina_finance` | symbols / rows             | 3 symbols / 200 rows                  |
| `ths_ifind`                  | concepts / reports         | disabled-by-default; 5 rows if auth   |
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

**3G index:** `R3G_MASS_REHEARSAL_OPEN_GAPS.md` §2 G11, G16; G2/G17 trading calendar may partial here or hand off R3H-05 (**须用户确认**，见 grill-me Q12).

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

8. **auth_gated_ports** — TDD 子序（单步内仍 RED→GREEN 逐 port）：
   - `ths_ifind_port.py` — default **authorization-disabled**；`-k ifind` unauthorized 负例 → authorized fixture 正例
   - `qmt_xtdata_port.py` — skeleton 迁出；`-k qmt` unauthorized 负例
   - `qmt_xqshare_port.py` — default **authorization-disabled**；`-k xqshare` unauthorized 负例
   - 三门共享 `license_gate`；**禁止** silent enable；READY 仅 env proof + 负例齐全

9. **registry_coordinator** — Update owned rows only in shared YAML + `contract_coverage.yaml`; manifest table per `BATCH_3H_COORDINATOR_PLAYBOOK.md` §3.

10. **layer_cn_smoke** — Minimal Layer3/Layer4/Layer5 CN evidence binding (not R3H-05 full audit).

11. **merge_gate** — Full pytest + `loop_maintain.py`; catalog update for new test modules.

### Execute state (§9)

| Step | 已执行 |
| ---- | ------ |
| 9.0 boot_test_skeleton | [x] |
| 9.1 cn_market_evidence_contract | [x] |
| 9.2 baostock_port | [x] |
| 9.3 cninfo_port | [x] |
| 9.4 akshare_validation_port | [x] |
| 9.5 tdx_family_ports | [x] |
| 9.6 eastmoney_sina_ports | [x] |
| 9.7 auth_gated_ports | [x] |
| 9.8 registry_coordinator | [x] |
| 9.9 layer_cn_smoke | [x] |
| 9.10 merge_gate | [x] |

---

## 10. Tests / gates

```bash
uv run pytest tests/test_cn_market_adapters.py -q
uv run pytest tests/test_tdx_provider_port.py -q
uv run pytest tests/test_source_route_planner.py -q -k "baostock or cninfo or akshare or tdx or mootdx or eastmoney or sina or ifind or qmt or xqshare"
uv run pytest tests/test_source_capabilities.py -q
```

### 10.1 Per-step adversarial focus

| Step | Must prove |
| ---- | ---------- |
| 9.0  | Module skeleton exists; normalizer import fails first |
| 9.1  | `cn_market_evidence_v1` end-to-end; staged pilot L2 迁出 |
| 9.2  | baostock Primary READY + unauthorized DISABLED；cap overflow blocks |
| 9.3  | cninfo filings metadata + route；PDF cap enforced |
| 9.4  | akshare **cannot** become primary；`quality_flags` present |
| 9.5  | tdx/mootdx no silent fallback；independent source_id |
| 9.6  | eastmoney/sina conflict evidence；no silent primary replacement |
| 9.7  | QMT/iFinD/**xqshare** default disabled；unauthorized blocks |
| 9.8  | Ten-source registry manifest；**no R3H-04 row edits** |
| 9.9  | Layer CN smoke fails if provenance fields missing |
| 9.10 | Full suite green; no main DB mutation tests |

### 10.2 Plan 对抗性审计闭包（5d · Execute 不读 research）

| 攻击面 | 对策（frozen/INDEX） |
| ------ | -------------------- |
| akshare 升格 primary | §2.8 #6；§9.4；route 负例 |
| QMT/iFinD/xqshare 无授权 READY | §2.8 #5；§9.7 `-k xqshare` 负例 |
| aggregator silent primary | §9.6 conflict evidence；§8.1 #5 |
| 全市场/分钟默认扫描 | §7 cap；`reject_over_cap` |
| EasyXT/参考项目 runtime | §13；`reference_adoption_guardrails` |
| 主库写入 | §8；INDEX §2.1 Tier D |
| registry 并行污染 R3H-04 | §2.8 #7；§9.8 coordinator；禁止 kalshi/polymarket/web_search |
| Layer smoke 范围蔓延 | §8.1；§9.9 仅 smoke |
| ADR 偷懒 defer | §1.2；§8.1；`docs/adr/` 三门齐 |
| G2/G17 交易日历 silent defer | §8 须用户确认 Q12；§9.9 最小 profile |

**Plan 已知 Execute GAP（9.0 关闭）：** `test_cn_market_adapters.py`、replay fixtures、`9.8-manifest.md` 尚不存在 — 属预期 RED 起点，非 Plan 遗漏。

Five-field test comments per `GLOBAL_TESTING_POLICY.md`. Adversarial: unauthorized QMT/iFinD/**xqshare** blocks; akshare cannot become primary; cap overflow blocks.

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

**本地路径（gitignore，Execute 须 Read 后定阶梯；禁止 runtime import）：**

| 参考 | 阶梯 | QMD 目标 |
|------|------|----------|
| `参考项目/EasyXT/easy_xt/realtime_data/providers/tdx_provider.py` | L2（R3FR-03 已拷改） | `tdx_pytdx_port.py`, `mootdx_port.py` |
| `参考项目/EasyXT/data_manager/smart_data_detector.py` | L2 拷改 | `calendar_gap_rules` / CN trading calendar（**用户 Gate：完整 G2/G17**） |
| `参考项目/EasyXT/data_manager/data_integrity_checker.py` | L2 拷改 | `ops/data_health_profiles/cn_market.py` |
| `ops/staged_pilot_fetch_ports.py` + adapters skeleton | L2 迁出 | `baostock_port`, `cninfo_port`, `akshare_port` |

Allowed: TDX lifecycle, server failover, security list / bar parsing, OHLCV integrity, staged pilot field maps (L2 rewrite into QMD modules with attribution).

Forbidden: auto-login, full-market scan, hardcoded DB/table, SQL interpolation, runtime `import`/`sys.path` from `参考项目/**`.

**采纳审计 SSOT：** `research/reference-adoption-audit.md`

---

## 15. Execute Skill freeze

| Skill                       | 本任务 | 绑定 Step |
| --------------------------- | ------ | --------- |
| test-driven-development     | 必做   | 每 §9.x   |
| karpathy-guidelines         | 必做   | 每步      |
| testing-guidelines          | 必做   | 每步      |
| incremental-implementation  | 必做   | 每 GREEN  |
| gitnexus-impact-analysis    | 必做   | 改符号前  |
