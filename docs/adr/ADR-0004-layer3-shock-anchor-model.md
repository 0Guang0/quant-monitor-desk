# ADR-0004: layer3-shock-anchor-model

- 状态：accepted
- 来源：从 v1.6 设计文档已确认结论拆分生成

## 背景

第三层如果做成普通行业清单或股票池，会导致标的过多、地位混乱、关系分散。

## 决策

Layer 3 定义为全球产业链资金震动锚点层，并执行方案B：chain + anchor + node + edge + cross-chain edge。

## 影响

Layer 3 只保存关系、地位、影响、传导逻辑；行情和证据仍由 Layer 5 提供。

## 详细参考

`docs/modules/layer3_industry_shock_anchor.md`、`specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/`
