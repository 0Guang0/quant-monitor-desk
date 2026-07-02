# Audit A7 — Ops / DuckDB 隔离与 Live 验收

> **维：** A7 (audit-ops)  
> **任务：** `.trellis/tasks/m-data-03-tier-a-live` — M-DATA-03 全 scope  
> **协议：** `plan_protocol_version: 4.1`  
> **模板：** `agents/database-administrator.md` + `agents/sre-engineer.md`（adjunct）  
> **权威：** ADR-034 · `AUDIT.plan.md` §1 A7 · `to-issues-slices.md` S00-INFRA / S-ACCEPT  
> **审计日期：** 2026-07-03  
> **模型：** composer-2.5

---

## 维度证据

### AUDIT.plan §2 A7 对照

| 检查项                                    | 锚点                                                                          | 证据                                                     | 判定        |
| ----------------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------- | ----------- |
| `DATA_ROOT` 须 `.audit-sandbox/m-data-03` | `tier_a_live_acceptance.py` L58–72 `assert_isolated_live_data_root`           | 路径段检查 + `ISOLATED_ROOT_REQUIRED`                    | **PASS**    |
| 主库路径拒绝                              | L38–55 `canonical_main_db_paths` / `is_canonical_main_*`                      | harness 参数化负向测绿                                   | **PASS**    |
| `QMD_ALLOW_LIVE_FETCH` fail-closed        | `product_live_gate.py` L24–40 · `validate_live_acceptance_env` L102–106       | harness 3 项负向测 + CLI exit 2 绿                       | **PASS**    |
| 默认 pytest 不跑 network                  | `conftest.py` L156–162 · harness `test_networkMark_skippedInDefaultPytestRun` | subprocess 收集 skipped                                  | **PASS**    |
| ops inspect 路径                          | `tier_a_live_incremental_dispatch.py` L451 `DbInspector(...).inspect()`       | 程序化 inspect；`test_ops_db_inspector.py` 证明 CLI 同源 | **PASS**    |
| sandbox DB registry sync                  | `tier_a_live_acceptance.py` L132–154 `ensure_isolated_db`                     | 运行时探针：`registry_rows=25`（见 §3.2）；**无单测**    | **PARTIAL** |
| 零主库污染                                | ADR-034 · AUDIT.plan §1 PASS 门槛                                             | 路径拒绝有测；**无 mtime/size 指纹断言**                 | **PARTIAL** |

### §3.1 冻结命令 / pytest

| 步骤                       | 命令                                                                                    | exit  | 关键输出                             |
| -------------------------- | --------------------------------------------------------------------------------------- | ----- | ------------------------------------ |
| harness 单测               | `uv run pytest tests/test_tier_a_live_harness.py tests/test_tier_a_live_dispatch.py -q` | **0** | `17 passed, 1 skipped`（2026-07-03） |
| 负向：主库路径             | `test_assertIsolatedLiveDataRoot_rejectsCanonicalMainDb`                                | 绿    | `CANONICAL_MAIN_DB_REJECTED`         |
| 负向：非 m-data-03 sandbox | `test_assertIsolatedLiveDataRoot_rejectsNonMdata03Sandbox`                              | 绿    | `ISOLATED_ROOT_REQUIRED`             |
| 负向：无 live opt-in       | `test_validateLiveAcceptanceEnv_rejectsWithoutLiveFetchOptIn`                           | 绿    | `LIVE_FETCH_NOT_OPTED_IN`            |
| 负向：silent fallback      | `test_livePort_noSilentFallbackToMock`                                                  | 绿    | `LIVE_FETCH_REJECTED`                |
| CLI exit 2 契约            | `test_tierALiveAcceptanceCli_exit2WhenEnvInvalid`                                       | 绿    | `returncode == 2`                    |

### §3.2 `ensure_isolated_db` 运行时探针（审计复验）

```text
QMD probe root: .audit-sandbox/m-data-03/a7-audit-probe
db: .../duckdb/quant_monitor.duckdb
registry_rows: 25
main db: data/duckdb/quant_monitor.duckdb exists (4468736 bytes) — probe 未触主库路径
```

`apply_migrations` + `SourceRegistry.sync_to_db(tombstone_missing=True)` 在隔离库可执行；**缺 RED 单测锁定行为**。

### §3.3 写路径追溯（GitNexus + 静态）

| 入口                                              | DB 解析                                                                                  | 隔离闸                                                                | 备注                                                                    |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `run_acceptance` → `validate_live_acceptance_env` | `resolve_live_data_root`                                                                 | `assert_isolated_live_data_root` + live gate                          | 金路径                                                                  |
| `run_source_live_acceptance`                      | `ensure_isolated_db(data_root)` + `os.environ["QMD_DATA_ROOT"]`                          | 同上                                                                  | 设 env 后调 dispatch                                                    |
| `run_tier_a_live_incremental`（10 源）            | `_prepare_sandbox` → `data_root/duckdb/quant_monitor.duckdb`                             | **无** `assert_isolated_live_data_root`                               | 依赖上游                                                                |
| `run_tier_a_live_incremental`（fred）             | `_sync_fred_macro_incremental` 读 **env** `QMD_DATA_ROOT`（`data_commands.py` L205–206） | `assert_sandbox_db_allowed`（仅拒 canonical / 要求 `.audit-sandbox`） | **不**强制 `m-data-03` 段；inspect 用 **param** `data_root`（L450–451） |

### §3.4 GitNexus

| 动作                                                              | 结果                                                                             |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `query(..., repo=quant-monitor-desk)` tier A live sandbox         | 返回 live_pilot / DbInspector 邻近流；**未索引** `tier_a_live_acceptance` 新符号 |
| `impact(assert_isolated_live_data_root, repo=quant-monitor-desk)` | **Target not found**（索引 stale）                                               |
| `impact(ensure_isolated_db, repo=quant-monitor-desk)`             | **Target not found**                                                             |
| `context(run_tier_a_live_incremental)`                            | 审计策略拦截（只读约束）                                                         |

> 索引 stale：`node .gitnexus/run.cjs analyze` 后重跑 impact。本维以 pytest 输出 + 静态追溯 + 运行时探针为准。

### §3.5 DOUBT（未单独升格）

| 疑点                                                  | 结论                                                                                        |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| fred 无 env 时回落 `PROJECT_ROOT/data`                | **fail-closed**：`assert_sandbox_db_allowed` 拒 canonical（`rehearsal_runner.py` L107–109） |
| live e2e 用 `*_incr.duckdb` 非 `quant_monitor.duckdb` | 与 acceptance harness 命名不一致；e2e 走 `isolated_live_data_root`，**不触主库**            |
| `DbInspector` vs `qmd data inspect` CLI               | `test_qmdOps_cli_invokesSameInspector` 已等价；**非 finding**                               |

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

---

## 计划外发现

| ID        | P   | 标题                                                     | 锚点                                                                                     | 根因                                                                                                                                                                               | 修复方案                                                                                                                                                                                                                                    | 验证                                                                                                                                                                                             |
| --------- | --- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A7-P1-001 | P1  | fred dispatch：sync 用 env、inspect 用 param，路径可分裂 | `tier_a_live_incremental_dispatch.py` L114–120 vs L450–451；`data_commands.py` L205–206  | fred 分支跳过 `_prepare_sandbox`；`_sync_fred_macro_incremental` 只读 `QMD_DATA_ROOT` env，而 `DbInspector` 用 `data_root` 参数；调用方 env/param 不一致时 sync 写 A、inspect 查 B | 在 `run_tier_a_live_incremental` 入口统一 `assert_isolated_live_data_root(data_root)` 并 `os.environ["QMD_DATA_ROOT"]=str(data_root)`；fred 分支改调 `_prepare_sandbox(data_root)` 或显式传入 `data_root` 给 `_sync_fred_macro_incremental` | 新增 `test_tier_a_live_dispatch.py`：env 指向 A、`data_root` 指向 B 时抛 `TierALiveEnvError` 或强制同根；`uv run pytest tests/test_tier_a_live_dispatch.py tests/test_tier_a_live_harness.py -q` |
| A7-P2-001 | P2  | `ensure_isolated_db` registry sync 无单测                | `tier_a_live_acceptance.py` L132–154                                                     | `sync_to_db(tombstone_missing=True)` 是 S-ACCEPT inspect/路由前提，但 harness 未断言 `source_registry` 行数                                                                        | 在 `test_tier_a_live_harness.py` 增 `test_ensureIsolatedDb_syncsRegistryRows`：`isolated_live_data_root` 上调 `ensure_isolated_db`，断言 `COUNT(*) FROM source_registry >= 11`（Tier A 源）                                                 | `uv run pytest tests/test_tier_a_live_harness.py::test_ensureIsolatedDb_syncsRegistryRows -q`                                                                                                    |
| A7-P2-002 | P2  | dispatch 层缺 ADR-034 隔离复验                           | `tier_a_live_incremental_dispatch.py` `run_tier_a_live_incremental` L445                 | 仅 acceptance 包装器校验；dispatch 可被直接 import，`_prepare_sandbox` 不检查 `m-data-03` 段                                                                                       | `run_tier_a_live_incremental` 首行 `assert_isolated_live_data_root(data_root)`                                                                                                                                                              | 新增负向测：对 `.audit-sandbox/other-task` 调 `run_tier_a_live_incremental` 抛 `ISOLATED_ROOT_REQUIRED`；`uv run pytest tests/test_tier_a_live_dispatch.py -q`                                   |
| A7-P3-001 | P3  | 缺主库指纹零污染断言                                     | AUDIT.plan §1「零主库污染」；对比 `scripts/wave3_live_production_acceptance.py` L139–155 | harness 仅路径拒绝，未像 wave3 脚本记录 canonical SHA256/mtime 前后                                                                                                                | harness 增 `test_acceptanceProbe_doesNotMutateCanonicalMainDb`：探针前后比对 `data/duckdb/quant_monitor.duckdb` size+mtime（或 hash）                                                                                                       | `uv run pytest tests/test_tier_a_live_harness.py -q`；主库文件存在时断言不变                                                                                                                     |

已对抗搜索：`tier_a_live_acceptance.py` 全路径闸 · `tier_a_live_incremental_dispatch.py` 11 源写路径 · `conftest.py` `isolated_live_data_root` · `test_tier_a_live_harness.py` 负向矩阵 · `product_live_gate.py` · `data_commands._sync_fred_macro_incremental` sandbox denylist · `ensure_isolated_db` 运行时 registry 探针 · GitNexus query/impact（索引 stale）· 11 源 `*_incremental_e2e.py` `@pytest.mark.network` + fixture 用法 · `wave3_live_production_acceptance.py` 指纹模式。

[REDACTED]
