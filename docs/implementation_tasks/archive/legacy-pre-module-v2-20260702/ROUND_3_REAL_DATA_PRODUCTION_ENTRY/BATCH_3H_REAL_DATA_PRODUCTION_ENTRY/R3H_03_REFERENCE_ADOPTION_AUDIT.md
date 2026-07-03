# R3H-03 参考项目采纳追溯（CLOSED @ 2026-06-28）

> **权威规则：** `specs/contracts/reference_adoption_guardrails.yaml` · 活卡 `R3H_03_CN_MARKET_ADAPTERS.md` §8  
> **Trellis 归档：** `.trellis/tasks/archive/2026-06/06-28-round3h-r3h03-cn-market/`（A3 参考项目 0 runtime import · A5 audit PASS）  
> **R3H-05：** 交叉项 **REF-ADOPT-GATE**、**STAGED-PILOT-SSOT**、**CAL-US**（US 不在本卡）须引用本文。

## 1. 批次级结论

| 项                                               | 结论                                                                                                           |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| runtime `参考项目/**` import                     | **PASS** — `backend/` 0 命中；`test_reference_adoption_guardrails.py` 绿                                       |
| EasyXT `tdx_provider` / `data_integrity_checker` | **L2 已完成** — `tdx_pytdx_port` / `mootdx_port` / `cn_market` DH profiles                                     |
| EasyXT `smart_data_detector` TradingCalendar     | **L2 已完成（CN）** — `cn_trading_calendar.py` + `calendar_authority=True` @ Grill-me Q12                      |
| **US 交易日历**                                  | **本卡不做** → R3H-05 **CAL-US**                                                                               |
| `staged_pilot_fetch_ports`                       | **L2 部分迁出** — `baostock_port` / `cninfo_port`；staged 仍保留 3G rehearsal → **STAGED-PILOT-SSOT** 延后收敛 |

## 2. 十源采纳矩阵

| source_id      | adoption_ladder         | 参考路径（只读/归档）                                      | QMD 落点                           | direct_copy | Trellis 证据                                |
| -------------- | ----------------------- | ---------------------------------------------------------- | ---------------------------------- | ----------- | ------------------------------------------- |
| `baostock`     | **L2** copy_and_rewrite | `ops/staged_pilot_fetch_ports.py` · `adapters/baostock.py` | `fetch_ports/baostock_port.py`     | false       | A5 audit · `execute-evidence/9.8-full*.txt` |
| `cninfo`       | **L2** copy_and_rewrite | staged pilot + `adapters/cninfo.py`                        | `fetch_ports/cninfo_port.py`       | false       | 同上                                        |
| `akshare`      | **L2** copy_and_rewrite | `adapters/akshare.py` validation skeleton                  | `fetch_ports/akshare_port.py`      | false       | validation_only 永久                        |
| `tdx_pytdx`    | **L2** copy_and_rewrite | EasyXT `tdx_provider.py`（R3FR-03）                        | `fetch_ports/tdx_pytdx_port.py`    | false       | MIT attribution in port header              |
| `mootdx`       | **L2** extend           | `tdx_pytdx_port` + EasyXT lifecycle 思路                   | `fetch_ports/mootdx_port.py`       | false       | 独立 source_id；无 silent fallback          |
| `qmt_xtdata`   | **L2** copy_and_rewrite | `adapters/qmt_xtdata.py`                                   | `fetch_ports/qmt_xtdata_port.py`   | false       | license_gate default DISABLED               |
| `qmt_xqshare`  | **L2** copy_and_rewrite | `qmt_xtdata` auth-gated 模式                               | `fetch_ports/qmt_xqshare_port.py`  | false       | Grill-me Q8 实现                            |
| `ths_ifind`    | **L2** copy_and_rewrite | `qmt_xtdata` auth-gated 边界                               | `fetch_ports/ths_ifind_port.py`    | false       | authorization-disabled 负路径               |
| `eastmoney`    | **L3** greenfield       | 无 EasyXT 1:1                                              | `fetch_ports/eastmoney_port.py`    | false       | mock/replay + conflict_evidence             |
| `sina_finance` | **L3** greenfield       | 无 EasyXT 1:1                                              | `fetch_ports/sina_finance_port.py` | false       | mock/replay + conflict_evidence             |

## 3. 延后 / 不在本卡重做

| 项                     | 处置                                           | 登记位置                                 |
| ---------------------- | ---------------------------------------------- | ---------------------------------------- |
| **STAGED-PILOT-SSOT**  | staged 薄封装/废弃 → **post-R3H-05 debt-lite** | `R3H_REFERENCE_ADOPTION_INDEX.md` §3     |
| **CAL-US**             | 美股日历                                       | R3H-05 三选一（见 `R3H_05_*.md` §3.1.1） |
| **PILOT-OPS-CALENDAR** | 3G pilot 脚本自然日窗                          | 与产品路径分开 limitation                |

## 4. R3H-05 审计引用

- 十源矩阵 + port 头注释 ladder 一致
- CN G2/G17 **CLOSED**；US 日历 **不得**在本卡 silent PASS
- `test_r3h03_*` + `test_reference_adoption_guardrails` 绿
