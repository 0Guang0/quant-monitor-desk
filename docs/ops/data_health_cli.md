# QMD Data Health CLI 设计

> 状态：Batch 6 / Phase C 的用户冻结设计输入。本文档非运行时代码，不参与 DB migration。
>
> 范围：local-first、默认只读，针对 QMD 自有表与契约做域级数据质量检查。
>
> 契约输入：`specs/contracts/data_quality_rules.yaml`（`ops_cli_profiles`）、`specs/contracts/source_conflict_rules.yaml`、`docs/modules/data_validation_and_conflict.md`。
>
> 参考落地：`R3-REF-OPS-DB-DATA-HEALTH` / `R3D_ops_db_data_health_reference.md`。

## 1. 决策摘要

数据健康工具回答：

> 对所选数据域与日期窗口，QMD 表是否满足契约驱动的质量规则——且不变更生产数据、不抓取外部源？

最终命令族：

```bash
qmd data health
```

Round 3 v1（`qmd ops db-inspect`）**不**实现域质量规则。本设计为 Batch 6 实现权威。

过渡期入口（打包未就绪时）：

```bash
python scripts/qmd_ops.py data-health
```

## 2. 参考采纳边界

| 参考模式                                           | 来源                                                    | 采纳                                                                     | 不采纳                                                                 |
| -------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| 完整性类别：缺失交易日、字段质量、价格关系、离群值 | [EasyXT](https://github.com/quant-king299/EasyXT)       | 将类别映射到各域 `data_quality_rules.yaml` 规则 ID；PASS/WARN/FAIL 摘要  | 硬编码 `stock_daily` 表、字符串拼接 SQL、自动源 fallback、QMT 自动登录 |
| 本地 DB 路径覆盖与可重复 CLI 运行                  | [JQ2PTrade](https://github.com/quant-king299/JQ2PTrade) | `--db` / `--duckdb-path` 风格覆盖；`--domain` + `--format json` 供自动化 | 回测引擎、策略转换、PTrade/JoinQuant 下单 API                          |
| 运维可读状态与排障流程                             | EasyXT + `docs/ops/TROUBLESHOOTING.md`                  | 文本模式含含义与下一步提示；失败带 `error_code` + `docs_anchor`          | 交易平台教程内容                                                       |

采纳规则：仅借鉴检查**类别**与本地 CLI 易用性。规则、表、严重级别来自 QMD 契约，而非外部 schema。

## 3. 与 `qmd ops db-inspect` 的关系

| 工具                 | 回答问题                                                | 默认模式 | 阶段                       |
| -------------------- | ------------------------------------------------------- | -------- | -------------------------- |
| `qmd ops db-inspect` | DB 是否存在、能否只读打开、元数据/证据行数？            | 只读     | Round 3 Batch 1（Phase A） |
| `qmd data health`    | 域内行是否满足 `data_quality_rules.yaml` 请求窗口规则？ | 只读     | Batch 6（Phase C）         |

`db-inspect` 不得静默扩展为 data-health 检查。运维应先跑 `db-inspect` 确认存在/证据，再跑 `data health` 做域规则。

## 4. 检查类别（QMD 自有）

每类映射现有 validator 契约，非 EasyXT 表名。

| 类别               | 示例规则 ID                                               | QMD 表（示意）                              |
| ------------------ | --------------------------------------------------------- | ------------------------------------------- |
| 日历完整性         | `STALE_DATA`、`INSUFFICIENT_HISTORY` + 域扩展             | `security_bar_1d`、各 `--domain` 层表       |
| 字段 / schema 质量 | `MISSING_REQUIRED_FIELD`、`SCHEMA_DRIFT`、`INVALID_ENUM`  | 各域 staging 或 clean 表                    |
| 价格关系           | `INVALID_PRICE_RANGE`、`NEGATIVE_PRICE`、`INVALID_VOLUME` | `security_bar_1d`                           |
| 重复键             | `DUPLICATE_PRIMARY_KEY`、`MISSING_PRIMARY_KEY`            | 域主键                                      |
| 来源血缘           | `MISSING_SOURCE_USED`、`FALLBACK_WITHOUT_REASON`          | `fetch_log`、`validation_report`、layer1 表 |
| 冲突感知           | 只读汇总 `source_conflict`                                | `source_conflict`、`manual_review_queue`    |

冲突**解决**仍在 `SourceConflictValidator` / `ReconcileJob`。Data health CLI 可**报告**未结冲突，但不得自动 reconcile 或写入。

## 5. CLI 契约（设计）

### 5.1 命令形态（R3FR-06 规范）

```bash
qmd data health \
  --domain market_bar_1d \
  --profile market_bar_p0 \
  --evidence-dir tests/fixtures/data_health/good_bundle \
  --format json
```

可选只读 DB 覆盖（文件存在时对 `fetch_log.schema_hash` 做有界扫描；域规则仍以 evidence 驱动）：

```bash
qmd data health --db-path data/duckdb/quant_monitor.duckdb --domain market_bar_1d --profile market_bar_p0 --evidence-dir <path>
```

### 5.1.1 Data health R2 — 四类 profile 族（Plan R2 SSOT）

Profile 定义：`specs/contracts/data_quality_rules.yaml`；绑定：同文件 `source_health_bindings`。

```bash
# 市场 bar（baostock / mootdx / alpha_vantage）
qmd data health --domain market_bar_1d --profile market_bar_p0 --evidence-dir <path> --db-path <duckdb>

# 宏观观测（fred / us_treasury / bis / world_bank / cftc_cot）
qmd data health --domain layer1_observation --profile layer1_observation_p0 --evidence-dir <path> --db-path <duckdb>

# 披露（sec_edgar → us_disclosure；cninfo → cn_disclosure）
qmd data health --domain us_disclosure --profile disclosure_p0 --evidence-dir <path> --db-path <duckdb>
qmd data health --domain cn_disclosure --profile disclosure_p0 --evidence-dir <path> --db-path <duckdb>

# 加密衍生品（deribit）
qmd data health --domain crypto_derivative --profile crypto_derivative_p0 --evidence-dir <path> --db-path <duckdb>
```

**禁止：** 以 SKIP / 仅 inspect 不做 health 当作通过（Plan R2）。

### 5.2 参数（规范 — 冻结 §6.3）

| 参数                | 必填 | 默认   | 行为                                                                       |
| ------------------- | ---- | ------ | -------------------------------------------------------------------------- |
| `--domain`          | 是   | —      | `market_bar_1d`（映射 `ops_cli_profiles`）                                 |
| `--profile`         | 是   | —      | `market_bar_p0`（非 `--rule-set`）                                         |
| `--evidence-dir`    | 是\* | —      | 证据包根目录（测试用 `good_bundle`）                                       |
| `--db-path`         | 否   | —      | 可选只读 DuckDB；有行时在 envelope 中输出有界 `fetch_log.schema_hash` 覆盖 |
| `--start` / `--end` | 否   | —      | bar 行上的闭区间日期窗口                                                   |
| `--max-rows`        | 否   | 1000   | 报告明细行上限                                                             |
| `--format`          | 否   | `json` | `json` 或 `text`                                                           |

\* R3FR-02+06 垂直切片中，受支持 profile 必填。

旧版设计注记：早期草稿用 `--db` 与 `--rule-set`；实现使用 `--db-path` 与 `--profile`。

### 5.3 禁止参数（v1 设计）

```text
--write
--migrate
--allow-network
--enable-qmt
--enable-xqshare
--sql
--full-market-scan
--show-secrets
--auto-reconcile
```

`--write-report` 可在后续子批次设计，须用户显式批准并为持久化 health snapshot 设计 migration。

## 6. 报告模型（JSON — R3FR-06 §5）

CLI JSON envelope（`qmd data health` 权威）：

```json
{
  "command": "health",
  "dry_run": true,
  "side_effects_allowed": false,
  "domain": "market_bar_1d",
  "profile": "market_bar_p0",
  "status": "PASS",
  "rules_run": [],
  "issue_counts_by_severity": {},
  "row_count_checked": 0,
  "window": { "start": "", "end": "" },
  "source_ids": [],
  "content_hash_coverage": {},
  "schema_hash_coverage": {},
  "limitations": [],
  "report_path": null
}
```

`report_path` 可选。内部 `DataHealthReport` 仍可用于 C-20 staged profile；CLI 映射到上述 envelope。

旧版设计形态（CLI 输出已 supersede）：

每条 finding：

```json
{
  "rule_id": "INVALID_PRICE_RANGE",
  "severity": "failed",
  "affected_rows": 0,
  "sample_count": 0,
  "docs_anchor": "specs/contracts/data_quality_rules.yaml"
}
```

文本模式须说明含义与下一步（EasyXT 风格运维 UX），例如：

```text
QMD Data Health: WARN (market_bar_1d)
Window: 2024-01-01 .. 2024-12-31 | checked_rows=120
Failed: 0 | Warning: 2 (STALE_DATA, INSUFFICIENT_HISTORY)
DB: data/duckdb/quant_monitor.duckdb (read-only)
Next: run user-authorized staging fetch or narrow --start/--end.
```

## 7. 安全不变量

1. 默认只读打开 DuckDB（`ConnectionManager.reader()` 或 `duckdb.connect(..., read_only=True)`）。
2. 不得调用 `apply_migrations`、`ConnectionManager.writer()` 或 `DuckDBWriteManager`。
3. 不得触发外部 fetch 或从此 CLI 启用 QMT/xqshare。
4. 不得打印 secret、token 或大段原始行 dump。
5. 遵守 `resource_limits.yaml` 行/样本上限；默认有界窗口。
6. 每条 FAIL 须含与 `docs/ops/ERROR_CODE_GUIDE.md` 兼容的 `error_code` 与 `docs_anchor`。

## 8. 实现位置（未来）

| 产物     | 路径                                              |
| -------- | ------------------------------------------------- |
| 后端服务 | `backend/app/ops/data_health.py`                  |
| CLI 包装 | `scripts/qmd_ops.py` 或 `backend/app/cli/main.py` |
| 测试     | `tests/test_ops_data_health.py`                   |
| 设计文档 | `docs/ops/data_health_cli.md`（本文）             |
| 机器规则 | `specs/contracts/data_quality_rules.yaml`         |

## 9. 阶段计划

| 阶段    | 时机               | 范围                                           |
| ------- | ------------------ | ---------------------------------------------- |
| Phase A | Round 3 Batch 1    | 仅 `qmd ops db-inspect`（无域规则）            |
| Phase C | Batch 6            | 从 `ops_cli_profiles` 做只读 `qmd data health` |
| 后续    | migration 设计之后 | 可选持久化 health snapshot 写入模式            |

## 10. 规划追溯

- 实现 Batch 6 data health 的任务输入清单须引用本文。
- 外部 URL：EasyXT、JQ2PTrade（见 §2）；ptqmt-site 仅适用于 `ops_report_cli.md` 报告渲染。
