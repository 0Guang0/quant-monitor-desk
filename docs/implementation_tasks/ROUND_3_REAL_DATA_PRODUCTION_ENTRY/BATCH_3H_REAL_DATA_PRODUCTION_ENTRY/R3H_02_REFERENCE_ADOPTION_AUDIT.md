# R3H-02 参考项目采纳追溯（CLOSED @ 2026-06-28）

> **权威规则：** `specs/contracts/reference_adoption_guardrails.yaml` · 活卡 `R3H_02_MARKET_DATA_ADAPTERS.md` §14  
> **Trellis 归档：** `.trellis/tasks/archive/2026-06/06-28-round3h-r3h02-market-data/`（A3 0 runtime import · A5 audit PASS · `execute-evidence/9.8-full*.txt`）  
> **R3H-05：** 交叉项 **REF-ADOPT-GATE**、**CAL-US** 须引用本文。

## 1. 批次级结论

| 项                           | 结论                                                                                                                  |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| runtime `参考项目/**` import | **PASS** — A3 `rg` 0 命中                                                                                             |
| OpenBB provider runtime 拷贝 | **禁止** — §14 architecture_only                                                                                      |
| JQ2PTrade / EasyXT           | **只读约束**（loader/report/integrity 思路）；**未** runtime import                                                   |
| **US 交易日历 G2**           | **本卡故意不做 L2** — 活卡 §2 否决 EasyXT 完整 TradingCalendar；ponytail `calendar_days` → **延后** R3H-05 **CAL-US** |

## 2. 五源采纳矩阵

| source_id       | adoption_ladder         | 参考路径（只读/归档）                                                       | QMD 落点                            | direct_copy | 说明                                                |
| --------------- | ----------------------- | --------------------------------------------------------------------------- | ----------------------------------- | ----------- | --------------------------------------------------- |
| `alpha_vantage` | **L3** greenfield       | 无 1:1；mock 模式对齐 `coingecko_port` / `fred_port` 证据形状               | `fetch_ports/alpha_vantage_port.py` | false       | mock-first；live API key 路径 defer                 |
| `stooq`         | **L3** greenfield       | 无 1:1                                                                      | `fetch_ports/stooq_port.py`         | false       | validation-only；`market_data_evidence_v1`          |
| `yahoo_finance` | **L2** copy_and_rewrite | 3G fixture 语义 → replay `tests/fixtures/replay/market_data/yahoo_finance/` | `fetch_ports/yahoo_finance_port.py` | false       | **非** OpenBB 拷贝；validation_only 永久            |
| `deribit`       | **L3** greenfield       | 无 1:1；禁止交易/账户 API                                                   | `fetch_ports/deribit_port.py`       | false       | mock surface only                                   |
| `coingecko`     | **L3** greenfield       | 无 1:1                                                                      | `fetch_ports/coingecko_port.py`     | false       | 内部 mock 模式样板（R3H-04 kalshi/polymarket 参照） |

**标签纠正（2026-06-28 文档债闭合）：** `alpha_vantage`/`stooq`/`deribit`/`coingecko` 原标「L2」过宽 → **L3**；`yahoo_finance` 保留 **L2**（自 3G replay 迁出）。

## 3. 延后 / 不在本卡重做

| 项                                                        | 处置                              | 登记位置                                          |
| --------------------------------------------------------- | --------------------------------- | ------------------------------------------------- |
| **US equity 交易日历**（EasyXT `smart_data_detector` L2） | **延后** — 本卡 ponytail 自然日窗 | R3H-05 **CAL-US** · 路线图 §5.0.1                 |
| 五源 live 产品化                                          | **延后**                          | R3H-05 **LIVE-PROD**                              |
| `domain_roles` 与 `validation_only` YAML 语义统一         | **债务** — route 已 fail-closed   | R3H-05 审计注记；可选 Round4 前 registry 协调切片 |

## 4. R3H-05 审计引用

- 五源矩阵 + 上表 ladder 一致
- **CAL-US** 必须写明：US bar 域仍 `window_kind: calendar_days` → WARN+ADR 或 closure gate
- crypto 源（deribit/coingecko）**不适用** NYSE 日历
