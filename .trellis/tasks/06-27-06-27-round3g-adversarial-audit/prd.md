# PRD — R3G-02 Pre-Production Adversarial Audit

> **任务卡 SSOT：** `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md`  
> **前置：** R3G-01 已合并 `master`（`4aa6a1c3`）  
> **轨道：** `simple` — 任务卡即规格，无 EXECUTION_INDEX / frozen

## 问题

R3G-01 已在 sandbox 完成受控写入排练并产出报告与证据，但**尚未有机器可执行的 go/no-go 判定**来决定能否讨论 R3G-03 有限生产写入。需要把排练证据转成严格、可重复的对抗审计结论。

## 用户 / 角色

- **Coordinator**：批准本任务 Execute；消费审计决策
- **Execute agent**：实现审计器 + CLI + 测试
- **R3G-03（后续）**：仅当审计决策允许且用户书面授权

## 范围（In）

- 读取 R3G-01 `rehearsal_report.json`、sandbox DB 路径、evidence 目录
- 五维对抗审计（数据质量、loader 边界、报告证据、provider 架构、no-agent）
- 输出**唯一**决策枚举之一：
  - `PASS_ALLOW_LIMITED_PROD_WRITE`
  - `WARN_ALLOW_WITH_MANUAL_APPROVAL`
  - `BLOCK_PRODUCTION_WRITE`
- CLI：`qmd data sandbox-clean-write audit ...`
- 新模块：`adversarial_audit.py`、`audit_decision.py`（`sandbox_clean_write/` 包内）
- 扩展 `tests/test_round3g_pre_production_adversarial_audit.py`（task card §7 全矩阵）

## 范围（Out）

- 生产 DB 写入 / mutation
- 新数据源 fetch（除 R3G-01 artifact 授权的只读核验）
- cap 扩大、候选集扩展
- OpenBB runtime 拷贝、Agent 触发写入路径
- R3G-03 实现

## AC 摘要

| ID    | 验收                                                                                      |
| ----- | ----------------------------------------------------------------------------------------- |
| AC-01 | 审计输出使用契约 `r3g02_audit.decision_enum` 三者之一                                     |
| AC-02 | 每条决策含 blocking/warning reasons + evidence paths                                      |
| AC-03 | 缺 report / 缺 DH profile / uncapped / 参考项目 runtime import → `BLOCK_PRODUCTION_WRITE` |
| AC-04 | 近似 calendar 证据 → 至多 `WARN_ALLOW_WITH_MANUAL_APPROVAL`                               |
| AC-05 | 合法有界证据 → `PASS` 或带 manual approval 的 `WARN`                                      |
| AC-06 | CLI 不接受生产 DB 写路径；`production_mutation_allowed=false`                             |
| AC-07 | `uv run pytest tests/test_round3g_pre_production_adversarial_audit.py -q` 全绿            |
| AC-08 | `uv run pytest tests/test_reference_adoption_guardrails.py -q` 全绿                       |

## 依赖

- R3G-01：`backend/app/ops/sandbox_clean_write/{rehearsal_runner,rehearsal_report,rehearsal_plan}.py`
- `specs/contracts/sandbox_clean_write_contract.yaml`（`r3g02_audit` 段已存在）
- `specs/contracts/reference_adoption_guardrails.yaml`
- R3F-R data-health profiles

## 风险

| 风险                     | 缓解                                         |
| ------------------------ | -------------------------------------------- |
| 审计误放行生产           | fail-closed block_if；测试覆盖 task card §7  |
| 与 R3G-01 报告形状不一致 | 消费 `required_report_fields` + 真实 fixture |
| 主会话上下文过长         | Execute 由派发 agent 完成                    |
