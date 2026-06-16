# 自检与审计清单

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 19 章

# 19. 自检与审计清单

交付前必须检查：

| 检查项 | 结果要求 |
|---|---|
| 本地文件系统定位 | 已明确为 Raw Store / File Lake / Audit Store |
| DuckDB 定位 | 本地分析库，单写多读 |
| Parquet 定位 | 可选但推荐的历史归档格式 |
| Layer 1 五轴 | 只写框架，指标细节外置 |
| Layer 1 标准化字段 | 仅第一版物化于 Layer 1 |
| Layer 2 | 跨资产传感器，保存 OHLCV 等行情字段，不默认全量 z-score |
| Layer 3 | 全球产业链资金震动锚点层，细节外置 |
| Layer 4 | 市场结构层，各市场建立自己的规则 |
| Layer 5 | 个股 / 合约证据层，保存行情、财务、资金、事件、暴露，不套用第一层全字段 |
| Agent | 只读、只解释、不直接写库、不自由上网 |
| 数据源 | Yahoo、同花顺、腾讯、百度已纳入辅助源定位 |
| QMT | 通过 Adapter 调用，不在业务层写死 API |
| 写入 | staging → validation → WriteManager |
| 传统技术指标 | 只作为 baseline/reference，不是核心模型 |
| Layer 3 展开视图 | 可以展示映射标的行情，但行情来自 Layer 5，不重复保存历史大表 |
| Layer 4 市场详情 | 美股/A股/港股/期货/期权等都有各自指数、板块、宽度和规则 |
| 数据同步 | FullLoad / Incremental / Backfill / RevisionAudit / Reconcile 已拆分 |
| 多源冲突 | 主源优先 + 阈值校验 + 重抓 + 必要时人工确认，口径不同字段分源保存 |
| Layer 1 前端解释 | axis_indicator_profile 与 axis_interpretation_snapshot 已加入 Layer 1 对应位置 |
| 预警职责 | 程序负责预警标签，Agent 只负责受控自然语言解释 |
| 质量检查 | DataQualityValidator 负责单源/单表自身质量 |
| 冲突检查 | SourceConflictValidator / ReconcileJob 负责多源打架与重抓 |
| 冲突检查范围 | 日常最新批次 + 近期窗口，修订查受影响历史，全历史只在特定场景触发 |
| 运维文件 | 新增 docs/ops_and_performance_v1_2.md |

---
