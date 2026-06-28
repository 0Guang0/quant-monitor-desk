# R3H-05 — Layer Binding and Production Entry Audit

> **状态：** **当前 Batch 3H 唯一执行入口**（R3H-01～04 **CLOSED** @ 2026-06-28）。  
> **开放项 SSOT：** `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0.1 + 本卡 §3.1 — 须逐条 **CLOSED / WARN+ADR / BLOCK** 后方可 Round4。  
> **Registry 覆盖：** `source_registry.yaml` 全部 **25** 行（含 `openbb_provider_reference`）须有终态，不得只审 24 个业务源。  
> **参考采纳索引：** `R3H_REFERENCE_ADOPTION_INDEX.md`（四轨 L1/L2/L3 追溯；**REF-ADOPT-GATE**）。

## 1. Goal

Run the final Round3 admission gate before Round4. This task must verify that all target sources from R3H-01 through R3H-04 **plus every remaining registry row** are closed and that Layer1–5 have real-data/evidence bindings for the declared production-entry envelope.

This card must not implement missing adapters. If an adapter or gate is missing, this card blocks Round4 or requires an ADR that narrows the product promise.

`PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` is only a coverage checklist for gap visibility; audit conclusions and evidence remain in this card, `docs/quality/round3h_real_data_production_entry_audit.md`, and R3H-01..04 / Trellis archive outputs.

---

## 2. QMD files to read

```text
PROJECT_IMPLEMENTATION_ROADMAP.md
docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md  # coverage checklist only
docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_MASS_REHEARSAL_OPEN_GAPS.md
MODULE_COMPLETION_RATING.md
docs/modules/data_sources.md
docs/modules/source_route_plan.md
docs/modules/layer5_security_evidence.md
docs/modules/data_validation_and_conflict.md
docs/quality/round3h_real_data_production_entry_audit.md
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_REFERENCE_ADOPTION_INDEX.md
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_01_REFERENCE_ADOPTION_AUDIT.md
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_02_REFERENCE_ADOPTION_AUDIT.md
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_03_REFERENCE_ADOPTION_AUDIT.md
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_04_REFERENCE_ADOPTION_AUDIT.md
specs/contracts/reference_adoption_guardrails.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/datasource_service_contract.yaml
specs/contracts/data_quality_rules.yaml
specs/contracts/source_conflict_rules.yaml
specs/contracts/layer5_evidence_contract.yaml
specs/contracts/snapshot_lineage_contract.yaml
specs/contracts/resource_limits.yaml
specs/contracts/sandbox_clean_write_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_catalog.yaml
docs/adr/  # WARN 项须已有或新建 ADR
```

Also read all R3H-01..04 task cards and their evidence outputs.

### 2.1 Trellis archive evidence（四轨 — 审计输入，非重新 Execute）

```text
.trellis/tasks/archive/2026-06/06-28-round3h-r3h01-official-macro/
.trellis/tasks/archive/2026-06/06-28-round3h-r3h02-market-data/
.trellis/tasks/archive/2026-06/06-28-round3h-r3h03-cn-market/
.trellis/tasks/archive/2026-06/06-28-round3h-r3h04-prediction-web/
```

每轨至少引用：`audit.report.md`（或等效 PASS 结论）、`research/grill-me-session.md`（若存在）、`execute-evidence/9.8-full*.txt` 或 full pytest 证据。

---

## 3. Required audit matrix

Create or update:

```text
docs/quality/round3h_real_data_production_entry_audit.md
```

### 3.0 Source inventory（25 registry rows — 缺一不可）

**R3H-01..04 业务源（24）：**

```text
fred, us_treasury, sec_edgar, cftc_cot, bis, world_bank
alpha_vantage, stooq, yahoo_finance, deribit, coingecko
baostock, akshare, cninfo, tdx_pytdx, mootdx, eastmoney, sina_finance, ths_ifind, qmt_xtdata, qmt_xqshare
kalshi, polymarket, web_search
```

**Registry 元数据源（1）— 须单独一行，不得遗漏：**

```text
openbb_provider_reference
```

预期终态：`ADR_DISABLED_OUT_OF_SCOPE`（architecture/metadata reference only；`notes: no runtime adapter`）。若误标 `READY_WITH_EVIDENCE` → **BLOCK**。

For each source row, record:

```text
source_id
final_decision: READY_WITH_EVIDENCE or ADR_DISABLED_OUT_OF_SCOPE
allowed_domains
adapter/fetch_port path
auth/license decision
ResourceGuard cap
route READY or DISABLED evidence
replay fixture / sandbox sample
fetch_log/content_hash/schema_hash/source_fetch_id evidence
data health result
source conflict result
Layer1/2/3/4/5 binding, if applicable
production-entry status
release limitation, if any
```

### 3.1 Cross-cutting open items（审计必查 — 对照路线图 §5.0.1）

R3H-05 **不得实现**下列实现类缺口；须在 `round3h_real_data_production_entry_audit.md` **§7** 与 source 矩阵中逐条 **CLOSED / WARN+ADR / BLOCK**。任一交叉项留空或 `PENDING` → **BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE**。

| ID                          | 严重度 | 3G    | 检查项                                                     | 证据 / 通过标准                                                                                                                                                                         |
| --------------------------- | ------ | ----- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **REGISTRY-ORPHAN**         | 高     | —     | `openbb_provider_reference` registry 第 25 行              | 矩阵独立行；`ADR_DISABLED_OUT_OF_SCOPE`；禁止无终态                                                                                                                                     |
| **MAIN-DB-GATE**            | 高     | G8    | 主库 `quant_monitor.duckdb` denylist；禁止 pilot merge     | `canonical DB denylist` / mutation proof 测试绿；审计注记「无 pilot 数据入主库」+ 证据日期                                                                                              |
| **G14-PILOT-SIDECAR**       | 高     | G14   | baostock `--live-wire` → `live_evidence_bridge` DH sidecar | 点名 `live_evidence_bridge._write_sandbox_rehearsal_gate_sidecars`；FRED 路径已无 sidecar；baostock pilot → **WARN+limitation** 或 CLOSED+ADR                                           |
| **G16-LIVE-WIRE**           | 高     | G16   | cninfo/akshare/yahoo 未接 `--live-wire`                    | 逐源区分 replay READY vs live-wire；未接须 **release limitation**（不得 silent 当 live 产品化）                                                                                         |
| **CAL-US**                  | 高/中  | G2    | **US equity bar 域**交易日历（非 Mon–Fri）                 | 仅 `yahoo_finance` / `stooq` / `alpha_vantage` 等 **US equity bar** DH；`calendar_authority=false` → WARN+ADR。**不适用** `deribit`/`coingecko`（crypto 维持 `calendar_days` ponytail） |
| **CAL-CN-TAIL**             | 中     | G17   | A 股日历 2030+ / 交易所权威                                | `cn_trading_calendar.py` ponytail + 审计注记                                                                                                                                            |
| **SCHEMA-G3G4**             | 中     | G3G4  | clean 分表 / OHLCV / 域语义                                | 须有 schema 任务归属或 ADR 收窄 Layer 写入；本卡禁止实现 DDL                                                                                                                            |
| **CNINFO-DISCLOSURE-SHAPE** | 中     | G5    | cninfo 公告压成 `market_bar` 形                            | 审计注记偏离 + ADR 或 defer limitation；不得假装 disclosure-native                                                                                                                      |
| **G6-IDEMPOTENCY**          | 中     | G6    | `append_only` 无 PK / 重复 execute 叠行                    | ADR 归属 Batch3V 或 upsert 策略任务；审计须写明 Round4 前是否接受叠行风险                                                                                                               |
| **LIVE-PROD**               | 高/中  | G1G11 | 真网→clean **产品化**（非 pilot `--live-wire`）            | **逐源**：`baostock`, `cninfo`, `akshare`, `yahoo_finance`, `fred` 等；区分 replay/mock READY vs live 产品承诺                                                                          |
| **MACRO-LIVE-DEFER**        | 中     | —     | 官方宏观五源 mock-first live                               | `us_treasury`, `sec_edgar`, `cftc_cot`, `bis`, `world_bank` 逐源 limitation（FRED 证据契约已闭合 ≠ 全源 live 产品化）                                                                   |
| **G13-VALIDATION-ROLE**     | 中     | G13   | `validation_only` 不得冒充 primary clean-write             | `yahoo_finance` / `akshare` 矩阵行 + `test_r3h02_*` / `test_r3h03_*` primary-block 测试引用；pilot 隔离库例外须写明                                                                     |
| **WEB-SEARCH-LIVE**         | 高     | —     | `web_search` 真实搜索 API                                  | mock stub deferred（Grill-me Q4）；`web_search_evidence_port.py` L3                                                                                                                     |
| **KALSHI-POLY-LIVE**        | 高     | —     | kalshi/polymarket 默认真网                                 | mock/replay default；live env-gated；404/403 → `live_network_note` limitation                                                                                                           |
| **REF-ADOPT-GATE**          | 中     | —     | 四轨参考采纳追溯与 port 头注释一致                         | `R3H_REFERENCE_ADOPTION_INDEX.md` + `R3H_01..04_REFERENCE_ADOPTION_AUDIT.md`；§7.1 矩阵与 port 头一致；`test_reference_adoption_guardrails` 绿                                          |
| **STAGED-PILOT-SSOT**       | 中     | —     | `staged_pilot_fetch_ports` vs `fetch_ports/*` 双轨         | 产品 SSOT = `fetch_ports/*`；staged 仅 rehearsal/**延后收敛**（post-R3H-05 debt-lite）；R3H-05 审计注记，不得 silent 双实现                                                             |
| **PILOT-OPS-CALENDAR**      | 低     | G2    | `r3g03_isolated_pilot_dry_run.py` 等运维脚本自然日窗       | **非**产品 adapter 承诺；与 **CAL-US** 分开登记 limitation                                                                                                                              |

**显式不进 R3H-05 默认审计：** G7（超 cap stress）— 仅用户签字 mass-stress approval，非 Round4 前默认门禁。

### 3.1.1 CAL-US 强制裁决（禁止 silent PASS）

R3H-02 已否决在本卡做 EasyXT `TradingCalendar` L2；与全局 G2「交易日 SSOT」在 **US equity bar 域** 不完全一致。审计员**必须**在 `round3h_real_data_production_entry_audit.md` §7 **CAL-US** 行登记下列**三选一**（可组合 ③ 与 ①）：

| 选项           | 裁决                                                       | Round4 含义                               | 须产出                                                                                        |
| -------------- | ---------------------------------------------------------- | ----------------------------------------- | --------------------------------------------------------------------------------------------- |
| **① WARN+ADR** | Round4 前 US equity bar 仍 `calendar_days` / Mon–Fri proxy | 允许 narrowed scope 进入 Round4           | `docs/adr/` + registry `release_limitation`；点名 `yahoo_finance` / `stooq` / `alpha_vantage` |
| **② 债务切片** | 单列 post-R3H-05（或并行）US 日历 L2 卡                    | Round4 **BLOCK** 直至日历 CLOSED 或选 ①/③ | 新任务卡 + EasyXT `smart_data_detector` 只读拷改计划                                          |
| **③ 收窄承诺** | 声明哪些 API/Layer/域**不承诺** US 交易日对齐              | 与 ① 常并用                               | 审计矩阵 `allowed_domains` + Layer binding N/A 理由                                           |

**不适用：** `deribit` / `coingecko`（crypto 维持 `calendar_days` ponytail）。  
**分开登记：** 3G pilot 运维脚本自然日 → **PILOT-OPS-CALENDAR**（非 CAL-US 替代品）。

权威索引：`PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0.1 · `R3G_MASS_REHEARSAL_OPEN_GAPS.md` §2 · `R3H_REFERENCE_ADOPTION_INDEX.md`。

---

## 4. Layer gates

Verify declared Round3 production-entry scope has real-data/evidence binding for:

| Layer  | Required proof                                                                     |
| ------ | ---------------------------------------------------------------------------------- |
| Layer1 | macro/axis inputs use official or ADR-approved real source path                    |
| Layer2 | cross-asset sensors use real market/validation source path or ADR-narrowed scope   |
| Layer3 | CN/industry-chain inputs use real CN source/evidence path or ADR-narrowed scope    |
| Layer4 | market structure inputs use real market source/evidence path or ADR-narrowed scope |
| Layer5 | instrument/disclosure/evidence chain has source_fetch_id/content_hash/schema_hash  |

### 4.1 Binding depth boundary（避免与 G12 混淆）

| 本卡必须验证                                                                 | 本卡不要求（Round4+ / Layer 任务）                    |
| ---------------------------------------------------------------------------- | ----------------------------------------------------- |
| R3H-01..04 已交付的 **Layer smoke 测试绿**                                   | Layer1 **全量指标计算**（G12）                        |
| 声明范围内路径 **非 staged-only fixture**（有 R3H-approved source evidence） | 全市场 Layer 快照产品化                               |
| 审计模板 Layer summary 行填 **PASS / WARN+ADR / N/A**                        | 把 smoke 等同于 `R6_FULL_PRODUCTION_STABLE`（Round5） |

证据：各轨 `layer*_smoke` 步骤 + `tests/test_r3h_layer_binding_audit.py` 规划门禁。

---

## 5. Output decision

The final decision must be one of:

```text
PASS_ROUND4_REAL_DATA_READY
WARN_ROUND4_ALLOWED_WITH_NARROWED_SCOPE_ADR
BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE
```

Rules:

- PASS requires every **25** registry source rows either implemented with evidence or ADR-disabled; **§3.1 全部交叉项** CLOSED 或已记入 release limitation；every declared layer scope has smoke-passing real-data/evidence binding per §4.1.
- WARN requires explicit ADR in `docs/adr/` + registry/route sync + release limitation for every open §3.1 item and every deferred live/schema item. Cannot silently defer source implementation.
- BLOCK is required if: any source remains `PENDING_R3H_EXECUTION` or vague proposed-disabled; any READY route lacks evidence; any §3.1 row pending; **MAIN-DB-GATE** fails; any declared layer scope depends only on staged fixture without ADR.

---

## 6. Done criteria

- Audit matrix covers **all 25** `source_registry.yaml` rows including `openbb_provider_reference`.
- `round3h_real_data_production_entry_audit.md` **§7 Cross-cutting** fully populated (no pending cross-cutting IDs).
- No source marked READY without adapter/gate/replay/route/evidence/data health/source conflict where applicable.
- **G13-VALIDATION-ROLE:** validation-only sources have matrix + test citation.
- **DataSourceService / route:** in-scope READY sources routable via `DataSourceService` / `SourceRoutePlanner` — cite green tests (e.g. `test_source_route_planner.py`, `test_r3h0*_*.py`, per-source adapter tests); facade-only bypass → BLOCK.
- No layer production-entry claim relies only on staged fixture (§4.1).
- Round4 admission decision written; roadmap §9 / §10 注记已同步（§9.4）。
- WARN items have `docs/adr/` files and registry `release_limitation` notes.

---

## 7. Verification commands

```text
uv sync --locked
uv run python scripts/loop_maintain.py
uv run pytest tests/test_r3h_adapter_evidence_matrix.py tests/test_r3h_layer_binding_audit.py tests/test_r3h_source_final_decisions.py -q
uv run pytest tests/test_source_registry.py tests/test_source_capabilities.py tests/test_source_route_planner.py -q -k "r3h or denylist or validation"
uv run pytest -q
```

Audit 填完后：确认 `test_r3hAuditTemplate_marksPendingRowsAsRound4Blockers` 语义仍满足（完成态不得保留 `PENDING_R3H_EXECUTION`）。

---

## 8. Implementation steps（Execute 顺序 — 审计卡不补 adapter）

1. **boot_read** — Read §2 QMD + §2.1 四轨 Trellis 归档 + `R3G_MASS_REHEARSAL_OPEN_GAPS.md` §2。
2. **cross_cutting_draft** — 在 `round3h_real_data_production_entry_audit.md` §7 起草全部 §3.1 ID 行（可先 WARN 占位，不得留空）。
3. **source_matrix_populate** — 从四轨 audit/registry/tests 填入 25 行 source 矩阵；`openbb_provider_reference` → ADR。
4. **layer_summary** — 填 Layer1–5 summary（§4.1 深度）；引用各轨 smoke 证据。
5. **main_db_gate** — 跑 MAIN-DB-GATE 证据（denylist / 无主库写测试）。
6. **service_route_smoke** — 核对 DataSourceService/route 测试引用（§6）。
7. **adr_warn_package** — 凡 WARN：写 `docs/adr/` + 更新 registry limitation。
8. **admission_decision** — 写 §5 三态之一；BLOCK 须列阻断项清单。
9. **downstream_sync** — 执行 §9.4 下游同步。
10. **full_pytest_green** — §7 全量命令；证据写入 Trellis `execute-evidence/`（若走 Trellis）。

---

## 9. Post-audit downstream sync（PASS 或 WARN 后必做）

| 下游文件                                                                          | 动作                                                                  |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` §5 批次状态、§9 数据源表、§10 门禁            | 写入 R3H-05 决策日期 + PASS/WARN/BLOCK；更新「当前下一入口 → Round4」 |
| `docs/quality/round3h_real_data_production_entry_audit.md`                        | `R3H-05 decision` 字段最终值；消除全部 `PENDING_R3H_EXECUTION`        |
| `docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` Slice 12 | coverage checklist only — 勾选 R3H-05 audit 完成 AC                   |
| `BATCH_3H_TASK_CARD_MANIFEST.md`                                                  | Batch 3H 标 **CLOSED**（仅当 PASS 或 WARN+ADR 完整）                  |
| `R3G_MASS_REHEARSAL_OPEN_GAPS.md` §2                                              | 同步 G14/G16/G8 等 R3H-05 闭合状态                                    |
| Round4 `BATCH_04_*`                                                               | 确认 manifest 仍引用 R3H-05 决策；Round4 方可开工                     |

**BLOCK 时：** 不得改 Round4 入口为可开工；须列 repair 切片回 R3H-01..04 或 schema/ADR 任务。
