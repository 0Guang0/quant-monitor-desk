## 问题陈述

用户当前面对的问题不是某个单独数据源、某个 CLI 或某个 runner 没跑通，而是 Phase 1 的完成口径不够硬：task01 已经新增了与最终主库 schema/contract 等价、但物理隔离的生产等价验收库（production-equivalent acceptance DB）和 `SourceRouteDbAcceptanceSpine`，可是 `qmd-data data sync/backfill/full-load/scheduler` 这些正式数据同步入口仍主要接在旧 `.audit-sandbox` / sandbox-clean-write / limited production entry 语义上。

这会造成一个严重产品风险：后续 Layer1、62 指标、特征、模板解读继续往上堆时，看起来底层“有隔离库、有 dry-run、有 replay e2e、有部分 clean write”，但这些证据没有统一证明最终业务链路已经完成。尤其是 backfill、full-load、scheduler 等子模块可能只做到试点、dry-run 或少数源可执行，却被误当成设计文档、架构设计、规则定义中的最终成品形态。

用户需要的 Phase 1 不是 R5 运维收尾，也不是 Phase 2 的 62 指标全量建模，而是一个严格 R4 级的数据同步地基：所有正式同步入口统一走 task01 后的生产等价验收语义，并能证明完整链路从 source registry / capabilities 到 clean table 的每一步都真实存在、可审计、失败诚实、不可被 mock/replay/dry-run 冒充。

最终必须解决的问题是：

1. 旧 sandbox / limited production entry 入口不能继续作为 Phase 1 完成依据。
2. `sync`、`backfill`、`full-load`、`scheduler` 必须统一接入生产等价验收库语义。
3. 完整链路必须严格对齐设计文档、架构设计、规则定义中的最终成品形态。
4. 只有达到这个 R4 地基后，Phase 2 的 Layer1 62 指标才有意义。

## 解决方案

Phase 1 要把正式数据同步入口收敛到一个最高验收接缝：`qmd-data` 正式入口委托到 `SourceRouteDbAcceptanceSpine` / 生产等价验收库，统一证明完整数据链路。

目标链路如下：

```text
source_registry / capabilities
  -> SourceRoutePlan
  -> DataSourceService
  -> fetch port / adapter
  -> raw files + fetch_log + staging
  -> DataQualityValidator
  -> SourceConflictValidator
  -> WriteManager
  -> clean table
```

Phase 1 的产品成品定义是：

1. `sync`、`backfill`、`full-load`、`scheduler` 都必须通过同一生产等价验收语义验收。
2. 旧 sandbox / limited production entry 入口可以短期保留为兼容 adapter 或历史工具，但不能作为完成标准。
3. 任何正式验收都必须在 task01 语义下的隔离生产等价验收库中运行，不能污染 canonical main DB。
4. 验收报告必须能说明每条链路的 route、fetch、raw/staging、quality、conflict、write、clean、downstream read 状态。
5. `mock`、`replay`、`dry_run`、`not_implemented` 只能作为分类，不能作为 live 成功。
6. 未授权、缺 key、缺本机终端、缺商业许可、外部网络失败，必须诚实输出 `BLOCKED` / `FAIL_EXTERNAL` / `CONTRACT_VIOLATION`，不能用假数据补绿。
7. backfill 和 full-load 必须从少数试点源扩展为设计要求的最终同步能力；如果某源只能 blocked，也必须由统一验收报告诚实表达。
8. scheduler 必须从 profile dry-run 展开升级为可通过 binding registry 调度正式 job，并能证明 live path 的验收结果。

推荐测试接缝：一个最高层接缝。

```text
qmd-data data <sync|backfill|full-load|scheduler>
  -> SourceRouteDbAcceptanceSpine
  -> production-equivalent acceptance DB
  -> AcceptanceReport
```

低层测试仍可存在，但 Phase 1 关账以这个最高接缝为准。

### 统一验收接口与 R4 可观测证据

`SourceRouteDbAcceptanceSpine` 是深模块：公开接口保持为小接缝，内部隐藏 route resolution、live authorization、isolated DB bootstrap、fetch、raw/staging、validation、conflict、WriteManager clean write、downstream read probe 和失败分类。正式命令不得为 `sync`、`backfill`、`full-load`、`scheduler` 各自发明验收形状。

每个可计入 P1-GATE 的正式命令必须产出或关联同一语义的 `AcceptanceReport`，至少包含：

1. `report_version`、`run_id`、`job_kind`、`trigger`、`data_root`、`generated_at`。
2. `gate_eligible`：只有 task01 production-equivalent acceptance root + official `qmd-data data <job>` 才能为 true。
3. `status`：`PASS`、`FAIL`、`BLOCKED`、`FAIL_EXTERNAL`、`CONTRACT_VIOLATION`，不得把 `dry_run`、`replay`、`mock`、`not_implemented` 写成 PASS。
4. `implementation_mode`、`route_grade`、`write_grade`、`source_used`、`source_role`、`source_switched`。
5. `route_status`、`fetch_status`、`raw_status`、`staging_status`、`validation_status`、`conflict_status`、`write_status`、`clean_status`、`downstream_layer_read_status`。
6. `failure_class`、`errors[]`、`warnings[]`、`blocked_by[]`。
7. `observability_evidence`：`sync_job_id`、`route_plan_id`、`fetch_log_ids`、`raw_file_ids`、`validation_run_ids`、`clean_write_transaction_id`、`job_event_ids`、`resource_guard_decision`、`rows_fetched`、`rows_staged`、`rows_written`、`schema_hash`、`content_hash`、`duration_ms`。

Scheduler 是唯一允许聚合 report 的入口：parent report 记录 profile/trigger/fan-out 状态，child reports 仍逐 job 保留同一 `AcceptanceReport` 语义。parent `PASS` 只表示所有 required child 均 PASS 或 honest skipped；任何 required child 的 `BLOCKED`、`FAIL_EXTERNAL`、`CONTRACT_VIOLATION` 都必须让 parent 非 PASS。

R4 只要求这些证据能从命令输出或落盘报告中查询；不要求 R5 的 dashboard、alert、SLO、pager、runbook 或长期监控。

## 用户故事

1. 作为项目负责人，我想让 Phase 1 完成等同于生产等价验收，所以后续 Layer1 工作不会建立在局部 sandbox 路径上。
2. 作为项目负责人，我想让旧 sandbox 成功不再计入 Phase 1 完成，所以历史演练工具不会定义当前产品就绪度。
3. 作为项目负责人，我想把 limited production entry 视为 legacy compatibility，所以它不能静默替代 task01 acceptance spine。
4. 作为项目负责人，我想让所有正式 sync 命令共享同一验收标准，所以 `sync`、`backfill`、`full-load`、`scheduler` 不会各自发明完成定义。
5. 作为项目负责人，我想在数据链路完成前阻塞 Phase 2，所以 62 个 Layer1 指标不会建立在未完成的 ingestion 层上。
6. 作为项目负责人，我想让 R4 表示代码层面的最终产品形态，所以 runbook 和监控可以留到 R5，而不是掩盖核心行为未完成。
7. 作为数据平台维护者，我想让 `qmd-data data sync` 使用生产等价验收语义，所以 incremental sync 能证明真实产品路径。
8. 作为数据平台维护者，我想让 `qmd-data data backfill` 使用生产等价验收语义，所以历史补数能证明与 incremental sync 相同的链路。
9. 作为数据平台维护者，我想让 `qmd-data data full-load` 使用生产等价验收语义，所以 cold-start loading 不只是 baostock 试点。
10. 作为数据平台维护者，我想让 `qmd-data data scheduler run` 使用生产等价验收语义，所以定时 profile 执行证明的是真实 job，而不是只做 dry-run 展开。
11. 作为数据平台维护者，我想让每个正式 sync 入口默认拒绝 canonical main DB 写入，所以验收永远不会污染当前生产数据根。
12. 作为数据平台维护者，我想让每个正式 sync 入口指向 task01 acceptance data root 形态，所以不同命令产生的隔离 DB 证据可以互相比较。
13. 作为数据平台维护者，我想让每个验收通过的命令产出或关联一个 `AcceptanceReport`，所以证据是结构化的，而不是从控制台输出中推断。
14. 作为数据平台维护者，我想让每次验收运行都持久化 route evidence，所以选源和 fallback 决策可审计。
15. 作为数据平台维护者，我想让 SourceRoutePlan 在 fetch 前执行，所以 adapter 不能绕过 source capability、auth、license 或 ResourceGuard 检查。
16. 作为数据平台维护者，我想让 SourceRoutePlan 包含 route grade，所以 primary、degraded、blocked 路由不会被混淆。
17. 作为数据平台维护者，我想让 DataSourceService 保持产品 fetch 边界，所以正式 sync 路径不会直接调用 vendor adapter。
18. 作为数据平台维护者，我想让 fetch port 写入 raw files 和 fetch logs，所以 validation 和 clean write 之前存在 raw evidence。
19. 作为数据平台维护者，我想让 staging tables 来自真实 fetch 结果，所以 validation 检查的是真实 payload 形态，而不是构造出来的 seed rows。
20. 作为数据平台维护者，我想让 DataQualityValidator 在 clean writes 前执行，所以 schema drift、缺失字段、stale data 和非法值不能静默进入 clean tables。
21. 作为数据平台维护者，我想在 validation sources 存在时运行 SourceConflictValidator，所以严重 source conflicts 会阻塞或进入 reconcile，而不是写入有争议的 clean rows。
22. 作为数据平台维护者，我想只有带审计证据时才允许显式跳过 conflict checks，所以缺少 validation source 的事实是可见的。
23. 作为数据平台维护者，我想让 WriteManager 成为唯一 clean write 边界，所以每个 clean row 都有 validation 和 audit lineage。
24. 作为数据平台维护者，我想让 WriteManager 携带 source role 和 degraded metadata，所以 fallback 和 validation-source data 不会表现成 primary-grade data。
25. 作为数据平台维护者，我想在可用时让 clean table writes 包含 schema hash 和 content hash，所以下游 reads 可以追溯到 raw evidence。
26. 作为数据平台维护者，我想在 clean writes 后运行 downstream read probes，所以 Phase 1 能证明数据可被 Layer modules 消费。
27. 作为数据平台维护者，我想让 `sync` 支持超过单个代表性 tracer 的 live incremental paths，所以不会夸大生产就绪度。
28. 作为数据平台维护者，我想让 `backfill` 对 Tier A canonical domains 执行 live 或诚实 blocked paths，所以历史数据恢复不局限于 dry-run plans。
29. 作为数据平台维护者，我想让 `full-load` 超出 `cn_equity_daily_bar + baostock` 试点，所以 cold-start loading 符合设计中的 sync subsystem。
30. 作为数据平台维护者，我想让 scheduler live runs 要么要求 backfill/full-load 显式窗口，要么提供 profile-defined windows，所以 scheduled jobs 可执行，而不是永久失败。
31. 作为数据平台维护者，我想让 scheduler incremental jobs 通过 indicator bindings 展开，所以 profile execution 不会硬编码 source-specific series lists。
32. 作为数据平台维护者，我想让 BindingSyncExecutor 保持唯一 binding-to-orchestrator 实现，所以 ops、scheduler 和 Layer facade 不会重复 orchestration logic。
33. 作为数据平台维护者，我想让 Layer1 ingestion 调用 sync facade 而不是直接调用 datasources，所以 Layer modules 保持在 data source boundary 之上。
34. 作为数据平台维护者，我想让产品命令不存在 direct adapter path，所以 adapter injection 只保留为 test-only。
35. 作为数据平台维护者，我想让产品命令在某个 source 没有 acceptance handler 时 fail closed，所以 unsupported paths 是可见的。
36. 作为数据平台维护者，我想让产品命令在 env gates 缺失时 fail closed，所以 live fetch 不会被意外触发。
37. 作为数据平台维护者，我想让产品命令在 credentials 缺失时 fail closed，所以 missing auth 不会被误判为产品 bug。
38. 作为数据平台维护者，我想让产品命令诚实报告 external failures，所以上游网络问题不会变成假的 implementation success。
39. 作为审计复核者，我想要一个最高层 acceptance seam，所以我不需要手工对齐 sandbox reports、smoke reports、replay tests 和 production-equivalent reports。
40. 作为审计复核者，我想让 acceptance results 包含 implementation mode，所以 live、mock、replay、dry-run、not-implemented 状态不会混在一起。
41. 作为审计复核者，我想让 acceptance results 包含 write grade，所以 primary-grade clean 和 degraded clean 可以分开复核。
42. 作为审计复核者，我想让 acceptance results 包含 validation status，所以 quality gates 不会被默认假设为通过。
43. 作为审计复核者，我想让 acceptance results 包含 conflict status，所以 source disagreement 是可见的。
44. 作为审计复核者，我想让 acceptance results 包含 downstream layer read status，所以 clean data 被证明可用，而不是仅仅被写入。
45. 作为审计复核者，我想让 acceptance reports 包含 failure class，所以 blocked prerequisites、external failures、contract violations 和 missing implementation 能被区分。
46. 作为审计复核者，我想盘点 legacy sandbox entry usage，所以剩余旧 seams 不能静默声称产品就绪。
47. 作为审计复核者，我想让旧 sandbox/limited production commands 要么委托到 new spine，要么标记为 legacy，所以不会存在互相竞争的 acceptance authority。
48. 作为审计复核者，我想让 tests 通过 CLI/report outputs 验证行为，所以它们不会因为检查 private implementation details 而通过。
49. 作为审计复核者，我想让 replay e2e tests 保留 replay 标签，所以它们能支持开发，但不会证明 live readiness。
50. 作为审计复核者，我想让 dry-run tests 保留 dry-run 标签，所以 plan generation 不会被混同为 fetch/write completion。
51. 作为 Layer1 开发者，我想让数据链路在 Phase 2 前达到 R4，所以 indicator features 基于真实 clean data lineage 计算。
52. 作为 Layer1 开发者，我想让每个 indicator binding 解析到 product sync path，所以 Layer1 不需要 vendor-specific fetch code。
53. 作为 Layer1 开发者，我想让 degraded clean rows 对 Layer reads 可见，所以 Layer1 能在需要时返回 honest NULL 或 degraded state。
54. 作为 Layer1 开发者，我想让 source-switched rows 可区分，所以 model interpretation 不会夸大 data quality。
55. 作为 Layer1 开发者，我想让 missing data 显式化，所以 features 不会静默使用 stale 或 fallback values。
56. 作为 operator，我想让 `qmd-data` commands 显示 acceptance DB 位置，所以我能检查生成的 DuckDB 和 raw evidence。
57. 作为 operator，我想让命令失败包含稳定 error codes 和 docs anchors，所以失败可处理，而不是只能从 stack traces 调试。
58. 作为 operator，我想让 live commands 要求显式 authorization gates，所以不会意外触发网络或付费 API 调用。
59. 作为 operator，我想让 blocked local-terminal 和 licensed sources 保持 blocked，所以 missing commercial prerequisites 不会被隐藏。
60. 作为 operator，我想让 scheduler dry-run 和 live run 语义清晰分开，所以 schedule expansion 不会被误认为 job completion。
61. 作为 operator，我想让 backfill caps 继续强制执行，所以 catch-up jobs 不会意外变成 unbounded scans。
62. 作为 operator，我想让 full-load caps 或 windows 保持显式，所以 cold-start runs 有边界且可审计。
63. 作为 operator，我想让失败 shard job 重跑时能安全 resume，所以 long jobs 可恢复且不会重写 completed shards。
64. 作为 operator，我想让 replay 和 live supported domains 的 clean writes 具备 idempotence，所以重复 acceptance runs 不会产生重复 rows。
65. 作为 operator，我想让 job events 展示 shard start、shard complete、skipped 和 failure states，所以 long-running jobs 可检查。
66. 作为 operator，我想让 acceptance output 包含 ResourceGuard decisions，所以 pause 或 hard-stop 行为可见。
67. 作为后续 agent，我想让 PRD 区分 R4 和 R5，所以我不会在完成核心产品行为前添加 runbooks。
68. 作为后续 agent，我想让 Phase 2 在本 PRD 中明确 out of scope，所以我不会在 Phase 1 关闭前开始 62 indicator implementation。
69. 作为后续 agent，我想让 file-level old paths 不再定义 product completion，所以我会跟随 acceptance seam，而不是复制旧 helpers。
70. 作为后续 agent，我想让删除 old helper 是有意为之，所以 official entry points 委托到 new spine 前不会破坏 compatibility。

## 实现决策

- 将 `SourceRouteDbAcceptanceSpine` 视为 Phase 1 的验收权威（acceptance authority）。公开产品接缝应保持很小：输入 request，输出 acceptance report。
- 将 `qmd-data` 视为 sync 操作的正式用户入口。ops acceptance CLI 可以继续作为低层/admin wrapper 保留，但 Phase 1 产品命令必须收敛到同一验收语义。
- 将旧 sandbox / limited production entry 从完成标准中退役。它们可以临时作为兼容 wrapper、迁移 helper 或历史工具保留，但不能成为 P1-GATE 权威。
- 当正式 sync 入口用于 Phase 1 验收时，必须指向生产等价验收 data root，而不是通用 `.audit-sandbox` root。
- 保留 canonical main DB 拒绝规则。生产等价验收指的是形态等同生产的隔离 DB（production-shaped isolated DB），不是写 canonical data root。
- 扩展或适配 sync 命令返回信封，使 `sync`、`backfill`、`full-load`、`scheduler` 能返回或写入 acceptance report 的标识或路径。
- 保持 `DataSourceService` 作为产品 fetch 边界。直接执行 adapter 只能是 test-only 或内部 legacy compatibility，不能是正式产品路径。
- 保持 `DataSyncOrchestrator` 作为 incremental、backfill、full-load、reconcile、data-quality、revision-audit 行为的 job execution facade。
- 保持 `BindingSyncExecutor` 作为 binding-to-orchestrator 深模块。Ops runners、scheduler 和 Layer sync facade 应调用它，而不是重复 watermark、mapper 或 job-spec logic。
- 保持 `WriteManager` 作为唯一 clean table 写入边界。绕过 WriteManager 的 clean writes 不满足 Phase 1 产品契约。
- Full-load 不能继续停留在单源试点。它的 command 和 orchestrator path 必须通过同一 binding/source route machinery 支持设计中的 domains；前置条件缺失时必须输出 honest blocked states。
- Backfill 不能继续停留在“dry-run 覆盖广、live 覆盖窄”的状态。它的 no-dry-run 产品路径必须对 supported Tier A domains 收敛到同一验收语义。
- Scheduler 不能继续停留在 dry-run profile 展开器。Live scheduler execution 必须为 backfill/full-load 提供显式 window semantics，或以 product-level unsupported state 失败并阻塞 P1-GATE。
- 如果 revision audit 和 data quality jobs 被纳入 Phase 1 最终 job 行为，它们不能继续停留在 state-machine stubs。若保留在 P1-GATE 中，它们需要可观察的 product work，或显式 ADR-level deferral。
- Acceptance report semantics 必须在 job types 之间保持统一：route grade、implementation mode、write grade、source used/role/switched、quality flags、stale/fallback reason、schema hash、content hash、validation status、conflict status、failure class、downstream layer read status 和 errors。
- Acceptance report 是正式命令的测试接口：测试优先断言 report 字段、job events 和证据 ID，不断言 private helper call order。
- Scheduler report 必须是 parent + child reports 聚合，不得把多个 child 的失败压扁成一个模糊 `FAILED_FINAL`。
- R4 可观测性仅要求结构化证据字段和稳定事件 ID；R5 才要求监控、告警、runbook 和 operator 文档。
- Validation-only sources 可以支持 route/fetch/evidence/conflict validation，但除非 domain fallback policy 明确授权 degraded clean semantics，否则不得写 primary-grade clean rows。
- Missing keys、local terminals、licenses 和 external network failures 不是 implementation PASS states。它们必须诚实报告为 blocked 或 external failure。
- 现有 replay/mock tests 对开发速度仍有价值，但它们的结果语言不得暗示 product-live completion。
- Module boundary rules 仍属于 Phase 1：sync facade 存在后，Layer modules 不得直接 import 或 call data source services。
- Phase 1 PRD 有意不要求 R5 runbooks、monitoring、alerting、backup/restore 或 operator documentation。这些是代码达到 R4 product shape 后的后续 operational hardening。

## 测试决策

- 最高行为测试接缝是正式命令到验收的流程：`qmd-data data <job>` 产出或委托到生产等价验收报告。
- 好的 Phase 1 测试验证产品可观察行为：命令返回信封、acceptance report、route evidence、raw/fetch log/staging evidence、validation report、conflict report 或 explicit skip、WriteManager clean write、downstream clean read。
- 好的 Phase 1 测试不应断言 private helper call order，不应把 monkeypatch internals 当作 product success 证据，也不应把 mock calls 计为 live acceptance。
- CLI tests 应验证通用 `.audit-sandbox` acceptance 不再满足 P1-GATE，除非它是 task01 production-equivalent acceptance root shape。
- Migration tests 应列出或失败化剩余 product/runtime consumers 对 old sandbox-clean-write 和 limited-production completion paths 的使用。
- Sync tests 应验证通过 DataSourceService 和 WriteManager 的 incremental live/honest-blocked execution，而不是 direct adapter success。
- Backfill tests 应验证 bounded shard planning、cap enforcement、supported domains 的 no-dry-run execution、resume behavior、clean write、idempotence 和 acceptance report linkage。
- Full-load tests 应验证超出现有 single-source pilot 的 cold-start shard execution、checkpoint resume、clean write 和 acceptance report linkage。
- Scheduler tests 应验证通过 indicator bindings 做 profile expansion、incremental jobs 的 live execution semantics，以及 backfill/full-load windows 的显式处理。
- Orchestrator tests 应通过 job status 和 job events 外部验证 state transitions，而不是 private runner internals。
- SourceRoutePlan tests 应验证 route grade、source selection、fallback/blocking reasons 和 persisted route evidence。
- DataSourceService tests 应验证 product fetch 会 emit route evidence，并尊重 capability、auth/license 和 ResourceGuard gates。
- DataQualityValidator tests 应验证 schema drift、missing required fields、stale values 和 can-write-clean outcomes。
- SourceConflictValidator tests 应验证 severe conflict 会阻塞 clean writes，并且 reconcile/manual review states 可见。
- WriteManager tests 应验证 source role、source switched、quality flags、stale/fallback reason，以及 primary-grade 与 degraded clean semantics。
- Layer read tests 应验证 downstream behavior 面对 primary-grade、degraded、missing 和 blocked clean data 时的表现。
- 当前代码库已有先例：source-route-db acceptance tests、qmd-data CLI tests、bounded backfill tests、full-load runner tests、sync orchestrator tests、SourceRoutePlan/DataSourceService tests、WriteManager tests、module boundary checks 和 indicator binding checks。
- Phase 1 最终验证应包含最高接缝加有针对性的 lower seam tests。Lower seam tests 支持诊断，但不能替代 highest seam。

## 非目标范围

- Phase 2 的 62-indicator sync-to-feature-to-template implementation 不属于本 PRD 范围，应后续追加。
- Layer1 feature engineering、state buckets、interpretation templates、Round4 API、frontend 和 agent-facing reports 不属于本 PRD 范围；唯一例外是 downstream read probes 用来证明 clean data 可消费。
- R5 operational hardening 不属于本 PRD 范围：runbooks、monitoring、alerting、backup/restore、operator documentation、deployment process 和 long-term production SLOs。
- Canonical main DB writes 不属于 acceptance 范围。Acceptance 必须保持 production-shaped but isolated。
- 要求每个 external source 都 live PASS 不属于本 PRD 范围。当前置条件真实缺失时，honest blocked/external-failure states 是有效结果。
- 立即删除每个 historical helper 不属于本 PRD 范围。要求是将它们从 completion criteria 中退役，并安全迁移/废弃 product consumers。
- 新增 third-party dependencies 不属于本 PRD 范围，除非现有 libraries 或 ports 无法实现当前 source。
- 重写整个 data platform 不属于本 PRD 范围。应复用现有 modules，并围绕最高 acceptance seam 收敛。

## 进一步说明

- Triage label：`ready-for-agent`。
- 本 PRD 取代旧的 Phase 1 完成解释；旧解释中，generic sandbox/dry-run/replay evidence 曾可能被计入 closure。
- 用户定义的 R4 标准是：代码层面达到 authority docs/contracts/rules 所描述的最终产品形态。R5 只能在此完成后开始。
- 核心风险不是缺少代码，而是 acceptance authority 分裂。最短正确修复是先让 official entrypoints 收敛到 task01 acceptance spine，再继续向 Phase 2 往上建设。
- 预期 Phase 1 gate 是严格的：如果 `sync/backfill/full-load/scheduler` 不能通过 production-equivalent acceptance DB 证明完整 route->fetch->validate->conflict->write->clean 链路，Phase 2 必须继续阻塞。
