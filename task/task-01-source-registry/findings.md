# task-01-source-registry · Findings

> **planning-with-files 外部记忆** · 本票只记**问题**：未执行前发现的、或执行后仍开放/已关的债。  
> **不记：** 执行时临时拍板的方案取舍 → [`note.md`](note.md)。  
> 全局索引：`task-19-phase1-gate/PHASE1_COMPLETION_INVENTORY.md`

## Requirements

- R4 成品：数据源注册模块（Source Registry / Capability）
- 范围：源注册与 capability
- 权威：见 `README.md` → **权威文件**（`**/design/**` only）

## Research Findings

- 2026-07-11：完整的权威倒查、正式入口复现、反证和 CC-0～CC-7 结论，以 [completion-check-audit.md](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:1) 为唯一详细记录；本文件只保留可执行的短台账与审计后新增发现。
- task-19 F-15 经核验属 Phase-1 的 production-live 决议，不是当前 task-01 design 的已审阅变更；当前权威 YAML 仍规定 `macro_series` 默认禁用，因此未迁入。F-16 的 Tier A 启用清单当前确实缺失，但它是 Phase-1 运营治理要求、非本票 design 的原子交付，也未迁入。F-17 的大量默认禁用与权威一致，非缺陷。
- 2026-07-11 G1-01：正式入口与 OVERRIDE 消费者全量见 [g1-01-wiring-inventory.md](g1-01-wiring-inventory.md)。新增运行时事实：YAML `validation` 多源列表在 `_normalize_validation_source` 只保留首项（→ G1-03）；无 per-domain 回补缓冲天数字面量（ADR-017 规则足够，→ G1-07）。
- 2026-07-11 G1-01 补缺：`sync_to_db` 调用方补登 `qmd-init-db --sync-registry`（E-REG-03）、`DataSyncOrchestrator.bootstrap(sync_registry=True)`（E-REG-04，当前仅测试调用但仍可写）、`ensure_isolated_db`（E-ACC-ISO-01，gate_live only）。
- 2026-07-11 G1-01 Plan 复审：首版清单遗漏 `qmd-init-db --sync-registry` 与 `DataSyncOrchestrator.bootstrap(sync_registry=True)` 两个 `SourceRegistry.sync_to_db` 调用方；因此 `PLAN-OPEN`，不得进入 RED。完整 CC-0～CC-7 记录见 [completion-check-plan-g1-01.md](completion-check-plan-g1-01.md)。
- 2026-07-11 G1-02 票 04/05 接线后：全量 pytest ≈20 FAIL，共性 `source_policy_denied` + `source_disabled_by_default` + `overlay_revision=""`。判定轴与明细见下方 **开放项** T01-F05-A / T01-F05-B（已并入本文件，不另立分类稿）。
- 2026-07-12：对票 01–05 的提交基线 `0cad574f` 做金融数据策略评审（不含票 06/07 的未提交改动）。内存 DuckDB 反证：已写 `fred/macro_series/fetch_macro_series` overlay 仍为 `DISABLED_SOURCE`；未声明 operation 却为 `READY/baostock`。完整评审结论由本轮会话报告；可执行缺口列为 T01-F08～F12。

## 审计索引（2026-07-11）

| Findings 条目 | 详细审计记录 | 去重规则 |
|---|---|---|
| T01-F01 | [CC-2 验真](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:18) | capability 成品性、运行时证据与闭环条件只在审计记录展开。 |
| T01-F03 | [CC-1 证伪](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:17)、[CC-3 同路](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:19)、[CC-4～CC-7](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:20) | 入口覆盖、档位、权威偏离与技术债只在审计记录展开。 |
| T01-F04 | [Plan CC-3/CC-4](completion-check-plan-g1-01.md) | G1-01 入口盘点缺口只在本轮 Plan 审计记录展开。 |
| T01-F02 | 无（审计后新增） | 保留本条的当前配置与 RoutePlan 复现事实。 |
| T01-D01 | [CC-7 守闸](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:23) | 保留“按设计”的结论；入口绕过的反证以审计记录为准。 |

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| [ADR-017](/C:/Users/Guang/Desktop/quant-monitor-desk/docs/decisions/design/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md:1)（Accepted） | 用户已确认动态启用覆盖层、按领域自动降级、来源/质量独立标签、连续监控、回补与异常归档生命周期；已同步至索引 design 与共享契约，后续实现必须遵守。 |
| [ADR-018](../../docs/decisions/design/ADR-018-enable-seam-two-layer-and-fred-merge-gate.md)（Accepted） | 两层接缝：先问开关（overlay/DB）再安检；禁内存撬门；测试仅隔离根正规 overlay；FRED 启用与通用路径合并有硬门槛。 |

## 开放项（ledger）

| ID | 现象 | 标签 | disposition | 证据 |
|----|------|------|-------------|------|
| T01-F03 | 启用 SSOT 入口债：票 01–07 Execute CLOSED；**4a/4b 生产 ESR 撬门已清**（无 `def enabled_*_source_registry`）；**余 4x（票 08 bridge）未清** | enable policy / 跨模块依赖 | 待修复（**仅余 4x bridge → 票 08**） | 2026-07-12 CC 对象 F/G CLOSED；hygiene `--strict` OK；测试已用 `load_plain_source_registry`；≠ F03 整包 / ≠ G1-02 |
| T01-F06 | `tests/service_path_support.enable_source_route` 仍改测试副本 `_sources` / `_domain_roles` / capability `_raw`（**生产包已无**；正式路径改用 `build_activation_route_planner` + `preferred_primary_source_id`） | E-TEST 夹具债 | 阶段外置（**仍开放 → 票 08 后夹具零构造切片**） | 2026-07-12：内存撬门迁出 `backend/app/`；**不得**声称「夹具零内存构造」直至删 tests 侧构造；登记：待修复清单 + ROADMAP |
| T01-F07 | `plan(con=None)` 仍回落 YAML 内存 `is_enabled` | 启用 SSOT 缺口 | 阶段外置（**仍开放 → 票 08 后删回落切片**） | `route_planner._activation_allows` 无 con 分支仍在；**未删**；登记：待修复清单 + ROADMAP |
| T01-F08 | RoutePlanner 只检查 capability 的 source/domain，不检查 operation；未声明 operation 可 READY | capability / 路由正确性 | 阶段外置（**→ 票 09 前纠正切片**） | `is_capability_declared(source, domain)` 仍无 operation；登记：待修复清单 + ROADMAP |
| T01-F09 | （发现时）overlay 已允许后，`domain_enabled_by_default=false` 仍强制 `DISABLED_SOURCE` | activation overlay | **代码已改、待独立复验关账**（**→ 票 09 证据前复验**；不得写已修复） | 实现：`plan` 在选中源有 overlay revision 时不再因域默认关否决 READY；**关账前须独立复现原反证** |
| T01-F10 | `write_activation_overlay(sandbox=True)` 只看 reason 文本，不验隔离根 / 已登记能力 | overlay 写入边界 | 阶段外置（**→ 管理员写 overlay 产品 CLI 前 / 票 09 前置**） | 未改 `activation_overlay` 边界校验；登记：待修复清单 + ROADMAP |
| T01-F11 | capability 加载器不校验 `frequency`/`fields`/`requires_auth` 类型与非空 | capability 契约 | 阶段外置（**→ 票 09 前纠正切片**；可与 F08 同包） | 加载器仍弱校验；登记：待修复清单 + ROADMAP |
| T01-F12 | `source_policy_denied.reason_code` 取首个 candidate skip，且缺 platform 字段 | 可观测性 | 阶段外置（**→ 票 09**） | emit 逻辑未按 RoutePlan 最终原因对齐；登记：待修复清单 + ROADMAP |
| T01-ENABLE-FRED-MERGE-001 | FRED 编排壳与通用宏路径双轨 | 合并门槛 | 阶段外置 → **票 10**（G1-08 前） | **票 06/07 不关**；见待修复清单 |

### T01-F05-A · node-id 清单（防遗漏 SSOT）

> **基线：** 2026-07-11 全量失败摘要（terminal `652051`，票 04/05 接线后、B/A7 修前）。  
> **处置：** A 类由票 **06/07** 迁 overlay；**禁止**恢复 ESR/`__setattr__` 保绿；**禁止**删测文件。  
> **本切片结论（严格）：** A1–A6 **pytest 已绿**（见下表）；**仅关闭「旧口径测红」债**；**≠** 票 06/07 Execute CLOSED、**≠** G1-02、**≠** R4。  
> **再验命令（2026-07-12）：**  
> - `uv run pytest -q -m "not slow and not network"` → exit 0  
> - A1–A6 定向：`uv run pytest -q tests/test_alpha_vantage_incremental_e2e.py tests/test_deribit_incremental_e2e.py tests/test_sec_edgar_incremental_e2e.py tests/test_mootdx_incremental_e2e.py tests/test_layer5_mootdx_bar_clean_e2e.py::test_mootdxBarClean_layer5Provenance_matchesSameRunBundle tests/test_qmd_ops_source_route_db_acceptance.py::test_qmdOps_acceptSourceRouteDb_allDocumentedSources_liveAuthorized_writesMatrixReport tests/test_source_route_db_acceptance_contract.py::test_sourceRouteDbAcceptance_fredMacroTracer_mockedLiveObservations_writesAndReadsClean` → exit 0

| 桶 | 票 | node-id | 状态（2026-07-12） |
|----|----|---------|-------------------|
| A1 | **06** | `tests/test_alpha_vantage_incremental_e2e.py::test_alphaVantageIncremental_replay_writesSecurityBar1d` | **pytest 绿**（overlay 夹具；≠ G1-02） |
| A1 | **06** | `tests/test_alpha_vantage_incremental_e2e.py::test_alphaVantageIncremental_repeatRun_noRowGrowth` | **pytest 绿** |
| A2 | **06** | `tests/test_deribit_incremental_e2e.py::test_deribitIncremental_replay_writesCryptoDerivativeClean` | **pytest 绿** |
| A2 | **06** | `tests/test_deribit_incremental_e2e.py::test_deribitIncremental_emptyResponse_whenWatermarkCurrent` | **pytest 绿** |
| A3 | **06** | `tests/test_sec_edgar_incremental_e2e.py::test_secEdgarIncremental_replay_writesUsDisclosureClean` | **pytest 绿** |
| A3 | **06** | `tests/test_sec_edgar_incremental_e2e.py::test_secEdgarIncremental_repeatRun_noRowGrowth` | **pytest 绿** |
| A3 | **06** | `tests/test_sec_edgar_incremental_e2e.py::test_secEdgarIncremental_emptyResponse_whenWatermarkCurrent` | **pytest 绿** |
| A4 | **06** | `tests/test_mootdx_incremental_e2e.py::test_mootdxIncremental_replay_writesSecurityBar1d` | **pytest 绿** |
| A4 | **06** | `tests/test_mootdx_incremental_e2e.py::test_mootdxIncremental_opsRun_writesSecurityBar1d` | **pytest 绿** |
| A4 | **06** | `tests/test_mootdx_incremental_e2e.py::test_mootdxIncremental_repeatRun_noRowGrowth` | **pytest 绿** |
| A4 | **06**/**07** | `tests/test_layer5_mootdx_bar_clean_e2e.py::test_mootdxBarClean_layer5Provenance_matchesSameRunBundle` | **pytest 绿**（含于 `test:quick`） |
| A5 | **07** | `tests/test_qmd_ops_source_route_db_acceptance.py::test_qmdOps_acceptSourceRouteDb_allDocumentedSources_liveAuthorized_writesMatrixReport` | **pytest 绿**（matrix live `route_planner=`） |
| A6 | **07** | `tests/test_source_route_db_acceptance_contract.py::test_sourceRouteDbAcceptance_fredMacroTracer_mockedLiveObservations_writesAndReadsClean` | **pytest 绿** |
| A7 | — | `tests/test_platform_source_matrix.py::test_qmtXqshareMissingEnvNotSchedulable` | **已关闭**（本阶段改断言） |
| B（曾红） | — | `tests/test_datasource_service.py::{test_serviceFetch_runtimeGateOrder,test_serviceWritesRoutePlanPayloadBeforeFetch,test_serviceGuardBlocked_emitsResourceGuardPausedRoutePlan,test_serviceFetch_recordsSourceOverrideQualityFlag}` | **已关闭**（`seed_activation_base`） |
| B（曾红） | — | `tests/test_datasource_route_grade_payload.py::test_dataSourceService_resourceGuardPausedRoutePlan_writesBlockedRouteGrade` | **已关闭** |
| B（曾红） | — | `tests/test_sync_orchestrator.py::test_plannedJobWritesRoutePlanBeforeFetching` | **已关闭** |

**说明：** 上表含 `@slow`/`network` 行时，「pytest 绿」指定向命令/本机复验；全量 CI 仍须再撞。**不得**把本表绿写成 G1-02 / R4 / Execute CLOSED。

### T01-F05 问题摘要（ledger，非方案）

| ID | 现象 | disposition |
|----|------|-------------|
| F05-A | 上表 A1–A6 node-id 旧口径红 | **已修复（仅测债）** → 见「已关闭」；≠ G1-02 |
| F05-B | baostock 等默认可启用源：空库未 sync → ask 拒 | **已修复**（见已关闭） |

## 已关闭 / 按设计

| ID | 摘要 | disposition | 证据 |
|----|------|-------------|------|
| T01-REV-L5-0607 | pragmatic L5：沙箱子串误放行、preferred 域外注入、bare-except、preview DRY、writer 锁、tmp 泄漏、测注入改写副本、artifact meta-test | **已修复** | 2026-07-12 清零；g1_02/sync/envelope + hygiene `--strict` |
| T01-D01 | 大量 `enabled_by_default: false` 是 fail-closed 设计：不得 mass-enable；缺授权、资格或配置时应返回 `DISABLED_SOURCE` / `USER_AUTH_REQUIRED` | 按设计 | `data_sources.md` 默认启用与 domain gating；`qmt_xqshare_setup.md` §3-4；详见审计索引 CC-7 |
| T01-F01 | capability 顶层 draft / implementation_gap 作放行依据 | 已修复 | 票 01 · `capability_registry._validate_capability_document`；YAML `status: active`；load 边界测试 |
| T01-F02 | macro_supplementary 默认启用但 validation_only Primary → VALIDATION_ONLY_BLOCKED | 已修复 | 票 02 · `_validate_domain_roles` + 三域失败关闭；默认路由 DISABLED_SOURCE |
| T01-F03-3A | 问开关三键→三字段 + `source_activation_overlay` 持久化 + 隔离根可测；禁 setattr 撬门 | 已修复（切片） | 票 03 · `completion-check-execute.md`；`tests/test_activation_overlay.py`；≠ G1-02 整包 |
| T01-F03-3B/3C | RoutePlanner/Service 接 ask；E-TEST overlay 夹具 | **已修复（票级 Execute CLOSED）** | 票 04/05 · `completion-check-execute.md` 对象 D/E；≠ G1-02 CLOSED |
| T01-F05-A | 票 04/05 后 A1–A6 旧口径测红；迁 overlay 后 pytest 绿 | **已修复（仅 A1–A6 测债）** | 2026-07-12 上表再验命令 exit 0；`test:quick` exit 0；**≠** 票 06/07 `/completion-check` Execute CLOSED；**≠** G1-02/R4 |
| T01-REV-0607-DEAD | `service_path_support` 三死 helper（迁 `incremental_route_activation` 后未删） | **已修复** | 2026-07-12 联审闭环删除；hygiene `--strict` OK |
| T01-F05-B | baostock 等 YAML 默认可启用源：`fetch(con=)` ask 读空库 | 已修复 | `tests/service_path_support.seed_activation_base`；service / route_grade / orchestrator 夹具 sync；6 passed |
| T01-F05-A7 | `test_qmtXqshareMissingEnvNotSchedulable` 仍期望旧 skip 顺序 | 已修复 | 先断言 `source_disabled`；overlay 打开后再断言 `missing_env` |
| T01-F04 | G1-01 入口清单曾漏 E-REG-03/04 等 | 已修复（清单） | `g1-01-wiring-inventory.md`；Plan r6 `PLAN-READY` |

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| 2026-07-11 testing-guidelines 复查票 01/02：`test_domainsEnabledByDefault_haveSchedulablePrimary` 读私有 `reg._domain_roles` | **已修**：改为读权威 YAML `domain_roles` 键 + 公开 `get_domain_roles` |
| 同复查：缺 op 字段三案挤在同一 test 循环 | **已修**：`@pytest.mark.parametrize` 一案一行为 |
| 阶段性代码混入正式路径？ | **无**：实现在 `backend/app/datasources/` + `specs/`；测试在 `tests/`；未新增 `phase-scripts` 需求 |
| 2026-07-11 票 04/05 后全量 pytest 红 | **问题**入 F05-A/B；**怎么分/怎么修**入 [note.md](note.md) |

## Resources

- `README.md` — 模块职责与权威/运行时文件
- `../TASK_PIPELINE_INDEX.md` — 流水线顺序
- [note.md](note.md) — 执行阶段现场裁定（计划未穷尽项）
- [completion-check-audit.md](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:1) — 2026-07-11 的独立 R4 审计与 CC-0～CC-7 判定

## Visual/Browser Findings

- （无则留空）

---
*每 2 次查看/搜索后更新本节，防止上下文丢失*
