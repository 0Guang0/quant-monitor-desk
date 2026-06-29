# Audit A5 — 完成度 / 执行偏差（链 B）

## 元信息

| 字段                  | 值                                        |
| --------------------- | ----------------------------------------- |
| 维度                  | A5 completion                             |
| 任务                  | `06-29-round3h-r3h07-us-trading-calendar` |
| plan_protocol_version | 4.1                                       |
| 模板                  | `agents/audit-a5-completion.md`           |
| 覆盖模型              | `agents/audit-coverage-model.md` 链 B     |
| diff 基线             | `git diff 231b5798`                       |
| 审计日期              | 2026-06-29                                |

---

## 维度证据

### A5 checklist

| 项                                        | 结论                                                                 |
| ----------------------------------------- | -------------------------------------------------------------------- |
| 每条 INDEX §2 AC → 代码/测试追溯 + 1–5 分 | 见下表（**不以** INDEX `[x]` / txt 为据）                            |
| 独立复跑与实现一致                        | 指定 pytest **exit 0**；与磁盘代码行为一致                           |
| diff 无 silent 扩大 scope                 | **PASS** — 变更集中于 US equity fetch / Layer4 / replay fixtures     |
| INDEX §2.1 最弱 2 行                      | **本任务 INDEX 无 §2.1**；改按 tier B 取 AC-SVC + AC-04 单测独立复跑 |

### 独立 pytest（必做）

| 命令                                                                                                                          | exit code | 说明                           |
| ----------------------------------------------------------------------------------------------------------------------------- | --------: | ------------------------------ |
| `uv run pytest -q tests/test_us_trading_calendar.py tests/test_market_data_adapters.py tests/test_layer4_market_structure.py` |     **0** | INDEX §2 主验收集（76 项量级） |
| `uv run pytest -q tests/test_cn_market_adapters.py -k calendar`                                                               |     **0** | AC-CN-REG（1 项）              |
| `uv run pytest -q tests/test_us_trading_calendar.py::test_datasourceService_usEquityFetch_exposesTradingSessionWindow`        |     **0** | §2.1 替代：AC-SVC 金路径       |
| `uv run pytest -q tests/test_us_trading_calendar.py::test_calUs_holidayWindow_usFetchProducesNoTradingBars`                   |     **0** | §2.1 替代：AC-04 假日负向      |

### `git diff 231b5798` 范围摘要

**已跟踪变更（15 路径）：** 三 US fetch port、`fetch_window.py`、`market_structure.py`、replay fixtures、`test_market_data_adapters.py`、`test_layer4_market_structure.py`、`test_catalog.yaml`、生成 project_map、任务 INDEX/AUDIT.plan。

**未纳入 diff 但工作区存在（`git status ??`）：**

- `backend/app/ops/data_health_profiles/us_trading_calendar.py` — AC-01 SSOT 本体
- `tests/test_us_trading_calendar.py` — AC-01/02/04/SVC 主测模块

> 独立 pytest 能绿，是因为未跟踪文件在磁盘上；**链 B 交付物与 diff 不一致**。

### INDEX §2 AC 追溯与评分

| AC ID         | 切片      | 代码证据                                                                                                                                   | 测试证据                                                                                                                                               |    分 | 备注                                                             |
| ------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----: | ---------------------------------------------------------------- |
| **AC-BOOT**   | S07-BOOT  | 三 port `window_kind=trading_sessions`；`research/calendar-baseline-matrix.md`                                                             | `test_calUsBoot_usSourcesEvidenceStillCalendarDays_pendingClosure`（`test_us_trading_calendar.py`）                                                    | **5** | BOOT RED 已翻 GREEN；矩阵齐全                                    |
| **AC-01**     | S07-01    | `us_trading_calendar.py`：`is_trading_day` / `get_trading_days` / `get_missing_trading_days`、`_RANGE_END`、`ponytail:`                    | `test_usTradingCalendar_*` 4 项；**无** `get_missing_trading_days` 专项测                                                                              | **3** | API 对称 CN 三函数已有；**SSOT 文件未跟踪**；缺 `get_missing` 测 |
| **AC-02**     | S07-02    | 三 port + `fetch_window.recent_trading_*` / `filter_us_trading_day_bars`                                                                   | `test_marketData_usSourceEvidence_windowKindTradingSessions`；`test_evidence_contract_*`；`test_yahooFinance_fetchPayload_excludesHolidayBars`         | **4** | 三源 `trading_sessions` 可复现；**stooq 假日 bar 无专用负向测**  |
| **AC-03**     | S07-03    | `market_structure.py` US_EQ → `is_trading_day` → `non-trading`                                                                             | `test_layer4_usEquity_buildRejectsNonTradingHoliday` / `buildAllowsTradingDay`                                                                         | **5** | 假日拒绝 + 交易日通过                                            |
| **AC-04**     | S07-04    | `filter_us_trading_day_bars` + AV mock                                                                                                     | `test_calUs_holidayWindow_usFetchProducesNoTradingBars`；yahoo 假日过滤测                                                                              | **4** | 至少一固定假日（Thanksgiving）闭合；stooq 端点未单测             |
| **AC-CN-REG** | 全切片    | 未改 `cn_trading_calendar.py`                                                                                                              | `test_layer_cn_calendarGapProfile_failsOnMissingTradingDaysWithAuthority`（`-k calendar`）                                                             | **5** | exit 0                                                           |
| **AC-SVC**    | S07-02    | `DataSourceService.fetch` + yahoo port                                                                                                     | `test_datasourceService_usEquityFetch_exposesTradingSessionWindow`（**在** `test_us_trading_calendar.py`，非 INDEX 写的 `test_datasource_service.py`） | **4** | 行为可复现；INDEX 锚点文件偏差                                   |
| **AC-BOUND**  | S07-01    | `_RANGE_START` / `_RANGE_END` + `ponytail:` 注释                                                                                           | `test_usTradingCalendar_getTradingDays_respectsBounds`                                                                                                 | **5** | 有界非万年历                                                     |
| **AC-NO-DDL** | 全切片    | `git diff 231b5798` **无** `backend/migrations/` 变更                                                                                      | —                                                                                                                                                      | **5** | 符合无新 migration                                               |
| **AC-CLOSE**  | S07-CLOSE | `docs/quality/round3h_real_data_production_entry_audit.md` §7 **仍为** `CAL-US \| PENDING_R3H_EXECUTION`；diff **未**更新 registry / G4→R4 | —                                                                                                                                                      | **2** | Execute 切片未关账；属 INDEX §2 明确 AC                          |

**均分（10 项）：3.6** — 主路径（日历→fetch→Layer4→CN 回归）可独立复验；关账与 git 交付链存在缺口。

### §2.1 最弱 2 行独立复验记录

| 原锚点                           | 独立命令                                                                                                               |  exit | 与代码一致                                          |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----: | --------------------------------------------------- |
| AC-SVC（DataSourceService 窗口） | `uv run pytest -q tests/test_us_trading_calendar.py::test_datasourceService_usEquityFetch_exposesTradingSessionWindow` | **0** | ✅ raw JSON `window_kind==trading_sessions`         |
| AC-04（假日负向）                | `uv run pytest -q tests/test_us_trading_calendar.py::test_calUs_holidayWindow_usFetchProducesNoTradingBars`            | **0** | ✅ 仅 Thanksgiving 候选 → `MarketDataEvidenceError` |

---

## §维度裁决

**FAIL**

**理由：** §计划内问题含 2 条非占位 finding（P1 未跟踪 SSOT 交付物；P2 registry 关账 AC 未闭合）。独立 pytest 全绿**不能**抵消链 B 交付与 INDEX AC-CLOSE 缺口。

---

## 计划内问题

| ID        | P   | 标题                                     | 锚点                                                                           | 根因                                                            | 修复方案                                                                                                                                  | 验证                                                                                                                |
| --------- | --- | ---------------------------------------- | ------------------------------------------------------------------------------ | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| A5-P1-001 | P1  | 核心 SSOT 与专项测未纳入 git 交付        | `us_trading_calendar.py` · `test_us_trading_calendar.py` · `git diff 231b5798` | Execute 完成未 `git add` 新文件；diff 仅含接线层                | `git add` 两文件 + `loop_maintain.py --fix`（若需 authority_graph/docs index）；复跑 INDEX §2 pytest                                      | `git diff 231b5798 --stat` 含上述路径；`uv run pytest -q tests/test_us_trading_calendar.py` exit 0                  |
| A5-P2-001 | P2  | AC-CLOSE：`CAL-US` registry 仍为 PENDING | INDEX §2 AC-CLOSE · `round3h_real_data_production_entry_audit.md` §7           | S07-CLOSE 未执行：audit 表未 CLOSED、无 G4 R3→R4 证据           | 按 `to-issues-slices.md` §7 更新 `docs/quality/round3h_real_data_production_entry_audit.md` CAL-US 行 + Wave 登记；Audit 全维 PASS 后关账 | `rg CAL-US docs/quality/round3h_real_data_production_entry_audit.md` 显示 CLOSED；`validate-execute-handoff` exit 0 |
| A5-P3-001 | P3  | `get_missing_trading_days` 无行为测      | S07-01 切片 · `us_trading_calendar.py`                                         | TDD 覆盖停在 `is_trading_day` / `get_trading_days`              | 增 1 测：给定 `existing_dates` 缺 Thanksgiving 周中交易日 → 返回缺失列表                                                                  | `uv run pytest -q tests/test_us_trading_calendar.py -k missing` exit 0                                              |
| A5-P3-002 | P3  | stooq 假日 bar 过滤无专用负向测          | S07-02/04 · `stooq_port.py`                                                    | 仅 yahoo/alpha 有假日 monkeypatch 测；stooq 仅 window_kind 断言 | 增 `test_stooq_fetchPayload_excludesHolidayBars`（镜像 yahoo 模式）或 parametrized 三源假日测                                             | `uv run pytest -q tests/test_us_trading_calendar.py -k stooq` exit 0                                                |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`backend/app/datasources/fetch_ports/*` 对非 `us_equity_daily_bar` 域是否误用 `trading_sessions`；`deribit`/`coingecko` diff 无变更；`cn_trading_calendar` 无 diff。未发现计划外 scope 泄漏或 CN 回退。

---

## 裁决摘要（A9）

| 项                       | 值                                                                              |
| ------------------------ | ------------------------------------------------------------------------------- |
| 独立 pytest（主集 + CN） | **exit 0**                                                                      |
| AC 均分                  | **3.6 / 5**                                                                     |
| 链 B 交付完整性          | **FAIL**（未跟踪 SSOT + AC-CLOSE 未闭合）                                       |
| 建议                     | Repair：先 P1 纳入版本库 → P2 关账登记 → 可选 P3 补测 → 全量 `uv run pytest -q` |
