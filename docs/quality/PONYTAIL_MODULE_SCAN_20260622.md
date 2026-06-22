# Ponytail 模块大扫描报告 — 正式实现代码

> **生成时间：** 2026-06-22  
> **审计方式：** 8 个并行只读 Agent（每 Agent 负责一个 `backend/app` 模块集群）+ 主会话逐项核实  
> **审计标准：** `/ponytail` 等价路径 — `code-simplification` skill + `docs/decisions/README.md` 声明的 `ponytail-review` 等价规范  
> **PASS 阈值：** 单模块 ≥95/100；整体以「全部模块达标」为最终目标  
> **范围：** `backend/app/` 正式实现（不含 tests/scripts 本身，但测试用于行为约束验证）  
> **约束：** 本轮只产出报告，未修改任何代码

---

## 1. 执行摘要

| 指标               | 数值                                            |
| ------------------ | ----------------------------------------------- |
| 扫描模块数         | 8                                               |
| 核实后登记发现项   | **69**（HIGH 14 / MEDIUM 31 / LOW 24）          |
| 模块 PASS（≥95）   | **0 / 8**                                       |
| 模块最高分         | datasources **92**                              |
| 模块最低分         | ops **52**                                      |
| 主会话 pytest 复验 | **通过**（27 个测试文件；观察到 **2 skipped**） |

**整体结论：FAIL。** 功能测试绿，但正式实现代码在 ponytail（极简 / 反过度工程 / 运行时与证据分离）维度存在系统性债务，尚不能声称「已严格遵守 /ponytail」。

---

## 2. 审计方法与核实流程

### 2.1 Ponytail 判定准则（摘要）

1. **Preserve Behavior Exactly** — 简化不得改变行为；测试绿是前提
2. **反过度工程** — 无 factory-for-factory、无 speculative wrapper、无证据工具混入 runtime 导入面
3. **体量门禁** — 函数 >50 行、文件 >500 行、嵌套 ≥3 层需有明确理由
4. **DRY** — 5+ 行重复逻辑应合并（Chesterton's Fence：先理解再删）
5. **项目惯例** — 分层边界（Layer 不得直引 adapter factory）优先于个人偏好

### 2.2 Agent 分工

| Agent | 模块路径                                                           | 初评                |
| ----- | ------------------------------------------------------------------ | ------------------- |
| A1    | `layer1_axes/`                                                     | 73 FAIL             |
| A2    | `datasources/`                                                     | 92 FAIL             |
| A3    | `db/`                                                              | 64 FAIL             |
| A4    | `sync/`                                                            | 68 FAIL             |
| A5    | `ops/`                                                             | 52 FAIL             |
| A6    | `layer2_sensors/`                                                  | 65 FAIL             |
| A7    | `validators/`                                                      | 88 FAIL             |
| A8    | `storage/` + `core/` + `layer5_evidence/` + `config`/`main`/`util` | 73 CONDITIONAL FAIL |

### 2.3 主会话核实

对每项 Agent 发现，主会话通过 **读源码 + grep 定位 + 针对性 pytest** 核实。下表「核实」列：

- **确认** — 代码证据存在，登记有效
- **部分确认** — 问题存在但严重度/LOC 与 Agent 叙述略有出入（已在描述中修正）
- **不登记** — 误报（本轮无）

---

## 3. 模块评分汇总

| 模块                | 分数 | 结论 | 主要扣分原因                                                  |
| ------------------- | ---: | ---- | ------------------------------------------------------------- |
| layer1_axes         |   73 | FAIL | 976 LOC ingestion、331 行 commit monolith、evidence re-export |
| datasources         |   92 | FAIL | fetch_log 双 owner、factory 重复、production/test 路径不对称  |
| db                  |   64 | FAIL | WriteManager 双事务 + gate 双入口重复                         |
| sync                |   68 | FAIL | BackfillShardRunner monolith、incremental/backfill 镜像编排   |
| ops                 |   52 | FAIL | live_pilot.py ~1428 行 god module                             |
| layer2_sensors      |   65 | FAIL | lineage 三重复制、staging-write 样板                          |
| validators          |   88 | FAIL | common 薄包装、3 个长方法                                     |
| storage_core_layer5 |   73 | FAIL | 跨层 lineage 复制、staged 旁路仅靠约定                        |

---

## 4. 完整发现项登记（69 项，无遗漏）

> **说明：** 下列 **全部** HIGH / MEDIUM / LOW 项均已主会话核实为「确认」或「部分确认」。修复建议为 ponytail 向的最小路径，不代表本轮已实施。

---

### 4.1 模块 A1 — `layer1_axes/`（14 项）

| ID    | 级别       | 位置                                                                        | 问题                                                      | 证据                                                                                                         | 核实 | 修复方向                                                         |
| ----- | ---------- | --------------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ---- | ---------------------------------------------------------------- |
| L1-01 | **HIGH**   | `ingestion.py:905-975`                                                      | 审计/证据 API 经 runtime 门面 re-export，污染运行时导入面 | `from ingestion_evidence import ...` + 70 项 `__all__`；测试仍可从 `ingestion` 导入 evidence 符号            | 确认 | 删除 re-export；调用方改 `from ...ingestion_evidence import ...` |
| L1-02 | **HIGH**   | `ingestion.py:556-887`                                                      | 单函数严重超长（**~332 LOC**）                            | `commit_clean_observation_and_snapshots` 含 fetch→validate→conflict→obs→feature→interp→lineage 全链路 + 事务 | 确认 | 拆为 ≤50 行的私有步骤或 `ingestion_commit.py`                    |
| L1-03 | **HIGH**   | `ingestion.py`（**976 LOC**）                                               | 文件超 500 行门禁                                         | 仍含 service + 常量 + 路径工具 + evidence re-export                                                          | 确认 | 提交逻辑外移 + 去 re-export 后目标 ≤450 LOC                      |
| L1-04 | **MEDIUM** | `ingestion_evidence.py:414-434` vs `564-586`                                | Phase2/4 task 沙箱 DB 解析重复（≥5 行×2）                 | 相同 `sandbox_db.is_file()` → `copy_sandbox_db` → `apply_migrations` 分支                                    | 确认 | 提取 `_resolve_task_sandbox_db(...)`                             |
| L1-05 | **MEDIUM** | `ingestion.py:360-365,399-404,568-573`                                      | allowlist 校验块重复 3 次                                 | 相同 6 行 `if indicator_id not in self._allowlist: raise ...`                                                | 确认 | 合并为 `_assert_allowlisted(indicator_id)`                       |
| L1-06 | **MEDIUM** | `ingestion_inventory.py`（**671 LOC**）                                     | 审计/Phase1 工具位于 `backend/app/` 运行时包              | `capture_phase1_inventory` 等仅服务 execute-evidence                                                         | 确认 | 迁至 `ops/` 或 `scripts/layer1_evidence/`                        |
| L1-07 | **MEDIUM** | `ingestion_evidence.py`（**640 LOC**）                                      | 证据模块仍超 500 行且在 app 包内                          | phase capture + markdown formatters 集中单文件                                                               | 确认 | 与 L1-06 同迁或拆 `evidence_formatters.py`                       |
| L1-08 | **MEDIUM** | `ingestion.py:614-858`                                                      | 嵌套 ≥4 层                                                | `with writer` → `try` → fetch → map → quality → conflict → register                                          | 确认 | early-return 子函数降低嵌套                                      |
| L1-09 | **MEDIUM** | `lineage.py:252-286` 等                                                     | Write 路径三重样板（各 ~15 行）                           | `write_features` / `write_lineage` / `write_interpretation` 相同 `if con is None: with writer...`            | 确认 | 单 `_with_connection(con, fn)` 助手                              |
| L1-10 | **MEDIUM** | `guardrails.py` vs `ingestion.py` commit                                    | 已实现护栏未接入 commit（死路径）                         | `AxisEngineeringGuardrailValidator` 存在；commit 无 import/调用                                              | 确认 | commit 前校验 `source_used` vs `forbidden_substitutes`           |
| L1-11 | **MEDIUM** | `ingestion.py:323-342` + `tests/test_layer1_observation_ingestion.py:55-74` | `_row_counts` 生产/测试重复                               | 相同 information_schema 查询循环 ~20 行                                                                      | 确认 | 抽到 `db/row_counts.py` 或共享只读 helper                        |
| L1-12 | **LOW**    | `axis_loader.py:224-349`（**~125 LOC**）                                    | `_build_indicator_records` 超长                           | 单函数承担校验、默认值、definition+profile 双构建                                                            | 确认 | 拆 `_validate_observable_fields` + `_make_definition/profile`    |
| L1-13 | **LOW**    | `ingestion.py:860-869`                                                      | 事务成功后 10 行 `assert x is not None`                   | 成功路径变量已由 try 赋值                                                                                    | 确认 | 删除或收窄为 1–2 个关键 assert + 类型注解                        |
| L1-14 | **LOW**    | `interpretation.py:46-50` vs commit                                         | 禁止词静默替换而非拒绝                                    | `build_interpretation` 将「买入/信号」替换为「观察」；`reject_if_forbidden` 存在但 commit 未调用             | 确认 | commit 后对 `summary_sentence` 调 `reject_if_forbidden`          |

**模块测试：** `test_layer1_*.py` 125 项 — 主会话 **全部通过**

---

### 4.2 模块 A2 — `datasources/`（10 项）

| ID    | 级别       | 位置                                                | 问题                                            | 证据                                                                                             | 核实 | 修复方向                                                |
| ----- | ---------- | --------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------ | ---- | ------------------------------------------------------- |
| DS-01 | **MEDIUM** | `base_adapter.py:29-98`, `service.py:220-223`       | fetch_log **双写路径**                          | adapter 内置 `FetchLogWriter`；service 对 `BaseDataAdapter` 设 `record_fetch_log=False` 后统一写 | 确认 | service 单点写 log；adapter 去掉 DB 副作用或默认 False  |
| DS-02 | **MEDIUM** | `adapters/__init__.py:32-95`                        | `create_adapter` / `create_test_adapter` 近重复 | ~35 行各一份，仅 port/registry 默认值不同                                                        | 确认 | 提取 `_build_adapter(..., *, require_production: bool)` |
| DS-03 | **MEDIUM** | `service.py:199-217`                                | Production fetch 隐式走 test 路径               | 无 `file_registry_factory` 时用 `create_test_adapter` + `StubFetchPort`                          | 确认 | production `fetch()` 要求 registry；test 路径仅显式 DI  |
| DS-04 | **MEDIUM** | `capability_registry.py`, compat map                | 三套 domain 命名空间                            | adapter `supported_domains`、capability YAML、`ADAPTER_DOMAIN_COMPATIBILITY_MAP`                 | 确认 | 统一 domain 名；shrink compat map                       |
| DS-05 | **MEDIUM** | `route_planner.py`, `service.py`, `base_adapter.py` | 能力/域校验三重叠加                             | planner → service assert → adapter registry 检查                                                 | 确认 | adapter 仅保留 source_id 匹配 + `_fetch_impl`           |
| DS-06 | **LOW**    | `service.py:245-264`                                | `_default_operation` 与 capability YAML 双源    | domain→operation 硬编码 dict                                                                     | 确认 | 从 capability registry 推导                             |
| DS-07 | **LOW**    | `service.py:54-58`                                  | 访问私有状态 `_sources` / `.sources`            | 破坏封装                                                                                         | 确认 | 公开 `is_loaded()` 或幂等 `load()`                      |
| DS-08 | **LOW**    | `source_registry.py`（**514 LOC**）                 | 单文件偏长                                      | YAML 解析+校验+DB sync 集中                                                                      | 确认 | 可选拆 `registry_parser.py` / `registry_sync.py`        |
| DS-09 | **LOW**    | `adapters/tdx_pytdx.py`, `__init__.py:23-29`        | `TdxPytdxAdapter` 未注册 factory                | 018C 占位类不在 `_ADAPTER_TYPES`                                                                 | 确认 | 移入 proposed 或注册为 disabled 并文档化                |
| DS-10 | **LOW**    | `service.py:129-224`                                | `fetch()` ~95 行                                | 含 route/guard/capability/adapter 分支                                                           | 确认 | 仅当继续增长时拆 `_plan_and_guard`                      |

**积极面（不计入违规）：** skeleton adapter 分层合理，vendor 类无 copy-paste fetch 逻辑。

**模块测试：** datasource/source/adapter 相关 — 主会话 **全部通过**

---

### 4.3 模块 A3 — `db/`（9 项）

| ID    | 级别       | 位置                                | 问题                                                                 | 证据                         | 核实 | 修复方向                                      |
| ----- | ---------- | ----------------------------------- | -------------------------------------------------------------------- | ---------------------------- | ---- | --------------------------------------------- |
| DB-01 | **HIGH**   | `write_manager.py` `_execute_write` | 同时处理 own_transaction T/F、gate 双调用、成功/失败、sidecar 懒加载 | 单函数认知负荷过高           | 确认 | 收敛为「失败审计策略」对象 + 单一 except 分发 |
| DB-02 | **HIGH**   | `write_manager.py:67-79`            | `_validate_request` 与 `_validated_tables` 重复 `quote_ident`        | 同一 request 两次 quoting    | 确认 | 合并为一次 validated tuple                    |
| DB-03 | **HIGH**   | `validation_gate.py:244-303`        | `assert_can_write` / `assert_can_write_with` 几乎整段复制            | 双入口 ~60 行镜像            | 确认 | 合并为 `assert_can_write(..., *, con=None)`   |
| DB-04 | **MEDIUM** | `write_manager.py:298-305`          | `hasattr(gate, "assert_can_write_with")` 鸭子类型                    | 无统一 gate 协议             | 确认 | 删除 hasattr 分支                             |
| DB-05 | **MEDIUM** | `validation_gate.py`                | `_fetch_report` 等各自 `con is None → reader()` 分支                 | 三分支重复                   | 确认 | 抽 `_with_con(con, fn)`                       |
| DB-06 | **MEDIUM** | `write_manager.py:354-372`          | `own_transaction=False` + `duckdb.Error` 不写 audit/sidecar          | 与 validation 失败路径不对称 | 确认 | 统一失败审计行为                              |
| DB-07 | **MEDIUM** | `validation_gate.py:71,148`         | `_SCHEMA_APPROVED_MODES` 无 WriteManager 写入方                      | 死策略路径                   | 确认 | 落地 manual_patch 前移除或 ADR                |
| DB-08 | **LOW**    | `connection.py` `_apply_pragmas`    | 每次 reader/writer 都 mkdir + psutil                                 | ~30 行（有 profile 需求）    | 确认 | 加注释说明必要性；可选缓存                    |
| DB-09 | **LOW**    | `write_manager.py` `_write_audit`   | 固定 `rows_deleted=0`, `traceback_digest=None`                       | 占位字段噪音                 | 确认 | 删占位或填真实值                              |

**模块测试：** write_manager / validation_gate / duckdb / schema_contract — 主会话 **全部通过**

---

### 4.4 模块 A4 — `sync/`（7 项）

| ID    | 级别       | 位置                              | 问题                                                          | 证据                                                            | 核实 | 修复方向                                  |
| ----- | ---------- | --------------------------------- | ------------------------------------------------------------- | --------------------------------------------------------------- | ---- | ----------------------------------------- |
| SY-01 | **HIGH**   | `runners.py:365-621`              | `BackfillShardRunner.run` **~256 行 monolith**                | for + 多层 if/continue/return                                   | 确认 | 单 shard 函数 + early return              |
| SY-02 | **HIGH**   | `runners.py:242-327` vs `449-583` | incremental 与 backfill **镜像编排** (~80+ 行)                | validate→quality fail→conflict→write 重复                       | 确认 | 抽 `_PipelineMixin._finalize_staged(...)` |
| SY-03 | **MEDIUM** | `runners.py:465-596`              | 事件路径不一致                                                | `_emit_event` / `emit_custom_event` / `transition+payload` 混用 | 确认 | 统一单一 emit 入口                        |
| SY-04 | **MEDIUM** | `runners.py:187-221`              | Fetch / ResourceGuard 双路径                                  | adapter 走 `begin_fetching`；fetch_callable 内联捕获            | 确认 | 统一 `_fetch_with_guard`                  |
| SY-05 | **MEDIUM** | `runners.py:629-789`              | `ReconcileJobRunner.run` **~161 行**                          | 内联 SQL + 冲突校验，未复用 mixin                               | 确认 | 复用 staging 后处理或拆函数               |
| SY-06 | **LOW**    | `orchestrator.py:133-159`         | `run_incremental` / `run_backfill` 重复 `PipelineConfig` 构造 | 两处相同 kwargs                                                 | 确认 | 提取 `_default_pipeline_config(...)`      |
| SY-07 | **LOW**    | `jobs.py:467-480`                 | `_is_allowed` backfill/reconcile 特例分支                     | transition 矩阵难一眼看清                                       | 确认 | 表驱动或文档化矩阵                        |

**模块测试：** `test_sync_*.py` ~29 项 — 主会话 **全部通过**

---

### 4.5 模块 A5 — `ops/`（6 项）

| ID    | 级别       | 位置                                                                 | 问题                                                          | 证据                                                                                                          | 核实 | 修复方向                                                              |
| ----- | ---------- | -------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ---- | --------------------------------------------------------------------- |
| OP-01 | **HIGH**   | `live_pilot.py`（**~1428 LOC**）                                     | god module：授权+runtime fetch+证据编排+格式化+关闭全在一文件 | 30+ 顶层函数；`capture_phase4_validation` L971-1166 **~196 行**                                               | 确认 | 按 phase/seam 拆 ≤300 LOC/文件                                        |
| OP-02 | **HIGH**   | `live_pilot.py` + `interface_probe.py:29`                            | 证据工具 vs 运行时未分离                                      | `interface_probe` import `live_pilot._key_table_row_counts` 私有符号                                          | 确认 | 抽 `ops/mutation_proof.py` 共享；018C 禁止 import live_pilot 私有 API |
| OP-03 | **MEDIUM** | `live_pilot_fetch_ports.py:75` + `interface_probe_fetch_ports.py:19` | 重复 fetch port 抽象                                          | `_recent_window_start` 两处各一份；Akshare equity 模式近似重复                                                | 确认 | `ops/fetch_port_common.py` 合并                                       |
| OP-04 | **MEDIUM** | `live_pilot.py` 多个 capture 函数                                    | 超长 monolith 方法                                            | `capture_phase4_validation` ~196 行；`run_live_pilot_raw_only` ~107 行；`capture_phase3_raw_evidence` ~107 行 | 确认 | 拆 load/validate/write artifact 步骤                                  |
| OP-05 | **MEDIUM** | `db_inspector.py`（**~429 LOC**）                                    | 单文件接近体量上限                                            | 单类 + 多 helper，职责尚可但偏长                                                                              | 确认 | 可选拆 report formatter                                               |
| OP-06 | **LOW**    | `interface_probe.py`（**~353 LOC**）                                 | 运行时与证据流水线混装                                        | `run_single_probe` + `run_interface_probe` 同文件；无专属 `test_ops_interface_probe.py`                       | 确认 | 拆 evidence 模块 + 补测试                                             |

**模块测试：** ops/batch275/policy — 主会话 **全部通过**（2 skip 来自其他套件）

---

### 4.6 模块 A6 — `layer2_sensors/`（9 项）

| ID    | 级别       | 位置                                     | 问题                                                         | 证据                                                                    | 核实 | 修复方向                                       |
| ----- | ---------- | ---------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------- | ---- | ---------------------------------------------- |
| L2-01 | **HIGH**   | `layer2_sensors/lineage.py` vs L1/L5     | lineage 逻辑三重复制                                         | `LINEAGE_REQUIRED_FIELDS`、`_AGENT_SOURCE_PATTERN` 等 17 字段逐字相同   | 确认 | 抽共享 `core/snapshot_lineage.py`              |
| L2-02 | **HIGH**   | `models.py` / lineage                    | `Layer2LineageEnvelope` 与 L1 `LineageEnvelope` 字段完全一致 | 仅 `layer_id` 语义不同                                                  | 确认 | 共用 dataclass + `layer_id` 参数               |
| L2-03 | **HIGH**   | `snapshot_builder.py:215,350`            | `layer2_lineage_to_axis_tuple` 绕路桥接                      | L2 envelope → L1 envelope → L1 tuple，绕过 L2 `lineage_row_to_db_tuple` | 确认 | writer 直接 `lineage_row_to_db_tuple(lineage)` |
| L2-04 | **MEDIUM** | `snapshot_builder.py`（**365 LOC**）     | Builder + Writer 同文件                                      | `CrossAssetSnapshotBuilder` + `Layer2SnapshotWriter`                    | 确认 | Writer 迁至 `snapshot_writer.py`               |
| L2-05 | **MEDIUM** | builder vs `observation_writer.py`       | 重复 observation 校验                                        | 两处 `assert_observation_asset_match` / `filter_observations_for_as_of` | 确认 | 抽 `prepare_staged_observations(...)`          |
| L2-06 | **MEDIUM** | 4 个 writer                              | staging-write 样板重复 4 份                                  | `stg_l2_*` → CREATE → INSERT → WriteRequest → WriteManager              | 确认 | 抽 `write_staging.py` 统一样板                 |
| L2-07 | **LOW**    | `resource_guard_helper.py`（**16 LOC**） | 单函数微文件                                                 | 仅包装 ResourceGuard                                                    | 确认 | 可内联到调用方（非必须）                       |
| L2-08 | **LOW**    | `observation_writer.py` 域守卫           | L2 比 L1 writer 厚 ~60 LOC                                   | `display_only_write`、`guard_layer2_writeback`                          | 确认 | **属合理域差异**，保留；文档说明即可           |
| L2-09 | **LOW**    | `sensor_loader.py`                       | staged-only gate + registry 字段校验                         | 对齐 axis_loader 契约风格                                               | 确认 | **属合理增量**，保留                           |

**模块测试：** `test_layer2_sensor_loader.py` 32 项 — 主会话 **全部通过**

---

### 4.7 模块 A7 — `validators/`（8 项）

| ID    | 级别       | 位置                                   | 问题                                    | 证据                                                | 核实  | 修复方向                                             |
| ----- | ---------- | -------------------------------------- | --------------------------------------- | --------------------------------------------------- | ----- | ---------------------------------------------------- | ----------------------------------- |
| VA-01 | **LOW**    | `data_quality.py:80-89`, `561-562`     | common 薄包装重复                       | `_is_missing/_as_text/_as_float/_fetch_rows` 纯转发 | 确认  | 直接 `from common import ...`                        |
| VA-02 | **LOW**    | `source_conflict.py:97-102`, `211-212` | 同上                                    | `_as_float/_as_text/_fetch_rows` 转发               | 确认  | 删除 wrapper                                         |
| VA-03 | **LOW**    | `common.py` vs 两 validator            | `as_text(None)` 语义不一致              | common 返回 `"None"` 字符串；DQ 标注 `str           | None` | 确认                                                 | 统一契约，去掉 `or "None"` 双重兜底 |
| VA-04 | **MEDIUM** | `data_quality.py:461-547`              | `validate_rows` **~87 行**              | 主循环 + 多域规则编排                               | 确认  | 可选拆 `_check_row_batch` / `_check_aggregate_rules` |
| VA-05 | **MEDIUM** | `data_quality.py:564-634`              | `_persist_report` **~71 行**            | 双表 INSERT + lineage JSON                          | 确认  | 抽 SQL 常量或 `_insert_report_rows`                  |
| VA-06 | **MEDIUM** | `data_quality.py:282-356`              | `_add_market_bar_findings` **~75 行**   | enum + 5 字段负价 + volume/amount 重复 append       | 确认  | 字段→rule_id 小表驱动                                |
| VA-07 | **LOW**    | YAML vs Python `rule_id`               | 契约双轨                                | 增删规则需改代码；YAML 主要管 severity              | 确认  | 文档化或生成 rule_id 常量                            |
| VA-08 | **LOW**    | `data_quality.py:550`                  | `_table_exists` 用 `quote_ident` 副作用 | 返回值未使用 quote 结果                             | 确认  | 显式校验或删冗余                                     |

**积极面：** 无通用 rule engine；命令式校验符合 ponytail。

**模块测试：** DQ + conflict 34 项 — 主会话 **全部通过**

---

### 4.8 模块 A8 — `storage/` + `core/` + `layer5_evidence/` + 根（6 项）

| ID    | 级别       | 位置                                | 问题                                      | 证据                                               | 核实 | 修复方向                                |
| ----- | ---------- | ----------------------------------- | ----------------------------------------- | -------------------------------------------------- | ---- | --------------------------------------- |
| SC-01 | **HIGH**   | L1/L2/L5 `lineage.py`               | 跨层 lineage **三重复制**                 | 三文件 `LINEAGE_REQUIRED_FIELDS` 等 ~150+ 行可复制 | 确认 | 抽 `core/snapshot_lineage.py` 共享内核  |
| SC-02 | **MEDIUM** | `staged_evidence.py:35-37`          | WriteManager 旁路仅靠约定                 | Phase3 bypass 有文档；无 runtime phase 锁          | 确认 | 契约测试 + 可选 `phase=` 参数门禁       |
| SC-03 | **MEDIUM** | `resource_guard.py:339 LOC`         | `evaluate()` 8 路 `_signal_decision` 重复 | 可表驱动压缩 ~40-60 LOC                            | 确认 | 阈值信号改 data-driven 循环             |
| SC-04 | **LOW**    | `test_config.py`                    | 未测 `get_resource_profile()` 非法值      | 仅测 env path                                      | 确认 | 补合法/非法 profile 用例                |
| SC-05 | **LOW**    | `util/error_redaction.py`           | 已接入 db/sync/datasources 持久化路径   | `fetch_log.py` · `write_manager.py` · `jobs.py` import `redact_error_message` | **CLOSED@PROMPT_17** | 扫描“无引用”为误报；见 §10 delta 与 `debt-round3-ponytail-low-touch` merge gate |
| SC-06 | **LOW**    | `api_limits.py:8` vs `config.py:19` | `CONFIGS_ROOT` 双源                       | 两处 `PROJECT_ROOT / "configs"`                    | 确认 | `api_limits` 改用 `config.CONFIGS_ROOT` |

**合规保留（非违规，记录备查）：**

- `path_compat.py` — Windows 深路径必需，**不得删除**（`test_path_compat.py` 覆盖）
- `config.py` / `main.py` — 体量与职责符合 ponytail
- `raw_store.py` / `file_registry.py` — 精简合格

**模块测试：** raw_store / resource_guard / layer5 / config — 主会话 **全部通过**

---

## 5. 跨模块共性债务（汇总）

| 主题                       | 涉及模块                | 发现 ID                           | 优先级 |
| -------------------------- | ----------------------- | --------------------------------- | ------ |
| lineage 三重复制           | L1 / L2 / L5 / SC       | L2-01, L2-02, SC-01               | P0     |
| evidence 与 runtime 混装   | L1 / ops                | L1-01, L1-06, L1-07, OP-01, OP-02 | P0     |
| 超长 monolith 函数         | L1 / ops / sync / db    | L1-02, OP-01, OP-04, SY-01, DB-01 | P1     |
| staging-write 样板         | L1 lineage / L2 writers | L1-09, L2-06                      | P1     |
| fetch_log / factory 双路径 | datasources             | DS-01, DS-02, DS-03               | P1     |
| WriteManager 复杂度        | db / storage            | DB-01–07, SC-02                   | P1     |

---

## 6. 测试复验摘要

**主会话命令：**

```bash
python -m pytest \
  tests/test_layer1_axis_loader.py tests/test_layer1_ingestion_gates.py \
  tests/test_layer1_interpretation.py tests/test_layer1_observation_ingestion.py \
  tests/test_datasource_service.py tests/test_source_route_planner.py \
  tests/test_source_registry.py tests/test_source_capabilities.py \
  tests/test_data_adapter_contract.py \
  tests/test_write_manager.py tests/test_db_validation_gate.py \
  tests/test_duckdb_connection.py tests/test_schema_contract.py \
  tests/test_sync_jobs.py tests/test_sync_orchestrator.py \
  tests/test_sync_migration.py tests/test_sync_pipeline_contract.py \
  tests/test_ops_db_inspector.py tests/test_batch275_live_pilot_gate.py \
  tests/test_production_live_pilot_policy.py \
  tests/test_layer2_sensor_loader.py \
  tests/test_data_quality_validator.py tests/test_source_conflict_validator.py \
  tests/test_raw_store.py tests/test_resource_guard.py \
  tests/test_layer5_evidence_foundation.py tests/test_config.py -q
```

**结果：** exit 0；**全部通过**；观察到 **2 skipped**（来自套件内条件 skip，非失败）。

**含义：** 当前 ponytail 债务是 **可维护性 / 极简性** 问题，不是立即功能回归；任何修复必须保持上述测试绿。

---

## 7. 达到「严格遵守 /ponytail」的最小修复路线图

### 7.1 P0（阻塞 PASS）

1. **拆分 `live_pilot.py`** → auth / runtime / evidence / closeout / mutation_proof（OP-01, OP-02）
2. **去除 `ingestion.py` evidence re-export** + 外迁 inventory/evidence（L1-01, L1-06, L1-07）
3. **抽取共享 lineage 内核**（L2-01, L2-02, SC-01）

### 7.2 P1（模块分数拉升至 95+）

4. 拆分 `commit_clean_observation_and_snapshots`（L1-02, L1-03）
5. 统一 datasources fetch_log owner + factory（DS-01–03）
6. 合并 `DbValidationGate` 双入口 + 简化 `WriteManager` 事务（DB-01–06）
7. 提取 sync incremental/backfill 共享 finalize（SY-01, SY-02）
8. 删除 validators common 薄包装（VA-01, VA-02）

### 7.3 P2（LOW 项清零）

9. 其余 **24 项 LOW** 按模块迭代消化（见第 4 节完整表）

---

## 8. 最终判定

| 判定项                     | 结果                                                                   |
| -------------------------- | ---------------------------------------------------------------------- |
| 正式实现是否符合 /ponytail | **否 — FAIL**                                                          |
| 功能正确性（测试）         | **通过**                                                               |
| 登记发现项完整性           | **69 项 HIGH/MEDIUM/LOW 已全部收录，无遗漏**                           |
| 建议下一步                 | 按 §7 P0→P1→P2 顺序 TDD 修复；每模块修复后重跑对应 pytest + 本报告复验 |

---

## 9. 附录 — Agent 报告索引

本轮 Agent 原始输出可参考工作区 `临时报告/` 下 Round3 Batch2.5 系列；**本文件为 2026-06-22 模块级 ponytail 大扫描的权威汇总**，以主会话核实后的 69 项登记为准。

---

## 10. Post PROMPT_16/17 delta（2026-06-22）

> **Authority:** `fix/round3-ponytail-pilot-prep-bucket-a` (PROMPT_16), `debt/round3-ponytail-low-touch` (PROMPT_17), `docs/quality/adversarial_audit_post14_contract_ponytail_lane.md`.  
> **Merge gate:** 下列 ID 在 post-14 审计中已验证闭合；§4 原表保留为历史扫描基线，勿重复登记为 OPEN。

| ID    | Bucket | Closure summary                                                                                      | Evidence                                                                 |
| ----- | ------ | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| DS-01 | A      | `fetch_log` 双写路径统一为 service-authoritative                                                       | `test_r3x_ponytail_pilot_prep_bucket_a.py` · PROMPT_16 merge gate        |
| DS-02 | A      | Adapter factory 单路径                                                                                 | same                                                                     |
| DS-03 | A      | `record_fetch_log` 参数化                                                                             | same                                                                     |
| SC-02 | A      | `staged_evidence` phase lock 文档 + 契约测试                                                           | PROMPT_16                                                                |
| OP-02 | A      | `mutation_proof` 最小闭环                                                                              | PROMPT_16                                                                |
| SY-04 | A      | `_fetch_with_guard` 抽取                                                                               | PROMPT_16                                                                |
| VA-03 | A      | validation gate 路径                                                                                   | PROMPT_16                                                                |
| SC-03 | C      | `resource_guard.evaluate()` 表驱动                                                                       | PROMPT_17 · `debt-round3-ponytail-low-touch`                             |
| SC-04 | C      | `get_resource_profile` 合法/非法测试                                                                   | PROMPT_17                                                                |
| SC-05 | C      | `error_redaction` **wired** in db/sync/datasources（非死代码）                                         | PROMPT_17 · module docstring · ADV-POST14-B-003 fix                      |
| SC-06 | C      | `api_limits` → `config.CONFIGS_ROOT` 单源                                                              | PROMPT_17                                                                |
| VA-01 | C      | DQ thin wrappers 删除                                                                                  | PROMPT_17                                                                |
| VA-02 | C      | conflict thin wrappers 删除                                                                            | PROMPT_17                                                                |
| VA-07 | C      | YAML/Python `rule_id` 双轨文档化                                                                       | PROMPT_17                                                                |
| VA-08 | C      | `_table_exists` 冗余 `quote_ident` 副作用移除                                                          | PROMPT_17                                                                |

**仍 OPEN（Bucket B，53 项）：** SC-01, L1-01, L2-01/02, OP-01, SY-01, DB-01 等 — 见 `adversarial_audit_post14_master_fix_manifest.md` Slice 4。
