# A3 架构审计 — R3H-07 US Trading Calendar（CAL-US SSOT）

| 字段      | 值                                                                  |
| --------- | ------------------------------------------------------------------- |
| 维度      | A3 架构（单 SSOT · CN 隔离 · 模块边界）                             |
| 任务      | `06-29-round3h-r3h07-us-trading-calendar`                           |
| 协议      | `plan_protocol_version: 4.1`                                        |
| Diff 基线 | `git diff 231b5798`（Plan freeze commit）                           |
| 审计日期  | 2026-06-29                                                          |
| 模式      | 只读 · 静态 diff + 独立 pytest（不 commit）                         |
| 权威      | ADR-026 · `AUDIT.plan.md` §1 A3 · `00-EXECUTION-ENTRY.md` §2        |
| 模板      | `agents/audit-finding-schema.md` · `agents/audit-coverage-model.md` |

---

## 维度证据

### ADR-026 / AUDIT.plan §1 A3 checklist

| 检查项                                             | 裁决     | 证据                                                                                                                                                                                                                                                  |
| -------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 单一 SSOT：`us_trading_calendar.py` 为 US 假日权威 | **PASS** | 新增 `backend/app/ops/data_health_profiles/us_trading_calendar.py`；假日生成逻辑（周末 + federal market holidays）仅在此模块；`rg` 全 `backend/` 无第二份 US 假日表                                                                                   |
| C3 与 G4 共用同一 SSOT                             | **PASS** | C3：`fetch_window.py` 经 `_us_trading_calendar()` lazy import 调用 `is_trading_day`；三 port（yahoo/stooq/alpha_vantage）仅 import `fetch_window` 助手，不直连假日表。G4：`MarketStructureBuilder.build` 在 `US_EQ` 分支 lazy import `is_trading_day` |
| `cn_trading_calendar` 未改动                       | **PASS** | `git diff 231b5798 -- cn_trading_calendar.py` 空；`layer4_markets/market_structure.py` 无 `cn_trading_calendar` import                                                                                                                                |
| 禁止 per-source 假日表                             | **PASS** | `fetch_ports/` 内无 `holiday`/`NON_TRADING`/`_federal_market` 定义；仅 `filter_us_trading_day_bars` / `recent_trading_dates` 委托 SSOT                                                                                                                |
| Lazy import（破环）                                | **PASS** | `fetch_window._us_trading_calendar()` 函数内 import + `ponytail:` 注释；`market_structure.build` 在 `US_EQ` 分支函数体内 import                                                                                                                       |
| Wave 2（R3H-08）承接项未 silent bypass             | **PASS** | diff 未触 `service.py` · `sync/**` · `interface_probe` · `run_reconcile` · `build_route_matrix`；`ENTRY §2 Wave 2 承接表` 三项仍阶段外置                                                                                                              |
| ADR 显式排除：crypto 仍 `calendar_days`            | **PASS** | `coingecko_port.py` · `deribit_port.py` 不在 diff；US port 对非 `is_us_equity_bar_fetch` 路径保留 `window_kind: calendar_days`（如 AV `us_option_chain`）                                                                                             |
| API 镜像 CN 形状                                   | **PASS** | `is_trading_day` / `get_trading_days` / `get_missing_trading_days` 三函数对称；`ponytail:` 2030 天花板注释与 CAL-CN-TAIL 模式一致                                                                                                                     |
| 有界范围 2000–2030                                 | **PASS** | `_RANGE_START` / `_RANGE_END`；`is_trading_day` 越界返回 `False`                                                                                                                                                                                      |

### 模块边界与 import 图（对抗性）

```text
us_trading_calendar.py (L2 ops SSOT)
    ↑ lazy import
fetch_window.py (C3 共享门面)
    ↑ import
yahoo_finance_port · stooq_port · alpha_vantage_port

us_trading_calendar.is_trading_day
    ↑ lazy import (US_EQ only)
MarketStructureBuilder.build (G4)
```

- **无环：** datasources 不顶层 import ops；lazy 破 `data_health_profiles ↔ datasources` 环。
- **CN 路径隔离：** `calendar_gap_rules` / `cn_market` 仍只引用 `cn_trading_calendar`；本 diff 未改。
- **访问模式差异（计划内）：** C3 经 `fetch_window` 门面；G4 直接 lazy import SSOT — 符合 ADR-026 §4（ports 用 shared helper）与 §5（Layer4 用同一 module），非双 SSOT。

### 静态命令

```bash
git diff 231b5798 --name-only
# → us_trading_calendar.py（新）· fetch_window.py · 3 US ports · market_structure.py · tests/fixtures · 索引

rg "us_trading_calendar|_federal_market|NON_TRADING" backend/app/datasources/fetch_ports/
# → 仅 fetch_window 助手名；无假日表

rg "import.*us_trading_calendar|from.*us_trading_calendar" backend/
# → fetch_window.py:13 · market_structure.py:196（均为 lazy/函数体内）

git diff 231b5798 -- backend/app/ops/data_health_profiles/cn_trading_calendar.py
# → 空
```

### Pytest 复验（架构不变量）

```bash
uv run pytest -q tests/test_us_trading_calendar.py \
  tests/test_market_data_adapters.py \
  tests/test_layer4_market_structure.py \
  tests/test_cn_market_adapters.py -k calendar
# → 15 passed
```

| 用例簇                                   | 证明的架构不变量                                              |
| ---------------------------------------- | ------------------------------------------------------------- |
| `test_us_trading_calendar.py`            | SSOT API · 三源 `window_kind==trading_sessions` · G4 假日拒绝 |
| `test_market_data_adapters.py`           | evidence 契约与 CAL-US 一致                                   |
| `test_layer4_market_structure.py`        | `US_EQ` + `CN_A` 路径未互污                                   |
| `test_cn_market_adapters.py -k calendar` | CN 日历回归绿                                                 |

### GitNexus impact（变更符号）

| 调用                                                     | 结果                                                            |
| -------------------------------------------------------- | --------------------------------------------------------------- |
| `impact(is_trading_day, upstream)`                       | **symbol not found**（索引未收录 working tree 新符号）          |
| `impact(filter_us_trading_day_bars, upstream)`           | **symbol not found**                                            |
| `impact(MarketStructureBuilder, upstream)`               | **symbol not found**                                            |
| `detect_changes({scope:"compare", base_ref:"231b5798"})` | `changed_files: 15` · `changed_symbols: []` · `risk_level: low` |

**手工 blast radius（对照 `research/gitnexus-summary.md` / `gitnexus-audit-summary.md`）：**

| 符号 / 区域                                           | 直接上游                                                                                   | 风险             |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------ | ---------------- |
| `us_trading_calendar.is_trading_day`                  | `fetch_window` 三助手 · `MarketStructureBuilder.build(US_EQ)` · `test_us_trading_calendar` | **MEDIUM**       |
| `filter_us_trading_day_bars` / `recent_trading_dates` | yahoo · stooq · alpha_vantage mock/replay                                                  | **MEDIUM**       |
| `MarketStructureBuilder.build`                        | layer4 tests · staged pilots                                                               | **MEDIUM**       |
| `cn_trading_calendar`                                 | `calendar_gap_rules` · CN health（未改）                                                   | **LOW**          |
| `DataSourceService.fetch` / reconcile / probe         | 未在 diff 中                                                                               | **无本卡架构面** |

**索引滞后：** 合并前建议 `node .gitnexus/run.cjs analyze` 刷新；不构成 CAL-US SSOT 架构 FAIL。

### 残余观察（非 finding · 记入维度证据）

1. `recent_trading_window_start` 已定义但当前无调用方；mock 路径用 `recent_trading_dates` + `window_kind` 闭合 S07-02 测。显式 `start_time/end_time` 窗仍走 `reject_window_span_over_cap` 日历日语义 — 属 A5/后续 live 切片范畴，不破坏 SSOT 单一权威。
2. G4 `build` 对 `US_EQ` 有双重非交易日守卫（SSOT `is_trading_day` + fixture `calendar_for_day.is_trading_day`）— 纵深一致，非双 SSOT。

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

已对抗搜索：`git diff 231b5798` 全量 · `backend/app/datasources/**` · `backend/app/layer4_markets/**` · `backend/app/ops/data_health_profiles/**` · `rg` US 假日/双 SSOT/per-source 表 · Wave 2 路径名 · crypto port 排除 · CN 回归 pytest · GitNexus impact/detect_changes。

---

## 正面观察

- **CAL-US 闭合形态正确：** 假日权威单点；C3 门面 + G4 直连均回落同一 `us_trading_calendar`。
- **CN 隔离干净：** A 股日历模块与 import 链零改动；CN 日历 pytest 绿。
- **ponytail 有界：** 2030 天花板与升级路径注释；lazy import 破环有文档。
- **Wave 2 未越界：** R3H-08 reconcile/probe 承接项无 silent 实现或 bypass。

---

## Verdict

| 项                                        | 结论                  |
| ----------------------------------------- | --------------------- |
| **A3 AUDIT.plan §1（单 SSOT · CN 隔离）** | **PASS**              |
| ADR-026 架构决策 1–6                      | ✅                    |
| C3 + G4 共用 SSOT                         | ✅                    |
| 无 per-source 假日表                      | ✅                    |
| Lazy import                               | ✅                    |
| R3H-08 Wave 2 未 fail                     | ✅                    |
| Findings 非占位                           | **0** → 维度 **PASS** |

<!-- A9: 总裁决仅写入 audit.report.md §4.2 -->
