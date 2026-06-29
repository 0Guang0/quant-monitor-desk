# R3H-07 `/to-issues` 垂直切片

> **Execute 入口：** `research/00-EXECUTION-ENTRY.md`  
> **活卡：** `R3H_07_US_TRADING_CALENDAR.md`  
> **Module：** **G4**（主）· **C3**（US 拉数窗）  
> **评级：** `R3_STAGED_FIXTURE_CLOSED` → `R4_SANDBOX_REAL_DATA_OR_REHEARSAL`  
> **前置：** R3H-10 CLOSED @ `227e0734`  
> **映射：** Trellis Step `9.0`..`9.4` = S07-BOOT..S07-04 · S07-CLOSE → Audit

---

## 0. 切片原则

| 原则          | 本任务                                                           |
| ------------- | ---------------------------------------------------------------- |
| Tracer bullet | 每切片 = 端到端可验证行为（日历 → fetch evidence → layer4 拒绝） |
| SSOT          | 假日权威 **仅** `us_trading_calendar.py`；C3/G4 共用             |
| CN 隔离       | 不修改 `cn_trading_calendar.py` 语义                             |
| 不在范围      | R3H-08 live · 新 migration · crypto `calendar_days`              |

---

## 1. 切片总表

| 序  | ID            | 标题                   | 阻塞          | Step  | 评级  |
| --- | ------------- | ---------------------- | ------------- | ----- | ----- |
| 0   | **S07-BOOT**  | CAL-US 自然日窗基线    | R3H-10 CLOSED | `9.0` | —     |
| 1   | **S07-01**    | US 日历 SSOT 数据面    | BOOT          | `9.1` | G4,C3 |
| 2   | **S07-02**    | C3 拉数窗 + evidence   | S07-01        | `9.2` | C3    |
| 3   | **S07-03**    | G4 Layer4 绑定         | S07-01        | `9.3` | G4    |
| 4   | **S07-04**    | 负向：美股假日不拉     | S07-02,03     | `9.4` | G4,C3 |
| 5   | **S07-CLOSE** | CAL-US 关账 + registry | S07-04        | Audit | G4→R4 |

```text
S07-BOOT
  └→ S07-01 ─┬→ S07-02 ─┐
             └→ S07-03 ─┴→ S07-04 → S07-CLOSE
```

---

## 2. S07-BOOT — CAL-US 自然日窗基线

### What to build

盘点 US equity 源仍使用自然日窗 / `calendar_days` 的入口，产出基线矩阵并写 **RED** 测证明缺口（期望 FAIL 直至 S07-02 GREEN）。

### 交付物

- `research/calendar-baseline-matrix.md`
- `execute-evidence/9.0-red.txt`（基线测 RED）
- `execute-evidence/9.0-green.txt`（矩阵完成 + 全量 pytest 快照 @ BOOT 末）

### 验收

- [ ] 矩阵含 yahoo_finance · stooq · alpha_vantage · `fetch_window` · R3H02 evidence 契约
- [ ] 每行：`入口` · `当前 window_kind` · `目标切片` · `风险`
- [ ] RED 测：US 源 evidence 仍为 `calendar_days`（或假日未过滤）→ **故意 FAIL**

### 建议测试（TDD · 五字段草案）

| 测名草案                                                           | 目的                                                                                     |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| `test_calUsBoot_usSourcesEvidenceStillCalendarDays_pendingClosure` | BOOT RED：yahoo/stooq/AV replay 断言 `window_kind==calendar_days` **或** 假日 bar 未过滤 |

### Blocked by

R3H-10 CLOSED

---

## 3. S07-01 — US 日历 SSOT 数据面

### What to build

新增 `backend/app/ops/data_health_profiles/us_trading_calendar.py`：bounded NYSE 非交易日 frozenset（2000–2030）、`is_trading_day` / `get_trading_days` / `get_missing_trading_days`（镜像 CN API）。

### 端到端行为

`us_trading_calendar.is_trading_day(date(2024, 11, 28))` → `False`（Thanksgiving）；`date(2024, 11, 29)` → `True`（若交易所开市规则按 ADR-026 表）。

### 验收

- [ ] 模块 API 与 `cn_trading_calendar` 对称（不含 CN 特有农历生成器）
- [ ] `ponytail:` 注释标明 2030+ 天花板与升级路径
- [ ] 专项测绿：S07-01 新建 us 日历模块测文件
- [ ] `execute-evidence/9.1-red.txt` → `9.1-green.txt`

### 建议测试（五字段草案）

| 测名草案                                                  | 验证点                 |
| --------------------------------------------------------- | ---------------------- |
| `test_usTradingCalendar_thanksgiving2024_isNonTradingDay` | 固定假日为非交易日     |
| `test_usTradingCalendar_regularWeekday_isTradingDay`      | 普通周二为交易日       |
| `test_usTradingCalendar_getTradingDays_respectsBounds`    | 范围有界、无空跑万年历 |

### Blocked by

S07-BOOT

---

## 4. S07-02 — C3 拉数窗接线

### What to build

US fetch ports（`yahoo_finance_port` · `stooq_port` · `alpha_vantage_port`）与 `fetch_window.py`：

- 窗口 span 按 **trading sessions** 计 cap
- evidence bundle `window_kind: trading_sessions`
- mock/replay bar 日期落在交易日；假日不生成 bar
- 经 `DataSourceService.fetch` 路径可验证 bundle 字段（现有金路径测扩展）

### 端到端行为

对 `us_equity_daily_bar` fetch（fixture/replay），返回 bundle 的 `window_kind` 为 `trading_sessions`，且 span 内 bar 的 `trade_date` 均为 US 交易日。

### 验收

- [ ] 三源 port 均更新（禁止只改 yahoo）
- [ ] `test_market_data_adapters.py` R3H02-R-22 契约 **翻转** 为 `trading_sessions`
- [ ] `tests/test_datasource_service.py` 或 `test_vendor_fetch_e2e.py` 扩展：service fetch 后 bundle window_kind 可验证
- [ ] `execute-evidence/9.2-red.txt` → `9.2-green.txt`

### 建议测试（五字段草案）

| 测名草案                                                           | 验证点                      |
| ------------------------------------------------------------------ | --------------------------- |
| `test_marketData_usSourceEvidence_windowKindTradingSessions`       | 三源 evidence `window_kind` |
| `test_yahooFinance_fetchPayload_excludesHolidayBars`               | 假日无 bar                  |
| `test_datasourceService_usEquityFetch_exposesTradingSessionWindow` | service 金路径 window 语义  |

### Blocked by

S07-01

---

## 5. S07-03 — G4 Layer4 loader 绑定

### What to build

Layer4 `MarketStructureBuilder`（及 US 适配路径）对 `US_EQ` 使用 `us_trading_calendar`：

- 非交易日 `build` → `Layer4MarketError`（含 `non-trading`）
- 交易日通过（fixture 或生成 bounded calendar row）

### 端到端行为

`MarketStructureBuilder.build(market_id="US_EQ", trade_date=<thanksgiving>)` 拒绝；普通交易日通过。

### 验收

- [ ] 与 CN 非交易日测对称（`test_layer4_market_structure.py` 模式）
- [ ] 不触发全市场扫描；仅用 bounded calendar 行集 / fixture
- [ ] `execute-evidence/9.3-red.txt` → `9.3-green.txt`

### 建议测试（五字段草案）

| 测名草案                                             | 验证点      |
| ---------------------------------------------------- | ----------- |
| `test_layer4_usEquity_buildRejectsNonTradingHoliday` | US 假日拒绝 |
| `test_layer4_usEquity_buildAllowsTradingDay`         | 交易日通过  |

### Blocked by

S07-01

---

## 6. S07-04 — 负向：美股假日不拉

### What to build

端到端负向：在美股联邦假日窗口，fetch plan / port **不得** 产出有效交易日 bar；Layer4 同步拒绝。覆盖至少 **一个** 固定假日（Thanksgiving 2024 推荐）。

### 验收

- [ ] RED→GREEN 证据齐全
- [ ] CN 回归：`tests/test_cn_market_adapters.py` 日历 authority 用例仍绿
- [ ] 全量 `uv run pytest -q` 绿
- [ ] `execute-evidence/9.4-red.txt` → `9.4-green.txt`

### 建议测试（五字段草案）

| 测名草案                                                                   | 验证点                     |
| -------------------------------------------------------------------------- | -------------------------- |
| `test_calUs_holidayWindow_usFetchProducesNoTradingBars`                    | 假日窗无 bar / FAIL closed |
| `test_cnMarket_calendarAuthorityRegression_stillFailsOnMissingTradingDays` | CN Q12 不回退              |

### Blocked by

S07-02, S07-03

---

## 7. S07-CLOSE — 审计 + registry

### What to build

- `CAL-US` = **CLOSED** 登记（`docs/quality/round3h_real_data_production_entry_audit.md` 或 MODULE rating 证据）
- G4 `R3→R4` 证据路径
- Audit A1–A8 PASS

### 验收

- [ ] S07-01..04 证据齐全
- [ ] `validate-execute-handoff` exit 0
- [ ] Wave 1b 状态更新 `R3H_PASS_EXECUTION_PLAN.md` §3

### Blocked by

S07-04

---

## Out of scope

- R3H-08 真网 live 产品化
- 新 clean DDL / migration
- `deribit` / `coingecko` 日历（维持 `calendar_days`）
- CN 日历 2030+ tail（`CAL-CN-TAIL` → R3H-05）
