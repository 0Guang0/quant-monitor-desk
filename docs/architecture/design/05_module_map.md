# 五层分析建模框架与模块地图

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 5 章

# 5. 五层分析建模框架

## 5.1 总体定义

```text
Layer 1：Global Regime State Panel
全球底层状态面板：环境、信用压力、风险偏好、流动性、情绪

Layer 2：Cross-Asset Sensor Layer
跨资产传感器层：美元、黄金、原油、铜、VIX、美债、商品、航运等

Layer 3：Global Industry Chain Shock-Anchor Layer
全球产业链资金震动锚点层：AI Capex、AI 芯片、HBM、半导体制造瓶颈、AI 基础设施、电力冷却、能源、关键矿产、航运、军工、GLP-1 等资金震动锚点。它不是普通行业/股票清单，而是追踪能够引发产业链资金重定价的核心锚点。

Layer 4：Market Structure Layer
市场结构层：美股、A股、港股、商品、外汇、期货、期权等各自市场规则

Layer 5：Security Evidence Layer
个股 / 合约证据层：个股、ETF、期货、期权、商品合约的可验证证据链
```

## 5.2 不做单向迷信

系统支持两种方向：

```text
Top-down：Layer 1 → Layer 2 → Layer 3 → Layer 4 → Layer 5
Bottom-up：Layer 5 异动 → Layer 4 扩散 → Layer 3 主题验证 → Layer 2 跨资产确认 → Layer 1 状态解释
```

不能只做自上而下。真实市场中，个股、产业链或某个局部市场常常先动，之后宏观解释才补上。

---

---

## 5.3 模块化实现文件补充索引

当前拆分版继续将实现细节落入 `docs/modules/`。除五层分析模块外，核心工程模块包括：

```text
data_sources
data_sync_orchestrator
data_validation_and_conflict
write_manager
duckdb_and_parquet
fastapi_backend
frontend_dashboard
agent_module
ops_and_performance
notification_and_reports
```

其中 `notification_and_reports` 负责日报、周报、数据质量报告、盘中提醒和通知发送；Agent 只负责生成结构化解释，不负责报告归档与通知状态追踪。
