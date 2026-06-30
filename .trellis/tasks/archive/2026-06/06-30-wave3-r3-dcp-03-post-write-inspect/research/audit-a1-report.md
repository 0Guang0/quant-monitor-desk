# Audit A1 — 正确性

| 字段     | 值                                         |
| -------- | ------------------------------------------ |
| 维度     | A1 正确性                                  |
| 任务     | `06-30-wave3-r3-dcp-03-post-write-inspect` |
| 协议     | debt-lite（无 v4.1 ENTRY）                 |
| worktree | `quant-monitor-desk-wt-dcp03`              |
| 日期     | 2026-06-30                                 |
| 模板     | `agents/audit-a1-spec.md`                  |

---

## 维度证据

| 检查项                          | 结果                           | 证据                                                                                                                                                                                                                                  |
| ------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 变更范围                        | PASS                           | `git diff --name-only`：`tests/test_incremental_post_write_inspect.py`（新）、`tests/post_write_inspect_support.py`（新）、`tests/test_catalog.yaml`（登记）；无 `backend/` 改动                                                      |
| 独立复验 pytest                 | PASS（绿）                     | worktree 内 `uv run pytest tests/test_incremental_post_write_inspect.py -q` → **3 passed** exit 0                                                                                                                                     |
| DEBT S01：DbInspector 报告字段  | PASS                           | `test_postWriteInspect_twoIncremental_rowCountStable` L65–73：`DbInspector.inspect()` → `key_tables` 中 `security_bar_1d.row_count` 前后相等；**非**裸 SQL COUNT 断言稳定性                                                           |
| DEBT S01：`max(trade_date)`     | PASS                           | 同上 L75–81：read-only SQL `SELECT MAX(trade_date) …`；活卡 §5 允许「测试内 read-only SQL」                                                                                                                                           |
| DEBT S02：incremental 会话接线  | **FAIL**                       | `test_postWriteHealth` 调用 `run_two_incremental` + `build_evidence_bundle_from_fetch_log`（非 `good_bundle`）；但独立探针显示 `run_data_health_profile` 返回 `overall_status=FAIL`、`INSUFFICIENT_HISTORY`（0 bars）— 见下文对抗复验 |
| DEBT S02：禁止 good_bundle 偷换 | PASS                           | `tests/test_incremental_post_write_inspect.py` 无 `good_bundle` 路径引用；`grep good_bundle` 仅 docstring 说明                                                                                                                        |
| AUDIT.plan A1 范围              | **FAIL**                       | 活卡 §5 / DEBT S02 要求写后 health「可跑通（PASS/WARN）」；实测 FAIL                                                                                                                                                                  |
| GitNexus                        | PASS                           | `context(DbInspector)` → `inspect` 方法、`qmd_ops.py` 等上游；`query("post-write inspect…")` 命中 `DbInspector.inspect` 与 health profile 链                                                                                          |
| 对抗：S01 非 SQL COUNT 捷径     | PASS                           | 稳定性断言锚定 `table_before/after["row_count"]`（Inspector `key_tables`），`db_inspector._table_stats` L282 虽内部 COUNT，测试消费的是报告字段                                                                                       |
| 对抗：S02 非夹具捷径            | PASS（路径）/ **FAIL**（语义） | 路径来自 `fetch_log`；语义上 health 未真正消费到 bar 行                                                                                                                                                                               |

### 独立对抗复验（S02 根因）

在 worktree 内复现 incremental → bundle → health（与测试同 helper）：

```text
overall_status FAIL
DataHealthCheckResult(rule_id='INSUFFICIENT_HISTORY', status='FAIL',
  message='expected at least 2 bars, got 0')
```

根因链：

1. `build_evidence_bundle_from_fetch_log`（`post_write_inspect_support.py` L173–180）将 `manifest_entries[].relative_paths` 指向复制的 `raw_*.json`（baostock replay / cn_market bundle，顶层键为 **`bars`**）。
2. `run_data_health_profile` → `_bars_from_evidence`（`data_health_profiles/__init__.py` L207–222）对 manifest 指向文件调用 `_equity_bar_rows`。
3. `_equity_bar_rows`（`staged_pilot.py` L967–971）**仅**读取 `payload["rows"]`，对 cn_market `bars` 结构返回 `[]`。
4. helper 虽写入 `bars.json`（含 `rows`），但 manifest **未**指向该文件；`good_bundle` SSOT 则正确指向 `bars.json`（`tests/fixtures/data_health/good_bundle/raw_evidence_manifest.json` L11）。

因此：pytest 绿（无未处理异常 + `len(checks)>=1`），但活卡 §5「PASS/WARN 可跑通」未满足。

---

## §维度裁决

**FAIL**

（§计划内 1 行非占位 finding）

---

## §计划内问题

| ID        | P   | 标题                                                            | 锚点                                                                                                                                                                   | 根因                                                                                                                                                          | 修复方案                                                                                                                                                                                                                                                                                                                                   | 验证                                                                                                                                                                  |
| --------- | --- | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A1-P1-001 | P1  | incremental evidence bundle 无法被 health profile 解析出 bar 行 | `tests/post_write_inspect_support.py:173-180` · `tests/test_incremental_post_write_inspect.py:95-107` · `backend/app/ops/staged_pilot.py:967-971` · 活卡 §5 · DEBT S02 | manifest 指向 cn_market 原始 JSON（`bars`），而 `_equity_bar_rows` 只认 `rows`；helper 生成的 `bars.json` 未被 manifest 引用 → 0 bars → `overall_status FAIL` | 1) `build_evidence_bundle_from_fetch_log` 将 `relative_paths` 改为 `["bars.json"]`（helper 已用 `_rows_from_cn_market_payload` 写出 `rows`）；或 2) 复制 raw 时归一为 `{"rows":[…]}` 再入 manifest。同步在 `test_postWriteHealth` 增加 `assert report.overall_status in {"PASS", "WARN"}`（对齐 `test_ops_data_health.py` L445 与活卡 §5） | `uv run pytest tests/test_incremental_post_write_inspect.py -k health -q` exit 0；探针或断言 `overall_status in {PASS,WARN}` 且 checks 无 `INSUFFICIENT_HISTORY` FAIL |

---

## §计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`tests/test_incremental_post_write_inspect.py` 全文 · `post_write_inspect_support.py` 全文 · `good_bundle` 与 cn_market replay 载荷结构 · `db_inspector._table_stats` · `run_data_health_profile` / `_bars_from_evidence` · CLI 子测 `test_postWriteCli_dbInspect_jsonIncludesSecurityBar1d` · worktree `git diff` 全量 · 活卡 `R3_DCP_03_POST_WRITE_INSPECT.md` §5 Red Flags（只读边界、禁止 good_bundle 偷换）。
