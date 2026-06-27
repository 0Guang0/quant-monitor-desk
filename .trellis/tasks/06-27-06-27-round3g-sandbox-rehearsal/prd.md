# PRD — R3G-01 Sandbox Clean-Write Rehearsal

## 问题

五层 staged 闭环已有，但 **Batch 3G** 须单独证明：**受控 clean write** 能在 sandbox 内通过 QMD 门禁链（fetch → data health → validation → WriteManager → rollback 证据），才允许考虑 R3G-02 审计与 R3G-03 有限生产入口。

## 用户 / 角色

- **Coordinator**：审批 Plan、授权 FRED 排练
- **Execute agent**：实现 sandbox 编排器与 CLI（本任务）
- **Audit（R3G-02，后续）**：消费 R3G-01 排练报告

## 范围（In）

- sandbox-only 排练：`baostock` daily bar、`cninfo` metadata、`fred` macro（用户授权 artifact）
- 新模块 `backend/app/ops/sandbox_clean_write/*`
- CLI：`qmd data sandbox-clean-write rehearse --no-production-mutation ...`
- 结构化 `rehearsal_report.json`（契约必填字段）
- TDD 扩展 `test_round3g_sandbox_*` + `test_reference_adoption_guardrails.py`

## 范围（Out）

- 生产 DB 写入 / R3G-03
- 五层全量端到端证明
- 扩大候选 cap / 新数据源
- L1 ingest allowlist 扩展

## AC 摘要

见 `EXECUTION_INDEX.md` §2（AC-01..AC-10）。

## 依赖

- R3F-R data-health profiles、`staged_pilot.py` 编排模式
- `sandbox_clean_write_contract.yaml`
- FRED：`round3-fred-authorized-sandbox-pilot` authorization YAML 形态参考

## 风险

| 风险                       | 缓解                                                       |
| -------------------------- | ---------------------------------------------------------- |
| sandbox 与生产 DB 路径混淆 | `--no-production-mutation` 强制；拒绝 `DATA_ROOT` 生产路径 |
| FRED 无授权仍 fetch        | fail-closed artifact 校验                                  |
| 绕过 WriteManager          | 测试断言 + 禁止 ad-hoc runner                              |
| cap 静默扩大               | 契约 + rehearsal_plan 硬编码 r3g01 caps                    |

## 追溯

- 活任务卡：`R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md`
- 路线图：`PROJECT_IMPLEMENTATION_ROADMAP.md` §4 Batch 3G
- Playbook：`BATCH_3G_COORDINATOR_PLAYBOOK.md`
