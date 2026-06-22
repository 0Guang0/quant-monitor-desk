# 019_implement_layer2_cross_asset_sensor 实现 Layer 2 跨资产传感器

## 1. 任务目标

实现 cross_asset_registry、observation、daily snapshot、double_count_guard。

## 2. 预期结果

完成后，Claude Code / Codex 应能在不依赖上下文记忆的情况下，依据本任务和输入文件完成对应模块的可运行实现或可验证骨架。

## 3. 输入文件

- `docs/modules/layer2_cross_asset_sensor.md`
- `specs/contracts/layer2_sensor_contract.yaml`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `specs/contracts/runtime_versions.md`
- `docs/quality/staged_acceptance_policy.md`
- `specs/contracts/snapshot_lineage_contract.yaml`

## 4. 相关代码 / 输出文件

- `backend/app/layer2_sensors/sensor_loader.py`
- `tests/test_layer2_sensor_loader.py`

## 5. 现有模式 / 参考

- 遵循 `docs/architecture/03_runtime_flows.md` 中的运行链路。
- 遵循 `docs/architecture/04_data_architecture.md` 中的数据分层。
- 遵循 `docs/quality/final_package_rules.md` 中的最终包规则。
- 任何写入 clean table 的行为都必须经过 `DuckDBWriteManager`。
- 任何重任务都必须先通过 `ResourceGuard`。

## 6. 技术约束

- 后端优先使用 Python、FastAPI、Pydantic、DuckDB、Parquet、Polars Lazy。
- 前端使用 Vite + React + TypeScript；页面布局只是占位，正式实现前必须提醒用户确认。
- 配置与契约使用 YAML / JSON / SQL / Markdown。
- 不允许新增未经用户确认的大型依赖。

## 7. 资源约束

- 默认运行模式为 `eco`。
- 不允许全市场全历史扫描作为默认行为。
- 不允许无分页 API 或 Agent 大查询。
- 如果触发 `RESOURCE_GUARD_PAUSED`，必须停止非核心任务并汇报原因。

## 8. 边界约束

- 不得恢复 `Primary / Shadow / Emergency` 旧口径。
- 不得输出交易动作语义。
- 不得绕过 `WriteManager`。
- 不得把 Agent 文本当作事实来源。
- 不得固定死前端最终页面设计。
- 不得修改与本任务无关的金融语义和 spec。

## 9. 实现步骤

- 加载跨资产 registry
- 主力合约切换事件
- 避免与 Layer1 双算
- 先写或补充最小测试 / smoke test，再实现。
- 运行本任务验收命令。
- 汇报改动文件、测试结果、未完成项、资源保护状态。

## 10. 测试要求

- 只 mock 外部 I/O，例如数据库、HTTP、文件系统、消息队列。
- 纯计算逻辑和条件分支必须使用真实值。
- 每个测试至少包含一个业务语义断言。
- 禁止只用 `assertNotNull` 或 `assertDoesNotThrow` 作为唯一断言。
- 测试命名建议：`functionName_condition_expectedBehavior`。

## 11. 验收命令

本任务为后端实现任务。验收命令：

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run python -m compileall backend scripts tests
```

## 12. 完成标准

- 本任务列出的输出文件已创建或更新。
- 测试命令通过，或明确说明未运行原因和阻塞项。
- 没有生成临时 round report、scratch、tmp 或一次性 self-check 文件。
- 没有引入与现有 docs/specs/contracts 冲突的口径。

## 13. Red Flags

出现以下情况必须停止并修正：

- 为了完成本任务修改了无关模块。
- 跳过测试并声称“看起来没问题”。
- 前端页面布局被当作最终设计写死。
- Agent 能自由 SQL、自由联网或直接写库。
- 大查询未经过 ResourceGuard。
- 测试只验证方法调用，不验证业务结果。

## 14. 输出要求

执行完成后只输出：

1. 改动文件清单。
2. 新增文件清单。
3. 删除文件清单。
4. 测试命令和结果。
5. ResourceGuard 是否触发。
6. 未完成项或需要用户确认的点。

## 15. 审计修复补充要求

所有建模/快照输出必须写入统一 lineage：

- `snapshot_id`、`snapshot_type`、`layer_id`。
- `as_of_timestamp` 与输入观测的可见时间边界。
- `source_fetch_ids`、`source_content_hashes`。
- `rule_version`、`code_version`、`parameter_hash`。
- `upstream_snapshot_ids` 与是否 incremental。
- 测试必须证明不会读入 as_of 之后的未来数据。

### 用户决策补充：D-09

用户已拍板：完整标准化字段仅 Layer 1；Layer 2-5 不默认复制，只能按需局部扩展。

## 16. Batch 3 staged-only downstream gate

在实现或审计 Batch 3 / `019` 前，必须先关闭 `R3-B3-STAGED-DOWNSTREAM-GATE`（见 `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`）。MASTER.plan.md 与 AUDIT.plan.md 必须显式引用以下上下文：

- `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`。
- Batch 2.5 `final_registry_update.md`：当前 ingestion type 是 staged，不是 production-live。
- `018A_layer1_observation_ingestion_bridge.md` §13。
- `docs/UNRESOLVED_ISSUES_REGISTRY.md` 中 `R3-B2.75-01` 的当前状态。

若 `R3-B2.75-01` 仍为 `DEFERRED`，或 Batch 2.75 closeout 为 `PILOT_FAIL_SOURCE` 且 Request 2 仍在 `R3-B2.75-REQ2-EM`，本任务不得声称 production-live readiness，不得把 Batch 2.5 staged evidence 升级表述为 live production evidence，也不得使用 live FRED / production DB / external vendor writes 作为默认前提。

## 17. Round 3 sequencing / branch boundary

`019` 是 staged-only mainline 的第一批下游建模任务。它可以和 Phase 8D debt branches 并行，但不能与 `020`/`021` 同时修改 snapshot lineage semantics。推荐分支：`feature/round3-019-layer2-sensor`；前置：`feature/round3-batch3-staged-gate` 已关闭。
