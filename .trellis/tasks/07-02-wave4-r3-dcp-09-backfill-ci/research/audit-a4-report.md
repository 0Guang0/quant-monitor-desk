# Audit A4 — 代码质量 / backfill replay e2e clean 断言

| 字段                  | 值                                              |
| --------------------- | ----------------------------------------------- |
| 维度                  | A4（audit-quality）                             |
| 任务                  | 07-02-wave4-r3-dcp-09-backfill-ci               |
| 分支 / worktree       | feature/wave4-r3-dcp-09-backfill-ci @ wt-dcp09  |
| plan_protocol_version | 4.1                                             |
| 日期                  | 2026-07-02                                      |
| 模板                  | `agents/code-reviewer.md`                       |

---

## 维度证据

### Boot / 对抗动作

- 已 Read：`agents/audit-adversarial-authority.md`、`agents/audit-finding-schema.md`、`AUDIT.plan.md` §2 A4、`research/00-EXECUTION-ENTRY.md` §1–§2、`research/to-issues-slices.md` S02/S05、`docs/decisions/ADR-030-bounded-backfill-cap-and-ci-nightly.md`。
- 已审 diff 范围：`git status` 工作区全部 DCP-09 变更（分支与 `master` 同 HEAD，实现均为未提交 diff）。
- 已对照增量先例：`tests/test_baostock_incremental_e2e.py`（fixture `close` 断言 + 幂等）。

### AUDIT.plan §2 A4 要点对照

| 要点 | 证据 | 结论 |
| ---- | ---- | ---- |
| backfill replay e2e | `tests/test_bounded_backfill_cli_e2e.py` | 有；2 shard + `SHARD_COMPLETE` + 幂等 |
| 写 clean（隔离库） | e2e 查 `security_bar_1d`；`QMD_DATA_ROOT` 在 `.audit-sandbox`；`assert_sandbox_db_allowed` @ `data_commands.py` L640–648 | 路径正确 |
| 隔离库 | `_require_baostock_sync_operator_or_sandbox` @ L294–311；`test_qmd_data_backfill_without_dry_run_requires_sandbox` | gate 有测 |

### git diff 摘要（质量相关）

| 区域 | 变更 |
| ---- | ---- |
| `backend/app/cli/data_commands.py` | 新增 `backfill_plan`（cap / dry-run / sandbox gate / 金路径） |
| `backend/app/ops/baostock_incremental_run.py` | 新增 `run_baostock_bar_backfill` |
| `backend/app/sync/jobs.py` | `plan_backfill_shards` + `max_shards` / `truncate_to_cap` |
| `backend/app/sync/orchestrator.py` | `run_backfill` datasource_service 金路径（既有，本票复用） |
| `tests/test_bounded_backfill_*` · `test_qmd_data_backfill_cli.py` | cap + e2e + CLI |
| `tests/test_wave3_*` · `test_nightly_ci_manifest.py` | quick / findings gate / nightly 清单 |
| `scripts/wave3_*_production_acceptance.py` | `--quick` / `--fail-on-severity` |
| `.github/workflows/nightly.yml` · `docs/ops/nightly_ci.md` | nightly 双轨 |

### 五轴审查（关键文件）

| 轴 | 评估 | 要点 |
| -- | ---- | ---- |
| **正确性** | 良（实现）/ 中（测试） | 金路径 `backfill_plan` → `run_baostock_bar_backfill` → `orch.run_backfill` + `DataSourceService`；cap fail-closed @ `jobs.py` L159–170。e2e 断言偏弱（见 findings）。 |
| **错误处理** | 良 | `BackfillShardCapExceededError` → `CliFailure(BACKFILL_CAP_EXCEEDED)`；非 sandbox 非 dry-run → `USER_AUTH_REQUIRED`；`ResourceGuard` / `route_status` fail-closed。 |
| **可读性** | 良 | `backfill_plan` 结构与 `sync_baostock_incremental` 对齐；ADR-030 锚点清晰。 |
| **架构** | 良（ponytail） | Plan D2 有意将 `max_shards` 留在 planner+CLI；runner 吃已截断 `date_end`。ops 直调仍可绕过 cap（计划外 finding）。 |
| **安全（局部）** | 可接受 | 默认 dry-run；非 dry-run 须 `.audit-sandbox` 路径；无密钥进 diff。 |
| **性能** | 可接受 | 有界 shard；replay e2e 隔离 tmp；无新无界 I/O 热点。 |

### 测试复验（本维独立跑测）

```text
uv run pytest tests/test_bounded_backfill_cap.py tests/test_bounded_backfill_cli_e2e.py \
  tests/test_qmd_data_backfill_cli.py tests/test_wave3_isolated_acceptance_quick_profile.py \
  tests/test_wave3_live_acceptance_findings_gate.py tests/test_nightly_ci_manifest.py \
  tests/test_r3_dcp09_registry_closure.py -q
→ 13 passed
```

### §3.4 轴表

| 轴 | 发现 | 证据 |
| -- | ---- | ---- |
| 正确性 | backfill e2e 仅 COUNT≥2，未绑 fixture `close` | `test_bounded_backfill_cli_e2e.py` L111–116 |
| 正确性 | 非 dry-run e2e 未走 subprocess CLI | `test_bounded_backfill_cli_e2e.py` L97 vs `test_qmd_data_backfill_cli.py` L45–55 |
| 架构 | ops/runner 无 `max_shards` 二次校验 | `baostock_incremental_run.py` L133；`runners.py` L646 |
| 测试 | live gate 未测主库污染 CRITICAL | `test_wave3_live_acceptance_findings_gate.py`；`wave3_live_production_acceptance.py` L454–456 |

### 做得好的地方

- `backfill_plan` dry-run JSON 含 `clean_table`、`shards`、`effective_date_end`，可审计。
- cap 契约 `bounded_backfill_cap.yaml` + `test_bounded_backfill_cap.py` 双层 fail-closed / truncate 单测齐全。
- e2e 覆盖 2+ `SHARD_COMPLETE` 与幂等行数稳定，隔离库路径正确。
- nightly / quick / findings gate 均有最小 manifest 或 helper 单测，五字段 docstring 齐全。

### DOUBT（错误处理 / 边界）

已搜索：`backfill_plan`、`run_baostock_bar_backfill`、`BackfillShardRunner.run`、`test_bounded_backfill_cli_e2e.py`、`test_wave3_live_acceptance_findings_gate.py`。

- **边界遗漏（计划外）：** `run_baostock_bar_backfill` 与 `BackfillShardRunner` 内 `plan_backfill_shards` 不传 `max_shards`（`baostock_incremental_run.py` L133、`runners.py` L646）。Plan D2 有意将 cap 留在 CLI，但 ops/runner 直调大窗仍可无 shard 数上限（仅 31 天/片），与 ADR-030「单次 invocation shard 上限」语义存在防御纵深缺口。
- **脆弱断言（计划内）：** e2e 未断言 replay `close=1405/1415`，错误 promote 或空行膨胀仍可通过 `row_count >= 2`（`test_bounded_backfill_cli_e2e.py` L111–116）。

---

## §维度裁决

**FAIL**

（§计划内 2 条 + §计划外 2 条非占位 finding）

---

## 计划内问题

| ID       | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| -------- | --- | ---- | ---- | ---- | -------- | ---- |
| A4-P2-01 | P2  | backfill e2e 仅 COUNT≥2，未绑 fixture 字段 | `tests/test_bounded_backfill_cli_e2e.py` L111–116；对照 `tests/test_baostock_incremental_e2e.py` L49–57 | S02 AC「replay → clean upsert」未对齐增量 e2e 先例；`close` 错映射或假行仍可绿 | 在 e2e 中 `SELECT trade_date, close FROM security_bar_1d WHERE instrument_id=? AND trade_date IN ('2024-06-25','2024-07-15')` 断言 `close` 为 1405.0 / 1415.0（与 `_write_two_shard_replay` L24–44 一致） | `uv run pytest tests/test_bounded_backfill_cli_e2e.py -q` |
| A4-P2-02 | P2  | S02 e2e 非 dry-run 绕过 subprocess CLI | `tests/test_bounded_backfill_cli_e2e.py` L97 直调 `data_commands.backfill_plan`；`test_qmd_data_backfill_cli.py` 仅 dry-run 走 `_run_qmd_data` | `main.py` backfill 参数解析 / `--no-dry-run` / exit code 链未在 e2e 覆盖；CLI 接线回归可漏 | 新增用例：`_run_qmd_data("backfill", ..., "--no-dry-run")` + sandbox `QMD_DATA_ROOT` + replay patch，断言 exit 0 且 stdout JSON `job_status=COMPLETED`；或把现有 e2e 改为 subprocess 路径 | `uv run pytest tests/test_bounded_backfill_cli_e2e.py tests/test_qmd_data_backfill_cli.py -q` |

---

## 计划外发现

| ID       | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| -------- | --- | ---- | ---- | ---- | -------- | ---- |
| A4-P2-03 | P2  | ops/runner 可绕过 CLI `max_shards` cap | `backend/app/ops/baostock_incremental_run.py` L133；`backend/app/sync/runners.py` L646 | Plan D2 将 cap 止于 CLI+planner，金路径 runner 重算 shard 无 `max_shards`；直调 `run_baostock_bar_backfill` 或大窗 `run_backfill` 可超「单次 invocation 默认 3 片」意图 | ponytail 选项 A：`run_baostock_bar_backfill` 增加 `max_shards` 并传入 `plan_backfill_shards`；选项 B：在 `BackfillShardRunner.run` 读取 cap SSOT 默认 `DEFAULT_MAX_BACKFILL_SHARDS` fail-closed。至少补单测：不经 CLI 的大窗调用应抛 `BackfillShardCapExceededError` | `uv run pytest tests/test_bounded_backfill_cap.py tests/test_sync_orchestrator.py -k backfill -q` |
| A4-P2-04 | P2  | live findings gate 未测主库污染 CRITICAL | `tests/test_wave3_live_acceptance_findings_gate.py`（仅 helper 单测）；`scripts/wave3_live_production_acceptance.py` L448–456 | ADR-030 §4 / 活卡要求 `LIVE-ACC-MAIN-DB-POLLUTION` 始终 CRITICAL；当前测试未覆盖 fingerprint 变化 → severity gate 交互 | 新增单测：构造 `report` 含 `canonical_main_db_before/after` 不同 fingerprint，断言脚本产出 `LIVE-ACC-MAIN-DB-POLLUTION` 且 `_count_severity_gate_violations` 在 `fail_on={CRITICAL}` 时 ≥1；或抽取 `_main_db_pollution_finding` 可测函数 | `uv run pytest tests/test_wave3_live_acceptance_findings_gate.py -q` |

已对抗搜索：`tests/test_bounded_backfill*.py`、`tests/test_qmd_data_backfill_cli.py`、`tests/test_wave3_*`、`tests/test_nightly_ci_manifest.py`、`backend/app/cli/data_commands.py`（`backfill_plan`）、`backend/app/ops/baostock_incremental_run.py`、`backend/app/sync/jobs.py`、`backend/app/sync/runners.py`（`BackfillShardRunner`）、`scripts/wave3_*_production_acceptance.py`、`.github/workflows/nightly.yml`、`docs/decisions/ADR-030-*.md`。

---

## Verification Story

| 项 | 结果 |
| -- | ---- |
| 测试 reviewed | 是 — DCP-09 全部新增测试模块 + `backfill_plan` / ops 金路径 |
| Build verified | 是 — 本维 pytest 子集 13 passed |
| Security checked | 是 — sandbox gate、默认 dry-run、无密钥 |
