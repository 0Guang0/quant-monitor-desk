# 执行索引 — R3H-06 Clean Schema (Wave 1)

> P0i：**索引完整**（v4 · Plan 2026-06-29 · 对抗审计修复后）

## 0. 冻结元数据

| 字段         | 值                                                                                                                        |
| ------------ | ------------------------------------------------------------------------------------------------------------------------- |
| slug         | `06-29-round3h-r3h06-clean-schema`                                                                                        |
| source_card  | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_06_CLEAN_SCHEMA.md` |
| frozen_card  | `frozen/R3H_06_CLEAN_SCHEMA.md`                                                                                           |
| batch / item | Batch 3H PASS 收口 / `R3H-06`                                                                                             |
| wave         | Wave 1（阻塞 Wave 3）                                                                                                     |
| branch       | `feature/round3h-r3h06-clean-schema`                                                                                      |
| base_branch  | `master`                                                                                                                  |
| user_gate    | 禁止主库；仅 R3H-06 拥有 DDL；**禁止 VIEW**                                                                               |

### 0.1 血缘

| 活卡 AC             | Step | 验证链 |
| ------------------- | ---- | ------ |
| AC-BOOT             | 9.0  | §2     |
| AC-SCHEMA-G3G4-BAR  | 9.1  | §2     |
| AC-CNINFO-SHAPE     | 9.2  | §2     |
| AC-SCHEMA-G4-OHLCV  | 9.3  | §2     |
| AC-STG-DISCLOSURE   | 9.4  | §2     |
| AC-SCHEMA-G3-ROUTER | 9.5  | §2     |
| AC-CNINFO-NO-BAR    | 9.6  | §2     |
| AC-G6-IDEMPOTENCY   | 9.7  | §2     |
| AC-PILOT-COMPAT     | 9.8  | §2     |
| AC-DOCS             | 9.9  | §2     |
| AC-MERGE            | 9.10 | §2.1   |

**G5（预演 gap）：** 由 AC-CNINFO-NO-BAR + AC-CNINFO-SHAPE 覆盖（无独立 §5.0.1 ID）。

**切片依赖：** 9.1→9.3/9.5；9.2→9.4/9.6；9.5→9.7；9.8 依赖 9.1+9.5；9.10 最后。

## 1. 步骤与证据（Execute）

| Step | 锚点           | RED 命令                                                                                                                                                       | GREEN 命令         | 证据路径                                     |
| ---- | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | -------------------------------------------- |
| 9.0  | boot           | `uv run pytest tests/test_r3h06_clean_schema.py -q`（ModuleNotFound）                                                                                          | 空壳绿             | `execute-evidence/9.0-{red,green}.txt`       |
| 9.1  | bar_ddl        | `uv run pytest tests/test_r3h06_clean_schema.py tests/test_schema_contract.py -q -k bar_ddl`                                                                   | 全绿               | `execute-evidence/9.1-{red,green}.txt`       |
| 9.2  | disclosure_ddl | `uv run pytest tests/test_r3h06_clean_schema.py -q -k disclosure_ddl`                                                                                          | 全绿               | `execute-evidence/9.2-{red,green}.txt`       |
| 9.3  | stg_bar_ohlcv  | `uv run pytest tests/test_r3h06_clean_schema.py -q -k ohlcv`                                                                                                   | 全绿               | `execute-evidence/9.3-{red,green}.txt`       |
| 9.4  | stg_disclosure | `uv run pytest tests/test_r3h06_clean_schema.py -q -k stg_disclosure`                                                                                          | 全绿               | `execute-evidence/9.4-{red,green}.txt`       |
| 9.5  | domain_router  | `uv run pytest tests/test_r3h06_clean_schema.py -q -k domain_router`                                                                                           | 全绿               | `execute-evidence/9.5-{red,green}.txt`       |
| 9.6  | cninfo_no_bar  | `uv run pytest tests/test_r3h06_clean_schema.py -q -k cninfo_no_bar`                                                                                           | 全绿               | `execute-evidence/9.6-{red,green}.txt`       |
| 9.7  | idempotency    | `uv run pytest tests/test_r3h06_clean_schema.py -q -k idempotency`                                                                                             | 全绿               | `execute-evidence/9.7-{red,green}.txt`       |
| 9.8  | pilot_compat   | 活卡 §9.8.1 `rg` 零匹配 + `uv run pytest tests/test_round3g_limited_production_clean_write.py tests/test_round3g_limited_production_rollback.py -q -k promote` | 全绿               | `execute-evidence/9.8-{red,green}.txt`       |
| 9.9  | docs_coverage  | `uv run pytest tests/test_migration_coverage.py -q` + `uv run python scripts/loop_maintain.py`                                                                 | exit 0             | `execute-evidence/9.9-{red,green}.txt`       |
| 9.10 | merge_gate     | 子集若有红                                                                                                                                                     | `uv run pytest -q` | `execute-evidence/9.10-{red,green,full}.txt` |

每步 GREEN 后：`uv run pytest -q` → 0。

### 1.1 `market_bar_clean` 清除（9.8）

```bash
rg market_bar_clean backend/ scripts/ tests/ specs/ docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/ --glob '!**/.trellis/**'
```

**通过：** exit 1（零匹配）。

## 2. AC ↔ 测试 / 验收

| AC                  | 测试 / 命令               | 通过条件                                                                        |
| ------------------- | ------------------------- | ------------------------------------------------------------------------------- |
| AC-SCHEMA-G3G4-BAR  | `-k bar_ddl` + 013        | `instrument_registry`/`security_bar_1d` 存在；PK 含 `adjustment_type`           |
| AC-CNINFO-SHAPE     | `-k disclosure_ddl`       | §6.1 全列存在；capabilities 基字段 ⊆ DDL；`content_status` 默认 `metadata_only` |
| AC-SCHEMA-G4-OHLCV  | `-k ohlcv`                | `stg_foundation_smoke` 含 OHLCV 列；staging 传递 `adjustment_type`              |
| AC-STG-DISCLOSURE   | `-k stg_disclosure`       | `stg_disclosure_smoke` + `filing_id`→`announcement_id`                          |
| AC-SCHEMA-G3-ROUTER | `-k domain_router`        | bar→`security_bar_1d`；cninfo→`cn_announcement_clean`；fred→`axis_observation`  |
| AC-CNINFO-NO-BAR    | `-k cninfo_no_bar`        | cninfo promote 后 `security_bar_1d` 行数不变                                    |
| AC-G6-IDEMPOTENCY   | `-k idempotency`          | **真实 promote** 重复 execute 行数不变；`upsert_by_pk`                          |
| AC-PILOT-COMPAT     | §1.1 rg + r3g03 回归      | 实现路径无 `market_bar_clean`                                                   |
| AC-DOCS             | migration_coverage + loop | 013/014 DONE；rollback 说明在 MIGRATION_COVERAGE                                |
| AC-MERGE            | 全库 pytest               | exit 0                                                                          |

### 2.1 Tier

| 层  | 命令                                                | 环境     |
| --- | --------------------------------------------------- | -------- |
| A   | `uv run pytest tests/test_r3h06_clean_schema.py -q` | local/ci |
| A+  | `uv run pytest -q`                                  | local/ci |
| D   | **禁止**写 `data/duckdb/quant_monitor.duckdb`       | —        |

## 3. 必须读原文（manifest）

| path                                                                                                                          | manifest   | audience | extract                     | for     |
| ----------------------------------------------------------------------------------------------------------------------------- | ---------- | -------- | --------------------------- | ------- |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`                                                                         | must-read  | execute  | WriteManager                | 9.0     |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                                                                          | must-read  | execute  | 五字段 TDD                  | 9.0     |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`                                                                         | must-read  | execute  | cap                         | 9.5     |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_MASS_REHEARSAL_OPEN_GAPS.md`          | must-read  | both     | G3–G6                       | 9.1     |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_PASS_EXECUTION_PLAN.md` | must-read  | both     | Wave 1                      | 9.0     |
| `specs/schema/schema.sql`                                                                                                     | must-read  | both     | DDL SSOT                    | 9.1–9.2 |
| `docs/schema/MIGRATION_COVERAGE.md`                                                                                           | must-read  | both     | 013/014                     | 9.9     |
| `specs/datasource_registry/source_capabilities.yaml`                                                                          | must-read  | execute  | cn 域字段                   | 9.2     |
| `specs/contracts/sandbox_clean_write_contract.yaml`                                                                           | must-read  | execute  | pilot 仅 `cn_announcements` | 9.8     |
| `backend/app/db/migrations/001_foundation.sql`                                                                                | must-read  | execute  | `stg_foundation_smoke` 基线 | 9.3     |
| `backend/app/db/migrations/011_layer1_tables.sql`                                                                             | must-read  | execute  | `axis_observation`          | 9.5     |
| `backend/app/db/write_manager.py`                                                                                             | must-read  | execute  | upsert                      | 9.7     |
| `backend/app/ops/sandbox_clean_write/rehearsal_loader.py`                                                                     | must-read  | execute  | staging                     | 9.3–9.6 |
| `backend/app/ops/sandbox_clean_write/limited_production_entry.py`                                                             | must-read  | execute  | promote 改点                | 9.5–9.8 |
| `backend/app/layer1_axes/ingestion_evidence.py`                                                                               | must-read  | execute  | macro 映射                  | 9.5     |
| `tests/test_round3g_limited_production_clean_write.py`                                                                        | must-read  | execute  | 回归                        | 9.8     |
| `tests/test_round3g_limited_production_rollback.py`                                                                           | must-read  | execute  | 回归                        | 9.8     |
| `tests/test_write_manager.py`                                                                                                 | must-read  | execute  | upsert 对照                 | 9.7     |
| `tests/test_schema_contract.py`                                                                                               | must-read  | execute  | 013 contract                | 9.1     |
| `MIGRATION_MAP.md`                                                                                                            | must-read  | both     | 边界                        | 9.0     |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                                                                                           | audit-only | audit    | §5.0.1                      | A1      |
| `MODULE_COMPLETION_RATING.md`                                                                                                 | audit-only | audit    | 完成度                      | A1      |

### 3.1 禁止改（manifest · forbidden）

| path                                                 | audience | for  |
| ---------------------------------------------------- | -------- | ---- |
| `specs/datasource_registry/source_registry.yaml`     | execute  | 全步 |
| `specs/datasource_registry/source_capabilities.yaml` | execute  | 全步 |
| `specs/contracts/source_route_contract.yaml`         | execute  | 全步 |

## 4. 已并入冻结任务卡（Execute 禁止读 `research/*`）

| 来源                                        | 并入 frozen        | 摘要               |
| ------------------------------------------- | ------------------ | ------------------ |
| `research/plan-boot.md`                     | §2.8、§8           | 前提与禁止主库     |
| `research/brainstorm-session.md`            | §1.1               | 无 VIEW；013+014   |
| `research/grill-me-session.md`              | §1.1、§6.1、§8、§9 | 三域；cninfo 列    |
| `research/spec-driven-development-notes.md` | §5–§6              | 契约→测；rollback  |
| `research/to-issues-slices.md`              | §9                 | S0–S10 依赖        |
| `research/gitnexus-summary.md`              | §4、§5             | promote 硬编码风险 |
| `research/project-overview.md`              | §5                 | G3–G6              |
| `research/adversarial-audit-report.md`      | §8、§9             | B01–B10 修复对照   |

## 5. Audit 追溯集

| 类别     | 文件                                     |
| -------- | ---------------------------------------- |
| frozen   | `frozen/R3H_06_CLEAN_SCHEMA.md`          |
| PASS     | `R3H_PASS_EXECUTION_PLAN.md`             |
| gaps     | `R3G_MASS_REHEARSAL_OPEN_GAPS.md` §2     |
| 对抗闭环 | `research/adversarial-audit-report.md`   |
| omission | `research/project-map-omission-check.md` |
