# Audit A7 报告 — R3H-06 Clean Schema

| 字段       | 值                                                                                                    |
| ---------- | ----------------------------------------------------------------------------------------------------- |
| 维度       | **A7** Ops / DBA / SRE                                                                                |
| 任务       | `06-29-round3h-r3h06-clean-schema`                                                                    |
| 仓库       | `C:\Users\Guang\Desktop\quant-monitor-desk`                                                           |
| 分支       | `feature/round3h-r3h06-clean-schema`                                                                  |
| HEAD       | `ed0981c1`                                                                                            |
| 模式       | **只读 Audit**（不改代码、不 commit、不写 production DB）                                             |
| Agent 模板 | `agents/database-administrator.md` · `agents/sre-engineer.md` · `agents/devops-incident-responder.md` |
| 对抗权威   | `agents/audit-adversarial-authority.md`                                                               |
| 审计日期   | 2026-06-29                                                                                            |

---

## 1. AUDIT.plan §1 A7 冻结条件

| 项               | 冻结要求                                           | 审计结论                                                                                                                                                                                           |
| ---------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| promote 主库拒写 | promote 仍拒 `quant_monitor.duckdb` canonical 路径 | **PASS** — `_assert_production_db_allowed` / `assert_sandbox_db_allowed` 三路径 denylist 未削弱；`test_PromoteRunner_refusesCanonicalProductionDbPath` + rehearsal CLI 5 测绿                      |
| 无新写主库 CLI   | 本卡不得新增默认写主库的 ops CLI                   | **PASS** — `scripts/qmd_ops.py` 仍仅 `db-inspect`（只读）+ `data` 转发；无 `--write`/`--migrate`/`--sql`；`r3g03_isolated_pilot_dry_run.py` 为既有 R3G-03 脚本，仅更新 target 常量，非本卡新增入口 |
| CLI 边界         | audit-sandbox 下 CLI 边界 fail-closed              | **PASS** — 契约禁 `--write`/`--migrate`/`--sql`/`--enable-qmt`；`test_qmdOps_cli_rejectsForbiddenSqlFlag` 等回归绿                                                                                 |
| 通过条件         | CLI 边界 + promote 主库 denylist                   | **PASS** — 见 §3 运维证据表                                                                                                                                                                        |

**说明：** 本任务 A7 主判据为 **promote 主库 denylist + ops CLI 只读边界**；标准「kill migrate 中途恢复」因 013/014 为 additive/staging rebuild、AUDIT.plan 未单列 kill 场景，以 **两遍 init_db 幂等 + migration pytest** 替代（§3.1）。

---

## 2. 运维路径表（Ops Path Matrix）

| 路径                                                   | 类型               | 写库？                 | 默认/典型 DB                                 | 主库 denylist                        | 本卡变更                                                                                  | 证据                                                       |
| ------------------------------------------------------ | ------------------ | ---------------------- | -------------------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `qmd ops db-inspect` / `scripts/qmd_ops.py db-inspect` | 只读巡检 CLI       | **否**                 | `$QMD_DATA_ROOT/duckdb/quant_monitor.duckdb` | N/A（只读 open）                     | 契约 `key_tables` 加入 L5 两表；`future_phase_key_tables: []`                             | `test_ops_db_inspector.py` 28 passed / 1 skipped           |
| `scripts/init_db.py`                                   | schema 初始化      | **是**（DDL）          | 同上                                         | 无 denylist（运维负责路径）          | 应用 **013+014**                                                                          | 沙盒两遍 init：`applied [...013,014]` → `applied none`     |
| `run_limited_production_entry`                         | R3G-03 promote     | **是**（cap + 四件套） | approval 指定 **isolated pilot**             | **三路径硬拒**                       | target 路由 → `security_bar_1d` / `cn_announcement_clean`                                 | `test_PromoteRunner_refusesCanonicalProductionDbPath`      |
| `run_sandbox_clean_write_rehearsal`                    | R3G-01 rehearsal   | **是**（sandbox only） | `--sandbox-db`                               | **同 denylist**                      | bar rehearsal 仍 legacy smoke；promote 分离                                               | rehearsal canonical 拒写 5 测绿                            |
| `scripts/r3g03_isolated_pilot_dry_run.py`              | 人工 pilot promote | **是**（`--execute`）  | pilot DuckDB only                            | 经 `run_limited_production_entry` 链 | `target_table` 常量 → `security_bar_1d` 等                                                | 脚本描述 + promote gate 链                                 |
| `DbInspector` / `mutation_proof.key_table_row_counts`  | 只读证明           | **否**                 | 任意 path                                    | N/A                                  | `KEY_TABLES` 含 `instrument_registry`/`security_bar_1d`；**不含** `cn_announcement_clean` | GitNexus impact `DbInspector` → MEDIUM（5 direct callers） |
| `WriteManager` + `resolve_clean_write_target`          | clean promote 内核 | **是**                 | pilot / pytest tmp                           | 不经 CLI 直达主库                    | 新 SSOT `clean_write_targets.py`                                                          | `test_r3h06_clean_schema.py`                               |

**DOUBT（DBA）：** 是否存在绕过 promote gate 直写主库的新 CLI？→ `git diff master -- scripts/` 本卡仅改 `r3g03_isolated_pilot_dry_run.py`（target 常量）与 `check_test_catalog.py`；`qmd_ops.py` **零 diff**；`rg add_parser` 无本卡新增 promote/db-write 子命令。

---

## 3. §3.7 运维证据表

### 3.1 Database Administrator（migration 幂等 / schema 一致性）

| 步骤             | 命令                                                                          | exit  | 关键输出 / 证据                                                                                                            |
| ---------------- | ----------------------------------------------------------------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------- |
| 沙盒 init 第一遍 | `QMD_DATA_ROOT=<task>/.audit-sandbox/data uv run python scripts/init_db.py`   | **0** | `applied [... '013_clean_domain_tables', '014_stg_bar_ohlcv']`                                                             |
| 沙盒 init 第二遍 | 同上                                                                          | **0** | `applied none (up to date)`                                                                                                |
| migration 回归   | `uv run pytest tests/test_schema_migration.py -q --tb=no`                     | **0** | **10 passed**                                                                                                              |
| migration 矩阵   | `uv run pytest tests/test_migration_coverage.py -q --tb=no`                   | **0** | **7 passed**（L5 由 DEFERRED → MIGRATED）                                                                                  |
| db-inspect @ 013 | `uv run python scripts/qmd_ops.py db-inspect --db <sandbox-db> --format json` | **0** | `instrument_registry`/`security_bar_1d` exists=true, row_count=0；status=WARN（空库预期）                                  |
| 本地陈旧 DB init | `uv run python scripts/init_db.py`（默认 `data/`）                            | **1** | `MigrationChecksumError: 010_lineage_not_null checksum mismatch` — **环境卫生**，非 013/014 回归；沙盒 fresh DB 已证明幂等 |

**MIGRATION_COVERAGE ↔ 013/014 对照：**

| 对象                         | 文档状态   | 013/014 实际          | schema.sql          | 备注                                                                  |
| ---------------------------- | ---------- | --------------------- | ------------------- | --------------------------------------------------------------------- |
| `instrument_registry`        | DONE @ 013 | CREATE @ 013          | 对齐                | PK `instrument_id`                                                    |
| `security_bar_1d`            | DONE @ 013 | CREATE @ 013          | 对齐                | PK 含 `adjustment_type` + OHLCV                                       |
| `cn_announcement_clean`      | DONE @ 013 | CREATE @ 013          | 对齐                | metadata + 指针列                                                     |
| `stg_disclosure_smoke`       | DONE @ 013 | CREATE @ 013          | **未入 schema.sql** | staging-only；矩阵 §R3H 已记                                          |
| `stg_axis_observation_smoke` | DONE @ 013 | CREATE @ 013          | **未入 schema.sql** | macro promote staging                                                 |
| `stg_foundation_smoke`       | DONE @ 014 | **DROP+CREATE** @ 014 | 对齐（OHLCV+PK）    | 014 破坏性重建 staging；**无 down migration**（矩阵 L109–110 已声明） |

**Rollback 运维口径（矩阵 L109–110）：** 013/014 **无 down migration**；pilot 回滚靠 promote 前 `backup_or_snapshot_pointer` 快照恢复；共享 audit DB 禁止协调外 `DROP`。

### 3.2 SRE Engineer（fail-closed / 可靠性）

| 场景                      | 命令                                                                                                                  | exit  | 日志 / 证据                                                     |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------- | ----- | --------------------------------------------------------------- |
| promote 拒 canonical 主库 | `pytest tests/test_round3g_limited_production_clean_write.py::test_PromoteRunner_refusesCanonicalProductionDbPath -q` | **0** | `PRODUCTION_DB_PATH_REJECTED` / match `canonical production DB` |
| rehearsal 拒 canonical    | `pytest tests/test_round3g_sandbox_clean_write_rehearsal.py -k refusesCanonical -q`                                   | **0** | **5 passed**                                                    |
| db-inspect 只读契约       | `pytest tests/test_ops_db_inspector.py -q`                                                                            | **0** | **28 passed, 1 skipped**                                        |
| R3H-06 schema 回归        | `pytest tests/test_r3h06_clean_schema.py -q`                                                                          | **0** | **18 passed, 1 skipped**                                        |
| cninfo 不写 bar           | 含于 `test_r3h06_clean_schema.py`                                                                                     | **0** | `security_bar_1d` COUNT 不变（A3 交叉）                         |

**DOUBT（SRE）：** promote dry_run 是否静默 mutation？→ `limited_production_entry` 仍 `key_table_row_counts` 对比 + dry_run 禁 mutation；L5 bar 表已纳入 KEY_TABLES。

### 3.3 DevOps Incident Responder（RCA / 事故面）

| 检查项                                   | 结论                                                                                                                |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| 本卡新增 production clean-write CLI      | **无** — 仅既有 R3G-03 脚本 target 更新                                                                             |
| 主库 `quant_monitor.duckdb` promote 穿透 | **无** — denylist 三路径 + pytest                                                                                   |
| db-inspect 误写主库                      | **无** — `ConnectionManager.reader()`；契约禁 DML 动词                                                              |
| 014 staging DROP 生产面                  | **无** — 仅 `stg_foundation_smoke`；clean 表 013 CREATE IF NOT EXISTS                                               |
| Execute evidence 可 RCA                  | `execute-evidence/9.9-green.txt` + 沙盒 init 日志可复现                                                             |
| GitNexus 变更半径                        | `DbInspector` impact **MEDIUM**（5 direct：qmd_ops、mutation_proof、live_pilot、interface_probe、layer1 inventory） |

---

## 4. db_inspector 专项复核

| 检查点                        | 结论                   | 细节                                                                                                                    |
| ----------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `key_tables` L5 升级          | **PASS**               | `instrument_registry`、`security_bar_1d` 从 `future_phase_key_tables` 移至 `key_tables`                                 |
| `future_phase_key_tables: []` | **PASS**               | `db_inspector.py` 修复 falsy 误判（`if tables is None`）；空列表合法                                                    |
| 只读 invariant                | **PASS**               | 无 `writer()` / DML；`test_dbInspect_dbFile_unchanged`                                                                  |
| L5 专项 pytest                | **GAP（非 BLOCKING）** | 仅有 `test_dbInspect_layer1AxisTables_presentAfterMigration`；**无** L5 表 exists 断言（运行时 db-inspect JSON 已验证） |
| `cn_announcement_clean` 巡检  | **GAP（P2）**          | 未入 `key_tables`；disclosure promote 后主库 mutation proof 不完备（与 A3 F-01 一致）                                   |

---

## 5. 计划外发现

> 对抗性搜索：AUDIT.plan A7 · MIGRATION_COVERAGE · 013/014 SQL · `db_inspector` · `ops_db_inspect_contract.yaml` · promote/CLI 路径 · 沙盒 init 实测 · GitNexus impact。

| ID      | 发现                                                                                               | 严重度 | BLOCKING | 说明                                                                          |
| ------- | -------------------------------------------------------------------------------------------------- | ------ | -------- | ----------------------------------------------------------------------------- |
| O-A7-01 | `cn_announcement_clean` 未纳入 `KEY_TABLES` / mutation proof                                       | P2     | 否       | promote 路径已 fail-closed；旁路写 disclosure 表可能漏检（A3 F-01 同源）      |
| O-A7-02 | `test_ops_db_inspector` 缺 L5 表 post-013 回归                                                     | P3     | 否       | 仅 layer1 断言；建议补 `test_dbInspect_layer5Tables_presentAfterMigration013` |
| O-A7-03 | staging 表（`stg_disclosure_smoke`/`stg_axis_observation_smoke`）仅在 migration，不在 `schema.sql` | Info   | 否       | MIGRATION_COVERAGE 已记；运维须知 staging ≠ design SSOT                       |
| O-A7-04 | 014 `DROP TABLE stg_foundation_smoke` 无 down migration                                            | Info   | 否       | staging-only；fresh test DB 重跑 migration 即可；共享 DB 需协调               |
| O-A7-05 | 本地 `data/duckdb` 若已应用旧 010 checksum，`init_db` fail-closed                                  | Info   | 否       | 沙盒 fresh path 幂等正常；生产运维需备份后重建或 repair 010 行                |
| O-A7-06 | GitNexus 未索引 `_assert_production_db_allowed` / `clean_write_targets`                            | Info   | 否       | impact 返回 symbol not found；合并前建议 `node .gitnexus/run.cjs analyze`     |
| O-A7-07 | `db-inspect` 默认指向 canonical DB 路径但只读                                                      | Info   | 否       | 设计如此；不会 mutation；WARN 空库为预期                                      |

**DOUBT 扫描：**

| 类                                 | 结果       |
| ---------------------------------- | ---------- |
| 新增写主库 CLI                     | **未发现** |
| promote denylist 削弱              | **未发现** |
| db-inspect 写路径                  | **未发现** |
| 013/014 与 MIGRATION_COVERAGE 漂移 | **未发现** |

---

## 6. 全部发现项汇总

| ID      | 标题                                      | 维度   | 等级 | BLOCKING | 文件锚点                                      |
| ------- | ----------------------------------------- | ------ | ---- | -------- | --------------------------------------------- |
| F-01    | disclosure 表未入 KEY_TABLES              | A3/A7  | P2   | 否       | `ops_db_inspect_contract.yaml:164-185`        |
| F-02    | file_registry 指针无校验                  | A3     | P2   | 否       | `rehearsal_loader.py:301-305`                 |
| F-03    | announcement_url 无 scheme 限制           | A3     | P3   | 否       | `013_clean_domain_tables.sql`                 |
| F-04    | rehearsal_runner COUNT 未 quote_ident     | A3     | P3   | 否       | `rehearsal_runner.py:287`                     |
| F-05    | domain/target 错配缺契约层校验            | A3     | P3   | 否       | `limited_production_entry.py:541-545`         |
| F-06    | GitNexus 索引滞后                         | A3/A7  | Info | 否       | GitNexus impact                               |
| F-07    | R3G-01 rehearsal bar 仍 legacy smoke 路径 | A3     | Info | 否       | `rehearsal_runner.py:237-241`                 |
| F-A7-01 | L5 key_tables 无专项 pytest               | **A7** | P3   | 否       | `tests/test_ops_db_inspector.py`              |
| F-A7-02 | staging 表 schema.sql 分裂                | **A7** | Info | 否       | `013_clean_domain_tables.sql` vs `schema.sql` |
| F-A7-03 | 014 无 down migration（staging DROP）     | **A7** | Info | 否       | `MIGRATION_COVERAGE.md` L109-110              |
| F-A7-04 | 本地陈旧 DB 010 checksum 阻塞 init        | **A7** | Info | 否       | 沙盒 init 对比                                |

**BLOCKING 计数：0**

---

## 7. 判定

| 维度                    | 判定     | 理由                                                                      |
| ----------------------- | -------- | ------------------------------------------------------------------------- |
| **AUDIT.plan A7**       | **PASS** | promote canonical denylist intact；无新写主库 CLI；db-inspect 只读边界绿  |
| DBA migration adjunct   | **PASS** | 沙盒两遍 init 013/014 幂等；`test_schema_migration` 10/10；矩阵 7/7       |
| SRE fail-closed adjunct | **PASS** | canonical 拒写 pytest；db-inspect 28/28（1 skip）；R3H-06 18/18（1 skip） |
| Incident 生产写面       | **PASS** | 变更限于 DDL + pilot promote 路由；主库默认路径仍不可 promote             |

### 移交主会话 / 其他维度

- **F-01 / O-A7-01：** 建议 Repair 将 `cn_announcement_clean` 加入 `key_tables`（与 A3 一致）。
- **F-A7-01：** 可选补 L5 db-inspect pytest（非 A7 必达）。
- **F-A7-04：** 本地 dev 环境 010 checksum 需人工处理；不阻塞本卡 audit-sandbox 证据。

---

## 8. 参考命令（audit-sandbox 复现）

```powershell
# 沙盒 init 幂等
$env:QMD_DATA_ROOT = ".trellis/tasks/06-29-round3h-r3h06-clean-schema/.audit-sandbox/data"
uv run python scripts/init_db.py
uv run python scripts/init_db.py

# db-inspect @ 013
$db = ".trellis/tasks/06-29-round3h-r3h06-clean-schema/.audit-sandbox/data/duckdb/quant_monitor.duckdb"
uv run python scripts/qmd_ops.py db-inspect --db $db --format json

# A7 pytest 子集
uv run pytest tests/test_ops_db_inspector.py -q --tb=no
uv run pytest tests/test_round3g_limited_production_clean_write.py::test_PromoteRunner_refusesCanonicalProductionDbPath -q
uv run pytest tests/test_round3g_sandbox_clean_write_rehearsal.py -k refusesCanonical -q
uv run pytest tests/test_schema_migration.py tests/test_migration_coverage.py tests/test_r3h06_clean_schema.py -q --tb=no
```

---

_A7 只读审计完成（2026-06-29）。未修改仓库业务代码，未 commit。_
