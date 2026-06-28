# Audit A8 — Test Gap Report · R3H-06 Clean Schema

> **维度：** A8（测试矩阵 / 对抗性边界）  
> **任务：** `06-29-round3h-r3h06-clean-schema`  
> **权威：** `agents/audit-adversarial-authority.md` · 活卡 `frozen/R3H_06_CLEAN_SCHEMA.md` · `AUDIT.plan.md` §1 A8  
> **审计员：** test-engineer subagent  
> **日期：** 2026-06-29

---

## A8 命令执行记录

```bash
uv run pytest tests/test_r3h06_clean_schema.py \
  tests/test_round3g_limited_production_clean_write.py \
  tests/test_migration_coverage.py \
  -q --basetemp=.audit-sandbox/pytest
```

| 项                         | 结果                                                                                                                             |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **退出码**                 | `0`                                                                                                                              |
| **用例数**                 | **65**（`test_r3h06_clean_schema.py` 12 · `test_round3g_limited_production_clean_write.py` 46 · `test_migration_coverage.py` 7） |
| **耗时**                   | ~4.4s（二次 `-v` 复跑：65 passed in 4.40s）                                                                                      |
| **环境**                   | `audit-sandbox` basetemp（`--basetemp=.audit-sandbox/pytest`）                                                                   |
| **AUDIT.plan A8 通过条件** | 全绿 — **满足**                                                                                                                  |

> **说明：** A8 命令范围内全绿，但对抗性审计不以「命令绿」为完备上限（见权威层级第三级 vs 第一级任务卡 Red Flags）。

---

## 五字段 docstring 合规

| 检查项                                                        | 结果                                                  |
| ------------------------------------------------------------- | ----------------------------------------------------- |
| A8 三文件 `test_*` 函数数                                     | 61 个函数 + 4 条 parametrized case = **65 collected** |
| 五字段（覆盖范围 / 测试对象 / 目的·目标 / 验证点 / 失败含义） | **0 缺失**（AST 扫描三文件）                          |
| `testing-guidelines` 弱断言门禁                               | 见下文「弱断言 / happy path」                         |

**结论：** 形式合规 **PASS**；语义强度与 AC 对齐仍有缺口（见矩阵表）。

---

## 测试矩阵 Gap 表

对照活卡 §9 步骤、§10 测试要求、§13 Red Flags、`AUDIT.plan.md` §3 §5.0.1 交叉项。

| ID              | 活卡 AC / Step                      | 计划内期望行为                                                     | A8 范围内现有测                                                                                               | 覆盖       | Gap 摘要                                                                                                        |
| --------------- | ----------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------- |
| G3-G4-BAR       | 9.1 · SCHEMA-G3G4                   | `instrument_registry` + `security_bar_1d` PK 含 `adjustment_type`  | `test_bar_ddl_migration013_createsBarTables` · `test_bar_ddl_schemaContract_*` · `test_migrationCoverage_l5*` | **部分**   | 未断言 `security_bar_1d` **OHLCV+amount 列存在**（仅 PK）；未测 promote 后 bar 行 **OHLCV 值**                  |
| G4-OHLCV        | 9.3 · 9.14                          | staging + promote 携带 open/high/low/close/volume/amount           | `test_ohlcv_stgFoundationSmoke_*` · `test_ohlcv_populateStaging_*`                                            | **部分**   | staging 列存在性有；`amount` 未列入断言；`test_PromoteRunner_execute_*`（回归）**只验 close**，不验 OHLCV       |
| CNINFO-SHAPE    | 9.2 · 9.4 · CNINFO-DISCLOSURE-SHAPE | `cn_announcement_clean` §6.1 列 + staging 对齐                     | `test_disclosure_ddl_*` · `test_stg_disclosure_populate_*`                                                    | **部分**   | DDL/capabilities 子集有；**`pdf_file_id` 指针挂接**无行为测；`announcement_type` 可空路径未验                   |
| CNINFO-NO-BAR   | 9.6 · Red Flag                      | cninfo promote 不写 `security_bar_1d`                              | `test_cninfo_no_bar_promote_leavesSecurityBar1dEmpty`                                                         | **是**     | 负向 E2E 充分                                                                                                   |
| DOMAIN-ROUTER   | 9.5                                 | bar / disclosure / macro 三域分表 + `upsert_by_pk`                 | `test_domain_router_resolvesThreeDomains`                                                                     | **部分**   | 每域只测 **1 个代表 domain**；**`cn_filings` / `cn_pdf_reports`** 未单独断言（实现已注册于 `METADATA_DOMAINS`） |
| MACRO-MAPPER    | 9.5b                                | fred bundle → `axis_observation` 行 + `populate_macro_from_bundle` | `test_domain_router`（仅路由表名）                                                                            | **否**     | **`populate_macro_from_bundle` 全库 0 引用**；无 promote execute 写入 `axis_observation` 的 E2E                 |
| G6-IDEMPOTENCY  | 9.7                                 | 三域重复 promote 行数不增长                                        | `test_idempotency_duplicatePromote_rowCountStable`（baostock only）                                           | **部分**   | 仅 **bar 域**；cninfo / fred **幂等未测**                                                                       |
| PILOT-COMPAT    | 9.8 · `market_bar_clean` rg         | 实现路径零 `market_bar_clean`                                      | **A8 范围无**                                                                                                 | **未知**   | 无 dedicated pytest；需依赖手工 `rg`（活卡 9.8.1）                                                              |
| DOCS-013/014    | 9.9                                 | `MIGRATION_COVERAGE` + migration 矩阵                              | `test_migrationCoverage_*`                                                                                    | **部分**   | `L5_MIGRATED_TABLES` 仅含 bar 两表；**`cn_announcement_clean` / `stg_*` 不在矩阵常量**                          |
| SCHEMA-CONTRACT | §10 · 9.1                           | `test_schema_contract` 子集                                        | **不在 A8 命令**                                                                                              | **范围外** | `test_cleanDomainMigration013Columns_existInSchemaContract` 存在但未纳入 A8 复跑                                |
| R3G-REGRESSION  | §10 回归                            | limited production 四门链                                          | `test_round3g_limited_production_clean_write.py` 46 条                                                        | **是**     | 契约负向丰富；与 R3H-06 三域正交                                                                                |

### 弱断言 / 仅 happy path（A8 范围内）

| 测                                                                               | 问题                                                                                                                                                                 | 严重度   |
| -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `test_r3h06_bootShell_moduleLoads`                                               | 仅 `assert "test_r3h06" in mod.__name__`，无业务行为                                                                                                                 | Low      |
| `test_ohlcv_populateStaging_passesAdjustmentType`                                | `open/high/low` 只断言 `is not None`，不验数值；**volume/amount 未查**                                                                                               | Medium   |
| `test_stg_disclosure_populate_mapsFilingIdToAnnouncementId`                      | 只验 `announcement_id` 非空 + `metadata_only`；未验 `data_domain` 字段                                                                                               | Medium   |
| `test_domain_router_resolvesThreeDomains`                                        | 未测 `resolve_clean_write_target` 对未知 domain 抛 `CleanWriteTargetError`                                                                                           | Medium   |
| `test_LiveEvidenceBridge_fred_materializesMultiSeriesObservations`（回归文件内） | 走 **`staging_rows_from_bundle` → `_fred_staging_rows`（bar 形 `StagingRow`）**，**非** `populate_macro_from_bundle` / `axis_observation` 形；与 9.5b 目标路径不一致 | **High** |

---

## 计划外发现

> 已对抗搜索：实现代码、`tests/` 全库 grep、`populate_macro_from_bundle`、`pdf_file_id`、`cn_filings`、`market_bar_clean`。

| #   | 发现                                                          | 证据                                                                                                                                                                                          | 分类                      |
| --- | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| P1  | **`populate_macro_from_bundle` 零测试引用**                   | `rg populate_macro_from_bundle tests/` → 无匹配；实现于 `rehearsal_loader.py:462`                                                                                                             | **计划外 · 覆盖空洞**     |
| P2  | **FRED 回归测仍验证 bar 形 staging**                          | `test_LiveEvidenceBridge_fred_*` 用 `staging_rows_from_bundle`；`_fred_staging_rows` 产出 `trade_date/close` 的 `StagingRow`（`rehearsal_loader.py:222-253`），与 R3H-06 macro clean 路径分叉 | **计划外 · 假绿风险**     |
| P3  | **`stg_axis_observation_smoke` 无存在性/列对齐测**            | 013 已建表（`MIGRATION_COVERAGE.md` §Round 3H）；A8 无 PRAGMA/列序断言                                                                                                                        | **计划外**                |
| P4  | **`cn_announcement_clean` PK 行为未单测**                     | DDL 有 `PRIMARY KEY (announcement_id)`；无 upsert 冲突/重复 `announcement_id` 披露域测                                                                                                        | **计划外**                |
| P5  | **`test_migration_coverage` L5 常量未含 disclosure 表**       | `L5_MIGRATED_TABLES = {instrument_registry, security_bar_1d}`；文档已标 `cn_announcement_clean` DONE                                                                                          | **计划外 · 文档/测漂移**  |
| P6  | **活卡 9.8.1 `market_bar_clean` rg 门禁无 pytest**            | `tests/` 无 `market_bar_clean` 字符串；依赖人工 rg                                                                                                                                            | **计划外**                |
| P7  | **A8 命令未含 `test_schema_contract` / `test_write_manager`** | 活卡 §10 / §11 验收命令包含；A8 仅三文件                                                                                                                                                      | **计划外 · 审计范围偏窄** |

---

## 全部发现项汇总

| 优先级            | 分类      | 发现                                               | 建议新增测（概要）                                                                                                                                                                                                                                                   | 判定                                                                                               |
| ----------------- | --------- | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **P0 · Critical** | AC 缺口   | **fred → `axis_observation` promote E2E 缺失**     | `test_macro_populate_fromBundle_writesAxisObservationStaging` + `test_fred_promote_execute_writesAxisObservation_notBar`（audit-sandbox DB，`run_limited_production_entry` execute，断言 `axis_observation` 行数/indicator_id/raw_value；`security_bar_1d` COUNT=0） | **NON-BLOCKING**（A8 命令已绿；活卡 §12 要求全库 pytest + 对抗零 BLOCKING — 交主会话裁决是否升格） |
| **P0 · Critical** | 假绿风险  | FRED bridge 测走 bar 形 `staging_rows_from_bundle` | 将 `test_LiveEvidenceBridge_fred_*` 改为断言 `populate_macro_from_bundle` + `AXIS_OBSERVATION_DDL_COLUMNS`；或新增并行测并 deprecate 旧断言                                                                                                                          | **NON-BLOCKING**                                                                                   |
| **P1 · High**     | 域路由    | `cn_filings` / `cn_pdf_reports` 未在 R3H-06 测断言 | `test_domain_router_cnFilingsAndPdfReports_resolveToDisclosureClean`                                                                                                                                                                                                 | **NON-BLOCKING**                                                                                   |
| **P1 · High**     | §6.1 指针 | **`pdf_file_id` 可挂接**无测（活卡 L141）          | fixture 含 `file_registry` 行 + disclosure row `pdf_file_id` + `content_status='pdf_registered'` promote 后 SELECT 验证                                                                                                                                              | **NON-BLOCKING**                                                                                   |
| **P1 · High**     | G6 幂等   | 仅 baostock 幂等                                   | `test_idempotency_cninfo_duplicatePromote_rowCountStable` · `test_idempotency_fred_duplicatePromote_rowCountStable`                                                                                                                                                  | **NON-BLOCKING**                                                                                   |
| **P2 · Medium**   | OHLCV     | promote execute 不验 OHLCV 值                      | 扩展 `test_PromoteRunner_execute_*` 或 R3H-06 测：断言 open/high/low/volume/amount 非 NULL 且与 fixture 一致                                                                                                                                                         | **NON-BLOCKING**                                                                                   |
| **P2 · Medium**   | 负向边界  | 未知 domain / 错误 staging 表                      | `test_domain_router_unknownDomain_raises` · `test_populate_macro_emptyEvidence_raises`                                                                                                                                                                               | **NON-BLOCKING**                                                                                   |
| **P2 · Medium**   | 矩阵      | migration_coverage 缺 disclosure                   | 扩展 `L5_MIGRATED_TABLES` 或新增 `CLEAN_DOMAIN_TABLES` 常量测                                                                                                                                                                                                        | **NON-BLOCKING**                                                                                   |
| **P3 · Low**      | 弱断言    | boot shell / OHLCV 弱非空断言                      | 加强 `test_ohlcv_populateStaging` 数值断言；boot 测可合并入 9.1                                                                                                                                                                                                      | **NON-BLOCKING**                                                                                   |
| **P3 · Low**      | 审计范围  | A8 未跑 schema_contract / write_manager            | AUDIT.plan 可考虑扩命令或注明「A8 子集 + 全库 gate」                                                                                                                                                                                                                 | **信息性**                                                                                         |

### Red Flags 对照（§13）

| Red Flag                            | A8 能否拦住                                                                  |
| ----------------------------------- | ---------------------------------------------------------------------------- |
| 三源同写 `market_bar_clean`         | **不能**（无 rg/pytest 门禁在 A8 范围）                                      |
| cninfo 用 bar 形 `trade_date+close` | **部分**（9.6 负向有；fred 旧 staging 路径仍 bar 形）                        |
| 仅 close 无 OHLCV                   | **部分**（DDL/staging 列有；promote 值未验）                                 |
| `append_only` 叠行                  | **部分**（baostock 幂等有；披露/宏观幂等无）                                 |
| 宣称主库 promote                    | **能**（`test_PromoteRunner_refusesCanonicalProductionDbPath` 在 A8 回归内） |

---

## A8 维度结论

| 项                     | 结论                                                                                                                                                             |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **AUDIT.plan A8 命令** | **PASS**（65/65 绿）                                                                                                                                             |
| **五字段 docstring**   | **PASS**（0 缺失）                                                                                                                                               |
| **活卡 AC 语义覆盖**   | **PASS_WITH_GAPS** — bar DDL、cninfo 非 bar、baostock 幂等、域路由表名已覆盖；**macro promote E2E、`pdf_file_id`、cn_filings 域、三域幂等、OHLCV 值级断言** 不足 |
| **对抗性 BLOCKING**    | **0 项硬性 BLOCKING**（测试缺口均为 NON-BLOCKING；P0 项建议主会话在 §12「Audit 零 BLOCKING」裁决时重点复核）                                                     |
| **建议**               | 合并前至少补 **P0 macro E2E** + 修正 **P2 FRED bridge 路径**；其余 P1/P2 可记入 PASS_WITH_FIXES 跟进                                                             |

---

## 参考文件

- `tests/test_r3h06_clean_schema.py` — R3H-06 主测（12）
- `tests/test_round3g_limited_production_clean_write.py` — R3G-03 回归（46）
- `tests/test_migration_coverage.py` — 矩阵门禁（7）
- `backend/app/ops/sandbox_clean_write/clean_write_targets.py` — 域路由 SSOT
- `backend/app/ops/sandbox_clean_write/rehearsal_loader.py` — `populate_macro_from_bundle` / `_fred_staging_rows`
- `frozen/R3H_06_CLEAN_SCHEMA.md` §9–§13
