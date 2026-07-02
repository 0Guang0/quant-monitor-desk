# Audit A7 — tmp_path 隔离 / 主库零污染（R3-DCP-06）

| 元信息   | 值                                |
| -------- | --------------------------------- |
| 维度     | A7 隔离库 / 无生产 DuckDB 写      |
| 任务     | `wave4-r3-dcp-06-five-axis-clean` |
| 协议     | `plan_protocol_version: 4.1`      |
| 审计日期 | 2026-07-02                        |

---

## 维度证据 §3.7

### 0. 审计范围（相对 `master` diff）

| 路径                                                  | 角色                              |
| ----------------------------------------------------- | --------------------------------- |
| `tests/layer1_clean_e2e_support.py`                   | 共享 `bootstrap_layer1_clean_db`  |
| `tests/test_layer1_clean_reader.py`                   | S00 + S07 row_cap                 |
| `tests/test_layer1_environment_clean_e2e.py`          | S01                               |
| `tests/test_layer1_credit_stress_clean_e2e.py`        | S02                               |
| `tests/test_layer1_risk_appetite_clean_e2e.py`        | S03                               |
| `tests/test_layer1_liquidity_clean_e2e.py`            | S04                               |
| `tests/test_layer1_sentiment_clean_e2e.py`            | S05                               |
| `tests/test_layer1_five_axis_panel_clean_smoke.py`    | S06 + S07 K1/ResourceGuard/window |
| `backend/app/layer1_axes/clean_observation_reader.py` | S00 读路径（注入 `con`）          |

### 1. Grep：`ConnectionManager` · `DATA_ROOT` · `duckdb` · `quant_monitor` · `QMD_DATA_ROOT`

| 文件                                         | 命中                                                                      | 判定                              |
| -------------------------------------------- | ------------------------------------------------------------------------- | --------------------------------- |
| `layer1_clean_e2e_support.py`                | `ConnectionManager(db_path=tmp_path/"layer1_clean.duckdb")`               | 显式 tmp_path；无默认路径         |
| `clean_observation_reader.py`                | **0**                                                                     | 不 import DB；仅 SQL 经入参 `con` |
| `test_layer1_clean_reader.py`                | 经 `bootstrap_layer1_clean_db(tmp_path)`                                  | 6/6 测均 `tmp_path`               |
| `test_layer1_*_clean_e2e.py`（五轴）         | 经 bootstrap                                                              | 各 1 测；均 `tmp_path`            |
| `test_layer1_five_axis_panel_clean_smoke.py` | `PROJECT_ROOT` 仅读 `layer1_source_whitelist.yaml`；DB 测经 bootstrap     | 无 canonical DB 路径              |
| 全范围                                       | **0** 条 `quant_monitor.duckdb` / `data/duckdb/` / `QMD_DATA_ROOT` 硬编码 | —                                 |

### 2. `bootstrap_layer1_clean_db` 写面追溯

```text
tmp_path/layer1_clean.duckdb          ← apply_migrations + 种子 INSERT（axis_observation / security_bar_1d）
tmp_path/layer1_clean.duckdb.write.lock ← ConnectionManager 写锁
```

- 种子 helper（`seed_macro_series` / `seed_spy_bars` / COT weekly）均在调用方传入的 `con` 上执行，无全局 DB 单例。
- `fred_macro_incremental_support.insert_axis_observation` 仅操作传入 `con`（其自有 bootstrap 亦 `tmp_path/fred_inc.duckdb`）。

### 3. `tmp_path` 覆盖率（DB 触达测）

| 模块                                         | 测数   | 需 DB  | `tmp_path` | 无 DB 测说明                                 |
| -------------------------------------------- | ------ | ------ | ---------- | -------------------------------------------- |
| `test_layer1_clean_reader.py`                | 6      | 6      | 6/6        | —                                            |
| `test_layer1_environment_clean_e2e.py`       | 1      | 1      | 1/1        | —                                            |
| `test_layer1_credit_stress_clean_e2e.py`     | 1      | 1      | 1/1        | —                                            |
| `test_layer1_risk_appetite_clean_e2e.py`     | 1      | 1      | 1/1        | —                                            |
| `test_layer1_liquidity_clean_e2e.py`         | 1      | 1      | 1/1        | —                                            |
| `test_layer1_sentiment_clean_e2e.py`         | 1      | 1      | 1/1        | —                                            |
| `test_layer1_five_axis_panel_clean_smoke.py` | 5      | 2      | 2/2        | MagicMock ResourceGuard；YAML 只读；常量断言 |
| **合计**                                     | **16** | **14** | **14/14**  | 2 测无 DB 触达                               |

### 4. `clean_observation_reader` — 无默认 `ConnectionManager`

| 检查项                                              | 结果                             |
| --------------------------------------------------- | -------------------------------- |
| import `ConnectionManager` / `DATA_ROOT` / `duckdb` | 否                               |
| `read_macro_clean_observations(con, …)`             | `con` 由测试在 tmp_path 库上提供 |
| `read_bar_history(con, …)`                          | 同上                             |
| 生产路径 fallback                                   | 无                               |

`AxisFeatureEngine` / `AxisInterpretationEngine` 在 e2e 链中亦无 DB import（纯内存观测序列）。

### 5. S07 repair 测隔离（caps · K1 · ResourceGuard · window）

| 测名                                                                  | 切片                 | 隔离                                                        |
| --------------------------------------------------------------------- | -------------------- | ----------------------------------------------------------- |
| `test_layer1CleanReader_macroRespectsWhitelistRowCap`                 | S07 row_cap          | `tmp_path` bootstrap                                        |
| `test_layer1CleanReader_barHistoryRespectsWhitelistRowCap`            | S07 bar cap          | `tmp_path` bootstrap                                        |
| `test_dcp06K1_whitelistAlignsP0CleanBindings`                         | S07 K1               | 只读 `specs/…/layer1_source_whitelist.yaml`                 |
| `test_layer1FiveAxisPanel_resourceGuardOnMigratedDb`                  | S07 真 ResourceGuard | `tmp_path` bootstrap；`ResourceGuard(con=…)` 不打开主库文件 |
| `test_layer1FiveAxisPanel_windowLenWithinWhitelistCap`                | S07 window           | 无 I/O                                                      |
| `test_layer1FiveAxisPanel_resourceGuardHardStop_blocksFeatureCompute` | S06/A4               | MagicMock；无 DB                                            |

### 6. 独立复跑

```text
uv run python -m pytest \
  tests/test_layer1_clean_reader.py \
  tests/test_layer1_environment_clean_e2e.py \
  tests/test_layer1_credit_stress_clean_e2e.py \
  tests/test_layer1_risk_appetite_clean_e2e.py \
  tests/test_layer1_liquidity_clean_e2e.py \
  tests/test_layer1_sentiment_clean_e2e.py \
  tests/test_layer1_five_axis_panel_clean_smoke.py -q
```

| exit | 结果      |
| ---- | --------- |
| 0    | 16 passed |

### 7. 基础设施观察（非 DCP-06 引入 · 不进 findings）

`ConnectionManager.writer()` 经 `_apply_pragmas` 可能对 `DATA_ROOT/cache/duckdb_tmp` 执行 `mkdir`（DuckDB spill 目录）；**不**打开 `quant_monitor.duckdb`。本票全部 DB 数据与 migration 落在 `tmp_path/*.duckdb`；与 `plan-doubt-review` replay 政策及 DCP-05 e2e 同型。若需全文件系统沙箱化，属 `ConnectionManager` 横切升级，非本票 AC。

---

## §维度裁决

**PASS**

---

## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：全 9 文件 `ConnectionManager|DATA_ROOT|duckdb|quant_monitor|QMD_DATA_ROOT`；`clean_observation_reader` 符号与 import 面；`ConnectionManager._apply_pragmas` DATA_ROOT cache 侧效应；S07 repair 五测；`AxisFeatureEngine`/`AxisInterpretationEngine`/`ResourceGuard` DB 打开路径；`master` diff 文件清单与 `plan-spec` NFR-1。
