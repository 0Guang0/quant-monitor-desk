# completion-check

- 角色：`execute`
- 日期：`2026-07-11`
- 对应 plan：`task/task-01-source-registry/task_plan.md` 工作包 3 · 3A；票 `.scratch/task-01-g1-02-enable-seam/issues/03-ask-activation-overlay.md`
- 对象范围：票 **03** 仅「问开关 API + `source_activation_overlay` 持久化（隔离根可测）」；**不含** 3B 安检接线、3C/E-TEST 夹具迁移、4a/4b/4x ESR 清零、G1-02 整切片、模块 R4、3-OBS 遥测管道、管理员撤销 CLI
- 声称：票 03 AC 执行关账（≠ G1-02 CLOSED / ≠ R4）
- 权威：ADR-018 · `docs/modules/design/data_sources.md` §5.2.1 · `g1-02-execution-brief.md` §1.1 / §6 3A · 票 03 AC
- 正式入口：`ask_activation` / `write_activation_overlay`（库 API 接缝）+ `apply_migrations`→`017_source_activation_overlay`；**尚未**成为 CLI/RoutePlanner 生产调用面（属票 04+）
- 声称档位：`product_default`（无 overlay 拒绝 P-MACRO）+ `sandbox`（隔离根正规 overlay 允许）；非 live / 非 G1-08

## 逐对象关账记录

### 对象 A · 票 03 问开关 + overlay 持久化

| CC        | 具体场景示范                                         | 本对象运行事实                                                                                                                                                                            | 证据 / 反证                                                                                                                                                                               | Verdict | 闭环控制                                                             |
| --------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | -------------------------------------------------------------------- |
| CC-0 对靶 | 用户要业务表与审计表一致，交付只证明 job `COMPLETED` | 用户要票 03：三键→三字段、§5.2.1 表、隔离根可测、禁 setattr/force 后门。交付即该接缝，未把 pytest 绿或 G1-02 整包冒充目标                                                                 | 票 03 AC 四条；实现 `activation_overlay.py` + `017_*.sql`；明确不声称 ESR 迁移                                                                                                            | PASS    | 关账仅票 03；升格 G1-02/R4 须新 claim                                |
| CC-1 证伪 | 集成测注入 `fetch_port` 且只断言无异常               | 覆盖集合：①三字段契约 ②setattr 不放行 ③sandbox overlay 允许 vs 产品库拒绝 ④overlay.enabled=false 拒 ⑤base 启用允许 ⑥sandbox 标记强制 ⑦迁移建表。删除 overlay 行后同参重回 DISABLED_SOURCE | `uv run pytest -q tests/test_activation_overlay.py tests/test_schema_migration.py` 绿；手工 `DELETE FROM source_activation_overlay` → `DISCRIMINATION_OK`；已删 meta-testing `hasattr` 测 | PASS    | 再引入内存读 `SourceRecord.is_enabled` 或忽略 overlay 时上述测必须红 |
| CC-2 验真 | 权威要求校验→双写→回读，实现只转状态                 | 原子：迁移建表、write 落库（operator/time/reason/revision）、ask 回读最新未撤销、无 force_enable。撤销**列**已齐；撤销**API**/3-OBS/安检接线不在本票 AC                                   | 表可 INSERT/SELECT；ask 读 DB 非内存；`sandbox=True` 无标记 → ValueError                                                                                                                  | PASS    | 本 claim 不含 revoke CLI / RoutePlanner 接线；若声称含之则改 FAIL    |
| CC-3 同路 | CLI 用 overlay 启用可写，scheduler 读默认 registry   | 声称入口仅库 API 问开关；生产 CLI/增量仍走 ESR（**范围外**，票 06–08）。同库 ask 同参一致；产品库 vs 沙箱库分裂是**有意档位差**非入口分裂                                                 | inventory 仍列 ESR；本票未改 `enabled_source_registry`（CRITICAL，有意不迁）                                                                                                              | PASS    | 若声称「正式 CLI 已同路」→ FAIL；当前声称未含                        |
| CC-4 验档 | 报告标 live，fetch_id 含 replay                      | 证据分档：product_default 无 overlay 拒 P-MACRO；sandbox 隔离路径写 `[sandbox]` overlay 后允许。未标 live/product-enabled                                                                 | 双 DuckDB 路径测试；`sandbox=True` 强制 reason 含 sandbox                                                                                                                                 | PASS    | 禁止用 sandbox 允许升格「产品已默认启用」                            |
| CC-5 对表 | 权威失败码被吞成 exit 0                              | 形：DDL 对齐 §5.2.1 字段；义：拒绝=`DISABLED_SOURCE`（ERROR_CODE_GUIDE），允许 reason 空串不自造成功码；行为：最新未撤销 overlay 优先于 DB base；效果：P-MACRO 产品拒 / 沙箱允            | design DDL vs `017_*.sql` / `schema.sql`；测试断言 reason_code                                                                                                                            | PASS    | 改 DDL 字段须再审阅 design；本轮未改 design 语义                     |
| CC-6 清债 | 三处 monkeypatch 代替共享根因                        | 本轮修：删 meta-testing hasattr；补 overlay deny / base allow / sandbox 标记；纠正 INGESTION_TABLES 漂移。ESR 旁路属后续票，非本轮可关且未用来支撑本 claim                                | 测试文件 diff；impact(ESR)=CRITICAL → 不在本切片强迁                                                                                                                                      | PASS    | ESR/3B/3C 严格后置票 04–08；不支撑本 claim CLOSED 以外对象           |
| CC-7 守闸 | 缺密钥切 mock 仍报 live PASS                         | 诚实未完成：RoutePlanner 消费、CLI 迁出 ESR、E-TEST 夹具、FRED 合并、模块 R4、撤销管理 CLI、3-OBS 日志管道。状态保持 OPEN 于更大对象                                                      | HANDOFF / brief 依赖图；台账 `T01-ENABLE-FRED-MERGE-001`                                                                                                                                  | PASS    | CC-7 PASS≠G1-02 完成；更大对象仍 OPEN                                |

## Summary

- 首个决定性缺口：none（修复后：原 meta-testing / 缺 deny 路径 / sandbox 标记未强制 / INGESTION 断言漂移已闭环）
- 最终状态：`CLOSED`
- 声称结论：`permitted`（**仅**票 03 AC）
- 闭环控制：再验入口 = `uv run pytest -q tests/test_activation_overlay.py tests/test_schema_migration.py`；人为删 overlay 行或去掉 sandbox 标记校验须使对应断言失败；不得将本记录当作 G1-02 / R4 / ESR 清零关账

## 测试资产治理（TEST-EVIDENCE-GOVERNANCE）

| 资产                                                        | 角色                | 处置                           |
| ----------------------------------------------------------- | ------------------- | ------------------------------ |
| `test_askActivation_returnsThreeFieldDecision`              | 核心契约            | 保留                           |
| `test_askActivation_baseEnabledSource_allowsWithoutOverlay` | 核心 / 回落 base    | 保留                           |
| `test_askActivation_ignoresInMemorySetattrBypass`           | 回归 / 禁撬门       | 保留                           |
| `test_sandboxOverlay_allowsWhileProductDefaultStillDenies`  | 核心 / 档位         | 保留                           |
| `test_overlayEnabledFalse_deniesEvenWhenBaseEnabled`        | 核心 / 正规拒绝     | 保留（替原 hasattr meta-test） |
| `test_writeSandboxOverlay_requiresSandboxMarker`            | 边界 / ADR-018 标记 | 保留                           |
| `test_migrationCreatesSourceActivationOverlayTable`         | contract / 迁移     | 保留                           |
| 原 `test_activationOverlay_moduleHasNoForceEnableBackdoor`  | meta-testing        | **已删除**                     |

---

# completion-check · 追加轮次（票 01 / 02）

- 角色：`execute`
- 日期：`2026-07-11`
- 对应 plan：`task/task-01-source-registry/task_plan.md` 工作包 1·2；票 `.scratch/task-01-g1-02-enable-seam/issues/01-capability-contract.md` · `02-macro-supplementary-default.md`
- 对象范围：票 **01**（capability 加载可执行校验 + 生产配置升级）∥ 票 **02**（默认域失败关闭，消灭 validation_only Primary 伪放行）；**不含** 票 03 以外的 G1-02 3B/3C、4a/4b/4x、G1-02 整包、模块 R4、完整 JSON Schema 引擎、管理员 overlay CLI
- 声称：票 01 + 票 02 AC 执行关账（≠ G1-02 CLOSED / ≠ R4 / ≠ 票 03 以外对象）
- 权威：`task_plan.md` WP1/WP2 · 票 01/02 AC · `specs/contracts/source_capability_contract.yaml` · `docs/modules/design/data_sources.md` 默认启用/domain gating · findings T01-F01/T01-F02
- 正式入口：`SourceCapabilityRegistry.load` · `SourceRegistry.load` / `_validate_domain_roles` · 未 monkeypatch 的 `SourceRoutePlanner.plan`（`DataSourceService.fetch` 同用该 planner）
- 声称档位：`product_default`（生产 YAML 加载与默认路由）；非法样本用仓库内 fixture / 临时合法路径下 draft 样本；非 live / 非 G1-08

## 逐对象关账记录

### 对象 B · 票 01 Capability 契约可执行校验

| CC | 具体场景示范 | 本对象运行事实 | 证据 / 反证 | Verdict | 闭环控制 |
|---|---|---|---|---|---|
| CC-0 对靶 | 用户要业务一致，交付只证明 job COMPLETED | 用户要：非法 capability 在**加载边界**稳定失败；生产配置去 draft/implementation_gap；不缩校验范围。交付即 load 校验 + YAML/契约升级；未把 pytest 绿或「完整 schema 引擎」冒充整包 R4 | 票 01 AC；`_validate_capability_document`；YAML `status: active`；契约去伪 evidence | PASS | 关账仅票 01；升格「全量 schema 解释器 / R4」须新 claim |
| CC-1 证伪 | 注入假绿 | 覆盖集合：①draft 拒 ②implementation_gap 拒 ③缺 frequency/fields\|output/requires_auth 拒 ④空 domains 拒 ⑤生产 active 可加载且 baostock 三元组可断言。反证：临时 draft YAML → `CapabilityRegistryError`（`T01_DRAFT_DISCRIM_OK`） | `uv run pytest -q tests/test_source_capabilities.py` exit 0；脚本反证 draft 必红；既有 adapter reconciliation 测仍绿 | PASS | 再放行 draft/gap 或去掉 op 字段校验时上述测/反证必须红 |
| CC-2 验真 | 权威要双写，实现只转状态 | 原子：顶层/源级拒 draft；拒 unresolved gap；每源须 domains；每 op 须 frequency + 字段声明（含 observation_fields/bundle_fields）+ requires_auth；生产 25 源可 load。适配器域对齐由既有 reconciliation **测试**强制（load **不**冒充查 adapter）— 与诚实 notes/契约 evidence 一致 | 生产 load OK；notes/契约已删「load 强制 adapter alignment」假证据；`test_adapterSupportedDomains_*` 仍在 | PASS | 若声称「load 内核对 adapter.supported_domains」→ FAIL；当前声称不含 |
| CC-3 同路 | CLI 与 scheduler 分裂 | 声称入口=`SourceCapabilityRegistry.load`；凡经该 load 的消费方（planner/service/矩阵等）同规则。未另开旁路加载器 | Grep/实现：唯一正式 load 实现含 `_validate_capability_document` | PASS | 若新增跳过校验的 load 旁路 → FAIL |
| CC-4 验档 | 标 live 实为 replay | 证据为 product_default 配置加载 + 非法 fixture；未声称 live 启用新源 | 生产 YAML status=active；非法样本在 tests/fixtures 或项目根临时文件 | PASS | 禁止把「配置可加载」升格为「域已默认可调度生产抓取」 |
| CC-5 对表 | 失败吞成 exit 0 | 形：契约 status=active、required_tests 指向真实测名；义：draft/gap 不可作放行；行为：非法即 `CapabilityRegistryError`；效果：生产可加载。本轮审查发现契约/notes 过度声明 → **已修**（工作区 diff） | 契约 evidence 仅留 adapter 测试；notes 写明 load 拒 gap、对齐靠测试 | PASS | 再写入「load=adapter 对齐」假证据 → 本 claim 失效须重验 |
| CC-6 清债 | 三处 patch 代根因 | 本轮：可执行校验落地；删契约假 evidence；收紧 notes；补全 ponytail 空 map 的 ceiling/upgrade。T01-F01 → 已修复。未借本票迁 ESR | findings 开放项仅 T01-F03；honesty diff 在工作区 | PASS | ESR/3B 严格后置票 04–08，不支撑本 claim 以外对象 |
| CC-7 守闸 | 缺密钥仍报 live PASS | 诚实未完成：完整 JSON Schema 引擎、load 内 adapter 扫描、G1-02 整包、模块 R4、问开关消费方 | HANDOFF Frontier=04∥05；Audit 仍 OPEN | PASS | CC-7 PASS≠R4；更大对象仍 OPEN |

### 对象 C · 票 02 macro_supplementary 默认诚实关闭

| CC | 具体场景示范 | 本对象运行事实 | 证据 / 反证 | Verdict | 闭环控制 |
|---|---|---|---|---|---|
| CC-0 对靶 | 只证明报告非空 | 用户要：无合规 Primary 时默认失败关闭；`macro_supplementary` 不再 `VALIDATION_ONLY_BLOCKED` 伪放行；不升格 AkShare。交付=加载守卫 + 三域 YAML 关闭 + 默认路由 DISABLED_SOURCE | 票 02 AC；akshare 仍 `validation_only=True`；primary 仍 akshare | PASS | 关账仅票 02；「合规 Primary 后重新默认启用」须新 claim+设计 |
| CC-1 证伪 | 弱断言放行 | 覆盖：①加载拒 validation_only+domain_enabled ②生产默认启用域均有可调度 Primary ③macro 默认 disabled + assert_domain_schedulable→DISABLED_SOURCE ④未 monkeypatch planner→DISABLED_SOURCE+DOMAIN_DISABLED_BY_DEFAULT ⑤sibling：cn_index/sector_board/minute_bar/macro_series 默认 DISABLED。反证：`bad_validation_only_primary_enabled.yaml` load → InvalidRegistryError（`T02_VALONLY_DISCRIM_OK`） | pytest registry+route 绿；脚本 `T02_ROUTE DISABLED_SOURCE`；四 sibling 路由同为 DISABLED_SOURCE | PASS | 再把三域改回 enabled_default 或删 validation_only 守卫 → load/测必须红 |
| CC-2 验真 | 只改文档 | 原子：`_validate_domain_roles` 共享守卫；YAML 三域 `domain_enabled_by_default:false`+`disabled_until_configured:true`+`expected_error=DISABLED_SOURCE`；默认路由可观察 DISABLED_SOURCE。未改 AkShare 角色 | registry YAML；route plan 实测 | PASS | 若 AkShare `validation_only` 被静默去掉 → 本 claim 失效 |
| CC-3 同路 | CLI 旁路 | 域策略在 `SourceRegistry.load`；路由消费同一 binding。`DataSourceService.fetch` 调同一 `SourceRoutePlanner.plan`，非第二套默认策略 | service.py `fetch`→`_route_planner.plan`；production_route_planner 用正式 load | PASS | 若 ESR/OVERRIDE 绕过本守卫宣称「默认已同路启用」→ 属 T01-F03/票 06–08，非本 claim |
| CC-4 验档 | 沙箱冒充产品默认 | 证据=生产 YAML + 未 patch 的 planner；monkeypatch 的 VALIDATION_ONLY_BLOCKED 测（R3H-02/04）仍测「强制启用后」行为，**不**充当默认档位证据 | `test_macro_supplementary_defaultRoute_isDisabledSource` 无 monkeypatch；R3H 测有意 patch | PASS | 禁止用 patch 后 VALIDATION_ONLY_BLOCKED 证明「默认已诚实」 |
| CC-5 对表 | 权威要 DISABLED，实现仍伪放行 | 形/义/行为/效果：默认=`DISABLED_SOURCE`+`DOMAIN_DISABLED_BY_DEFAULT`；与 `data_sources.md` 无合规主源则 domain 关闭一致；不再默认返回 VALIDATION_ONLY_BLOCKED | 实测 route_status 与 quality_flags | PASS | 默认再出现 VALIDATION_ONLY_BLOCKED → FAIL |
| CC-6 清债 | 只修表象 | 同根矛盾域（cn_index/sector_board）一并关闭+共享守卫；T01-F02 已修复。未升格 AkShare。import 噪声已收 | findings；sibling 路由实测 | PASS | inventory P-SUPP 旧文案若仍写 VALIDATION_ONLY_BLOCKED → 文档漂移，不挡本运行 claim，宜后续改清单 |
| CC-7 守闸 | 隐瞒未完成 | 诚实未完成：合规 Primary 配置前重新启用、ESR 清零、3B overlay 安检、G1-02/R4 | HANDOFF；开放 finding 仅 T01-F03 | PASS | 更大对象仍 OPEN |

## Summary（本追加轮 · 票 01∥02）

- 首个决定性缺口：none（审查期契约假 evidence 已在工作区修正并纳入 CC-5/CC-6）
- 最终状态：`CLOSED`
- 声称结论：`permitted`（**仅**票 01 AC + 票 02 AC）
- 闭环控制：再验 = `uv run pytest -q tests/test_source_capabilities.py tests/test_source_registry.py tests/test_source_route_planner.py`；draft capability 或 `bad_validation_only_primary_enabled.yaml` 须使 load 失败；生产 `macro_supplementary` 未 patch plan 须为 `DISABLED_SOURCE`；**不得**将本记录当作 G1-02 / R4 / ESR 清零 / 票 03 以外关账

## 测试资产治理（本追加轮）

| 资产 | 角色 | 处置 |
|---|---|---|
| `test_capabilityRegistry_load_rejectsDraftStatus` | 核心 / 加载边界 | 保留 |
| `test_capabilityRegistry_load_rejectsImplementationGapMarker` | 核心 / 禁 gap 放行 | 保留 |
| `test_capabilityRegistry_load_rejectsMissingOperationContract` | 核心 / op 契约 | 保留 |
| `test_capabilityRegistry_load_rejectsEmptyDomains` | 边界 | 保留 |
| `test_capabilityRegistry_load_productionConfigSucceeds` | 核心 / 生产可加载 | 保留 |
| 既有 `test_adapterSupportedDomains_*` / domain 对齐测 | contract | 保留（adapter 对齐证据，非 load 冒充） |
| `test_load_validationOnlyPrimaryWhenDomainEnabled_raisesInvalidRegistryError` | 核心 / 配置矛盾 | 保留 |
| `test_domainsEnabledByDefault_haveSchedulablePrimary` | 核心 / 生产不变量 | 保留 |
| `test_macro_supplementary_defaultDisabledUntilConfigured` | 核心 / 域默认 | 保留 |
| `test_macro_supplementary_defaultRoute_isDisabledSource` | 核心 / 默认路由 | 保留 |
| `bad_validation_only_primary_enabled.yaml` | 反证 fixture | 保留 |
| R3H-02/04 validationOnlyPrimaryBlocked（monkeypatch） | 回归 / 强制启用后行为 | 保留；**不得**作默认档位完成证据 |

---

# completion-check · 追加轮次（票 04 / 05）

- 角色：`execute`
- 日期：`2026-07-11`
- 对应 plan：`task/task-01-source-registry/task_plan.md` 工作包 3 · 3B/3C；`g1-02-execution-brief.md` §6；票 `.scratch/task-01-g1-02-enable-seam/issues/04-planner-readonly-overlay-revision.md` · `05-test-fixtures-overlay.md`
- 对象范围：票 **04**（RoutePlanner/Service 只读合成 + `overlay_revision` + 3-OBS stderr）∥ 票 **05**（E-TEST 夹具改正规 overlay；禁 patch 关账证据）。**不含** 4a/4b/4x ESR 清零、G1-02 整包、模块 R4、管理员 overlay CLI、FRED 编排合并
- 声称：票 04 + 票 05 AC 执行关账（≠ G1-02 CLOSED / ≠ R4 / ≠ 全量 pytest 绿）
- 权威：ADR-018 · `data_sources.md` §5.2.1 · brief §1.2/§5/§6 3B·3C · 票 04/05 AC · findings T01-F03 切片
- 正式入口：`DataSourceService.fetch` / `preview_route` → `SourceRoutePlanner.plan(con=…)` → `ask_activation`；测试夹具 `enable_source_route` / `seed_activation_base` → 正式 `plan`/`fetch`
- 声称档位：`product_default`（有 con、无 overlay 时读 DB base；P-MACRO 仍 DISABLED）+ `sandbox`（隔离根正规 overlay）；非 live 升格

## 业务价值（对靶摘要）

| 票 | 交付 | 业务价值 |
|----|------|----------|
| 04 | 安检接问开关；`overlay_revision` 可观察；策略日志 | 正式拉数与预览不再信内存开关；运维能看见「按哪版开关本」做的决定 |
| 05 | E-TEST 用隔离库 overlay 证明启用 | 关账证据不再靠 `__setattr__`/强制 platform 假绿；与产品默认库诚实分离 |

## 逐对象关账记录

### 对象 D · 票 04 安检接线 + overlay_revision / 3-OBS

| CC | 具体场景示范 | 本对象运行事实 | 证据 / 反证 | Verdict | 闭环控制 |
|---|---|---|---|---|---|
| CC-0 对靶 | 只证明 pytest 绿 | 用户要：安检在问开关后合成；CLI/服务只读；revision 进 RoutePlan/日志；无新遥测依赖。交付即 `plan(con=)`→`ask_activation`、Service 透传 con、stderr `source_policy_*`。未把 G1-02/ESR 清零冒充本票 | 票 04 AC 三条；brief 3B/3-OBS；实现 `route_planner.py` / `service.py` / `route_models.py` | PASS | 关账仅票 04；升格 G1-02/R4 须新 claim |
| CC-1 证伪 | 弱断言 | 覆盖：①overlay revision 与 ask 一致且进日志 ②overlay.enabled=false 不选 baostock ③setattr is_enabled=False 有 con 仍 READY（读 DB）④P-MACRO 无 overlay→DISABLED_SOURCE ⑤A7：默认 source_disabled；overlay 后 missing_env。反证：overlay deny → baostock.enabled False / selected≠baostock（`DISCRIM_OK`） | `uv run pytest -q tests/test_route_planner_activation.py tests/test_platform_source_matrix.py::test_qmtXqshareMissingEnvNotSchedulable`；手工 deny overlay 脚本 | PASS | 再只读内存 is_enabled 或吞掉 overlay deny → 上述测/反证必须红 |
| CC-2 验真 | 权威要合成，实现只透传 | 原子：有 con 问开关→capability→platform；`overlay_revision` 在 plan/payload/SCHEMA_KEYS；stderr 含 correlation/run_id、reason_code、revision；`QMD_SOURCE_POLICY_TELEMETRY` 可关；无新依赖。无 con 回落内存属 ponytail，**不**作产品入口完成证据（T01-F07→06+07） | 测 + `event_payload` SCHEMA_KEYS；P-MACRO 脚本 DISABLED | PASS | 若声称「无 con 亦正式 SSOT」→ FAIL |
| CC-3 同路 | preview READY fetch DENIED | `fetch`/`preview_route` 均 `plan(..., con=)`。同 con+同 overlay → 同 status/revision。E-INC/CLI 仍 ESR（范围外票 06/07）；本票未新增生产 ESR | Grep `backend/app`：ESR 仍在 ops/cli（预存）；`service.py` 透传 con | PASS | 若声称「增量 CLI 已同路」→ FAIL |
| CC-4 验档 | sandbox 升格产品启用 | 证据分档：product_default 无 overlay 时 P-MACRO DISABLED；sandbox overlay 仅隔离库。日志未标 live product-enabled | P-MACRO 脚本；overlay reason 含 `[sandbox]` | PASS | 禁止用 sandbox READY 声称产品默认已开宏源 |
| CC-5 对表 | 失败吞成 READY | 形：字段附加不改义；义：先开关再安检；行为：deny overlay 阻挡该源；效果：revision 可观察。A7 旧期望已本阶段改断言对齐 ADR-018 | A7 测绿；deny 反证 | PASS | 再期望「未 overlay 先 missing_env」→ 与 ADR 冲突须 FAIL |
| CC-6 清债 | 能修却登记 | 本阶段修：F05-B `seed_activation_base`；A7 断言；emit 简化。严格后置：F05-A 余 E-INC/acceptance→**票 06/07**；F07 无 con 回落→**06+07 后**。均登记 `docs/quality/待修复清单.md`，**不支撑**本 claim 以外对象 | findings + 待修复清单 | PASS | 后置项不得用来声称 G1-02/全量绿 CLOSED |
| CC-7 守闸 | 隐瞒 ESR 仍在 | 诚实未完成：生产 ESR（ops/cli）、4a/4b、G1-02 整包、R4、撤销管理 CLI | Grep 生产 ESR 清单；HANDOFF 下一刀 06∥07 | PASS | CC-7 PASS≠G1-02 完成 |

### 对象 E · 票 05 E-TEST 夹具 overlay 治理

| CC | 具体场景示范 | 本对象运行事实 | 证据 / 反证 | Verdict | 闭环控制 |
|---|---|---|---|---|---|
| CC-0 对靶 | 只改注释 | 用户要：E-TEST 隔离根正规 overlay→正式入口；删除 setattr/强制 platform 作关账证据；生产 rg 可剩 06/07 清单。交付=`enable_source_route` 写 overlay+sync；etest 禁撬门字样；本票未新增生产 ESR | 票 05 AC；`service_path_support.py`；`test_etest_overlay_governance.py` | PASS | 关账仅票 05 |
| CC-1 证伪 | 静态测永远绿 | 覆盖：①helper 含 `write_activation_overlay`/`enable_source_route` ②无 `object.__setattr__`/force_platform ③B 夹具 sync 后 service/orchestrator 绿。反证：去掉 overlay 写路径则 etest/激活测红（由 04 测共证） | pytest etest + service/orchestrator 子集 | PASS | 再引入 setattr 撬门字样 → etest 必须红 |
| CC-2 验真 | 仍靠内存启用冒充 | 原子：隔离 DB migrate+sync+sandbox overlay；`activation_con`/`con=` 同库约定。测试副本上改 `_domain_roles`/`_raw` 为构造输入（T01-F06→票 06），**不作**「零内存构造」完成证据 | enable_source_route 实现；findings F06 | PASS | 若声称「夹具零内存字段写入」→ FAIL 至 F06 关 |
| CC-3 同路 | 夹具与正式入口分裂 | 夹具产出 planner/con 供正式 `plan`/`fetch`；不另开第二套启用权威 | fetch(con=) 与 plan(con=) | PASS | 夹具再强制 `_platform_allows` → FAIL |
| CC-4 验档 | 升格 product_default | sandbox reason 强制含 sandbox；未把 E-TEST READY 当产品默认启用证据 | write_activation_overlay sandbox 校验 | PASS | 同 CC-4 票 03/04 |
| CC-5 对表 | ADR 禁撬门，helper 仍 setattr | 形：无 `object.__setattr__`/force_platform；义：启用经 overlay；行为：seed_activation_base 对齐 ask 读库 | etest 静态面；Grep service_path_support | PASS | 再出现 `__setattr__(is_enabled` 于该 helper → FAIL |
| CC-6 清债 | 内存构造能本票删却挂起 | 本票可关：patch helper 形态与 B 夹具债。F06 内存 domain/capability 构造严格依赖票 06 迁完仍读内存的调用方 → **阶段外置票 06**。F05-A 生产 ESR 测→**06/07**。未新增生产 ESR | 待修复清单 T01-F06/F05-A | PASS | F06 不支撑「夹具已零构造」声称 |
| CC-7 守闸 | 假装生产 rg 已清零 | 诚实：`backend/app/ops/*` 与 `data_commands` 仍含 ESR/`_platform_allows=`；属票 06/07 显式清单，本票未新增 | Grep 生产路径命中表 | PASS | 全库生产清零须 06/07 后再 claim |

## Summary（本追加轮 · 票 04∥05）

- 首个决定性缺口：none（关账前已修 F05-B、A7、emit 简化；余债严格后置 06/07）
- 最终状态：`CLOSED`
- 声称结论：`permitted`（**仅**票 04 AC + 票 05 AC）
- 闭环控制：再验 = `uv run pytest -q tests/test_route_planner_activation.py tests/test_etest_overlay_governance.py tests/test_platform_source_matrix.py::test_qmtXqshareMissingEnvNotSchedulable` + service/orchestrator B 子集；overlay.enabled=false 须使 baostock 不可选；P-MACRO 无 overlay 须 DISABLED_SOURCE；**不得**将本记录当作 G1-02 / R4 / 生产 ESR 清零 / 全量 pytest 绿关账

## 测试资产治理（本追加轮）

| 资产 | 角色 | 处置 |
|---|---|---|
| `test_route_planner_activation.py`（revision/deny/setattr） | 核心 / 安检接线 | 保留 |
| `test_etest_overlay_governance.py` | tooling/policy（E-TEST 交付面） | 保留；**不得**单独证明生产启用 |
| `test_qmtXqshareMissingEnvNotSchedulable` | 核心 / 先开关再 missing_env | **已改写保留** |
| `seed_activation_base` / `enable_source_route` | 测试基础设施 | 保留；F06 跟踪内存构造收敛 |
| E-INC/acceptance 旧口径测 | 生产保证仍在，启用方式旧 | **阶段外置票 06/07**（不删测） |
