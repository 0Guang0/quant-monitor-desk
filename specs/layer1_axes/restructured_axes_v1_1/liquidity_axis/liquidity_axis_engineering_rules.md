# 流动性轴工程规则

## 1. 必须保留的核心规则
- 本轴只记录狭义市场微观结构交易摩擦。
- 所有主指标都是日线 OHLCV proxy，不是真实订单簿。
- HYG 只能用 OHLCV 计算交易摩擦，不能引入 OAS 或违约风险。
- TLT/IEF 只能用于交易摩擦，不能解释期限利差或宏观利率。
- volume / dollar-volume 口径不合格时，Impact 与 Dry-Up 必须 NaN。

## 2. 数据源重构
- 不再要求 Primary/Shadow/Emergency 三外部源。
- 保留 Primary + Validation + FallbackPolicy。
- Validation 只对账，不接管主值。

## 3. 禁止项
- 禁止 Shadow 接管主指标。
- 禁止把 Roll spread 作为主指标。
- 禁止把期权隐含波动当作价差。
- 禁止把信用利差或宏观流动性混入本轴。

## 4. 用户版删减说明
用户版保留“交易成本、冲击度、可交易性干涸”的含义；删除 roll spread 细节、BlindSpot 技术长说明和端点运行细节。

## 5. 自检清单
- 3 个 Layer1 主探针完整保留。
- 4 个 Shadow 只做诊断，不接管。
- 4 个 BlindSpot 仍登记，未伪造。
- Pastor-Stambaugh 已降为 optional background。
