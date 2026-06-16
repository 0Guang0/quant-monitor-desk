# 风险偏好轴工程规则

## 1. 必须保留的核心规则
- 输出状态向量，不生成单一恐惧指数。
- R1 只允许 option-derived 隐含波动水位。
- R2 SKEW 若无合规稳定通道，输出 NaN + NO_ACCEPTED_CHANNEL。
- R3 必须在方差尺度计算，禁止 VIX - realized volatility。
- R4 若历史不足，输出 NaN + INSUFFICIENT_HISTORY，不隐式缩窗。
- R5 是 Layer2 慢变量，不回写 Layer1。

## 2. 数据源角色
- VIX/VXV/VRP/R4 以 FRED 作为主事实源或主输入。
- SKEW 不强制抓取；从 P0 调整为 P1 optional/source-gated。
- VVIX 只做旁证，不接管 SKEW。

## 3. 禁止项
- 禁止把 VIX 叫成底层“恐慌总分”。
- 禁止 PCR 进入风险偏好轴。
- 禁止信用利差、融资压力、订单簿摩擦进入风险偏好轴。
- 禁止动作语义。

## 4. 用户版删减说明
用户版保留“保险费、尾部保护费、VRP、股债对冲锚”的含义；删除 lint 规则编号、探针五件套、stitching 细节和 endpoint 长说明。

## 5. 自检清单
- 8 个指标身份完整保留。
- SKEW 降为 optional/source-gated，没有伪造通道。
- VRP 量纲错误已经封杀。
- R4 历史不足规则保留。
