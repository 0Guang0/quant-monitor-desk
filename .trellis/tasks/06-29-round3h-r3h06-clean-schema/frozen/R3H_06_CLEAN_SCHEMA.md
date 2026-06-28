<!-- FROZEN: Plan protocol v4 · do not edit · source: docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_06_CLEAN_SCHEMA.md · frozen_at: 2026-06-28T17:37:56Z -->

# R3H-06 — Clean Schema（Wave 1 · PASS 收口）

## 1. 任务目标

闭合 Round4 PASS 路径 **Wave 1**：交付正式 **clean 域分表 DDL**、**OHLCV 完整列**、**cninfo 公告原生形**、**PK + upsert 幂等**；解除 Wave 3（R3H-08 live 产品化）写 clean 的 schema 阻塞。

闭合路线图 §5.0.1 交叉项：**SCHEMA-G3G4**、**CNINFO-DISCLOSURE-SHAPE**、**G6-IDEMPOTENCY**（与 Batch 3V write_mode 底座衔接）。

### 1.1 Plan 架构决策（2a brainstorm + 3 grill-me · 已内联）

| 选项                                                 | 结论                                             |
| ---------------------------------------------------- | ------------------------------------------------ |
| A. 继续 `market_bar_clean` CTAS 无 PK                | **否决** — G3/G4/G6 未闭合                       |
| B. 三域分表：bar / disclosure / macro                | **采纳** — 对齐预演 gap §3                       |
| C. 新建 macro 表 duplicate `axis_observation`        | **否决** — migration 011 已有                    |
| D. 本卡写主库 `quant_monitor.duckdb`                 | **否决** — 仅 DDL + 隔离库/测试库验证            |
| E. 并行改 R3H-08 live fetch                          | **否决** — Wave 3 专属                           |
| F. `security_bar_daily` 重命名替代 `security_bar_1d` | **否决** — `specs/schema/schema.sql` 为 DDL SSOT |

| 三域落表（PASS 最小集）      | 表                                    | 写入模式       |
| ---------------------------- | ------------------------------------- | -------------- |
| 日线 bar（baostock/yahoo/…） | `security_bar_1d`                     | `upsert_by_pk` |
| cninfo 公告元数据            | `cn_announcement_clean`（新增契约表） | `upsert_by_pk` |
| 宏观序列（fred 等）          | `axis_observation`（011 已迁移）      | `upsert_by_pk` |

| grill 锁定项    | 决定                                                                                    |
| --------------- | --------------------------------------------------------------------------------------- |
| DDL 独占        | **仅 R3H-06** 可新增 migration；Wave 2+ 禁止改 schema                                   |
| 主库            | **禁止**默认写 `quant_monitor.duckdb`；测试用 temp/pilot DB                             |
| pilot 兼容      | **无 VIEW** @ 用户 2026-06-29 — 删除 `market_bar_clean`；实现路径统一 `security_bar_1d` |
| cninfo          | **禁止** bar 形 clean；`filing_id`→`announcement_id` 归一化                             |
| OHLCV           | bar 含 open/high/low/close/volume/amount + `adjustment_type`                            |
| G6              | promote **`upsert_by_pk`** + 域正确 PK；禁 `append_only` 叠行                           |
| cninfo 列       | §6.1 metadata + 指针 + `content_status`                                                 |
| Layer3/4/5 大表 | **不在本卡** — 仍 DEFERRED Round 3F                                                     |
| R3H-05          | **禁止** — 本卡不做 PASS 审计                                                           |

### 2.8 Plan vs Execute gates

1. **Wave 0 Batch 3V CLOSED** @ 2026-06-28（trust 底座 + write_mode）。
2. **R3H-01～04 CLOSED** — adapter 已交付；本卡只补 **clean 形态**。
3. **No main DB writes** — migration 在测试/pilot 路径验证；不 promote 进 `quant_monitor.duckdb`。
4. **单轨串行** — 建议分支 `feature/round3h-r3h06-clean-schema`；禁止与 R3H-07/08 并行改 migration。
5. **R3H-05 forbidden** — 审计留 Wave 4。

---

## 2. 预期结果

1. migration `013_clean_domain_tables.sql`（及必要 follow-up）创建 `instrument_registry`、`security_bar_1d`、`cn_announcement_clean`。
2. `specs/schema/schema.sql` 登记 `cn_announcement_clean`（与 capabilities 字段对齐）。
3. sandbox promote / rehearsal 路径按 **domain** 路由到正确 clean 表（非三源同表）。
4. bar 写入携带 **OHLCV**；cninfo 写入 **announcement 字段**；fred 宏观写入 **axis_observation**。
5. `upsert_by_pk` 幂等：重复 promote/execute **行数不增长**（G6）。
6. `docs/schema/MIGRATION_COVERAGE.md` 更新；`test_migration_coverage.py` / 新测绿。
7. 全库 `uv run pytest -q` 绿。

---

## 3. 输入文件

```text
PROJECT_IMPLEMENTATION_ROADMAP.md §5.0.1 / §5.0.3
R3H_PASS_EXECUTION_PLAN.md
R3G_MASS_REHEARSAL_OPEN_GAPS.md §2 G3/G4/G5/G6
docs/schema/MIGRATION_COVERAGE.md
specs/schema/schema.sql
specs/datasource_registry/source_capabilities.yaml（cn_announcements fields）
specs/contracts/sandbox_clean_write_contract.yaml
docs/modules/duckdb_and_parquet.md §4–§5
docs/architecture/04_data_architecture.md
docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md
docs/implementation_tasks/GLOBAL_TESTING_POLICY.md
docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md
BATCH_3H_HARDENING_RULES.md
```

---

## 4. 相关代码文件

```text
backend/app/db/migrations/013_clean_domain_tables.sql（新建）
backend/app/db/migrations/014_stg_bar_ohlcv.sql（新建，扩 `stg_foundation_smoke` OHLCV 列）
backend/app/ops/sandbox_clean_write/clean_write_targets.py（新建：domain→表/write_mode/PK 路由 SSOT）
specs/schema/schema.sql
docs/schema/MIGRATION_COVERAGE.md
backend/app/ops/sandbox_clean_write/rehearsal_loader.py
backend/app/ops/sandbox_clean_write/limited_production_entry.py
backend/app/ops/sandbox_clean_write/rehearsal_runner.py
backend/app/sync/runners.py（_write_clean 域路由，若需）
backend/app/db/write_manager.py（只读对照 upsert 语义）
tests/test_r3h06_clean_schema.py（新建）
tests/test_schema_contract.py
tests/test_migration_coverage.py
tests/test_round3g_limited_production_clean_write.py（回归）
scripts/r3g03_isolated_pilot_dry_run.py（目标表常量）
```

---

## 5. 现有模式 / 参考

- **DDL SSOT：** `specs/schema/schema.sql`；`security_bar_1d` 已设计含 OHLCV + PK。
- **宏观：** `axis_observation` @ migration `011_layer1_tables.sql`。
- **写路径：** `WriteManager` + `DbValidationGate`；`append_only` / `upsert_by_pk`（Batch 3V C01）。
- **预演偏离：** `research/r3g03_mass_rehearsal_gap_analysis.md` §3 — 三源同 `market_bar_clean`。
- **B3V-L5R：** `instrument_registry` / `security_bar_1d` 标 DEFERRED → **本卡升为 owner**。

---

## 6. 技术约束

- Python `uv run`；DuckDB migration runner 现有机制。
- 遵守 `reference_adoption_guardrails.yaml` — 禁止运行时 import `参考项目/**`。
- 新表列名与 `source_capabilities.yaml` / `layer5_evidence_contract.yaml` 对齐（bar 域）。
- cninfo：**clean 表只存元数据 + 指针**；PDF 字节、全文、摘要存 `file_registry`（及未来独立 raw 路径），**禁止** BLOB/TEXT 正文进 clean。

### 6.1 `cn_announcement_clean` 列设计（用户 2026-06-29 + Plan 建议）

**原则：** 现在做「能检索、能挂原文、能接未来抓取管道」的骨架；抓取方式（MCP/插件/爬虫）未定，故 **只预留指针与状态，不实现正文写入**。

| 列                                                              | 必填    | 业务含义                                                                                      | 当前 R3H-06 填法            |
| --------------------------------------------------------------- | ------- | --------------------------------------------------------------------------------------------- | --------------------------- |
| `announcement_id`                                               | PK      | 公告唯一 ID（normalizer 统一 `filing_id`→此列）                                               | replay/live 有则填          |
| `instrument_id`                                                 | ✓       | 标的                                                                                          | 有                          |
| `title`                                                         | ✓       | 标题                                                                                          | 有                          |
| `publish_timestamp`                                             | ✓       | 发布时间                                                                                      | 有                          |
| `announcement_url`                                              | 可空    | 公告列表/详情页 URL（capabilities 的 `url`）                                                  | 有则填                      |
| `announcement_type`                                             | 可空    | 公告类型（年报摘要/业绩预告/重大事项等）                                                      | **列必有**；源未提供则 NULL |
| `data_domain`                                                   | ✓       | `cn_announcements` / `cn_filings` / `cn_pdf_reports`                                          | 区分抓取域                  |
| `source_used`                                                   | ✓       | 固定 `cninfo`                                                                                 | 有                          |
| `pdf_file_id`                                                   | 可空    | → `file_registry.file_id`（PDF 已落盘时）                                                     | 仅 PDF smoke 路径可填       |
| `extracted_text_file_id`                                        | 可空    | → `file_registry.file_id`（未来摘要/全文 JSON 或 txt）                                        | **恒 NULL**（预留）         |
| `content_status`                                                | ✓       | `metadata_only` \| `pdf_registered` \| `text_pending` \| `summary_ready` \| `full_text_ready` | 默认 `metadata_only`        |
| `batch_id` / `source_fetch_id` / `content_hash` / `schema_hash` | lineage | 审计与去重                                                                                    | 与 bar 表一致               |
| `quality_flags` / `created_at`                                  | ✓       | 质量标记 / 入库时间                                                                           | 有                          |

**本卡不做：** `summary_text` 列、爬虫/MCP 实现、自动摘要；仅 DDL + promote 写 metadata + 测证明 `pdf_file_id` 可挂接。

**`file_registry` 分工：** PDF/原文/摘要文件一律登记在既有 `file_registry`（`file_type`, `local_path`, `content_hash`…）；clean 行只保存 `*_file_id` 外键式指针（VARCHAR，无 DB FK 约束，ponytail 与项目其它表一致）。

---

## 7. 资源约束

- 测试库行数 cap 沿用 r3g03（≤10 symbols / ≤120d）；禁止全市场 migration dry-run 写生产路径。
- ResourceGuard 不在本卡扩张 cap。

---

## 8. 边界约束

**Must not（registry 三件套 — 无 coordinator 时禁止改）：**

```text
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_route_contract.yaml
```

**Must not（其它）：**

- 实现 env-gated **live 产品化**（R3H-08）
- US 交易日历（R3H-07）
- R3H-05 审计 / PASS 裁决
- Layer3/4 industry/market 表 migration（Round 3F）
- 写 `data/duckdb/quant_monitor.duckdb`
- Wave 2+ agent 提交 migration SQL

**Must:**

- TDD：每步先 RED 测再 GREEN 实现
- 测试五字段注释（GLOBAL_TESTING_POLICY）
- Execute 每步 GREEN 后全库 pytest

---

## 9. 实现步骤

| Step | ID             | 交付                                                                                                                                                                        |
| ---- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 9.0  | boot           | `tests/test_r3h06_clean_schema.py` 空壳 + import 绿                                                                                                                         |
| 9.1  | bar_ddl        | migration **013**：`instrument_registry` + `security_bar_1d`；`schema.sql` + `test_schema_contract` 子集绿                                                                  |
| 9.2  | disclosure_ddl | **013** 含 `cn_announcement_clean`（§6.1 全列）；capabilities 基字段 ⊆ DDL                                                                                                  |
| 9.3  | stg_bar_ohlcv  | migration **014** 扩 `stg_foundation_smoke` OHLCV 列；`StagingRow` + `populate_staging_from_bundle` bar 路径                                                                |
| 9.4  | stg_disclosure | `populate_disclosure_from_bundle`（`filing_id`→`announcement_id`）；staging 目标 `stg_disclosure_smoke`（013 同批建表）                                                     |
| 9.5  | domain_router  | 新建 `clean_write_targets.py`：`domain→(target_table, staging_table, write_mode, primary_keys)`；`limited_production_entry` **删除**硬编码 `append_only`/`market_bar_clean` |
| 9.5b | macro_mapper   | fred bundle→`axis_observation` 行（对照 `011` + `ingestion_evidence.py`）；纳入 9.5 同测 `-k domain_router`                                                                 |
| 9.6  | cninfo_shape   | 删除 `_cninfo_staging_rows` bar 合成；cninfo promote 仅写 `cn_announcement_clean`；**负向**：promote 后 `security_bar_1d` 行数不变                                          |
| 9.7  | idempotency    | 真实 promote 路径重复 execute；`upsert_by_pk`；行数不增长                                                                                                                   |
| 9.8  | pilot_compat   | 实现路径零 `market_bar_clean`（见 §9.8.1）；改 `r3g03` 脚本/测/fixture→`security_bar_1d`                                                                                    |
| 9.9  | docs_coverage  | `MIGRATION_COVERAGE.md` 013/014 DONE；migration 无 down → pilot 快照回滚说明；`loop_maintain.py` 绿                                                                         |
| 9.10 | merge_gate     | 全库 pytest；Plan 对抗审计零 BLOCKING                                                                                                                                       |

### 9.8.1 `market_bar_clean` 清除门禁（可执行）

```bash
rg market_bar_clean backend/ scripts/ tests/ specs/ docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/ --glob '!**/.trellis/**'
```

通过条件：**exit 1（零匹配）**。历史 `research/`、`R3G_*` 归档文档不在此 rg 范围。

**9.8 必改文件清单：** `scripts/r3g03_isolated_pilot_dry_run.py`；`tests/test_round3g_limited_production_clean_write.py`；`tests/test_round3g_limited_production_rollback.py`；`tests/fixtures/sandbox_clean_write/r3g03/*.json|yaml`。

**切片依赖：** 9.1→9.3/9.5；9.2→9.4/9.6；9.5→9.7；9.8 依赖 9.5+9.1；9.10 最后。

---

## 10. 测试要求

- 新模块 `tests/test_r3h06_clean_schema.py`：DDL 存在、OHLCV 列、三域路由、cninfo 非 bar、幂等。
- 扩展 `test_schema_contract.py` / `test_migration_coverage.py` 覆盖 013。
- 回归 `test_round3g_limited_production_clean_write.py`、`test_write_manager.py` upsert 路径。

---

## 11. 验收命令

```bash
uv sync --locked
uv run pytest tests/test_r3h06_clean_schema.py -q
uv run pytest tests/test_schema_contract.py tests/test_migration_coverage.py -q
uv run pytest tests/test_round3g_limited_production_clean_write.py -q
uv run pytest -q
uv run python scripts/loop_maintain.py
```

---

## 12. 完成标准

1. §5.0.1 三项 **SCHEMA-G3G4 / CNINFO-DISCLOSURE-SHAPE / G6** 有代码+测+文档证据。
2. Wave 3（R3H-08）可在本卡 CLOSED 后合法改 clean 写路径。
3. Audit 零 BLOCKING OPEN；pytest 全绿。

---

## 13. Red Flags

- 继续三源同写 `market_bar_clean`
- cninfo 公告仍用 `trade_date`+`close` 冒充 bar
- 仅有 close 无 OHLCV 列的 bar clean
- `append_only` 写入有 PK 的 bar/disclosure 表导致叠行
- 本卡改 registry 六源 route 却无 coordinator manifest
- 宣称 production-live / 主库已 promote

---

## 14. 输出要求

改动清单、migration 编号、三域表对照、测试结果、未完成项（若有）、主库未写入证明。

---

## 15. Execute Skill 冻结

| Skill                      | 本任务 | 绑定 Step                |
| -------------------------- | ------ | ------------------------ |
| test-driven-development    | 必做   | 9.0–9.9 每步             |
| karpathy-guidelines        | 必做   | 全步                     |
| testing-guidelines         | 必做   | 全测五字段               |
| incremental-implementation | 必做   | 每步 GREEN 后全库 pytest |
