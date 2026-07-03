# R3-DCP-08 参考项目采纳调研（L1/L2/L3）

> **任务：** `.trellis/tasks/07-02-wave4-r3-dcp-08-layer4/`  
> **日期：** 2026-07-02  
> **方式：** 检索 `参考项目/**` + QMD 仓内 trace（仓内不进 L 梯）  
> **SSOT：** `specs/contracts/reference_adoption_guardrails.yaml`

---

## 0. 铁律

1. **L1/L2/L3 只评 `参考项目/**`**；`backend/app/layer4_markets/\*\*` 记「仓内承接」。
2. 禁止 runtime import / sys.path / 软链参考树。
3. OpenBB = **architecture_only**（AGPL）。

---

## 1. 三等级总表（仅参考项目）

| 参考路径                                    | 等级                       | 采纳 / 禁止                                  | QMD 目标                                   |
| ------------------------------------------- | -------------------------- | -------------------------------------------- | ------------------------------------------ |
| `参考项目/OpenBB/.../fetcher.py` L36–85     | **architecture_only → L3** | transform_query / extract / transform 三阶段 | clean read 行为对齐；**不拷贝 Fetcher 类** |
| `参考项目/digital-oracle/.../bis.py` L54–66 | **L2 概念**                | API 窗参数来自 watermark                     | 已 DCP-05 承接；L4 不重复                  |
| Layer4 breadth / market calendar 专用实现   | **L3 greenfield**          | 参考树无 market_breadth / advancers 直拷点   | `CleanBreadthAggregator` 仓内最小实现      |
| EasyXT unified_data_interface               | **forbidden**              | silent fallback                              | 负向：L4 不得换源补 breadth                |

**调研结论：** `参考项目/**` 内 **无** Layer4 market breadth / calendar 快照的可安全 L1 直拷模块；本票 breadth 聚合与 clean adapter 走 **L3 greenfield**，Fetch 链行为 **L3 对齐** OpenBB 三阶段（已在 DCP-05 验证）。

---

## 2. 仓内承接（非参考 L 梯）

| 组件                  | 路径                                                   | DCP-08 用法                         |
| --------------------- | ------------------------------------------------------ | ----------------------------------- |
| US 日历 SSOT          | `ops/data_health_profiles/us_trading_calendar.py`      | US_EQ 非交易日拒绝（R3H-07 已接线） |
| Staged builder        | `layer4_markets/market_structure.py`                   | 保留 022 AC；新增 clean 分支        |
| Tier A bar clean      | `alpha_vantage_incremental_run.py` · `security_bar_1d` | US_EQ breadth 输入                  |
| Layer1 clean e2e 模式 | `tests/layer1_clean_e2e_support.py`                    | 复制 bootstrap 模式到 L4 support    |
| Registry overlay      | `enabled_source_registry` + `sync_mootdx_incremental`  | S08-REG-MOOTDX 对齐 dry-run         |

---

## 3. Execute RED 前门禁

实读 `参考项目/OpenBB/.../fetcher.py`（若存在）并落盘 `research/execute-reference-read-evidence-s08.md`；Layer4 实现以仓内 `market_structure.py` + `layer4_market_structure.md` 为权威。

---

## 4. 采纳决策摘要

| 能力                         | 参考等级          | 决策                                                             |
| ---------------------------- | ----------------- | ---------------------------------------------------------------- |
| Market breadth 聚合          | **L3**            | 从 `security_bar_1d` 按 pct_change 符号计数；ponytail 最小字段集 |
| US calendar                  | 仓内 R3H-07       | 复用 `is_trading_day`；不新造假日表                              |
| CN mootdx/eastmoney registry | 仓内 DCP-05       | registry proposed delta + runtime dry-run 对齐                   |
| OpenBB Fetcher               | architecture_only | 不引入类型；clean read 链对齐                                    |
