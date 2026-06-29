# R3H-07 参考采纳调研

- **任务：** `.trellis/tasks/06-29-round3h-r3h07-us-trading-calendar/`
- **日期：** 2026-06-29
- **方式：** QMD 已有 CN 先例优先；参考树只读（若本地存在）

---

## 0. 铁律

1. **禁止** runtime `import 参考项目/**`
2. **CN 先例 = 主采纳路径：** `backend/app/ops/data_health_profiles/cn_trading_calendar.py`（R3H-03 L2）
3. US 不引入新依赖（pandas_market_calendars / exchange HTTP）
4. OpenBB = `architecture_only`（R3H-02 已登记）

---

## 1. QMD 内权威（非参考树）

| 文件                     | 可采纳模式                                                       | R3H-07 用法                                                        |
| ------------------------ | ---------------------------------------------------------------- | ------------------------------------------------------------------ |
| `cn_trading_calendar.py` | `_NON_TRADING_DAYS` frozenset · `is_trading_day` · bounded range | **L2 镜像** → `us_trading_calendar.py`                             |
| `calendar_gap_rules.py`  | `calendar_authority=True` gap detect                             | US 本卡 **不**扩 gap rules（仅 window_kind + layer4）；CN 路径不动 |
| `fetch_window.py`        | `recent_window_start(calendar_days)`                             | 增 `trading_sessions` 变体                                         |
| `market_data.py`         | `window_kind` on evidence bundle                                 | US → `trading_sessions`                                            |
| `market_structure.py`    | non-trading `Layer4MarketError`                                  | US_EQ 复用同一拒绝模式                                             |

---

## 2. R3H-03 / R3H-02 追溯

| 来源                                 | 结论                                                                        |
| ------------------------------------ | --------------------------------------------------------------------------- |
| R3H-03 Q12                           | CN `TradingCalendar` → `cn_trading_calendar` **已闭合**；本卡 **不得** 回退 |
| R3H-02 R3H02-R-22                    | US 故意 `calendar_days` ponytail → **本卡闭合** CAL-US                      |
| `R3H_02_REFERENCE_ADOPTION_AUDIT.md` | US G2 延后 R3H-05/CAL-US → **本卡即 CAL-US 执行轨**                         |

---

## 3. 参考项目（只读 · 结论锚点）

> 注：`参考项目/**` 可能未 clone；下列以 R3H-03 audit 已消化结论 + QMD 源码为准。

| 参考                                         | 锚点                                                     | 采纳                                            |
| -------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------- |
| EasyXT `smart_data_detector.TradingCalendar` | R3H-03 audit：节假日逻辑 L2 拷改至 `cn_trading_calendar` | **L2 模式复用** — US 独立模块，不 import EasyXT |
| digital-oracle `yfinance_provider` / `stooq` | R3H-02：metadata/gather 灵感 only                        | **L3** — 不抄 HTTP；窗口语义走 QMD calendar     |
| OpenBB providers                             | architecture_only                                        | 无 runtime 采纳                                 |

---

## 4. 反模式（禁止进入产品路径）

- 每源一份 US 假日表（yahoo vs stooq）
- `parse_pilot_date_window` 的 `1.5x` 估算当作产品 SSOT
- Mon–Fri proxy 冒充 NYSE 日历
- 万年历无 cap 扫描（INDEX §2 禁止）

---

## 5. 切片绑定

| 切片   | 采纳动作                                        |
| ------ | ----------------------------------------------- |
| S07-01 | 新建 `us_trading_calendar.py`（CN 镜像）        |
| S07-02 | ports + `fetch_window` + evidence `window_kind` |
| S07-03 | `MarketStructureBuilder` / US adapter           |
| S07-04 | 固定假日（如 Thanksgiving）负向测               |

## Caveats

- 2030+ US 假日：ponytail 天花板 → R3H-05 或 ADR 延期（对称 `CAL-CN-TAIL`）
