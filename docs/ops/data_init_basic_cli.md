# QMD Data Init-Basic CLI 设计

> 状态：面向 `qmd data init-basic` 的运维设计（Round 2.6+）。非运行时 migration 权威。
>
> 契约：`specs/contracts/data_cli_contract.yaml` → `qmd data init-basic`。

## 1. 决策摘要

`qmd data init-basic` 用于在本地 DuckDB 文件上应用 schema migration，并可选同步 `source_registry`。**不是**数据抓取或 clean 写入命令。

默认姿态：**仅 dry-run** — 除非运维人员显式关闭 dry-run，否则不对文件系统或 DB 做任何变更。

## 2. 命令形态

```bash
qmd data init-basic --dry-run
qmd data init-basic --no-dry-run --db-path data/duckdb/quant_monitor.duckdb
```

过渡期打包入口：

```bash
python -m backend.app.cli.init_db --db <path> --sync-registry
```

## 3. 参数与行为

| 模式     | `dry_run` | 行为                                                                                                              |
| -------- | --------- | ----------------------------------------------------------------------------------------------------------------- |
| 默认     | `true`    | 仅返回计划步骤；提示信息指向 `qmd-init-db`                                                                        |
| 确认写入 | `false`   | 创建父目录；打开 `ConnectionManager.writer()`；执行 `apply_migrations`；以 `tombstone_missing=True` 同步 registry |

确认写入时允许的范围（契约）：仅 `schema`、`registry`。禁止 fetch、clean-write、live 源启用。

## 4. 安全不变量

1. `data_commands.init_basic` 默认 `dry_run=True`。
2. 写入路径使用 `ConnectionManager.writer()` — 除 migration/registry 引导外，不得绕过 WriteManager 写生产表。
3. 运维须将 `--no-dry-run` 视为显式确认；回滚见备份策略（`docs/ops/design/backup_and_recovery.md`）。
4. 经 CLI envelope 路由的失败须 surfaced `error_code` + `docs_anchor`（见 `docs/ops/ERROR_CODE_GUIDE.md`）。

## 5. 与其他工具的关系

| 工具                  | 回答的问题                                   |
| --------------------- | -------------------------------------------- |
| `qmd data init-basic` | 是否创建/迁移 DB 并同步 registry？           |
| `qmd ops db-inspect`  | 只读元数据/证据是否存在？                    |
| `qmd data health`     | 证据是否满足域质量规则（只读）？             |
| `qmd data sync`       | 抓取 + 分阶段入库（受 ResourceGuard 门禁）？ |

## 6. 实现位置

- `backend/app/cli/data_commands.py::init_basic`
- 测试：`tests/test_qmd_data_cli.py::test_initBasic_noDryRun_syncsRegistry`、`tests/test_qmd_data_cli.py`
