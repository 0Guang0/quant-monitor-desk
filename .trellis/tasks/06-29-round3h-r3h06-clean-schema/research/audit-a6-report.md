# A6 audit-perf — R3H-06 Clean Schema 性能审计

> **维度：** A6 · performance-engineer + doubt-driven-development  
> **任务：** `06-29-round3h-r3h06-clean-schema`（R3H-06 · Wave 1 DDL）  
> **仓库：** `C:\Users\Guang\Desktop\quant-monitor-desk`  
> **日期：** 2026-06-29  
> **模式：** Audit（只读，无 commit、无改码）

---

## 总判定

| 项                   | 值                                |
| -------------------- | --------------------------------- |
| **verdict**          | **SKIP**                          |
| **BLOCKING**         | 0                                 |
| **NON-BLOCKING**     | 5                                 |
| **Info**             | 2                                 |
| **AUDIT.plan §1 A6** | **SKIP** — schema 任务无 hot path |

---

## Scorecard（静态审计 + pytest durations 参考）

| 指标               | 值           | 来源                    | 阈值（Plan 冻结） | 状态        |
| ------------------ | ------------ | ----------------------- | ----------------- | ----------- |
| LCP / INP / CLS    | not measured | —                       | CWV               | —（无 Web） |
| smoke 端到端耗时   | not measured | Plan 未挂载             | —                 | SKIP        |
| ResourceGuard 触发 | not measured | promote 路径有调用      | 未冻结            | SKIP        |
| r3h06 最慢单测     | 0.61s        | pytest `--durations=10` | 未冻结            | 参考 only   |
| migration 013/014  | DDL only     | 静态审阅                | 未冻结            | SKIP        |
| promote 批大小     | ≤1200 理论   | contract 10 sym × 120d  | r3g03 cap         | 有界        |

> **Artifacts used:** `uv run pytest tests/test_r3h06_clean_schema.py -q --basetemp=.audit-sandbox/pytest --durations=10`（12 passed，~7.5s 总时长）  
> **Stack detected:** Python 单机 pipeline + DuckDB；DDL + sandbox promote；无 API/前端 hot path；非 Web 应用

---

## GitNexus 爆炸半径（参考）

| 符号                           | 方向     | risk        | 说明                                       |
| ------------------------------ | -------- | ----------- | ------------------------------------------ |
| `WriteManager.write`           | upstream | **LOW**     | d=1；Tests 模块直接调用                    |
| `populate_staging_from_bundle` | —        | **UNKNOWN** | 索引未收录（新符号）；静态审阅 3 处 caller |

**结论：** 无 CRITICAL/HIGH；与 AUDIT.plan「schema 无 hot path」一致。

---

## 1. SKIP 理由（§3.6 等价 · 与 AUDIT.plan §1 A6 一致）

> Plan 原文：**「SKIP — schema 任务无 hot path」**

### 1.1 五条证实

1. **任务性质为 DDL + 路由 SSOT** — migration 013/014 仅 `CREATE TABLE` / staging 重建；无生产调度、无 FastAPI 路由、无用户可见延迟面。
2. **frozen §7 明确不扩张 ResourceGuard** — 「ResourceGuard 不在本卡扩张 cap」；perf 验收非本卡 DoD。
3. **无冻结 perf 阈值** — frozen §9–§11 仅 pytest + `loop_maintain`；无 `production_equivalent_smoke.py`、无 MASTER §10 时长/内存行。
4. **写路径仍走既有 R3G-03 有界 promote** — `sandbox_clean_write_contract.yaml`：`r3g03_max_symbols: 10`、`r3g03_max_window_days: 120`；测试 fixture ≤10 symbols / ≤120d（frozen §7）。
5. **禁止主库 / 全市场** — frozen §2.8 #3、§8 Must not：不写 `quant_monitor.duckdb`、禁止全市场 migration dry-run。

### 1.2 必查项结论（AUDIT 派发检查）

| 检查项                     | 结论                                             | 证据                                                                                                      |
| -------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| migration 013/014 全表扫描 | **无运行时全表扫**                               | 013 仅 `CREATE TABLE IF NOT EXISTS`；014 `DROP` + `CREATE` 仅 `stg_foundation_smoke`（staging ephemeral） |
| promote 批大小             | **有界**                                         | `limited_production_entry` 传 `candidate.max_rows`；contract 限 symbol/window；fixture `max_rows: 100`    |
| staging 无界 I/O           | **当前有界；结构性缺口见 NB-3/NB-4**             | `max_rows` 行级 cap；`json.loads` 全文件读见 NB-3                                                         |
| OHLCV 列扩增对 write path  | **列宽 +14 列；pilot 量级可忽略；规模化见 NB-1** | 014 列序与 `security_bar_1d` 对齐；`WriteManager` 全列 upsert                                             |

---

## 2. 计划外 perf 风险扫描

> 按 `audit-adversarial-authority.md` A6：Plan 标 SKIP 仍须对抗搜索 hot path、无界 I/O、批大小/内存尖峰。

### 2.1 计划外 perf 风险表

| ID     | 区域          | 位置                                                  | 描述                                                                                                                        | 影响                                                                                             | 严重度           | 与本卡关系                                                                                         |
| ------ | ------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------- | -------------------------------------------------------------------------------------------------- |
| NB-1   | SQL / upsert  | `write_manager.py` `_build_merge_sql`                 | `upsert_by_pk` = `DELETE FROM target WHERE EXISTS (staging …)` + 全列 `INSERT SELECT`；`_count_pk_matches` 同类 EXISTS 扫描 | **potential impact：** target 表达百万行时每次 promote 可能全表或大范围扫描；pilot ≤~1200 行无感 | **NON-BLOCKING** | R3H-06 将 bar 从 `append_only`→`upsert_by_pk` **放大**既有模式；Wave 3 规模化前需 `MERGE`/索引策略 |
| NB-2   | I/O / staging | `rehearsal_loader.py` `populate_*_from_bundle`        | 逐行 `INSERT`（每行一次 `con.execute`），非 bulk/`executemany`                                                              | **potential impact：** max_rows≈1200 时 ~1200 次 round-trip；毫秒–秒级，非 pilot 瓶颈            | **NON-BLOCKING** | 014 OHLCV 列增宽略增单条 payload；可 `INSERT SELECT` 或 `executemany` 优化                         |
| NB-3   | 内存 / ingest | `rehearsal_loader.py` `_baostock_staging_rows`        | `json.loads(bars_path.read_text())` 全文件入内存；行数由 `max_rows` 截断但**文件字节无硬顶**                                | **potential impact：** 恶意/超大 `bars.json` 可触发内存尖峰                                      | **NON-BLOCKING** | 继承 R3G loader；非 R3H-06 新增；与 `GLOBAL_RESOURCE_LIMITS` §3「禁止全历史读入」精神相关          |
| NB-4   | 契约 / cap    | `approval_contract.py` `validate_r3g03_source_caps`   | 校验 symbol 数、window 天数；**未**将 `max_rows` 硬顶为 `symbols × window_days`                                             | **potential impact：** approval 可设 `max_rows` 远大于实际窗口行数（fixture 已用 100）           | **NON-BLOCKING** | 继承 R3G-03；`no_cap_expansion` 仅布尔，不量化 max_rows                                            |
| NB-5   | 迁移 / DDL    | `014_stg_bar_ohlcv.sql`                               | `DROP TABLE IF EXISTS stg_foundation_smoke` 后重建；PK 从 `(instrument_id, trade_date)` 扩为含 `adjustment_type`            | **potential impact：** 升级时清空 staging 残留（设计允许）；无 clean 表数据迁移                  | **NON-BLOCKING** | 符合 `duckdb_and_parquet.md` §4.1 staging 可重建                                                   |
| INFO-1 | 迁移          | `013_clean_domain_tables.sql`                         | 纯 `CREATE IF NOT EXISTS` 新表                                                                                              | 无现有表全表扫                                                                                   | **Info**         | 符合预期                                                                                           |
| INFO-2 | 守卫          | `limited_production_entry.py` / `rehearsal_runner.py` | promote 前 `ResourceGuard().check()`                                                                                        | pilot 路径仍有系统级硬停                                                                         | **Info**         | 本卡未改 guard 阈值                                                                                |

**显式声明：** 已对照 frozen `R3H_06_CLEAN_SCHEMA.md` §7/§9、`AUDIT.plan.md` §1 A6、`sandbox_clean_write_contract.yaml`、`write_manager.py`、`rehearsal_loader.py`、migration 013/014、`agents/audit-adversarial-authority.md`、`agents/performance-engineer.md`；**无 BLOCKING perf 项**。

### 2.2 Hot path

| 路径                        | 是否 hot           | 说明                                 |
| --------------------------- | ------------------ | ------------------------------------ |
| migration apply（013/014）  | **否**             | 一次性 DDL；非请求路径               |
| sandbox promote（R3G-03）   | **否（本卡）**     | 显式用户审批 + cap；非默认生产热路径 |
| `WriteManager.write` upsert | **否（当前量级）** | 有界 staging；规模化后见 NB-1        |
| 前端 / API                  | **未涉及**         | 本卡 scope 外                        |

### 2.3 OHLCV 列扩增 — write path 细化

| 维度         | 变更前（001 staging）         | 变更后（014）                                      | perf 含义                                           |
| ------------ | ----------------------------- | -------------------------------------------------- | --------------------------------------------------- |
| staging 列数 | 5 数据列 + PK(2)              | 12 数据列 + PK(3)                                  | 单行 ~7 个新增 DOUBLE/VARCHAR                       |
| PK 粒度      | `(instrument_id, trade_date)` | `+ adjustment_type`                                | 同标的多复权类型分行；行数上界 ×复权种类（通常 ≤3） |
| WriteManager | 列序必须完全匹配              | `_assert_staging_columns_match` 每次写 PRAGMA 双表 | 固定小表 O(1)；无全表                               |
| upsert 语义  | 原 r3g03 `append_only` 叠行   | `upsert_by_pk` DELETE+INSERT                       | 正确性换略增写放大（NB-1）                          |

**pilot 量级估算：** 10 symbols × 120 days × 1 adjustment ≈ 1200 行；14 列 × 8B 量级 ≈ 百 KB staging，可忽略。

### 2.4 migration 013/014 与「全表扫描」澄清

| Migration | 操作                                            | 是否扫描已有 clean 大表                                           |
| --------- | ----------------------------------------------- | ----------------------------------------------------------------- |
| 013       | `CREATE TABLE IF NOT EXISTS` ×4（含 3 staging） | **否** — 空表创建                                                 |
| 014       | `DROP` + `CREATE` `stg_foundation_smoke`        | **否** — 仅 staging；不 `ALTER`/`INSERT SELECT` `security_bar_1d` |

**计划外风险：** 若运维误对含数据的 pilot DB 反复 apply 014，仅丢 staging 行，不影响 clean 域表。

---

## 3. DOUBT（doubt-driven-development）

| 疑点                                                          | 结论                                                                       |
| ------------------------------------------------------------- | -------------------------------------------------------------------------- |
| SKIP 是否遗漏 smoke？                                         | **否** — AUDIT.plan §1 + frozen §11 无 perf 阈值                           |
| 013/014 是否会在生产库全表迁移？                              | **否** — 无 `INSERT SELECT`/`UPDATE` 全表；本卡禁止写主库                  |
| OHLCV 扩列是否 BLOCKING？                                     | **否** — pilot 有界；Wave 3 前登记 NB-1/NB-2 即可                          |
| idempotency 测 0.61s 是否回归？                               | **否** — 无冻结基线；DuckDB fixture 启动主导                               |
| `rehearsal_runner` 用 `bundle.staged_row_count` 作 max_rows？ | **有界于 r3g01 cap**（3 sym / 30d）；与 r3g03 promote 路径不同，非本卡新增 |

---

## 4. §3.6 证据表（SKIP 专用）

| 指标                                                         | 阈值（Plan 冻结）     | 实测           | 证据                     |
| ------------------------------------------------------------ | --------------------- | -------------- | ------------------------ |
| `test_r3h06_clean_schema.py`                                 | exit 0（A8 子集）     | 12 passed      | `--durations=10`         |
| 最慢 call `test_idempotency_duplicatePromote_rowCountStable` | **未冻结**            | 0.61s          | 同上                     |
| smoke 端到端                                                 | **未冻结**            | **未测**       | SKIP                     |
| ResourceGuard 阈值                                           | eco profile（GLOBAL） | **未实测触发** | 静态：promote 路径有调用 |
| 内存峰值                                                     | **未冻结**            | **未测**       | fixture KB 级            |

---

## 5. 计划外发现

| ID   | 发现                                                      | 严重度           |
| ---- | --------------------------------------------------------- | ---------------- |
| NB-1 | `upsert_by_pk` DELETE…EXISTS 在 target 规模化时潜在全表扫 | **NON-BLOCKING** |
| NB-2 | staging 逐行 INSERT，无 bulk 写                           | **NON-BLOCKING** |
| NB-3 | `bars.json` 全文件 `json.loads`，无字节 cap               | **NON-BLOCKING** |
| NB-4 | `max_rows` 未与 symbol×window 硬绑定                      | **NON-BLOCKING** |
| NB-5 | 014 DROP staging 升级清空（设计内）                       | **NON-BLOCKING** |
| —    | hot path / 生产无界 I/O / 本卡新 perf 阈值缺失            | **无 BLOCKING**  |

---

## 6. 正面观察

- **三域路由 SSOT**（`clean_write_targets.py`）避免错误表写入的重复扫描/回滚成本。
- **staging 有界加载**：`staging_rows_from_bundle` 用 `min(max_rows, bundle.staged_row_count)` + 窗口过滤。
- **promote 仍经 ResourceGuard + DbValidationGate + WriteManager** 链，未绕过治理。
- **frozen §7** 显式禁止全市场与主库写，缩小 perf 验收面。
- **pytest idempotency** 0.61s 级，无异常慢测尖峰。

---

## 7. 结论与建议（Audit 级）

**A6 审计判定：SKIP（维持）。**

R3H-06 为 Wave 1 DDL + sandbox 路由收口，无生产 hot path、无冻结 perf SLA。migration 013/014 不产生 clean 表全表扫描；promote 批大小受 r3g03 contract 约束；OHLCV 扩列在 pilot 量级下对 write path 影响可忽略。

**Wave 3（R3H-08）前建议（非本卡阻断）：**

1. 评估 `upsert_by_pk` 在 `security_bar_1d` 百万行下的 `EXPLAIN` / `MERGE` 替代（NB-1）。
2. staging populate 改 bulk insert（NB-2）。
3. 在 `validate_r3g03_source_caps` 增加 `max_rows ≤ symbols × window_days`（或 contract 显式 `r3g03_max_rows`）（NB-4）。

---

## 全部发现项汇总

| ID       | 标题                               | 区域          | 严重度       | 影响类型         | 建议                                |
| -------- | ---------------------------------- | ------------- | ------------ | ---------------- | ----------------------------------- |
| **SKIP** | schema 任务无 hot path             | Plan          | —            | —                | 维持 AUDIT.plan A6 SKIP             |
| NB-1     | upsert DELETE…EXISTS 规模化扫描    | SQL / Network | NON-BLOCKING | potential impact | Wave 3 前 EXPLAIN + MERGE/索引      |
| NB-2     | staging 逐行 INSERT                | I/O           | NON-BLOCKING | potential impact | `executemany` 或 `INSERT SELECT`    |
| NB-3     | bars.json 全文件读入内存           | Memory        | NON-BLOCKING | potential impact | 流式/字节 cap 或 Parquet 证据       |
| NB-4     | max_rows 缺 contract 硬顶          | Network       | NON-BLOCKING | potential impact | `validate_r3g03_source_caps` 扩检   |
| NB-5     | 014 DROP staging 升级清空          | Loading       | NON-BLOCKING | potential impact | 文档已符合 staging 语义；无需本卡改 |
| INFO-1   | 013 纯 CREATE 无扫表               | Loading       | Info         | —                | 无动作                              |
| INFO-2   | promote 路径 ResourceGuard 仍在    | Rendering     | Info         | —                | 无动作                              |
| **正面** | r3g03 symbol/window cap + 三域路由 | —             | —            | —                | 保持                                |
| **正面** | idempotency pytest sub-second      | —             | —            | —                | 保持                                |

**BLOCKING 合计：0 · NON-BLOCKING：5 · Info：2**
