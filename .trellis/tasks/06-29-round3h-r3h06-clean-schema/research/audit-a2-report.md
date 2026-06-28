# Audit A2 — Ponytail / 最小 diff · R3H-06

> **维度：** A2（ponytail-review）  
> **分支：** `feature/round3h-r3h06-clean-schema`  
> **权威：** 冻结卡 `frozen/R3H_06_CLEAN_SCHEMA.md` · `AUDIT.plan.md` · `agents/audit-a2-ponytail.md`  
> **范围：** `git diff master` + 工作区未提交改动（含 untracked）  
> **日期：** 2026-06-29

---

## 总裁决

**PASS_WITH_FIXES**

实现整体对齐冻结卡 Wave 1 目标（三域分表、OHLCV、cninfo 公告形、upsert 幂等、`market_bar_clean` 清零）。`clean_write_targets.py` 为卡 §9.5 显式交付，非过度抽象。未发现必须阻断 merge 的 YAGNI 大块；存在 **~120 行可合并/可删** 的重复与双轨路径，建议在 merge 前或紧随 merge 的 debt-lite 切片内消化。

---

## diff 范围审查

### 统计（`git diff master --stat` + untracked）

| 类别           | 文件数 | 净增行（约）                                       |
| -------------- | ------ | -------------------------------------------------- |
| 已跟踪 diff    | 28     | **+480**（+667 / −187）                            |
| 未跟踪（核心） | 4      | **+624**（013/014/clean_write_targets/test_r3h06） |
| **合计（估）** | **32** | **~+1100**                                         |

### 冻结卡 §4「相关代码文件」对照

| 路径                                          | 卡 §4        | 实际                              | 判定                                           |
| --------------------------------------------- | ------------ | --------------------------------- | ---------------------------------------------- |
| `013_clean_domain_tables.sql`                 | ✓            | untracked 新建                    | **IN SCOPE**                                   |
| `014_stg_bar_ohlcv.sql`                       | ✓            | untracked 新建                    | **IN SCOPE**                                   |
| `clean_write_targets.py`                      | ✓            | untracked 新建                    | **IN SCOPE**（§9.5 SSOT）                      |
| `rehearsal_loader.py`                         | ✓            | +288 行                           | **IN SCOPE**（OHLCV/disclosure/macro staging） |
| `limited_production_entry.py`                 | ✓            | ~+73                              | **IN SCOPE**                                   |
| `rehearsal_runner.py`                         | ✓            | ~+73                              | **IN SCOPE**                                   |
| `schema.sql` / `MIGRATION_COVERAGE.md`        | ✓            | 已改                              | **IN SCOPE**                                   |
| `test_r3h06_clean_schema.py`                  | ✓            | untracked ~456 行                 | **IN SCOPE**                                   |
| 回归测/fixture/r3g03 脚本                     | ✓（§9.8）    | 已改                              | **IN SCOPE**                                   |
| `backend/app/sync/runners.py`                 | 卡列「若需」 | **未改**                          | OK（YAGNI）                                    |
| `db_inspector.py`                             | **未列**     | +4 行                             | **计划外 · 必要涟漪**                          |
| `ops_db_inspect_contract.yaml`                | **未列**     | L5 迁出 `future_phase_key_tables` | **计划外 · 必要涟漪**                          |
| `BATCH_3H_TASK_CARD_MANIFEST.md`              | **未列**     | +21 行 Wave 表                    | **计划外 · 文档**                              |
| `R3H_PASS_EXECUTION_PLAN.md`                  | **未列**     | +8 列 Trellis 列                  | **计划外 · 文档**                              |
| `docs/generated/*`                            | loop 产物    | staged                            | **IN SCOPE**（9.9 / loop_maintain）            |
| `check_test_catalog.py` / `test_catalog.yaml` | 新测登记     | staged+unstaged                   | **IN SCOPE**                                   |

### §9.8 门禁

`rg market_bar_clean backend/ scripts/ tests/ specs/ docs/implementation_tasks/ROUND_3…` → **backend/scripts/tests/specs 内零匹配**（仅 `research/`、`R3G_*` 历史文档保留）→ **PASS**。

### DOUBT（≥20 行可简化）

**已找到**（搜索：`rehearsal_loader.py`、`limited_production_entry.py`、`rehearsal_runner.py`、`tests/db_helpers.py`、`tests/test_r3h06_clean_schema.py`、`tests/test_schema_contract.py`）— 见下表 ponytail 违规项 #2–#7。

---

## ponytail 违规表

| #   | 候选删改（file:line）                                                                                                                    | ponytail 梯级                                   | 估行  | 是否阻塞 |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ----- | -------- |
| 1   | `rehearsal_loader.py:222-253` `_fred_staging_rows` 仍注册于 `_STAGING_ROW_BUILDERS`，promote/rehearsal 已走 `populate_macro_from_bundle` | 1 YAGNI / 2 复用 macro 路径                     | ~32   | **建议** |
| 2   | `limited_production_entry.py:560-569` 与 `rehearsal_runner.py:261-270` 相同 staging 三分支 dispatch                                      | 2 抽 `populate_staging_for_write_target()` 一处 | ~24×2 | **建议** |
| 3   | `tests/db_helpers.py:18-47` 与 `50-80` `insert_stg_*` / `insert_smoke_clean_row` 几乎相同 INSERT                                         | 2 单函数 + `table=` 参数                        | ~30   | **建议** |
| 4   | `tests/test_r3h06_clean_schema.py:17-28` `_table_columns_from_sql` 与 `test_schema_contract.py:22-35` `_table_columns` 重复              | 2 复用既有 helper                               | ~12   | **建议** |
| 5   | `test_r3h06` `test_bar_ddl_schemaContract_*` 与 `test_schema_contract` `test_cleanDomainMigration013Columns_*` 列对齐重复                | 1 删一侧或 parametrized 一处                    | ~25   | **建议** |
| 6   | `test_r3h06_clean_schema.py:261-357` 与 `359-455` 两段 promote 夹具（yaml/json/rollback）结构相同                                        | 2 共享 `_promote_fixture()`                     | ~90×2 | **建议** |
| 7   | `rehearsal_loader.py:107-168` `DisclosureStagingRow` dataclass + macro 用 `dict` 双风格                                                  | 5 统一或保持（非必须）                          | ~60   | **可选** |
| 8   | `BATCH_3H_TASK_CARD_MANIFEST.md` + `R3H_PASS_EXECUTION_PLAN.md` Wave 表更新                                                              | 1 卡未要求                                      | ~30   | **可选** |

**不算违规（卡显式 AC）：** migration 013/014 行数、`clean_write_targets.py`、`rehearsal_loader` OHLCV/disclosure/macro populate 主体增量。

---

## 计划外发现

> 对抗搜索：对照冻结卡 §4/§8、`rg market_bar_clean`、diff 文件名与 `db_inspector` / BATCH_3H docs。

| ID  | 发现                                                                                                                                                                              | 严重度 | 阻塞                                                   |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------ |
| O1  | `db_inspector.py` + `ops_db_inspect_contract.yaml`：L5 表从 `future_phase_key_tables` 清空；`if not tables` → `if tables is None` 修空列表合法                                    | LOW    | NON-BLOCKING                                           |
| O2  | `BATCH_3H_TASK_CARD_MANIFEST.md` / `R3H_PASS_EXECUTION_PLAN.md` Wave 1–4 表 — 卡 §4 未列，属协调文档                                                                              | LOW    | NON-BLOCKING                                           |
| O3  | FRED **双轨**：promote 用 `axis_observation`，但 `test_LiveEvidenceBridge_fred_*`（`test_round3g_limited_production_clean_write.py:1131+`）仍测 `staging_rows_from_bundle` bar 形 | MEDIUM | NON-BLOCKING（测目的与 9.5b 漂移，见 #A2-004）         |
| O4  | `rehearsal_runner.py` bar 域仍写 `security_bar_smoke_clean` + `append_only`（注释 ponytail 有意保留 r3g01）— 与 promote `security_bar_1d` upsert 分叉                             | LOW    | NON-BLOCKING（卡 §9.8 允许 rehearsal 与 promote 分轨） |
| O5  | 无 `market_bar_clean` 残留于 backend/scripts/tests/specs — **计划外负向检查 PASS**                                                                                                | —      | —                                                      |

---

## 全部发现项汇总

### BLOCKING

| ID  | 级别 | 发现   | 修复建议 |
| --- | ---- | ------ | -------- |
| —   | —    | **无** | —        |

### NON-BLOCKING

| ID     | 级别   | 发现                                                                       | 修复建议                                                                                                                                                                                                                |
| ------ | ------ | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A2-001 | MEDIUM | `_fred_staging_rows` 与 macro promote 双轨；loader 仍暴露 bar 形 FRED API  | 删除 `_fred_staging_rows` 及 `_STAGING_ROW_BUILDERS["fred"]`；将 `test_LiveEvidenceBridge_fred_*` / `test_official_macro_adapters` 中 fred staging 断言改为 `populate_macro_from_bundle` + `stg_axis_observation_smoke` |
| A2-002 | MEDIUM | `limited_production_entry` 与 `rehearsal_runner` staging dispatch 复制粘贴 | 在 `rehearsal_loader.py` 增加 `populate_staging_for_target(con, bundle, staging_table, **kwargs) -> int`，两处各减 ~10 行                                                                                               |
| A2-003 | LOW    | `db_helpers` 两个 INSERT helper 重复                                       | `insert_smoke_clean_row(..., table="stg_foundation_smoke")` 一处实现；`insert_stg_foundation_smoke_row` 薄包装或删除                                                                                                    |
| A2-004 | LOW    | 测试 SQL 列解析 helper 重复（r3h06 vs schema_contract）                    | 从 `test_schema_contract._table_columns` import 或抽到 `tests/sql_contract_helpers.py`                                                                                                                                  |
| A2-005 | LOW    | 013↔schema.sql 列对齐测重复（r3h06 + schema_contract）                     | 保留 `test_schema_contract.test_cleanDomainMigration013Columns_*`；删 r3h06 中 `test_bar_ddl_schemaContract_*` 或改为只测 PK/存在性                                                                                     |
| A2-006 | LOW    | r3h06 两个 promote 集成测 ~90 行夹具重复                                   | 提取 `tests/fixtures` 或模块级 `_build_promote_artifacts(tmp_path, source_id, domain, target_table)`                                                                                                                    |
| A2-007 | LOW    | BATCH_3H manifest / PASS plan 文档 diff 超出卡 §4 文件清单                 | 保留有价值则单独 commit 说明「协调文档」；或 revert 仅留 `MIGRATION_COVERAGE.md`                                                                                                                                        |
| A2-008 | LOW    | `DisclosureStagingRow` vs macro `dict` 风格不一致                          | 非必须；若统一则 macro 也 dataclass，或 disclosure 简化为 dict（与 macro 对称）                                                                                                                                         |

### 与 A4 交叉（供下游）

| 关联                                                    | 说明                                                                      |
| ------------------------------------------------------- | ------------------------------------------------------------------------- |
| staging 零行                                            | 两处均已 `staged_count <= 0` fail-closed — 与 A4 错误模型一致，无额外抽象 |
| `LimitedProductionEntryError` vs `RehearsalRunnerError` | dispatch 合并时不应吞异常类型差异                                         |

---

## What's Done Well

- **`clean_write_targets.py`** 48 行、三域一函数，符合卡 §9.5 SSOT，三处消费（entry / runner / test），非 wrapper 膨胀。
- **macro 路径** 复用 `AXIS_OBSERVATION_DDL_COLUMNS`，避免手写列序（ponytail 梯级 2）。
- **014 migration** 用 DROP+CREATE 对齐列序，注释标明 WriteManager 列序约束。
- **cninfo 负向门禁** `limited_production_entry` 在 METADATA_DOMAINS 下断言 `security_bar_1d` 不变，最小增量 fail-closed。
- **`market_bar_clean` 清除** 实现路径已零引用；fixture/脚本已切 `security_bar_1d`。
- **db_inspector 涟漪** 仅 4 行 + contract 空列表，与 013 状态一致，非随意扩 scope。

---

## Verification Story

| 项                 | 状态                                                                                                                              |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| Tests reviewed     | **是** — `test_r3h06_clean_schema.py`（13 测）、`test_schema_contract` 新增、`test_migration_coverage` L5 翻转、round3g 回归 diff |
| Build verified     | **否** — 本维只读，未跑 pytest                                                                                                    |
| Security checked   | **否** — 非 A3 维；未见本 diff 引入密钥/旁路                                                                                      |
| ponytail checklist | diff stat 已记录；≥20 行候选已列；阻塞/建议已区分                                                                                 |

---

## A2 Checklist

- [x] `git diff --stat` 已记录（28 tracked +480 net；+ untracked ~624）
- [x] 每候选附 file:line + ponytail 梯级
- [x] A4 交叉引用（staging 零行 / 异常类型）
- [x] 阻塞 vs 建议已区分
- [x] `## 计划外发现` 已显式声明（含对抗搜索）
