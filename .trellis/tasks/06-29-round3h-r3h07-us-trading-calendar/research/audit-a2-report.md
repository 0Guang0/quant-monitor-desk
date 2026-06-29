# A2 Ponytail 审计报告 — R3H-07 CAL-US

> **维：** audit-ponytail (A2)  
> **任务：** `06-29-round3h-r3h07-us-trading-calendar`  
> **协议：** `plan_protocol_version: 4.1`  
> **模板：** `agents/audit-a2-ponytail.md`  
> **Diff 基线：** `git diff 231b5798` · scope `backend/` + `tests/`  
> **日期：** 2026-06-29

---

## 维度证据

### git diff --stat（backend/ + tests/）

```
 backend/app/datasources/fetch_ports/alpha_vantage_port.py  |  32 +-
 backend/app/datasources/fetch_ports/stooq_port.py          |  32 +-
 backend/app/datasources/fetch_ports/yahoo_finance_port.py |  38 +-
 backend/app/datasources/fetch_window.py                    |  65 ++
 backend/app/layer4_markets/market_structure.py           |  33 +-
 tests/fixtures/replay/market_data/...                     |   6 (3 files)
 tests/test_catalog.yaml                                   | 665 +++++++++------------
 tests/test_layer4_market_structure.py                     |  70 +++
 tests/test_market_data_adapters.py                        |  12 +-
 11 files changed, 555 insertions(+), 398 deletions(-)
```

**未纳入 stat 的未跟踪交付物（Execute 已落地，A2 必读）：**

- `backend/app/ops/data_health_profiles/us_trading_calendar.py`（~118 LOC）
- `tests/test_us_trading_calendar.py`（~310 LOC）

**净增粗算：** 生产 ~+280 LOC（含 us_trading_calendar + fetch_window + ports + layer4）；测试 ~+380 LOC（含新模块测 + layer4 US 测）；`test_catalog.yaml` 为机械重排非业务逻辑。

### A2 checklist

- [x] `git diff --stat` 已记录
- [x] 每候选附 `file:line` + ponytail 梯级
- [x] 与 A4 交叉：port 层无重复错误模型抽象；`filter_us_trading_day_bars` 静默丢 bar 属 A4 语义维，本维仅记「冗余调用」
- [x] 阻塞 vs 建议：P0 无；P1–P3 见 findings 表

### §3.2 候选删改追溯

| 候选删改（file:line）                                                                              | ponytail 梯级                              | 备注                                                    |
| -------------------------------------------------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------- |
| `fetch_window.py:30-46` `recent_trading_window_start` 零调用                                       | 梯级 1（YAGNI）                            | 全仓 grep 仅定义处命中                                  |
| `market_structure.py:151-159` `StagedUSEquityMarketAdapter`                                        | 梯级 2（复用 CNA 适配器形态）              | 与 `StagedCNAMarketAdapter` 方法体相同                  |
| `alpha_vantage_port.py:54-68` + `stooq_port.py:49-63` + `yahoo_finance_port.py:74-88` US mock 分支 | 梯级 2（抽 `fetch_window` 共享）           | 三份近重复 bar 模板                                     |
| 三 port `window_kind` 三元 (~5×3 行)                                                               | 梯级 2                                     | 可 `us_equity_window_kind(domain, symbol)` 一行         |
| `alpha_vantage_port.py:151-152` / `stooq_port.py:97-98` 二次 `filter_us_trading_day_bars`          | 梯级 5（mock 已用 `recent_trading_dates`） | replay 路径应在 `_mock_*` 内过滤一次即可                |
| `test_us_trading_calendar.py:61-84` vs `144-184`                                                   | 梯级 6（测试 purpose 重叠）                | 同断言三源 `trading_sessions`                           |
| `test_us_trading_calendar.py:245-288` service 接线                                                 | 梯级 2                                     | `tests/service_path_support.enable_source_route` 已存在 |

### DOUBT（≥20 行可简化）

**结论：有。** 已读：`us_trading_calendar.py`、`fetch_window.py`、三 US port、`market_structure.py` US 绑定、`test_us_trading_calendar.py`、`test_layer4_market_structure.py` US 段；对照 `cn_trading_calendar.py` 与 `to-issues-slices.md` S07-01..04。

**明确不算 bloat（AC/ADR 要求，勿删）：**

- `us_trading_calendar.py` 假日生成器（`_easter_sunday`、`_nth_weekday_of_month` 等）— ADR-026 拒绝「仅 weekday」；CN 用静态表、US 用算法表，对称 API 即可。
- Layer4 `US_EQ` 前置 `is_trading_day`（`market_structure.py:195-201`）— S07-03 要求 SSOT 先于 fixture 行；与下方 `calendar_for_day.is_trading_day` 非重复职责。
- `fetch_window._us_trading_calendar()` lazy import — 破 cycle，保留。

---

## §维度裁决

**FAIL**

（findings 表共 6 行非占位候选删改。）

---

## 计划内问题

| ID       | P   | 标题                                       | 锚点                                                                                                          | 根因                                                                                              | 修复方案                                                                                                                                                          | 验证                                                                                                         |
| -------- | --- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| A2-P2-01 | P2  | `recent_trading_window_start` 死代码       | `backend/app/datasources/fetch_window.py:30-46`                                                               | ADR-026 要求扩展 trading-session helper，但 Execute 仅消费 `recent_trading_dates`；无 port/测调用 | 删除 `recent_trading_window_start`；若 S07-02 需 span cap 再按调用点加回                                                                                          | `rg recent_trading_window_start backend tests` 零命中；`uv run pytest -q`                                    |
| A2-P2-02 | P2  | 三 port US mock + `window_kind` 拷贝粘贴   | `alpha_vantage_port.py:54-68,153-157` · `stooq_port.py:49-63,100-104` · `yahoo_finance_port.py:74-88,120-124` | S07-02 要求三源均改，但未抽共享 helper                                                            | 在 `fetch_window.py` 增加 `us_equity_window_kind(...)` + `mock_us_equity_daily_bars(symbol, count, source_used)`（或等价 ≤15 行）；三 port 各保留 domain 分支一次 | 三 port 各减 ≥10 行；`uv run pytest -q tests/test_us_trading_calendar.py tests/test_market_data_adapters.py` |
| A2-P3-03 | P3  | mock 路径二次 `filter_us_trading_day_bars` | `alpha_vantage_port.py:151-152` · `stooq_port.py:97-98`                                                       | `_mock_*` 已用 `recent_trading_dates` 仅产出交易日；`fetch_payload` 再滤冗余                      | 移除 `fetch_payload` 内二次 filter；replay/合成 bar 仅在 `_mock_*` 出口调用一次 `filter_us_trading_day_bars`                                                      | `test_yahooFinance_fetchPayload_excludesHolidayBars` · `test_calUs_holidayWindow_*` 仍绿                     |
| A2-P2-04 | P2  | BOOT 测与 S07-02 测重复                    | `tests/test_us_trading_calendar.py:61-84` · `144-184`                                                         | S07-BOOT RED 转 GREEN 后未收敛：两测均 parametrize 三源断言 `window_kind==trading_sessions`       | 合并为一测（保留五字段 docstring 覆盖 BOOT+S07-02）；或 BOOT 测改断言「非 calendar*days」并删 `test_marketData*\*` 重复体                                         | 合并后 `test_us_trading_calendar.py` 净减 ≥25 行；`uv run pytest -q tests/test_us_trading_calendar.py`       |

---

## 计划外发现

| ID       | P   | 标题                                   | 锚点                                                             | 根因                                                                                                                      | 修复方案                                                                                                                                                                | 验证                                                                                                                                           |
| -------- | --- | -------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| A2-P2-05 | P2  | `StagedUSEquityMarketAdapter` 空壳重复 | `backend/app/layer4_markets/market_structure.py:151-159,277-284` | 计划外复制 CNA 类；`load_calendar`/`load_breadth` 与 CNA 完全相同                                                         | 单 `StagedFixtureMarketAdapter(market_id: str)` 或去掉 US 子类、`_adapter_for_market` 对 US_EQ 仍返回 CNA 实例（`market_id` 仅 registry 用）                            | `uv run pytest -q tests/test_layer4_market_structure.py -k usEquity`                                                                           |
| A2-P2-06 | P2  | DataSourceService 金路径测手工接线膨胀 | `tests/test_us_trading_calendar.py:245-288`                      | 未复用 `tests/service_path_support.enable_source_route` / `patch_fetch_port_evidence_adapter`（R3H-04 已有 dedup helper） | 改用 `enable_source_route(monkeypatch, source_id="yahoo_finance", data_domain="us_equity_daily_bar")` + 注入 yahoo port；删内联 `DomainRoleBinding`/`_ready_yahoo_plan` | 该测 setup 净减 ≥30 行；`uv run pytest -q tests/test_us_trading_calendar.py::test_datasourceService_usEquityFetch_exposesTradingSessionWindow` |

已对抗搜索：`backend/app/datasources/fetch_window.py`、`fetch_ports/{yahoo,stooq,alpha_vantage}_port.py`、`ops/data_health_profiles/us_trading_calendar.py`、`layer4_markets/market_structure.py`、`tests/test_us_trading_calendar.py`、`tests/test_layer4_market_structure.py`；对照 `cn_trading_calendar.py`、`service_path_support.py`、`to-issues-slices.md` S07-01..04。

---

**Finding 计数：** 6（计划内 4 · 计划外 2）  
**裁决：** FAIL
