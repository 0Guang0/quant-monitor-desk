# CodeGraph + GitNexus Plan 阶段刷新摘要

> 2026-06-18 · Batch D Plan 补强 · 非 Execute 6.pre（Execute 须另写 `gitnexus-execute-summary.md`）

## 安装与 MCP 状态

| 项 | 状态 |
|----|------|
| CodeGraph CLI | **已安装** `@colbymchenry/codegraph` v1.0.1（`npx` 可运行） |
| 本地索引 `.codegraph/` | **存在** · sync 后 up to date |
| Cursor MCP | **已注册**（`codegraph install --target cursor` 写入 `~/.cursor/mcp.json`） |
| 此前不可用原因 | **CLI+索引已有，MCP 未注册**；非「未安装」 |
| 用户动作 | **重启 Cursor** 后 Agent 侧 `mcps/user-codegraph` 才会出现 |

### mcp.json 新增条目

```json
"codegraph": {
  "type": "stdio",
  "command": "codegraph",
  "args": ["serve", "--mcp", "--path", "${workspaceFolder}"]
}
```

## CodeGraph 索引（sync 后）

| 指标 | 值 |
|------|-----|
| Files | 162 |
| Nodes | 1,590 |
| Edges | 4,215 |
| Python files | 106 |
| YAML files | 52 |

本次 sync：38 changed files · +13 added · 25 modified

## GitNexus 索引（analyze 后）

| 指标 | 值 |
|------|-----|
| Nodes | 3,045 |
| Edges | 4,452 |
| Clusters | 45 |
| Flows | 67 |

## CodeGraph explore — Batch D 编排触点

查询：`DataSyncOrchestrator sync orchestration`（80 symbols · 7 files）

**关键编排依赖（Execute 须接线）：**

| 符号 | 路径 | 备注 |
|------|------|------|
| `DataQualityRequest/Report` | `validators/data_quality.py` | job_id/run_id 字段已存在 |
| `SourceRegistry.sync_to_db` | `source_registry.py:340` | **已实现 `tombstone_missing`**（DECISIONS GPT-P2-2 部分偿还） |
| `ResourceGuard.check` | `resource_guard.py` | FETCHING 前门禁 |
| `WriteManager` | `write_manager.py` | gate 注入写 clean |
| `DbValidationGate` | `validation_gate.py` | 含 open severe conflict 拒绝 |
| `BaseDataAdapter.fetch` | `base_adapter.py` | adapter 入口 |
| `test_batch_c_validation_flow` | tests | E2E 模板 |

**无符号：** `DataSyncOrchestrator`（确认 Batch D 新建）

## GitNexus query — 文档 File 节点（补读线索）

命中代码侧为主；相关 File 定义包括 `write_manager.py`、`validation_gate.py`、`test_batch_c_validation_flow.py`。

任务卡/规格类 File 需结合 `docs/implementation_tasks/` 树 + 任务卡 §3 交叉核对（见 Agent 1 文档缺口分析）。

## Plan 阶段建议补读（图工具发现）

| 路径 | 理由 |
|------|------|
| `docs/modules/write_manager.md` | job_id ↔ write_audit 关联 |
| `docs/modules/data_validation_and_conflict.md` | Batch C 模块规格（014 间接依赖） |
| `docs/modules/data_sources.md` | fetch_log / registry 权威 |
| `specs/contracts/data_adapter_contract.md` | adapter 契约 |
| `specs/contracts/data_quality_rules.yaml` | orchestrator VALIDATING 阶段 |
| `specs/contracts/source_conflict_rules.yaml` | reconcile 阶段 |
| `backend/app/datasources/adapters/__init__.py` | `create_adapter` factory |
| `scripts/ci_ingestion_smoke.py` | GPT-P3-6 扩展基线 |
| `.trellis/tasks/06-17-round2-batch-c-validation-conflict/finish.md` | 前置 handoff |

## DECISIONS 漂移注意

`SourceRegistry.sync_to_db` 已支持 `tombstone_missing: bool = True`（YAML 缺失源 disabled）。MASTER §8.8 / §1.3 若仍写「仅最小 disabled 策略待实现」需修订为「调用既有 tombstone_missing API + 测试」。
