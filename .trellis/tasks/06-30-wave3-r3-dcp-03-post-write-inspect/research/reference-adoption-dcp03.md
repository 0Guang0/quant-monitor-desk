# R3-DCP-03 参考项目采纳调研（仅外部 `参考项目/**`）

> **任务：** `.trellis/tasks/06-30-wave3-r3-dcp-03-post-write-inspect/`  
> **日期：** 2026-06-30（修订：三等级仅指外部参考项目）  
> **阶梯 SSOT：** `specs/contracts/reference_adoption_guardrails.yaml`  
> **设计已落地指针：** `docs/ops/db_inspect_cli.md` · `R3D_ops_db_data_health_reference.md` · R3FR-02 `market_bar_p0`

---

## 0. 术语（必读，防混淆）

| 类别             | 含义                                              | 本文件是否用 L1/L2/L3                                               |
| ---------------- | ------------------------------------------------- | ------------------------------------------------------------------- |
| **参考项目**     | 仓库外/本地 `参考项目/**` 成熟项目源码            | **是** — 唯一进入三等级的对象                                       |
| **仓内已有代码** | `backend/`、`tests/`、已合并契约与 CLI            | **否** — 只写「复用 / 已有资产」，**禁止**标 L1/L2/L3               |
| **本轨新建**     | `tests/test_incremental_post_write_inspect.py` 等 | **否** — 写「本轨交付 / 绿场」，**禁止**标 L3（避免与参考阶梯混用） |

**铁律：** `参考项目/**` 只读；**禁止** runtime import、`sys.path`、运行时读取参考路径执行。

---

## 1. 仓内已有资产（复用 — 非三等级）

| 资产              | 路径                                                                             | 本轨用法                                             |
| ----------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 只读 DB 巡检      | `backend/app/ops/db_inspector.py`                                                | 写后 `key_tables[].row_count`                        |
| 巡检契约          | `specs/contracts/ops_db_inspect_contract.yaml`                                   | `security_bar_1d` / `axis_observation` 在 key_tables |
| CLI 薄包装        | `scripts/qmd_ops.py` `db-inspect`                                                | JSON smoke                                           |
| Health profile    | `backend/app/ops/data_health_profiles/` · `run_data_health_profile`              | `market_bar_p0`                                      |
| baostock 增量 e2e | `tests/test_baostock_incremental_e2e.py`                                         | 编排样板（2× incremental）                           |
| 巡检契约测        | `tests/test_ops_db_inspector.py`                                                 | CLI 调用样板                                         |
| profile 先例      | `tests/test_data_health_easyxt_profiles.py` + `fixtures/data_health/good_bundle` | bundle 格式 SSOT                                     |
| DCP-01/02 已闭合  | 归档 audit / e2e                                                                 | 幂等语义不重复证明为唯一 AC                          |

---

## 2. 参考项目三等级总表（仅外部）

> Execute 前须产出 `research/execute-reference-read-evidence.md`（实读登记表）；`参考项目/**` 不可见时登记 `MISSING_REFERENCE_TREE` 并仅依赖本节 + R3D 已落地边界，**不得**假装已实读。

| 参考项目 / 文件                                                     | 等级                  | 证据（须实读登记）                               | 本轨处置                                                              |
| ------------------------------------------------------------------- | --------------------- | ------------------------------------------------ | --------------------------------------------------------------------- |
| EasyXT `data_manager/data_integrity_checker.py`（或等价完整性模块） | **L2 已落地**         | R3FR-02 已拷改规则 → `market_bar_p0`；R3D §3     | **不二次拷贝**；Execute 实读对照「类别」是否已被 `market_bar_p0` 覆盖 |
| EasyXT `data_manager/unified_data_interface.py`                     | **禁止**              | DCP-01 实读先例                                  | silent 换源 / 直写 DuckDB — **不得**进入 inspect 路径                 |
| EasyXT trading / QMT auto-login / scheduler                         | **禁止**              | `reference_adoption_guardrails.yaml`             | 不得采纳                                                              |
| JQ2PTrade CLI `--duckdb-path` / 本地库路径覆盖                      | **L1 已落地**         | `ops_db_inspect_contract.yaml` `v1_arguments.db` | **不二次拷贝**；本轨 CLI smoke 用 `--db`                              |
| JQ2PTrade 回测 / 下单 / 策略转换                                    | **禁止**              | R3D §3                                           | 不得采纳                                                              |
| ptqmt-site 本地隐私/文档组织                                        | **architecture_only** | `docs/ops/ops_report_cli.md` 延后                | 本轨不实现 report CLI                                                 |
| OpenBB Fetcher                                                      | **architecture_only** | guardrails                                       | 与本轨无关                                                            |

**本轨无新增 L2 拷贝：** 写后抽检所需完整性规则与 CLI 路径覆盖 **已在 Round3 Batch1/R3FR-02 落入仓内**；DCP-03 只做 **接线 + 集成测**。

---

## 3. 本轨交付（绿场 — 非三等级）

| 交付                                           | 说明                                                            |
| ---------------------------------------------- | --------------------------------------------------------------- |
| `tests/test_incremental_post_write_inspect.py` | 2× incremental → `DbInspector` 行数稳定 + `max(trade_date)` SQL |
| 同上                                           | 写后 `run_data_health_profile`（见 §4 证据目录策略）            |
| 同上                                           | `qmd_ops db-inspect --format json` smoke                        |
| 可选 `tests/post_write_inspect_support.py`     | 从 `fetch_log` 组装最小 evidence bundle（仅测试）               |

**明确不做：** 新 macro profile、扩 `DbInspector` 报告字段（默认）、新 migration、参考项目 runtime 依赖。

---

## 4. 分主题深读

### A. E2 — DbInspector（仓内复用）

- 已有 `key_tables[].row_count`；**无** `max(trade_date)` 字段。
- **ponytail：** `max(trade_date)` 在集成测内 read-only SQL 断言。

### B. F0 — market_bar_p0 与证据目录（关键缺口已在本节闭合）

`run_data_health_profile` **要求** `evidence_path` 为含 `raw_evidence_manifest.json` 的 **evidence bundle**（见 `tests/fixtures/data_health/good_bundle/`）。

**事实：** `run_incremental` 写 `fetch_log.raw_file_paths` 与 raw 文件，**不**自动产出 bundle 目录。

**本轨 S02 策略（DEBT.plan 已绑定）：**

1. 2× incremental 完成后，从**同一隔离库** `fetch_log` 取最新 `raw_file_paths`；
2. 在 `tmp_path` 用 **测试 helper**（仓内新建，非参考项目）组装最小 bundle：`raw_evidence_manifest.json` + 指向已写入 raw JSON；
3. 对该 `db_path` 调用 `run_data_health_profile(market_bar_p0, …)`；
4. **禁止** AC 偷换为仅用 `good_bundle` 夹具而**未**接 incremental 会话（夹具仅作格式 SSOT / helper 单测）。

### C. 与 DCP-01/02 边界

| 轨     | 已验                | DCP-03 增量证明                                 |
| ------ | ------------------- | ----------------------------------------------- |
| DCP-01 | SQL `COUNT(*)` 幂等 | **DbInspector** 视角 + health + CLI             |
| DCP-02 | fred 幂等 e2e       | 非主路径；活卡允许 baostock **或** fred inspect |

---

## 5. Execute 前门禁

1. Read 活卡 + 本文 + `architecture-dcp03.md` + `DEBT.plan.md`
2. 完成 `research/execute-reference-read-evidence.md`（EasyXT 完整性模块 + JQ2PTrade CLI 路径段；**禁止**把仓内文件标成 L1/L2/L3）
3. Read `test_baostock_incremental_e2e.py` · `test_ops_db_inspector.py` · `test_data_health_easyxt_profiles.py`
4. RED 前确认：不改 `sync/*` / port（除非 Repair 根因）
