# ADR-0003: layer1-standardization-only

- 状态：accepted
- 来源：从 v1.6 设计文档已确认结论拆分生成

## 背景

完整标准化字段 raw_value/z_score/percentile/state_bucket 等非常重，如果扩展到所有层会导致字段爆炸。

## 决策

第一版只在 Layer 1 物化完整标准化字段；Layer 2/4/5 不默认物化完整套件。

## 影响

Layer 1 能展示完整水位和解释；其他层保留基础事实、局部特征和快照。

## 详细参考

`docs/modules/layer1_global_regime_panel.md`、`docs/architecture/00_project_overview.md`
