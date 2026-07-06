# 设计 Schema 与 Migration 覆盖矩阵

> **最近核实：** 2026-07-06 · **基线：** `master` @ migrations `001`–`015` · DCP-05 Tier A clean 域  
> **用途：** 厘清 `specs/schema/schema.sql` 中哪些对象已落地、哪些延后（闭合审计 A2-P2-01）。

## 图例

| 状态         | 含义                                                                    |
| ------------ | ----------------------------------------------------------------------- |
| **DONE**     | 表/列已存在于已应用的 migration 中                                      |
| **PARTIAL**  | 表已存在；部分列或 CHECK 约束延后至应用层实现                           |
| **DEFERRED** | 在设计 `schema.sql` 中但尚无 migration；见 `AUDIT_DEFERRED_REGISTRY.md` |
| **N/A**      | Round 3+ 建模 / 回测表；不在 Round 2 范围内                             |

## 核心摄取（Round 2）

| 对象                     | Migration     | 状态     | 备注                                                                                                                 |
| ------------------------ | ------------- | -------- | -------------------------------------------------------------------------------------------------------------------- |
| `schema_version`         | 001           | DONE     |                                                                                                                      |
| `source_registry`        | 004, 009, 012 | PARTIAL  | `source_type` / `license_type` CHECK 经 009；`registry_generation` / `removed_from_yaml_at` 经 **012**（R3F-MIG-04） |
| `fetch_log`              | 004, 009, 012 | PARTIAL  | `status` CHECK 经 009；显式列重建经 **012**（R3F-MIG-03）                                                            |
| `file_registry`          | 001/004       | DONE     | `content_hash` UNIQUE                                                                                                |
| `data_sync_job`          | 006, 007      | DONE     | `status` CHECK 经 007 重建                                                                                           |
| `job_event_log`          | 006, 007      | DONE     | old/new status CHECK                                                                                                 |
| `validation_report`      | 005           | DONE     | Status CHECK                                                                                                         |
| `data_quality_log`       | 005           | DONE     |                                                                                                                      |
| `source_conflict`        | 005, 009      | DONE     | `severity` / `reconcile_status` CHECK 经 009                                                                         |
| `write_audit_log`        | 001, 007      | PARTIAL  | 设计中的额外审计列尚未全部迁移                                                                                       |
| `resource_guard_log`     | 003           | DONE     |                                                                                                                      |
| `manual_review_queue`    | 005, 009, 012 | PARTIAL  | `status` / `source_object_type` CHECK 经 009；`priority` 应用层（R2-RISK-4, ADR-002）；显式重建 **012**              |
| `source_health_snapshot` | —             | DEFERRED | D2-P2-1                                                                                                              |

## 建模 / 回测（Round 3+）

| 对象                                                | Migration | 状态            | 备注                                                  |
| --------------------------------------------------- | --------- | --------------- | ----------------------------------------------------- |
| `axis_registry` … `axis_snapshot_lineage`（7 张表） | 011       | DONE            | Layer 1 权威来源；`schema.sql` 同步 **DEFERRED O-02** |
| `instrument_registry`, `security_bar_1d`            | 013       | DONE            | R3H-06 Wave 1；bar 表 PK 含 `adjustment_type`         |
| `backtest_*`, `alert_event`                         | —         | N/A — Round 4/5 |                                                       |

## Round 3 Layer 3 — 产业链（已设计，尚无 migration）

> **SSOT：** `docs/modules/layer3_industry_shock_anchor.md` — **不在** `specs/schema/schema.sql` 中（设计拆分）。  
> **闭合测试：** `tests/test_migration_coverage.py` · **对账矩阵：** 本文矩阵与 schema/migration 代码。

| 对象                            | Migration | 状态     | 备注                           |
| ------------------------------- | --------- | -------- | ------------------------------ |
| `industry_chain_registry`       | —         | DEFERRED | Staged loader `layer3_chains/` |
| `industry_chain_anchor`         | —         | DEFERRED | Staged loader                  |
| `industry_chain_node`           | —         | DEFERRED | Staged loader                  |
| `industry_chain_edge`           | —         | DEFERRED | Staged loader                  |
| `industry_chain_cross_edge`     | —         | DEFERRED | Staged loader                  |
| `industry_chain_instrument_map` | —         | DEFERRED | Staged loader                  |
| `industry_chain_event_anchor`   | —         | DEFERRED | 文档延后说明                   |
| `industry_chain_daily_snapshot` | —         | DEFERRED | Staged `snapshot_builder.py`   |

**Migration 归属：** Round 3F（`R3-MODEL-L3L4-MIGRATION` 提议延后）。

## Round 3 Layer 4 — 市场结构（已设计，尚无 migration）

> **SSOT：** `docs/modules/layer4_market_structure.md` — **不在** `specs/schema/schema.sql` 中。

| 对象                      | Migration | 状态     | 备注                     |
| ------------------------- | --------- | -------- | ------------------------ |
| `market_registry`         | —         | DEFERRED | Staged `layer4_markets/` |
| `market_calendar`         | —         | DEFERRED | Staged adapters          |
| `market_index_snapshot`   | —         | DEFERRED | Staged adapters          |
| `market_sector_snapshot`  | —         | DEFERRED | Staged adapters          |
| `market_breadth_snapshot` | —         | DEFERRED | Staged adapters          |
| `market_rule_event`       | —         | DEFERRED | Staged adapters          |

## Round 3 Layer 5 — 证券证据（`schema.sql` 中部分设计）

> **SSOT 拆分：** `specs/schema/schema.sql` 列出 `instrument_registry`、`security_bar_1d`、`cn_announcement_clean`；模块文档在运行态模型中使用 `security_bar_daily` 命名 — bar 表 **已在 013 迁移**。  
> **Staged 运行态：** `backend/app/layer5_evidence/` — 仅 pilot/sandbox promote 路径；**非**默认 `quant_monitor.duckdb`。

| 对象                                                       | Migration | 状态              | 备注                                                       |
| ---------------------------------------------------------- | --------- | ----------------- | ---------------------------------------------------------- |
| `instrument_registry`                                      | 013       | DONE              | R3H-06；PK `instrument_id`                                 |
| `security_bar_1d`（`schema.sql`）                          | 013, 014  | DONE              | OHLCV + PK；**014** 重建 `stg_foundation_smoke` 以对齐     |
| `cn_announcement_clean`                                    | 013       | DONE              | cninfo 元数据 clean；`content_status` 默认 `metadata_only` |
| `stg_disclosure_smoke`                                     | 013       | DONE              | cninfo promote staging                                     |
| `security_bar_daily`（模块文档）                           | —         | DEFERRED          | 运行态模型名；与 schema 命名漂移                           |
| `futures_bar_daily`, `options_chain_snapshot`              | —         | DEFERRED          | 023 全量范围                                               |
| `financial_statement_snapshot`, `valuation_snapshot`       | —         | DEFERRED          | 023 全量范围                                               |
| `event_registry`, `evidence_chain`, `stock_model_evidence` | —         | DEFERRED / staged | `evidence_chain` 目前仅内存链                              |

## Round 3 Layer 1（migration 011）

| 对象                    | 状态 | 备注                                                               |
| ----------------------- | ---- | ------------------------------------------------------------------ |
| `axis_observation`      | DONE | 17 列；无 DB CHECK（ADR-002 应用层）；见 `observation_contract.py` |
| `axis_snapshot_lineage` | DONE | `source_fetch_ids` / `source_content_hashes` 为 VARCHAR JSON       |

## 验证

```powershell
.venv\Scripts\python.exe -m pytest tests/test_schema_migration.py -q
.venv\Scripts\python.exe -m pytest tests/test_audit_fixes.py -q
.venv\Scripts\python.exe -m pytest tests/test_migration_coverage.py -q
```

交叉引用：`docs/AUDIT_DEFERRED_REGISTRY.md`。

## Round 3H clean 域（migrations 013–014 · R3H-06）

| Migration | 对象                                                                                                                        | 回滚                                                                                                                                                                  |
| --------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **013**   | `instrument_registry`, `security_bar_1d`, `cn_announcement_clean`, `stg_disclosure_smoke`, `stg_axis_observation_smoke`     | **无 down migration。** Pilot/sandbox 回滚：恢复 promote 前 DuckDB 快照（R3G-03 proof 前 `backup_or_snapshot_pointer`）；未经 coordinator 不得在共享审计库上 `DROP`。 |
| **014**   | 重建 `stg_foundation_smoke`，含 OHLCV + `adjustment_type` PK                                                                | **无 down migration。** 仅 staging；在全新测试库上重新应用 migrations。                                                                                               |
| **015**   | `us_disclosure_clean`, `stg_us_disclosure_smoke`, `crypto_derivative_clean`, `stg_crypto_derivative_smoke`（DCP-05 Tier A） | **无 down migration。** Pilot/sandbox 回滚按 ADR-009；未经 coordinator 不得在共享审计库上 `DROP`。                                                                    |

**Migration 009 vs 008 叙事（ADV-A6-003 / R4）：** Migration **007** 重建 sync job 表并加 CHECK 约束；**008**（`008_lineage_version_fields.sql`）为 rule/version lineage 列；**009** 对摄取表应用 `status` CHECK 约束；**010** 在 validation lineage 上强制非空 `rule_set_id` / `rule_version`，采用显式列重建（禁止 `SELECT *` 回放）；**012**（Round 3F / R3F-MIG）新增 `registry_generation` / `removed_from_yaml_at`、对 `fetch_log` / `manual_review_queue` 做显式列重建，并记录 `priority` 仅应用层（ADR-002）。

## Round 3F 路由（R3F-MIG-05）

| 桶                                | 项                                                                                                                                        | 归属 / 证据                                                                              |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **009-resolved**                  | `fetch_log.status`、`source_registry` 枚举 CHECK、`manual_review_queue.status`/`source_object_type`、`source_conflict` severity/reconcile | `009_status_check_constraints.sql`；`test_schemaContract_includesStatusCheckConstraints` |
| **3F-open → closed**              | `registry_generation` / `removed_from_yaml_at`（D2-P3-1）；`fetch_log`/`manual_review_queue` 显式列重建（A9-P3-01 子集）                  | **012**；`tests/test_round3f_migration_residuals.py`                                     |
| **App-layer / wont-fix DB CHECK** | `manual_review_queue.priority`（R2-RISK-4）                                                                                               | ADR-002 §App-layer-only columns                                                          |
| **Deferred**                      | `source_health_snapshot` 表（D2-P2-1）                                                                                                    | B3F-SH 拥有表语义 — **非** B3F-MIG                                                       |
