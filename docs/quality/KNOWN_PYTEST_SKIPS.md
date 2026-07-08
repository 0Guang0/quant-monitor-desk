# 已知 Pytest Skip 登记

> 运维/CI 排障参考。完整审计上下文见 `docs/quality/待修复清单.md` 与 `docs/RESOLVED_ISSUES_REGISTRY.md`。

| 测试                                                                               | Skip 条件                                 | 平台                 | 缓解措施                                                |
| ---------------------------------------------------------------------------------- | ----------------------------------------- | -------------------- | ------------------------------------------------------- |
| `tests/test_ops_db_inspector.py::test_dbInspect_symlinkOutsideDataRoot_notCounted` | `symlinks not supported on this platform` | Windows（常见）      | 在 Linux CI 上运行；符号链接路径 containment 在那里覆盖 |
| `tests/test_raw_store.py::test_save_windowsLongPath_writesSuccessfully`            | `Windows long-path regression only`       | 非 Windows           | Windows 开发机/agent 覆盖 MAX_PATH                      |
| `tests/test_path_compat.py::*`                                                     | `Windows-only`                            | 非 Windows           | 同上                                                    |
| `tests/test_batch25_production_data_gate.py`（条件性）                             | 缺少本地生产 DB 或 `data/raw`             | 无生产产物的开发环境 | 预期行为；gate 仅测本地就绪状态                         |
| `@pytest.mark.network` 子集（24 条）                                               | 默认无 `--run-network`                    | 全平台               | replay/mock 路径已覆盖；live 需 opt-in                  |

**全量套件预期：** `pytest -q` → Windows 上出现 1 个 skip（符号链接测试）+ 24 个 network skip 属正常。

## CI 分层（perf P1/P3）

```bash
# Quick（pre-commit / 开发循环，排除 slow + network）
uv run pytest -q -m "not slow and not network"
# 或 npm run test:quick

# Full（pre-push / CI；本地无 coverage，CI 用 -n auto 并行 + cov）
uv run pytest -q
# 或 npm run test:full

# Parallel full（可选，需 pytest-xdist）
uv run pytest -q -n auto

# Live opt-in
uv run pytest -q --run-network
```

**slow 分层 SSOT：** `tests/slow_tier.py`（`conftest.py` 在 collection 时自动打标）。

当前 slow 覆盖：

- 全部 `*_incremental_e2e.py` replay 路径
- CLI/E2E 慢测：`test_bounded_backfill_cli_e2e.py`、`test_incremental_post_write_inspect.py`、`test_qmd_ops_source_route_db_acceptance.py`、`test_layer1_five_axis_panel_clean_smoke.py`
- 按名称模式：matrix dry-run、baostock CLI nonDryRun、layer1 whitelist row cap、orchestrator backfill/reconcile/servicePath、sync full-load、meta guard 等
- 整模块 slow：`test_sync_binding_executor.py`（单条重集成）
- 显式 `@pytest.mark.slow`：`tests/test_resource_guard.py::test_snapshot_realCall_returnsFiniteMetrics`

**Git hooks：**

| Hook                                  | 命令                                   | 墙钟（本机参考） | 说明                          |
| ------------------------------------- | -------------------------------------- | ---------------- | ----------------------------- |
| **pre-commit**（`.husky/pre-commit`） | `test:quick` + lint-staged + typecheck | ~2.5 min         | 开发循环；排除 slow + network |
| **pre-push**（`.husky/pre-push`）     | `test:full`                            | ~4 min           | 推送前全量；无 coverage       |
| **CI**（`.github/workflows/ci.yml`）  | `pytest -q -n auto --cov=...`          | Linux 更快       | 合并门禁                      |

跳过本地 pre-push：`git push --no-verify`（仅应急；CI 仍会跑 full）。

**性能预算（guard）：** 全量 `pytest -q` ≤ 300s；quick profile ≤ 180s；CI `-n auto` ≤ 240s。

**墙钟 guard（P5 / opt-in）：** 默认不跑；仅 `QMD_PERF_GATE=1` 或 nightly `perf-gate` job：

```bash
# 本地 — 推荐按 profile 单独跑（避免一次等 8–10 分钟）
uv run python scripts/run_perf_gate.py --profile quick      # ~2 min
uv run python scripts/run_perf_gate.py --profile full       # ~4 min
uv run python scripts/run_perf_gate.py --profile ci-parallel

# 全套 sequential（约 quick+full+parallel 墙钟之和）
npm run test:perf-gate

# pytest 契约入口（同 run_perf_gate.py，需 QMD_PERF_GATE=1）
QMD_PERF_GATE=1 uv run python -m pytest -q tests/test_pytest_slow_tier.py -m perf_gate
```

PR / pre-commit **不**启用 `QMD_PERF_GATE`（避免冷启动误杀）。
