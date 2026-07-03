# M-DATA-03 Technical Spec（Plan R2）

> **SSOT：** 本文件 + `specs/contracts/live_tier_a_evidence_v1.yaml` + `research/to-issues-slices.md`  
> **用户 AC：** `plan-revision-r2.md` §2（锁定，不得改）

## Objective

Deliver **R4 sandbox live** acceptance for all 11 Tier A sources: unified acceptance layer, normative evidence contract, full F0 + B2 post-write gates, dispatch dedup, CI regression — **no SKIP as pass**.

## Authority（优先级顺序）

1. **`research/plan-revision-r2.md` §2** — 用户锁定 AC
2. `specs/contracts/live_tier_a_evidence_v1.yaml`
3. `docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/M_DATA_03_TIER_A_LIVE.md` §5.1 R2
4. `PROJECT_IMPLEMENTATION_ROADMAP.md` §0.3.3–0.3.4
5. `specs/contracts/data_quality_rules.yaml`
6. `docs/ops/data_health_cli.md` · `specs/contracts/data_cli_contract.yaml`
7. `docs/modules/data_validation_and_conflict.md`
8. `reference-adoption-m-data-03.md`（仅 `参考项目/**`）

## ASSUMPTIONS

1. 11/11 live when keys/env available; FAIL_EXTERNAL only with merged ADR.
2. No new DDL (ADR-028 migration 015).
3. Isolated `DATA_ROOT` under `.audit-sandbox/m-data-03/`.
4. Reference adoption: L2/L3 per `plan-revision-r2.md` §4; **no runtime import** from `参考项目/**`.

## failure_class（引用 contract SSOT）

见 `live_tier_a_evidence_v1.yaml` → `failure_class_canonical`。CLI/report 用 `PASS` / `FAIL_FIXABLE` / `FAIL_EXTERNAL`；manifest `acceptance.failure_class` 用 mapped 字段值。

## Retry policy（引用 contract）

| 场景           | 行为                                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------------ |
| 网络超时       | 最多 **3** 次指数退避（1s · 2s · 4s），仍失败 → `FAIL_EXTERNAL`（须 ADR）或 `FAIL_FIXABLE`（本地 bug） |
| 可修复技术错误 | 不重试；直接 `FAIL_FIXABLE`                                                                            |
| 分类           | 按 contract `failure_class_canonical.mapping`                                                          |

## Interface Contract

### `tier_a_live_acceptance.py`

```text
tier_a_live_acceptance.py [--source-id ID] [--quick] [--data-root PATH] [--report PATH]

Exit codes:
  0 — all sources PASS or FAIL_EXTERNAL with valid ADR ref
  1 — any FAIL_FIXABLE or FAIL_EXTERNAL without ADR
  2 — invalid env (no QMD_ALLOW_LIVE_FETCH / main DB / missing KEY)

--quick — fred + baostock smoke (CI nightly)
--report — TierALiveAcceptanceReport JSON (live_tier_a_evidence_v1 acceptance_report)
```

失败时额外写出 `tier_a_live_acceptance_failure_{run_id}.json`（见 contract `failure_artifact`）；CI workflow **必须** upload 该文件。

### Per-source pipeline（SSOT · 与 plan-boot §5 一致）

1. `validate_live_acceptance_env`
2. `run_tier_a_live_incremental` via **DCP-05 ops runner**（post S-R2-DISPATCH dedup）
3. sync → clean（含于 incremental）
4. Write `live_tier_a_evidence_manifest.json` per contract
5. **B2** `DataQualityValidator.validate_table` on `clean_table` / `rule_set_id`
6. **E2** `DbInspector.inspect()` — non FAIL
7. **F0** `run_data_health_profile(health_domain, health_profile_id, ...)` — non FAIL/BLOCKED
8. Emit per-source row in acceptance report

**Forbidden:** `_run_f0_data_health` SKIP paths; `inspect_only_without_health`; `_live_sync_registry` bypass.

### F0 profiles（per source · 与 contract `source_bindings`）

| source_id                                    | health_domain      | health_profile_id     |
| -------------------------------------------- | ------------------ | --------------------- |
| baostock, mootdx, alpha_vantage              | market_bar_1d      | market_bar_p0         |
| fred, us_treasury, bis, world_bank, cftc_cot | layer1_observation | layer1_observation_p0 |
| sec_edgar                                    | us_disclosure      | disclosure_p0         |
| cninfo                                       | cn_disclosure      | disclosure_p0         |
| deribit                                      | crypto_derivative  | crypto_derivative_p0  |

### platform_source_matrix — mootdx 行模板（S-R2-DISPATCH）

```yaml
mootdx:
  source_id: mootdx
  tier: A
  live_incremental: true
  platform_matrix_source_id: mootdx # 与 contract source_bindings 一致
  notes: "R2 DISPATCH — 禁止 acceptance bypass"
```

### Official API（SDD · RED 前必读）

| source_id     | 权威 URL                                                                   |
| ------------- | -------------------------------------------------------------------------- |
| fred          | https://fred.stlouisfed.org/docs/api/fred/series_observations.html         |
| us_treasury   | https://fiscaldata.treasury.gov/api-documentation/                         |
| sec_edgar     | https://www.sec.gov/search-filings/edgar-application-programming-interface |
| cftc_cot      | https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm          |
| bis           | https://stats.bis.org/api-doc/v1                                           |
| world_bank    | https://datahelpdesk.worldbank.org/knowledgebase/articles/889392           |
| alpha_vantage | https://www.alphavantage.co/documentation/                                 |
| deribit       | https://docs.deribit.com/                                                  |
| baostock      | http://baostock.com/baostock/index.php/Python_API文档                      |
| cninfo        | 仓内 `cninfo_port.py` 头部注释                                             |
| mootdx        | 仓内 `mootdx_port.py` + pytdx 文档                                         |

`EXTERNAL-INDEX.md` §E 指向本表。

## Commands

```bash
uv run pytest -q
uv run python scripts/loop_maintain.py
QMD_ALLOW_LIVE_FETCH=1 DATA_ROOT=.audit-sandbox/m-data-03/<run> \
  uv run python scripts/tier_a_live_acceptance.py --report /tmp/tier-a-report.json
```

## Success Criteria

1. Contract `accepted` + tests per `required_tests`
2. 11-source acceptance report + failure artifact schema stable
3. F0 four profile families; no SKIP
4. B2 main validator 11/11
5. Dispatch dedup; mootdx matrix row present
6. CI nightly + workflow_dispatch + failure artifact upload
7. `uv run pytest -q` exit 0; MCR R4 per `plan-revision-r2.md` §2#9

## Open Questions

None — user grill closed 2026-07-03.
