# ADR-009：clean 域扩展（migration 015）

**状态：** 已接受（计划冻结）  
**日期：** 2026-07-02

## 22 源 vs 11 源（范围说明 · AD-05）

- **22 源完整枚举 SSOT：** `docs/modules/design/data_sources.md` §5.9.1（全注册表验收面）。
- **本 ADR 表（下文 §3）：** DCP-05 **11 源增量金路径**子集 — 每源一行 canonical domain → clean 表映射。
- **禁止**在多处维护互斥的源列表；新增源先更新 §5.9.1，再在本表或 registry 登记子集职责。

## 背景

用户明确要求：**11/11 个数据源**必须完成增量同步，且须写入 **clean 表 upsert**（不能停留在仅写 staging）。  
当前 R3H-06 的 clean 落点（`013_clean_domain_tables.sql`）仅覆盖 bar（`security_bar_1d`）、中国元数据（`cn_announcement_clean`）、宏观（`axis_observation`）。`sec_edgar` 与 `deribit` 缺少 clean 目标；若干官方宏观 domain 尚未在 `resolve_clean_write_target` 注册。

## 决策

### 1. 新增 **migration 015**

- `us_disclosure_clean` + `stg_us_disclosure_smoke` — SEC 申报 / Form 4（`sec_edgar`）
- `crypto_derivative_clean` + `stg_crypto_derivative_smoke` — Deribit 期权曲面 / 期限结构快照

### 2. 扩展 `clean_write_targets.py` 的 domain 路由（015 之外不再新增 clean 表）

- **BAR_DOMAINS** 增加：`us_equity_daily_bar`、`etf_daily_bar`、`fx_daily_bar`、`commodity_daily_bar` → 统一写入 `security_bar_1d`
- **MACRO_DOMAINS** 别名增加：`us_treasury_yield_curve`、`inflation_expectation`、`central_bank_policy`、`credit_gap`、`development_indicator`、`global_macro_reference`、`cot_positioning` → 统一写入 `axis_observation`

### 3. 每个源的 **规范增量 domain**（DCP-05 完成口径：每源一行）

| source_id     | canonical_domain        | clean_table             |
| ------------- | ----------------------- | ----------------------- |
| baostock      | cn_equity_daily_bar     | security_bar_1d         |
| mootdx        | cn_equity_daily_bar     | security_bar_1d         |
| fred          | macro_series            | axis_observation        |
| us_treasury   | us_treasury_yield_curve | axis_observation        |
| bis           | central_bank_policy     | axis_observation        |
| world_bank    | development_indicator   | axis_observation        |
| cftc_cot      | cot_positioning         | axis_observation        |
| cninfo        | cn_announcements        | cn_announcement_clean   |
| sec_edgar     | us_filings              | us_disclosure_clean     |
| alpha_vantage | us_equity_daily_bar     | security_bar_1d         |
| deribit       | crypto_options_surface  | crypto_derivative_clean |

### 4. Watermark 读取规则

| 数据类型      | 读取位置                                           |
| ------------- | -------------------------------------------------- |
| bar           | `sync/watermark.py`                                |
| macro         | `ops/*_incremental_watermark.py`（以 fred 为先例） |
| metadata      | `cn_announcement_clean` 上的 `publish_timestamp`   |
| US disclosure | `us_disclosure_clean` 上的 `filing_date`           |
| crypto        | `crypto_derivative_clean` 上的 `as_of_timestamp`   |

## 曾考虑的替代方案

| 方案                                     | 结论                                                                |
| ---------------------------------------- | ------------------------------------------------------------------- |
| **sec_edgar / deribit 仅写 staging**     | **拒绝** — 用户于 2026-07-02 明确要求须写 clean upsert。            |
| **单一通用 `vendor_clean` JSON 表**      | **拒绝** — 会破坏 R3H-06 的类型化 clean 契约与 DQ profile。         |
| **将 deribit 映射到 `axis_observation`** | **拒绝** — 期权曲面行不是标量宏观观测；独立表才能保留 domain 语义。 |

## 后果

- DCP-05 **依赖 migration** → 不属于「纯 Phase 8D 轻债」；归入 Plan v4.1 **complex track**。
- 须在切片 **S00** 同步更新 `docs/schema/MIGRATION_COVERAGE.md` 与 `test_migration_coverage`。
- 当 11 个 e2e 测试全部变绿后，DCP-06 方可消费 clean 输入。
- `alpha_vantage` 的额外 domain（如期权链、`macro_series`）**不在** DCP-05 规范行内；后续 wave 可为单源增加第二 domain。
