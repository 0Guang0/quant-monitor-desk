# ADR-010：Layer1 五轴 clean read

**状态：** 已接受（计划冻结）  
**日期：** 2026-07-02

## 背景

R3-DCP-05 已关闭增量 clean 写入。DCP-06 须用 **clean 表输入**（非 `staged_fixture_only`）证明 G12 五轴 PASS。Layer1 接入桥（018A/Batch 2.5）对 `ENV-E1-DGS10` 仍默认 staged 微抓取。

## 决策

1. 新增 **QMD 自有 clean 读路径**（`Layer1CleanObservationReader` 或 `backend/app/layer1_axes/` 中等价物），从以下表加载 P0 锚点观测：

- `axis_observation`：宏观/COT 序列（fred、cftc_cot 等 domain，见 ADR-009）
- `security_bar_1d`：由 bar 衍生的流动性代理（alpha_vantage 规范 domain）

2. **每轴 P0 锚点**（每轴至少一条 pytest 竖切）：

| axis_id       | indicator_id                 | clean_table      | 数据源（DCP-05） | 说明                                          |
| ------------- | ---------------------------- | ---------------- | ---------------- | --------------------------------------------- |
| ENVIRONMENT   | ENV-E1-DGS10                 | axis_observation | fred             | 序列 DGS10                                    |
| CREDIT_STRESS | CRD.CS1.BAA10Y               | axis_observation | fred             | 序列 BAA10Y                                   |
| RISK_APPETITE | RA.R1.VIXCLS_30D_IMPLIED_VOL | axis_observation | fred             | 序列 VIXCLS                                   |
| LIQUIDITY     | LIQ.B-I1.AMIHUD_ILLIQ        | security_bar_1d  | alpha_vantage    | SPY 符号；相对 tiingo 规范主源为 **ponytail** |
| SENTIMENT     | SEN-S1-COT_LF_NET            | axis_observation | cftc_cot         | `cot_positioning` domain                      |

1. **流动性 ponytail：** 规范主源为 `tiingo_eod_`\*（非 DCP-05 十一源）。DCP-06 用 `security_bar_1d` 上 Amihud 作有界代理。升级路径：注册 tiingo/FMP port + 校验（Batch 6 或更晚 wave）。
2. watermark/seed 对齐 DCP-05 e2e replay 模式（`tmp_path` 隔离库）。
3. **ACC-LAYER-E2E-LIVE-001：** DCP-06 关闭 L1 五轴 + 非 fixture 层 smoke；L3–L5 全链 **阶段外置** 的具体情况待定，请用户裁决

## 曾考虑的替代方案

- **流动性/情绪仅用 staged fixture：** **拒绝** — 违反 §3.5.1「非 staged fixture」PASS 语义。
- **Layer1 接入内做 live fetch：** **待做** — 数据平面
- **实现 YAML 全量指标：** **待做**

## 后果

- Execute 扩展 `layer1_axes` 读/算路径；对 `Layer1ObservationIngestionService` 影响 LOW（并行路径，不替换 staged 桥）。
- K1 whitelist `readiness` 可将 P0 行从 `sandbox_candidate` → `clean_replay_proven`（非 `production-live ready`）。
- `B2.5-O-05` 仍开放；DCP-06 **不得**宣称 FRED live primary 已关账。
