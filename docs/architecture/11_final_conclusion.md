# 最终结论

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 21 章

# 21. 最终结论

v1.6 的核心是：

```text
总设计文档负责架构、边界、表结构、接口和工程规则；
五轴指标细节、产业链细节、市场细节全部外置到独立 spec；
Layer 1 物化完整标准化状态字段；
Layer 2-5 保存各自原始事实和局部特征，不强制套用 Layer 1 的标准化字段；
Agent 负责解释和汇总，不负责生成事实、抓取数据或写库；
Layer 1 前端解释由“静态指标说明 + 每日状态快照 + 程序预警 + 受控 Agent 解释”共同生成；
数据验证拆为质量检查与冲突检查，冲突检查按最新批次、近期窗口、修订范围和全历史审计分层执行；
Layer 3 使用 chain_priority / anchor_priority / source_validation_status，并已从轻量 root node 升级为功能节点 + 链内边 + 跨链边的方案B，避免退化成无层级股票池；
Layer 1 五轴使用 Primary / Validation / FallbackPolicy，降低第三外部源维护成本。
```

这版文档可以直接交给 Claude Code / Codex 作为 v1.6 的系统实现蓝图。
