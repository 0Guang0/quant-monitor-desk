# 五轴共同规则（Common Axis Rules）

## 1. 设计目标

五轴文件的目标不是给出交易动作，而是给 Layer 1 全球底层状态面板提供可解释、可审计、可追溯的状态变量。

五轴分别为：

- ENVIRONMENT：环境轴
- CREDIT_STRESS：信用压力轴
- RISK_APPETITE：风险偏好轴
- LIQUIDITY：流动性轴
- SENTIMENT：情绪轴

## 2. 面向用户的统一解释口径

前端展示时，每个指标至少回答：

1. 它是什么？
2. 它今天是多少？
3. 它处于历史高位、低位还是正常区间？
4. 今天变化是平稳、上升、下降还是突变？
5. 它能说明什么？
6. 它不能说明什么？
7. 数据是否新鲜？是否滞后？是否有质量问题？

## 3. 统一舱位

> **全链路（用户裁决 @ 2026-07-04）：** 下表全部舱位均须走 **真 sync → clean → 特征 → 解读** 同库管道（见 `../README.md` §指标全链路要求）。舱位只决定 **是否进主面板 / 是否可当 primary_source / 如何诚实降级**，**不**豁免管道步骤。

| 标记                 | 含义                         | 是否进入 Layer 1 主面板  | 管道与降级                                                                |
| -------------------- | ---------------------------- | ------------------------ | ------------------------------------------------------------------------- |
| A / Layer1_State     | 状态量，频率和可得性相对及时 | 是                       | 全链路；可作 `primary_source`                                             |
| B / Layer1_Projected | 投影、滞后、窗口估计或混频态 | 是，但必须标注滞后和方法 | 全链路；可作 `primary_source`                                             |
| C / Layer2_Warning   | 慢变量、背景灯、解释灯       | 不回写 Layer 1 分值      | 全链路；不当主面板主值；解读标背景灯                                      |
| D / BlindSpot        | 盲区：公开可审计数据可能不足 | 不冒充主状态             | 全链路；**不得**当 `primary_source`；客观不可达时诚实失败 + 边界解读      |
| SHADOW               | 对账、诊断、旁证             | 不进面板，不接管主值     | 全链路；`validation_only` / 旁证；**不得**当 `primary_source`             |
| Forbidden            | 禁用身份 / 防误用 substitute | 不得进入主结论           | 全链路 + registry；阻断 forbidden substitute；**不得**当 `primary_source` |

## 4. 数据源角色重构

原说明书中的 `Primary / Shadow / Emergency` 重构为：

- `primary_source`：正式事实源。
- `validation_source`：对账、审计或旁证源；仅在领域 RoutePlan 的 `FallbackPolicy` 明确授权、有效启用且能力匹配时，才可作为 `DEGRADED` 兜底，不得成为 Primary。
- `fallback_policy`：失败处理策略，不等于第三个外部数据源。

`fallback_policy` 可选值：

- retry
- last_good_cache
- NaN + stale_reason
- manual_review
- source_switched_flagged

默认不再要求每个指标维护第三个外部数据源，以降低运维成本。

### 4.1 `SHADOW` 诊断标签的窄例外

Layer 1 YAML 中的 `*.SHADOW.*`、`layer: Shadow`、`dest_tag: SHADOW` 只表示诊断/旁证指标，不表示旧数据源角色。该窄例外必须满足：

- 允许出现在明确带诊断/旁证语义的 Layer 1 indicator 条目、`shadow_diagnostics` 分组、`schema_note` 或说明文字中。
- 不得写入 `source_registry` 的 `source_role`、`default_role`、domain role 或 fallback role。
- 不得产生 clean 主值接管，不得替代 A/B/C 主展示指标。
- 每个 `*.SHADOW.*` 指标必须带 `no_main_score_input`、`no_takeover`、`validation_only` 或同等约束语义。
- 若 `*.SHADOW.*` 条目不在 `shadow_diagnostics` 分组下，必须在条目内显式写明 `diagnostic_only` / `evidence_only` / `does_not_replace_main_indicator` 或同等约束。
- 实现测试必须覆盖：`test_layer1ShadowDiagnostics_areExplicitlyAllowedButNoTakeover`、`test_shadowDiagnosticLabels_doNotEnterSourceRegistryRoles` 与 `test_shadowDiagnosticsOutsideGroup_requireExplicitDiagnosticOnly`。

## 5. 统一状态字段

每个 Layer 1 指标建议落地以下字段：

- raw_value
- raw_unit
- as_of_timestamp
- publish_timestamp
- fetch_time
- source_used
- source_grade
- quality_grade
- manual_review_required
- route_plan_id
- data_lag_days
- stale_reason
- quality_flags
- z_score
- robust_z_score
- percentile_rank
- raw_delta_abs
- raw_delta_pct
- raw_delta_log
- z_score_delta
- percentile_delta
- state_bucket
- window_len
- valid_obs_count
- coverage_ratio

## 6. 统一窗口策略

| 指标频率        |   主窗口 |   最小样本数 | 说明                   |
| --------------- | -------: | -----------: | ---------------------- |
| Daily           |       3Y |          500 | 主力窗口               |
| Weekly          |       5Y |          156 | 周频足够做分位与标准化 |
| Monthly         |      10Y | 60，优先 120 | 5Y 偏短，只可参考      |
| Quarterly       |  10Y-15Y |  40，优先 60 | 5Y 不足以判断极端      |
| Irregular/Event | 按观测数 |    30/60/120 | 不按自然年硬套         |

## 7. 禁止项

- 不输出买卖、加仓、减仓、开仓、平仓、入场、出场等动作语义。
- 不把 Layer 2 慢变量回写 Layer 1。
- 不把 SHADOW 诊断标签当作主值接管或数据源角色。
- 不 silent switch；任何 source_switched 必须显式标记。
- 不跨轴污染：每个指标只能归属一个轴。
- 不用不可审计来源伪造指标。

## ADR-017 来源／质量连续监控规则

Validation 源未经领域 `FallbackPolicy` 授权时不接管；经授权时只能作为 `DEGRADED` 的
`FallbackPolicy`，不能成为 Primary。`PRIMARY|DEGRADED` 与 `QUALITY_PASSED|QUALITY_FAILED`
必须独立传播。质量失败但可归一化、血缘完整的数据可进入连续监控计算和告警，但结果必须标记
`MANUAL_REVIEW_REQUIRED`；不可解析或无数值时必须诚实为 `MISSING`。完整字段与存储边界见
`specs/contracts/design/source_provenance_quality_contract.yaml`。

## 8. Agent 边界

程序负责计算数值、分位、z-score、状态标签、预警等级和质量标签。Agent 只负责基于结构化事实和静态说明生成通俗解释。Agent 不直接决定预警、不直接改库、不直接给交易建议。

## 9. 指标全链路关账（M-G1-03 · Audit 核对）

1. **62 个 `indicator_id`**（五轴 YAML 合计）均须有同库链路证据；禁止「每轴 1 代表」关账 G1。
2. **禁止** pytest / 验收 seed 冒充 sync 成功。
3. BlindSpot / Forbidden / SHADOW：**同样**走 sync→受治理写入（可信最终库或连续监控区）→特征→解读；不得当 `primary_source`；付费墙、登录、交易所内部信息等导致不可达时，**诚实失败**算链路通（须留 `quality_flags` / `stale_reason` / 边界解读）。
4. 「不伪造不可得数据」= 不 seed、不冒充当日真值、不用 forbidden substitute 填主位；**≠** 跳过抓取与落库步骤。
5. 细则 SSOT：`../README.md` §指标全链路要求 · `docs/implementation_tasks/M_G1_03_LAYER1_FULL/M_G1_03_LAYER1_FULL.md`。
