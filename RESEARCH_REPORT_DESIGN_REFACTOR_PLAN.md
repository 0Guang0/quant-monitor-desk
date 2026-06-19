# 基于调研分析报告与最新进度的设计调整 / 重构方案

> 生成日期：2026-06-19  
> 生成方式：只读审计；未修改代码、未修改既有设计文档、未修改既有执行计划。  
> 输入材料：用户上传《调研分析报告.md》、当前仓库 `docs/`、`specs/`、`docs/implementation_tasks/`、`ROUND2_REAUDIT_CLOSEOUT.md`、当前实现目录。  
> 审核要求：本文件是待用户审核的方案。用户确认前，不得据此修改设计文档、执行计划或代码。

---

## 0. 当前最新进度判断

### 0.1 已经被最新进度覆盖的旧审计项

当前仓库已经比上一轮九维审计有明显推进。以下项目已经关闭或已有 closeout 记录，不应在后续方案中重复作为未完成 P1/P2 提出：

| 已覆盖项                 | 当前证据                                                                             | 方案处理                                                                           |
| ------------------------ | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| Orchestrator runner 拆分 | `backend/app/sync/runners.py`；`ROUND2_REAUDIT_CLOSEOUT.md` P1-01 / A3-01 说明       | 不再要求“大拆 orchestrator”，仅提出下一阶段 DataSourceService / RoutePlan 接入重构 |
| rule/version/lineage     | `backend/app/validators/rule_contract.py`、migration `008/010`、closeout P1-02/A9-02 | 不再作为 Round2 缺口；后续只要求被 Layer snapshot 消费                             |
| DB CHECK 约束            | migration `009_status_check_constraints.sql`、closeout P1-04/A9-01                   | 不再重复要求；后续只扩展新表/新 enum                                               |
| Reconcile re-fetch       | `ReconcileJobRunner` 中真实调用 adapter.fetch 并重比对                               | 不再重复要求；后续要求 RoutePlan + DataSourceService 化                            |
| Backfill validate/write  | `BackfillShardRunner` 已执行 validate/write                                          | 不再重复要求；后续要求生产等价规模 benchmark                                       |
| vendor fixture E2E       | `tests/test_vendor_fetch_e2e.py`                                                     | 不再重复要求；后续要求真实授权源或更大 fixture-scale 场景                          |
| ADR 补充                 | `docs/decisions/ADR-001/002/003`                                                     | 不再重复要求；后续新增 ADR 只针对参考项目引入的新边界                              |
| ruff gate                | `ROUND2_REAUDIT_CLOSEOUT.md` 记录 ruff green                                         | 不再作为未执行缺口                                                                 |
| ponytail CLI 替代口径    | `docs/decisions/README.md` 明确 ponytail-review/code-simplification 等价             | 不再作为阻塞项                                                                     |

### 0.2 当前仍缺的设计层能力

调研报告提出的核心价值不是“照搬交易项目”，而是把 JQ2PTrade / EasyXT / ptqmt-site 的工程经验转成项目自己的非自动交易、local-first、强审计设计。结合最新进度，当前真正需要补的是：

1. **SourceCapabilityRegistry**：从 source/domain 级别提升到 operation/field/capability 级别。
2. **DataSourceService Facade**：避免 Orchestrator/API/Agent 直接使用 adapter factory。
3. **SourceRoutePlan**：显式、可审计的候选源/禁用源/fallback 计划，禁止 silent fallback。
4. **ModuleBoundaryMatrix**：机器化约束模块之间 import 边界。
5. **Ops/User 文档入口**：从 implementation-task 文档转成用户/运维/开发者路径入口。
6. **BacktestReviewEngine 生命周期契约**：把 Round4 回测从抽象表结构细化为可实现 lifecycle。
7. **Privacy / Local-only / No-action 边界**：面向前端导入、Agent 输入、策略复盘沙箱明确用户数据流。

---

## 1. 总体调整策略

### 1.1 不建议现在改代码

本阶段用户明确要求只读审计。因此本方案只列出后续应如何修改设计文档、契约和执行计划。代码层调整只列为“未来实现变更”，不得在本阶段执行。

### 1.2 推荐新增一个 Round2.6 前置调整包

当前 Round2 修复已经 closeout，Round3 正准备进入建模层。但调研报告中的 `SourceCapabilityRegistry`、`DataSourceService`、`SourceRoutePlan` 属于数据源 / 同步基础设施，不适合塞进 Round3 Layer 1-5 的建模任务，也不应延后到 Round4 API/Agent。建议新增一个**不破坏原 017-023 编号**的前置包：

```text
ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/
```

该包建议使用补充编号：

```text
016A_define_source_capability_registry.md
016B_define_source_route_plan_and_datasource_service.md
016C_define_module_boundary_contract.md
016D_define_data_sync_quick_reference_and_error_guides.md
016E_define_platform_source_matrix_and_qmt_xqshare.md
016F_define_prod_equivalent_scale_benchmark.md
```

这样既不改写已有 Round3 编号，也能在进入真实 adapter / 真实数据规模前补齐关键边界。

---

## 2. 按 ID 列出的调整 / 重构方案

---

## DS-CAP-001：新增数据源能力矩阵 SourceCapabilityRegistry

### 来源与依据

- 调研报告 REF-DATA-001。
- 当前 `source_registry.yaml` 只描述 source/domain/role，不描述 operation / field / granularity / adjustment / incremental capability。
- `docs/modules/data_sources.md` 目前已有“每个 Adapter 只能声明自己支持的 data_domain”，但缺少机器可验证的能力矩阵。

### 当前最新进度判断

当前实现有：

- `SourceRegistry`
- adapter skeleton `supported_domains`
- `create_adapter()` factory
- `FetchPort` / `FetchResult`

但没有：

- `source_capabilities.yaml`
- `CapabilityRegistry`
- operation-level capability 校验
- adapter capability 与 registry 一致性测试

### 需要调整的设计文档

| 文件                                          | 调整方式 | 内容                                                                                               |
| --------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------- |
| `docs/modules/data_sources.md`                | 修改     | 新增 “Source Capability Matrix” 小节，定义 operation/field/granularity/adjustment/incremental 能力 |
| `docs/modules/data_sync_orchestrator.md`      | 修改     | 说明 Orchestrator 创建 fetch plan 前必须检查 capability                                            |
| `docs/architecture/05_module_map.md`          | 修改     | 把 CapabilityRegistry 加入 data_sources 模块地图                                                   |
| `docs/architecture/10_external_references.md` | 修改     | 增加 JQ2PTrade mapping-first 作为参考，但说明只借鉴 mapping，不借鉴交易转换                        |

### 需要新增的设计 / 契约文档

| 新文件                                               | 目的                                                      |
| ---------------------------------------------------- | --------------------------------------------------------- |
| `specs/datasource_registry/source_capabilities.yaml` | 机器契约：source → domain → operation → fields/capability |
| `specs/contracts/source_capability_contract.yaml`    | capability schema 与验收要求                              |
| `docs/modules/source_capability_registry.md`         | 人类可读设计说明                                          |

### 需要修改的执行计划

| 文件                                                                                                  | 修改内容                                                              |
| ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `docs/implementation_tasks/README.md`                                                                 | 新增 Round2.6 包与 `016A_define_source_capability_registry.md`        |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/011_implement_source_registry.md`        | 增加 “后续兼容：SourceRegistry.allowed_domain 必须有 capability 声明” |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/013_implement_core_adapter_skeletons.md` | 增加 adapter supported_domains 必须是 capability 子集                 |

### 当前实现未来需要改变的点

| 模块                                                    | 未来改动                                                                  |
| ------------------------------------------------------- | ------------------------------------------------------------------------- |
| `backend/app/datasources/source_registry.py`            | 不直接扩展为 capability；保持 source registry 职责单一                    |
| 新模块 `backend/app/datasources/capability_registry.py` | 新增，只读加载 capability 契约                                            |
| adapter skeleton                                        | 初始化或 factory 阶段检查 adapter 支持域/operation 是否被 capability 声明 |
| tests                                                   | 新增 `tests/test_source_capabilities.py`                                  |

### 落地验收

```bash
python -m pytest tests/test_source_capabilities.py tests/test_source_registry.py tests/test_adapter_skeletons.py -q
```

### 优先级

P1。进入真实 adapter 与更大生产等价场景前完成。

---

## DS-SVC-001：新增 DataSourceService Facade，收敛 adapter factory 调用点

### 来源与依据

- 调研报告 REF-DATA-002。
- EasyXT 的统一 API facade 值得借鉴，但本项目不能照搬交易 API。
- 当前 `create_adapter()` 已经是显式 factory，但如果 Orchestrator/API/Agent 都直接 import factory，会形成多入口策略漂移。

### 当前最新进度判断

当前实现：

- `create_adapter()` 要求显式 `fetch_port` 与 `file_registry`，生产安全边界较好。
- `DataSyncOrchestrator` 当前仍以 `adapter` 参数形式运行 job。
- 尚无 `DataSourceService`。

### 需要调整的设计文档

| 文件                                     | 调整方式 | 内容                                                                                                       |
| ---------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------- |
| `docs/modules/data_sources.md`           | 修改     | 新增 DataSourceService 职责边界：registry、route plan、ResourceGuard、adapter creation、fetch_log 统一入口 |
| `docs/modules/data_sync_orchestrator.md` | 修改     | 把“根据 data_domain 选择 adapter”改为“调用 DataSourceService.resolve_and_fetch”                            |
| `docs/modules/agent_module.md`           | 修改     | 明确 Agent 不得直接调用 adapter factory，只能通过只读 API / DataSourceService 结果                         |
| `docs/modules/fastapi_backend.md`        | 修改     | API diagnostic/source-route 只读接口由 DataSourceService 提供                                              |

### 需要新增的设计 / 契约文档

| 新文件                                             | 目的                                           |
| -------------------------------------------------- | ---------------------------------------------- |
| `specs/contracts/datasource_service_contract.yaml` | 定义 fetch request lifecycle、错误码、权限边界 |
| `docs/modules/datasource_service.md`               | 设计说明与调用边界                             |

### 需要修改的执行计划

| 文件                                                           | 修改内容                                                                                  |
| -------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 新增 `016B_define_source_route_plan_and_datasource_service.md` | 定义 DataSourceService 与 SourceRoutePlan 的设计和验收                                    |
| `014_implement_data_sync_orchestrator.md`                      | 修改：未来 Orchestrator 不直接接受外部 adapter 或 factory，而是通过 service / runner 注入 |
| `024_implement_fastapi_routes.md`                              | 修改：诊断类路由只能读 service 输出，不直接构造 adapter                                   |
| `025_implement_agent_tool_layer.md`                            | 修改：Agent tool 禁止 import adapter factory                                              |

### 当前实现未来需要改变的点

| 模块                                           | 未来改动                                                               |
| ---------------------------------------------- | ---------------------------------------------------------------------- |
| `backend/app/datasources/adapters/__init__.py` | `create_adapter()` 保留，但标记为 DataSourceService 内部使用           |
| 新模块 `backend/app/datasources/service.py`    | 新增 facade                                                            |
| `backend/app/sync/runners.py`                  | 当前接受 adapter；后续改为接受 `DataSourceService` 或 `fetch_callable` |
| tests                                          | 新增 `tests/test_datasource_service.py`，验证 direct factory 禁止策略  |

### 落地验收

```bash
python -m pytest tests/test_datasource_service.py tests/test_sync_orchestrator.py tests/test_vendor_fetch_e2e.py -q
```

### 优先级

P1。建议 Round2.6 完成，或至少在任何真实 vendor adapter 接入前完成。

---

## DS-ROUTE-001：新增显式 SourceRoutePlan，替代隐式 fallback / skip 逻辑

### 来源与依据

- 调研报告 REF-DATA-003。
- EasyXT 的降级链有借鉴价值，但本项目禁止 silent fallback。
- 当前 `SourceRegistry.assert_domain_schedulable()` 能判断 disabled，但缺少面向运行时、报告、前端展示的 route plan 对象。

### 当前最新进度判断

已有：

- `domain_enabled_by_default`
- `disabled_until_configured`
- `DISABLED_SOURCE`
- fallback disabled tests

缺少：

- `SourceRoutePlan`
- `SourceRouteCandidate`
- route_status / skipped_sources / disabled_reason 的统一 contract
- source route audit log

### 需要调整的设计文档

| 文件                                       | 调整方式 | 内容                                                                       |
| ------------------------------------------ | -------- | -------------------------------------------------------------------------- |
| `docs/modules/data_sources.md`             | 修改     | 在 Primary/Validation/FallbackPolicy 后新增 SourceRoutePlan 明确运行时对象 |
| `docs/modules/data_sync_orchestrator.md`   | 修改     | job PLANNED 阶段必须生成 route plan                                        |
| `docs/modules/frontend_dashboard.md`       | 修改     | 未来前端展示 `selected_source_id`、`skipped_sources`、`disabled_reason`    |
| `docs/modules/notification_and_reports.md` | 修改     | 报告必须显示 fallback / disabled source 事实                               |

### 需要新增的设计 / 契约文档

| 新文件                                       | 目的                   |
| -------------------------------------------- | ---------------------- |
| `specs/contracts/source_route_contract.yaml` | 定义 route plan schema |
| `docs/modules/source_route_plan.md`          | 人类可读设计           |

### 需要修改的执行计划

| 文件                                                      | 修改内容                                       |
| --------------------------------------------------------- | ---------------------------------------------- |
| `016B_define_source_route_plan_and_datasource_service.md` | 新增 RoutePlan 设计与测试要求                  |
| `014_implement_data_sync_orchestrator.md`                 | PLANNED 阶段先记录 route plan，再进入 FETCHING |
| `028_implement_reports_and_notifications.md`              | 通知/报告必须显示 source route status          |

### 当前实现未来需要改变的点

| 模块                                              | 未来改动                                                                    |
| ------------------------------------------------- | --------------------------------------------------------------------------- |
| 新模块 `backend/app/datasources/route_models.py`  | `SourceRoutePlan` / `SourceRouteCandidate`                                  |
| 新模块 `backend/app/datasources/route_planner.py` | 从 SourceRegistry + CapabilityRegistry 生成 route plan                      |
| DB schema                                         | 可新增 `source_route_log` 或复用 `job_event_log.payload_json`，设计时需明确 |
| tests                                             | 新增 `tests/test_source_route_planner.py`                                   |

### 落地验收

```bash
python -m pytest tests/test_source_route_planner.py tests/test_source_registry.py tests/test_sync_orchestrator.py -q
```

### 优先级

P1。应与 DS-SVC-001 同批完成。

---

## DS-QMT-001：新增可选 qmt_xqshare 源，但默认禁用

### 来源与依据

- 调研报告 REF-DATA-004。
- EasyXT 跨平台 xqshare 思路有价值。
- 当前 D-11 已明确 QMT 第一版默认禁用，不能自动连接本机或远程终端。

### 当前最新进度判断

当前 `source_registry.yaml` 有 `qmt_xtdata` 默认禁用、Yahoo 默认禁用，但没有 `qmt_xqshare` 可选远程源。

### 需要调整的设计文档

| 文件                                               | 调整方式 | 内容                                                       |
| -------------------------------------------------- | -------- | ---------------------------------------------------------- |
| `docs/modules/qmt_xtdata_adapter.md`               | 修改     | 增加 qmt_xqshare 作为可选远程 QMT 源，默认禁用             |
| `docs/modules/data_sources.md`                     | 修改     | 数据源清单加入 qmt_xqshare，但强调 disabled by default     |
| `docs/ops/config_secret_policy.md`                 | 修改     | 增加 XQSHARE_REMOTE_HOST/PORT 配置与安全说明               |
| `docs/architecture/06_deployment_and_local_ops.md` | 修改     | 增加 Windows 原生 QMT 与 macOS/Linux remote xqshare 的边界 |

### 需要新增的设计 / 契约文档

| 新文件                                        | 目的                                          |
| --------------------------------------------- | --------------------------------------------- |
| `specs/contracts/platform_source_matrix.yaml` | 平台 × source × domain × default_enabled 矩阵 |
| `docs/ops/qmt_xqshare_setup.md`               | 用户授权与配置说明                            |

### 需要修改的执行计划

| 文件                                                    | 修改内容                                    |
| ------------------------------------------------------- | ------------------------------------------- |
| `016E_define_platform_source_matrix_and_qmt_xqshare.md` | 新增可选源设计任务                          |
| `013_implement_core_adapter_skeletons.md`               | 后续新增 qmt_xqshare skeleton 任务引用      |
| `032_implement_resource_limit_tests.md`                 | 增加远程源不可自动探测、缺 env 不可调度测试 |
| `033_implement_security_and_boundary_tests.md`          | 增加远程授权与禁止自动联网探测测试          |

### 当前实现未来需要改变的点

| 模块                                             | 未来改动                                                     |
| ------------------------------------------------ | ------------------------------------------------------------ |
| `specs/datasource_registry/source_registry.yaml` | 新增 disabled `qmt_xqshare` source                           |
| `backend/app/datasources/adapters/`              | 后续新增 `qmt_xqshare.py` skeleton，默认不连接               |
| tests                                            | `test_qmtXqshare_disabledByDefault_returnsDisabledSource` 等 |

### 落地验收

```bash
python -m pytest tests/test_platform_source_matrix.py tests/test_source_registry.py tests/test_adapter_skeletons.py -q
```

### 优先级

P2。不阻塞 Round3 建模，但应在真实 QMT 场景扩展前完成。

---

## OPS-CLI-001：新增数据同步速查表与增量命令矩阵

### 来源与依据

- 调研报告 REF-DATA-005。
- EasyXT 的数据下载速查表适合真实用户/运维。
- 当前项目文档偏 implementation task，不够 operator-oriented。

### 当前最新进度判断

当前已有：

- `scripts/init_db.py`
- `scripts/sync_registry.py`
- `scripts/production_equivalent_smoke.py`
- `docs/ops/verification_commands.md`

缺少：

- 一页式 data sync quick reference
- 面向用户的 domain-level sync 命令矩阵
- 每个命令的 dry-run / ResourceGuard / idempotency 说明

### 需要调整的设计文档

| 文件                                     | 调整方式 | 内容                                    |
| ---------------------------------------- | -------- | --------------------------------------- |
| `docs/ops/verification_commands.md`      | 修改     | 增加 data sync quick commands 链接      |
| `docs/modules/data_sync_orchestrator.md` | 修改     | 增加 CLI / dry-run / route preview 约束 |
| `README.md`                              | 修改     | 增加 “数据同步速查”入口                 |

### 需要新增的设计 / 契约文档

| 新文件                                   | 目的                                                |
| ---------------------------------------- | --------------------------------------------------- |
| `docs/ops/data_sync_quick_reference.md`  | 运维/用户一页式命令说明                             |
| `docs/ops/data_sync_command_matrix.md`   | domain × command × safe/unsafe × ResourceGuard 矩阵 |
| `specs/contracts/data_cli_contract.yaml` | CLI 输出 envelope 与错误码                          |

### 需要修改的执行计划

| 文件                                                        | 修改内容                    |
| ----------------------------------------------------------- | --------------------------- |
| `016D_define_data_sync_quick_reference_and_error_guides.md` | 新增 docs/ops 任务          |
| `031_implement_integration_smoke_tests.md`                  | 增加 CLI dry-run smoke      |
| `034_implement_docs_consistency_check.md`                   | 检查 README / docs ops 链接 |

### 当前实现未来需要改变的点

| 模块       | 未来改动                                                                 |
| ---------- | ------------------------------------------------------------------------ |
| `scripts/` | 可新增统一 CLI wrapper，例如 `scripts/qmd_data.py`；当前阶段只设计不实现 |
| tests      | `tests/test_data_cli_contract.py`                                        |

### 落地验收

```bash
python -m pytest tests/test_data_cli_contract.py tests/test_documentation_index.py -q
python scripts/check_doc_links.py
```

### 优先级

P1。建议 Round2.6 完成文档与契约，代码 CLI 可稍后。

---

## ARCH-BND-001：新增模块边界矩阵与 import contract

### 来源与依据

- 调研报告 REF-ARCH-001。
- EasyXT 的低耦合模块边界值得借鉴。
- 当前项目已有目录与 ADR，但缺少机器化 import boundary。

### 当前最新进度判断

当前 `docs/architecture/05_module_map.md` 只列模块地图，没有 “may_import / must_not_import” 规则。`tests/test_sync_pipeline_contract.py` 已开始约束 pipeline seam，但不是全局模块边界。

### 需要调整的设计文档

| 文件                                 | 调整方式 | 内容                                       |
| ------------------------------------ | -------- | ------------------------------------------ |
| `docs/architecture/05_module_map.md` | 修改     | 增加 ModuleBoundaryMatrix 入口             |
| `docs/modules/agent_module.md`       | 修改     | 明确 Agent 不得 import writer / adapter    |
| `docs/modules/fastapi_backend.md`    | 修改     | API 层不得直接 import vendor adapters      |
| `docs/modules/data_sources.md`       | 修改     | datasources 不得 import API/Agent/Frontend |

### 需要新增的设计 / 契约文档

| 新文件                                          | 目的                   |
| ----------------------------------------------- | ---------------------- |
| `docs/architecture/module_boundary_matrix.md`   | 人类可读模块边界       |
| `specs/contracts/module_boundary_contract.yaml` | 机器可校验 import 规则 |
| `scripts/check_module_boundaries.py`            | 后续实现边界检查脚本   |

### 需要修改的执行计划

| 文件                                           | 修改内容                          |
| ---------------------------------------------- | --------------------------------- |
| `016C_define_module_boundary_contract.md`      | 新增边界契约设计任务              |
| `033_implement_security_and_boundary_tests.md` | 增加 import boundary 检查         |
| `034_implement_docs_consistency_check.md`      | docs 索引必须包含 boundary matrix |

### 当前实现未来需要改变的点

| 模块        | 未来改动                                  |
| ----------- | ----------------------------------------- |
| tests       | 新增 `tests/test_module_boundaries.py`    |
| scripts     | 新增 `scripts/check_module_boundaries.py` |
| import 结构 | 若发现违规 import，按最小重构修复         |

### 落地验收

```bash
python scripts/check_module_boundaries.py
python -m pytest tests/test_module_boundaries.py -q
```

### 优先级

P1。建议 Round3 前完成，以避免 Layer1-5 实现时交叉依赖失控。

---

## DOC-USER-001：新增用户路径式文档入口

### 来源与依据

- 调研报告 REF-DOC-001。
- EasyXT / ptqmt-site 更强调用户路径入口。
- 当前文档更适合 AI coding agent 与工程执行，不适合首次使用者。

### 当前最新进度判断

当前已有 `README.md`、`docs/INDEX.md`、implementation tasks，但缺少：

- `START_HERE`
- operator guide
- developer guide
- researcher guide

### 需要调整的设计文档

| 文件                                                  | 调整方式 | 内容                                                |
| ----------------------------------------------------- | -------- | --------------------------------------------------- |
| `README.md`                                           | 修改     | 增加按角色阅读入口                                  |
| `docs/INDEX.md`                                       | 修改     | 增加 START_HERE / OPERATOR / DEVELOPER / RESEARCHER |
| `docs/architecture/07_project_directory_structure.md` | 修改     | 说明 docs 分层：用户文档 vs 执行任务文档            |

### 需要新增的设计 / 契约文档

| 新文件                     | 目的                           |
| -------------------------- | ------------------------------ |
| `docs/START_HERE.md`       | 第一次使用入口                 |
| `docs/OPERATOR_GUIDE.md`   | 本地运维、数据健康、错误处理   |
| `docs/DEVELOPER_GUIDE.md`  | 开发、测试、Round 任务执行     |
| `docs/RESEARCHER_GUIDE.md` | Layer3/回测/研究数据使用者入口 |

### 需要修改的执行计划

| 文件                                      | 修改内容                    |
| ----------------------------------------- | --------------------------- |
| `004_create_documentation_index.md`       | 补充角色入口文档要求        |
| `034_implement_docs_consistency_check.md` | docs index 必须覆盖角色入口 |
| `035_implement_final_package_cleanup.md`  | 最终包必须保留这些入口      |

### 当前实现未来需要改变的点

无代码改动。纯文档。

### 落地验收

```bash
python scripts/check_doc_links.py
python -m pytest tests/test_documentation_index.py -q
```

### 优先级

P1。应在 Round3 大量建模文档继续扩张前完成。

---

## OPS-ERR-001：新增 Troubleshooting / Error Code Guide / Incident Playbook

### 来源与依据

- 调研报告 REF-DOC-003、REF-OPS-001。
- 当前项目已有许多“正常失败”状态：`DISABLED_SOURCE`、`RESOURCE_GUARD_PAUSED`、`NOT_PUBLISHED_YET`、`SCHEMA_DRIFT` 等。
- 如果没有运维文档，用户会把正常保护误判为系统故障。

### 当前最新进度判断

当前有 `docs/ops/*`，但没有集中式错误码排障索引。

### 需要调整的设计文档

| 文件                                     | 调整方式 | 内容                                          |
| ---------------------------------------- | -------- | --------------------------------------------- |
| `docs/ops/verification_commands.md`      | 修改     | 加入错误码排障入口                            |
| `docs/modules/data_sources.md`           | 修改     | 将 source/fetch 错误码链接到 ERROR_CODE_GUIDE |
| `docs/modules/data_sync_orchestrator.md` | 修改     | job status 与 incident playbook 关联          |
| `docs/modules/ops_and_performance.md`    | 修改     | ResourceGuard / performance incident 关联     |

### 需要新增的设计 / 契约文档

| 新文件                          | 目的                    |
| ------------------------------- | ----------------------- |
| `docs/ops/TROUBLESHOOTING.md`   | 通用排障入口            |
| `docs/ops/ERROR_CODE_GUIDE.md`  | 错误码 → 原因/重试/修复 |
| `docs/ops/incident_playbook.md` | 场景化运维手册          |

### 需要修改的执行计划

| 文件                                                        | 修改内容                            |
| ----------------------------------------------------------- | ----------------------------------- |
| `016D_define_data_sync_quick_reference_and_error_guides.md` | 新增运维文档任务                    |
| `028_implement_reports_and_notifications.md`                | 报告/通知要链接错误码说明           |
| `034_implement_docs_consistency_check.md`                   | 检查每个 error code 都有文档 anchor |

### 当前实现未来需要改变的点

| 模块            | 未来改动                                 |
| --------------- | ---------------------------------------- |
| error constants | 后续可集中定义 error code registry       |
| API/CLI output  | 输出 error_doc_anchor 或 error_code_link |

### 落地验收

```bash
python scripts/check_doc_links.py
python -m pytest tests/test_documentation_index.py -q
```

### 优先级

P1。

---

## PRIV-001：新增 Local-only Privacy / User Input Data Flow Contract

### 来源与依据

- 调研报告 REF-DOC-002。
- ptqmt-site 的“浏览器本地处理，不上传服务器”表达值得借鉴。
- 当前项目 D-12 已规定 Agent 只读固定来源与用户手动导入文本，禁止自由联网搜索。

### 当前最新进度判断

当前已有：

- `docs/ops/privacy_retention_policy.md`
- `docs/ops/agent_security_policy.md`
- `docs/ops/frontend_security_policy.md`

但缺少面向前端导入和 Agent 手动文本输入的数据流 contract。

### 需要调整的设计文档

| 文件                                   | 调整方式 | 内容                                                    |
| -------------------------------------- | -------- | ------------------------------------------------------- |
| `docs/ops/privacy_retention_policy.md` | 修改     | 增加 local-only user import 数据流                      |
| `docs/ops/agent_security_policy.md`    | 修改     | Agent 手动文本输入默认不成为事实源，除非保存为 evidence |
| `docs/modules/frontend_dashboard.md`   | 修改     | 前端导入组件必须显示 Local-only / retention disclosure  |
| `docs/modules/agent_module.md`         | 修改     | Agent input provenance 与 evidence 保存边界             |

### 需要新增的设计 / 契约文档

| 新文件                                             | 目的                                                         |
| -------------------------------------------------- | ------------------------------------------------------------ |
| `docs/ops/privacy_data_flow.md`                    | 用户输入、Agent 输入、report/evidence 的数据流说明           |
| `specs/contracts/user_input_privacy_contract.yaml` | 机器契约：local_only、save_as_evidence、redaction、retention |

### 需要修改的执行计划

| 文件                                         | 修改内容                                                       |
| -------------------------------------------- | -------------------------------------------------------------- |
| `025_implement_agent_tool_layer.md`          | Agent tool 输入必须带 provenance/privacy flag                  |
| `026_implement_frontend_shell.md`            | shell 可预留 LocalOnlyBadge/Disclosure，但 UI 布局仍需用户确认 |
| `027_implement_frontend_layer_pages.md`      | 数据导入或展示必须按 privacy contract                          |
| `030_implement_no_action_semantics_guard.md` | 用户导入策略/文本不得绕过 no-action guard                      |

### 当前实现未来需要改变的点

| 模块     | 未来改动                                           |
| -------- | -------------------------------------------------- |
| frontend | 后续新增 `LocalOnlyBadge` / `UserImportDisclosure` |
| backend  | Agent input schema 增加 provenance/privacy fields  |
| tests    | 新增 `tests/test_privacy_contract.py`              |

### 落地验收

```bash
python -m pytest tests/test_privacy_contract.py tests/test_api_security_contract.py -q
cd frontend && npm run typecheck && npm test
```

### 优先级

P1。Round4 前端/Agent 前必须完成。

---

## BT-LIFE-001：细化 BacktestReviewEngine 生命周期契约

### 来源与依据

- 调研报告 REF-BT-001。
- JQ2PTrade MiniPTrade 的生命周期可借鉴，但不能借鉴交易下单语义。
- 当前 `docs/modules/backtest_and_review.md` 已有表结构和运行链路，但还不够像可实现 lifecycle。

### 当前最新进度判断

当前 backtest 主要处于设计阶段。`specs/contracts/backtest_contract.yaml` 与 schema 表存在，但没有实现引擎。

### 需要调整的设计文档

| 文件                                  | 调整方式 | 内容                                                                                                                  |
| ------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------- |
| `docs/modules/backtest_and_review.md` | 修改     | 增加 `BacktestReviewEngine` lifecycle：load scenario → freeze data → build event set → compute windows → write report |
| `docs/modules/agent_module.md`        | 修改     | Agent 只能解释 backtest，不得改写结果或生成交易建议                                                                   |
| `docs/modules/write_manager.md`       | 修改     | 回测 run/metric/report 写入是否必须经 WriteManager 的边界                                                             |

### 需要新增的设计 / 契约文档

| 新文件                                          | 目的               |
| ----------------------------------------------- | ------------------ |
| `specs/contracts/backtest_metric_contract.yaml` | 固定 metric schema |
| `docs/modules/backtest_review_lifecycle.md`     | 更细的生命周期设计 |

### 需要修改的执行计划

| 文件                                           | 修改内容                                      |
| ---------------------------------------------- | --------------------------------------------- |
| `029_implement_backtest_and_review.md`         | 从“实现回测与复盘”改为按 lifecycle 分阶段实现 |
| `031_implement_integration_smoke_tests.md`     | 增加 backtest lifecycle smoke                 |
| `033_implement_security_and_boundary_tests.md` | Agent 不得把回测输出转成交易建议              |

### 当前实现未来需要改变的点

| 模块                                           | 未来改动                                  |
| ---------------------------------------------- | ----------------------------------------- |
| 新模块 `backend/app/review/backtest_engine.py` | 后续新增                                  |
| 新模块 `backend/app/review/review_context.py`  | 后续新增                                  |
| 新模块 `backend/app/review/report_builder.py`  | 后续新增                                  |
| tests                                          | `tests/test_backtest_review_lifecycle.py` |

### 落地验收

```bash
python -m pytest tests/test_backtest_review_lifecycle.py tests/test_backtest_metric_contract.py -q
```

### 优先级

P1。Round4 `029` 前必须完成设计调整。

---

## BT-METRIC-001：新增回测指标契约，避免报告字段漂移

### 来源与依据

- 调研报告 REF-BT-003。
- JQ2PTrade 的报告指标字段简单明确，可借鉴“固定报告 schema”思想。
- 本项目不能默认引入交易次数、佣金、下单收益等交易语义。

### 当前最新进度判断

`docs/modules/backtest_and_review.md` 已列出可选指标，但没有独立 machine contract。

### 需要调整的设计文档

| 文件                                     | 调整方式 | 内容                             |
| ---------------------------------------- | -------- | -------------------------------- |
| `docs/modules/backtest_and_review.md`    | 修改     | 将默认指标与可选策略沙箱指标分离 |
| `specs/contracts/backtest_contract.yaml` | 修改     | 引用新 metric contract           |

### 需要新增的设计 / 契约文档

| 新文件                                          | 目的                                           |
| ----------------------------------------------- | ---------------------------------------------- |
| `specs/contracts/backtest_metric_contract.yaml` | 固定 metric name、unit、horizon、quality flags |

### 需要修改的执行计划

| 文件                                         | 修改内容                        |
| -------------------------------------------- | ------------------------------- |
| `029_implement_backtest_and_review.md`       | 增加 metric contract validation |
| `028_implement_reports_and_notifications.md` | 报告消费固定 metric schema      |

### 当前实现未来需要改变的点

| 模块                            | 未来改动                                 |
| ------------------------------- | ---------------------------------------- |
| `backend/app/review/metrics.py` | 后续新增                                 |
| tests                           | `tests/test_backtest_metric_contract.py` |

### 落地验收

```bash
python -m pytest tests/test_backtest_metric_contract.py -q
```

### 优先级

P1。

---

## REVIEW-SBX-001：新增只读策略证据沙箱设计，禁止直接执行用户策略代码

### 来源与依据

- 调研报告 REF-BT-002、NO-004。
- JQ2PTrade API shim 有兼容层价值，但其策略 `compile/exec` 与交易 API 不适合本项目默认边界。

### 当前最新进度判断

当前没有策略导入 / 策略沙箱实现。Round4 backtest/Agent 前需要先定边界。

### 需要调整的设计文档

| 文件                                   | 调整方式 | 内容                                            |
| -------------------------------------- | -------- | ----------------------------------------------- |
| `docs/modules/backtest_and_review.md`  | 修改     | 增加只读策略证据沙箱，不执行真实 order API      |
| `docs/modules/agent_module.md`         | 修改     | Agent 不得执行用户策略代码                      |
| `docs/ops/agent_security_policy.md`    | 修改     | AST 扫描、禁止 os/sys/subprocess/network/import |
| `docs/modules/fastapi_and_frontend.md` | 修改     | 用户导入策略需显示安全边界                      |

### 需要新增的设计 / 契约文档

| 新文件                                         | 目的               |
| ---------------------------------------------- | ------------------ |
| `specs/contracts/review_sandbox_contract.yaml` | 允许/禁止 API 列表 |
| `docs/modules/review_sandbox_api.md`           | 只读沙箱设计       |

### 需要修改的执行计划

| 文件                                           | 修改内容                                            |
| ---------------------------------------------- | --------------------------------------------------- |
| `029_implement_backtest_and_review.md`         | 若支持策略导入，必须先实现 sandbox guard            |
| `030_implement_no_action_semantics_guard.md`   | order/order_target/order_value 等函数必须命中 guard |
| `033_implement_security_and_boundary_tests.md` | 增加用户策略代码执行禁止测试                        |

### 当前实现未来需要改变的点

| 模块                                                 | 未来改动                           |
| ---------------------------------------------------- | ---------------------------------- |
| 新模块 `backend/app/review/sandbox_api.py`           | 后续新增，只读 API                 |
| 新模块 `backend/app/review/strategy_import_guard.py` | 后续新增 AST 静态扫描              |
| tests                                                | `tests/test_review_sandbox_api.py` |

### 落地验收

```bash
python -m pytest tests/test_review_sandbox_api.py tests/test_api_security_contract.py -q
```

### 优先级

P2。只有启用策略导入/复盘时才实现，但设计边界应 Round4 前确认。

---

## DOCSITE-001：新增轻量 docs index / docs_site 方案，但不立即引入重型文档框架

### 来源与依据

- 调研报告 REF-DOC-004。
- ptqmt-site 的文档站结构有借鉴价值。
- 当前项目 docs 已经膨胀，纯文件树导航压力增大。

### 当前最新进度判断

当前有 `docs/INDEX.md`、`MANIFEST.json`、`MIGRATION_MAP.md`，但没有可检索 docs_site。

### 需要调整的设计文档

| 文件                                  | 调整方式 | 内容                                   |
| ------------------------------------- | -------- | -------------------------------------- |
| `docs/INDEX.md`                       | 修改     | 增加 docs_site 生成说明                |
| `docs/quality/final_package_rules.md` | 修改     | docs_site 生成物是否进入最终包需要明确 |

### 需要新增的设计 / 契约文档

| 新文件                        | 目的                       |
| ----------------------------- | -------------------------- |
| `docs_site/index.html`        | 轻量本地文档入口，后续生成 |
| `docs_site/sidebar.json`      | 生成导航                   |
| `docs_site/search_index.json` | 本地搜索索引               |
| `scripts/build_docs_index.py` | 后续实现脚本               |

### 需要修改的执行计划

| 文件                                      | 修改内容                         |
| ----------------------------------------- | -------------------------------- |
| `034_implement_docs_consistency_check.md` | 增加 docs_site index build/check |
| `035_implement_final_package_cleanup.md`  | 明确 docs_site 产物保留/清理策略 |

### 当前实现未来需要改变的点

纯文档 / 工具脚本，无业务代码。

### 落地验收

```bash
python scripts/build_docs_index.py
python scripts/check_doc_links.py
```

### 优先级

P2。不阻塞 Round3。

---

## SPEC-MIG-001：新增 spec migrator 设计，用于配置/契约版本迁移

### 来源与依据

- 调研报告 REF-CONV-001。
- JQ2PTrade mapping-first 转换思路可转化为本项目 spec migrator，而不是交易策略转换器。

### 当前最新进度判断

当前已有：

- `MIGRATION_MAP.md`
- schema migrations
- SourceRegistry 对旧字段有部分禁止/兼容逻辑

缺少：

- dry-run spec migrator
- old source_registry → new source_registry 的 migration report

### 需要调整的设计文档

| 文件                                    | 调整方式 | 内容                                                          |
| --------------------------------------- | -------- | ------------------------------------------------------------- |
| `docs/modules/data_sources.md`          | 修改     | 旧字段迁移由 spec migrator 处理，不由 runtime silently accept |
| `docs/ops/migration_recovery_policy.md` | 修改     | 增加 config/spec migration dry-run 策略                       |

### 需要新增的设计 / 契约文档

| 新文件                                                       | 目的                      |
| ------------------------------------------------------------ | ------------------------- |
| `tools/spec_migrator/mappings/source_registry_v1_to_v2.yaml` | 映射规则                  |
| `tools/spec_migrator/README.md`                              | 迁移工具说明              |
| `specs/contracts/spec_migrator_contract.yaml`                | dry-run / report contract |

### 需要修改的执行计划

| 文件                                      | 修改内容                          |
| ----------------------------------------- | --------------------------------- |
| `034_implement_docs_consistency_check.md` | 可加入 spec migrator dry-run 检查 |
| `035_implement_final_package_cleanup.md`  | 确保 migrator 不遗留临时输出      |

### 当前实现未来需要改变的点

| 模块  | 未来改动                               |
| ----- | -------------------------------------- |
| tools | 新增 `tools/spec_migrator/migrator.py` |
| tests | `tests/test_spec_migrator.py`          |

### 落地验收

```bash
python -m pytest tests/test_spec_migrator.py -q
```

### 优先级

P2。

---

## UI-DIAG-001：规划只读 Diagnostics Tools Page

### 来源与依据

- 调研报告 REF-UI-001。
- ptqmt-site 的在线工具入口可借鉴为本项目本地诊断工具页。
- 当前项目要求前端最终 UI 布局必须用户确认，因此这里只规划能力，不固定视觉布局。

### 当前最新进度判断

当前前端 shell 有测试，但仍不是最终 UI。适合提前定义 Diagnostics API/contract，不宜现在写死页面。

### 需要调整的设计文档

| 文件                                 | 调整方式 | 内容                                 |
| ------------------------------------ | -------- | ------------------------------------ |
| `docs/modules/frontend_dashboard.md` | 修改     | 增加 Diagnostics Tools Page 能力占位 |
| `docs/modules/fastapi_backend.md`    | 修改     | 只读 diagnostics endpoints           |
| `docs/api/fastapi_routes.md`         | 修改     | 增加 diagnostics API contract        |

### 需要新增的设计 / 契约文档

| 新文件                                          | 目的                                                                |
| ----------------------------------------------- | ------------------------------------------------------------------- |
| `specs/contracts/diagnostics_api_contract.yaml` | source route preview / registry validation / resource guard preview |

### 需要修改的执行计划

| 文件                                    | 修改内容                                                   |
| --------------------------------------- | ---------------------------------------------------------- |
| `024_implement_fastapi_routes.md`       | 增加只读 diagnostics routes                                |
| `026_implement_frontend_shell.md`       | shell 可增加 diagnostics nav placeholder，但布局需用户确认 |
| `027_implement_frontend_layer_pages.md` | 不得把 diagnostics 写成交易/操作入口                       |

### 当前实现未来需要改变的点

| 模块        | 未来改动                            |
| ----------- | ----------------------------------- |
| backend api | 新增只读 diagnostics endpoints      |
| frontend    | 后续新增 diagnostics UI placeholder |
| tests       | frontend + API contract tests       |

### 落地验收

```bash
python -m pytest tests/test_api_security_contract.py -q
cd frontend && npm run typecheck && npm test
```

### 优先级

P2。Round4 前细化。

---

## TEST-PLATFORM-001：新增平台 × 数据源支持矩阵

### 来源与依据

- 调研报告 REF-TEST-001。
- EasyXT 明确 Windows/macOS/Linux 与 QMT/xqshare 支持边界。
- 当前项目 D-11 有 QMT 默认禁用，但缺少平台矩阵化 contract。

### 当前最新进度判断

当前没有 `platform_source_matrix.yaml`。

### 需要调整的设计文档

| 文件                                               | 调整方式 | 内容                                |
| -------------------------------------------------- | -------- | ----------------------------------- |
| `docs/modules/data_sources.md`                     | 修改     | 平台支持与默认禁用说明              |
| `docs/modules/qmt_xtdata_adapter.md`               | 修改     | Windows local QMT vs remote xqshare |
| `docs/architecture/06_deployment_and_local_ops.md` | 修改     | 平台矩阵                            |

### 需要新增的设计 / 契约文档

| 新文件                                        | 目的             |
| --------------------------------------------- | ---------------- |
| `specs/contracts/platform_source_matrix.yaml` | 平台支持机器契约 |
| `tests/test_platform_source_matrix.py`        | 后续测试         |

### 需要修改的执行计划

| 文件                                                    | 修改内容              |
| ------------------------------------------------------- | --------------------- |
| `016E_define_platform_source_matrix_and_qmt_xqshare.md` | 新增平台矩阵任务      |
| `033_implement_security_and_boundary_tests.md`          | 增加平台禁用/授权测试 |

### 当前实现未来需要改变的点

| 模块               | 未来改动                         |
| ------------------ | -------------------------------- |
| SourceRoutePlanner | 后续使用平台矩阵判定 schedulable |
| tests              | 新增平台矩阵 tests               |

### 落地验收

```bash
python -m pytest tests/test_platform_source_matrix.py -q
```

### 优先级

P2。

---

## ARCH-EXTRAS-001：规划 optional extras，避免依赖膨胀

### 来源与依据

- 调研报告 REF-ARCH-002。
- 项目目标强调 local-first、低资源占用、默认 eco。

### 当前最新进度判断

当前 `pyproject.toml` 依赖相对轻，但真实 adapter、backtest、agent、docs 未来会增加依赖。应先设计 optional extras 策略，避免未来无边界膨胀。

### 需要调整的设计文档

| 文件                                                  | 调整方式 | 内容                                             |
| ----------------------------------------------------- | -------- | ------------------------------------------------ |
| `docs/architecture/06_deployment_and_local_ops.md`    | 修改     | 默认安装与 optional extras 策略                  |
| `docs/ops/performance_limits.md`                      | 修改     | 依赖体积与运行模式边界                           |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md` | 修改     | 新增大型依赖必须进入 optional extra 且需用户确认 |

### 需要新增的设计 / 契约文档

| 新文件                                            | 目的                                                    |
| ------------------------------------------------- | ------------------------------------------------------- |
| `specs/contracts/dependency_extras_contract.yaml` | default/dev/datasources/backtest/agent/docs extras 边界 |

### 需要修改的执行计划

| 文件                                           | 修改内容                                  |
| ---------------------------------------------- | ----------------------------------------- |
| `033_implement_security_and_boundary_tests.md` | 增加依赖边界检查                          |
| `035_implement_final_package_cleanup.md`       | 检查默认依赖不包含 QMT/xqshare/重型可选包 |

### 当前实现未来需要改变的点

| 模块             | 未来改动                                   |
| ---------------- | ------------------------------------------ |
| `pyproject.toml` | 后续增加 optional dependencies；本阶段不改 |
| tests            | 依赖 contract test                         |

### 落地验收

```bash
python -m pytest tests/test_dependency_extras_contract.py -q
```

### 优先级

P2。

---

## NEG-001：把“不借鉴项”固化为负面约束

### 来源与依据

- 调研报告 NO-001 至 NO-004。
- 参考项目包含真实交易、自动登录、silent fallback、策略 exec，这些都不应进入本项目默认边界。

### 当前最新进度判断

当前项目已有 no-action 与 QMT 默认禁用原则，但调研报告中的“不借鉴项”应被固化为更明确的执行检查，避免后续 Agent 误搬参考项目能力。

### 需要调整的设计文档

| 文件                                                  | 调整方式 | 内容                                |
| ----------------------------------------------------- | -------- | ----------------------------------- |
| `docs/modules/backtest_and_review.md`                 | 修改     | 不借鉴真实交易 / 自动下单           |
| `docs/modules/qmt_xtdata_adapter.md`                  | 修改     | 不借鉴自动登录/验证码识别           |
| `docs/modules/data_sources.md`                        | 修改     | 不借鉴 silent fallback              |
| `docs/ops/agent_security_policy.md`                   | 修改     | 不直接执行用户策略代码              |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md` | 修改     | 把 NO-001~NO-004 加入全局 red flags |

### 需要新增的设计 / 契约文档

| 新文件                                               | 目的                      |
| ---------------------------------------------------- | ------------------------- |
| `specs/contracts/reference_adoption_guardrails.yaml` | 参考项目功能采纳/禁止清单 |

### 需要修改的执行计划

| 文件                                           | 修改内容                                                           |
| ---------------------------------------------- | ------------------------------------------------------------------ |
| `030_implement_no_action_semantics_guard.md`   | 增加 order/auto-login/silent fallback/exec strategy 的 guard tests |
| `033_implement_security_and_boundary_tests.md` | 增加参考项目误搬迁防护测试                                         |

### 当前实现未来需要改变的点

| 模块  | 未来改动                                           |
| ----- | -------------------------------------------------- |
| tests | 新增 `tests/test_reference_adoption_guardrails.py` |
| code  | 若未来出现真实交易/自动登录/exec，需要直接 fail    |

### 落地验收

```bash
python -m pytest tests/test_reference_adoption_guardrails.py tests/test_api_security_contract.py -q
```

### 优先级

P0/P1。文档与测试应在 Round4 前完成；如发现代码中已有违反项，必须立即修。

---

## 3. 哪些模块设计文档需要调整

### 3.1 必须调整的现有设计文档

| 文件                                                             | 必要性 | 涉及 ID                                                                      |
| ---------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------- |
| `docs/modules/data_sources.md`                                   | 必改   | DS-CAP-001、DS-SVC-001、DS-ROUTE-001、DS-QMT-001、TEST-PLATFORM-001、NEG-001 |
| `docs/modules/data_sync_orchestrator.md`                         | 必改   | DS-CAP-001、DS-SVC-001、DS-ROUTE-001、OPS-CLI-001                            |
| `docs/modules/backtest_and_review.md`                            | 必改   | BT-LIFE-001、BT-METRIC-001、REVIEW-SBX-001、NEG-001                          |
| `docs/modules/agent_module.md`                                   | 必改   | DS-SVC-001、PRIV-001、BT-LIFE-001、REVIEW-SBX-001、NEG-001                   |
| `docs/modules/frontend_dashboard.md`                             | 必改   | DS-ROUTE-001、PRIV-001、UI-DIAG-001                                          |
| `docs/modules/fastapi_backend.md` / `docs/api/fastapi_routes.md` | 必改   | DS-SVC-001、UI-DIAG-001                                                      |
| `docs/modules/qmt_xtdata_adapter.md`                             | 必改   | DS-QMT-001、TEST-PLATFORM-001、NEG-001                                       |
| `docs/architecture/05_module_map.md`                             | 必改   | DS-CAP-001、ARCH-BND-001                                                     |
| `docs/architecture/06_deployment_and_local_ops.md`               | 必改   | DS-QMT-001、TEST-PLATFORM-001、ARCH-EXTRAS-001                               |
| `docs/architecture/10_external_references.md`                    | 建议改 | DS-CAP-001、DOCSITE-001、NEG-001                                             |
| `docs/ops/privacy_retention_policy.md`                           | 必改   | PRIV-001                                                                     |
| `docs/ops/agent_security_policy.md`                              | 必改   | PRIV-001、REVIEW-SBX-001、NEG-001                                            |
| `docs/ops/verification_commands.md`                              | 必改   | OPS-CLI-001、OPS-ERR-001                                                     |
| `docs/quality/final_package_rules.md`                            | 建议改 | DOCSITE-001                                                                  |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`            | 必改   | ARCH-EXTRAS-001、NEG-001                                                     |

### 3.2 不建议直接修改的文档

| 文件                                               | 原因                                                         |
| -------------------------------------------------- | ------------------------------------------------------------ |
| `docs/decisions/ADR-001/002/003`                   | 已经 closeout，不应重写历史 ADR；如有新决策，应新增 ADR-004+ |
| `ROUND2_REAUDIT_CLOSEOUT.md`                       | 它是历史收口记录，不应改写                                   |
| `ROUND2_ABCD_9_AGENT_ADVERSARIAL_AUDIT_SUMMARY.md` | 它是历史审计输出，不应改写                                   |
| 已归档 `.trellis/tasks/archive/*`                  | 不应修改归档任务                                             |

---

## 4. 哪些设计 / 契约文档需要新增

| 新文件                                               | 优先级 | 对应 ID                        |
| ---------------------------------------------------- | -----: | ------------------------------ |
| `specs/datasource_registry/source_capabilities.yaml` |     P1 | DS-CAP-001                     |
| `specs/contracts/source_capability_contract.yaml`    |     P1 | DS-CAP-001                     |
| `docs/modules/source_capability_registry.md`         |     P1 | DS-CAP-001                     |
| `specs/contracts/datasource_service_contract.yaml`   |     P1 | DS-SVC-001                     |
| `docs/modules/datasource_service.md`                 |     P1 | DS-SVC-001                     |
| `specs/contracts/source_route_contract.yaml`         |     P1 | DS-ROUTE-001                   |
| `docs/modules/source_route_plan.md`                  |     P1 | DS-ROUTE-001                   |
| `docs/architecture/module_boundary_matrix.md`        |     P1 | ARCH-BND-001                   |
| `specs/contracts/module_boundary_contract.yaml`      |     P1 | ARCH-BND-001                   |
| `docs/START_HERE.md`                                 |     P1 | DOC-USER-001                   |
| `docs/OPERATOR_GUIDE.md`                             |     P1 | DOC-USER-001                   |
| `docs/DEVELOPER_GUIDE.md`                            |     P1 | DOC-USER-001                   |
| `docs/RESEARCHER_GUIDE.md`                           |     P1 | DOC-USER-001                   |
| `docs/ops/TROUBLESHOOTING.md`                        |     P1 | OPS-ERR-001                    |
| `docs/ops/ERROR_CODE_GUIDE.md`                       |     P1 | OPS-ERR-001                    |
| `docs/ops/incident_playbook.md`                      |     P1 | OPS-ERR-001                    |
| `docs/ops/privacy_data_flow.md`                      |     P1 | PRIV-001                       |
| `specs/contracts/user_input_privacy_contract.yaml`   |     P1 | PRIV-001                       |
| `specs/contracts/backtest_metric_contract.yaml`      |     P1 | BT-METRIC-001                  |
| `docs/modules/backtest_review_lifecycle.md`          |     P1 | BT-LIFE-001                    |
| `specs/contracts/review_sandbox_contract.yaml`       |     P2 | REVIEW-SBX-001                 |
| `docs/modules/review_sandbox_api.md`                 |     P2 | REVIEW-SBX-001                 |
| `specs/contracts/platform_source_matrix.yaml`        |     P2 | DS-QMT-001 / TEST-PLATFORM-001 |
| `docs/ops/qmt_xqshare_setup.md`                      |     P2 | DS-QMT-001                     |
| `specs/contracts/diagnostics_api_contract.yaml`      |     P2 | UI-DIAG-001                    |
| `specs/contracts/dependency_extras_contract.yaml`    |     P2 | ARCH-EXTRAS-001                |
| `specs/contracts/reference_adoption_guardrails.yaml` |     P1 | NEG-001                        |
| `tools/spec_migrator/README.md`                      |     P2 | SPEC-MIG-001                   |
| `specs/contracts/spec_migrator_contract.yaml`        |     P2 | SPEC-MIG-001                   |

---

## 5. 哪些执行计划需要修改 / 新增

### 5.1 新增 Round2.6 执行计划目录

建议新增目录：

```text
 docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/
```

建议新增任务：

| 任务文件                                                    | 目的                               | 对应 ID                       |
| ----------------------------------------------------------- | ---------------------------------- | ----------------------------- |
| `016A_define_source_capability_registry.md`                 | capability matrix 设计与契约       | DS-CAP-001                    |
| `016B_define_source_route_plan_and_datasource_service.md`   | RoutePlan + DataSourceService      | DS-SVC-001、DS-ROUTE-001      |
| `016C_define_module_boundary_contract.md`                   | import boundary                    | ARCH-BND-001                  |
| `016D_define_data_sync_quick_reference_and_error_guides.md` | ops quick reference / error guide  | OPS-CLI-001、OPS-ERR-001      |
| `016E_define_platform_source_matrix_and_qmt_xqshare.md`     | platform matrix / optional xqshare | DS-QMT-001、TEST-PLATFORM-001 |
| `016F_define_prod_equivalent_scale_benchmark.md`            | 生产等价规模与性能验证计划         | DS-ROUTE-001、OPS-CLI-001     |

### 5.2 修改现有 Round2 任务

| 文件                                      | 修改原因                                                      |
| ----------------------------------------- | ------------------------------------------------------------- |
| `011_implement_source_registry.md`        | 增加后续 capability / route plan 对接说明                     |
| `012_implement_data_adapter_contract.md`  | 增加 capability + DataSourceService 输出边界                  |
| `013_implement_core_adapter_skeletons.md` | adapter skeleton 必须声明并通过 capability 校验               |
| `014_implement_data_sync_orchestrator.md` | Orchestrator 后续改为调用 DataSourceService / SourceRoutePlan |

### 5.3 修改 Round3 任务

| 文件                                              | 修改原因                                                                                      |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `017_implement_layer1_axis_loader.md`             | Layer snapshot lineage 消费 validation rule_version；若外部数据 fetch，需经 DataSourceService |
| `018_implement_layer1_interpretation_snapshot.md` | 引用 backtest/review 与 no-action 边界，不得产生交易动作                                      |
| `019_implement_layer2_cross_asset_sensor.md`      | 依赖 source capability 中全球资产数据能力                                                     |
| `020_implement_layer3_industry_chain_loader.md`   | 数据来源需明确 capability / source route / evidence provenance                                |
| `021_implement_layer3_snapshot_builder.md`        | snapshot lineage 需消费 source_route / rule_version / quality_flags                           |
| `023_implement_layer5_evidence_chain.md`          | evidence 需标注 local-only/user-import/source-route provenance                                |

### 5.4 修改 Round4 任务

| 文件                                         | 修改原因                                                      |
| -------------------------------------------- | ------------------------------------------------------------- |
| `024_implement_fastapi_routes.md`            | 增加 diagnostics API 与 DataSourceService 禁止绕过规则        |
| `025_implement_agent_tool_layer.md`          | Agent 禁止 adapter factory、禁止写库、输入 provenance/privacy |
| `026_implement_frontend_shell.md`            | LocalOnlyBadge / Diagnostics placeholder 需用户确认 UI        |
| `027_implement_frontend_layer_pages.md`      | 展示 source route、quality flags、disabled reason             |
| `028_implement_reports_and_notifications.md` | 报告链接 error guide / incident playbook                      |
| `029_implement_backtest_and_review.md`       | 改为 lifecycle + metric contract                              |
| `030_implement_no_action_semantics_guard.md` | 增加参考项目误搬迁防护：order/auto-login/silent fallback/exec |

### 5.5 修改 Round5 任务

| 文件                                           | 修改原因                                               |
| ---------------------------------------------- | ------------------------------------------------------ |
| `031_implement_integration_smoke_tests.md`     | 加入 CLI dry-run / DataSourceService / RoutePlan smoke |
| `032_implement_resource_limit_tests.md`        | 加入生产等价规模 benchmark 与 platform matrix          |
| `033_implement_security_and_boundary_tests.md` | 加入 module boundary、privacy、reference guardrails    |
| `034_implement_docs_consistency_check.md`      | 检查新增 docs/specs/contracts 索引与 anchor            |
| `035_implement_final_package_cleanup.md`       | docs_site / generated index / temp output 清理策略     |
| `036_create_final_release_manifest.md`         | manifest 纳入新增 contract 与 docs                     |

---

## 6. 当前已实现情况中未来需要改变的地方

> 当前阶段不改代码；以下是用户批准后、进入实现阶段才允许执行的代码级变更。

| 模块                                           | 当前状态                                            | 未来改变                                                                        |
| ---------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------- |
| `backend/app/datasources/adapters/__init__.py` | `create_adapter()` 是生产 factory，已经要求显式依赖 | 保留，但标记为 DataSourceService 内部 API；禁止 Orchestrator/API/Agent 直接调用 |
| `backend/app/sync/runners.py`                  | 已拆分 Incremental/Backfill/Reconcile runner        | 后续 runner 不直接拿 adapter，而是通过 DataSourceService 或 fetch callable      |
| `backend/app/datasources/source_registry.py`   | 负责 source/domain/role/disabled 校验               | 不塞入 capability，新增独立 CapabilityRegistry 和 RoutePlanner                  |
| `tests/test_vendor_fetch_e2e.py`               | fixture E2E 已覆盖真实 orchestrator 路径            | 后续扩展为 DataSourceService path E2E + larger fixture-scale benchmark          |
| `frontend/src/*`                               | shell 与基本测试存在                                | 后续只读 diagnostics / LocalOnlyBadge / source route 展示需先用户确认 UI        |
| `scripts/production_equivalent_smoke.py`       | 已存在生产等价 smoke                                | 后续接入 source route、capability、规模数据集、性能输出                         |
| `pyproject.toml`                               | 依赖尚可控                                          | 后续引入真实源/agent/backtest/docs 时使用 optional extras                       |
| schema migrations                              | 008/009/010 已关闭 lineage/check/not-null           | 新增 source_route_log / capability 相关 schema 时必须独立 migration             |

---

## 7. 推荐执行顺序

### Phase A：只改设计文档与执行计划，不改代码

1. 修改 `docs/implementation_tasks/README.md`，新增 Round2.6 包。
2. 新增 Round2.6 任务文件 016A-016F。
3. 修改 `docs/modules/data_sources.md`、`data_sync_orchestrator.md`、`backtest_and_review.md`、`agent_module.md`。
4. 新增 P1 contract 文档：capability、datasource service、source route、module boundary、privacy、backtest metric。
5. 新增 docs/ops 用户与运维文档入口。

### Phase B：只做 contract tests / doc checks

1. `tests/test_source_capabilities.py`
2. `tests/test_source_route_planner.py`
3. `tests/test_datasource_service.py`
4. `tests/test_module_boundaries.py`
5. `tests/test_privacy_contract.py`
6. `tests/test_backtest_metric_contract.py`
7. `scripts/check_doc_links.py`

### Phase C：代码重构实现

1. CapabilityRegistry。
2. SourceRoutePlanner。
3. DataSourceService。
4. Orchestrator runners 改用 service/fetch callable。
5. Diagnostics API。
6. BacktestReviewEngine lifecycle。

### Phase D：生产等价验证

1. fixture-scale 数据集。
2. source route + capability + service 贯穿 smoke。
3. ResourceGuard / performance benchmark。
4. 平台矩阵 / disabled source / qmt_xqshare dry-run。

---

## 8. 通过 / 不通过判定

本方案审核通过后，建议以以下条件作为进入实际修改阶段的 gate：

```text
1. 用户确认是否新增 Round2.6 任务包。
2. 用户确认 qmt_xqshare 是否列入 P2 backlog，而不是当前实现。
3. 用户确认 BacktestReviewEngine 是否只做“复盘评估”，不做策略自动交易。
4. 用户确认 Diagnostics Tools 只做只读工具页，UI 布局另行确认。
5. 用户确认本阶段先改 docs/specs/tasks，代码另行授权后再改。
```

未经用户确认，不得修改：

```text
backend/app/**
frontend/src/**
specs/**
docs/**
docs/implementation_tasks/**
pyproject.toml
```

本文件自身除外，因为它是本次只读审计输出。

---

## 9. 最终建议

当前 Round2 re-audit closeout 已经解决了上一轮关键工程缺口。基于调研报告，下一步不应继续围绕已关闭的 runner/lineage/DB CHECK 反复修补，而应把精力转向“进入真实数据源、真实建模、真实用户使用前必须补齐的边界层”：

```text
SourceCapabilityRegistry
DataSourceService
SourceRoutePlan
ModuleBoundaryMatrix
Ops / Error Guide
Privacy Data Flow
BacktestReviewEngine Lifecycle
Reference Adoption Guardrails
```

这些改动本质上是设计与执行计划的再对齐，而不是立即改业务代码。建议先执行 Phase A，待用户审核设计后，再进入 contract tests 与实现阶段。
