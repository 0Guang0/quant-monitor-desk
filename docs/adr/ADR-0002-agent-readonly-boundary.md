# ADR-0002: agent-readonly-boundary

- 状态：accepted
- 来源：从 v1.6 设计文档已确认结论拆分生成

## 背景

系统引入 Agent 解释、摘要、日报和问答，但不能让 Agent 成为事实源或写入者。

## 决策

Agent 只能调用受控只读查询工具，不自由上网，不直接写 DuckDB，不输出买卖/加减仓/入场/出场等动作语义。

## 影响

Agent 的输出用于解释和汇总；写入和预警等级由程序/规则层控制。

## 详细参考

`docs/modules/agent_module.md`、`docs/modules/layer1_global_regime_panel.md`
