# 情绪轴工程规则

## 1. 必须保留的核心规则

- 情绪轴输出多分量状态向量，不生成单一总分。
- 周频/月频指标必须 honest lag。
- PCR 必须做分母保护和活性底线，不允许无交易也有情绪。
- AAII 必须保留 bullish / neutral / bearish 三分量；bull-bear spread 只能作为派生。
- RSP-SPY 必须使用 adjusted close / total return；raw close 禁止。
- FINRA margin 固定 Layer2，不得进 Layer1。

## 2. 数据源重构

- 大多数指标保留 Primary + Validation，删除第三外部源。
- Fallback 使用 last_available / stale_reason。
- 任何 source_switched 都必须点灯。

## 3. 禁止项

- 禁止把 PCR 当 VIX/SKEW/VRP 替代。
- 禁止把 RSP-SPY 称为真实广度。
- 禁止把 AAII 做成单一恐惧指数或反指交易信号。
- 禁止社交媒体情绪进入第一版主面板。

## 4. 用户版删减说明

用户版保留“仓位、成交行为、集中度、信念、杠杆燃料”的解释；删除抓取窗口长细节、Shadow 通道明细和 Stage 验收文字。

## 5. 自检清单

- 9 个指标身份含 BlindSpot 完整保留。
- Layer1 5 个、Layer2 1 个、BlindSpot 3 个结构未丢失。
- 真实广度盲区未被伪造成主指标。
- FINRA margin 未错误提升到 Layer1。
