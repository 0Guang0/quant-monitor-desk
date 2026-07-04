# 执行索引 — M-G1-03 Layer1 + Sync 架构解耦

> **v4.2 计划正文：** `EXECUTION_PLAN.md`（AC 语义 SSOT）  
> **本文件 §1–§2：** 量化验收路由 · **关账证据**与 PLAN Verify **一一对应**（禁止仅用代理旧测冒充完成）  
> **协议：** Slim Plan v4.2 · `frozen/` 为活卡薄指针

## 0. 冻结元数据

| 字段          | 值                                                                     |
| ------------- | ---------------------------------------------------------------------- |
| slug          | `07-04-m-g1-03-layer1-full`                                            |
| protocol      | `4.2`                                                                  |
| execute_entry | `EXECUTION_PLAN.md`                                                    |
| source_card   | `docs/implementation_tasks/M_G1_03_LAYER1_FULL/M_G1_03_LAYER1_FULL.md` |
| frozen_at     | 2026-07-04（§1–§2 加固 @ 2026-07-04）                                  |
| 前置          | M-DATA-03 **CLOSED** @ 2026-07-04 · ADR-034                            |
| 票结构        | **B** — Phase 1 → **P1-GATE** → Phase 2 → **P2-GATE**                  |

### 0.1 验收分层（L0–L4 · 对齐 `全局规则.txt`）

| 层     | 含义         | 本票关账                                      |
| ------ | ------------ | --------------------------------------------- |
| **L0** | 模块业务关账 | G1/K1/K2 **MCR ≥ R4**                         |
| **L1** | 门禁 + 人工  | P1/P2-GATE 全勾 · `ready-for-human`           |
| **L2** | 契约字段     | YAML/contract 无 reserved/违规 import         |
| **L3** | 机制/结构    | executor 唯一 · ops LOC · CLI 登记            |
| **L4** | 机器证据     | §2 专测 + 脚本 **GREEN** · `uv run pytest -q` |

**Pass ≠ 任意旧测绿。** 每 Step 须 L4 专测绿 + §1「量化 Done」勾选 +（票末）L0–L1。

---

## 1. 步骤与证据（Execute · v4.2）

| Step        | PLAN             | 业务交付（用户可感知）                     | 量化 Done（全勾才 `[x]`）                                                                                  | RED 关账证据                                                                                                                                                | GREEN 关账证据                               | 禁止提前宣称              | 运行证据（关账贴附）                   | 完成  |
| ----------- | ---------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ------------------------- | -------------------------------------- | ----- |
| **S01**     | P1-01..04        | 62 行绑定矩阵骨架 + 边界契约可检           | ☐ registry 文件存在 ☐ 62 行 ☐ `check_indicator_binding_matrix.py` exit 0 ☐ boundary RED 可检出 layer fetch | `scripts/check_indicator_binding_matrix.py` · `tests/test_module_boundaries.py` · `tests/test_indicator_binding_registry.py`                                | 上列全绿 + `check_module_boundaries.py`      | P1-14 ingestion 已迁出    | 矩阵行数截图/日志；boundary RED 输出   | `[ ]` |
| **S02**     | P1-05..06′       | watermark/mapper/executor 唯一编排         | ☐ `read_watermark` 单入口 ☐ mapper 纯函数 ☐ **仅** `execute_binding` 编排                                  | `tests/test_sync_watermark.py` · `tests/test_sync_macro_mapper.py` · `tests/test_sync_binding_executor.py`                                                  | 三测绿 + 删除测试成立                        | FullLoad/scheduler 已落地 | executor 单测日志                      | `[ ]` |
| **S03**     | P1-07..09        | FullLoad 机制 + 契约 + CLI                 | ☐ `full_load`∈implemented ☐ §13.4.1 断点续跑 ☐ CLI 登记 `data_cli_contract`                                | `tests/test_sync_full_load.py` · `tests/test_sync_job_contract.py` · `tests/test_qmd_data_full_load_cli.py` · `tests/test_data_cli_contract.py`             | 四测绿 · `qmd-data data full-load --dry-run` | Tier A backfill 已扩      | dry-run CLI 输出                       | `[ ]` |
| **S04**     | P1-10..12        | Backfill 扩域 + ops 薄绑定                 | ☐ 11 源 domain 可 backfill ☐ ADR-030 cap ☐ ops 无内联 orchestration                                        | `tests/test_qmd_data_backfill_cli.py` · `tests/test_bounded_backfill_cap.py` · `tests/test_sync_binding_executor.py` · `tests/test_tier_a_live_dispatch.py` | 全绿 · `fred_incremental_run` LOC 显著下降   | Layer facade 已接         | ops 文件 LOC diff                      | `[ ]` |
| **S05**     | P1-13..14        | Layer 只经 `sync_indicator`；无直连 vendor | ☐ `layer1_axes` 无 `datasources.service` ☐ ingestion 改调 facade                                           | `tests/test_layer1_sync_facade.py` · `tests/test_module_boundaries.py` · `tests/test_layer1_observation_ingestion.py`                                       | 三测绿 · boundary **GREEN**                  | 62 指标真链               | `rg DataSourceService layer1_axes` = 0 | `[ ]` |
| **S06**     | P1-15..17        | §13.7 CLI 余量 + §13.6 scheduler + 五 job  | ☐ scheduler profile 展开 binding ☐ 五 job 非空壳 ☐ CLI 登记                                                | `tests/test_sync_scheduler.py` · `tests/test_sync_orchestrator.py` · `tests/test_data_cli_contract.py`                                                      | 全绿 · `scheduler run --dry-run`             | P1-GATE 已人工确认        | scheduler dry-run 日志                 | `[ ]` |
| **P1-GATE** | Success Criteria | Phase 1 同步子系统完整可运营               | ☐ §2.2 全勾 ☐ L2–L4 ☐ 人工                                                                                 | —                                                                                                                                                           | §2.2 + `uv run pytest -q`                    | Phase 2 开工              | 隔离库 macro e2e 证据                  | `[ ]` |
| **S07**     | P2-01            | 矩阵 strict + ADR 逐条关账                 | ☐ `--strict` exit 0 ☐ 无 `adr_id=PENDING`                                                                  | `scripts/check_indicator_binding_matrix.py --strict`                                                                                                        | strict 绿                                    | 源批次真链                | strict 报告                            | `[ ]` |
| **S08**     | P2-02 macro      | fred/treasury/bis/wb 批真链                | ☐ 批内矩阵行各 1 条真链 e2e                                                                                | `tests/test_layer1_indicator_binding_macro_batch.py`                                                                                                        | 批测绿 · 同库 lineage                        | 他批完成                  | 隔离库查询/日志                        | `[ ]` |
| **S09**     | P2-02 COT        | cftc_cot 批真链                            | ☐ 批内全行真链                                                                                             | `tests/test_layer1_indicator_binding_cot_batch.py`                                                                                                          | 批测绿                                       | 同上                      | 同上                                   | `[ ]` |
| **S10**     | P2-02 CN bar     | baostock/mootdx 批真链                     | ☐ 批内全行真链                                                                                             | `tests/test_layer1_indicator_binding_cn_bar_batch.py`                                                                                                       | 批测绿                                       | 同上                      | 同上                                   | `[ ]` |
| **S11**     | P2-02 US/crypto  | alpha_vantage/deribit 批真链               | ☐ 批内全行真链                                                                                             | `tests/test_layer1_indicator_binding_us_crypto_batch.py`                                                                                                    | 批测绿                                       | 同上                      | 同上                                   | `[ ]` |
| **S12**     | P2-02 filings    | cninfo/sec_edgar 批真链                    | ☐ 批内全行真链                                                                                             | `tests/test_layer1_indicator_binding_filings_batch.py`                                                                                                      | 批测绿                                       | 同上                      | 同上                                   | `[ ]` |
| **S13**     | P2-08..10        | 特征/解读/读模型形状                       | ☐ 特征诚实 NULL ☐ 解读 profile ☐ §6.4–6.5 列形状                                                           | `tests/test_layer1_feature_engine.py` · `tests/test_layer1_interpretation.py` · `tests/test_layer1_round4_read_model_shape.py`                              | 三测绿                                       | Round4 HTTP               | 读模型断言输出                         | `[ ]` |
| **P2-GATE** | Success Criteria | 62 指标全链路 + G1 R4                      | ☐ §2.3 全勾 ☐ L0                                                                                           | —                                                                                                                                                           | §2.3 + MCR 跃迁                              | 票 CLOSED                 | Audit A1–A8                            | `[ ]` |

> **RED 占位：** 专测文件已建并 `pytest.mark.skip`（M-G1-03 Execute 实现后去 skip 转 RED→GREEN）。  
> **竖切 Issue：** `research/to-issues-slices.md`。

---

## 2. AC 五列卡（PLAN Acceptance → 量化关账）

| AC-ID         | 业务成品             | 设计/契约锚点                                                          | 量化断言（可勾选）                                                 | 关账证据命令                                                                                        | 反冒充              |
| ------------- | -------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- | ------------------- |
| P1-01         | 62×指标绑定 SSOT     | `indicator_binding_registry.yaml` · EXECUTION_PLAN §9.1                | 62 行；schema 列齐全；`adr_id` 可 PENDING                          | `python scripts/check_indicator_binding_matrix.py`                                                  | 空 YAML/少行仍绿    |
| P1-02         | 类型安全绑定加载     | §9.1 · `indicator_binding.py`                                          | frozen dataclass 1:1；`UnknownIndicatorError`+`CAPABILITY_MISSING` | `pytest tests/test_indicator_binding_registry.py -q`                                                | 裸 `ValueError`     |
| P1-03/04      | 边界契约可检         | `module_boundary_contract.yaml` · `module_boundary_matrix.md`          | `layer*` must_not_import `datasources.service`；RED 可检出         | `check_module_boundaries.py` · `test_module_boundaries.py`                                          | S01 宣称 P1-14 完成 |
| P1-05         | 统一 watermark       | `data_sync_orchestrator.md` §13                                        | 单 `read_watermark(domain,key)`；macro+bar                         | `pytest tests/test_sync_watermark.py -q`                                                            | ops 双实现          |
| P1-06         | 纯函数 mapper        | `sync/mappers/`                                                        | macro→axis_observation；无 orchestrator 调用                       | `pytest tests/test_sync_macro_mapper.py -q`                                                         | mapper 内 fetch     |
| P1-06′        | **唯一**编排深度模块 | AD-MG103-10 · §9.2                                                     | **仅** `execute_binding`；删除测试失败若编排散落                   | `pytest tests/test_sync_binding_executor.py -q`                                                     | facade/ops 复制编排 |
| P1-07/08      | FullLoad 机制        | §13.4.1 · `sync_job_contract.yaml`                                     | 无 `DeferredJobTypeError`；`full_load` implemented                 | `test_sync_full_load` · `test_sync_job_contract`                                                    | reserved full_load  |
| P1-09         | full-load CLI        | `data_cli_contract.yaml` · ERROR_CODE_GUIDE                            | 登记；`CliFailure`；`--dry-run` 默认                               | `test_qmd_data_full_load_cli` · `test_data_cli_contract`                                            | 未登记命令          |
| P1-10..12     | Backfill+ops 薄绑定  | ADR-030 · `incremental_source_registry.py`                             | 全 Tier A domain；ops→executor；LOC↓                               | `test_qmd_data_backfill_cli` · `test_bounded_backfill_cap` · `test_tier_a_live_dispatch`            | ops 内联 DDL/sync   |
| P1-13/14      | Layer 接缝           | AD-MG103-11 · facade                                                   | `sync_indicator`=load+execute；ingestion 无 fetch                  | `test_layer1_sync_facade` · `test_module_boundaries` · `test_layer1_observation_ingestion`          | Layer 直连 vendor   |
| P1-15..17     | CLI+scheduler+五 job | §13.6–13.7 · `sync_scheduler_profiles.yaml`                            | profile→registry→executor；五 job 非空壳                           | `test_sync_scheduler` · `test_sync_orchestrator` · `test_data_cli_contract`                         | 硬编码 series 列表  |
| P2-01         | 矩阵 strict          | K2 · README §指标全链路                                                | 62 行填满；`adr_id` 无 PENDING                                     | `check_indicator_binding_matrix.py --strict`                                                        | strict 未跑         |
| P2-02 S08–S12 | 分源批次真链         | `restructured_axes_v1_1/**` · ADR-034 输入                             | 批内矩阵行各真链；同库 lineage；**非 seed**                        | `test_layer1_indicator_binding_*_batch.py`                                                          | 每轴 1 代表         |
| P2-08..10     | 特征/解读/读模型     | `layer1_global_regime_panel.md` §6.4–6.5 · `layer1_axis_contract.yaml` | 诚实 NULL；列形状子集                                              | `test_layer1_feature_engine` · `test_layer1_interpretation` · `test_layer1_round4_read_model_shape` | seed 特征           |

### 2.1 四层验收（Tier · L4 机器层）

| 层  | 命令                                                                       | 环境                       |
| --- | -------------------------------------------------------------------------- | -------------------------- |
| A   | `uv run pytest -q`                                                         | local/ci                   |
| B   | `uv run python scripts/check_module_boundaries.py`                         | local/ci                   |
| C   | `uv run python scripts/check_indicator_binding_matrix.py`（P2 `--strict`） | local/ci                   |
| D   | `uv run python scripts/loop_maintain.py`                                   | 触达 specs/docs/backend 后 |

### 2.2 P1-GATE 关账清单（L1 人工 + L2–L4）

| #   | 断言（对应 EXECUTION_PLAN）                         | L2–L4 证据                                                 | 人工 |
| --- | --------------------------------------------------- | ---------------------------------------------------------- | ---- |
| 1   | `full_load` implemented；contract 无 reserved       | `test_sync_full_load` · `test_sync_job_contract`           | ☐    |
| 2   | Backfill ≥ Tier A 全 domain（含 macro_series）      | `test_qmd_data_backfill_cli` · registry 对照               | ☐    |
| 3   | §13.7 CLI + §13.6 scheduler 可执行                  | `test_sync_scheduler` · `test_data_cli_contract` · dry-run | ☐    |
| 4   | module_boundary 绿；layer1 无 fetch                 | `check_module_boundaries` · `test_module_boundaries`       | ☐    |
| 5   | BindingSyncExecutor 唯一；ops 无内联编排            | `test_sync_binding_executor` · ops LOC 审查                | ☐    |
| 6   | 62 行矩阵 + check 脚本绿                            | `check_indicator_binding_matrix.py`                        | ☐    |
| 7   | macro_series→axis_observation 隔离库 e2e（非 seed） | `test_layer1_observation_ingestion` + 运行日志             | ☐    |
| 8   | `uv run pytest -q` exit 0                           | CI/local 全绿                                              | ☐    |

### 2.3 P2-GATE 关账清单（L0–L1）

| #   | 断言                             | 证据                                                 | 人工 |
| --- | -------------------------------- | ---------------------------------------------------- | ---- |
| 1   | 矩阵 `--strict`；62 指标同库真链 | strict 脚本 + 五批 `test_layer1_indicator_binding_*` | ☐    |
| 2   | G1 **MCR ≥ R4**；K1/K2 随父跃迁  | `MODULE_COMPLETION_RATING.md` 更新                   | ☐    |
| 3   | `tests/test_layer1_*` 相关全绿   | `uv run pytest -q tests/test_layer1_*`               | ☐    |
| 4   | Audit A1–A8 PASS                 | `audit.report.md`                                    | ☐    |

---

## 3. 必须读原文（manifest · Execute Boot 必读）

> **分类：** `[1]` 工单 · `[2]` 设计 · `[3]` 轴规格 · `[4]` 契约 · `[5]` ADR · `[6]` 代码 SSOT · `[7]` 运维 · `[8]` 全局规则  
> **Execute 创建：** `indicator_binding_registry.yaml`（P1-01）· `sync_scheduler_profiles.yaml`（P1-16）

| path                                                                       | manifest  | audience | extract             | for            |
| -------------------------------------------------------------------------- | --------- | -------- | ------------------- | -------------- |
| `docs/implementation_tasks/M_G1_03_LAYER1_FULL/M_G1_03_LAYER1_FULL.md`     | must-read | execute  | [1] 活卡指针        | Boot           |
| `docs/implementation_tasks/M_G1_03_LAYER1_FULL/M_G1_03_TO_ISSUES_INDEX.md` | must-read | execute  | [1] /to-issues 索引 | Boot · 派发    |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                                        | must-read | execute  | [1] 路线图 §3.2     | Boot           |
| `MODULE_COMPLETION_RATING.md`                                              | must-read | execute  | [1] G1/K1/K2 R3→R4  | Boot · P2-GATE |
| `docs/modules/data_sync_orchestrator.md`                                   | must-read | both     | [2] Sync §13.4–13.9 | Boot · S02–S06 |
| `docs/modules/layer1_global_regime_panel.md`                               | must-read | both     | [2] 读模型 §6.4–6.5 | S13            |
| `docs/architecture/module_boundary_matrix.md`                              | must-read | both     | [2] import 边界     | S01 · S05      |
| `specs/layer1_axes/restructured_axes_v1_1/README.md`                       | must-read | execute  | [3] §指标全链路     | S07–S13        |
| `specs/layer1_axes/restructured_axes_v1_1/common/common_axis_rules.md`     | must-read | execute  | [3] §3 §9           | S07–S13        |
| `specs/contracts/sync_job_contract.yaml`                                   | must-read | both     | [4] 五 job          | S02–S06        |
| `specs/contracts/module_boundary_contract.yaml`                            | must-read | both     | [4] layer\* 边界    | S01 · S05      |
| `specs/contracts/data_cli_contract.yaml`                                   | must-read | execute  | [4] CLI 登记        | S03 · S06      |
| `specs/contracts/bounded_backfill_cap.yaml`                                | must-read | execute  | [4] ADR-030         | S04            |
| `specs/contracts/layer1_axis_contract.yaml`                                | must-read | both     | [4] quality_flags   | S13            |
| `docs/decisions/ADR-034-m-data-03-tier-a-live-acceptance.md`               | must-read | both     | [5] 前置            | Boot           |
| `docs/decisions/ADR-025-r3h10-sync-fail-closed-datasource-service.md`      | must-read | execute  | [5] Sync 金路径     | S02–S06        |
| `docs/decisions/ADR-030-bounded-backfill-cap-and-ci-nightly.md`            | must-read | execute  | [5] Backfill cap    | S04            |
| `backend/app/sync/incremental_source_registry.py`                          | must-read | execute  | [6] 11 源           | S08–S12        |
| `backend/app/sync/jobs.py`                                                 | must-read | execute  | [6] SyncJobSpec     | S02–S06        |
| `backend/app/cli/errors.py`                                                | must-read | execute  | [6] CliFailure      | S03 · S06      |
| `pyproject.toml`                                                           | must-read | execute  | [6] qmd-data        | S03 · S06      |
| `docs/ops/ERROR_CODE_GUIDE.md`                                             | must-read | execute  | [7] 错误码          | S03 · S06      |
| `docs/ops/performance_limits.md`                                           | must-read | execute  | [7] ResourceGuard   | S06            |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`                      | must-read | execute  | [8] 可验证          | Boot           |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                       | must-read | execute  | [8] 五字段/TDD      | Boot           |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`                      | must-read | execute  | [8] 资源限制        | Boot           |
| `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md`                        | must-read | execute  | [8] 任务模板        | Boot           |
| `docs/implementation_tasks/README.md`                                      | must-read | execute  | [8] 活工单目录      | Boot           |

## 5. Audit 追溯集（v4.2 Slim）

| 类别     | 文件                            | 用途                  |
| -------- | ------------------------------- | --------------------- |
| 计划正文 | `EXECUTION_PLAN.md`             | AC · P1/P2 · §9 契约  |
| 量化验收 | 本文 §1–§2                      | L0–L4 · 五列卡 · GATE |
| manifest | 本文 §3                         | 外部必读              |
| 竖切     | `research/to-issues-slices.md`  | S01–S13               |
| 冻结活卡 | `frozen/M_G1_03_LAYER1_FULL.md` | Plan 快照             |
| 审计矩阵 | `AUDIT.plan.md`                 | A1–A8                 |
