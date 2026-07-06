# ADR-006：生产 Sync 在无 datasource_service 时 fail-closed

## 状态

已接受（2026-06-29）— 计划 R3H-10 / S10-01

## 背景

R3H-10 闭合 **C2**：Sync、CLI 路由预览、rehearsal 边界（`STAGED-PILOT-SSOT`）在生产路径上必须以 `DataSourceService` 为唯一拉数门面。

现有守卫已在生产环境对「传入 `adapter=` 却无 `DataSourceService`」**fail-closed**（`backend/app/sync/runners.py` 中的 `guard_production_adapter_bypass`）。Runner 也会在既无 `adapter` 又无 `fetch_callable` 时拒绝执行（`IncrementalJobRunner.run` / `BackfillShardRunner.run`）。

剩余歧义在编排器层：当 **`adapter=` 与 `datasource_service=` 均未传入** 时，是自动构造默认生产 service，还是显式报错。参考分析（`reference-adoption-r3h10.md`）将 EasyXT 的 `auto_data_updater` 标为反模式：经 `sys.path` 引入隐式第二入口（`DataManager`），绕过统一门面。

## 决策

1. **生产语义：** `DataSyncOrchestrator.run_incremental` / `run_backfill` 在省略 `datasource_service=` 时**不得**自动构造默认 `DataSourceService`。**`run_reconcile`** 在 R3H-10 仍保持 adapter 形态（见下文「Reconcile 延后」）。
2. **调用方契约：** 运维与脚本在生产金路径上必须显式传入 `datasource_service=`（如 `tests/test_vendor_fetch_e2e.py`）。
3. **失败模式：** fail-closed，错误信息可测、可区分：
   - 缺少 `datasource_service=`（本 ADR），与
   - 有 `adapter=` 绕过却无 service（既有 R3Y 守卫）。
4. **测试：** 扩展 `tests/test_sync_orchestrator.py`（或等价模块），使生产 profile 下既无 `datasource_service=` 又无 `adapter=` 的调用按 S10-01 RED→GREEN。
5. **范围外：** 不改动仅 pytest 可用的 `adapter=` 钩子（仍由 `sync_adapter_bypass_allowed()` 保护）。

### Reconcile 延后（R3H-10 关账范围）

- **R3H-10 S10-01 已交付：** 仅在 `run_incremental` / `run_backfill` 上启用 `guard_production_datasource_service_required`。
- **`run_reconcile(conflict_id, *, adapter=)`** 仍强制 `adapter=`；生产 profile 经 `guard_production_adapter_bypass` **fail-closed**（`test_r3ySync001_reconcile_*`）。
- **reconcile 的 `datasource_service=` 金路径** 延后至 R3H-10 之后独立 sync 切片（绑定：Wave 2 / R3H-08 产品 live 准备，或专用 reconcile-service 跟进）。**不是**静默绕过：当前生产环境下无 service 的 reconcile **不能跑**。

## 曾考虑的替代方案

### 自动构造默认 `DataSourceService`

- 优点：脚本改调用点更少。
- 缺点：掩盖 registry/守卫/fixture 选择；形成类似 EasyXT `DataManager` 的隐式第二入口；削弱 `datasource_service_contract.yaml` 可审计性。
- **已否决。**

### fail-closed（采纳）

- 优点：与 adapter 绕过守卫对称；金路径显式；符合 C2 SSOT 与 PASS 门禁。
- 缺点：调用方必须显式注入 service。

## 后果

- S10-01 执行聚焦编排器层强制与错误文案，不发明新的 runner 语义。
- 文档与 live 任务卡引用本 ADR。
- R3H-08 产品 live 工作继承显式 service 注入契约。

## 参考

- 历史执行材料：`docs/archive/trellis-loop-2026/` 下 R3H-10 相关 research（`00-EXECUTION-ENTRY.md` §4、`to-issues-slices.md` §3、`reference-adoption-r3h10.md` §3.2）
- `backend/app/sync/runners.py` — `guard_production_adapter_bypass`
