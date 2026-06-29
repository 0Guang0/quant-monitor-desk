# A1 审计报告 — audit-spec（R3H-07 CAL-US）

## 元信息

| 字段                    | 值                                                 |
| ----------------------- | -------------------------------------------------- |
| 维度                    | A1 audit-spec                                      |
| 任务                    | `06-29-round3h-r3h07-us-trading-calendar`          |
| `plan_protocol_version` | 4.1                                                |
| 审计基线                | `git diff 231b5798` + working tree（含 untracked） |
| 日期                    | 2026-06-29                                         |
| 模板                    | `agents/audit-a1-spec.md`                          |

---

## 维度证据

### Boot / 读序

| 检查项                   | 结果             | 证据                                                                                                                                                                                                |
| ------------------------ | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `task.json` protocol 4.1 | PASS             | `task.json` L27 `plan_protocol_version: "4.1"`                                                                                                                                                      |
| AUDIT.plan + audit.jsonl | PASS             | `AUDIT.plan.md` §1–2；`audit.jsonl` 3 行 manifest                                                                                                                                                   |
| ENTRY §1/§2 + to-issues  | PASS             | `00-EXECUTION-ENTRY.md` · `to-issues-slices.md` S07-BOOT..04                                                                                                                                        |
| INDEX §2 AC              | PASS             | `EXECUTION_INDEX.md` L46–59 AC 表与切片映射                                                                                                                                                         |
| ADR-026                  | PASS             | `docs/decisions/ADR-026-r3h07-us-trading-calendar-ssot.md` 已 Read                                                                                                                                  |
| gitnexus-audit-summary   | PASS             | `research/gitnexus-audit-summary.md`（7.pre）                                                                                                                                                       |
| GitNexus query/context   | PASS（索引缺口） | `query("US trading calendar fetch window trading_sessions")` → proc_284/285；`context(us_trading_calendar)` / `impact(recent_trading_dates)` → **Symbol not found**（新文件 untracked，索引未收录） |

### trellis-check 1–7

| 步骤               | 结果           | 证据                                                                                                                                     |
| ------------------ | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| 1 变更范围         | PASS（含缺口） | `git diff 231b5798 --name-only` → 15 文件；`git status` → `us_trading_calendar.py` · `test_us_trading_calendar.py` 为 `??` **未进 diff** |
| 2 任务工件         | PASS           | `frozen/R3H_07_US_TRADING_CALENDAR.md` 指针；ENTRY 为 Execute SSOT                                                                       |
| 3 包上下文         | SKIP           | 本步未跑 `get_context.py`；触及 `ops/data_health_profiles` · `datasources` · `layer4_markets` 已直读代码                                 |
| 4 Spec Quality     | PASS           | ADR-026 + `cn_trading_calendar` 镜像模式；`ponytail:` 注释 @ `us_trading_calendar.py` L13–14                                             |
| 5 项目检查         | 部分 PASS      | 见下「pytest」                                                                                                                           |
| 6 跨层             | PASS           | C3 ports → `fetch_window` → SSOT；G4 `market_structure.py` lazy import `is_trading_day`；`cn_trading_calendar` **未改**                  |
| 7 manifest vs diff | FAIL           | `audit.jsonl` + INDEX §3 点名 ADR-026；diff 缺 SSOT 新文件；`project_map.generated.*` 无 `us_trading` 符号登记                           |

### pytest（独立复验）

| 命令                                 | 结果               | 证据                                                                                                                                                                                                                                                            |
| ------------------------------------ | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CAL-US 范围测                        | **PASS**           | `uv run pytest -q tests/test_us_trading_calendar.py tests/test_market_data_adapters.py tests/test_layer4_market_structure.py tests/test_cn_market_adapters.py -k "calendar or trading or usEquity or windowKind or calUs or evidence_contract"` → **20 passed** |
| `test_us_trading_calendar.py` 全模块 | **PASS**           | 12 passed（含 `test_datasourceService_usEquityFetch_exposesTradingSessionWindow`）                                                                                                                                                                              |
| 全量 `uv run pytest -q`              | **FAIL**（计划外） | `tests/test_sync_orchestrator.py::test_syncRegistry_cli_syncsYamlToDb` returncode=2（GBK 解码子进程 stderr）；**不在** `git diff 231b5798` 触达集                                                                                                               |

### Trace Authority（AUDIT.plan 无 §0.1 表 · 继承 audit.jsonl）

| 条目                    | 结果              | 证据                                                              |
| ----------------------- | ----------------- | ----------------------------------------------------------------- |
| 原始任务卡              | PASS              | `frozen/R3H_07_US_TRADING_CALENDAR.md` + ENTRY §6 → 活卡路径      |
| Plan 入口               | PASS              | `00-EXECUTION-ENTRY.md` v4.1 唯一 Execute 入口                    |
| round map / batch       | PASS              | Wave 1b · `blocked_by` R3H-10 @ `227e0734`                        |
| source-index / manifest | PASS（diff 不全） | `audit.jsonl` 3 行；INDEX §3 must-read ADR-026                    |
| integration-ledger      | PASS              | `integration-audit.md` doc-gap 表 S07-01..04 → 代码已落地（磁盘） |
| omission-check          | PASS              | ENTRY §5.1 登记文件均在 `research/` 存在                          |

### 链 A · ADR-026 / ENTRY §2 vs Bundle

| 约束                            | Bundle                           | 结果                                                    |
| ------------------------------- | -------------------------------- | ------------------------------------------------------- |
| US SSOT 单模块                  | `to-issues` S07-01 · ADR-026 §1  | PASS                                                    |
| 有界 2000–2030                  | slices + ADR-026 §2              | PASS（代码 `_RANGE_END`）                               |
| `window_kind: trading_sessions` | S07-02 AC                        | PASS（三源 + replay fixture）                           |
| CN 隔离                         | ENTRY §2 · AC-CN-REG             | PASS（`-k calendar` 绿；`cn_trading_calendar` 无 diff） |
| 无 migration                    | AC-NO-DDL                        | PASS（`git diff 231b5798 -- backend/migrations` 空）    |
| span cap = trading sessions     | ADR-026 §3 · S07-02「窗口 span」 | **FAIL**（见 §计划内 A1-P2-02）                         |

### AC 抽样（代码 + 测，非文档自述）

| AC                    | 结果 | 证据                                                                                           |
| --------------------- | ---- | ---------------------------------------------------------------------------------------------- |
| AC-01 SSOT API        | PASS | `us_trading_calendar.py` + `test_usTradingCalendar_*`                                          |
| AC-02 C3 window_kind  | PASS | 三源 `trading_sessions`；`test_marketData_usSourceEvidence_*`                                  |
| AC-03 G4 假日拒绝     | PASS | `market_structure.py` L195–201；`test_layer4_usEquity_buildRejectsNonTradingHoliday`           |
| AC-04 假日负向 fetch  | PASS | `test_calUs_holidayWindow_usFetchProducesNoTradingBars`                                        |
| AC-SVC service 金路径 | PASS | `test_datasourceService_usEquityFetch_exposesTradingSessionWindow`                             |
| AC-BOUND              | PASS | `_RANGE_END` + `test_usTradingCalendar_getTradingDays_respectsBounds`                          |
| AC-CN-REG             | PASS | `test_cn_market_adapters.py -k calendar` 绿（`test_layer_cn_calendarGapProfile_*` 等行为仍在） |

### DOUBT / 对抗搜索

| 疑点                                 | 搜索范围                                                                  | 结论                                                                  |
| ------------------------------------ | ------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| D5 span 仅改 bundle                  | `fetch_window.py` · ports · `evidence_bundle.reject_window_span_over_cap` | 默认 mock 用 `recent_trading_dates`；**显式窗**仍自然日 cap → finding |
| D6 option chain calendar_days        | `alpha_vantage_port.py` L145                                              | PASS（ADR/plan 明确 equity bar only）                                 |
| 活卡 Red Flags 万年历                | `us_trading_calendar._load_non_trading_days` 有界循环                     | PASS                                                                  |
| `recent_trading_window_start` 死代码 | 全仓库 grep                                                               | 仅定义无调用 → 并入 span finding                                      |

---

## §维度裁决

**FAIL**

（§计划内 2 项非占位 finding）

---

## 计划内问题

| ID       | P   | 标题                                 | 锚点                                                                                                                                                                                                                                      | 根因                                                                                                                                                                       | 修复方案                                                                                                                                                                                                                                                 | 验证                                                                                                                                                                                                                                                         |
| -------- | --- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A1-P2-01 | P2  | 核心 SSOT 交付物未纳入 git 变更集    | `git status` → `?? backend/app/ops/data_health_profiles/us_trading_calendar.py` · `?? tests/test_us_trading_calendar.py`；`git diff 231b5798` 不含上述文件                                                                                | Execute 实现落盘但未 `git add`；Audit 基线 diff 与 INDEX §2 AC-01 交付物不一致；GitNexus 无法索引新符号                                                                    | 将 SSOT 模块与专项测 `git add` 后重跑 `uv run python scripts/loop_maintain.py --fix` 刷新 `project_map`；复验 `git diff 231b5798 --stat` 含两文件                                                                                                        | `git status` 无 `??` 于上述路径；`git diff 231b5798 --name-only` 列出两文件；`rg us_trading_calendar docs/generated/project_map.generated.md` 有命中                                                                                                         |
| A1-P2-02 | P2  | ADR-026 显式窗口 span 仍按自然日计界 | ADR-026 §3 · `to-issues-slices.md` S07-02「窗口 span 按 trading sessions 计 cap」· `evidence_bundle.py` L77「calendar-day cap」· 三源 port `reject_window_span_over_cap(..., cap=MAX_WINDOW_DAYS)` · `recent_trading_window_start` 零调用 | S07-02 仅闭合 mock 默认路径（`recent_trading_dates`）与 `window_kind`；未将 **显式 start/end 窗** 的 cap 语义切换为 trading sessions；`recent_trading_window_start` 未接入 | 方案 A：US equity 域在 `fetch_payload` 对显式窗调用 trading-session span 校验（可扩 `reject_window_span_over_cap` 或 US 专用 helper 消费 `recent_trading_window_start`）。方案 B：若刻意 defer 显式窗，须 `ponytail:` 注释天花板并绑定 follow-up 任务 ID | 新增/扩展测：US port 传入 `start_time`/`end_time` 跨度 120 **自然日**但 ≤120 **交易日** 时行为符合 ADR；`rg recent_trading_window_start backend` 有 US port 调用；`uv run pytest -q tests/test_us_trading_calendar.py tests/test_market_data_adapters.py` 绿 |

---

## 计划外发现

| ID       | P   | 标题                                          | 锚点                                                                                                        | 根因                                                                    | 修复方案                                                                                                           | 验证                      |
| -------- | --- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------- |
| A1-P3-01 | P3  | 全量 pytest 单点失败（与 R3H-07 diff 无交集） | `tests/test_sync_orchestrator.py::test_syncRegistry_cli_syncsYamlToDb` L713；全量 `uv run pytest -q` exit 1 | Windows 子进程 stderr GBK 解码 `UnicodeDecodeError`；非 CAL-US 代码回归 | 子进程 `text=True` 改 `encoding=utf-8`/`errors=replace` 或设 `PYTHONIOENCODING=utf-8`；属仓库级 hygiene，可独立 PR | `uv run pytest -q` exit 0 |

已对抗搜索：`git diff 231b5798` 全文件 · `backend/app/datasources/**` · `backend/app/layer4_markets/**` · `backend/app/ops/data_health_profiles/**` · `tests/test_*calendar*` · `tests/test_market_data_adapters.py` · `tests/test_layer4_market_structure.py` · ADR-026 · plan-doubt-review D1–D8 · integration-audit doc-gap 表。

---

## 关账自检

- [x] Boot v4.1 读序 #1–4 + 任务包
- [x] §维度裁决 ∈ {PASS, FAIL}
- [x] findings 表头符合 `audit-finding-schema.md`
- [x] 非占位 finding → FAIL
- [x] 每行 P0–P3 + 修复方案 + 验证
- [x] 只读；未 commit
