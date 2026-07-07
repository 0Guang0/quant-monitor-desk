# Agent 模块

> 权威定位：本文件是 Agent 模块的实现级文档。Agent 只负责解释、摘要、结构化报告与问答，不负责抓数据、不直接写库、不自由上网、不输出交易动作。
> 来源继承：由 `quant_monitor_design_document_v1_6.md` 第 14 章拆分而来，并在本轮扩展为可交给 Claude Code / Codex 实现的模块规格。

---

# 1. 模块目标

Agent 模块负责把结构化数据转换成可读解释，但不能越权成为交易决策器。

Agent 可以做：

```text
新闻摘要
公告分类
事件提取
异动解释
日报生成
周报生成
策略复盘说明
自然语言问答
五层证据链解释
数据质量异常解释
```

Agent 不可以做：

```text
不抓取原始数据。
不直接写 DuckDB clean table。
不自由执行 SQL。
不自由上网。
不输出买、卖、加仓、减仓、入场、出场等动作语义。
不把自身推理当成事实数据。
```

---

# 2. Agent 清单

| agent_id                      | 中文名             | 主要职责                 | 是否可写库                                  |
| ----------------------------- | ------------------ | ------------------------ | ------------------------------------------- |
| `daily_report_agent`          | 日报 Agent         | 汇总五层状态、异常、事件 | 只能写 report 表，且通过 WriteManager       |
| `news_event_agent`            | 新闻事件 Agent     | 新闻摘要、事件抽取       | 只能写 event staging                        |
| `announcement_agent`          | 公告 Agent         | 公告分类、公告摘要       | 只能写 event staging                        |
| `layer1_interpretation_agent` | 五轴解释 Agent     | 把五轴状态改写成通俗解释 | 只能写 axis_interpretation_snapshot staging |
| `cross_layer_explain_agent`   | 五层解释 Agent     | 串联 Layer 1-5 证据链    | 只读，输出解释                              |
| `data_quality_explain_agent`  | 数据质量解释 Agent | 解释数据异常和冲突       | 只读或写 report staging                     |
| `strategy_review_agent`       | 策略复盘 Agent     | 策略复盘说明             | 只读或写 report staging                     |

---

# 3. 统一工具边界

Agent 只能调用受控工具：

```text
get_layer1_snapshot
get_layer2_snapshot
get_layer3_chain_snapshot
get_layer4_market_snapshot
get_layer5_security_evidence
get_data_quality_summary
get_source_conflict_summary
get_report_context
```

禁止工具：

```text
execute_arbitrary_sql
write_duckdb_directly
fetch_web_directly
modify_source_registry_directly
modify_clean_table_directly
```

---

# 4. 输入输出结构

所有 Agent 输入输出必须是 JSON Schema 可校验对象。

## 4.1 cross_layer_explain_agent 输入

```json
{
  "target_id": "NVDA.US",
  "target_type": "instrument",
  "trade_date": "2026-06-15",
  "include_layers": ["layer1", "layer2", "layer3", "layer4", "layer5"],
  "language": "zh-CN"
}
```

## 4.2 cross_layer_explain_agent 输出

```json
{
  "summary_sentence": "string",
  "layer_explanations": [
    {
      "layer": "Layer 3",
      "facts_used": ["string"],
      "interpretation": "string",
      "boundary_reminder": "string"
    }
  ],
  "missing_evidence": ["string"],
  "quality_warnings": ["string"],
  "no_action_semantics_passed": true,
  "needs_human_review": false
}
```

---

# 5. Structured Outputs 规则

Agent 输出必须尽量使用结构化输出，避免自由文本丢字段。

要求：

```text
所有 Agent 输出必须有 schema_version。
所有 enum 字段必须由 schema 限定。
所有解释必须引用 facts_used。
所有输出必须经过 no_action_semantics 检查。
输出失败时不写 report clean table，只写 agent_error_log。
```

---

# 6. No Action Semantics Guard

禁止词包括但不限于：

```text
买入
卖出
加仓
减仓
满仓
清仓
入场
出场
抄底
逃顶
必须买
必须卖
```

如果 Agent 生成文本包含禁词：

```text
1. 标记 no_action_semantics_passed=false
2. 不写入 clean report
3. 触发二次改写
4. 二次失败进入 needs_human_review=true
```

---

# 7. Agent 写入规则

Agent 不直接写库。允许写入的内容必须走：

```text
agent_output_staging
    ↓
AgentOutputValidator
    ↓
NoActionSemanticGuard
    ↓
WriteManager
    ↓
report / interpretation / event clean table
```

---

# 8. 表结构

## 8.1 agent_run_log

```sql
CREATE TABLE IF NOT EXISTS agent_run_log (
    run_id              VARCHAR PRIMARY KEY,
    agent_id            VARCHAR,
    task_type           VARCHAR,
    input_hash          VARCHAR,
    output_hash         VARCHAR,
    status              VARCHAR,
    started_at          TIMESTAMP,
    finished_at         TIMESTAMP,
    error_code          VARCHAR,
    error_message       TEXT
);
```

## 8.2 agent_output_staging

```sql
CREATE TABLE IF NOT EXISTS agent_output_staging (
    output_id           VARCHAR PRIMARY KEY,
    run_id              VARCHAR,
    agent_id            VARCHAR,
    target_id           VARCHAR,
    target_type         VARCHAR,
    output_json         JSON,
    no_action_passed    BOOLEAN,
    needs_human_review  BOOLEAN,
    created_at          TIMESTAMP
);
```

---

# 9. Agent 与报告模块的关系

日报、周报、数据质量报告由 `notification_and_reports.md` 负责定义结构。Agent 只负责生成其中的解释字段，报告模块负责排版、归档、发送和状态追踪。

---

# 10. API / Tool 契约

```text
POST /api/agent/cross-layer-explain
POST /api/agent/layer1-interpret
POST /api/agent/daily-report-context
GET  /api/agent/runs/{run_id}
GET  /api/agent/runs
```

Agent tool 输入输出详见：

```text
specs/contracts/agent_contract.yaml
docs/api/agent_tool_contracts.md
```

---

# 11. 验收测试

必须通过：

```text
Agent 不能调用任意 SQL。
Agent 输出必须符合 JSON Schema。
Agent 输出必须包含 facts_used。
Agent 输出不能包含动作语义禁词。
Agent 输出不能直接写 clean table。
缺少结构化事实时必须输出 missing_evidence。
数据质量异常时必须输出 quality_warnings。
Agent 失败必须写 agent_run_log。
```

## 用户决策补充：Agent 来源固定

落实 D-12：Agent 只允许读取固定 source adapter、结构化数据库事实、file_registry 中已登记文档和用户手动导入文本。禁止 Agent 自由联网搜索新闻或临时浏览未知网页。Agent 输出必须绑定 `facts_used_json` / `evidence_ids`，不得把 LLM 生成内容当事实源。
