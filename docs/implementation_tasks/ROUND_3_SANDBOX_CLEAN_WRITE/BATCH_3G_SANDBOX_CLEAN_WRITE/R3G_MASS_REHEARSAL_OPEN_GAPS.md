# R3G 大规模预演 — 已暴露未闭合项与规划归属

> **目的：** 避免「预演已跑过但能力未交付」再次遗漏。  
> **范围：** 2026-06-27 隔离库 mass rehearsal 暴露项；**不**扩大 R3G-03 Trellis 归档范围，仅登记后续谁做、在哪做。  
> **主库：** 以下项均假定仅 `quant_monitor_r3g03_pilot.duckdb` 或 `.audit-sandbox/**`，不写 `quant_monitor.duckdb`。

---

## 0. 参考项目采纳阶梯（2026-06-27 修订）

`参考项目/**` **即将删除**，不得作为运行时代码、不得 `import`、不得 `sys.path` 指向、不得在运行时读其路径。

闭合 G1–G5 等缺口时，按下列**优先级**在 **QMD 自有路径**（`backend/app/**` 等）落地，并满足 `specs/contracts/reference_adoption_guardrails.yaml` 许可与 license gate：

| 阶梯        | 条件                                                                    | 动作                                                                                                               |
| ----------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **L1 直拷** | 逻辑与 QMD 技术栈/定位一致，无禁止语义（交易下单、OpenBB 运行时依赖等） | 将参考源码**复制**到 QMD 目标文件，改包名/路径；任务卡记录 `reference_project.*`                                   |
| **L2 拷改** | 思路可用但 DB 路径、日历、SQL、报告形态与 QMD 不合                      | **先复制再改**：去掉硬编码库表、换 QMD 日历/ConnectionManager/证据 JSON；禁止保留对 `参考项目/**` 的 import 或链接 |
| **L3 自研** | 无合适参考，或 license/语义禁止（AGPL 未决、执行 API 等）               | 在 QMD 内从零实现最小可用子集                                                                                      |

**硬性边界（不因 L1/L2 放宽）：**

- 必须符合当前项目技术栈（DuckDB + WriteManager + registry/route/gate）与「监控台、非券商执行」定位。
- **不得**为省事保留「指向参考项目」的链接、相对路径读参考树、或「详见参考项目 xxx」类运行依赖。
- OpenBB：**架构借鉴可，运行时 provider 拷贝不可**（见 guardrails `openbb_provider_architecture`）。
- EasyXT 日历/缺口检测：**L2 拷改**目标（如 G2 TradingCalendar）— 复制 `smart_data_detector` 相关逻辑后换 QMD 日历源，禁止沿用参考项目内硬编码节假日。

任务卡须写明：参考路径（归档用）、`direct_copy_allowed` / `rewrite_required`、QMD 目标路径。

---

## 1. 状态图例

| 标记           | 含义                                                 |
| -------------- | ---------------------------------------------------- |
| ✅ 已闭合      | 本轮代码/证据已交付                                  |
| ⚠️ 部分        | 门禁/脚本有，真能力未接                              |
| ❌ 未做        | 规划有提及但无实现                                   |
| 📋 仅 research | 只在 `research/r3g03_*` 写过，**未**进官方任务卡阶段 |

---

## 2. 暴露问题 → 规划归属矩阵

| #   | 暴露问题                                                   | 当前 | 原规划写在哪                                                                                       | **应完成阶段**（补登）                                                                        | 备注                                                                                                                                                                                                                                                                                                          |
| --- | ---------------------------------------------------------- | ---- | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| G1  | promote 走 fixture 非 live 真数据                          | ⚠️   | R3G-03 §9.4「live fetch 仅 fred + 授权」；**未写** baostock promote live                           | **R3H-02 / mass-rehearsal 运维切片**                                                          | **`--live-wire` + `live_evidence_bridge` 已接 baostock/fred→pilot**；cninfo/akshare/yahoo 仍 fixture                                                                                                                                                                                                          |
| G2  | 日期窗 = 自然日硬编码，非「最新交易日−120交易日」          | ⚠️   | R3G-01 §4.x TradingCalendar **idea**；`live_pilot_fetch_ports` 有 `recent N trading days` **估算** | **CN：已闭合 @ R3H-03**（`cn_trading_calendar` + Q12）；**US/全球：R3H-05** §5.0.1 **CAL-US** | CN：`calendar_authority=True`；US：`yahoo`/`stooq`/`alpha_vantage` 仍 `calendar_days`                                                                                                                                                                                                                         |
| G3  | 五源同表 `market_bar_clean`，无域语义                      | ❌   | `research/r3g03_mass_rehearsal_gap_analysis.md` P3 defer                                           | **Batch 3H / R3H-05**（正式 clean DDL）                                                       | R3G-03 活卡未列分表为交付项                                                                                                                                                                                                                                                                                   |
| G4  | clean 仅 `close`，OHLCV 丢失                               | ❌   | R3G-01 DH 检查 OHLC；promote staging 仅 `stg_foundation_smoke` 列                                  | **Batch 3H schema**                                                                           | 与 G3 同批                                                                                                                                                                                                                                                                                                    |
| G5  | cninfo 公告压成 bar 形                                     | ❌   | R3G-01 metadata_only；loader 合成行                                                                | **R3H cninfo adapter + 分表**                                                                 | 预演已知偏离                                                                                                                                                                                                                                                                                                  |
| G6  | `append_only` 无 PK，重复 execute 叠行                     | ⚠️   | R3G-03 rollback identify-only                                                                      | **Batch 3V / 3H**（PK 或 upsert 策略）                                                        | 隔离库可删库规避                                                                                                                                                                                                                                                                                              |
| G7  | 合同 cap 10 标的/10 series vs 用户要 50/100                | ❌   | R3G-03 活卡明确 3–10                                                                               | **用户签字 mass-stress approval**（非默认 R3G-03）                                            | 过度工程风险：先打满合同内 10/10                                                                                                                                                                                                                                                                              |
| G8  | 主库污染风险                                               | ✅   | R3G-03 + 本轮 `canonical DB denylist`                                                              | **已闭合 @ 2026-06-27**                                                                       |                                                                                                                                                                                                                                                                                                               |
| G9  | bundle→staging 多行灌数（非 smoke 占位）                   | ✅   | R3G mass rehearsal P0                                                                              | **已闭合 @ 2026-06-27**                                                                       |                                                                                                                                                                                                                                                                                                               |
| G10 | FRED promote「live」仅验授权，未真拉 API 写库              | ✅   | R3E FRED sandbox pilot（**sandbox-only**）                                                         | **已闭合 @ R3H-01（2026-06-28）**                                                             | `official_macro_evidence_v1` SSOT（`official_macro.py` + `fred_port`）；`materialize_fred_evidence_from_live` / `materialize_fred_promote_evidence` 经 normalizer，**无 FRED DH sidecar**；`observation_date` 统一；`test_official_macro_adapters` G10 断言。真网 live 写库仍仅 pilot/`--live-wire`，非主库。 |
| G11 | baostock live 真网抓取                                     | ⚠️   | R3X staged pilot；**非** R3G-03                                                                    | **R3X v2 + `--live-wire`**                                                                    | **真网 34 行已写 pilot**；v2 单次 fetch 仍偏单标的样本                                                                                                                                                                                                                                                        |
| G12 | Layer1 指标未计算                                          | ❌   | Round3 Modeling Layers 018+                                                                        | **Round4 前 / Layer 任务**                                                                    | 预演不承诺                                                                                                                                                                                                                                                                                                    |
| G13 | akshare/yahoo validation 写 clean                          | ⚠️   | registry validation_only；用户 2026-06-27 授权隔离库                                               | **mass-rehearsal 运维**（已允许 pilot）                                                       | 语义偏离 registry                                                                                                                                                                                                                                                                                             |
| G14 | live 证据缺 DH 门禁 sidecar（closeout/validation_summary） | ⚠️   | 接线暴露 @ 2026-06-27                                                                              | **FRED：已闭合 @ R3H-01**；**baostock/pilot：R3H-03 / R3H-05**                                | **FRED 官方宏观路径**：promote 物化不再写 DH sidecar（R3H-01 audit PASS）。**未闭合**：`live_evidence_bridge._write_sandbox_rehearsal_gate_sidecars` 仍在 **baostock** `--live-wire` 物化路径（pilot 专用）；全源 DH 契约与取消 bridge sidecar 归属 R3H-03/05。                                               |
| G15 | staged v2 manifest 双路径致 baostock 重复行                | ✅   | 接线暴露 @ 2026-06-27                                                                              | **已闭合**（桥接去重）                                                                        | promote 写库前须 dedupe instrument+date                                                                                                                                                                                                                                                                       |
| G16 | cninfo/akshare/yahoo 未接 `--live-wire`                    | ❌   | 腿 B cninfo re-defer                                                                               | **R3H cninfo + R3X akshare/yahoo**                                                            | live-wire 五源中后三源仍 fixture                                                                                                                                                                                                                                                                              |
| G17 | baostock live promote DH WARNING（日历缺口）               | ⚠️   | `market_bar_p0`                                                                                    | **CN：已闭合 @ R3H-03**（Q12）；**US 日历** → R3H-05 **CAL-US**                               | CN DH 可走 `calendar_authority`；pilot `--live-wire` 仍可有 sidecar → R3H-05 **LIVE-PROD**                                                                                                                                                                                                                    |

---

## 3. R3G-03 归档边界（避免过度工程）

**R3G-03 已完成（`23429ad8`）：** promote CLI、四门链、隔离库 pilot 脚本、fixture 预演、主库 denylist。

**不属于 R3G-03 但预演已暴露、需另列的：**

- G1 G2 G3 G4 G5 G6 G11 → **Batch 3H / R3X / 运维切片**，不要回流开 R3G-04 Trellis 全量 Plan。
- G10 → **已闭合 @ R3H-01（2026-06-28）**；G14（FRED 段）同批闭合，baostock/pilot sidecar 仍开放。
- G7 → 用户单次 stress approval，不改合同默认值。

---

## 4. 与 `research/r3g03_*` 的关系

| 文件                                            | 用途                                      |
| ----------------------------------------------- | ----------------------------------------- |
| `research/r3g03_mass_rehearsal_gap_analysis.md` | 预演差距分析草稿                          |
| `research/r3g03_mass_rehearsal_report.md`       | 执行证据摘要                              |
| **本文**                                        | **官方索引**：暴露项 → 路线图阶段，防遗漏 |

后续预演轮次：**先更新本文 §2 状态列**，再改代码。

---

## 5. 建议执行顺序（轻量，非 Trellis）

1. 运维切片：交易日窗用脚本常量 / `recent 120 trading days` 标签（G2）
2. **`--live-wire --execute`**：baostock/fred 真网→pilot（G1/G11 部分闭合；**G10 证据契约 @ R3H-01 已闭合**）
3. Batch 3H：域分表 + OHLCV（G3 G4 G5）+ **baostock pilot DH sidecar 替代**（G14 余量，R3H-03/05）
4. cninfo/akshare/yahoo live 接线（G16）
5. 可选 stress：用户签字超 cap（G7）

---

## 6. 接线结论（勿写入 `quant_monitor.duckdb`）

**数据主库 `quant_monitor.duckdb`：** 接线暴露的问题**不得**回补进主库；仅练习库 `.audit-sandbox` + `quant_monitor_r3g03_pilot.duckdb`。

**规划主索引（本文）：** 接线新项 **G14–G17** 与 G1/G10/G11 状态更新**必须**写回本文 §2；G10 + G14（FRED）**已同步 @ R3H-01 归档（2026-06-28）**；**G2/G17（CN）已同步 @ R3H-03 归档（2026-06-28）**；G1/G11 等仍 @ 2026-06-27 基线。

**运行入口：** `uv run python scripts/r3g03_isolated_pilot_dry_run.py --live-wire --execute [--refresh-live]`

**运维 vs 产品日历（2026-06-28 补登）：** 上列 pilot 脚本可用**自然日窗**（非产品级交易日 SSOT）；产品 adapter 路径以 `fetch_ports/*` + `cn_trading_calendar`（CN）为准；US 日历 → R3H-05 **CAL-US** / **PILOT-OPS-CALENDAR** limitation。见 `R3H_REFERENCE_ADOPTION_INDEX.md` §3。
