# ADR-004：写入热路径 C901 复杂度上限

> **相关：** 任务文档与代码路径映射见 [ADR-003](ADR-003-implementation-path-mapping.md)。

## 状态

已接受（2026-07-01）

## 背景

Round2 审计项 `D3-P1-2` 对以下符号的 mccabe 复杂度提出告警：

- `SourceRegistry._validate_domain_roles`
- `WriteManager._execute_write`

二者位于接入写入热路径，含大量域相关分支（fail-closed 守卫、模式路由、血缘钩子等）。

## 决策

1. **Wave 4 prep 不做拆分重构** — 抽 helper 会打散事务边界逻辑，且不降低真实风险。
2. **复杂度由测试锁定** — `tests/test_write_manager.py`、`tests/test_source_registry.py` 及契约漂移测试固定行为。
3. **未来拆分触发条件** — 若任一函数新增**第四种**独立写入域，在 Batch 6 专用切片（`R3F-HYG`）中提取域 handler。

## 后果

- `D3-P1-2` 以 **ADR wont-fix** 关账（非静默忽略）。
- Ruff C901 仍可能报告上述符号；当前 CI **不以 C901 为门禁**。
- 在这些函数中新增分支时，须按 `testing-guidelines` 补 pytest 覆盖。
