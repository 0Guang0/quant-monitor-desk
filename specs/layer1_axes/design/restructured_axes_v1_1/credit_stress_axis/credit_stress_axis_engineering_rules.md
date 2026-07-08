# 信用压力轴工程规则

## 1. 必须保留的核心规则

- 信用压力轴只输出信用/融资压力状态，不输出动作语义。
- Layer1 只输出两类白盒得分：Corporate Solvency Score 与 Systemic Funding Friction Score。
- 融合规则使用 max/门控，禁止线性叠加，防止同一冲击重复计入。
- CS2 改名为“短端无担保信用融资楔子”，保留 CP-TBill proxy 本质说明。

## 2. 禁止项

- 禁止用 BAA 绝对收益率替代 BAA10Y。
- 禁止用 SOFR 当无担保互信基准。
- 禁止用 DCPF3M-DCPF1M 接管 CS3 主指标。
- 禁止用其他序列伪造 OFR repo 缺失 rate / volume。
- 禁止把 VIX/SKEW/PCR/Amihud 等跨轴指标混入信用压力轴。

## 3. 数据源与 fallback

- 大多数 FRED 指标保留 Primary + Validation；第三外部数据源删除。
- Fallback 使用 last_good_cache / NaN + stale_reason。
- OFR repo 缺失时不得接管，只能 NaN + stale_reason。

## 4. 用户版删减说明

用户版删除 Stage II runtime_audit 长字段、endpoint 五件套细节和 Shadow 长路由，但保留：指标身份、公式、边界、禁止替代、滞后与质量规则。

## 5. 自检清单

- Layer1 8 条指标完整保留。
- Layer2 2 条指标完整保留。
- BlindSpot 3 条登记保留。
- CS2 语义已修正，没有把 CP-TBill proxy 误写成严格同业拆借。
- OFR 缺失禁止伪造。
