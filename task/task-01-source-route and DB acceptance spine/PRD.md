## Problem Statement

用户当前面对的问题不是单个数据源不可用，而是产品数据链路的最终口径不稳定：设计文档、架构设计、规则定义、契约和当前实现之间存在阶段性表达、mock/replay 路径、dry-run 成功、沙箱验收、真实联网验收、clean 主值写入、Validation 源降级写入等多套语义。后续执行者容易把阶段性实现当成最终成品，继续停留在 mock、replay、staged fixture 或不落库的路径上，而不是推进到正式业务实现。

用户需要的是一条清晰的成品级数据链路：从 SourceRoutePlan 到 DataSourceService，从真实 fetch 到 raw/staging，从 DataQualityValidator 和 SourceConflictValidator 到 WriteManager，再到 clean 表和下游 Layer 读取。这个链路必须能区分 primary-grade clean 与 degraded clean，必须禁止 silent fallback，必须禁止把 Validation 源伪装成 Primary，也必须禁止把 mock/replay/dry-run 结果冒充成品验收。

用户还需要一个与最终主库形态一致、但物理隔离的 production-equivalent acceptance DB。它不是普通测试临时库，也不是仅用于安全演练的 sandbox；它要暴露真实数据源、真实网络、真实 schema、真实写入、真实下游读取中的问题，并用验收报告诚实标记 live、mock、replay、dry_run、not_implemented、FAIL_EXTERNAL、degraded clean 等状态。

## Solution

建立“Source Route and DB Acceptance Spine”：一条成品级验收主干，统一数据源路由、降级写入、RoutePlan 持久化、生产等价验收库和指标全链路准入语义。

从 codebase-design 视角看，它必须是一个深 Module：外部 Interface 很小，Implementation 很深。调用方只表达“我要验收哪个 source/domain/window，并把结果写到哪里”，不需要知道 route planner、fetch port、adapter、staging 表、validation report、conflict report、WriteManager 参数、Layer 探针如何串起来。

推荐外部 Seam：`SourceRouteDbAcceptanceSpine`。

推荐 Interface：

```text
preview(request) -> AcceptancePreview
execute(request, data_root, live_authorized) -> AcceptanceReport
```

其中 `AcceptanceReport` 是业务和审计共同读取的结果契约，必须包含 source_id、data_domain、route_plan_id、route_grade、implementation_mode、write_grade、source_used、source_role、source_switched、quality_flags、stale_reason/fallback_reason、schema_hash、content_hash、validation_status、conflict_status、failure_class、downstream_layer_read_status。

这个 Module 的 Implementation 可以继续复用现有 `DataSourceService`、`DataSyncOrchestrator`、`DataQualityValidator`、`SourceConflictValidator`、`WriteManager`、`production_equivalent_smoke.py` 和 source-specific live acceptance 资产，但这些都不得成为新的外部 Seam。旧入口要么成为内部 Adapter，要么在迁移完成后退场。

解决方案从用户视角看是：

1. 所有设计文档、架构设计、规则定义、契约只描述最终成品约束，不再出现阶段性目标或阶段性逃生口。
2. SourceRoutePlan 成为正式业务链路的一部分，所有 fetch、validation、clean 写入和验收报告都能追溯到持久化 RoutePlan。
3. Primary、Validation、FallbackPolicy 的语义固定：Validation 源不能无标记接管 clean 主值；只有 domain 级 FallbackPolicy 明确授权时，Validation 源才能以 degraded clean 进入链路。
4. clean 表语义固定为“已校验、可追溯、可被系统读取”，并进一步区分 primary-grade clean 与 degraded clean。
5. WriteManager 必须记录 source_used、source_role、source_switched、quality_flags、stale_reason 或 fallback_reason，避免降级数据伪装成正常主源数据。
6. production-equivalent acceptance DB 作为唯一成品验收主干：形态与最终主库一致，数据根隔离，不写 canonical 主库。
7. mock/replay/dry-run/not_implemented 只能作为缺陷或剩余工程量分类，不能作为成品验收通过依据。
8. 现有普通单元测试、临时测试库、source-specific sandbox 可保留，但不能替代 production-equivalent acceptance。
9. 任务最终关闭标准扩大为：旧 helper / 旧 smoke 入口完成迁移并清理，且 `docs/modules/data_sources.md` 的总数据源清单全部接入 `SourceRouteDbAcceptanceSpine`，每个源都能产出同一 `AcceptanceReport` 语义。
10. 多数据源扩展前必须先完成旧入口迁移和清理；否则旧 seam 会随新增数据源一起扩散，后续无法判断哪个入口才是成品验收标准。

## User Stories

1. 作为项目负责人，我想让权威设计文件只描述最终成品约束，所以后续执行者不会把阶段性实现当成产品目标。
2. 作为项目负责人，我想禁止权威设计文件出现阶段名，所以执行计划和产品设计不会混在一起。
3. 作为项目负责人，我想把执行阶段只放在任务计划中，所以代码实现可以按计划推进，但产品口径保持稳定。
4. 作为数据平台维护者，我想所有 fetch 前都有 SourceRoutePlan，所以我能知道系统为什么选择某个数据源。
5. 作为数据平台维护者，我想 SourceRoutePlan 被持久化，所以验收失败后可以追溯数据源选择过程。
6. 作为数据平台维护者，我想 RoutePlan 记录 Primary 失败原因，所以我能区分 auth、rate limit、schema drift、empty response、not published 和 network failure。
7. 作为数据平台维护者，我想 RoutePlan 记录 route_grade，所以我能区分 primary、degraded 和 blocked 路径。
8. 作为数据平台维护者，我想 route/audit payload 记录 fallback 策略，所以 fallback 不再是隐式行为。
9. 作为数据平台维护者，我想禁止 silent fallback，所以主源失败不会被系统偷偷掩盖。
10. 作为数据平台维护者，我想 Validation 源只能在 FallbackPolicy 授权下进入 clean，所以旁证源不会伪装成主事实源。
11. 作为数据平台维护者，我想 degraded clean 必须写 source_switched，所以任何降级数据都可被下游识别。
12. 作为数据平台维护者，我想 degraded clean 必须写 quality_flags，所以报告和前端能展示数据质量状态。
13. 作为数据平台维护者，我想 degraded clean 必须写 stale_reason 或 fallback_reason，所以用户能理解为什么发生降级。
14. 作为数据平台维护者，我想 last_good_cache 只能在策略允许时使用，所以缓存不会伪装成最新数据。
15. 作为数据平台维护者，我想 schema drift 阻止正常 clean 写入，所以字段变化不会污染主表。
16. 作为数据平台维护者，我想 severe source conflict 阻止 clean 写入，所以冲突数据不会被误当成事实。
17. 作为数据平台维护者，我想 manual_review_required 阻止自动写入，所以需要人工判断的数据不会自动进入主链路。
18. 作为数据平台维护者，我想 DataSourceService 是正式 fetch 入口，所以产品路径不会绕过 capability、license、ResourceGuard 和 RoutePlan。
19. 作为数据平台维护者，我想 runner 不能直传 adapter 进入产品路径，所以单元测试隔离不会变成正式业务入口。
20. 作为数据平台维护者，我想 WriteManager 是唯一 clean 写入边界，所以所有 clean 数据都有验证和审计。
21. 作为数据平台维护者，我想 clean 分成 primary-grade clean 和 degraded clean，所以下游不会混淆正常主源数据和降级数据。
22. 作为 Layer 模型维护者，我想读取 clean 时知道 source_switched，所以模型可以拒绝、降权、仅展示或返回诚实 NULL。
23. 作为 Layer 模型维护者，我想指标全链路验收使用 production-equivalent DB，所以模型结果能反映真实数据链路。
24. 作为 Layer 模型维护者，我想 mock/replay 不能作为指标全链路完成证据，所以模型不会建立在假数据路径上。
25. 作为业务用户，我想看到数据是否来自正常主源，所以我能判断报告可信度。
26. 作为业务用户，我想看到数据是否是降级来源，所以我不会把应急数据当作正常数据。
27. 作为业务用户，我想看到外部源失败被如实记录，所以我知道问题来自系统实现还是外部环境。
28. 作为业务用户，我想验收报告区分 live、mock、replay、dry_run 和 not_implemented，所以我能判断产品完成度。
29. 作为业务用户，我想验收库与最终主库形态一致，所以验收能发现字段、schema、契约和下游读取问题。
30. 作为业务用户，我想验收库不写 canonical 主库，所以真实验收不会污染当前主数据。
31. 作为审计者，我想验收报告列出 source_id 和 data_domain，所以我能定位每条链路的责任边界。
32. 作为审计者，我想验收报告列出 route_grade 和 write_grade，所以我能判断数据是否是主源级或降级级。
33. 作为审计者，我想验收报告列出 validation_status 和 conflict_status，所以我能确认数据是否通过质量和冲突检查。
34. 作为审计者，我想验收报告列出 schema_hash 和 content_hash，所以我能复盘真实输入是否变化。
35. 作为审计者，我想验收报告列出 failure_class，所以 FAIL_EXTERNAL 不会被误写成产品成功。
36. 作为审计者，我想验收报告列出 downstream_layer_read_status，所以我能确认 clean 数据真的被 Layer 消费。
37. 作为开发者，我想权威契约不再出现阶段性 status，所以我不会把阶段名当成最终目标。
38. 作为开发者，我想 mock 只能用于单元测试隔离外部副作用，所以我不会把 mock 放进正式业务代码。
39. 作为开发者，我想测试 helper 和产品入口边界清晰，所以测试便利不会泄漏到生产实现。
40. 作为开发者，我想生产等价验收只有一个最高层 seam，所以我不需要在多个低层 seam 里重复证明同一件事。
41. 作为运维者，我想 production-equivalent acceptance 使用隔离数据根，所以我能安全运行真实链路。
42. 作为运维者，我想真实 live 需要用户授权和环境门，所以不会无意触发真实联网或付费服务。
43. 作为运维者，我想 acceptance DB 使用与主库相同的 migrations/schema/spec/contracts，所以验收结果可以代表最终主库形态。
44. 作为运维者，我想验收报告保留 mock/replay/not_implemented 分类，所以我能安排后续修复优先级。
45. 作为后续 agent，我想 PRD 明确 out of scope，所以我不会把文档清理、代码重构、真实联网和主库写入混成一个任务。

## Implementation Decisions

- 设计一个新的深 Module：`SourceRouteDbAcceptanceSpine`。它的外部 Interface 只暴露 preview/execute 与结构化 AcceptanceReport；route、fetch、validate、conflict、write、Layer read、report assembly 都是内部 Implementation。
- `DataSourceService`、`DataSyncOrchestrator` 和 `WriteManager` 不是替代对象，而是该 Module 内部复用的现有 Module。
- `production_equivalent_smoke.py` 当前只是 pytest/smoke/metrics 包装器；它可以作为迁移期 Adapter，但不能作为最终 production-equivalent acceptance 的权威 Interface。
- `backend/app/ops/tier_a_live_acceptance.py` 是最接近正式 Implementation 的 source-specific prior art；它可以贡献隔离 DB、live env validation、manifest 和报告经验，但最终 Interface 不应按 Tier A/source-specific 形状暴露。
- `tests/live_incremental_support.py` 是测试 helper，包含 monkeypatch 和 injected factories；它可帮助测试，但不得升级成成品验收 Module。
- RoutePlan 持久化的首选落点先采用现有 `job_event_log.payload_json` 的 `ROUTE_PLAN` 事件；只有当查询、留存或报告需求证明它不够深时，再迁移到专门 `source_route_log` 表。
- `source_route_contract.yaml` 当前已有 RoutePlan-before-adapter 和 job_event_log/source_route_log 持久化规则，但还缺少最终 `route_grade=primary|degraded|blocked` 作为一等契约字段。
- `write_contract.yaml` 与当前 `WriteRequest` 已有 `source_used`、`source_role`，但还未完全覆盖 degraded clean 所需的 `source_switched`、`quality_flags`、`stale_reason/fallback_reason`。
- 当前 `WriteManager` audit 写入已有 `source_switched` 与 `stale_reason` 列，但实现仍会写死为 `False` / `None`；本任务必须把这些字段从 WriteRequest 传入 audit，而不是继续丢失降级语义。
- 建立一条成品级 “Source Route and DB Acceptance Spine”，贯穿 SourceRoutePlan、DataSourceService、DataQualityValidator、SourceConflictValidator、WriteManager、clean 表和 Layer 读取。
- SourceRoutePlan 必须持久化。允许通过专门 route log 或 job event payload 实现，但不得只在内存中生成后丢弃。
- RoutePlan 必须表达 route_grade，稳定语义为 primary、degraded、blocked。
- RoutePlan 必须记录 Primary 失败原因，包括 auth failure、rate limit、schema drift、empty response、not published、network failure、resource guard block、source disabled、capability missing 等。
- FallbackPolicy 必须是 domain 级策略，不允许 provider 全局自作主张接管。
- FallbackPolicy 支持 retry_same_source、use_validation_source_with_flag、use_last_good_cache、mark_missing、manual_review_required、skip_until_next_publish。
- Validation 源默认只用于 validation、source conflict、manual review 或 evidence。
- Validation 源只有在 domain FallbackPolicy 明确授权 use_validation_source_with_flag 时，才允许以 degraded clean 写入。
- degraded clean 必须写 source_role=fallback、source_switched=true、SOURCE_FALLBACK_USED。
- 如果 degraded clean 实际使用 Validation 源，还必须写 VALIDATION_SOURCE_USED。
- clean 的产品定义是“已校验、可追溯、可被系统读取”，不是“永远来自正常主源”。
- clean 必须区分 primary-grade clean 与 degraded clean。
- 下游 Layer、前端和 Agent 必须能识别 degraded clean，不能静默当成 primary-grade clean。
- 若某指标或模型声明只接受 primary-grade 输入，遇到 degraded clean 必须 fail-closed、降权、仅展示或返回诚实 NULL。
- WriteManager 必须成为 clean 写入唯一边界。
- WriteManager 输入契约必须包含 source_used、source_role、source_switched、quality_flags、stale_reason 或 fallback_reason。
- ValidationGate 最终状态必须能区分 PASSED_PRIMARY、PASSED_DEGRADED、FAILED、MANUAL_REVIEW_REQUIRED 或等价产品语义。
- DataSourceService 必须是正式 fetch 入口，产品路径不得绕过 capability、license/auth、ResourceGuard、SourceRoutePlan 和 route/audit 记录。
- runner 直传 adapter 只能作为单元测试隔离外部 I/O 的 helper，不得进入产品 CLI、production-equivalent acceptance、指标全链路验收或正式 clean 写入。
- production-equivalent acceptance DB 是成品验收环境，不是普通测试临时库。
- production-equivalent acceptance DB 必须使用与最终主库一致的 migrations、schema、spec 和 contracts。
- production-equivalent acceptance DB 必须位于隔离数据根，禁止写 canonical 主库。
- production-equivalent acceptance 必须通过正式入口运行真实 route、fetch、raw/file registry、staging、validation/source conflict、WriteManager、clean 和 Layer read。
- 验收报告必须列出 source_id、data_domain、route_grade、implementation_mode、write_grade、source_used、source_role、source_switched、quality_flags、schema_hash、content_hash、validation_status、conflict_status、failure_class、downstream_layer_read_status。
- implementation_mode 中 live 是唯一可证明真实链路的成功形态；mock、replay、dry_run、not_implemented 只能作为缺陷或剩余工程量分类。
- FAIL_EXTERNAL 允许出现在报告中，但不能被写成源 fetch SUCCESS。
- 所有数据源接入的含义是“都通过同一 spine 入口被枚举、preview、execute 并诚实报告状态”，不是要求每个外部源在未授权、未配置或商业许可缺失时都 live PASS。
- `docs/modules/data_sources.md` 第 5.9.1 节的总数据源清单是本任务多源扩展的人工设计权威；机器可读枚举仍应来自 `specs/datasource_registry/source_registry.yaml` 和 `source_capabilities.yaml`。
- 对 QMT / xtdata、同花顺 / iFinD、Yahoo、Alpha Vantage、FRED 等需要授权、key 或本机环境的源，缺少前置条件时必须输出 `BLOCKED`、`DISABLED_SOURCE`、`FAIL_EXTERNAL` 或等价诚实状态，不得用 replay/mock 代替 PASS。
- 权威设计文档、架构设计、规则定义和契约不得使用执行阶段词描述最终目标。执行阶段只能出现在 task 执行计划中。
- 普通单元测试仍允许 mock 外部 I/O，但 mock 不得进入正式业务实现，也不得作为成品验收通过依据。
- 现有 source-specific sandbox、临时测试库和 live acceptance helper 可作为参考或局部验证基础，但不能替代 production-equivalent acceptance spine。

## Testing Decisions

- 最高层测试 seam 采用 production-equivalent acceptance 入口。该 seam 是本 PRD 的核心验收 seam，也是唯一需要证明成品链路成立的最高层 seam。
- 该 seam 应通过正式 CLI 委托到 Module Interface 触发，而不是直接调用底层 adapter、runner 或测试 helper。
- 该 seam 必须使用隔离 acceptance DB，但 schema、migration、spec、contract 与最终主库一致。
- 好测试应验证外部业务行为：是否生成持久化 RoutePlan、是否真实 fetch、是否写 raw/staging、是否生成 validation/conflict 报告、是否经 WriteManager 写 clean、是否被 Layer read 消费、是否生成完整验收报告。
- 好测试不应验证私有函数调用次数、内部方法顺序、monkeypatch 是否生效等实现细节。
- 单元测试可以继续 mock 外部 I/O，但测试命名、断言和报告必须表明它是 mock/replay/fixture，不得命名成 live success。
- production-equivalent acceptance 禁止通过 monkeypatch ResourceGuard、source enablement、registry 或 route planner 来冒充真实链路。
- production-equivalent acceptance 可以在缺少授权或外部源不可用时输出 blocked、FAIL_EXTERNAL、not_implemented，但不能输出假 PASS。
- SourceRoutePlan 测试应验证 route_grade、fallback 策略、primary_failure_reason、quality_flags 和持久化证据。
- WriteManager 测试应验证 degraded clean 的 source_role、source_switched、quality_flags、stale_reason/fallback_reason，以及未经授权 Validation 源不得写 clean。
- DataSourceService 测试应验证正式 fetch 入口会生成 RoutePlan、检查 capability、检查 ResourceGuard，并保留 fetch/audit 证据。
- DataQualityValidator 和 SourceConflictValidator 测试应验证 schema drift、empty response、required field missing、severe conflict、manual review required 等业务语义。
- Layer read 测试应验证下游遇到 degraded clean 时可拒绝、降权、仅展示或返回诚实 NULL。
- 验收报告测试应验证 implementation_mode 不会把 mock/replay/dry_run/not_implemented 当成 live 成功。
- 验收报告测试应验证 FAIL_EXTERNAL 行保留 failure_class、source_id、request 和错误摘要。
- prior art 包括已有 live incremental acceptance helpers、source route planner tests、sync orchestrator tests、write manager tests、module boundary checks、production gate checks 和 resource guard tests；本 PRD 要求把这些低层能力收敛到一个成品级最高 seam。

## Out of Scope

- 不在本 PRD 中实现代码修改。
- 不在本 PRD 中启用 canonical 主库写入。
- 不在本 PRD 中要求所有外部源 live SUCCESS；但本任务最终关闭必须让总数据源清单里的每个源都进入同一 acceptance spine，并按真实前置条件诚实报告 PASS/BLOCKED/FAIL_EXTERNAL/disabled 等状态。
- 不在本 PRD 中引入真实交易、账户控制、自动下单、QMT 自动登录或验证码处理。
- 不在本 PRD 中新增大型依赖或外部服务。
- 不在本 PRD 中把 Validation 源普遍升级为 Primary。
- 不在本 PRD 中删除所有单元测试 mock；只禁止 mock 进入正式业务实现和成品验收通过依据。
- 不在本 PRD 中定义执行批次、阶段或任务顺序；这些内容必须放到 task 执行计划。
- 不在本 PRD 中重写全部历史文档台账；历史台账可保留历史阶段词，但权威设计、架构、规则和契约不得用阶段词定义最终目标。
- 不在本 PRD 中完成 62 个指标的全部真实链路接入；本 PRD 只定义验收主干和准入语义。

## Migration and Deprecation

- 替代对象：source-specific sandbox/live helpers、pytest smoke wrappers、直接拼 route/fetch/write 的临时验收路径。
- 替代目标：`SourceRouteDbAcceptanceSpine` 作为唯一生产等价验收 Module。
- 迁移策略：先 advisory deprecation，不立即删除旧 helper。旧入口先作为 Adapter 委托到新 Module，直到测试、CI、文档和人工 runbook 不再直接依赖旧入口。多数据源扩展必须在旧入口迁移/清理之后进行。
- 迁移工具：新增检查脚本或测试，列出仍直接调用旧 helper、直接构造 adapter 绕过 DataSourceService、或把 smoke wrapper 当 production-equivalent PASS 的位置。
- compulsory removal 条件：所有活跃消费者已迁移，CI 和任务文档只引用新 Interface，旧入口使用量为零。
- 禁止做法：在替代 Module 未覆盖关键用例前删除旧 helper；在旧 helper 中继续新增产品能力；用旧 helper 的 mock/replay 成功冒充新 Module 的 live 验收。

## Further Notes

- 建议 triage label：`ready-for-agent`。
- 本 PRD 使用当前对话中已确认的口径：权威设计文件描述最终成品，执行阶段只存在于 task 计划。
- 用户已明确要求后续正式业务实现禁止 mock 或非正式实现冒充完成。
- 当前代码中已有 acceptance DB 雏形和 source-specific live acceptance 资产，但仍需重构为统一 production-equivalent acceptance spine。
- 当前代码中已有普通测试临时库和 sandbox guard，这些资产可保留，但不能作为最终成品验收的替代。
- 本 PRD 的推荐测试 seam 是单一最高 seam：production-equivalent acceptance runner / CLI。若实现者提出更多 seam，必须证明它们不会弱化成品验收。
