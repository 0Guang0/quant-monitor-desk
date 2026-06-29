# Audit A2 — Ponytail / 可读性（R3-DCP-01 baostock incremental）

| 元信息 | 值 |
|--------|-----|
| 维度 | A2 可读性（ponytail-review） |
| 任务 | `06-30-wave3-r3-dcp-01-baostock` · debt-lite (`plan_protocol_version: 8d`) |
| 活卡 | `R3_DCP_01_BAOSTOCK_INCREMENTAL.md` |
| 模板 | `agents/audit-a2-ponytail.md` + 本任务 `AUDIT.plan.md` §A2 |
| 审计日期 | 2026-06-30 |
| 模型 | composer-2.5 |
| worktree | `quant-monitor-desk-wt-dcp01` |

---

## 维度证据 §3.2

### git diff --stat（DCP-01 触及文件 · 源码行数核对）

> `git diff master...HEAD` 在 worktree 与 `feature/wave3-r3-dcp-01-baostock` 上对本轨文件无额外 delta 输出（变更已落在分支工作树文件）；下列为 **实际源码净增估算**（对照 `DEBT.plan.md` allowed + A1 报告变更清单）。

| 文件 | 变更类型 | net（约） | 备注 |
|------|----------|-----------|------|
| `backend/app/sync/watermark.py` | 新建 | +66 | 轨 A 拥有 |
| `backend/app/sync/runners.py` | L2 注入 | +6 | `spec.date_*` → `FetchRequest` |
| `backend/app/cli/data_commands.py` | L2 子路径 | +~115 | `sync_baostock_incremental` |
| `backend/app/datasources/fetch_ports/baostock_port.py` | L2 窗过滤 | +~30 | `_parse_window_date` + `_filter_bars_by_window` |
| `backend/app/cli/main.py` | 路由 | 0 | `sync` 子命令未增 baostock 专属参数 |
| `tests/test_baostock_incremental_*.py` 等 | 新建 | +~200 | S01–S05 |
| **合计（估）** | | **~+417** | 无 ≥20 行无 AC 新抽象工厂 |

### AUDIT.plan §A2 可读性核对（代码）

| 检查项 | 结果 | 证据 |
|--------|------|------|
| `watermark.py` API 与 `architecture-dcp01.md` 建议签名一致 | **PASS** | `IncrementalWindow` · `read_bar_trade_date_watermark(con, *, clean_table, instrument_id?, adjustment_type?)` · `compute_incremental_window(watermark, *, end?, empty_table_lookback_days?)` 与 `research/architecture-dcp01.md:51-74` 逐字段一致 |
| `watermark.py` 模块 docstring / ponytail 延期可读 | **PASS** | `watermark.py:1-5` R3-DCP-01 · R3H-03 calendar defer · R3-DCP-02 macro 别名预留 |
| L2 拷改处 staged_pilot / 先例 attribution | **FAIL** | 见 §计划内问题 A2-P2-001、A2-P2-002 |
| CLI help 可发现 baostock 增量语义 | **FAIL** | `main.py:23` 仅 `Sync job (default dry-run)`；无 `cn_equity_daily_bar` watermark 说明；见 A2-P2-003 |
| CLI `--instrument-id` 与 `sync_plan` 对齐 | **FAIL** | `data_commands.sync_plan` / `sync_baostock_incremental` 接受 `instrument_id`；`main.py:128-136` `_run_data` **未**注册/传递该参数（`live-fetch` 有，`sync` 无） |

### ponytail 梯级记录（§3.2 候选删改）

| 候选删改（file:line） | ponytail 梯级 | 备注 |
|----------------------|---------------|------|
| `watermark.py` 全文件 +66 | — | DEBT S01 显式交付；`IncrementalWindow` + 两公开 API 为最小面，**不算** |
| `runners.py:436-439` date 注入 +6 | — | reference-adoption L2 明确要求；体量 <20 行，**不算** ≥20 违规块 |
| `data_commands.py:115-229` `sync_baostock_incremental` ~115 行 | 梯级 2（对照 `live_fetch`） | 活卡 §5 / S05-CLI 显式 AC；与 `live_fetch` 同构 guard+dry-run+service，**不算** YAGNI |
| `baostock_port.py:39-64` `_parse_window_date` + `_filter_bars_by_window` ~26 行 | 梯级 2（复用 `evidence_bundle` ISO 解析） | reference-adoption L2 窗过滤 AC；日期解析与 `evidence_bundle.py:80-81` 重复 → 见计划外 A2-P3-001 |
| `baostock_port.py:58` `lo, hi = min(start, end), max(start, end)` | — | 可读性/语义：倒置窗静默归一化，无注释；与 A1 caught-up 语义相关，见 A2-P2-002 |

### DOUBT（≥20 行可简化）

**已搜索，无必须删的 ≥20 行 AC 外块。** 搜索范围：`watermark.py` 全文 · `runners.py` `IncrementalJobRunner.run` diff 段 · `baostock_port.py` 窗过滤新增段 · `data_commands.py` `sync_baostock_incremental` · `main.py` sync 子命令 · 对照 `live_fetch` / `cninfo_port` L2 头注释先例。

唯一接近阈值的 `sync_baostock_incremental`（~115 行）为活卡 §5「CLI dry-run 可审计 + 真跑 smoke」显式交付，判为 **合理增量**。

### 与 A4 交叉引用

| A2 项 | A4 可能接续 |
|-------|-------------|
| `sync_baostock_incremental` guard / route / dry-run 三分支 | `RESOURCE_GUARD_PAUSED` · `USER_AUTH_REQUIRED` 消息与 ERROR_CODE_GUIDE 一致性 |
| `baostock_port` 倒置窗 `min/max` 归一化 | caught-up 语义与 fetch 边界（A1 A1-P2-001 同源） |

### A2 checklist（模板）

- [x] `git diff --stat` / 净行估算已记录
- [x] 每候选附 `file:line` + ponytail 梯级
- [x] A4 交叉引用（guard / 倒置窗）
- [x] P0–P3 已区分（无 BLOCKING/NON-BLOCKING 措辞）

---

## §维度裁决

**FAIL**

（§计划内 3 行 + §计划外 1 行非占位 finding）

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| A2-P2-001 | P2 | `IncrementalJobRunner` L2 注入缺先例 attribution | `backend/app/sync/runners.py:436-439` | reference-adoption-dcp01.md L2 要求拷改处标注来源；相对 R3H-03 port 头注释 / orchestrator 金路径先例，6 行注入无 `# L2` 或 docstring 指向 `test_batch_d_orchestration_flow` / `SyncJobSpec.date_*` 契约 | 在 `req_kwargs` 块上方加 1–2 行注释：`# L2 (R3-DCP-01): inject spec.date_start/end → FetchRequest (orchestrator gold path; fred track rebase)` | `rg "L2.*R3-DCP-01" backend/app/sync/runners.py` 命中；`uv run pytest tests/test_sync_runners.py::test_incrementalRunner_injectsDateWindowIntoFetchRequest -q` |
| A2-P2-002 | P2 | `baostock_port` 窗过滤 L2 块缺 R3-DCP-01 attribution | `backend/app/datasources/fetch_ports/baostock_port.py:39-64` · `:95-99` | 模块头仅有 R3H-03 staged_pilot 先例；DCP-01 新增 `_filter_bars_by_window` 未标 `L2 (R3-DCP-01)`；`lo,hi=min/max` 无注释说明倒置 start/end 行为 | 在 `_filter_bars_by_window` 上方加 `# L2 (R3-DCP-01): replay bar filter per FetchRequest window — see reference-adoption-dcp01.md §B`；`ponytail:` 或一行注释说明 `min/max` 仅容错 ISO 窗，caught-up 语义由 watermark/runner 负责 | `rg "R3-DCP-01" backend/app/datasources/fetch_ports/baostock_port.py` 命中窗过滤块 |
| A2-P2-003 | P2 | `qmd data sync` CLI help / 参数未暴露 baostock 增量契约 | `backend/app/cli/main.py:23-35` · `:128-136` | 活卡 §5「CLI help + dry-run 可审计」；`sync` 子命令 help 泛化、无 `cn_equity_daily_bar` watermark 说明；`instrument_id` 已在 `sync_plan` 支持但 CLI 未注册/未传入，运维只能依赖默认 `sh.600519` | `sync.add_argument("--instrument-id", ...)` + `_run_data` 传入 `sync_plan`；`help=` 补充「`cn_equity_daily_bar` 走 baostock watermark 增量（默认 dry-run 输出 window/watermark）」 | 新增或扩展 `tests/test_qmd_data_sync_baostock.py`：经 `main` 或 argparse 构造验证 `--instrument-id`；`uv run pytest tests/test_qmd_data_sync_baostock.py -q` |

AUDIT.plan §A2 第一项（watermark API 命名）已 PASS，未列入表。

---

## 计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| A2-P3-001 | P3 | `_parse_window_date` 重复 ISO 日期解析 | `baostock_port.py:39-45` · `evidence_bundle.py:80-81` | 同一 `fromisoformat` + `Z` 替换模式已在 `reject_window_span_over_cap` 存在；DCP-01 又拷一份私有 helper（~7 行 + 调用点） | 抽 `evidence_bundle.parse_fetch_window_date(value) -> date | None`（或复用现有内部模式一行内联），`baostock_port` 删除 `_parse_window_date`；`ponytail:` 若暂留则注释指向 SSOT | `uv run pytest tests/test_baostock_incremental_e2e.py tests/test_qmd_data_sync_baostock.py -q`；`rg "_parse_window_date" backend/app/datasources/fetch_ports/baostock_port.py` 无命中 |

已对抗搜索：`watermark.py` API 对照 `architecture-dcp01.md` · `backend/app/sync/runners.py` L2 注入段 · `baostock_port.py` / `cninfo_port.py` L2 头注释格式 · `main.py` sync/live-fetch 参数表 · `data_commands.sync_baostock_incremental` docstring · `grep staged_pilot|L2 migrate|R3-DCP` on `backend/app/sync` + `fetch_ports/baostock_port.py` · 活卡 §5 CLI help AC。

`watermark.py` 新模块（66 行）、`sync_baostock_incremental` 编排函数判为计划内合理增量，不进入 ponytail 违规表。
