# Researcher Guide

## 1. 研究入口

- Layer 1：`docs/modules/layer1_global_regime_panel.md`
- Layer 2：`docs/modules/layer2_cross_asset_sensor.md`
- Layer 3：`docs/modules/layer3_industry_shock_anchor.md`
- Layer 4：`docs/modules/layer4_market_structure.md`
- Layer 5：`docs/modules/layer5_security_evidence.md`
- 回测复盘：`docs/modules/backtest_review_lifecycle.md`

## 2. 数据可信边界

研究结果必须能追溯：

```text
source_used
SourceRoutePlan
quality_flags
rule_version
snapshot lineage
evidence_id
```

## 3. 禁止

研究复盘不能被渲染为买卖建议。若需要导入策略或研究文本，默认 local-only，不写 clean 表；保存为 evidence 需要用户确认。
