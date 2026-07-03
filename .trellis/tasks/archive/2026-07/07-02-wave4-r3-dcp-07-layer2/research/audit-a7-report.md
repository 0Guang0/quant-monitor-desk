# Audit A7 — tmp_path 隔离 / 主库零污染（R3-DCP-07）

| 元信息   | 值                                 |
| -------- | ---------------------------------- |
| 维度     | A7 隔离库 / 无生产 DuckDB 写       |
| 任务     | `07-02-wave4-r3-dcp-07-layer2`     |
| 协议     | `plan_protocol_version: 4.1`       |
| 模板     | `agents/database-administrator.md` |
| 审计日期 | 2026-07-02                         |

---

## 维度证据 §3.7

### 0. 审计范围（AUDIT.plan §2 A7 = tmp_path 隔离）

活卡 ENTRY §2 约束：`replay 隔离库；禁止 silent 主库写`；**不在范围：新 migration**。本维对照 DCP-06 同型 A7，聚焦 DCP-07 新增/改动文件的 DB 触达与路径隔离；**不**要求 init/migrate 两遍 walkthrough（无新 migration DDL）。

| 路径                                                           | 角色                                                             |
| -------------------------------------------------------------- | ---------------------------------------------------------------- |
| `backend/app/layer2_sensors/clean_observation_reader.py`       | S00 读路径（注入 `con`）                                         |
| `backend/app/layer2_sensors/sensor_loader.py`                  | `production_clean_replay` mode + `CLEAN_REPLAY_REGISTRY_FIXTURE` |
| `backend/app/layer2_sensors/observation.py`                    | `assert_observation_source` fred/staged 绑定                     |
| `backend/app/layer2_sensors/snapshot_builder.py`               | clean replay 观测源断言切换                                      |
| `tests/layer1_clean_e2e_support.py`                            | 复用 `bootstrap_layer1_clean_db`（DCP-06）                       |
| `tests/test_layer2_clean_reader.py`                            | S00 契约测（4 DB + 1 YAML）                                      |
| `tests/test_layer2_vix_clean_e2e.py`                           | S01 e2e：clean 读 + snapshot 写                                  |
| `tests/fixtures/layer2_cross_asset_registry_clean_replay.yaml` | clean replay registry fixture                                    |

**GitNexus `detect_changes`（worktree `quant-monitor-desk-wt-dcp07`，scope=all）：**

| 指标               | 值                                                   |
| ------------------ | ---------------------------------------------------- |
| changed_symbols    | 8                                                    |
| affected_processes | 6（`Build_daily_snapshots` ×5 · `Sync_registry` ×1） |
| risk_level         | HIGH（代码变更爆炸半径；**非**隔离失败）             |

`impact(CrossAssetSnapshotBuilder, upstream)` → **LOW**，direct=1（`__init__.py` import）。

### 1. Grep：`ConnectionManager` · `DATA_ROOT` · `duckdb` · `quant_monitor` · `QMD_DATA_ROOT`

| 文件                                         | 命中                                                                      | 判定                                                               |
| -------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `clean_observation_reader.py`                | **0** DB import                                                           | 仅 SQL 经入参 `con`；fail-closed 源校验                            |
| `test_layer2_clean_reader.py`                | 经 `bootstrap_layer1_clean_db(tmp_path)`                                  | 4/4 DB 测均 `tmp_path`                                             |
| `test_layer2_vix_clean_e2e.py`               | `ConnectionManager(tmp_path / name)`                                      | `layer1_clean.duckdb` + `layer2_vix_clean_wm.duckdb` 均在 tmp_path |
| `test_layer2_clean_reader.py`（无 tmp_path） | `test_layer2CleanReplayRegistry_loadsP0VixPrimaryFred`                    | 只读 YAML fixture；**无 DB 触达**                                  |
| DCP-07 新增/改动范围                         | **0** 条 `quant_monitor.duckdb` / `data/duckdb/` / `QMD_DATA_ROOT` 硬编码 | —                                                                  |
| 工作区 canonical DB                          | `data/duckdb/quant_monitor.duckdb` **不存在**                             | 无默认主库可被 silent 写                                           |

### 2. `bootstrap_layer1_clean_db` 写面追溯（复用 DCP-06）

```text
tmp_path/layer1_clean.duckdb          ← apply_migrations + seed_macro_series INSERT
tmp_path/layer1_clean.duckdb.write.lock
tmp_path/layer2_vix_clean_wm.duckdb   ← S01 snapshot/lineage 写（_layer2_cm）
```

- `seed_macro_series` → `insert_axis_observation` 均在调用方传入的 `con` 上执行。
- `Layer2CleanObservationReader.read_observations(con, …)` 不持有 `ConnectionManager`。
- `CrossAssetRegistryLoader.load` 仅解析 YAML；写路径 `CrossAssetRegistryWriter` **未**被 DCP-07 新测调用。

### 3. `tmp_path` 覆盖率（DCP-07 新增测）

| 模块                           | 测数  | 需 DB | `tmp_path` | 无 DB 测说明       |
| ------------------------------ | ----- | ----- | ---------- | ------------------ |
| `test_layer2_clean_reader.py`  | 5     | 4     | 4/4        | registry YAML 只读 |
| `test_layer2_vix_clean_e2e.py` | 1     | 1     | 1/1        | —                  |
| **合计**                       | **6** | **5** | **5/5**    | 1 测无 DB 触达     |

### 4. `production_clean_replay` mode — 误开 live 风险（plan-doubt-review Q3）

| 检查项                          | 结果                                                                             |
| ------------------------------- | -------------------------------------------------------------------------------- |
| mode 白名单                     | 仅 `staged_fixture_only` \| `production_clean_replay`                            |
| `primary_source=fred` P0 白名单 | `P0_CLEAN_REPLAY_ASSET_IDS = {"L2-VIX"}`；非 P0 抛 `CrossAssetRegistryLoadError` |
| clean 读 fail-closed            | `FORBIDDEN_FALLBACK_SOURCE_PREFIXES` 拒绝 staged_fixture / macro_supplementary   |
| ADR-032 §4                      | replay default = tmp_path isolated DB；无 live FRED primary                      |

### 5. `CrossAssetSnapshotBuilder` — e2e 链 DB 打开路径

| 检查项                  | 结果                                                                 |
| ----------------------- | -------------------------------------------------------------------- |
| `build_daily_snapshots` | 纯内存观测 + lineage 构建；**不** `duckdb.connect`                   |
| 默认 `ResourceGuard()`  | `con=None`；e2e 中 guard 不打开 canonical DB 文件                    |
| snapshot 持久化         | 仅 `Layer2SnapshotWriter(wm_cm)` 且 `wm_cm` 绑定 `tmp_path/*.duckdb` |

### 6. 独立复跑（audit-sandbox）

```text
uv run pytest tests/test_layer2_clean_reader.py tests/test_layer2_vix_clean_e2e.py -q
```

| 步骤              | 命令 | exit  | 关键证据                                     |
| ----------------- | ---- | ----- | -------------------------------------------- |
| DCP-07 隔离测全集 | 上式 | **0** | `6 passed`（`.audit-sandbox/pytest-a7.log`） |

### 7. 基础设施观察（非 DCP-07 引入 · 不进 findings）

`ConnectionManager.writer()` 经 `_apply_pragmas` 可能对 `DATA_ROOT/cache/duckdb_tmp` 执行 `mkdir`（DuckDB spill）；**不**打开 `quant_monitor.duckdb`。本票全部 migration 与数据落在 `tmp_path/*.duckdb`；与 ADR-032 replay 政策及 DCP-06 A7 同型。ENTRY 明示无新 migration → 省略 init/migrate 两遍 + kill 异常场景（registry 标准 A7 checklist 项，本票 Plan 覆写为 tmp_path 隔离）。

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

已对抗搜索：DCP-07 全部新增/改动文件 `ConnectionManager|DATA_ROOT|duckdb|quant_monitor|QMD_DATA_ROOT`；`clean_observation_reader` import 面；`production_clean_replay` P0 白名单与 `assert_observation_source`；`CrossAssetRegistryWriter` / `CrossAssetSnapshotBuilder` 默认 DB 打开路径；`ResourceGuard(con=None)` 侧效应；`plan-doubt-review` Q3/Q5 replay 政策；GitNexus `detect_changes` + `impact(CrossAssetSnapshotBuilder)`；canonical `quant_monitor.duckdb` 存在性；AUDIT.plan §2 A7 与 ENTRY §2「不在范围：新 migration」边界。
