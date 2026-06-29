# Plan 加固 — doubt-driven-development

> **日期：** 2026-06-29

---

## Cycle 1 — US 日历权威（S07-01）

### CLAIM

NYSE frozenset 足够闭合 CAL-US L2。

### 对抗发现

| #   | 发现                                    | 分类                                               |
| --- | --------------------------------------- | -------------------------------------------------- |
| D1  | NASDAQ 极少数与 NYSE 不同休市日         | **trade-off** — ponytail 合并；ADR-026 记录        |
| D2  | 2030 后假日漂移                         | **actionable** — ponytail 天花板；对称 CAL-CN-TAIL |
| D3  | 农历/浮动假日（Good Friday 等）须静态表 | **actionable** — 用显式日期表，不用 weekday proxy  |

### RECONCILE

采纳 ADR-026 bounded frozenset；Execute 用固定假日测锚定（Thanksgiving）。

---

## Cycle 2 — 翻转 R3H02 window_kind（S07-02）

### CLAIM

三源同时改 `trading_sessions` 不破坏 replay。

### 对抗发现

| #   | 发现                                        | 分类                                                                     |
| --- | ------------------------------------------- | ------------------------------------------------------------------------ |
| D4  | replay fixture 含假日 bar 会导致 GREEN 失败 | **actionable** — 过滤 mock 生成逻辑                                      |
| D5  | 只改 bundle 字段不改 span 仍 FAIL AC        | **actionable** — `fetch_window` 同步                                     |
| D6  | option chain 域是否改 window_kind           | **trade-off** — 本卡 US **equity bar** only；option 可保持 calendar_days |

### RECONCILE

S07-02 AC 限定 `us_equity_daily_bar` 三源；option chain 不在 CAL-US 必须项。

---

## Cycle 3 — Layer4 US_EQ（S07-03）

### CLAIM

不必实现 full US market live adapter；仅 calendar 拒绝即可 PASS G4 slice。

### 对抗发现

| #   | 发现                                 | 分类                                                      |
| --- | ------------------------------------ | --------------------------------------------------------- |
| D7  | `L4-US-DEFERRED` 与 G4 评级跳跃      | **trade-off** — 本卡闭合 CAL-US 登记；rating 证据写 audit |
| D8  | staged fixture 与 live calendar 双轨 | **actionable** — builder 内 consult `us_trading_calendar` |

### RECONCILE

S07-03 = 假日拒绝 + 交易日通过；不扩 whitelist universe。

---

## Stop condition

三轮后无 P0 Plan 缺陷；Execute 细节在切片内 TDD。

---

## doubt-driven-development 验证清单

- [x] ≥3 轮 doubt cycle
- [x] actionable 项绑定切片
- [x] trade-off 已 ADR/注释承接
