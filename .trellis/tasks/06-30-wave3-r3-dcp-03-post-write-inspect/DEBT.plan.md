# Repair/Debt Lite Plan — wave3-r3-dcp-03-post-write-inspect

## Source of truth

- **规划 ID:** R3-DCP-03
- **活卡:** `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_03_POST_WRITE_INSPECT.md`
- **INDEX:** `R3_DCP_TO_ISSUES_INDEX.md` §3
- **base branch:** `master`
- **target branch:** `feature/wave3-r3-dcp-03-post-write-inspect`
- **worktree:** `../quant-monitor-desk-wt-dcp03`
- **owner agent:** Execute agent（Plan 仅交付本文件）

## Boundary

### allowed files

```text
tests/test_incremental_post_write_inspect.py          # 新建主交付
tests/post_write_inspect_support.py                   # 可选：fetch_log → evidence bundle helper
tests/fixtures/data_health/good_bundle/**             # 只读；bundle 格式 SSOT（禁止改夹具语义）
tests/test_catalog.yaml                               # 登记新测；merge 排队
.trellis/tasks/06-30-wave3-r3-dcp-03-post-write-inspect/**
docs/implementation_tasks/.../R3_DCP_03_POST_WRITE_INSPECT.md  # AC 勾选（收尾）
docs/implementation_tasks/.../R3_DCP_TO_ISSUES_INDEX.md          # §3 状态（收尾）
PROJECT_IMPLEMENTATION_ROADMAP.md                     # Wave 3 CLOSED 行（主会话收尾）
docs/.../R3H_PASS_EXECUTION_PLAN.md                   # §3.1（主会话收尾）
```

### optional touch（仅 Plan-Audit 批准后）

```text
backend/app/ops/db_inspector.py   # 仅当必须输出 max(trade_date)；默认禁止
backend/app/ops/data_health_profiles/**  # 默认禁止（本轨只读消费 market_bar_p0）
```

### forbidden files

```text
backend/app/sync/watermark.py
backend/app/sync/runners.py
backend/app/sync/orchestrator.py
backend/app/datasources/fetch_ports/baostock_port.py
backend/app/datasources/fetch_ports/fred_port.py
backend/app/db/migrations/**
data/duckdb/quant_monitor.duckdb
specs/datasource_registry/**          # 本轨不碰 registry 三件套
```

### production/data boundary

- 测试 `tmp_path` 或 `.audit-sandbox`；`QMD_DATA_ROOT` 仅测试显式设置
- **禁止** silent 写 canonical 主库
- inspect / health **只读**

### explicit non-goals

- 新 macro health profile
- 新 `qmd data` 子命令
- 改 DCP-01/02 增量语义
- Wave 4 Tier A 扩展

---

## Vertical slices（Execute 阶段 · 共 3 片）

| Slice | Source ID | AC | Allowed files | Forbidden files | Verification | Evidence |
| ----- | --------- | --- | ------------- | --------------- | ------------ | -------- |
| **S01-POST-INCR-INSPECT** | 活卡 §5 · INDEX §3 | 2× incremental 后 **`DbInspector` 报告** `security_bar_1d.row_count` 稳定（非仅 SQL COUNT）；`max(trade_date)` read-only SQL | `tests/test_incremental_post_write_inspect.py` | sync/port | `uv run pytest tests/test_incremental_post_write_inspect.py -k postWriteInspect -q` | `research/execute-evidence/s01-green.txt` |
| **S02-HEALTH-PROFILE** | 活卡 §5 | 2× incremental 后：从 `fetch_log.raw_file_paths` 经测试 helper 组 **evidence bundle** → `run_data_health_profile(market_bar_p0, db_path=同库)` 无未处理异常；**禁止**仅用 `good_bundle` 夹具跳过 incremental 会话 | 同上 + 可选 `post_write_inspect_support.py` | 新 profile 模块；改 `good_bundle` | `uv run pytest tests/test_incremental_post_write_inspect.py -k health -q` | `s02-green.txt` |
| **S03-CLI-SMOKE** | 活卡 §5 | `qmd_ops db-inspect --format json` exit 0；JSON 含 `security_bar_1d` | 同上 | 新 CLI 实现 | `uv run pytest tests/test_incremental_post_write_inspect.py -k cli -q` | `s03-green.txt` |

> Plan 阶段 **P1 调研 + P2 Plan-Audit** 由主会话完成，不计入上表。

---

## Execute 顺序

```text
S01 → S02 → S03（可同文件 TDD 递进）
```

每片：**RED**（失败测证明 AC）→ **GREEN** → 本片 pytest → evidence txt。

---

## Merge gate

| 检查 | 命令 |
| ---- | ---- |
| 靶向测试 | `uv run pytest tests/test_incremental_post_write_inspect.py -q` |
| 全量 | `uv run pytest -q` exit 0 |
| Loop maintain | `uv run python scripts/loop_maintain.py`（新测登记后） |
| GitNexus | 改 symbol 前 `impact()`；提交前 `detect_changes()` |

---

## Audit / Repair 承接

- Execute 完成后：A1–A8（`AUDIT.plan.md` 待补）
- P6 Repair：ledger 关账 + pytest 全绿 → 主会话 merge + 归档
- Wave 3 CLOSED：更新路线图 / PASS plan / INDEX checklist

---

## 调研依赖（Execute Boot 必读）

1. `research/plan-boot.md`
2. `research/reference-adoption-dcp03.md`
3. `research/architecture-dcp03.md`
4. 活卡 + INDEX §3
5. `tests/test_baostock_incremental_e2e.py` · `tests/test_ops_db_inspector.py`
6. `db_inspector.py` · `data_health_profiles/__init__.py`
7. **`research/execute-reference-read-evidence.md`** — Execute RED 前填实读行（仅 `参考项目/**`；仓内路径不得标 L1/L2/L3）

**参考项目：** 三等级仅外部；本轨 **不新增 L2 拷贝**（EasyXT 规则已在 `market_bar_p0`；JQ2PTrade `--db` 已在契约）。`参考项目/**` 不可见时登记 `MISSING_REFERENCE_TREE` + R3D 引用，**不得**空白开工。
