# A6 audit-perf — B3V-OPS Contract Drift & Write Modes 性能审计

> **维度：** A6 · performance-engineer + doubt-driven-development  
> **模型：** composer-2.5  
> **任务：** `round3v-contract-drift-write-modes`（B3V-OPS · Manifest `B3V-C01`）  
> **Worktree：** `quant-monitor-desk-wt-b3v-ops`  
> **日期：** 2026-06-28  
> **模式：** Audit（只读，无 commit、无改码）

---

## 总判定

| 项                   | 值                                           |
| -------------------- | -------------------------------------------- |
| **verdict**          | **SKIP**                                     |
| **BLOCKING**         | 0                                            |
| **NON-BLOCKING**     | 2                                            |
| **AUDIT.plan §1 A6** | **SKIP** — 无 SLA 热路径                     |

---

## Scorecard（静态审计 + 参考 pytest durations）

| 指标               | 值           | 来源                    | 阈值（Plan 冻结） | 状态        |
| ------------------ | ------------ | ----------------------- | ----------------- | ----------- |
| LCP / INP / CLS    | not measured | —                       | CWV               | —（无 Web） |
| smoke 端到端耗时   | not measured | Plan 未挂载             | —                 | SKIP        |
| ResourceGuard 触发 | not measured | diff 未挂 guard         | —                 | SKIP        |
| import-time YAML   | ~6 KB        | `ops_db_inspect_contract.yaml` stat | 未冻结 | 参考 only   |
| 最慢单测 call      | 0.56s        | pytest `--durations=10` | 未冻结            | 参考 only   |
| reserved 早拒测    | 0.56s        | 同上                    | 未冻结            | 参考 only   |
| CLI subdir 扫描测  | ~0.42–0.54s  | 同上                    | 未冻结            | 参考 only   |

> **Artifacts used:** `uv run pytest tests/test_contract_drift_ops_write.py tests/test_ops_db_inspector.py tests/test_write_manager.py -q --basetemp=.audit-sandbox/pytest --durations=10`  
> **注记：** 本次参考跑 2 FAILED（CLI `subdirScan` parquet/report 子集，`returncode==1`）；属 A8 功能门禁范畴，A6 不依赖 exit 0，perf 结论来自静态路径审阅 + durations 参考。  
> **Stack detected:** Python 单机 pipeline；只读 `DbInspector` + `WriteManager` 契约对齐；无 API/调度 hot path；非 Web 应用

---

## 1. 权威层级（`audit-adversarial-authority.md`）

| 级别   | 来源                                                                                         | 与本维结论                                                                 |
| ------ | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 第一级 | `B02_01_contract_drift_and_write_modes.md` §4、`ops_db_inspect_contract.yaml`（`hard_cap: 100`）、`docs/ops/performance_limits.md` | 只读 inspect；禁止 production DB mutation；data-root 扫描有 `--limit` 硬顶 |
| 第二级 | `agents/performance-engineer.md` checklist、`AUDIT.plan.md` §1                               | A6 显式 **SKIP**；验收 = 任务卡 §7 pytest 子集（委托 A8）                 |
| 第三级 | `MASTER.plan.md` §2.2 设计决策、`§10` Execute DoD                                             | 契约 loader + write 分栏；**§10 无 perf 冻结行**（仅 handoff checklist） |

**对抗性注记：** MASTER §10 仅列 §9 证据 / validate-handoff，**未**定义 `production_equivalent_smoke.py`、`ResourceGuard`、内存峰值或 `--durations` 门禁。按 performance-engineer 模板无法填可 PASS/FAIL 的「指标 | 阈值 | 实测」perf 表；SKIP 为 Plan 冻结决策，非遗漏。

---

## 2. SKIP 理由（§3.6 等价 · 与 AUDIT.plan §1 A6 一致）

> Plan 原文：**「无 SLA 热路径」** — 本任务为契约漂移检测与 write mode 语义分栏，无生产调度/API 热路径，无冻结 SLA。

### 2.1 五条证实

1. **无 hot path / SLA** — 变更落在 import-time 契约加载、YAML 分栏、漂移/parity 测试；`DbInspector.inspect()` 与 `WriteManager.write()` 核心 I/O/SQL 路径未改语义（write 仅 reserved 错误文案微调）。
2. **有界 inspect 面** — 契约 `v1_arguments.limit.hard_cap: 100`；`DbInspector.__init__` 将 `limit` clamp 到 `[1, 100]`；`_count_files_under` 达 cap 即停；`--full-scan` 仍 forbidden。
3. **任务卡 scope 排除重 I/O** — `B02_01` §4：禁止 reserved 模式 runtime 实现、禁止 production clean write、禁止 DB migration。
4. **Write 路径 O(1) 早拒** — reserved 模式在 `write()` 入口 `ValueError` 返回，无 DuckDB 写事务；与变更前行为一致，仅消息对齐契约措辞。
5. **MASTER / AUDIT 无 perf 冻结行** — 通过条件为 pytest exit 0（A8）；无时长/内存数字可供 A6 PASS/FAIL。

### 2.2 实现路径 vs 性能特征

| 组件                              | 触发时机              | I/O / CPU 特征                                      | 数据量级上界                          |
| --------------------------------- | --------------------- | --------------------------------------------------- | ------------------------------------- |
| `_load_ops_inspect_contract()`    | 模块 import（一次）   | `read_text` + `yaml.safe_load` ~6KB               | 契约 YAML 固定小文件                  |
| `KEY_TABLES` / `DEFERRED_ITEM_MAPPING` | import 派生常量  | 21 表名 + 5 deferred 项解析 + `quote_ident` 校验   | O(表数)，无 DB 往返                   |
| `DbInspector.inspect()`           | CLI/运维手动调用      | DuckDB read_only；21× `_table_stats`；evidence SQL | `limit`≤100 文件扫描 cap              |
| `WriteManager.write()` reserved   | 显式错误路径          | 字符串比较 + `ValueError`；无 `_execute_write`      | O(1)                                  |
| 漂移/parity 测试                  | CI / Audit pytest     | 常量比对 + fixture 小 DB                            | sandbox KB–MB 级                      |

**结论：** 变更落在 **契约对齐与机检漂移**，非高频批处理或用户可见延迟面；与 AUDIT.plan「无 SLA 热路径」一致。

### 2.3 performance-engineer checklist（Audit 模式）

| 检查项                       | 状态        | 说明                                          |
| ---------------------------- | ----------- | --------------------------------------------- |
| Baseline 有证据来源          | **N/A**     | Plan 未冻结 perf 命令                         |
| EXPLAIN/profile/smoke        | **N/A**     | inspect SQL 既有；无 smoke 挂载点             |
| 优化后同一命令对比           | **N/A**     | 无优化项                                      |
| sandbox 数据量级与 Plan 一致 | **PASS**    | fixture 小 DB；契约 limit hard_cap=100        |
| 全量 pytest 无无关回归       | **委托 A8** | 本维 durations 参考；正式门禁见 A8            |

---

## 3. 计划外 perf 风险扫描

> 按 `audit-adversarial-authority.md` A6：**即使 SKIP，仍须扫描** hot path、无界 I/O、批大小/内存尖峰。

### 3.1 Hot path

| 路径                                   | 是否 hot   | 证据                          | 风险                         |
| -------------------------------------- | ---------- | ----------------------------- | ---------------------------- |
| `db_inspector` import-time YAML        | **否**     | 进程内一次；运维 CLI 冷启动   | ~6KB 可忽略                  |
| `DbInspector.inspect()` @ CLI          | **低**     | 手动运维；非 API 热路径       | 21 表 stats 为既有设计       |
| `WriteManager.write()` @ production    | **否**     | 本任务未改 `_execute_write`   | reserved 早拒无额外 DB 负载  |
| 批量 ingest / 多 worker                | **未涉及** | MASTER 明确单机 pipeline      | 未来多 worker 须单独契约     |

**结论：** 本分支**不存在**新增可观测的生产 hot path；SKIP 合理。

### 3.2 无界 I/O

| 面                     | 扫描                     | 发现                                           | 评级       |
| ---------------------- | ------------------------ | ---------------------------------------------- | ---------- |
| data-root `rglob` 扫描 | `db_inspector._count_files_under` | cap=`self.limit`≤100；`scan_limited` 可观测 | **无**（有界） |
| DuckDB 全表扫          | `_table_stats` / evidence SQL | 既有 inspect 设计；本任务未增表数           | **无新增** |
| 契约 YAML 重复读       | 模块级 `_contract` 缓存  | import 一次                                    | **无**     |
| 网络 / live fetch      | 任务边界                 | db-inspect forbidden `--allow-network`         | **无**     |
| write_contract 加载    | `WriteManager`             | 仍用类常量；未 runtime loader                  | **无**     |

### 3.3 批大小 / 内存尖峰

| 面                           | 行为                         | 当前量级     | 计划外风险                                      |
| ---------------------------- | ---------------------------- | ------------ | ----------------------------------------------- |
| YAML parse 于 import         | `safe_load` 全文件           | ~6KB         | 可忽略                                          |
| 21× `_table_stats` 于 inspect | 每表 COUNT/SQL              | 运维低频     | 大库下 inspect 慢 → 见 NB-1（既有，非本任务引入） |
| CLI subprocess 测试          | pytest 起子进程跑 qmd_ops    | ~0.5s/测     | 测试 harness 主导；非生产路径                    |
| `WriteManager` DataFrame 写  | 未改                         | 既有 ResourceGuard 域外 | 本任务不触及                              |

**结论：** 当前测试与 staged 规模下 CPU/内存**可忽略**；结构性备忘见 NB-1/NB-2。

### 3.4 与 deferred perf 项交叉

| 登记项                                   | 与 B3V-OPS 关系                  |
| ---------------------------------------- | --------------------------------- |
| `scripts/production_equivalent_smoke.py` | diff 未挂载；MASTER §10 无 smoke  |
| `tests/test_resource_guard.py`           | write/inspect 路径未改 guard 接入 |
| Batch 6 perf budget / nightly            | **不阻塞** 本任务                 |

---

## 4. DOUBT（doubt-driven-development）

| 疑点                                      | 结论                                                                      |
| ----------------------------------------- | ------------------------------------------------------------------------- |
| SKIP 是否遗漏 smoke？                     | **否** — AUDIT.plan §1 + MASTER §10 双重无 perf 阈值                    |
| import-time YAML 是否拖慢 pytest import？ | **否** — ~6KB 一次；最慢测 0.56s 为 DuckDB/fixture 主导                 |
| KEY_TABLES 从 YAML 加载是否增 inspect 负载？ | **否** — 表数量不变（21）；仅常量来源从硬编码→契约派生              |
| reserved 早拒是否引入额外 DB round-trip？ | **否** — `write()` L394–400 纯 Python 分支                              |
| CLI 测 ~0.5s 是否 perf 回归？             | **否** — subprocess + 110 文件 fixture；无冻结基线；2 FAIL 属功能非 perf |

---

## 5. §3.6 证据表（SKIP 专用）

| 指标                                                         | 阈值（Plan 冻结） | 实测                    | 证据                                                                 |
| ------------------------------------------------------------ | ----------------- | ----------------------- | -------------------------------------------------------------------- |
| drift + ops + write_manager pytest                           | exit 0（A8）      | 参考跑：2 FAILED*       | `uv run pytest … -q --basetemp=.audit-sandbox/pytest --durations=10` |
| 最慢 call `test_writeManager_reservedModes_rejectWithoutWrite` | **未冻结**        | 0.56s                   | 同上                                                                 |
| CLI subdirScan 测                                            | **未冻结**        | 0.42–0.54s              | 同上                                                                 |
| `ops_db_inspect_contract.yaml` 体积                          | **未冻结**        | ~6 KB                   | 文件 stat                                                            |
| smoke 端到端                                                 | **未冻结**        | **未测**                | SKIP                                                                 |
| ResourceGuard                                                | **未冻结**        | **未触及**              | 无调用路径变更                                                       |
| 内存峰值 MB                                                  | **未冻结**        | **未测**                | fixture KB–MB 级                                                     |

\* CLI `subdirScan` parquet/report 子集 `returncode==1`；属 A8 功能断言，非 A6 perf 缺陷。

---

## 6. 计划外发现

| ID   | 发现                                                                 | 严重度               | 说明                                                                 |
| ---- | -------------------------------------------------------------------- | -------------------- | -------------------------------------------------------------------- |
| NB-1 | `DbInspector.inspect()` **21 表 `_table_stats` 串行 SQL**            | **NON-BLOCKING**     | 既有 inspect 设计；大库运维可能秒级；本任务未增表数；非 B3V-OPS 引入 |
| NB-2 | **Write 双 SSOT**（YAML + `WriteManager` 类常量）无 runtime loader   | **NON-BLOCKING**     | Plan 既定；parity 测门控；无 perf 影响；见 A1/A4 语义维              |
| —    | hot path / 全表扫 / 网络无界 I/O / write 路径变更                   | **无 BLOCKING 发现** | 已审阅 `db_inspector.py`、`write_manager.py`、`B02_01` §4、契约 limit |

**显式声明：** 已对照 `B02_01_contract_drift_and_write_modes.md`、`AUDIT.plan.md` §1 A6、`MASTER.plan.md` §2/§10、`agents/performance-engineer.md` + `audit-adversarial-authority.md`、实现全文及 pytest durations；**无 BLOCKING perf 项**。

---

## 7. 结论

**A6 审计判定：SKIP（维持）。**

理由摘要：B3V-OPS 是 **契约漂移机检 + write mode implemented/reserved 分栏** 文档/代码对齐任务；AUDIT.plan §1 显式 SKIP「无 SLA 热路径」；任务卡排除 production I/O 与 reserved runtime。实现仅在 import 时加载 ~6KB YAML 派生 `KEY_TABLES`/`DEFERRED_ITEM_MAPPING`，`WriteManager.write()` 热路径无结构性变更。计划外扫描登记 2 项 **NON-BLOCKING** 备忘（既有 inspect 表统计、Write 双 SSOT 模式），**不阻断** B3V-OPS merge。
