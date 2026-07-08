# QMD Ops Report CLI 设计

> 状态：Round 5 / Phase E 的用户冻结设计输入。本文档非运行时代码。
>
> 范围：将运维工具产出的本地 JSON 证据转为运维可读的 Markdown/HTML 报告——完全离线，不上传。
>
> 参考落地：`R3-REF-OPS-DB-DATA-HEALTH` / `R3D_ops_db_data_health_reference.md`。

## 1. 决策摘要

运维报告工具回答：

> 给定本机已产出的 JSON 证据，能否渲染一份运维可读报告，且不把数据暴露到网络？

最终命令：

```bash
qmd ops report
```

依赖以下工具的稳定 JSON 形态：

- `qmd ops db-inspect --format json`
- `qmd data health --format json`（Phase C）
- 未来的 `qmd ops source-health snapshot --read-only-preview`

Round 3 v1 **不**实现此命令。

## 2. 参考采纳边界

| 参考模式                           | 来源                                                                 | 采纳                                 | 不采纳                     |
| ---------------------------------- | -------------------------------------------------------------------- | ------------------------------------ | -------------------------- |
| 仅本地 / 浏览器侧隐私表述          | [ptqmt-site](https://github.com/quant-king299/ptqmt-site)            | 报告头尾：数据留在本机；不上云       | 在线站点布局作为运行时依赖 |
| 运维文档结构：摘要 → 明细 → 下一步 | ptqmt-site + EasyXT 排障风格                                         | Markdown/HTML 模板章节顺序           | 交易教程或券商营销文案     |
| 可重复本地产物生成                 | [JQ2PTrade](https://github.com/quant-king299/JQ2PTrade) 报告构建概念 | `--input` JSON + `--output` 本地文件 | 策略/回测报告语义          |

交叉引用：`docs/ops/privacy_data_flow.md`、`specs/contracts/user_input_privacy_contract.yaml`。

## 3. CLI 契约（设计）

```bash
qmd ops report \
  --input evidence/db_inspect_20260622.json \
  --format markdown \
  --output reports/local/db_inspect_20260622.md
```

### 3.1 参数

| 参数       | 必填 | 默认                       | 行为                                                       |
| ---------- | ---- | -------------------------- | ---------------------------------------------------------- |
| `--input`  | 是   | —                          | JSON 证据文件路径（db-inspect、data-health 或合并 bundle） |
| `--format` | 否   | `markdown`                 | `markdown` 或 `html`                                       |
| `--output` | 否   | stdout                     | 本地文件路径，通常在 `data/reports/` 或用户指定目录        |
| `--title`  | 否   | 由证据 `mode` + 时间戳推导 | 报告标题                                                   |
| `--redact` | 否   | true                       | 按隐私契约剥离路径/secret                                  |

### 3.2 禁止参数

```text
--upload
--allow-network
--embed-external-cdn
--show-secrets
```

## 4. 报告章节（QMD 自有）

1. **隐私横幅** — 仅本地；不传外网（ptqmt-site 模式）。
2. **执行摘要** — PASS/WARN/FAIL、时间戳、证据来源命令。
3. **DB / 数据路径血缘** — `db.path`、`data_root.path`、行数（来自 db-inspect）。
4. **域健康发现** — 输入含 data-health JSON 时。
5. **Deferred 项映射** — registry ID 追溯提示（如 `DB-R3-001`）。
6. **下一步** — 仅链接 `docs/ops/TROUBLESHOOTING.md`、`ERROR_CODE_GUIDE.md` anchor（不要求 live URL）。

报告不得含原始凭证、完整行 payload 或网络调用。

## 5. JSON 输入兼容性

| `evidence_type` | 来源命令             | 最少字段                                              |
| --------------- | -------------------- | ----------------------------------------------------- |
| `db_inspect`    | `qmd ops db-inspect` | `status`、`db`、`key_tables`、`deferred_item_mapping` |
| `data_health`   | `qmd data health`    | `status`、`domain`、`summary`、`findings`             |
| `bundle`        | 上述合并             | `items[]` 含 `evidence_type` 判别字段                 |

未知 evidence 类型：渲染元数据 + 警告；不得崩溃。

## 6. 安全不变量

1. 纯本地转换：读 JSON 文件 → 写报告文件。
2. v1 不必打开 DuckDB（可选未来 `--live-db-inspect` 不在 Phase E v1）。
3. 无网络、无上传、无外部资源 fetch。
4. 默认脱敏主目录路径与 token。

## 7. 实现位置（未来）

| 产物     | 路径                                                      |
| -------- | --------------------------------------------------------- |
| 报告构建 | `backend/app/ops/report_models.py`                        |
| CLI      | `scripts/qmd_ops.py` 或 `backend/app/cli/main.py`         |
| 测试     | `tests/test_ops_report.py`（未来）                        |
| 输出目录 | `data/reports/`（见 `docs/modules/local_file_system.md`） |

## 8. 阶段计划

| 阶段    | 工具             | 报告支持                   |
| ------- | ---------------- | -------------------------- |
| Phase A | `db-inspect`     | 仅 JSON；无 report CLI     |
| Phase C | `data health`    | 仅 JSON                    |
| Phase E | `qmd ops report` | 由 JSON 生成 Markdown/HTML |

## 9. 外部 URL（来源上下文索引）

- `https://github.com/quant-king299/ptqmt-site` — 隐私/报告组织（主）
- `https://github.com/quant-king299/EasyXT` — 排障章节风格（次）
- `https://github.com/quant-king299/JQ2PTrade` — 本地报告产物模式（次，仅回测报告概念）
