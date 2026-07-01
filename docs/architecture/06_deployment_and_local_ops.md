# 部署与本地运维入口

> 本文件是部署/运维入口，完整运维细节见 `docs/ops/ops_and_performance_v1_2.md`。

## 当前阶段部署形态

- 本地优先。
- DuckDB 单写多读。
- 前端与 Agent 只通过 FastAPI 读取。
- 文件系统保存原始文件、审计日志、缓存、备份和 Parquet 归档。

## 运维文件

- 完整运维手册：`docs/ops/ops_and_performance_v1_2.md`
- 自检与审计清单：`docs/quality/self_check_and_audit.md`
- 数据同步速查：`docs/ops/data_sync_quick_reference.md`（含 **Tier A 11 源** `--source-id` 增量 CLI · R3-DCP-05）
- 错误码与排障：`docs/ops/ERROR_CODE_GUIDE.md`、`docs/ops/TROUBLESHOOTING.md`
- qmt_xqshare 可选远程源：`docs/ops/qmt_xqshare_setup.md`

## 本地数据根与生产路径（ACC-USER-LIVE-PATH）

- **Canonical 生产 DuckDB 路径（护栏拒绝写入）：** `<PROJECT_ROOT>/data/duckdb/quant_monitor.duckdb`
- **`QMD_DATA_ROOT`：** 可指向任意隔离目录（如 `.audit-sandbox/user-live`）；验收/排练须使用 `.audit-sandbox/wave3-acceptance-*` 等显式隔离树
- **勿混淆：** `DATA_ROOT` 在 audit-sandbox 下 ≠「已授权生产 live」；R3G 排练仍拒绝 `DEFAULT_PRODUCTION_DB` 路径

## 运维逃生口（WAVE-B-HYG-03）

- **`QMD_SYNC_ALLOW_ADAPTER=1`：** 仅紧急运维；绕过 sync orchestrator 的 adapter 旁路 guard。**不得**作为 Wave 4 PASS 或 production-live 依据；部署检查须确认未在生产环境默认开启

## CI 一键初始化（R2-GAP-1）

```bash
uv run python scripts/init_db.py --sync-registry
```

## CI perf budget（R3-B25-PERF-BUDGET-01）

```bash
uv run python scripts/ci_perf_budget_artifact.py
```

产物：`.audit-sandbox/r3b275-audit/production_equivalent_smoke_budget.json`（隔离库 · 不授权 live 源）

## Round2.6 部署补充：平台矩阵与 optional extras

默认部署仍为 local-first / eco mode。新增真实数据源、远程 QMT、回测、Agent 或 docs site 能力时，必须遵守：

- 平台数据源矩阵：`specs/contracts/platform_source_matrix.yaml`。
- 依赖分层契约：`specs/contracts/dependency_extras_contract.yaml`。
- QMT / qmt_xqshare 相关能力默认禁用，必须用户确认授权。
- 重型依赖不得进入 default install；必须放入 optional extra 并说明原因。
- `pyproject.toml`、`package.json`、`package-lock.json` 只有在实现阶段确有需要且用户确认后才允许修改。

平台边界摘要：

| Source          | Windows                   | macOS/Linux               | Default                 |
| --------------- | ------------------------- | ------------------------- | ----------------------- |
| `baostock`      | 可用                      | 可用                      | enabled                 |
| `akshare`       | 可用                      | 可用                      | validation / controlled |
| `qmt_xtdata`    | 用户本机授权后可用        | 不默认可用                | disabled                |
| `qmt_xqshare`   | 配置远程 host/port 后可选 | 配置远程 host/port 后可选 | disabled                |
| `yahoo_finance` | 可选验证源                | 可选验证源                | disabled                |

Phase A 不修改依赖文件、不新增外部服务、不启用任何远程源。
