# 五轴说明书重构包 v1.1

本包把原始五份说明书重构为更适合前端展示、工程实现和后续维护的文件结构。

## 文件结构

每条轴拆成三份文件：

1. `*_user_guide.md`：给前端、用户、Agent 解释层使用。
2. `*_indicator_spec.yaml`：给 Claude Code / Codex 实现抓取、计算、落库和验证使用。
3. `*_engineering_rules.md`：给工程侧实现质量检查、禁止项、降级策略和自检使用。

额外提供：

- `common/common_axis_rules.md`：五轴共同规则。

## 核心重构原则

1. 不删除指标身份，只把冗余说明拆层。
2. 用户版只保留通俗解释、边界、今日解释所需字段。
3. 工程版保留公式、数据源、fallback、质量规则。
4. `Primary / Shadow / Emergency` 改成 `Primary / Validation / FallbackPolicy`。
5. 删除第三外部数据源强制要求，保留 last_good_cache、stale_reason、quality_flags。
6. 不输出任何动作语义。
7. 不跨轴污染。
8. 不伪造不可得数据。

## 推荐落地方式

- 先把 YAML spec 作为实现蓝图。
- 用户指南作为前端说明卡和 Agent 解释模板来源。
- 工程规则作为 DataQualityValidator、SourceConflictValidator 和 ReconcileJob 的规则来源。



## v1.1 追加说明

- 统一继续使用 `Primary + Validation + FallbackPolicy`。
- 为 SHADOW / BlindSpot / Forbidden 指标补充最小 `plain_language_summary`、`layer` 和 `dest_tag`，防止实现时 schema 校验失败。
- Forbidden 指标只进入 registry 用于防误用，不进入 observation。
