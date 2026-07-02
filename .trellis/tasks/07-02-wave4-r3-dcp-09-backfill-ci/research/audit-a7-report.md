# Audit A7 — 运维 / 主库零污染（R3-DCP-09）

| 元信息   | 值                                              |
| -------- | ----------------------------------------------- |
| 维度     | A7 运维 — 隔离库 backfill + 主库 fingerprint    |
| 任务     | `07-02-wave4-r3-dcp-09-backfill-ci`             |
| 协议     | `plan_protocol_version: 4.1`                    |
| 模板     | `agents/database-administrator.md`              |
| 审计日期 | 2026-07-02                                      |
| 工作目录 | `quant-monitor-desk-wt-dcp09`                   |

> **AUDIT.plan §2 A7 焦点：** 主库零污染（验收 fingerprint）；backfill 写 clean 须隔离库。

---

## 维度证据 §3.7

### 1. GitNexus（必用）

| 查询 | 目标 | 结论 |
| ---- | ---- | ---- |
| `query` · `backfill sandbox QMD_DATA_ROOT canonical main DB fingerprint` | 隔离 / 验收流 | 返回 `live_pilot_phase3`、layer1 `zeroMutation`、`production_equivalent_smoke` 等；**未**直接索引 `backfill_plan` / `assert_sandbox_db_allowed`（索引 stale 或符号未入库） |
| `query` · `wave3_isolated_production_acceptance canonical_main_db` | 验收 fingerprint | 关联 `config._path_env`、`init_db.py`、`layer1 data_root_content_fingerprint` |
| `impact` · `backfill_plan` | 调用链 | **Target not found**（同上） |
| `context` · `assert_sandbox_db_allowed` | sandbox guard | **Symbol not found** |
| 代码对照（人工） | `data_commands.backfill_plan` L633–648 | 非 dry-run：` _require_baostock_sync_operator_or_sandbox` + `assert_sandbox_db_allowed(..., allow_isolated_data_root=True)` |

### 2. Backfill 隔离门控（cli-sandbox）

| 步骤 | 命令 | exit | 关键证据 |
| ---- | ---- | ---- | -------- |
| 非 sandbox 非 dry-run 拒写 | `uv run python -m backend.app.cli.main data backfill ... --no-dry-run`（无 `QMD_DATA_ROOT`） | **2** | `USER_AUTH_REQUIRED` · message 含 `.audit-sandbox` |
| 隔离 pytest 回归 | `uv run pytest tests/test_qmd_data_backfill_cli.py tests/test_bounded_backfill_cli_e2e.py -q` | **0** | 4 passed；含 `test_qmd_data_backfill_without_dry_run_requires_sandbox`、e2e 2+ shards + 二次跑幂等 |
| e2e 二次跑幂等 | `test_bounded_backfill_cli_e2e` | — | 第二次 `backfill_plan` 后 `security_bar_1d` 行数不变 |

### 3. init/migrate 幂等（audit-sandbox）

| 步骤 | 命令 | exit | 关键证据 |
| ---- | ---- | ---- | -------- |
| init 第 1 次 | `QMD_DATA_ROOT=<task>/.audit-sandbox/a7-ops/data uv run python scripts/init_db.py --db <sandbox>/quant_monitor.duckdb` | **0** | `applied ['001_foundation', …, '015_dcp05_tier_a_clean']` |
| init 第 2 次 | 同上 | **0** | `applied none (up to date)` |

### 4. 验收 fingerprint（AUDIT.plan A7 核心）

| 步骤 | 命令 | exit | 关键证据 |
| ---- | ---- | ---- | -------- |
| wave3 isolated `--quick`（干净 shell，无 `QMD_DATA_ROOT`） | `uv run python scripts/wave3_isolated_production_acceptance.py --quick` | **1** | evidence: `.audit-sandbox/wave3-acceptance-20260702T095857Z/acceptance_evidence.json` · `canonical_main_db_*` → `…/data/duckdb/quant_monitor.duckdb` · `main_db_pollution: false` · 唯一失败步 `loop_maintain_check`（audit-sandbox pytest 遗留 MASTER.plan，非 DB 面） |
| **对抗：shell 预置 `QMD_DATA_ROOT`** | 同上，但 shell 已 `export QMD_DATA_ROOT=<task>/.audit-sandbox/a7-ops/data` | **1** | evidence: `wave3-acceptance-20260702T095633Z` · **`canonical_main_db_*` 路径错误** → 指向 a7-ops 隔离库而非 `PROJECT_ROOT/data/duckdb/` · `main_db_pollution: false`（假阴性风险） |
| `config` 行为复现 | `QMD_DATA_ROOT=<sandbox> uv run python -c "from backend.app.config import DATA_ROOT, PROJECT_ROOT; …"` | **0** | `DATA_ROOT` = sandbox 路径；`PROJECT_ROOT/data/duckdb/…` 为应有 canonical |

### 5. 对抗性 DOUBT 结论

| 问题 | 结论 |
| ---- | ---- |
| 第二次 init 是否仅不报错？ | **否** — 第二次 `applied none`，DB 文件存在且 migration 已到顶 |
| backfill 能否 silent 写主库？ | **CLI 层 fail-closed** — 非 sandbox 抛 `USER_AUTH_REQUIRED`；e2e 仅写 `tmp_path/.audit-sandbox` |
| fingerprint 能否在 operator 已设 `QMD_DATA_ROOT` 时仍保证主库零污染？ | **不能可靠保证** — 验收脚本用 `config.DATA_ROOT`（随 env 变）而非硬编码 `PROJECT_ROOT/data`；见 §计划内 A7-P1-001 |
| 第二次 backfill 是否破坏数据？ | e2e 证明行数幂等 |

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID        | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --------- | --- | ---- | ---- | ---- | -------- | ---- |
| A7-P1-001 | P1  | 验收 fingerprint 随 `QMD_DATA_ROOT` 漂移，主库零污染门禁可假阴性 | `scripts/wave3_isolated_production_acceptance.py:186-188` · `scripts/wave3_live_production_acceptance.py:139-141` · `backend/app/config.py:37` | `canonical_main = CONFIG_DATA_ROOT / "duckdb" / …`；`DATA_ROOT` 绑定 `QMD_DATA_ROOT`；operator/backfill 作业常预置 env | 改为 `(PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb").resolve()`（与 `rehearsal_runner` L92 `canonical_prod` 一致）；**不要**用 `config.DATA_ROOT` | 1) shell 设 `QMD_DATA_ROOT=<任意 sandbox>` 后跑 `wave3_isolated --quick`，evidence 中 `canonical_main_db_before.path` 须为 `…/data/duckdb/quant_monitor.duckdb`；2) 新增/扩展 pytest 断言 fingerprint 路径不随 env 变 |
| A7-P2-001 | P2  | backfill 切片缺「主库 fingerprint 不变」回归测 | `tests/test_bounded_backfill_cli_e2e.py` · AUDIT.plan §2 A7 | e2e 只验隔离库行数幂等，未对 `PROJECT_ROOT/data/duckdb` 做 before/after hash | 在 e2e 或新 `test_*backfill*main*db*` 中：可选创建 stub canonical 文件，跑 `--no-dry-run` backfill 后 assert canonical sha256/mtime 不变 | `uv run pytest tests/test_bounded_backfill_cli_e2e.py -q`（扩展后） |

---

## 计划外发现

| ID        | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --------- | --- | ---- | ---- | ---- | -------- | ---- |
| A7-P2-002 | P2  | `wave3_*` 子进程 `-m pytest` 依赖 venv 已装 dev extra | `scripts/wave3_isolated_production_acceptance.py:98-116` · `pyproject.toml` `[project.optional-dependencies] dev` | `sys.executable -m pytest` 要求 `.venv` 含 pytest；默认 `uv sync` 不含 dev；仅 `uv run pytest` 可用 | 文档 `docs/ops/nightly_ci.md` / 验收脚本 docstring 写明 `uv sync --all-extras` 或 CI 式 `pip install -e ".[dev]"`；或子进程改 `uv run pytest` | 裸 `uv sync` 后 `python scripts/wave3_isolated_production_acceptance.py --quick` 的 pytest 步骤 exit 0 |
| A7-P3-001 | P3  | dry-run / 非 dry-run sandbox 判定实现不一致 | `data_commands.backfill_plan:633-640` · `tier_a_sync_router._require_audit_sandbox_data_root:31` | dry-run 用 `as_posix()` 子串 `.audit-sandbox`；非 dry-run 用 `Path.parts` 集合 | 统一为 `parts` 判定（ponytail：一处 helper） | `uv run pytest tests/test_qmd_data_backfill_cli.py -q` |

已对抗搜索：`data_commands.backfill_plan` · `rehearsal_runner.assert_sandbox_db_allowed` · `wave3_*_production_acceptance.py` · `tests/test_qmd_data_backfill_cli.py` · `tests/test_bounded_backfill_cli_e2e.py` · `tests/test_wave3_isolated_acceptance_quick_profile.py`（仅验 step 列表，无 fingerprint） · GitNexus query ×3。
