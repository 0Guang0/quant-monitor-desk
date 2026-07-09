# ADR-004：写入热路径 C901 复杂度上限

> **相关：** 任务文档与代码路径映射见 [ADR-003](ADR-003-implementation-path-mapping.md)。

## 状态

已修订（2026-07-09）— task-01.5 S7 提取式简化关账

## 背景

Round2 审计项 `D3-P1-2` 对以下符号的 mccabe 复杂度提出告警：

- `SourceRegistry._validate_domain_roles`
- `WriteManager._execute_write`

二者位于接入写入热路径，含大量域相关分支（fail-closed 守卫、模式路由、血缘钩子等）。

2026-07-01 初版决策为「测试锁行为、暂不拆」。2026-07-09 task-01.5 S7 以**行为保持的私有 helper 提取**取代该纪律。

## 决策

1. **复杂度由测试锁定** — `tests/test_write_manager.py`、`tests/test_write_manager_degraded_audit.py`、`tests/test_source_registry.py` 固定行为；**不**为 helper 单测。
2. **已完成的提取式简化（2026-07-09）**
   - `source_registry._validate_bound_source` — primary/validation 四条守卫共享；`_validate_domain_roles` 降为编排。
   - `WriteManager._resolve_audit_sidecar_root` · `_apply_staging_to_clean` · `_fail_write_after_error` — `_execute_write` 降为编排。
   - **零**对外 API 变更（`WriteRequest` · `write()` · `SourceRegistry` 公开方法不变）。
3. **未来再评触发条件** — 新增 `write_mode` 或**第四类** merge 策略时，再评是否引入独立 `MergePlanner` / `TransactionRunner` 模块（ponytail：本票不新建类模块）。

## 关账证据

- `uv run ruff check backend/app/db/write_manager.py backend/app/datasources/source_registry.py --select=C901` → 0 错误
- `uv run pytest tests/test_write_manager.py tests/test_write_manager_degraded_audit.py tests/test_source_registry.py -q` exit 0

## 后果

- 在这些热路径新增分支时，须按 `testing-guidelines` 补 pytest 覆盖。
- Round2「第四种写入域才拆」**不再**作为 `_execute_write` / `_validate_domain_roles` 维持高圈复杂度的唯一理由。
