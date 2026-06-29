# A4 安全审计 — R3H-07 US Trading Calendar (CAL-US)

> **维度：** A4 安全（本任务 `AUDIT.plan.md` §1 覆写；非全局 yaml A4=quality）  
> **任务：** `.trellis/tasks/06-29-round3h-r3h07-us-trading-calendar/`  
> **协议：** `plan_protocol_version: 4.1`  
> **Diff 基线：** `git diff 231b5798`  
> **权威：** `agents/audit-boot-v4.1.md` · `agents/audit-adversarial-authority.md` · `agents/audit-finding-schema.md`  
> **模式：** 只读（未改生产代码）  
> **日期：** 2026-06-29

---

## 维度证据

### 审查范围（diff 生产面）

| 文件                                                                              | 安全相关变更摘要                                                 |
| --------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `backend/app/ops/data_health_profiles/us_trading_calendar.py`                     | **新增** CAL-US SSOT；`_RANGE_START`/`_RANGE_END` 有界 frozenset |
| `backend/app/datasources/fetch_window.py`                                         | 交易日窗 helper；反向扫描含 `_RANGE_START` 硬停                  |
| `backend/app/datasources/fetch_ports/{yahoo_finance,stooq,alpha_vantage}_port.py` | mock/replay 路径接 `trading_sessions` 过滤；无新网络/密钥        |
| `backend/app/layer4_markets/market_structure.py`                                  | `US_EQ` 非交易日 fail-closed 阻断 snapshot                       |

### AUDIT.plan §1 A4 checklist

| 检查项                          | 结论     | 证据                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 有界日历（禁止无界/万年历扫描） | **满足** | `us_trading_calendar.py:10-11` 固定 `2000-01-01`..`2030-12-31`；`_load_non_trading_days` 仅遍历该区间（≈11.3K 日）；`is_trading_day` 超界返回 `False`（fail-closed）；`fetch_window.recent_trading_dates` / `recent_trading_window_start` 在 `current < cal._RANGE_START` 时终止（`fetch_window.py:44-45,57-58`）；`test_usTradingCalendar_getTradingDays_respectsBounds` 断言 `_RANGE_END+1` 为 False |
| 无 secrets 进 repo / diff       | **满足** | 对上述生产文件 `rg` 无 `api_key`/`secret`/`token`/`password`/`https://` 命中；三 port diff 未新增 env 读取或硬编码凭据                                                                                                                                                                                                                                                                                 |
| 无新信任边界破坏                | **满足** | Layer4 `US_EQ` 在非交易日 `raise Layer4MarketError`（`market_structure.py:195-201`）**加强** fail-closed；`cn_trading_calendar` 未改；无新 ops CLI 写路径、无 DB migration、无 live 源默认开启                                                                                                                                                                                                         |
| fetch ports 安全姿态不变        | **满足** | 三 port 仍 mock-first；`SYMBOL_WHITELIST` / `_reject_unknown_symbol` / `reject_over_cap` / `reject_window_span_over_cap` 保留；`AlphaVantageLiveFetchPort` 仍要求 `ALPHA_VANTAGE_API_KEY`（`alpha_vantage_port.py:184-185`）且委托 mock；diff 仅增日历过滤与 `window_kind` 元数据，无新 HTTP 出站                                                                                                      |

### 静态安全基线（security-auditor 命令 · 变更文件子集）

```text
rg "https?://|api[_-]?key|secret|token|password" \
  backend/app/ops/data_health_profiles/us_trading_calendar.py \
  backend/app/datasources/fetch_window.py \
  backend/app/datasources/fetch_ports/{yahoo_finance,stooq,alpha_vantage}_port.py \
  backend/app/layer4_markets/market_structure.py
→ 0 命中（us_trading_calendar / fetch_window）；port 仅既有 _alpha_vantage_api_key 模式未变

rg "f\".*SELECT|execute\(f|subprocess|eval\(|exec\(" \
  us_trading_calendar.py fetch_window.py market_structure.py
→ 0 命中（本切片无 SQL/动态执行面）
```

### GitNexus

`query({query: "us_trading_calendar fetch_window security trust boundary"})` — 命中 `fetch_payload`→`recent_window_start` 等既有拉数流程；**无**本次 diff 引入的新外部 I/O 或 auth 旁路符号。

### DOUBT（对抗 · 三类）

| 类别               | 攻击                                    | 结果                                                                  |
| ------------------ | --------------------------------------- | --------------------------------------------------------------------- |
| 硬编码 URL 变体    | diff 新增模块/端口是否引入未授权 egress | **无发现** — 变更文件无 URL 常量                                      |
| JWT / API key 模式 | diff 是否新增凭据读取或日志泄露         | **无发现** — 仅保留 AV 既有 `os.environ.get("ALPHA_VANTAGE_API_KEY")` |
| SQL 拼接           | 日历接线是否引入 DuckDB/SQL 面          | **无发现** — 本切片纯 Python 日期逻辑                                 |

**补充对抗（计划未写）：**

| Claim                                                        | Attack                                 | Result                                                                                                                                      |
| ------------------------------------------------------------ | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `recent_trading_window_start(trading_sessions=N)` 可无限回溯 | `N` 极大时 while 回溯至 `_RANGE_START` | **有界** — 最坏 ≈ 今日至 2000-01-01 日历日数（<10K 次），非无界                                                                             |
| `filter_us_trading_day_bars` 解析不可信 `trade_date`         | 恶意字符串致 `date.fromisoformat` 抛错 | **非新信任边界** — bar 来源仍为 mock 生成或本地 replay fixture（与改前相同信任级）；畸形日期在未过滤路径亦会进入 bundle；属健壮性非安全回归 |
| `instrument_id.endswith(".US")` 扩大交易日过滤面             | 伪造后缀绕过白名单                     | **不成立** — 白名单校验仍在 `fetch_payload` 入口；后缀仅影响窗语义，不开放新 symbol                                                         |

### ENTRY §2 安全相关约束对照

| 约束                                      | 状态                                              |
| ----------------------------------------- | ------------------------------------------------- |
| 禁止万年历无 cap                          | **闭合** — ADR-026 + `ponytail:` 注释 2030 天花板 |
| 禁止 per-source 假日表                    | **闭合** — 假日仅 `us_trading_calendar.py`        |
| CN 隔离（不得回退 `cn_trading_calendar`） | **闭合** — diff 未触 CN 模块                      |
| R3H-08 live / migration 不在范围          | **闭合** — 无 live 接线、无 migration             |

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

已对抗搜索：`git diff 231b5798` 全部生产变更 · `us_trading_calendar.py` / `fetch_window.py` 循环与边界 · 三 US fetch port 白名单/cap/live 门控 · `market_structure.py` US_EQ 阻断分支 · secrets/SQL/subprocess rg 基线 · GitNexus fetch 流程 · `tests/test_us_trading_calendar.py` 有界测 `test_usTradingCalendar_getTradingDays_respectsBounds`。

---

_审计时间：2026-06-29 · A4 只读 · 裁决 PASS_
