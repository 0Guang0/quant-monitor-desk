# Audit matrix — M-G1-03（v4.2 Slim）

> **追溯：** `EXECUTION_PLAN.md`（AC · P1/P2 任务 · §9 契约）· `EXECUTION_INDEX.md` §2 AC · §3 manifest  
> **模块：** G1 → R4 · K1 · K2 · A5  
> **门禁：** P1-GATE 未绿禁止 Phase 2；关账 `uv run pytest -q` exit 0

## 维度要点（Plan 冻结 @ 2026-07-04）

| 维度        | 验证焦点                                                        |
| ----------- | --------------------------------------------------------------- |
| A1 契约     | `specs/contracts/*` · 矩阵校验器 · `data_cli_contract` 扩展登记 |
| A2 边界     | `module_boundary_contract` · Layer 无 `datasources.service`     |
| A3 Sync     | `data_sync_orchestrator.md` §13 · 五 job · FullLoad · scheduler |
| A4 数据链   | 62 指标 sync→clean→特征→解读；禁止 seed 冒充                    |
| A5 范围     | 本票不做 Round4 API/前端；EXECUTION_PLAN Boundaries             |
| A6 测试     | 五字段 docstring · TDD · `tests/test_layer1_*`                  |
| A7 文档     | MCR G1/K1/K2 跃迁 R4；ADR 引用一致                              |
| A8 安全/ops | CliFailure · ERROR_CODE_GUIDE · ResourceGuard                   |

无占位符；维度验证见 `audit.jsonl` · Execute 完成后派发 A1–A8。
