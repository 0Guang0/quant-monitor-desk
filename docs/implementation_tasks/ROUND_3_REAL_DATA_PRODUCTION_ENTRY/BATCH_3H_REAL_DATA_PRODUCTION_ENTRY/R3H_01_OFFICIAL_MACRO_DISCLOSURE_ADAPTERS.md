# R3H-01 — Official Macro and Disclosure Adapters

## 1. Goal

Close every official macro / regulator / filing source before Round4. This is not a sample-source task.

Required source coverage:

```text
fred
us_treasury
sec_edgar
cftc_cot
bis
world_bank
```

Each listed source must end as `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`.

### 1.1 Plan architecture decisions（2a brainstorm + 3 grill-me · 已内联）

| 选项                                                 | 结论                          |
| ---------------------------------------------------- | ----------------------------- |
| A. 永久保留 bridge + DH sidecar                      | **否决** — G14 pilot hack     |
| B. 统一 `official_macro` normalizer + 迁 `fred_port` | **采纳**                      |
| C. 仅 debt-lite G10、不修六源                        | **否决** — Batch 3H hardening |
| D. 本卡写主库验证                                    | **否决** — 路线图 §5.0        |

| 风险                                         | 缓解                                                     |
| -------------------------------------------- | -------------------------------------------------------- |
| registry 与 R3H-02~04 并行冲突               | §9.6 coordinator manifest；禁止未协调改共享文件          |
| `ops/fred_fetch_ports` 与 `fred_port` 双实现 | L2 迁入 `datasources/fetch_ports/`；ops 仅 orchestration |
| 六源工期膨胀                                 | replay-first；真网 live 仅 fred P0；ADR 须书面           |

| grill 锁定项                  | 决定                                                                      |
| ----------------------------- | ------------------------------------------------------------------------- |
| 3G 预演                       | **≠** fred READY；G10/G14 本卡闭合                                        |
| 主库                          | **禁止**写 `quant_monitor.duckdb`                                         |
| bridge                        | 废弃 sidecar；共享 normalizer                                             |
| 六源终态                      | READY_WITH_EVIDENCE **或** ADR_DISABLED（禁止含糊 defer）                 |
| ADR 候选（仅 Execute 受阻时） | `world_bank`、`bis` 可 ADR；`fred`/`us_treasury`/`sec_edgar` **禁止 ADR** |
| Layer                         | §9.7 smoke only；**禁止** R3H-05                                          |
| B2.5-O-05                     | 可登记 capped production-entry；**仍** disabled-by-default + 用户授权三门 |
| 切片顺序                      | 9.1 G10 → 9.2 fred → 9.3–9.5 并行 → 9.6 registry → 9.7 layer → 9.8 merge  |

### 2.8 Plan vs Execute gates

1. **Batch 3G CLOSED** does not substitute for R3H-01 closure; G10/G14 **已闭合** @ 2026-06-28（Trellis `06-28-round3h-r3h01-official-macro`）。
2. **No main DB writes** in this task; sandbox/replay/`.audit-sandbox` only unless a future Batch 3H gate explicitly authorizes `quant_monitor.duckdb`.
3. **Coordinator review** required before merging shared registry/capability/route files (see §9.6 manifest table).
4. **R3H-05 is forbidden** in this branch; Layer work is §9.7 smoke only.
5. **FRED live fetch** requires existing R3E authorization artifact + `FRED_API_KEY`; mock/replay is the default in tests.

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
specs/contracts/layer5_evidence_contract.yaml
specs/contracts/snapshot_lineage_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_source_registry.py
tests/test_source_capabilities.py
tests/test_source_route_planner.py
tests/test_catalog.yaml
```

---

## 3. Reference project use

Reference tree:

```text
参考项目/
```

Use OpenBB provider structure only for architecture ideas:

```text
参考项目/OpenBB/openbb_platform/providers/
参考项目/OpenBB/openbb_platform/providers/fred/
```

Allowed ideas:

- provider metadata shape;
- optional auth/extras/terms metadata;
- provider README/catalog organization;
- source/domain separation.

Forbidden:

- copying OpenBB AGPL runtime provider source;
- importing `参考项目/**` from backend runtime;
- bypassing QMD route/auth/ResourceGuard gates.

---

## 4. Target QMD files

Implement or update QMD-owned files such as:

```text
backend/app/datasources/fetch_ports/fred_port.py
backend/app/datasources/fetch_ports/us_treasury_port.py
backend/app/datasources/fetch_ports/sec_edgar_port.py
backend/app/datasources/fetch_ports/cftc_cot_port.py
backend/app/datasources/fetch_ports/bis_port.py
backend/app/datasources/fetch_ports/world_bank_port.py
backend/app/datasources/normalizers/official_macro.py
backend/app/datasources/normalizers/sec_edgar.py
backend/app/datasources/auth/license_gate.py
backend/app/core/resource_guard.py
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/source_capability_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_official_macro_adapters.py
tests/test_sec_edgar_adapter.py
tests/test_source_route_planner.py
tests/test_source_capabilities.py
tests/fixtures/replay/official_macro/**
tests/fixtures/replay/sec_edgar/**
```

Do not create a generic catch-all `official_adapter.py` that hides source-specific auth, rate limits, fields, and evidence rules.

### 4.1 Data flow and impact targets (Plan 1b)

```text
live_pilot_phase3 / fred_sandbox_pilot
  → fred_live_fetch_evidence.json (series[].rows, observation_date)
official_macro.py normalizer  ← SSOT (G10)
  → fred_evidence.json (official_macro_evidence_v1)
rehearsal_loader._fred_staging_rows → promote (pilot DB only, 3G path)
fred_port.py (new) → FetchPort + replay fixtures
route_planner + capability_registry → READY / DISABLED
```

**GitNexus impact before edit:** `official_macro` writer/reader, `rehearsal_loader._fred_staging_rows`, `live_evidence_bridge.materialize_fred_promote_evidence`, `capture_phase3_raw_evidence`, `create_fred_fetch_port` (migrate target).

**ponytail:** one normalizer module; bridge becomes thin delegate until tests drop it.

### 4.2 Baseline state（Plan 1a · 开工前）

| 维度            | 当前                                                                      |
| --------------- | ------------------------------------------------------------------------- |
| `fred` registry | disabled-by-default, Primary, macro_series, requires_user_setup           |
| fetch port      | **无** `fred_port.py`；live 经 `live_pilot_phase3` + `fred_sandbox_pilot` |
| promote         | `rehearsal_loader._fred_staging_rows` ← `fred_evidence.json`              |
| live→promote    | `live_evidence_bridge`（pilot；待 §9.1 瘦身）                             |
| 兄弟五源        | registry `proposed_disabled_source`；adapter 未交付                       |

**3H 目标流：** live_pilot → **统一 normalizer** → rehearsal_loader（**无** bridge sidecar）。

### 4.3 GitNexus Execute boot（Plan 1b）

- 改码前：`impact()` 锚定 `official_macro` writer/reader、`_fred_staging_rows`、`materialize_fred_promote_evidence`、`capture_phase3_raw_evidence`、`fred_port`。
- 索引滞后时：Execute boot 可 `node .gitnexus/run.cjs analyze` 后重跑 impact。
- **风险预判：** FRED schema 统一 = **MEDIUM**（触及 bridge/loader/live_pilot/round3g 测）；不触及 R3H-05 全层路径。

---

## 5. Required implementation per source

For each source, implement:

1. adapter/fetch port with explicit source_id;
2. auth/license decision;
3. ResourceGuard caps for symbols/series/window/rows;
4. route planner READY test and DISABLED/unauthorized negative test;
5. replay fixture or sandbox sample;
6. fetch_log/content_hash/schema_hash/source_fetch_id evidence;
7. data health or freshness checks appropriate to low-frequency official data;
8. Layer1/Layer5 binding where the source feeds macro/disclosure evidence.

Minimum domain expectations:

| Source        | Domains                                      |
| ------------- | -------------------------------------------- |
| `fred`        | P0 macro series live/authorized closure      |
| `us_treasury` | yield curve, inflation expectation reference |
| `sec_edgar`   | company filings, Form 4 insider transactions |
| `cftc_cot`    | weekly COT positioning                       |
| `bis`         | policy rates, credit-to-GDP gap              |
| `world_bank`  | low-frequency development indicators         |

### 5.1 Contract schema and spec→test map（Plan 2b · 已内联）

**权威契约（原文仍在 §3 manifest）：** `source_capability_contract.yaml`, `source_route_contract.yaml`, `datasource_service_contract.yaml`, `data_quality_rules.yaml`, `layer5_evidence_contract.yaml`, `reference_adoption_guardrails.yaml`；`sandbox_clean_write_contract.yaml` 仅 3G promote 只读参考。

**本任务新增契约面：**

1. `official_macro_evidence_v1` — 实现于 `official_macro.py`；字段对齐 `source_capabilities.fred.macro_series.fields`（`observation_date` 等）。
2. registry — 六源 `status` → `READY_WITH_EVIDENCE` 或 ADR 登记。
3. route — 每源 READY 正例 + `enabled_by_default: false` 时 DISABLED 负例。

| 契约 / AC            | 测试锚点（INDEX §2）                                 |
| -------------------- | ---------------------------------------------------- |
| fred evidence fields | `test_official_macro_adapters -k evidence_contract`  |
| fred port + route    | `-k fred_port` + `test_source_route_planner -k fred` |
| guardrails           | `test_reference_adoption_guardrails`                 |
| Layer5 provenance    | `-k layer`                                           |
| 六源 registry        | `test_source_capabilities` + §9.6 manifest           |

---

## 6. Done criteria

- Every listed source is `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`.
- No listed source remains a vague proposed-disabled placeholder.
- Official factual sources have higher route priority than aggregators/web sources.
- Layer1/Layer5 can consume at least the declared official macro/disclosure evidence path.
- Tests and contract coverage are updated.

---

## 7. ResourceGuard and caps

Per-source caps must align with `source_capabilities.yaml` and `GLOBAL_RESOURCE_LIMITS.md`. Defaults for this card:

| Source        | Cap dimension        | Default cap (production-entry)  |
| ------------- | -------------------- | ------------------------------- |
| `fred`        | series / rows / days | 10 series / 500 rows / 120 days |
| `us_treasury` | tenors / rows        | 20 tenors / 500 rows            |
| `sec_edgar`   | CIK / filings        | 5 CIK / 50 filings per run      |
| `cftc_cot`    | markets / rows       | 5 markets / 52 weeks            |
| `bis`         | series / countries   | 10 series / 5 countries         |
| `world_bank`  | indicators           | 5 indicators / 5 countries      |

- No full-history macro pull.
- No minute-level official feeds.
- FRED live fetch requires `FRED_API_KEY` + user authorization artifact (existing R3E path).
- SEC EDGAR requires User-Agent / contact identity header on every HTTP call.

---

## 8. Boundary constraints

**Must not:**

- Write `data/duckdb/quant_monitor.duckdb` without Batch 3H production-entry gate / ADR (3G pilot data must not merge in).
- Runtime import or copy from `参考项目/**` or OpenBB AGPL providers.
- Keep `live_evidence_bridge._write_sandbox_rehearsal_gate_sidecars` as the long-term DH gate.
- Implement R3H-05 layer-binding audit or cross-source schema DDL (G3/G4 → R3H-05 / separate schema task).
- Mark any owned source READY without adapter + auth + ResourceGuard + route + replay + evidence fields.
- Change shared registry files without coordinator review manifest (see §9.6).

**Must:**

- Absorb 3G G10/G14: unified FRED evidence contract for live pilot and promote loader.
- Record per-source final status in registry notes and route tests.
- Use L2 copy-and-rewrite per `reference_adoption_guardrails.yaml` when moving ops fetch code into `datasources/fetch_ports/`.

**3G mass rehearsal index:** `R3G_MASS_REHEARSAL_OPEN_GAPS.md` §2 G10, G14 — **已闭合** @ 2026-06-28。

**归档追溯：** Trellis `06-28-round3h-r3h01-official-macro` · `official_macro_evidence_v1` SSOT · audit 零遗留。

### 8.1 Execute stop conditions

Stop and escalate if:

1. Any step requires writing `quant_monitor.duckdb` to proceed.
2. `live_evidence_bridge` sidecar is the only way to pass DH after §9.1.
3. Shared registry conflict with R3H-02/03/04 branch without coordinator merge.
4. Full pytest red after a GREEN step and root cause is outside current §9 slice.
5. Attempt to implement R3H-05 layer audit or domain-split clean DDL (G3/G4).
6. OpenBB or `参考项目/**` import appears in `backend/` runtime paths.

---

## 9. Implementation steps

**垂直切片（Plan 3.5 to-issues）：** S0=9.0 … S8=9.8。依赖：S1(9.1) 阻塞 S2(9.2)/S7(9.7)；S3–S5(9.3–9.5) 可在 S1 后并行；S6(9.6) 须 S2–S5 后且 coordinator 审查；S8(9.8) 最后。

1. **boot_test_skeleton** — Create `tests/test_official_macro_adapters.py` (and stub `tests/test_sec_edgar_adapter.py` if missing) with five-field module docstring; RED: import `official_macro` normalizer module that does not exist yet. Evidence: `execute-evidence/9.0-red.txt` → GREEN after empty contract tests pass.

2. **fred_evidence_contract (G10/G14)** — Add `backend/app/datasources/normalizers/official_macro.py`:
   - `schema_version: official_macro_evidence_v1`
   - Canonical fields per `source_capabilities.yaml` (`observation_date`, `source_fetch_id`, `content_hash`, `as_of_timestamp`, `retrieved_at`)
   - `write_fred_evidence_bundle()` / `read_fred_evidence_bundle()` used by **both** `live_pilot_phase3` capture and `rehearsal_loader._fred_staging_rows`
   - Refactor `live_evidence_bridge.materialize_fred_promote_evidence` to call normalizer only (**no** `_write_sandbox_rehearsal_gate_sidecars`)
   - Tests: live fixture `fred_live_fetch_evidence.json` + promote `fred_evidence.json` round-trip without field rename hacks.

3. **fred_fetch_port** — Implement `backend/app/datasources/fetch_ports/fred_port.py` (L2 migrate from `ops/fred_fetch_ports.py`):
   - Mock + authorized live ports behind `FetchPort` contract
   - P0 series whitelist unchanged (`DGS10`, `T10Y3M`, `VIXCLS`, `SP500`, `DFII10`)
   - Emit normalizer bundle shape directly
   - Route planner READY + DISABLED/unauthorized negative tests
   - Replay: `tests/fixtures/replay/official_macro/fred/`
   - Update `source_capabilities.fred.status` toward capped production-entry (still `enabled_by_default: false`)

4. **us_treasury_port** — `backend/app/datasources/fetch_ports/us_treasury_port.py` + normalizer hooks for yield curve + inflation expectation reference; ResourceGuard caps §7; route tests; replay fixture. Final: `READY_WITH_EVIDENCE` or ADR with `docs/adr/ADR-*-us-treasury-*.md`.

5. **sec_edgar_port** — `backend/app/datasources/fetch_ports/sec_edgar_port.py` + `normalizers/sec_edgar.py`; identity header gate; filings + Form4 operations per capability; replay under `tests/fixtures/replay/sec_edgar/`; `tests/test_sec_edgar_adapter.py`.

6. **cftc_cot_bis_world_bank_ports** — One port file per source (no `official_adapter.py` catch-all):
   - `cftc_cot_port.py` — weekly COT CSV/API capped fetch
   - `bis_port.py` — policy rate + credit-to-GDP gap reference
   - `world_bank_port.py` — low-frequency indicators
   - Each: auth/license note, ResourceGuard, route READY/DISABLED, replay fixture, evidence hashes
   - If scope blocked: **ADR_DISABLED_OUT_OF_SCOPE** with registry + route reason (no vague defer)

7. **registry_capability_route_coordinator** — Batch update (coordinator-reviewed PR):
   - `source_registry.yaml` / `source_capabilities.yaml` per-source final status
   - `source_route_contract.yaml` / `contract_coverage.yaml`
   - Manifest table: `source_id`, `old route`, `new route`, `READY|ADR`, auth decision, replay path, test command

8. **layer1_layer5_macro_smoke** — Minimal binding tests only (not R3H-05):
   - Macro/disclosure evidence shape consumable by Layer1 observation ingestion evidence builder
   - Layer5 `factual_source` provenance fields present on sample replay row
   - Do **not** claim full five-layer production-entry audit

9. **merge_gate** — `uv run pytest -q`; `uv run python scripts/loop_maintain.py`; update `tests/test_catalog.yaml` for new modules; document six-source closure in task evidence.

---

## 10. Tests / gates

Required verification:

```bash
uv run pytest tests/test_official_macro_adapters.py -q
uv run pytest tests/test_sec_edgar_adapter.py -q
uv run pytest tests/test_source_route_planner.py -q -k "fred or us_treasury or sec_edgar or cftc or bis or world_bank"
uv run pytest tests/test_source_capabilities.py -q
uv run pytest tests/test_reference_adoption_guardrails.py -q
```

### 10.1 Per-step adversarial focus

| Step    | Must prove                                                               |
| ------- | ------------------------------------------------------------------------ |
| 9.1     | No bridge sidecar required for DH; `observation_date` end-to-end         |
| 9.2     | Unauthorized FRED blocks; cap overflow blocks; mock default safe         |
| 9.3–9.5 | DISABLED route when `enabled_by_default: false`                          |
| 9.6     | No READY without replay path in registry notes                           |
| 9.7     | Layer smoke fails if evidence missing `content_hash` / `source_fetch_id` |
| 9.8     | Full suite green; no main DB mutation tests introduced                   |

Test bodies must use five-field comments per `GLOBAL_TESTING_POLICY.md`.

---

## 11. Acceptance commands

```bash
uv sync --locked
uv run pytest tests/test_official_macro_adapters.py tests/test_sec_edgar_adapter.py -q
uv run pytest tests/test_source_route_planner.py -q -k official_macro
uv run pytest -q
uv run python scripts/loop_maintain.py
uv run ruff check backend/app/datasources backend/app/datasources/fetch_ports backend/app/datasources/normalizers
```

Staged policy: see `docs/quality/staged_acceptance_policy.md` — per-step RED/GREEN in `EXECUTION_INDEX.md` §1 during Execute.

---

## 12. Completion standard

R3H-01 is done only when:

1. All six sources have documented final status (`READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`).
2. G10 closed: FRED live and promote share `official_macro_evidence_v1` without pilot-only DH sidecar.
3. `fred_port` lives under `datasources/fetch_ports/` with route + replay evidence.
4. Coordinator-reviewed registry/capability/route diff merged.
5. Layer1/Layer5 macro smoke tests pass.
6. Full pytest + loop_maintain exit 0.
7. No main DB write; no reference-project runtime import.

---

## 13. Red flags

Stop and fix if:

- Marking READY from registry note only (no adapter/replay).
- Reintroducing `live_evidence_bridge` sidecar as production gate.
- Copying OpenBB FRED provider source into backend.
- Writing rehearsal/pilot rows into `quant_monitor.duckdb`.
- Starting R3H-05 audit steps inside this card.
- Leaving `cftc_cot` / `bis` / `world_bank` as `proposed_disabled_source` without ADR.

---

## 14. reference_project

**采纳追溯 SSOT：** `R3H_01_REFERENCE_ADOPTION_AUDIT.md`（六源 L1/L2/L3 矩阵；五源 **L3** + `fred` **L2**）。Batch 索引：`R3H_REFERENCE_ADOPTION_INDEX.md`。

```yaml
reference_project:
  path: 参考项目/OpenBB/openbb_platform/providers/fred/
  qmd_target_files:
    - backend/app/datasources/fetch_ports/fred_port.py
    - backend/app/datasources/normalizers/official_macro.py
  direct_copy_allowed: false
  rewrite_required: true
  adoption_ladder: L2_copy_and_rewrite
  notes: Architecture/metadata only; keep QMD urllib fetch; no AGPL runtime.
```

---

## 15. Execute skill freeze (Plan placeholder)

| Skill                      | Binding | Step                 |
| -------------------------- | ------- | -------------------- |
| test-driven-development    | 必做    | 9.1–9.8              |
| karpathy-guidelines        | 必做    | 9.x                  |
| incremental-implementation | 必做    | post-GREEN each step |

Filled at Plan freeze into frozen card §15.
