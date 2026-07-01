# Audit A7 — ops/DB 隔离（R3-DCP-05 Tier A）

| 元信息   | 值                           |
| -------- | ---------------------------- |
| 维度     | A7 隔离库 / 主库零污染       |
| 任务     | `wave4-r3-dcp-05-tier-a`     |
| 协议     | `plan_protocol_version: 4.1` |
| 审计日期 | 2026-07-02                   |

---

## 维度证据 §3.7

### 1. tests 中 canonical 路径扫描

| 范围                                             | 结论                                                                   |
| ------------------------------------------------ | ---------------------------------------------------------------------- |
| `tests/test_*incremental*`（11 路 e2e + router） | **0** 条直接写 `PROJECT_ROOT/data/duckdb/`；e2e 均 `tmp_path/*.duckdb` |
| `tests/test_qmd_data_sync_tier_a_router.py`      | `sandbox_env` → `QMD_DATA_ROOT=<tmp>/.audit-sandbox/wave3-accept/data` |
| `tests/test_qmd_data_sync_baostock.py`           | 负向门控（canonical/user-live）                                        |

### 2. 增量真跑 production path guards（代码）

| 入口                           | non-dry-run 写保护                          |
| ------------------------------ | ------------------------------------------- |
| `sync_baostock_incremental`    | `assert_sandbox_db_allowed` + operator gate |
| `sync_mootdx_incremental`      | **同上**（实现对称）                        |
| `_sync_fred_macro_incremental` | 同上 + `assert_product_live_allowed`        |
| `tier_a_sync_router` 8/11 源   | `dry_run=False` → `USER_AUTH_REQUIRED`      |

### 3. GitNexus — `ConnectionManager`

`reader()` 使用 `read_only=True`；tier_a dry-run 经 `reader()` 无 migration。

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID        | P   | 标题                                              | 锚点                                                           | 根因                                                    | 修复方案                                                                                        | 验证                                                         |
| --------- | --- | ------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| A7-P2-001 | P2  | S08 mootdx CLI 缺 canonical/sandbox 门控靶向测    | `data_commands.py:504-554` · 无 `test_qmd_data_sync_mootdx.py` | 实现与 baostock 对称，但无 CLI 隔离回归测               | 新增 `tests/test_qmd_data_sync_mootdx.py`（refusesCanonicalDb · operatorAuth · user-live 拒绝） | `uv run pytest tests/test_qmd_data_sync_mootdx.py -q`        |
| A7-P2-002 | P2  | S12 tier_a 缺 8 源 non-dry-run fail-closed 靶向测 | `tier_a_sync_router.py:212-241` · router 测仅 dry_run          | 8 源 `dry_run=False` 代码抛 `USER_AUTH_REQUIRED` 但未测 | parametrize `bis`,`deribit` 等：`dry_run=False` → `CliFailure` `USER_AUTH_REQUIRED`             | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -q` |

---

## 计划外发现

| ID        | P   | 标题                                                          | 锚点                                              | 根因                                                                                    | 修复方案                                                                          | 验证                                           |
| --------- | --- | ------------------------------------------------------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------- |
| A7-P3-001 | P3  | tier_a dry-run 未设 QMD_DATA_ROOT 时可只读打开 canonical 主库 | `tier_a_sync_router.py:19-24` `_data_root_and_db` | `_path_env` 回落 `PROJECT_ROOT/data`；本机有 canonical db 时 dry-run 读生产水位（只读） | dry-run 要求 `QMD_DATA_ROOT` 含 `.audit-sandbox` 或对齐 baostock dry-run 空库行为 | 无 env + canonical 存在时 dry-run 不读生产水位 |

已对抗搜索：`tests/test_*incremental*` · `tier_a_sync_router.py` · `rehearsal_runner.assert_sandbox_db_allowed` · DEBT.plan production boundary。
