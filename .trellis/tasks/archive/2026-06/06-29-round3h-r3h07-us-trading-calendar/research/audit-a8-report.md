# Audit A8 — 证据（CAL-US 关账）

> **维度：** A8 · **任务：** `06-29-round3h-r3h07-us-trading-calendar`  
> **协议：** `plan_protocol_version: 4.1`  
> **模板：** `agents/qa-expert.md` · `agents/audit-finding-schema.md`  
> **日期：** 2026-06-29  
> **基线：** `git diff 231b5798` + 独立 pytest（**不**强制 `execute-evidence/9.*.txt`，依用户指令与 `AUDIT.plan.md` §1 A8）

## 维度证据

### §3.8 Red Flag → 测试/证据追溯

| Red Flag（plan-doubt-review） | 覆盖                       | 证据                                                      |
| ----------------------------- | -------------------------- | --------------------------------------------------------- |
| D1 NASDAQ/NYSE 合并 trade-off | ADR-026 + `ponytail:` 注释 | `us_trading_calendar.py` L13–14；ADR-026 §Alternatives    |
| D2 2030 天花板                | 有界测                     | `test_usTradingCalendar_getTradingDays_respectsBounds`    |
| D3 浮动假日（Thanksgiving）   | 固定假日测                 | `test_usTradingCalendar_thanksgiving2024_isNonTradingDay` |
| D4 replay 假日 bar            | 过滤测                     | `test_yahooFinance_fetchPayload_excludesHolidayBars`      |
| D5 span 仍自然日              | `fetch_window` 接线        | `fetch_window.recent_trading_dates` + 三源 port diff      |
| D6 option chain 不改          | 切片 Out of scope          | `to-issues-slices.md` §4 RECONCILE                        |
| D7 L4-US-DEFERRED             | 仅 calendar 拒绝           | `test_layer4_usEquity_buildRejectsNonTradingHoliday`      |
| D8 staged vs live 双轨        | builder consult SSOT       | `market_structure.py` lazy `is_trading_day`               |

### git diff `231b5798`（15 tracked + 2 untracked）

**已出现在 diff（S07-02..04）：**

| 切片     | 文件                                                                | 证据                                                  |
| -------- | ------------------------------------------------------------------- | ----------------------------------------------------- |
| S07-02   | `fetch_window.py`（+65）                                            | `recent_trading_dates` / `filter_us_trading_day_bars` |
| S07-02   | `yahoo_finance_port.py` · `stooq_port.py` · `alpha_vantage_port.py` | `window_kind: trading_sessions`                       |
| S07-02   | replay fixtures ×3                                                  | `window_kind` → `trading_sessions`                    |
| S07-02   | `test_market_data_adapters.py`                                      | R3H02-R-22 翻转为 `trading_sessions`                  |
| S07-03   | `market_structure.py`                                               | US_EQ 非交易日 `non-trading` 拒绝                     |
| S07-03   | `test_layer4_market_structure.py`（+70）                            | 假日拒绝 + 交易日通过                                 |
| S07-BOOT | `calendar-baseline-matrix.md`                                       | 基线矩阵已落盘（Plan 期）                             |

**未出现在 diff（untracked `??`）：**

| 切片       | 文件                                                          | 状态          |
| ---------- | ------------------------------------------------------------- | ------------- |
| S07-01     | `backend/app/ops/data_health_profiles/us_trading_calendar.py` | **untracked** |
| S07-01..04 | `tests/test_us_trading_calendar.py`                           | **untracked** |

→ `git diff 231b5798` **不能**单独复现 S07-01 交付物；证据链对审阅者不可 diff 追溯。

### pytest 独立复验（2026-06-29）

| AC                      | 命令                                                                      | 结果                             |
| ----------------------- | ------------------------------------------------------------------------- | -------------------------------- |
| 假日负向 S07-04         | `test_calUs_holidayWindow_usFetchProducesNoTradingBars`                   | **PASS**                         |
| 假日负向 G4             | `test_layer4_usEquity_buildRejectsNonTradingHoliday`                      | **PASS**                         |
| trading_sessions 三源   | `test_marketData_usSourceEvidence_windowKindTradingSessions`              | **PASS**                         |
| trading_sessions replay | `test_evidence_contract_replayFixture_windowKindTradingSessions`          | **PASS**                         |
| service 金路径          | `test_datasourceService_usEquityFetch_exposesTradingSessionWindow`        | **PASS**                         |
| CN 回归 AC-CN-REG       | `test_layer_cn_calendarGapProfile_failsOnMissingTradingDaysWithAuthority` | **PASS**                         |
| R3H-07 专项集（16 测）  | 上列 + S07-01 API 测                                                      | **16/16 PASS**                   |
| 全量 AC-04              | `uv run pytest -q`                                                        | **FAIL** 1（见计划内 A8-P2-002） |

### GitNexus

`query({search_query: "us_trading_calendar CAL-US"})` → 未索引新模块（untracked 文件）；`detect_changes` @ `gitnexus-audit-summary.md` 报告 0 symbols（working tree 未 commit）。

### v4.1 execute-evidence 豁免

任务目录无 `execute-evidence/` 目录；依用户指令与 `AUDIT.plan.md` §1 A8 **不作为**本维门禁。

## §维度裁决

**FAIL**

S07-02..04 行为证据经 pytest 可证；但 S07-01 核心文件未纳入 `git diff 231b5798`、CAL-US registry 仍为 PENDING、全量 pytest 未绿——CAL-US 证据关账未完成。

## 计划内问题

| ID        | P   | 标题                              | 锚点                                                                                                 | 根因                                                                                        | 修复方案                                                                                                            | 验证                                                                           |
| --------- | --- | --------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| A8-P1-001 | P1  | S07-01 SSOT 模块未纳入 git 证据链 | `us_trading_calendar.py` · `to-issues-slices.md` §3                                                  | 文件为 `??` untracked，`git diff 231b5798` 不可见 S07-01 交付                               | `git add` 两文件并 commit；审阅者 `git diff 231b5798` 须含 SSOT 模块                                                | `git diff 231b5798 --stat` 含 `us_trading_calendar.py`                         |
| A8-P1-002 | P1  | S07 专项测文件未纳入 git 证据链   | `test_us_trading_calendar.py` · INDEX §2 AC-01..04                                                   | 同上 untracked；10 条 CAL-US 端到端测无法 diff 追溯                                         | 与 A8-P1-001 同 commit 纳入版本控制                                                                                 | `git diff 231b5798 -- tests/test_us_trading_calendar.py` 非空                  |
| A8-P2-001 | P2  | CAL-US registry 仍为 PENDING      | `docs/quality/round3h_real_data_production_entry_audit.md` L114 · `to-issues-slices.md` §7 S07-CLOSE | S07-CLOSE 未更新 registry 行 `CAL-US` → CLOSED                                              | 将 §7 CAL-US 行改为 CLOSED 并附 R3H-07 commit/evidence 指针                                                         | `rg 'CAL-US.*CLOSED' docs/quality/round3h_real_data_production_entry_audit.md` |
| A8-P2-002 | P2  | 全量 pytest 未绿（AC-04）         | `to-issues-slices.md` §6 · ENTRY §1 完成条件                                                         | `test_syncRegistry_cli_syncsYamlToDb` exit 2（Windows subprocess GBK `UnicodeDecodeError`） | 修复 `test_sync_orchestrator.py` subprocess `encoding='utf-8', errors='replace'` 或等效；与 R3H-07 无关但阻塞 AC-04 | `uv run pytest -q` exit 0                                                      |

## 计划外发现

| ID        | P   | 标题                                | 锚点                                                       | 根因                                                                         | 修复方案                                                                                                          | 验证                                                         |
| --------- | --- | ----------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| A8-P2-003 | P2  | 新 backend 包未登记 authority_graph | `AGENTS.md` loop §8 · `specs/context/authority_graph.yaml` | `us_trading_calendar` 无映射；`authority_graph.yaml` 本身亦为 untracked 变更 | `uv run python scripts/loop_maintain.py --fix` 登记 `backend/app/ops/data_health_profiles/us_trading_calendar.py` | `uv run python scripts/loop_maintain.py` exit 0              |
| A8-P3-001 | P3  | GitNexus 索引未含新 SSOT            | `gitnexus-audit-summary.md` · Boot #16                     | untracked + 未 re-analyze                                                    | commit 后 `node .gitnexus/run.cjs analyze`                                                                        | `query("us_trading_calendar")` 返回 `us_trading_calendar.py` |

已对抗搜索：`tests/` CAL-US 相关测、`backend/app/datasources/fetch_*`、`backend/app/layer4_markets/market_structure.py`、`docs/quality/round3h_real_data_production_entry_audit.md`、`specs/context/authority_graph.yaml`、全量 pytest 失败栈。
