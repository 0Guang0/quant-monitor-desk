# 环境轴工程规则

## 1. 必须保留的核心规则
- 环境轴只输出宏观状态向量，不输出交易动作。
- E0 净水位 proxy 是混频投影，必须标记 `projection_method` 和 `source_frequency_map`。
- NET_LIQ_PROXY_BN 只用于归因解释，不参与 gate/scoring。
- WRESBAL 是 E0 的状态锚点，但它是周频且有发布滞后。
- ACMTP10 是模型输出且更新滞后，必须有 lag gate。
- CPI、UNRATE、SAHMREALTIME 等月频数据必须 honest lag。

## 2. 数据源角色
- Primary：正式事实源。
- Validation：同源或旁证对账源。
- Fallback Policy：last_good_cache、NaN + stale_reason、manual_review，不再维护第三外部源。

## 3. 禁止项
- 禁止 WM2NS。
- 禁止把信用利差、VIX、SKEW、PCR、Amihud 等跨轴指标塞入环境轴。
- 禁止把 GDPNow 或 Surprise Impulse 回写 Layer1。
- 禁止把 NET_LIQ_PROXY_BN 解释为准备金真实值。

## 4. 用户版删减说明
用户版删除 Stage II 探针细节、端点审计日志、Shadow 详细字段，但不删除：指标身份、边界、滞后、数据源、fallback、禁止项。

## 5. 自检清单
- Layer1 指标数量仍覆盖 E0-E4 主状态。
- M2SL、GDPNow、Surprise、DTS/OCB 等已保留但降级为背景、候选或禁用。
- NET_LIQ_PROXY_BN 双算风险已阻断。
- 月频/周频数据没有伪装成日频实时。
