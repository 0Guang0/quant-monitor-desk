# Round 3H Real Data Production Entry Audit

> **Owner:** R3H-05 Layer Binding and Production Entry Audit  
> **Batch:** `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/`  
> **Purpose:** final audit artifact for the Round4 admission gate.  
> **Template status:** `PENDING_R3H_EXECUTION` rows are placeholders only. A completed R3H audit must replace every placeholder with `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`.

## 1. Admission decision

| Field                              | Value                                                                                                                                                                                                                     |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R3H audit run id                   | `TBD`                                                                                                                                                                                                                     |
| R3H-05 decision                    | `BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE` until proven otherwise                                                                                                                                                               |
| Allowed final decisions per source | `READY_WITH_EVIDENCE`, `ADR_DISABLED_OUT_OF_SCOPE`                                                                                                                                                                        |
| Allowed Round4 admission outputs   | `PASS_ROUND4_REAL_DATA_READY`, `WARN_ROUND4_ALLOWED_WITH_NARROWED_SCOPE_ADR`, `BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE`                                                                                                        |
| Blocking rule                      | Round4 cannot start while any of: (1) any of **25** source rows `PENDING_R3H_EXECUTION` or vague proposed-disabled; (2) any READY without evidence; (3) any **§7 cross-cutting ID** pending; (4) **MAIN-DB-GATE** failed. |

## 2. Required source audit fields

Every source row must carry these fields in the completed audit:

| Field                                         | Required meaning                                                                                               |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `source_id`                                   | Source identifier from `specs/datasource_registry/source_registry.yaml` / `source_capabilities.yaml`.          |
| `final_decision`                              | `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`. Template-only `PENDING_R3H_EXECUTION` must block Round4. |
| `allowed_domains`                             | Explicit domains approved for capped fetch/replay.                                                             |
| `adapter_fetch_port_path`                     | QMD-owned adapter/fetch port path, or ADR path if out of scope.                                                |
| `auth_license_decision`                       | Auth, entitlement, local terminal, ToS, or public-official license decision.                                   |
| `resource_guard_cap`                          | Hard cap covering request count, rows, time window, symbols, rate limit, and/or chain depth.                   |
| `route_ready_or_disabled_evidence`            | Route planner proof: READY only with evidence; otherwise DISABLED_SOURCE with ADR.                             |
| `replay_fixture_or_sandbox_sample`            | Replay fixture path or bounded sandbox sample evidence.                                                        |
| `fetch_log_content_hash_schema_hash_evidence` | Evidence for `fetch_log`, `content_hash`, `schema_hash`, and `source_fetch_id`.                                |
| `data_health_result`                          | Source-specific health check result and failure semantics.                                                     |
| `source_conflict_result`                      | Primary/validation/supplementary role decision and conflict result.                                            |
| `layer1_binding`                              | Layer 1 real-data/evidence binding, or explicit N/A rationale.                                                 |
| `layer2_binding`                              | Layer 2 real-data/evidence binding, or explicit N/A rationale.                                                 |
| `layer3_binding`                              | Layer 3 real-data/evidence binding, or explicit N/A rationale.                                                 |
| `layer4_binding`                              | Layer 4 real-data/evidence binding, or explicit N/A rationale.                                                 |
| `layer5_binding`                              | Layer 5 evidence-chain binding.                                                                                |
| `production_entry_status`                     | Production-entry posture, capped scope, or out-of-scope status.                                                |
| `release_limitation`                          | Limitation text if ADR-disabled or narrowed.                                                                   |

## 3. Source final-decision matrix template

`final_decision = PENDING_R3H_EXECUTION` is not a valid completed state. R3H-05 must return `BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE` if any row remains pending.

| R3H card | source_id                 | final_decision        | allowed_domains | adapter_fetch_port_path | auth_license_decision | resource_guard_cap | route_ready_or_disabled_evidence | replay_fixture_or_sandbox_sample | fetch_log_content_hash_schema_hash_evidence | data_health_result | source_conflict_result | layer1_binding | layer2_binding | layer3_binding | layer4_binding | layer5_binding | production_entry_status | release_limitation |
| -------- | ------------------------- | --------------------- | --------------- | ----------------------- | --------------------- | ------------------ | -------------------------------- | -------------------------------- | ------------------------------------------- | ------------------ | ---------------------- | -------------- | -------------- | -------------- | -------------- | -------------- | ----------------------- | ------------------ |
| R3H-01   | fred                      | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-01   | us_treasury               | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-01   | sec_edgar                 | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-01   | cftc_cot                  | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-01   | bis                       | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-01   | world_bank                | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-02   | alpha_vantage             | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-02   | stooq                     | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-02   | yahoo_finance             | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-02   | deribit                   | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-02   | coingecko                 | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-03   | baostock                  | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-03   | akshare                   | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-03   | cninfo                    | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-03   | tdx_pytdx                 | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-03   | mootdx                    | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-03   | eastmoney                 | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-03   | sina_finance              | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-03   | ths_ifind                 | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-03   | qmt_xtdata                | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-03   | qmt_xqshare               | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-04   | kalshi                    | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-04   | polymarket                | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3H-04   | web_search                | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | TBD            | TBD            | TBD            | TBD            | TBD            | TBD                     | TBD                |
| R3FR-05  | openbb_provider_reference | PENDING_R3H_EXECUTION | TBD             | TBD                     | TBD                   | TBD                | TBD                              | TBD                              | TBD                                         | TBD                | TBD                    | N/A            | N/A            | N/A            | N/A            | N/A            | TBD                     | TBD                |

**Registry row count:** 25. Completed audit must have zero `PENDING_R3H_EXECUTION`. Expected for `openbb_provider_reference`: `ADR_DISABLED_OUT_OF_SCOPE` (architecture reference only; no runtime adapter).

## 4. Layer1–5 binding summary template

**Depth rule (R3H-05 §4.1):** verify R3H-01..04 **smoke tests green** and paths are not staged-only; **do not** require full Layer1 metric computation (G12) before Round4.

| Layer  | Declared production-entry scope | Real-data/evidence binding required                                               | Evidence path | Result                |
| ------ | ------------------------------- | --------------------------------------------------------------------------------- | ------------- | --------------------- |
| Layer1 | TBD                             | Must bind axes/observations to real source evidence or ADR-narrow scope.          | TBD           | PENDING_R3H_EXECUTION |
| Layer2 | TBD                             | Must bind sensors/snapshots to real source evidence or ADR-narrow scope.          | TBD           | PENDING_R3H_EXECUTION |
| Layer3 | TBD                             | Must bind chains/snapshots to real source evidence or ADR-narrow scope.           | TBD           | PENDING_R3H_EXECUTION |
| Layer4 | TBD                             | Must bind market/security structures to real source evidence or ADR-narrow scope. | TBD           | PENDING_R3H_EXECUTION |
| Layer5 | TBD                             | Must bind evidence chain to fetch/content/schema/source lineage.                  | TBD           | PENDING_R3H_EXECUTION |

## 5. Required final audit outcomes

- `PASS_ROUND4_REAL_DATA_READY`: every target source is `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`, and Layer1–5 declared production-entry scope has real-data/evidence binding.
- `WARN_ROUND4_ALLOWED_WITH_NARROWED_SCOPE_ADR`: every missing source/layer capability has explicit ADR narrowing and release limitation.
- `BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE`: any source remains vague proposed-disabled or pending; any READY route lacks evidence; any declared layer scope still depends only on staged fixtures; **any §7 cross-cutting ID pending**; **MAIN-DB-GATE** failed.

## 6. DataSourceService and route smoke (R3H-05 §6)

| Check                                                | Evidence command / test                                                                                      | Result |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------ |
| READY sources routable via SourceRoutePlanner        | `tests/test_source_route_planner.py` (r3h\* cases)                                                           | TBD    |
| Per-card adapter + capability alignment              | `tests/test_r3h01_*` … `tests/test_r3h04_*` / domain adapter modules                                         | TBD    |
| DataSourceService not facade-only for in-scope READY | cite specific green test or BLOCK                                                                            | TBD    |
| validation_only primary block (G13)                  | `test_r3h02_marketRoute_validationOnlyPrimaryBlocked`, `test_r3h03_akshare_validationOnly_registryPermanent` | TBD    |

## 7. Cross-cutting open items（对照 R3H-05 §3.1 / 路线图 §5.0.1）

Every ID must be `CLOSED`, `WARN+ADR`, or `BLOCK`. Empty or `PENDING` → **BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE**.

| ID                      | 3G    | Status                | Evidence / ADR path                                       | release_limitation |
| ----------------------- | ----- | --------------------- | --------------------------------------------------------- | ------------------ |
| REGISTRY-ORPHAN         | —     | PENDING_R3H_EXECUTION | `openbb_provider_reference` matrix row                    | TBD                |
| MAIN-DB-GATE            | G8    | PENDING_R3H_EXECUTION | canonical DB denylist / no pilot merge                    | TBD                |
| G14-PILOT-SIDECAR       | G14   | PENDING_R3H_EXECUTION | `live_evidence_bridge` baostock sidecar                   | TBD                |
| G16-LIVE-WIRE           | G16   | PENDING_R3H_EXECUTION | cninfo/akshare/yahoo live-wire vs replay                  | TBD                |
| CAL-US                  | G2    | PENDING_R3H_EXECUTION | US equity bar: yahoo/stooq/alpha_vantage only             | TBD                |
| CAL-CN-TAIL             | G17   | PENDING_R3H_EXECUTION | `cn_trading_calendar` 2030+ ponytail                      | TBD                |
| SCHEMA-G3G4             | G3G4  | PENDING_R3H_EXECUTION | domain split / OHLCV DDL task or ADR                      | TBD                |
| CNINFO-DISCLOSURE-SHAPE | G5    | PENDING_R3H_EXECUTION | cninfo disclosure vs bar shape                            | TBD                |
| G6-IDEMPOTENCY          | G6    | PENDING_R3H_EXECUTION | append_only PK / upsert strategy                          | TBD                |
| LIVE-PROD               | G1G11 | PENDING_R3H_EXECUTION | per-source live→clean productization                      | TBD                |
| MACRO-LIVE-DEFER        | —     | PENDING_R3H_EXECUTION | us_treasury/sec_edgar/cftc/bis/world_bank mock-first live | TBD                |
| G13-VALIDATION-ROLE     | G13   | PENDING_R3H_EXECUTION | yahoo/akshare validation_only + route tests               | TBD                |
| WEB-SEARCH-LIVE         | —     | PENDING_R3H_EXECUTION | web_search mock stub deferred                             | TBD                |
| KALSHI-POLY-LIVE        | —     | PENDING_R3H_EXECUTION | kalshi/polymarket mock/replay default                     | TBD                |
| REF-ADOPT-GATE          | —     | PENDING_R3H_EXECUTION | `R3H_REFERENCE_ADOPTION_INDEX.md` + 四轨追溯              | TBD                |
| STAGED-PILOT-SSOT       | —     | PENDING_R3H_EXECUTION | fetch_ports SSOT; staged pilot defer post-R3H-05          | TBD                |
| PILOT-OPS-CALENDAR      | G2    | PENDING_R3H_EXECUTION | pilot 脚本自然日 vs 产品 CAL-US                           | TBD                |

### 7.1 REF-ADOPT per-source ladder（对照四轨追溯 MD — Execute 时逐行 CLOSED）

文档债 **已预填**（2026-06-28）；R3H-05 Execute 须核对 port 头注释一致，并在 `ref_adopt_gate` 列登记 **DOC_ALIGNED** 或 **MISMATCH→BLOCK**。

| source_id                 | ladder       | reference_path（或「无」）                       | QMD 目标                               | Trellis / 测试证据       | ref_adopt_gate        | release_limitation（示例）     |
| ------------------------- | ------------ | ------------------------------------------------ | -------------------------------------- | ------------------------ | --------------------- | ------------------------------ |
| fred                      | L2           | `ops/fred_fetch_ports.py`；OpenBB fred arch only | `fred_port.py` · `official_macro`      | `06-28-round3h-r3h01` A5 | PENDING_R3H_EXECUTION | G10/G14 FRED 已闭合            |
| us_treasury               | L3           | 无 1:1                                           | `us_treasury_port.py` · official_macro | r3h01 archive            | PENDING_R3H_EXECUTION | WARN: mock-first live deferred |
| sec_edgar                 | L3           | 无 1:1                                           | `sec_edgar_port.py`                    | r3h01 archive            | PENDING_R3H_EXECUTION | WARN: mock-first live deferred |
| cftc_cot                  | L3           | 无 1:1                                           | `cftc_cot_port.py`                     | r3h01 archive            | PENDING_R3H_EXECUTION | WARN: mock-first live deferred |
| bis                       | L3           | 无 1:1                                           | `bis_port.py`                          | r3h01 archive            | PENDING_R3H_EXECUTION | WARN: mock-first live deferred |
| world_bank                | L3           | 无 1:1                                           | `world_bank_port.py`                   | r3h01 archive            | PENDING_R3H_EXECUTION | WARN: mock-first live deferred |
| alpha_vantage             | L3           | 无；mock 同 coingecko 形状                       | `alpha_vantage_port.py` · market_data  | r3h02 archive            | PENDING_R3H_EXECUTION | CAL-US 见 §7 CAL-US            |
| stooq                     | L3           | 无 1:1                                           | `stooq_port.py` · validation_only      | r3h02 archive            | PENDING_R3H_EXECUTION | CAL-US 见 §7                   |
| yahoo_finance             | L2           | 3G replay fixtures                               | `yahoo_finance_port.py`                | r3h02 + 3G fixtures      | PENDING_R3H_EXECUTION | validation_only；CAL-US        |
| deribit                   | L3           | 无 1:1                                           | `deribit_port.py`                      | r3h02 archive            | PENDING_R3H_EXECUTION | crypto；不适用 US 日历         |
| coingecko                 | L3           | 无 1:1                                           | `coingecko_port.py`                    | r3h02 archive            | PENDING_R3H_EXECUTION | mock 样板；R3H-04 参照         |
| baostock                  | L2           | staged_pilot + adapter skeleton                  | `baostock_port.py`                     | r3h03 archive            | PENDING_R3H_EXECUTION | STAGED-PILOT 迁出              |
| akshare                   | L2           | adapter skeleton                                 | `akshare_port.py`                      | r3h03 archive            | PENDING_R3H_EXECUTION | validation_only 永久           |
| cninfo                    | L2           | staged_pilot + adapter                           | `cninfo_port.py`                       | r3h03 archive            | PENDING_R3H_EXECUTION | disclosure shape → §7 G5       |
| tdx_pytdx                 | L2           | EasyXT tdx_provider (R3FR-03)                    | `tdx_pytdx_port.py`                    | r3fr03 + r3h03           | PENDING_R3H_EXECUTION | disabled/raw-only 默认         |
| mootdx                    | L2           | extend tdx_pytdx                                 | `mootdx_port.py`                       | r3h03 archive            | PENDING_R3H_EXECUTION | —                              |
| eastmoney                 | L3           | 无 EasyXT 1:1                                    | `eastmoney_port.py`                    | r3h03 archive            | PENDING_R3H_EXECUTION | validation conflict            |
| sina_finance              | L3           | 无 EasyXT 1:1                                    | `sina_finance_port.py`                 | r3h03 archive            | PENDING_R3H_EXECUTION | validation conflict            |
| ths_ifind                 | L2           | qmt_xtdata auth 模式                             | `ths_ifind_port.py`                    | r3h03 archive            | PENDING_R3H_EXECUTION | auth-disabled 默认             |
| qmt_xtdata                | L2           | adapter skeleton                                 | `qmt_xtdata_port.py`                   | r3h03 archive            | PENDING_R3H_EXECUTION | license_gate DISABLED          |
| qmt_xqshare               | L2           | qmt_xtdata 模式                                  | `qmt_xqshare_port.py`                  | r3h03 archive            | PENDING_R3H_EXECUTION | —                              |
| kalshi                    | L3 + mock L2 | coingecko mock 模式                              | `kalshi_port.py`                       | r3h04 archive            | PENDING_R3H_EXECUTION | KALSHI-POLY-LIVE               |
| polymarket                | L3 + mock L2 | coingecko mock 模式                              | `polymarket_port.py`                   | r3h04 archive            | PENDING_R3H_EXECUTION | KALSHI-POLY-LIVE               |
| web_search                | L3           | OpenBB widget arch only                          | `web_search_evidence_port.py`          | r3h04 archive            | PENDING_R3H_EXECUTION | WEB-SEARCH-LIVE deferred       |
| openbb_provider_reference | L1           | OpenBB providers catalog                         | registry metadata only                 | R3FR-05                  | PENDING_R3H_EXECUTION | ADR_DISABLED_OUT_OF_SCOPE      |

追溯 SSOT：`R3H_01..04_REFERENCE_ADOPTION_AUDIT.md` · `R3H_REFERENCE_ADOPTION_INDEX.md`。

## 8. Post-audit downstream sync checklist

- [ ] `R3H_REFERENCE_ADOPTION_INDEX.md` / `R3H_01..04_REFERENCE_ADOPTION_AUDIT.md` synced；§7.1 矩阵 `ref_adopt_gate` 无 MISMATCH
- [ ] `PROJECT_IMPLEMENTATION_ROADMAP.md` §5 / §9 / §10 updated with R3H-05 decision
- [ ] `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` Slice 12 AC checked
- [ ] `BATCH_3H_TASK_CARD_MANIFEST.md` Batch 3H CLOSED (PASS or WARN+ADR only)
- [ ] `R3G_MASS_REHEARSAL_OPEN_GAPS.md` §2 status columns synced
- [ ] Round4 manifest gate satisfied (`PASS_ROUND4_*` or `WARN_ROUND4_*`)
- [ ] WARN items: `docs/adr/` + registry `release_limitation` notes

## 9. Release-manifest carry-forward fields

Batch05 release manifests must carry forward these 3H fields:

- `source_id`
- `final_decision`
- `READY_WITH_EVIDENCE`
- `ADR_DISABLED_OUT_OF_SCOPE`
- `DISABLED_SOURCE`
- `route_ready_or_disabled_evidence`
- `production_entry_status`
- `release_limitation`
