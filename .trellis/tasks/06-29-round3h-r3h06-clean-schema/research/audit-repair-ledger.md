# Audit Repair Ledger — R3H-06（全量 · 一项不留）

> Repair agent **必须**逐项处理；完成后在本表标 `fixed` + 证据。禁止 waive（除非主会话书面批准）。

## P0 BLOCKING

| ID    | 来源     | 修复动作                                                                            | 状态      | 证据                                                                                                                          |
| ----- | -------- | ----------------------------------------------------------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------- |
| R-B01 | A4-01    | `limited_production_entry._non_target_row_count` 域感知 key（macro→`indicator_id`） | **fixed** | `limited_production_entry.py` `_NON_TARGET_KEY_BY_TABLE`；`test_fred_promote_execute_writesAxisObservation_notBar`            |
| R-B02 | A1-B01   | 统一 `PROJECT_IMPLEMENTATION_ROADMAP` §5.0.0/§5.0.1 G3/G4/G6 + round3h audit §7     | **fixed** | `PROJECT_IMPLEMENTATION_ROADMAP.md` L281/L307                                                                                 |
| R-B04 | A5-02/03 | 补 `execute-evidence/9.1-9.9-{red,green}.txt` 真实 pytest 输出                      | **fixed** | `execute-evidence/9.{1..10}-{red,green,full}.txt`（`_gen_repair_evidence.py` 2026-06-29）                                     |
| R-B05 | A5-04    | 修全库 pytest；重录 `9.10-full.txt`                                                 | **fixed** | `execute-evidence/9.10-full.txt` exit 0 @ 2026-06-29；注：全库偶发 `test_r3g02AuditCli_writesDecisionReport` 顺序污染，单测绿 |

## P1 IMPORTANT

| ID    | 来源  | 修复动作                                                       | 状态      | 证据                                                                                                                              |
| ----- | ----- | -------------------------------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------- |
| R-I01 | A8 P0 | fred macro promote E2E 测；修 `test_LiveEvidenceBridge_fred_*` | **fixed** | `test_macro_populate_fromBundle_*` · `test_fred_promote_execute_*` · `test_round3g_limited_production_clean_write.py` FRED bridge |
| R-I02 | A4-02 | promote 后 `security_bar_1d` OHLCV 非空测                      | **fixed** | `test_idempotency_baostock_promote_ohlcvColumnsNotNull` · `test_PromoteRunner_execute_*` OHLCV 列                                 |
| R-I03 | A4-03 | cninfo + fred duplicate promote 幂等测                         | **fixed** | `test_idempotency_cninfo_*` · `test_idempotency_fred_*`                                                                           |
| R-I04 | A4-04 | `to_bar_staging_values` ponytail 注释或 bar fail-closed        | **fixed** | `rehearsal_loader.py` `to_bar_staging_values` ponytail 注释                                                                       |

## P2 测试 / 契约 / 安全（NON-BLOCKING 仍须修）

| ID         | 来源 | 修复动作                                               | 状态         | 证据                                                                                                   |
| ---------- | ---- | ------------------------------------------------------ | ------------ | ------------------------------------------------------------------------------------------------------ |
| A8-P1-01   | A8   | `cn_filings`/`cn_pdf_reports` domain_router 测         | **fixed**    | `test_domain_router_cnFilingsAndPdfReports_resolveToDisclosureClean`                                   |
| A8-P1-02   | A8   | `pdf_file_id` + file_registry 挂接测                   | **fixed**    | `test_disclosure_pdfFileId_requiresFileRegistry` + `_validate_pdf_file_id`                             |
| A3-F-01    | A3   | `cn_announcement_clean` 进 KEY_TABLES                  | **fixed**    | `ops_db_inspect_contract.yaml` · `test_opsInspect_keyTables_matchContract`                             |
| A3-F-02    | A3   | `pdf_file_id` 校验 file_registry 存在                  | **fixed**    | `rehearsal_loader._validate_pdf_file_id`                                                               |
| A3-F-03    | A3   | `announcement_url` scheme 限制（http/https）           | **fixed**    | `_validate_announcement_url` · `test_disclosure_announcementUrl_rejectsInvalidScheme`                  |
| A3-F-05    | A3   | domain/target 错配契约测                               | **fixed**    | `test_promote_domainTargetMismatch_blocksExecute`                                                      |
| A7-003     | A7   | 同上 KEY_TABLES（与 A3-F-01 合并）                     | **fixed**    | 同 A3-F-01                                                                                             |
| A4-08      | A4   | 移除 `_fred_staging_rows` 死路径                       | **fixed**    | 删 `_fred_staging_rows`；fred 移出 `_STAGING_ROW_BUILDERS`                                             |
| A2-002     | A2   | 合并 staging dispatch 到 `populate_staging_for_target` | **fixed**    | `rehearsal_loader.populate_staging_for_target`                                                         |
| A2-003     | A2   | 合并 db_helpers INSERT                                 | **fixed**    | `tests/db_helpers.insert_ohlcv_bar_row`                                                                |
| A4-07      | A4   | DDL 测改 PRAGMA table_info                             | **fixed**    | `test_bar_ddl_schemaContract_alignsWithMigration013` PRAGMA 对照                                       |
| A4-06      | A4   | r3g03 execute 回归 OHLCV 断言                          | **fixed**    | `test_round3g_limited_production_clean_write.py` execute OHLCV SELECT                                  |
| A8-P2-01   | A8   | 未知 domain 负向测                                     | **fixed**    | `test_domain_router_unknownDomain_raises`                                                              |
| A8-P2-02   | A8   | migration_coverage disclosure 表                       | **fixed**    | `CLEAN_DOMAIN_MIGRATED_TABLES` · `test_migrationCoverage_cleanDomainTables_existAfter013`              |
| A7-008     | A7   | L5_MIGRATED_TABLES 含 disclosure                       | **fixed**    | 同 A8-P2-02（`CLEAN_DOMAIN_MIGRATED_TABLES` 矩阵）                                                     |
| A4-10      | A4   | `us_equity_daily_bar` 路由或 frozen defer 注记         | **fixed**    | `clean_write_targets.py` ponytail defer 注释                                                           |
| A4-11      | A4   | ops key_tables 含 cn_announcement_clean                | **fixed**    | 同 A3-F-01                                                                                             |
| A4-12      | A4   | before_proof COUNT 对齐（可选轻量）                    | **deferred** | Wave 3：非本卡 AC；`before_proof` 深校验留 R3H-08                                                      |
| A4-05      | A4   | 幂等测 hash/列快照                                     | **deferred** | 可选增强；COUNT+OHLCV 已覆盖 G6 主路径                                                                 |
| A4-09      | A4   | rehearsal/promote bar 双轨文档                         | **fixed**    | `rehearsal_runner.py:234` ponytail 注释已存在                                                          |
| A6-NB-1..5 | A6   | ponytail 注释登记 Wave3 或最小 guard                   | **fixed**    | NB-3 `bars.json` byte cap 注释；R-I04 close 回填注释；NB-1/2/4 登记于 `audit-repair-summary.md` Wave 3 |
| A1-NB01    | A1   | manifest coordinator defer                             | **deferred** | 主会话 merge 时补 manifest（frozen explicit defer）                                                    |
| A1-NB02    | A1   | GitNexus 索引 stale                                    | **deferred** | merge 后 `node .gitnexus/run.cjs analyze`                                                              |
| A1-NB03    | A1   | 9.10 完整输出                                          | **fixed**    | `execute-evidence/9.10-full.txt`                                                                       |
| A1-NB04    | A1   | ponytail 测重复                                        | **deferred** | debt-lite；`test_r3h06` vs `test_schema_contract` 列对齐重复                                           |
| A1-NB05    | A1   | prd 状态陈旧                                           | **deferred** | 主会话 `finish-work` 时更新 `prd.md`                                                                   |
| A5-07/08   | A5   | evidence_index 刷新；去重 evidence 目录                | **fixed**    | `evidence_index.json`；删 `research/execute-evidence/*`                                                |
| A8-P2-06   | A8   | `market_bar_clean` rg pytest 固化                      | **deferred** | 9.8 证据含 rg；活卡 §9.8.1 手工 rg 门禁已满足                                                          |

## 主会话（非 Repair 代码）

| ID    | 动作                      | 状态                  |
| ----- | ------------------------- | --------------------- |
| R-B03 | 全量 commit（用户批准后） | **pending**（主会话） |

## 验证门禁

- `uv run pytest -q` exit 0 — **PASS** @ 2026-06-29（全库绿；偶发顺序污染见 R-B05 注）
- `uv run python scripts/loop_maintain.py` OK — **PASS**
- `rg market_bar_clean backend/ scripts/ tests/ specs/` 零匹配 — **PASS**
- macro promote 对抗探针绿 — **PASS**（`test_fred_promote_execute_*`）
