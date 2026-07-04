# 五轴说明书重构包 v1.1

本包把原始五份说明书重构为更适合前端展示、工程实现和后续维护的文件结构。

**执行 / Audit SSOT（用户裁决 @ 2026-07-04 · M-G1-03）：** 下文 **§指标全链路要求** 优先于本文件旧版一句式摘要；与 `common/common_axis_rules.md` §3、§9 一致。冲突时以本节 + common 规则为准，并同步 `docs/modules/layer1_global_regime_panel.md` 验收表。

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
8. **不伪造不可得数据** — 指禁止 seed / 手工填数 / 替代指标冒充主值；**不等于**可跳过 sync→clean→特征→解读管道（见 §指标全链路要求）。

## 指标全链路要求（M-G1-03 · Execute / Audit 必读）

### 范围

- 五轴 YAML 中登记的 **全部 `indicator_id`（当前共 62 个身份）** 均须在同一张数据库内具备 **可审计的完整链路证据**。
- **禁止**以「每轴只做 1 个代表指标」作为 M-G1-03 或 G1→R4 关账口径（过度竖切、重复 Plan–Execute–Audit，与活规划 §3.2 冲突）。
- **禁止**测试或验收中使用 tmp DB **seed 手工塞数** 冒充「真 sync 已成功」。

### 统一管道（适用于全部舱位，无豁免）

每个 `indicator_id` 均须走同一条真实流水线（同库可追溯）：

```text
真 sync 尝试（外部抓取 / 已验收 adapter）
  → axis_observation / clean 可查（含诚实空结果与质量标记）
  → AxisFeatureEngine 产出状态档位（允许 NULL / INSUFFICIENT_HISTORY 等诚实结果）
  → AxisInterpretationEngine 产出带边界提醒的解读
```

**「完整链路已跑通」的判定：**

| 情况                                                                                                                                                       | 是否算链路关账                |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| sync 成功 → clean 有值 → 特征与解读可断言                                                                                                                  | ✅                            |
| sync 因付费墙、需登录、交易所内部、公开源不存在等 **客观不可达** → clean 无行或带 `quality_flags` / `stale_reason` → 特征诚实为 NULL 或不足 → 解读写明边界 | ✅（**诚实失败 / 诚实降级**） |
| 未调用 sync、仅 registry 登记、或测试 seed 假装成功                                                                                                        | ❌                            |

### 舱位差异（走同一管道；差异在角色与解读，不在「做不做」）

| 舱位                                     | 管道                         | 不得作为                                        | 面板 / 分值                          | 客观不可达时的诚实降级                                                        |
| ---------------------------------------- | ---------------------------- | ----------------------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------- |
| **A/B / Layer1_State、Layer1_Projected** | 全链路                       | —                                               | 可进主面板                           | `stale_reason`、滞后标注；不伪造 z-score                                      |
| **C / Layer2_Warning**                   | 全链路                       | `primary_source` 接管他指标主值                 | 背景灯；**不回写** Layer1 主分值     | 慢变量 / 无 feed 时在解读中标明「仅背景，非日频主状态」                       |
| **SHADOW / `*.SHADOW.*`**                | 全链路                       | `primary_source`；clean **主值接管**            | 不进主面板；`validation_only` / 旁证 | 解读标明「旁证 / 对账，不替代 A/B 主指标」                                    |
| **D / BlindSpot**                        | 全链路                       | `primary_source`；冒充可观测主状态              | 不伪造「今日有可靠主值」             | 解读标明盲区原因（许可、口径、稳定性不足等）；可用 `BLINDSPOT_NOT_OBSERVABLE` |
| **Forbidden / `layer: Forbidden`**       | 全链路（含 registry 防误用） | `primary_source`；**forbidden substitute** 写入 | 不得进入主结论                       | 阻断替代写入；解读标明禁用原因与边界                                          |

**统一要求：**

- `primary_source` 字段仅用于 **可承担主事实源** 的指标；BlindSpot / Forbidden / SHADOW **不得**在路由或面板语义上充当其他指标的主源。
- 「降级为旁证或盲区」指 **解读角色与分值权重**，不是省略 sync 或省略 clean/特征/解读步骤。
- Round4 的 **完整 API + 前端五轴卡** 不在 M-G1-03 范围；本票只闭合后端管道与同库证据 + pytest。

### 与「不伪造不可得数据」的关系

- **允许：** 真 sync 失败后在同库留下失败证据、质量标记、诚实 NULL 特征、边界解读。
- **禁止：** 无抓取却写入看似正常的 `raw_value`；用 last_good_cache **冒充**当日真值；用禁用替代指标填主指标空位；pytest seed 绕过 sync。

## 推荐落地方式

- 先把 YAML spec 作为实现蓝图。
- 用户指南作为前端说明卡和 Agent 解释模板来源。
- 工程规则作为 DataQualityValidator、SourceConflictValidator 和 ReconcileJob 的规则来源。
- M-G1-03 Plan 冻结前：以 **62 身份 × 全链路** 规划 `/to-issues` 竖切（按数据源/适配器分批，**不得**按「每轴 1 代表」拆票）。

## v1.1 追加说明

- 统一继续使用 `Primary + Validation + FallbackPolicy`。
- 为 SHADOW / BlindSpot / Forbidden 指标补充最小 `plain_language_summary`、`layer` 和 `dest_tag`，防止实现时 schema 校验失败。
- ~~Forbidden 指标只进入 registry 用于防误用，不进入 observation。~~ **已废止（2026-07-04）：** Forbidden 身份仍须走 §指标全链路要求；不得作为 `primary_source` 或 forbidden substitute 主值，但须在 sync→clean→特征→解读 同库留 honest 证据（见上表）。
