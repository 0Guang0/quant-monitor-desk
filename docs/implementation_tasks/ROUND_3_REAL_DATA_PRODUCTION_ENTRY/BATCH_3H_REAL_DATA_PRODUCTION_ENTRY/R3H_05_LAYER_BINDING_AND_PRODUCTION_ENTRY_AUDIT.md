# R3H-05 — Layer Binding and Production Entry Audit

> **状态：** **当前 Batch 3H 唯一执行入口**（R3H-01～04 **CLOSED** @ 2026-06-28）。  
> **开放项 SSOT：** `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0.1 + 本卡 §3.1 — 须逐条 CLOSED / WARN+ADR / BLOCK 后方可 Round4。

## 1. Goal

Run the final Round3 admission gate before Round4. This task must verify that all target sources from R3H-01 through R3H-04 are closed and that Layer1–5 have real-data/evidence bindings for the declared production-entry envelope.

This card must not implement missing adapters. If an adapter or gate is missing, this card blocks Round4 or requires an ADR that narrows the product promise.

`PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` is only a coverage checklist for gap visibility; audit conclusions and evidence remain in this card and R3H-01..04 outputs.

---

## 2. QMD files to read

```text
PROJECT_IMPLEMENTATION_ROADMAP.md
docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md  # coverage checklist only
MODULE_COMPLETION_RATING.md
docs/modules/data_sources.md
docs/modules/source_route_plan.md
docs/modules/layer5_security_evidence.md
docs/modules/data_validation_and_conflict.md
specs/datasource_registry/source_registry.yaml
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
```

Also read all R3H task cards and their evidence outputs.

---

## 3. Required audit matrix

Create or update an audit artifact, for example:

```text
docs/quality/round3h_real_data_production_entry_audit.md
```

The matrix must include every target source:

```text
qmt_xtdata
baostock
akshare
cninfo
yahoo_finance
tdx_pytdx
fred
qmt_xqshare
us_treasury
sec_edgar
cftc_cot
bis
world_bank
deribit
coingecko
kalshi
polymarket
stooq
alpha_vantage
mootdx
eastmoney
sina_finance
ths_ifind
web_search
```

For each source, record:

```text
source_id
final decision: READY_WITH_EVIDENCE or ADR_DISABLED_OUT_OF_SCOPE
allowed domains
adapter/fetch port path
auth/license decision
ResourceGuard cap
route READY or DISABLED evidence
replay fixture / sandbox sample
fetch_log/content_hash/schema_hash evidence
data health result
source conflict result
Layer1/2/3/4/5 binding, if applicable
production-entry status
release limitation, if any
```

### 3.1 Cross-cutting open items（审计必查 — 对照路线图 §5.0.1）

R3H-05 **不得实现**下列项；须在 audit matrix 或 `round3h_real_data_production_entry_audit.md` 中逐条 **CLOSED / WARN+ADR / BLOCK**：

| ID                   | 检查项                                   | 证据 / 通过标准                                                                                                        |
| -------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **CAL-US**           | 美股/全球权益交易日历（非 Mon–Fri 近似） | `calendar_gap_rules` / market_bar DH 对 US 域是否仍 `calendar_authority=false`；若仍开放 → `release limitation` 或 ADR |
| **CAL-CN-TAIL**      | A 股日历 2030+ / 交易所权威              | `cn_trading_calendar.py` ponytail 注释 + 审计注记                                                                      |
| **SCHEMA-G3G4**      | G3/G4/G6 clean DDL / 分表 / PK           | 须有 schema 任务归属或 ADR 收窄；R3H-01 §8 禁止本卡实现                                                                |
| **LIVE-PROD**        | baostock/cninfo 等真网→clean 产品化      | 每源 `production-entry status`；区分 replay READY vs live 产品承诺                                                     |
| **WEB-SEARCH-LIVE**  | `web_search` 真实搜索 API                | registry READY **≠** 真网；须记 **mock stub deferred**（Grill-me Q4；`web_search_evidence_port.py` L3）                |
| **KALSHI-POLY-LIVE** | 预测市场默认真网                         | mock/replay default；live smoke env-gated；limitation 若仅结构证据                                                     |

权威索引：`PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0.1。

---

## 4. Layer gates

This card must verify that declared Round3 production-entry scope has real-data/evidence binding for:

| Layer  | Required proof                                                                     |
| ------ | ---------------------------------------------------------------------------------- |
| Layer1 | macro/axis inputs use official or ADR-approved real source path                    |
| Layer2 | cross-asset sensors use real market/validation source path or ADR-narrowed scope   |
| Layer3 | CN/industry-chain inputs use real CN source/evidence path or ADR-narrowed scope    |
| Layer4 | market structure inputs use real market source/evidence path or ADR-narrowed scope |
| Layer5 | instrument/disclosure/evidence chain has source_fetch_id/content_hash/schema_hash  |

---

## 5. Output decision

The final decision must be one of:

```text
PASS_ROUND4_REAL_DATA_READY
WARN_ROUND4_ALLOWED_WITH_NARROWED_SCOPE_ADR
BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE
```

Rules:

- PASS requires every target source either implemented with evidence or ADR-disabled, and every declared layer scope has real-data/evidence binding.
- WARN requires explicit ADR narrowing. It cannot silently defer source implementation.
- BLOCK is required if any source remains vague proposed-disabled, any READY route lacks evidence, or any declared layer scope still depends only on staged fixture.

---

## 6. Done criteria

- Audit matrix covers every source listed above.
- No target source is missing final decision.
- No source is marked READY without adapter/gate/replay/route/evidence.
- No layer production-entry claim relies only on staged fixture.
- Round4 admission decision is written and linked from roadmap or release manifest planning.
