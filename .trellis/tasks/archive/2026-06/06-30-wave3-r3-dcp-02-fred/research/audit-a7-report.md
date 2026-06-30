# Audit A7 — Ops / CLI Sandbox

> **维：** A7 (audit-ops)  
> **任务：** `.trellis/tasks/06-30-wave3-r3-dcp-02-fred`  
> **协议：** debt-lite Phase 8D（`AUDIT.plan.md` · `AUDIT_PROD_ROOT=.audit-sandbox/user-live`）  
> **Worktree：** `quant-monitor-desk-wt-dcp02` · branch `feature/wave3-r3-dcp-02-fred`  
> **审计日期：** 2026-06-30  
> **模型：** composer-2.5  
> **模板：** `agents/database-administrator.md` + `agents/sre-engineer.md`（adjunct）

---

## 维度证据

### AUDIT.plan §2 A7 冻结命令

| 步骤                | 命令                                                                                                                       | exit  | 关键输出 / 证据                  |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------- | ----- | -------------------------------- |
| 1 沙箱准备          | `mkdir .trellis/tasks/06-30-wave3-r3-dcp-02-fred/.audit-sandbox/user-live/duckdb`                                          | 0     | 目录创建成功                     |
| 2 dry-run CLI       | `QMD_DATA_ROOT=<task>/.audit-sandbox/user-live uv run qmd-data data sync --domain macro_series --source-id fred --dry-run` | **0** | 见下方 JSON                      |
| 3 canonical 无污染  | 对比 `data/duckdb/quant_monitor.duckdb` mtime/size 前后                                                                    | —     | **未变**（见 §3.1）              |
| 4 env gate          | 同上 `QMD_DATA_ROOT` + `--no-dry-run`，**无** `QMD_ALLOW_LIVE_FETCH`                                                       | **2** | `LIVE_FETCH_REJECTED`（见 §3.2） |
| 5 forbidden sync/\* | `git diff master -- backend/app/sync/`                                                                                     | 0     | **无 diff**                      |
| 6 pytest 回归       | `uv run pytest tests/test_fred_macro_incremental_cli.py tests/test_data_cli_contract.py::test_syncDryRunDoesNotWrite -q`   | **0** | `5 passed`                       |

**步骤 2 完整输出（2026-06-30）：**

```json
{
  "command": "sync",
  "dry_run": true,
  "product_live": false,
  "data_domain": "macro_series",
  "operation": "fetch_macro_series",
  "window": { "start": null, "end": null, "since": null },
  "route_status": "READY",
  "selected_source_id": "fred",
  "resource_guard_decision": "OK",
  "message": "dry-run only; no fetch or DB writes performed",
  "source_id": "fred"
}
```

### §3.1 Canonical 写隔离（dry-run）

| 指标                                           | 执行前                         | dry-run 后 | 判定                             |
| ---------------------------------------------- | ------------------------------ | ---------- | -------------------------------- |
| `data/duckdb/quant_monitor.duckdb` mtime (UTC) | `2026-06-29T18:47:22.1675738Z` | 同左       | **无写**                         |
| size (bytes)                                   | `9973760`                      | `9973760`  | **无写**                         |
| sandbox DB 存在                                | 否                             | 否         | dry-run 不触库（符合 `message`） |

`QMD_DATA_ROOT` 解析为绝对路径：`<worktree>/.trellis/tasks/06-30-wave3-r3-dcp-02-fred/.audit-sandbox/user-live`。

### §3.2 Env gate（fail-closed · SRE 异常场景菜单）

| 场景           | 命令                                                                                                    | exit  | 结构化错误                                                 |
| -------------- | ------------------------------------------------------------------------------------------------------- | ----- | ---------------------------------------------------------- |
| 无 live opt-in | `qmd-data data sync --domain macro_series --source-id fred --no-dry-run`（`QMD_ALLOW_LIVE_FETCH` 未设） | **2** | `error_code: LIVE_FETCH_REJECTED` · `docs_anchor: ADR-027` |

与 `product_live_gate.assert_product_live_allowed`（`backend/app/datasources/product_live_gate.py` L30–40）及 `test_fredIncrementalCli_execute_rejectsWithoutLiveEnv` 一致；**未触达** `_sync_fred_macro_incremental` 写库段。

### §3.3 Forbidden `sync/*` 未改写

```text
git diff master --name-only -- backend/app/sync/
(空)
```

`orchestrator.py` · `runners.py` · `watermark*.py` 相对 master **零 diff**。本轨仅 **import** `DataSyncOrchestrator`（`data_commands.py` L164）；watermark 落在 `ops/fred_incremental_watermark.py`（ponytail 注释 L3–4）。

### §3.4 CLI 默认只读 / ResourceGuard

| 检查                              | 锚点                                | 结果                              |
| --------------------------------- | ----------------------------------- | --------------------------------- |
| sync 默认 `--dry-run`             | `cli/main.py` L30–35 `default=True` | PASS                              |
| dry-run 早返回、无 fetch/DB       | `data_commands.py` L71–123          | PASS                              |
| ResourceGuard 在 dry-run 路径检查 | `data_commands.py` L89–103          | PASS（decision=OK）               |
| fred dry-run 专用 route 预览      | `data_commands.py` L72–93           | PASS（`selected_source_id=fred`） |

### §3.5 静态 DOUBT（未升格为 finding）

| 疑点                                               | 结论                     | 说明                                                                                                                                                       |
| -------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--no-dry-run` 无 `QMD_DATA_ROOT` 时回落 canonical | **已知风险 · A1 已登记** | `_sync_fred_macro_incremental` L195–196 `_path_env(..., PROJECT_ROOT/data)`；**本次 A7 未执行写路径**；canonical `fetch_log` 污染见 A1-P1-003 / batch25 测 |
| GitNexus 新符号未索引                              | NOTE                     | `query`/`context` 未命中 `sync_plan` · `run_fred_macro_incremental`（索引 stale）；以独立命令输出 + pytest 为准                                            |

### GitNexus

| 动作                                                              | 结果                                                                |
| ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| `query("qmd data sync fred macro_series dry-run CLI")`            | 返回 DataSourceService.fetch / live_pilot 相关流；未索引新 CLI 符号 |
| `query("sync_plan _sync_fred_macro_incremental data_commands")`   | 返回 DataSourceService / sync jobs 流；同上                         |
| `context("sync_plan")` / `context("assert_product_live_allowed")` | Symbol not found                                                    |

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

已对抗搜索：`sync/orchestrator.py` · `sync/runners.py` · `sync/watermark*.py` 磁盘 diff · dry-run canonical mtime/size · env gate 无 opt-in 负例 · ResourceGuard dry-run 路径 · `QMD_DATA_ROOT` 沙箱解析 · GitNexus 新符号索引 · 非 dry-run canonical 回落（记入证据 DOUBT，A1-P1-003 已覆盖，本维未重复开 finding）。

---

## 关账自检

- [x] §维度裁决 ∈ {PASS, FAIL}
- [x] findings 表均为占位行
- [x] AUDIT.plan §2 A7 冻结 dry-run + 沙箱 + 无 canonical 写：**满足**
- [x] env gate fail-closed：**满足**
- [x] forbidden `sync/*` 未触：**满足**
- [x] 独立 pytest CLI 契约测：**5 passed**
- [x] 未改代码 · 未 commit
