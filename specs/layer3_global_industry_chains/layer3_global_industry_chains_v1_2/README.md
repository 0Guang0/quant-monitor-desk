# 第三层全球产业链资金震动锚点文件包 v1.2

本文件包用于替换/升级设计文档中的 Layer 3 产业链配置。它把第三层从“行业清单/股票池”改成“全球产业链资金震动锚点层”。

## 使用方式

1. 后端读取 `layer3_global_industry_chain_registry.yaml` 建立产业链和锚点基础表。
2. 后端读取 `layer3_anchor_registry.json` 快速生成前端卡片、搜索索引和 Agent 输入。
3. 前端展示时使用 `status_explanation_cn` 和 `impact_explanation_cn`，直接说明“这个标的是什么地位、会影响什么”。
4. Layer 5 负责提供行情、财务、公告、新闻；Layer 3 不重复保存大表。

## 关键原则

- 不做全量股票池。
- 每个锚点必须有地位和作用。
- 私有公司只能作为事件锚。
- 商品/期货/指数作为价格锚。
- 区域标的作为映射，不与全球绝对锚同级。


## v1.2 更新说明

- 将 chain 层级字段统一为 `chain_priority`。
- 将 anchor 层级字段统一为 `anchor_priority`，避免所有锚点被误判为同等 P0。
- 每条 chain 至少生成一个 root node，确保可初始化 `industry_chain_node`。
- 新增 `source_validation_status`，用于区分已验证来源、待补来源、事件锚和价格锚。
- 补充 `openai_2026_funding` 来源键。


## v1.2 更新说明

本版本执行方案B：在每条 chain 的 root node 基础上补充功能节点、链内边和AI主链跨链传导边。同时优先补齐 P0 锚点来源，P0 锚点不得缺少 source_keys。
