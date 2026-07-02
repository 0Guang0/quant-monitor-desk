# Audit A7 — sandbox 隔离 / init 幂等（R3-DCP-08）

| 元信息   | 值                                      |
| -------- | --------------------------------------- |
| 维度     | A7 运维 / sandbox 隔离 / migration 幂等 |
| 任务     | `07-02-wave4-r3-dcp-08-layer4`          |
| 协议     | `plan_protocol_version: 4.1`            |
| 模板     | `agents/database-administrator.md`      |
| 审计日期 | 2026-07-02                              |
| 工作目录 | `quant-monitor-desk-wt-dcp08`           |

---

## 维度证据 §3.7

### 0. 审计范围（Execute diff + 活卡 A7）

AUDIT.plan §2 冻结 A7 要点：**sandbox 隔离**。对照 DCP-08 引入/修改的 DB 触达面：

| 路径 | 角色 |
| ---- | ---- |
| `backend/app/layer4_markets/clean_read.py` | Tier A clean 只读 SQL（注入 `con`） |
| `backend/app/layer4_markets/market_structure.py` | `tier_a_clean` 分支；`clean_con` 必填 fail-closed |
| `backend/app/cli/data_commands.py` | mootdx dry-run JSON 预览（无 DB 写） |
| `tests/layer4_clean_e2e_support.py` | 共享 `bootstrap_layer4_clean_db` |
| `tests/test_layer4_clean_read.py` | S08-READ / ADAPTER 单测 |
| `tests/test_layer4_us_equity_clean_e2e.py` | S08-E2E |
| `tests/test_layer4_market_structure.py` | 022 回归（staged fixture；预存） |

### 1. GitNexus 追溯

| 查询 | 结果 |
| ---- | ---- |
| `context(apply_migrations)` | 22 上游调用方；含 `init_db.main`、`_ensure_sandbox_db`、pytest bootstrap；每 migration 事务 BEGIN/COMMIT/ROLLBACK |
| `context(ConnectionManager)` | 生产路径经 `db_path` 注入；Layer4 clean 测试显式 `tmp_path/layer4_clean.duckdb` |
| `impact(apply_migrations)` | CRITICAL 半径（共享 migration SSOT；本票未改 migrate.py） |
| `detect_changes(worktree=wt-dcp08, scope=all)` | 7 文件变更；新符号（`USEquityCleanMarketAdapter` 等）**未入索引**（未 commit）— 以 grep + 跑测为准 |
| `query(layer4 tier_a_clean)` | 无 DCP-08 新符号（索引滞后）；已用 `context(ConnectionManager)` + 文件级 grep 补全 |

### 2. Grep：DB 污染面（DCP-08 范围）

| 文件 | `ConnectionManager` / `DATA_ROOT` / `quant_monitor` / `QMD_DATA_ROOT` | 判定 |
| ---- | --------------------------------------------------------------------- | ---- |
| `clean_read.py` | **0** | 纯 SQL + 注入 `con`；无默认库 |
| `market_structure.py` | 仅错误文案含 `duckdb` | 不打开连接 |
| `layer4_clean_e2e_support.py` | `ConnectionManager(db_path=tmp_path/"layer4_clean.duckdb")` | 显式 tmp_path |
| `test_layer4_clean_read.py` | 经 bootstrap | 3/4 测 `tmp_path`；1 测无 DB（SSOT calendar） |
| `test_layer4_us_equity_clean_e2e.py` | 经 bootstrap | 1/1 `tmp_path` |
| `test_layer4_market_structure.py` | `_MUTATION_ROOT = PROJECT_ROOT/.audit-sandbox/layer4_market_mutations` | 文件 fixture 变异；**非** canonical DuckDB |
| `data_commands.py` diff | 仅改 preview dict | 无 DB I/O |
| DCP-08 全范围 | **0** 条硬编码 `quant_monitor.duckdb` / `data/duckdb/` | — |

### 3. `bootstrap_layer4_clean_db` 写面

```text
tmp_path/layer4_clean.duckdb          ← apply_migrations + 种子 INSERT
tmp_path/layer4_clean.duckdb.write.lock ← ConnectionManager 写锁
```

- `USEquityCleanMarketAdapter` / `aggregate_breadth_from_bars` 仅操作传入 `con`。
- `MarketStructureBuilder.build(source_mode=tier_a_clean)`：`clean_con is None` → `Layer4MarketError`（fail-closed）。
- 二次 bootstrap 同库：`bar_rows=3→3`，`migrations=15→15`（幂等，数据未损坏）。

### 4. `tmp_path` 覆盖率（DCP-08 新增测）

| 模块 | 测数 | 需 DB | `tmp_path` |
| ---- | ---- | ----- | ---------- |
| `test_layer4_clean_read.py` | 4 | 3 | 3/3 |
| `test_layer4_us_equity_clean_e2e.py` | 1 | 1 | 1/1 |
| **DCP-08 新增合计** | **5** | **4** | **4/4** |

022 回归 `test_layer4_market_structure.py`：18 测，DB 无关（staged YAML/JSON fixture + `_MUTATION_ROOT` 文件沙箱）。

### 5. audit-sandbox：init/migrate 两遍 + 异常场景

**环境：** `<task>/.audit-sandbox/`，`QMD_DATA_ROOT=<task>/.audit-sandbox/data`

| 步骤 | 命令 | exit | 关键证据 |
| ---- | ---- | ---- | -------- |
| 1 首次 init | `QMD_DATA_ROOT=.../data uv run python scripts/init_db.py` | 0 | `applied` 15 项（001→015）；DB 在 sandbox 内 |
| 2 二次 init | 同上 | 0 | `applied none (up to date)` |
| 3 schema 快照 | `a7_schema_check.py` | 0 | `migration_count=15`；`last=015_dcp05_tier_a_clean`；`table_count=30` |
| 4 kill 中途 | `a7_kill_scenario.py`（terminate @0.3s） | kill=1 | 进程被终止；无 stderr 污染 |
| 5 kill 后重跑 | `init_db.py` | 0 | 补跑 002→015；`post_recovery_migration_count=15` |
| 6 恢复后再 init | `init_db.py` | 0 | `applied none (up to date)` |
| 7 canonical 库 | `Test-Path data/duckdb/quant_monitor.duckdb` | — | **不存在**（主库零污染） |

**DOUBT 核对：**

- 第二次 init 不只「不报错」：`schema_version` 仍 15 行；checksum 与 spec 一致。
- kill 后：`schema_version` 与 migration 表一致（15 项），重跑可 idempotent 完成。

### 6. Layer4 pytest 独立复跑

```text
uv run pytest tests/test_layer4_clean_read.py \
  tests/test_layer4_us_equity_clean_e2e.py \
  tests/test_layer4_market_structure.py -q \
  --basetemp=<task>/.audit-sandbox/pytest
```

| exit | 结果 |
| ---- | ---- |
| 0 | 22 passed |

### 7. 基础设施观察（非 DCP-08 引入 · 不进 findings）

- `ConnectionManager._apply_pragmas` 可能对 `DATA_ROOT/cache/duckdb_tmp` 建目录（DuckDB spill）；本票全部 DB 数据与 migration 落在 `tmp_path/*.duckdb` 或 task `.audit-sandbox`。
- `_MUTATION_ROOT` 为 022 预存 fixture 变异模式（`PROJECT_ROOT/.audit-sandbox/layer4_market_mutations/{tmp_path.name}`），与 DCP-06 e2e 同型；非 canonical DB。
- GitNexus 索引未含未 commit 的 DCP-08 新文件；Execute 合入后建议 `node .gitnexus/run.cjs analyze` 刷新。

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

已对抗搜索：DCP-08 全 diff 文件 `ConnectionManager|DATA_ROOT|duckdb|quant_monitor|QMD_DATA_ROOT`；`clean_read.py` import 面；`MarketStructureBuilder._build_tier_a_clean` fail-closed；`apply_migrations` 事务边界（GitNexus `context`）；`_MUTATION_ROOT` 与 canonical DB 路径；kill 后 schema_version 一致性；`data_commands.py` preview 写面；plan-doubt-review NFR-1 sandbox 政策。
