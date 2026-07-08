# QMD Ops DB Inspect CLI 设计

> 状态：Round 3 早期规划的用户冻结设计输入。本文档非运行时代码，不参与 DB migration。
>
> 范围：长期、local-first、只读运维 CLI，用于检查本地 DuckDB 及相邻 data-root 证据。
>
> 契约：`specs/contracts/ops_db_inspect_contract.yaml`。

## 1. 决策摘要

DB inspect 工具是**长期正式只读运维工具**，不是 Round 3 一次性草稿脚本。

最终命令族：

```bash
qmd ops db-inspect
```

Round 3 v1 在打包未就绪时可用过渡脚本入口：

```bash
python scripts/qmd_ops.py db-inspect
```

过渡脚本必须调用与最终 console 脚本相同的后端实现模块，不得成为独立实现路径。

## 2. 第一性原则

工具安全地回答一个问题：

> 在不改变任何东西的前提下，本地项目数据库与 data root 当前能证明什么？

因此不变量为：

1. 以只读模式打开 DuckDB。
2. 永不变更生产 DB。
3. 永不触发 migration。
4. 永不触发外部网络 fetch。
5. 默认不启用 QMT / xqshare / Yahoo / 券商终端访问。
6. v1 不执行用户提供的自由 SQL。
7. 不打印 secret、token、凭证或大段原始数据行。
8. 产出 Plan / Audit 可追溯到 Round 3 deferred 项的审计友好证据。

## 3. 参考采纳边界

外部参考落地任务：`R3-REF-OPS-DB-DATA-HEALTH`（`docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_ops_db_data_health_reference.md`）。机器追溯：`specs/contracts/ops_db_inspect_contract.yaml` 的 `reference_landing`。

| 参考                           | URL                                           | db-inspect v1 采纳                        | 延后至                                                         |
| ------------------------------ | --------------------------------------------- | ----------------------------------------- | -------------------------------------------------------------- |
| EasyXT 数据完整性 / 诊断       | `https://github.com/quant-king299/EasyXT`     | 仅元数据 inspect；PASS/WARN/FAIL 状态词汇 | 域规则见 `docs/ops/data_health_cli.md`（缺失日、OHLC、离群值） |
| JQ2PTrade 本地 DuckDB 路径覆盖 | `https://github.com/quant-king299/JQ2PTrade`  | `--db` 只读路径覆盖                       | —                                                              |
| ptqmt-site 本地/隐私文档       | `https://github.com/quant-king299/ptqmt-site` | —（db-inspect 仅输出 JSON）               | 离线 Markdown/HTML 见 `docs/ops/ops_report_cli.md`             |

| 参考模式                       | 采纳                                                      | 不采纳                                                                                |
| ------------------------------ | --------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| EasyXT 数据完整性 / 诊断       | 高级检查类别落在 data-health 设计，非 db-inspect v1       | 交易、下单、GUI/QMT 自动登录、硬编码本地路径、单一 stock-daily 表假设、字符串拼接 SQL |
| JQ2PTrade 本地 DuckDB 路径覆盖 | `--db` / `--duckdb-path` 风格本地 DB 覆盖与可重复本地验证 | 回测引擎、策略转换、PTrade 仿真循环                                                   |
| ptqmt-site 本地/隐私文档       | 报告 CLI 中的 local-only 隐私表述                         | 在线站点形态或交易平台教程内容                                                        |

采纳规则：仅借鉴检查概念与 local-first UX；通过本项目契约、schema、资源边界与当前任务追溯实现。

## 4. 最终目标形态

最终运维 CLI 族应为：

```bash
qmd ops env-doctor
qmd ops db-inspect
qmd data health
qmd source probe
qmd ops source-health snapshot
qmd ops report
```

Round 3 v1 仅授权实现 `qmd ops db-inspect`。其余为未来阶段，不得作为 v1 一部分静默实现。

| 命令                             | 最终目的                                                    | 实现阶段                                                                                                 |
| -------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `qmd ops db-inspect`             | 只读 DB 与 data-root 证据检查                               | Round 3 Batch 1 v1                                                                                       |
| `qmd ops env-doctor`             | 本地环境、依赖、配置与安装检查                              | Round 5 / release-readiness                                                                              |
| `qmd data health`                | 域感知数据质量（缺失日、OHLC 合法性、重复键、as-of 泄漏等） | Batch 6 Phase C；设计：`docs/ops/data_health_cli.md`；规则：`data_quality_rules.yaml` `ops_cli_profiles` |
| `qmd source probe`               | 路由预览与用户授权 staging 源探针                           | Round 3 Batch 1 扩展或 Batch 6（源授权规则冻结后）                                                       |
| `qmd ops source-health snapshot` | 预览及后续持久化 source health 指标                         | Batch 6（`source_health_snapshot` migration 设计之后）                                                   |
| `qmd ops report`                 | 将 JSON 证据转为本地 Markdown / HTML 报告                   | Round 5 Phase E；设计：`docs/ops/ops_report_cli.md`                                                      |

## 5. Round 3 v1 范围

Round 3 v1 仅实现只读 DB inspect 最小闭环。

### 5.1 v1 必须回答

1. DB 文件是否存在？
2. 能否只读打开？
3. 有哪些表？
4. 各关键表行数？
5. DB 是否像仅 schema / 空数据？
6. 项目 data root 是否含 raw / parquet 证据？
7. 按元数据，最新 fetch、sync job、validation、conflict、manual review、write 证据行是什么？

### 5.2 v1 不得实现

- 自由 SQL 执行。
- 默认原始行浏览。
- 外部网络源探针。
- QMT / xqshare / Yahoo live 验证。
- OHLC、缺失交易日等数据质量域规则。
- `source_health_snapshot` 表写入。
- Markdown / HTML 报告生成。
- 任何 migration 或 schema 自动修复。

## 6. CLI 契约

### 6.1 最终命令

```bash
qmd ops db-inspect \
  --db data/duckdb/quant_monitor.duckdb \
  --data-root data \
  --format text
```

### 6.2 过渡命令

```bash
python scripts/qmd_ops.py db-inspect \
  --db data/duckdb/quant_monitor.duckdb \
  --data-root data \
  --format json
```

过渡命令仅允许作为 `backend/app/ops/db_inspector.py` 的薄包装。

### 6.3 参数

| 参数                   | 必填 | 默认                                                                                                       | v1 行为                                                        |
| ---------------------- | ---- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `--db`                 | 否   | `$QMD_DATA_ROOT/duckdb/quant_monitor.duckdb`；未设 `QMD_DATA_ROOT` 时为 `data/duckdb/quant_monitor.duckdb` | 只读目标 DB 路径                                               |
| `--data-root`          | 否   | `$QMD_DATA_ROOT`；未设时为 `data`                                                                          | 扫描 raw/parquet/文件证据的根目录                              |
| `--format`             | 否   | `text`                                                                                                     | `text` 或 `json`                                               |
| `--output`             | 否   | stdout                                                                                                     | JSON/text 可选输出文件；父目录须已存在（Phase A 不创建父目录） |
| `--limit`              | 否   | `20`                                                                                                       | 每类证据预览元数据行上限；硬顶 `100`                           |
| `--include-path-check` | 否   | v1 默认启用                                                                                                | 在 data-root 安全子目录下统计 raw/parquet 候选文件             |
| `--profile`            | 否   | 当前 `QMD_RESOURCE_PROFILE` 或 `eco`                                                                       | 适用时传给 connection manager 的资源 profile                   |

### 6.4 v1 禁止参数

v1 不得存在：

```text
--sql
--write
--migrate
--allow-network
--enable-qmt
--enable-xqshare
--show-secrets
--full-scan
```

未来若增加高风险 flag，须先修订设计且默认关闭。

## 7. 实现位置

| 产物          | 路径                                                                | 角色                       |
| ------------- | ------------------------------------------------------------------- | -------------------------- |
| 后端服务      | `backend/app/ops/db_inspector.py`                                   | 纯检查逻辑；CLI 与测试复用 |
| 输出模型      | `backend/app/ops/models.py` 或 `db_inspector.py` 内 typed dataclass | 稳定报告结构               |
| 最终 CLI 入口 | `backend/app/cli/main.py`                                           | 长期 `qmd` console 目标    |
| 过渡 CLI 入口 | `scripts/qmd_ops.py`                                                | 仅临时包装；无重复逻辑     |
| 测试          | `tests/test_ops_db_inspector.py`                                    | fixture DB 与无变更测试    |
| 设计文档      | `docs/ops/db_inspect_cli.md`                                        | 人类可读权威               |
| 机器契约      | `specs/contracts/ops_db_inspect_contract.yaml`                      | 命令与输出契约             |

实现不得落在 `docs/` 或 `specs/`。

## 8. 只读与安全模型

### 8.1 DuckDB 访问

优先使用项目既有只读连接路径：

```text
ConnectionManager(db_path).reader()
```

若内部需直接 DuckDB 访问，必须使用：

```text
duckdb.connect(str(db_path), read_only=True)
```

### 8.2 防变更

inspector 不得调用：

- `apply_migrations`
- `ConnectionManager.writer()`
- `DuckDBWriteManager`
- `INSERT`、`UPDATE`、`DELETE`、`CREATE`、`DROP`、`ALTER`、`COPY TO`、`EXPORT`
- 源 fetch / sync orchestration 函数

### 8.3 SQL 构造

v1 仅可对已知表执行固定内部元数据查询。若插值表名，须通过现有标识符工具校验。

v1 不接受用户提供的 SQL 字符串。

## 9. v1 报告模型

### 9.1 顶层形态

```json
{
  "status": "PASS|WARN|FAIL",
  "generated_at": "2026-06-20T00:00:00Z",
  "mode": "read_only",
  "db": {},
  "data_root": {},
  "schema": {},
  "key_tables": [],
  "evidence": {},
  "warnings": [],
  "errors": [],
  "deferred_item_mapping": []
}
```

### 9.2 状态规则

| 状态   | 含义                                                                                           |
| ------ | ---------------------------------------------------------------------------------------------- |
| `PASS` | DB 存在、只读打开、关键元数据检查完成、未检出严重证据缺口                                      |
| `WARN` | DB 可打开，但似仅 schema、缺 raw/parquet 证据、缺 fetch/job 证据，或有 open review/conflict 项 |
| `FAIL` | DB 缺失、无法只读打开、schema 自省失败，或违反安全不变量                                       |

### 9.3 DB 块

```json
{
  "path": "data/duckdb/quant_monitor.duckdb",
  "exists": true,
  "read_only_open": true,
  "file_size_bytes": 123456,
  "connection_error": null
}
```

### 9.4 Data-root 块

```json
{
  "path": "data",
  "exists": true,
  "raw_files_count": 0,
  "parquet_files_count": 0,
  "audit_files_count": 0,
  "report_files_count": 0,
  "scan_limited": true
}
```

路径扫描须留在配置的 data root 内，不得遍历任意系统路径。

### 9.5 关键表行数

v1 在表存在时须尝试统计：

| 表                    | 证据用途                |
| --------------------- | ----------------------- |
| `schema_version`      | 已应用 schema/migration |
| `source_registry`     | 源配置                  |
| `file_registry`       | 已登记 raw/文件         |
| `fetch_log`           | 抓取/源证据             |
| `data_sync_job`       | 任务生命周期            |
| `job_event_log`       | 任务状态迁移            |
| `validation_report`   | 数据验证                |
| `data_quality_log`    | 质量问题                |
| `source_conflict`     | 多源冲突                |
| `manual_review_queue` | 人工复核                |
| `write_audit_log`     | clean/写入              |
| `resource_guard_log`  | 资源保护                |
| `instrument_registry` | 证券主数据              |
| `security_bar_1d`     | 证券级行情              |

缺失表作为元数据事实报告，非自动失败（schema 覆盖因阶段而异）。若 DB 可打开但关键表全缺，依 `schema_version` 是否存在判 `FAIL` 或 `WARN`。

### 9.6 Evidence 块

报告应含仅元数据的最新/状态摘要：

```json
{
  "latest_fetch": {
    "fetch_time": null,
    "source_id": null,
    "status": null,
    "row_count": null
  },
  "job_status_counts": {},
  "validation_status_counts": {},
  "conflict_status_counts": {},
  "manual_review_status_counts": {},
  "latest_write": null
}
```

勿打印完整 raw payload、请求参数、凭证或大样本行。

### 9.7 Deferred 项映射

v1 输出须含 Round 3 早期闭环追溯提示：

| Deferred 项               | 证据字段                                                                                       |
| ------------------------- | ---------------------------------------------------------------------------------------------- |
| `DB-R3-001`               | `data_root.raw_files_count`、`data_root.parquet_files_count`、关键表行数、`file_registry` 计数 |
| `DB-R3-002`               | `db.exists`、`db.read_only_open`、schema/表自省                                                |
| `R3-PARTIAL-2`            | `latest_fetch`、`job_status_counts`、`validation_status_counts`                                |
| `R2.6-IMPL-8`             | 本工具不启用 live 源；仅可报告 DB 中已有 route/fetch 证据                                      |
| `R3-EARLY-DB-INSPECT-CLI` | 命令可用、只读模式、JSON 输出、无变更测试                                                      |

### 9.8 信任边界（Phase A）

`db-inspect` 是**运维信任的本地 CLI**。调用方 OS 用户可传任意 `--db` 与 `--output` 路径；除固定 `data_root` 扫描子目录外，工具不沙箱文件系统访问。勿在未加路径白名单与认证的情况下对不可信远程调用暴露此 CLI。

## 10. 文本输出 UX

文本模式应便于非专家运维阅读：

```text
QMD DB Inspect: WARN
DB: data/duckdb/quant_monitor.duckdb exists and opened read-only
Tables: 12 found
Evidence: fetch_log=0, data_sync_job=0, validation_report=0
Data root: raw=0, parquet=0
Meaning: database is present, but this run does not prove real vendor data ingestion yet.
Next: run user-authorized staging fetch or keep DB-R3-001 deferred.
```

文本模式给人看；JSON 模式是审计契约。

## 11. 测试与验收

### 11.1 必需测试

| 测试                      | 必需断言                                              |
| ------------------------- | ----------------------------------------------------- |
| 缺失 DB                   | 返回 `FAIL`，非仅 traceback                           |
| 含 schema 的空 fixture DB | 返回 `WARN`，报告表与零数据行                         |
| 含证据行的 fixture DB     | 正确报告行数与最新元数据                              |
| 只读不变量                | 测试 DB 未被修改；未调用 migration/写入 API           |
| 禁止 SQL flag             | v1 CLI 拒绝或不暴露自由 SQL                           |
| 输出 JSON 形态            | JSON 匹配 `ops_db_inspect_contract.yaml` 必需顶层字段 |
| 路径扫描防护              | 扫描留在 data root 内，仅统计 raw/parquet 候选        |

### 11.2 验收命令

Round 3 v1 实现至少运行：

```bash
pytest tests/test_ops_db_inspector.py -q
pytest tests/test_project_scaffold.py -q
```

若同任务实现打包/CLI 入口，另跑相关 CLI smoke。

## 12. 阶段计划

| 阶段                                     | 时机                                        | 范围                                                                            | 不得包含                                                        |
| ---------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Phase A / Round 3 Batch 1                | 首次实现                                    | `qmd ops db-inspect` 只读摘要、JSON、关键表行数、raw/parquet 证据、无变更测试   | 自由 SQL、网络、migration、data health 规则、source health 写入 |
| Phase B / Round 3 Batch 1 扩展或 Batch 6 | v1 JSON 稳定后                              | `qmd source probe --route-preview --no-fetch`                                   | 除非单独批准，否则不做用户授权 staging fetch                    |
| Phase C / Batch 6 或更晚                 | data-quality profile 选定后                 | 从 `data_quality_rules.yaml` 做 `qmd data health` 域检查                        | 默认不写生产表                                                  |
| Phase D / Batch 6 migration 工作         | `source_health_snapshot` migration 设计之后 | `qmd ops source-health snapshot --read-only-preview`；可选写入仅 migration 之后 | 无 migration 从 CLI 建表                                        |
| Phase E / Round 5 release/reporting      | JSON 证据形态稳定后                         | `qmd ops report` 本地 Markdown/HTML                                             | 上传数据或报告                                                  |
| Phase F / Release 加固                   | Round 5 / 最终打包                          | `qmd ops env-doctor`、console 打包、docs anchor、release manifest               | 未经批准的新增广泛依赖                                          |

## 13. 规划要求

任务触及本工具时：

1. 任务卡输入清单须含本文与 `specs/contracts/ops_db_inspect_contract.yaml`。
2. 任务卡须说明本 batch 仅 Phase A 或含更晚阶段。
3. Execute 须读原文时，执行说明可引用本文；否则任务卡须摘要 Phase A 精确约束。
4. 审计计划须验证无变更、无网络、JSON 形态、deferred 追溯证据。
5. 本文未显式授权的未来阶段须保持范围外并重新 defer。

## 14. 对原始执行任务的影响

下列原始任务卡在重新规划时须将本文视为规划输入：

| 任务 / 规划来源                                                                                                                  | 与本设计的关系                                          |
| -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`                                                                           | 声明 Local DB inspect CLI 为 Round 3 早期工作           |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/README.md`                                                                    | Round 3 规划指向未编号 DB inspect CLI 边界              |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016D_define_data_sync_quick_reference_and_error_guides.md` | 未来 CLI 命令矩阵不得与 `qmd ops db-inspect` 冲突       |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016F_define_prod_equivalent_scale_benchmark.md`            | 生产等价 smoke 证据可由 DB inspect 输出摘要             |
| `docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/031_implement_integration_smoke_tests.md`                                 | 集成 smoke 可验证 DB inspect CLI 为只读证据检查         |
| `docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/033_implement_security_and_boundary_tests.md`                             | 边界测试须断言无自由 SQL、无写入、无网络、前端不直连 DB |
| `docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/034_implement_docs_consistency_check.md`                                  | docs/spec/index 一致性须含本设计与契约                  |
| `docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/035_implement_final_package_cleanup.md`                                   | cleanup allowlist 须保留设计与契约                      |
| `docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/036_create_final_release_manifest.md`                                     | 实现/接受后 final manifest 须含本设计与契约             |

这不表示 Execute 须始终读原始任务卡。规划须按活路线图与模块文档将本设计折入当前任务追溯。

## 15. 已关闭的开放决策

用户已确认：

1. DB inspect CLI 是长期正式只读运维工具。
2. v1 命令目标是 `qmd ops db-inspect`。
3. `scripts/qmd_ops.py` 仅允许作为过渡薄包装。
4. v1 禁止自由 SQL、DB 写入、migration、网络访问、打印 secret、默认原始行浏览、生产数据变更。
5. v1 须输出 JSON 与人类可读文本。
6. v1 须检查 DB 存在、只读打开、关键表行数、元数据证据、raw/parquet data-root 证据。
7. `qmd data health`、`qmd source probe`、`qmd ops source-health snapshot`、`qmd ops report` 为未来阶段，非 v1 范围。
