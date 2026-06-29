# Audit A1 — 正确性（R3-DCP-01 baostock incremental）

| 元信息 | 值 |
|--------|-----|
| 维度 | A1 正确性 |
| 任务 | `wave3-r3-dcp-01-baostock` · debt-lite (`plan_protocol_version: 8d`) |
| 活卡 | `R3_DCP_01_BAOSTOCK_INCREMENTAL.md` |
| 模板 | `agents/audit-a1-spec.md` + 本任务 `AUDIT.plan.md` §A1 |
| 审计日期 | 2026-06-30 |
| 模型 | composer-2.5 |
| worktree | `quant-monitor-desk-wt-dcp01` |

---

## 维度证据 §3.1

### trellis-check（debt-lite 压缩）

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 变更范围 | PASS | `git diff master...HEAD`：`watermark.py`（新）、`runners.py`、`baostock_port.py`、`data_commands.py`、`adapters/baostock.py`、3 个新测 + `test_sync_runners.py` 回归；**未**改 `orchestrator.py` / `fred_port`（符合 `DEBT.plan.md` forbidden） |
| 任务工件 | PASS | `prd.md` AC 与活卡 §5 对齐；`DEBT.plan.md` S01–S06；`implement.jsonl` / `check.jsonl` manifest 可读 |
| 靶向 pytest | PASS | `uv run pytest tests/test_baostock_incremental_watermark.py tests/test_baostock_incremental_e2e.py tests/test_qmd_data_sync_baostock.py tests/test_sync_runners.py -q` → **12 passed**（Audit 独立复跑 2026-06-30） |
| 全量 pytest | 观察 | `uv run pytest -q` → **2 failed**（`test_batch25_production_data_gate.py` 两行）；canonical `data/duckdb` fetch_log=1 + `data/raw` 非 staged fixture；**非本轨靶向测**；见 `slice-status.md`；归 A5/merge gate，**不**计入本维 A1 checklist |
| test_catalog | PASS | `tests/test_catalog.yaml` 已登记 `test_baostock_incremental_*` · `test_qmd_data_sync_baostock.py` |
| diff vs manifest | PASS | 变更文件 ⊆ `DEBT.plan.md` allowed（含 `test_catalog.yaml`、generated docs） |

### AUDIT.plan §A1 正确性核对（代码 + 独立跑测）

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 边界日 `max+1` | PASS | `compute_incremental_window(date(2026,6,28), end=2026-06-30).date_start == 2026-06-29`；`tests/test_baostock_incremental_watermark.py::test_watermark_boundaryDay_startIsDayAfterMax` 绿 |
| 空表 lookback | PASS | `watermark is None` → `date_start = end - 30d`（`2026-05-31`）；`test_watermark_emptyTable_returnsNullAndLookbackWindow` 绿 |
| 有数据 watermark | PASS | `read_bar_trade_date_watermark` MAX + instrument 过滤；`test_watermark_withData_returnsMaxPlusOne` · `test_watermark_instrumentFilter_ignoresOtherSymbols` 绿 |
| Runner 日期注入 | PASS | `runners.py:436-439` `spec.date_start/date_end` → `FetchRequest.start_time/end_time`；`test_incrementalRunner_injectsDateWindowIntoFetchRequest` 绿 |
| Port 窗过滤 | PASS | `baostock_port.py:48-64` `_filter_bars_by_window`；`test_baostockPort_replayFiltersByFetchWindow` 绿 |
| E2E 金路径写库 | PASS | `test_baostockIncremental_e2e_writesSecurityBar1d`：`run_incremental` + `upsert_by_pk` → `security_bar_1d` 含 fixture 行 |
| 重复跑幂等 | PASS | `test_baostockIncremental_repeatRun_noRowGrowth`：两次 COMPLETED，`COUNT(*)==2` 不变 |
| 隔离库路径 | PASS | E2E/CLI 测均 `tmp_path` + `QMD_DATA_ROOT` monkeypatch；**无** `tests/test_*baostock*` 引用 canonical `data/duckdb/quant_monitor.duckdb`（grep 0 命中） |

### Trace Authority（debt-lite 等价）

| 条目 | 结果 | 证据 |
|------|------|------|
| 原始任务卡 AC | PASS | 活卡 §5 六项在 `prd.md` + `DEBT.plan.md` S01–S06 有映射；watermark/幂等/CLI 有对应测 |
| Plan 调研 L1/L2/L3 | PASS | `research/reference-adoption-dcp01.md` 表非空；Execute 实读 `execute-reference-read-evidence.md` |
| 架构契约 | PASS | `research/architecture-dcp01.md` API 与 `watermark.py` 签名一致 |
| unresolved / 非目标 | PASS | CN 交易日历、全 Tier A 扩展在活卡 §7 + watermark `ponytail:` 注释显式 defer |

### GitNexus

| 检查项 | 结果 | 证据 |
|--------|------|------|
| query | 已执行 | `baostock incremental watermark compute_incremental_window` → 命中 batch_d / orchestration 先例；**新文件 `watermark.py` 尚未入索引**（worktree 新符号） |
| context | N/A | `compute_incremental_window` 索引未收录（预期：Execute 后需 `gitnexus analyze`） |

### 对抗复验（ caught-up 边界）

独立 Python 复验（2026-06-30）：

```text
compute_incremental_window(date(2026,6,30), end=date(2026,6,30))
→ date_start=2026-07-01, date_end=2026-06-30  # date_start > date_end
```

`baostock_port._filter_bars_by_window` 对 `start_time > end_time` 做 `lo, hi = min, max` 归一化，**可能把 watermark 当日纳入 fetch 窗**；upsert 可防行数膨胀，但违背活卡「只拉新来的数据」语义。无单测覆盖 caught-up 路径。

---

## §维度裁决

**FAIL**

（§计划外发现 含 1 行非占位 finding）

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| — | — | 无 | — | — | — | — |

AUDIT.plan §A1 列出的 watermark 空/有/边界、max+1、幂等、隔离库路径均已由代码与靶向 pytest 独立证明。

---

## 计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| A1-P2-001 | P2 | caught-up 时增量窗倒置且 port 归一化可能重拉 watermark 日 | `watermark.py:51-65` · `baostock_port.py:48-64` | `watermark == end` 时 `date_start = watermark + 1` 大于 `date_end`；port 将倒置 start/end 归一化为 `[end, end+1]` 日历窗，含已落库日 | 在 `compute_incremental_window` 当 `watermark is not None and watermark >= date_end` 时返回空窗（`date_start > date_end` 或 `date_start = date_end + 1` 且 runner/CLI 早退 COMPLETED no-op）；或 runner 拒绝 `date_start > date_end`；补单测 caught-up | `uv run pytest tests/test_baostock_incremental_watermark.py -q` 新增 caught-up case；`uv run pytest tests/test_baostock_incremental_e2e.py -q` 可选 e2e no-op |

已对抗搜索：`compute_incremental_window` 全仓调用（CLI `data_commands.py:152`、e2e 测、watermark 单测）；`grep date_start.*date_end` on `runners.py` 无倒置守卫；GitNexus query baostock incremental；活卡 §7 非目标与 ponytail 注释未覆盖 caught-up 语义。
