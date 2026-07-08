# Operator Guide

## 1. 常用入口

- 部署与本地运维总入口：`docs/architecture/design/06_deployment_and_local_ops.md`
- 运行时版本与验收命令（`uv sync` / `uv run`）：`specs/contracts/design/runtime_versions.md`
- 日/周/月运维检查清单：`docs/ops/design/daily_weekly_monthly_checklist.md`
- 数据同步与运行时链路：`docs/architecture/design/03_runtime_flows.md`
- 同步 Job 与编排细则：`docs/modules/design/data_sync_orchestrator.md`
- 幂等 / 重试 / 路由预览：`docs/ops/design/idempotency_retry_dlq_policy.md` · `docs/modules/design/source_route_plan.md`
- 错误排障：`docs/ops/design/ERROR_CODE_GUIDE.md` · `docs/ops/design/TROUBLESHOOTING.md`
- 场景手册：`docs/ops/design/incident_playbook.md`

## 2. 安全运行原则

1. 先 dry-run，再写入。
2. 先 route-preview，再 fetch。
3. 遇到 disabled source，不要手工绕过代码。
4. 遇到 ResourceGuard 暂停，缩小范围或分片。
5. 生产等价验证只使用临时 DB、fixture-scale 数据或只读/脱敏快照。

## 3. QMT / xqshare

QMT 本地源和 qmt_xqshare 远程源默认禁用。启用前必须用户确认授权、配置路径或 env，并接受安全边界。细则见 `docs/ops/design/qmt_xqshare_setup.md` · `docs/modules/design/qmt_xtdata_adapter.md`。

## 4. 设计图与运行副本（parity）

- **设计图**：`MIGRATION_MAP.md` 索引的 `**/design/**` 路径（最高权威，不得为通过测试随意修改）。
- **运行副本**：`scripts/promote_design_runtime.py` 列出的原路径（代码读取）。
- **`test_design_runtime_parity` 失败时**：
  1. 运行 `uv run python scripts/promote_design_runtime.py`（design → runtime，单向）。
  2. **禁止**为让测试变绿而去改 `design/` 贴合运行副本。
  3. 若规格确需变更：先改 `design/` 并经用户审阅（须 ADR 时不得省略），再 promote。
