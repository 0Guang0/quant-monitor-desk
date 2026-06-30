# Audit A3 — 架构（R3-DCP-03 post-write inspect）

| 元信息 | 值 |
| --- | --- |
| 维度 | A3 架构 |
| 任务 | `06-30-wave3-r3-dcp-03-post-write-inspect` · debt-lite |
| 活卡 | `R3_DCP_03_POST_WRITE_INSPECT.md` |
| 模板 | `agents/audit-finding-schema.md` · `agents/audit-coverage-model.md` · `AUDIT.plan.md` §A3 · `DEBT.plan.md` |
| plan_protocol_version | 4.1 |
| 审计日期 | 2026-06-30 |
| worktree | `quant-monitor-desk-wt-dcp03` |
| 分支 | `feature/wave3-r3-dcp-03-post-write-inspect` |

---

## 维度证据

### 变更范围（未提交 diff + DEBT.plan allowed/forbidden）

| 文件 | 角色 | 与 DEBT 边界 |
| --- | --- | --- |
| `tests/test_incremental_post_write_inspect.py` | **新建** 三片集成测（inspect / health / CLI） | allowed |
| `tests/post_write_inspect_support.py` | **新建** bootstrap + bundle helper | allowed（可选） |
| `tests/test_catalog.yaml` | 登记新测 + YAML 全表重排 | allowed（merge 噪声见证据注记） |
| `.trellis/tasks/06-30-wave3-r3-dcp-03-post-write-inspect/**` | 任务包 / execute-evidence | allowed |

**未改（forbidden / 默认不改）：**

| 禁区 | 验证 |
| --- | --- |
| `backend/app/sync/**` | `git diff HEAD -- backend/app/sync` 空 |
| `backend/app/datasources/fetch_ports/*_port.py` | 无 diff |
| `backend/app/db/migrations/**` | 无 diff |
| `specs/datasource_registry/**` | 无 diff |
| `backend/app/ops/db_inspector.py`（E2） | 无 diff |
| `backend/app/ops/data_health_profiles/**`（F0） | 无 diff |
| `scripts/qmd_ops.py`（CLI） | 无 diff |

### AUDIT.plan §A3 核对项

| 检查项 | 结果 | 证据 |
| --- | --- | --- |
| E2/F0 只读边界 | **PASS** | `DbInspector.inspect()` 经 `ConnectionManager.reader()`（`db_inspector.py:196`）；`run_data_health_profile` docstring 声明 read-only，`db_path` 仅 `_schema_hash_coverage_from_db` 用 `reader()`（`data_health_profiles/__init__.py:61-68`）；测 `production_db_mutated is False`（`test_incremental_post_write_inspect.py:105`） |
| 不改 sync 金路径 | **PASS** | sync/runners/orchestrator/watermark 磁盘零 diff；测经 `DataSyncOrchestrator.run_incremental(..., datasource_service=service)`，无 `adapter=` |
| 测试编排不嵌入 runner 默认 hook | **PASS** | `rg post_write_pre_complete_hook` 于新测文件 0 命中；`runners.py` 现有 hook 仍 pytest-only guard（`runners.py:571-575`），本轨未触 |
| 测试仅编排四触点 | **PASS** | `run_incremental`（`post_write_inspect_support.py:94-95` / 主测 `63-70`）→ `DbInspector.inspect`（`65-72`）→ `run_data_health_profile`（`95-103`）→ `qmd_ops db-inspect` subprocess（`119-126`） |
| ops 边界未破坏 | **PASS** | 无 `post_write_hook` 生产默认；inspect/health 未写入 `IncrementalJobRunner`；CLI 显式 `--db` / `--data-root` |
| 隔离库 | **PASS** | `bootstrap_db` 用 `tmp_path/post_write_incr.duckdb`；CLI smoke 传 `str(cm.db_path)`，不触 canonical |

### `architecture-dcp03.md` mermaid 对照

| 序列步骤 | 架构图 | 实现 | 对齐 |
| --- | --- | --- | --- |
| `run_incremental x2` | Incr→DB upsert 幂等 | `run_two_incremental` / 主测双跑 `orch.run_incremental` | ✓ |
| `DbInspector` row_count 稳定 | Insp→DB read-only COUNT | 第一次 incremental 后 inspect + 第二次后 inspect，断言 `row_count` 相等 | ✓（实现比图多一次 before 快照，符合活卡 AC） |
| `max(trade_date)` | Incr→DB SELECT | `ConnectionManager.reader()` 参数化 SQL（`test_incremental_post_write_inspect.py:75-81`） | ✓ |
| `run_data_health_profile` | Health market_bar_p0 | 从 `fetch_log` 组 bundle → `profile_id="market_bar_p0"` | ✓ |
| `qmd_ops db-inspect` | CLI JSON smoke | subprocess `db-inspect --format json`，断言 `security_bar_1d ∈ key_tables` | ✓ |
| 非目标：不嵌 inspect 入 runner | Note | 无 runner/orchestrator 改动 | ✓ |

### 模块触点表（architecture-dcp03 §模块触点）

| 层 | 文件 | 计划 | 实际 |
| --- | --- | --- | --- |
| Tests | `test_incremental_post_write_inspect.py` | 新建 | 新建 ✓ |
| Tests | `post_write_inspect_support.py` | 可选 | 新建 ✓ |
| E2 | `db_inspector.py` | 默认不改 | 未改 ✓ |
| F0 | `data_health_profiles/*` | 默认不改 | 未改 ✓ |
| CLI | `qmd_ops.py` | 默认不改 | 未改 ✓ |

### 独立 pytest 复验（Audit 2026-06-30）

```text
uv run pytest tests/test_incremental_post_write_inspect.py -q
...                                                                      [100%]
3 passed
```

Execute evidence：`research/execute-evidence/s01-green.txt` · `s02-green.txt` · `s03-green.txt` 与上式一致。

### 对抗搜索（计划外 · A3 牵头）

| 类 | 范围 | 结论 |
| --- | --- | --- |
| runner hook 旁路 | `tests/test_incremental_post_write_inspect.py` · `post_write_inspect_support.py` · `backend/app/sync/runners.py` | 无 `post_write_pre_complete_hook` 调用 |
| `adapter=` 金路径 bypass | 新测 + support | 0 命中 |
| good_bundle 跳过 incremental | health 测路径 | 仅 docstring 提及；实际 `build_evidence_bundle_from_fetch_log` 读 `fetch_log` |
| E2/F0 生产写路径 | `db_inspector.py` · `data_health_profiles` diff | 无 diff；`writer/INSERT` grep 于 ops 模块本轨未新增 |
| canonical DB 引用 | 新测 | 全 `tmp_path`；CLI 显式 `--db` |
| bootstrap 漂移 | `post_write_inspect_support.py` vs `test_baostock_incremental_e2e.py` | 逻辑同构（`use_mock=True` · 同 `SyncJobSpec` · 同 upsert kwargs）；**复制**而非 import——见注记，不构成 ops 边界破坏 |

**注记（不计 finding）：** `tests/test_catalog.yaml` 除新增一行外另有全表 YAML 重排（~705 行 churn），属 merge 噪声，不影响 E2/F0/sync 架构边界；建议 merge 前由协调员确认 `loop_maintain` 意图（参照 DCP-02 A1 先例）。

---

## §维度裁决

**PASS**

（§计划内 + §计划外 findings 均为占位行；AUDIT.plan §A3 checklist 满足）

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| — | — | 无 | — | — | — | — |

---

## 计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| — | — | 无 | — | — | — | — |

已对抗搜索：`backend/app/sync/**` · `backend/app/ops/db_inspector.py` · `backend/app/ops/data_health_profiles/**` · `scripts/qmd_ops.py` · 新测/support 全文 · `post_write_pre_complete_hook` / `adapter=` / `good_bundle` grep · mermaid 逐步对照 · 独立 pytest 复跑。

---

## 已通过控制（不计 finding）

- **DEBT forbidden 零触及：** sync · ports · migrations · registry 均无 diff。
- **金路径编排：** `DataSourceService` + `orch.run_incremental`，与 DCP-01 e2e 同族参数。
- **E2/F0 仓内复用：** 无新 inspect/health 实现；测试层接线。
- **health 证据链：** incremental 会话 `fetch_log` → 测试 helper bundle → `market_bar_p0`，非夹具短路。
- **runner hook 隔离：** 生产默认无 post-write inspect；现有 hook 仍 pytest-only fail-closed。
