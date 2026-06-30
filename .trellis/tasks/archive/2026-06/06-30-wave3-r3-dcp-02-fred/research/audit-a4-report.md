# Audit A4 — Code Quality / Multi-axis Review

> **维：** A4 (audit-quality)  
> **任务：** `.trellis/tasks/06-30-wave3-r3-dcp-02-fred`  
> **协议：** debt-lite Phase 8D · `AUDIT.plan.md` §1 A4 行  
> **Worktree：** `../quant-monitor-desk-wt-dcp02` · branch `feature/wave3-r3-dcp-02-fred`  
> **审计日期：** 2026-06-30  
> **模板：** `agents/code-reviewer.md` · skills: code-review-and-quality + doubt-driven-development  
> **模型：** composer-2.5

---

## 维度证据

### AUDIT.plan §2 A4 验证矩阵（独立读码 + pytest）

| 检查项                            | 结果     | 证据                                                                                                                                                                                                                                                                                                                                           |
| --------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **watermark per-series 语义**     | PASS     | `fred_incremental_watermark.py` L17–32：`MAX(CAST(publish_timestamp AS DATE)) WHERE indicator_id = ?`；L74–89 `read_since_dates_for_series` 逐 series 独立 since；单测 `test_fredWatermark_multiSeries_independentWatermarks` 绿                                                                                                               |
| **PK `observation_id`**           | PASS     | `clean_write_targets.py` L41–47 `primary_keys=("observation_id",)`；`fred_incremental_run.py` L287–327 经 `resolve_clean_write_target("macro_series")` 传入 `primary_keys=target.primary_keys`；L62–65 `uuid5(NAMESPACE_URL, f"{indicator_id}\|{obs_date}\|{content_hash}")` 与 `observation_mapper._deterministic_observation_id` L26–28 同形 |
| **无 `trade_date` 误用**          | PASS     | `rg trade_date backend/app/ops/fred_*` 0 命中；`SyncJobSpec` 无 bar 域字段；`date_start`/`date_end` 为 None（L307–308）                                                                                                                                                                                                                        |
| **与 `clean_write_targets` 一致** | PASS     | `target_table=axis_observation` · `staging_table=stg_axis_observation_smoke` · `write_mode=upsert_by_pk`；`STAGING_TABLE` 常量与 SSOT 一致；staging 列用 `AXIS_OBSERVATION_DDL_COLUMNS`                                                                                                                                                        |
| **`datasource_service` 金路径**   | PASS     | `build_fred_incremental_service` → `DataSourceService` + `FredIncrementalFetchProxy`；`orch.run_incremental(..., datasource_service=proxy)` L320–327；e2e 测 docstring 明示金路径                                                                                                                                                              |
| **错误处理可观测**                | **FAIL** | 见 §计划内 A4-P1-001 / A4-P2-001 / A4-P2-002                                                                                                                                                                                                                                                                                                   |

### 维度证据 §3.4（多轴）

| 轴                  | 发现                                                                  | 证据                                                                |
| ------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Logic correctness   | 核心 macro 语义与 R3H-06 路由对齐                                     | 上表 PASS 行                                                        |
| Error handling      | 部分 series 失败仍报「completed」；adapter JSON 未包装                | `fred_incremental_run.py` L328–346 · L106 · `data_commands.py` L237 |
| Naming / boundaries | ops 模块边界清晰；runtime patch 有 ponytail 注释                      | `fred_incremental_run.py` L1–5 · L169–171                           |
| Duplication         | PK/行映射与 `observation_mapper` 平行实现（与 rehearsal_loader 同型） | L35–84 vs `observation_mapper.py` L26–28                            |
| Readability         | CLI dry-run 与 execute 装配重复（A2 已记）                            | `data_commands.py` L72–93                                           |
| Security（局部）    | live gate / 无 key 负例在 port 层                                     | `fred_port.py` L126–127 · port 测 L94–109                           |
| Test purpose        | 定向 13 passed, 1 skipped                                             | 见下                                                                |

### git diff 范围（worktree · 2026-06-30）

**已跟踪 modified（3）：** `fred_port.py` · `data_commands.py` · `main.py`  
**未跟踪核心（4+4 tests）：** `fred_incremental_watermark.py` · `fred_incremental_run.py` · `test_fred_macro_incremental_*.py` ×4 · `fred_macro_incremental_support.py`  
**说明：** `tests/test_catalog.yaml` 已 revert（A2 报告）；本维 diff 不含 catalog。

### 独立 pytest（A4 引用）

```text
uv run pytest tests/test_fred_macro_incremental_watermark.py \
  tests/test_fred_macro_incremental_port.py \
  tests/test_fred_macro_incremental_e2e.py \
  tests/test_fred_macro_incremental_cli.py -q
→ 13 passed, 1 skipped (live_smoke 无 FRED_API_KEY)
```

### GitNexus

| 动作                                                                | 结果                                                                                                                          |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `query("fred macro incremental run_incremental DataSourceService")` | 返回既有 live_pilot / Layer1 流；**未索引** `run_fred_macro_incremental` / `FredIncrementalFetchProxy`（worktree 未 analyze） |
| 判定                                                                | 以源码 + pytest 为准；索引 stale 不阻塞本维语义核对                                                                           |

### A4 checklist

- [x] 无 P0 逻辑/安全阻塞（macro PK / watermark / 金路径语义正确）
- [ ] 错误处理可观测 — **未满足**（部分失败静默、JSON 未包装）
- [x] 风格与邻近模块一致（rehearsal_loader macro 映射同型；karpathy 直写）
- [x] 测试变更保留五字段 purpose（定向测 Read 确认）
- [x] 判定基于读码 + pytest，非文档自述

### DOUBT（≥1 处错误处理/边界）

**是** — `run_fred_macro_incremental` 在 `result.status != "COMPLETED"` 时仍累积结果并正常返回；CLI 固定 `message: "fred macro incremental sync completed"`；`FredMacroStagingAdapter.fetch` L106 `json.loads` 无 PortError 包装。

**搜索范围：** `backend/app/ops/fred_*` · `fred_port.py` · `data_commands.py` L59–238 · `clean_write_targets.py` · `observation_mapper.py` · `rehearsal_loader._macro_observation_rows_from_bundle` · `sync/orchestrator.run_incremental` · 全 fred incremental 测 · `rg trade_date fred_*` · A1/A2 已报项（catalog / cite / canonical DB）— 不重复开 ID，canonical 默认路径见 A1-P1-003。

### 继承 prior reports（只读，不重复 ledger）

| 来源                                                   | 本维关系                                       |
| ------------------------------------------------------ | ---------------------------------------------- |
| A1-P1-003 canonical `fetch_log` / 默认 `QMD_DATA_ROOT` | ops/fail-closed；A4 证据已引用，不另开 finding |
| A2-P2-001 loop 内重复 `build_fred_incremental_service` | ponytail/perf；A4 仅交叉引用                   |
| A2 测试 duplicate helper                               | 可维护性；非 A4 阻塞轴                         |

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID        | P   | 标题                                 | 锚点                                                             | 根因                                                                                                                                     | 修复方案                                                                                                                                                                       | 验证                                                                                                                                    |
| --------- | --- | ------------------------------------ | ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| A4-P1-001 | P1  | 多 series 部分失败仍对外报成功       | `fred_incremental_run.py` L328–346 · `data_commands.py` L225–237 | `run_fred_macro_incremental` 循环内不检查 `result.status`；任意 FAILED_FINAL/RETRYABLE 仍 append 并返回；CLI `message` 恒为「completed」 | 聚合 `series_results`：若任一 `status != "COMPLETED"` 则 `FredIncrementalRunReport` 增 `overall_status="PARTIAL_FAILURE"` 或 raise `CliFailure`；CLI message 反映 worst status | 单测：mock 一 series PortError → payload/exception 含失败 series；`rg 'completed'` 在失败路径无 unconditional success                   |
| A4-P2-001 | P2  | staging adapter 未包装 JSON 解析失败 | `fred_incremental_run.py` L106                                   | `json.loads(payload.content)` 抛 `JSONDecodeError` 时 bypass `PortError` 路径，job 以未分类异常失败                                      | `try/except JSONDecodeError` → `FetchResult(status="FAILED", error_message=...)` 或 re-raise `PortError("FAILED", ...)`                                                        | 单测：inject 非 JSON payload → `FetchResult.status=="FAILED"` 或 PortError；`uv run pytest tests/test_fred_macro_incremental_e2e.py -q` |
| A4-P2-002 | P2  | 缺省观测值静默写 0.0                 | `fred_incremental_run.py` L70                                    | `float(obs.get("value") or 0.0)` 在 value 缺失时写入假零值；与 live port 层跳过 `"."` 不一致，污染 macro clean                           | 跳过无 value 观测（对齐 `fred_port._live_observations` L151–153）或 raise mapping error                                                                                        | 单测：bundle 含空 value → 行被 skip 或 validation FAIL；无 `raw_value==0.0` 假行                                                        |

---

## 计划外发现

| ID        | P   | 标题                               | 锚点                           | 根因                                                                                                     | 修复方案                                                                                                | 验证                                                                                                |
| --------- | --- | ---------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| A4-P2-003 | P2  | live port 吞 TypeError 回退冷启动  | `fred_port.py` L173–177        | `except TypeError` 后重调 `_live_observations(series_id)` 无 start，可能掩盖真实签名/调用 bug 并扩大拉窗 | 限定 catch 于 test mock（`ponytail:` + 仅 `use_mock`/测试 flag）；生产路径让 TypeError 冒泡为 PortError | `uv run pytest tests/test_fred_macro_incremental_port.py -q`；读码 live 分支无 bare TypeError catch |
| A4-P3-001 | P3  | `total_rows_written` 用 max 非 sum | `fred_incremental_run.py` L345 | 多 series 时 `total_rows = max(total_rows, row_count)` 低估写入量，CLI 操作员误判                        | 改为 `total_rows += row_count`（成功 series）或返回 per-series 明细为主                                 | CLI 测 mock 2 series → `total_rows_written` 等于行数之和                                            |

已对抗搜索：`trade_date` 误用 · adapter bypass · `observation_id` 公式漂移 · watermark 串扰 · conflict staging 误配 bar PK · uncaught `ValueError` whitelist（L297–298 会 raise，可接受）· pytest 绿掩盖的全库 gate（A1 已报）— 除上表外未发现额外 macro 语义级 P0 缺陷。

---

## A4 关账 checklist

- [x] Boot 必读（audit-boot · skill-paths A4 · code-reviewer · finding-schema · AUDIT.plan A4 行）
- [x] §3.4 多轴证据表
- [x] DOUBT 有 file:line
- [ ] §维度裁决 PASS — **FAIL**（findings 非占位）
- [x] 报告已落盘 `research/audit-a4-report.md`
