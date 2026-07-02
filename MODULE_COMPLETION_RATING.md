# Module Completion Rating

> **Purpose:** operator-facing status snapshot for planning and audit only.  
> **Not a design authority:** design documents, architecture documents, contracts, and rule definitions describe the desired complete product shape. They should not be downgraded with implementation-status labels.  
> **Planning authority:** execution plans and task cards must use this file to avoid claiming a module is complete when only scaffold, staged fixture, or sandbox evidence exists.  
> **Evidence rule (Pass E):** **Rating 列只信可执行代码 + pytest/vitest**；已 CLOSED 任务卡 / Plan 产物 **不**自动抬升评级；子集竖切记 **Milestone** 列，不得写入 Rating 列。  
> **Reference adoption:** rating movements for R3FR batches must also satisfy `specs/contracts/reference_adoption_guardrails.yaml` (`license_gate`, max three batches per module).  
> **Machine index:** `specs/context/authority_graph.yaml`（v2，`module_ids` + `rating_index`）· `docs/generated/project_map.generated.md` · `PROJECT_IMPLEMENTATION_ROADMAP.md` §3 · §8.  
> **Last reconciled:** **2026-07-03 M-DATA-03 close** — 11/11 live acceptance exit 0 · `uv run pytest -q` exit 0；prior Pass E @ 2026-07-02 · `68f70206`。

---

## 0. Pass E 总览（2026-07-02）

| 维度                       | 结论                                                                                                                                |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **已 CLOSED 任务 vs 模块** | Wave 4 DCP-05..10 等任务 **子集 AC 已绿**；**G1/G2/G4/K1/K2 模块 Rating 仍 R3**；**G5 仍 R2**；无建模模块因 DCP 达 **R4**           |
| **mock/replay 天花板**     | C3 十一源 e2e 默认 mock/replay；**M-DATA-03** `tier_a_live_acceptance.py` 11/11 真网绿（诚实 R4）；Layer clean e2e 多为 tmp DB seed |
| **production_live**        | L2/L3/L4 **拒绝** `production_live`；L3–L4 全链在 **M-G2/G4-FULL** + **M-PASS-01** 闭合                                             |
| **Round4 产品面**          | I1–I8 除 I3 壳外 **R0–R1**；B04 未开工                                                                                              |
| **PASS 前硬门禁**          | **M-PASS-01**（§6.1.1）；非「Wave 4 建模已完工」                                                                                    |

### 0.1 评级分布（51 Module ID）

| Rating | 数量 | 代表模块                                   |
| ------ | ---- | ------------------------------------------ |
| R0     | 5    | D3, E7, I2, I4, I5, I6                     |
| R1     | 9    | A6, E6, H1, I1, I7, I8, J2, J3, J6, J7     |
| R2     | 3    | A7, C4, G5, J4                             |
| R3     | 18   | A1–A5, B2–B3, C1, G1–G4, G6, J1, J5, K1–K3 |
| R4     | 9    | B1, C2, C3, D1, E1–E2, E4, F0              |
| R5     | 1    | E5                                         |
| R6     | 0    | —                                          |

---

## 1. Rating scale

| Level                               | Meaning                                                                                                                                                           | Can be called complete?         |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| `R0_NOT_STARTED`                    | No meaningful runtime implementation beyond placeholder files or planning docs.                                                                                   | No                              |
| `R1_SCAFFOLD`                       | API/module skeleton, contracts, or placeholders exist but no useful executable vertical slice.                                                                    | No                              |
| `R2_MINIMAL_VERTICAL_SLICE`         | A bounded end-to-end slice works with tests, real module boundaries, and no fake success claims. This is the minimum acceptable first implementation batch.       | No, only minimal slice complete |
| `R3_STAGED_FIXTURE_CLOSED`          | The module runs against staged fixtures with validation, lineage/evidence, and negative tests.                                                                    | No, staged implementation only  |
| `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | The module runs against bounded sandbox real-data/evidence or sandbox clean-write rehearsal with explicit caps.                                                   | No, sandbox only                |
| `R5_LIMITED_PRODUCTION_ENTRY`       | Explicitly approved, capped production entry exists with before/after proof, rollback, and regression tests.                                                      | Production-limited only         |
| `R6_FULL_PRODUCTION_STABLE`         | Stable production path, complete target-domain behavior, operational runbooks, monitoring, regression suite, and no open blocker for the module's promised scope. | Yes                             |

### 1.1 Milestone vs Rating（Pass E 规则）

| 列              | 含义                                        | 禁止                        |
| --------------- | ------------------------------------------- | --------------------------- |
| **Rating**      | 模块**当前**在量表上的级别（全声明 scope）  | 用任务 CLOSED 直接改 Rating |
| **Milestone**   | 已交付的**有界竖切**（可引用 DCP/R3H ID）   | 把子集写成「模块已达 R4」   |
| **Close round** | 模块核心能力预计在哪一轮 **R6 发布确认**    | 与 Rating 混为一谈          |
| **批/3**        | 向 R6 已消耗的实现批次（非 Trellis 任务数） | 用审计 finding 数充批次     |

**子集达标不抬升整模块的典型例：** DCP-06 五轴 P0 clean read → Milestone ✅；G1 Rating 仍 **R3**（ingestion 默认 staged；无 sync→clean→Layer1 集成测）。

---

## 2. Anti-overengineering completion rule

For every module or major feature after this file lands:

1. The **first implementation batch** must deliver at least `R2_MINIMAL_VERTICAL_SLICE`; a pure shell, placeholder, single-field guard, or isolated registry note is not enough.
2. The module must reach `R6_FULL_PRODUCTION_STABLE` in **no more than three implementation batches** for the declared scope.
3. Existing partially implemented modules must use their **next implementation batch** to close the main promised scope directly, unless a written ADR proves that the promise was too broad and narrows the module boundary.
4. Future task cards must distinguish:
   - first vertical slice;
   - production-complete closure;
   - hardening/regression closure.
5. Repeated micro-slices such as “add one metric”, “add one flag”, “add one registry note”, or “add one narrow test” without moving the module to the next rating level are treated as overengineering unless they are part of the same batch PR.
6. Every **new** task card must cite **Module ID** (§3) and which **rating movement** it will deliver — if only a milestone, say so explicitly.

**Batch column (`批/3`):** implementation batches already spent toward `R6` for the **declared module scope** (not Trellis task count).

---

## 3. Canonical module inventory

`docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` remains a coverage map only — **not** a work order. 通俗说：**地图不是工单；任务卡才是工单。**

> **列说明：** Evidence 仅列**可复验**代码/测试路径；`（窄）` = 能力存在但 scope 明显小于设计权威。

### 3.A Platform foundation

| ID  | Module                                   | Design authority                                                 | Rating                      | 批/3 | Milestone（子集，非 Rating）   | Close round | Evidence（Pass E @ `68f70206`）                                                                                      | 活票 / 归属（§1.8）                            |
| --- | ---------------------------------------- | ---------------------------------------------------------------- | --------------------------- | ---- | ------------------------------ | ----------- | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| A1  | Project scaffold / config / test harness | `GLOBAL_TESTING_POLICY.md`, `tests/test_catalog.yaml`            | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | loop/catalog gates             | R5          | `tests/test_loop_engineering_flow.py` · `test_project_scaffold.py` · `test_catalog.yaml`                             | Batch05                                        |
| A2  | DuckDB schema / migration foundation     | `db_platform`, `docs/schema/MIGRATION_COVERAGE.md`               | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | mig 001–015 incl. DCP-05       | R5          | `backend/app/db/migrations/` · `tests/test_schema_migration.py` · `test_migration_coverage.py`                       | Batch05                                        |
| A3  | Storage / evidence primitives            | `core_platform`, `docs/modules/local_file_system.md`             | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | R3H-08 staging · DCP-10 bridge | R3→R5       | `backend/app/storage/raw_store.py` · `tests/test_raw_store.py` · `tests/test_layer5_provenance_bridge.py`            | **M-G5-FULL** + **M-PASS-01**                  |
| A4  | ResourceGuard / performance budget       | `core_platform`, `docs/ops/performance_limits.md`                | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | DCP-06 panel caps              | R3→R5       | `backend/app/core/resource_guard.py` · `tests/test_resource_guard.py` · `test_layer1_five_axis_panel_clean_smoke.py` | **M-G1-03** / **M-PASS-01**                    |
| A5  | Snapshot lineage kernel                  | `core_platform`, `snapshot_lineage_contract.yaml`                | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | kernel unit tests              | R4→R5       | `backend/app/core/snapshot_lineage.py` · `tests/test_snapshot_lineage_kernel.py`                                     | **M-G1-03**                                    |
| A6  | Spec migrator (offline registry tool)    | `spec_migrator_contract.yaml`                                    | `R1_SCAFFOLD`               | 0/3  | —                              | Batch6→R5   | `specs/contracts/spec_migrator_contract.yaml`；**无** `tests/test_spec_migrator.py`                                  | 实现 dry-run migrator 或 ADR-wont-fix          |
| A7  | Platform matrix + dependency extras      | `platform_source_matrix.yaml`, `dependency_extras_contract.yaml` | `R2_MINIMAL_VERTICAL_SLICE` | 1/3  | contract tests                 | R5          | `tests/test_dependency_extras_contract.py` · `tests/test_platform_source_matrix.py`                                  | Batch05 release manifest 写入 platform posture |

### 3.B Validation and write path

| ID  | Module                          | Design authority                                | Rating                              | 批/3 | Milestone                                             | Close round | Evidence                                                                                                                                                                                | 活票 / 归属（§1.8）                                         |
| --- | ------------------------------- | ----------------------------------------------- | ----------------------------------- | ---- | ----------------------------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| B1  | WriteManager + DbValidationGate | `validators`, `docs/modules/write_manager.md`   | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3H-06 upsert · R3G sandbox promote                   | R3→R5       | `write_manager.py` · `tests/test_write_manager.py` · `test_round3g_limited_production_clean_write.py`（**仅** `.audit-sandbox`；`test_PromoteRunner_refusesCanonicalProductionDbPath`） | Batch05 main-DB posture smoke 或 manifest 声明 sandbox-only |
| B2  | Data quality validator          | `validators`, `data_quality_rules.yaml`         | `R3_STAGED_FIXTURE_CLOSED`          | 2/3  | R3H-08 profiles · DCP-03 smoke · M-DATA-03 partial F0 | R3→R5       | `validators/data_quality.py` · `test_data_quality_validator.py` · `test_incremental_post_write_inspect.py` · acceptance partial F0（bar/cninfo/fred profiles）                          | **M-DATA-03** 11/11 live 旁路验证                           |
| B3  | Source conflict validator       | `validators`, `data_validation_and_conflict.md` | `R3_STAGED_FIXTURE_CLOSED`          | 2/3  | R3H-08 live outcomes                                  | R3          | `validators/source_conflict.py` · `tests/test_source_conflict_validator.py`                                                                                                             | **M-PASS-01**                                               |

### 3.C Data sources and routing

| ID  | Module                                       | Design authority                           | Rating                              | 批/3 | Milestone                                             | Close round | Evidence                                                                                                                                                   | 活票 / 归属（§1.8）             |
| --- | -------------------------------------------- | ------------------------------------------ | ----------------------------------- | ---- | ----------------------------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| C1  | Source registry / capability / route planner | `datasources`, `source_route_plan.md`      | `R3_STAGED_FIXTURE_CLOSED`          | 2/3  | R3H-01～04 reconcile                                  | R3          | `source_registry.yaml` · `tests/test_source_registry.py` · `test_tierA_incremental_registry.py`                                                            | **M-PASS-01**                   |
| C2  | DataSourceService facade                     | `datasources`, `datasource_service.md`     | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3H-10 bypass guards                                  | R3→R4       | `datasources/service.py` · `tests/test_datasource_service.py` · `test_sync_orchestrator.py`（R3H-10 / R3Y-SYNC）                                           | 历史 CLOSED；**M-PASS-01** 审计 |
| C3  | Vendor adapters / provider fetch ports       | `datasources`, `fetch_ports/*`             | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3H-08 port live gate · DCP-05 · M-DATA-03 11/11 live | R3→R4       | `fetch_ports/*` · 11× `test_*_incremental_e2e.py`（默认 mock/replay）· `tier_a_live_acceptance.py` **11/11 exit 0**（`l4-tier-a-live-accept-evidence.md`） | **M-DATA-03** 诚实 R4           |
| C4  | Provider catalog / auth-license gate         | `provider_catalog.yaml`, `license_gate.py` | `R2_MINIMAL_VERTICAL_SLICE`         | 2/3  | R3FR-05 catalog tests                                 | R3→R5       | `tests/test_provider_catalog.py` · `license_gate.py`                                                                                                       | **M-PASS-01**                   |

### 3.D Sync, scheduling, and task reliability

| ID  | Module                         | Design authority                                 | Rating                              | 批/3    | Milestone                                       | Close round | Evidence                                                                                                        | 活票 / 归属（§1.8）                                 |
| --- | ------------------------------ | ------------------------------------------------ | ----------------------------------- | ------- | ----------------------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| D1  | Data sync orchestration        | `sync_orchestrator`, `data_sync_orchestrator.md` | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | **3/3** | DCP-01/02/05/09 · M-DATA-03 11/11 live dispatch | R3→R5       | `sync/orchestrator.py` · `tier_a_live_incremental_dispatch.py` · 11/11 live acceptance exit 0 · incremental e2e | **M-DATA-03** 真网验收 **已绿**                     |
| D2  | Task idempotency / retry / DLQ | `docs/ops/idempotency_retry_dlq_policy.md`       | `R1_SCAFFOLD`                       | 0/3     | —                                               | Batch6      | 政策文档 only；**无** `idempotency_key` runtime                                                                 | Batch6 store/replay 或 ADR 收窄为 write upsert 足够 |
| D3  | Sync scheduler / cron product  | `data_sync_orchestrator.md` §CLI                 | `R0_NOT_STARTED`                    | 0/3     | —                                               | R4→R5       | 无 scheduler 模块；仅 `qmd data` 手动触发                                                                       | R4：scheduler shell 调 D1 同一 entrypoint           |
| D4  | Source health snapshot writer  | `ADR-024`, `source_health_writer.py`             | `R2_MINIMAL_VERTICAL_SLICE`         | 1/3     | isolated writer test                            | Batch6      | `ops/source_health_writer.py` · `tests/test_source_health_snapshot.py`（`:memory:`）                            | Batch6 production migration                         |

### 3.E Ops, CLI, and sandbox entry

| ID  | Module                                         | Design authority                  | Rating                              | 批/3 | Milestone                                   | Close round | Evidence                                                                                                  | 活票 / 归属（§1.8）                 |
| --- | ---------------------------------------------- | --------------------------------- | ----------------------------------- | ---- | ------------------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| E1  | `qmd data` CLI                                 | `docs/ops/data_health_cli.md`     | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | DCP-01/02/05 router · M-DATA-03 ops runners | R3→R5       | `cli/data_commands.py` · `tier_a_live_incremental_dispatch.py` · 11/11 live acceptance（ops runner 路径） | **M-DATA-03** 诚实 R4               |
| E2  | Ops DB inspect + verification matrix           | `docs/ops/db_inspect_cli.md`      | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | DCP-03 · M-DATA-03 E2 per-source inspect    | R3→R5       | `ops/db_inspector.py` · acceptance 11/11 inspect 非 FAIL · `test_tier_a_live_dispatch.py` 集成            | **M-DATA-03** 诚实 R4               |
| E3  | Production gate + equivalent smoke             | `scripts/production_gate.py`      | `R2_MINIMAL_VERTICAL_SLICE`         | 1/3  | gate scripts                                | R5          | `tests/test_production_gate.py` · `test_production_equivalent_smoke_budget.py`                            | Batch05 integration smoke owner     |
| E4  | Live / staged pilot runners                    | `production_live_pilot_policy.md` | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3H-08 ProductLiveGate                      | R3          | `ops/live_pilot*.py` · `product_live_gate.py` · `tests/test_staged_pilot.py`                              | **M-PASS-01**                       |
| E5  | Sandbox clean write / limited production entry | `ops/sandbox_clean_write`         | `R5_LIMITED_PRODUCTION_ENTRY`       | 3/3  | R3G quadruple-lock promote                  | R5 confirm  | `limited_production_entry.py` · `tests/test_round3g_limited_production_clean_write.py`                    | Batch05 manifest 记录 write posture |
| E6  | Backup / recovery / disk thresholds            | `backup_and_recovery.md`          | `R1_SCAFFOLD`                       | 1/3  | —                                           | R5          | ops 文档；无 automated backup runner                                                                      | Batch05 runbook + optional smoke    |
| E7  | Ops report CLI                                 | `docs/ops/ops_report_cli.md`      | `R0_NOT_STARTED`                    | 0/3  | —                                           | R4→R5       | design only                                                                                               | B04_04 或 ADR defer                 |

### 3.F Data health (operator profiles)

| ID  | Module             | Design authority           | Rating                                         | 批/3 | Milestone                                   | Close round | Evidence                                                                                                             | 活票 / 归属（§1.8）      |
| --- | ------------------ | -------------------------- | ---------------------------------------------- | ---- | ------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| F0  | Data health engine | `ops/data_health_profiles` | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` **（窄）** | 2/3  | DCP-03 · M-DATA-03 partial F0 in acceptance | R3→R5       | `data_health_profiles/` · acceptance `_run_f0_data_health`（SKIP/FAIL 边界 pytest）· 完整 CLI 矩阵 → M-PASS ponytail | **M-DATA-03** partial F0 |

### 3.G Modeling layers (Layer1–5) — Pass E 重灾区

| ID  | Module                     | Design authority                               | Rating                          | 批/3 | Milestone（≠ Rating）                                           | Close round | Evidence                                                                                                                                     | 活票 / 归属（§1.8）         |
| --- | -------------------------- | ---------------------------------------------- | ------------------------------- | ---- | --------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| G1  | Layer1 axes / regime panel | `layer1_axes`, `layer1_global_regime_panel.md` | **`R3_STAGED_FIXTURE_CLOSED`**  | 2/3  | **DCP-06**：五轴 P0 clean **读** e2e（tmp seed）                | R4→R5       | `clean_observation_reader.py` · `tests/test_layer1_*_clean_e2e.py` · `test_layer1_five_axis_panel_clean_smoke.py`；ingestion 默认 **staged** | **M-G1-03**                 |
| G2  | Layer2 cross-asset sensors | `layer2_cross_asset_sensor.md`                 | **`R3_STAGED_FIXTURE_CLOSED`**  | 2/3  | **DCP-07**：**仅 L2-VIX** clean replay                          | R4→R5       | `sensor_loader.py`（`production_clean_replay` + fred 白名单）· `tests/test_layer2_vix_clean_e2e.py`；设计九组资产 **未**覆盖                 | **M-G2-FULL**               |
| G3  | Layer3 industry chains     | `layer3_industry_shock_anchor.md`              | `R3_STAGED_FIXTURE_CLOSED`      | 1/3  | 021/022 staged snapshots                                        | R4+         | `loader.py` / `snapshot_builder.py` **仅** `staged_fixture_only` · `tests/test_layer3_*.py`                                                  | Round4 初（非 PASS 硬门禁） |
| G4  | Layer4 market structure    | `layer4_market_structure.md`                   | **`R3_STAGED_FIXTURE_CLOSED`**  | 2/3  | **DCP-08**：**仅 US_EQ** `tier_a_clean`                         | R4→R5       | `market_structure.py` · `tests/test_layer4_us_equity_clean_e2e.py`；CN_A 仍 staged                                                           | **M-G4-FULL**               |
| G5  | Layer5 evidence / security | `layer5_security_evidence.md`                  | **`R2_MINIMAL_VERTICAL_SLICE`** | 2/3  | **DCP-10**：mootdx bar→provenance（**唯一** sync→clean 全链测） | R4→R5       | `tests/test_layer5_mootdx_bar_clean_e2e.py` · `provenance.py`；foundation 测仍 `STAGED_PROVENANCE`                                           | **M-G5-FULL**               |
| G6  | Manual review staging      | `manual_review_staging.py`                     | `R3_STAGED_FIXTURE_CLOSED`      | 1/3  | R3H-08D live bundle（**不写 clean**）                           | R3          | `tests/test_no_clean_write_for_web_evidence.py` · kalshi/polymarket replay                                                                   | **M-PASS-01**               |

> **Pass E 说明：** 任务卡写「G\* `R3→R4`」= **下一批目标 / 子集里程碑**，**不是**本表 Rating 已达 R4。升到 R4 需 sandbox 真数据 rehearsal 或 clean-write 全链证明，且覆盖**声明 scope 主路径**——当前 Layer 模块未满足。

### 3.H ETL and cold storage

| ID  | Module                       | Design authority        | Rating        | 批/3 | Milestone | Close round | Evidence                           | 活票 / 归属（§1.8） |
| --- | ---------------------------- | ----------------------- | ------------- | ---- | --------- | ----------- | ---------------------------------- | ------------------- |
| H1  | ETL / Parquet archive bridge | `duckdb_and_parquet.md` | `R1_SCAFFOLD` | 1/3  | —         | Batch6→R5   | `backend/app/etl/__init__.py` stub | Batch6 sync→Parquet |

### 3.I Product surface (Round4 primary)

| ID  | Module                      | Design authority                | Rating           | 批/3 | Milestone           | Close round | Evidence                                                       | 活票 / 归属（§1.8）      |
| --- | --------------------------- | ------------------------------- | ---------------- | ---- | ------------------- | ----------- | -------------------------------------------------------------- | ------------------------ |
| I1  | FastAPI API backend         | `fastapi_backend.md`            | `R1_SCAFFOLD`    | 0/3  | `/health` only      | R4          | `main.py` GET `/health` · `tests/test_backend_smoke.py`        | B04_01 首个只读 API 竖切 |
| I2  | Agent runtime + policy      | `agent_module.md`               | `R0_NOT_STARTED` | 0/3  | —                   | R4          | `agents/__init__.py` only                                      | B04_02                   |
| I3  | Frontend dashboard          | `frontend_dashboard.md`         | `R1_SCAFFOLD`    | 1/3  | Vite shell          | R4          | `frontend/src/App.tsx` · `App.shell.test.tsx`；**无 API 绑定** | B04_03                   |
| I4  | Notifications / reports     | `notification_and_reports.md`   | `R0_NOT_STARTED` | 0/3  | —                   | R4          | `notifications/__init__.py` only                               | B04_04                   |
| I5  | Backtest / review runtime   | `backtest_and_review.md`        | `R0_NOT_STARTED` | 0/3  | planning tests only | R4          | contracts only；无 `backend/app/review/`                       | B04_05                   |
| I6  | Backtest / review metrics   | `backtest_metric_contract.yaml` | `R0_NOT_STARTED` | 0/3  | —                   | R4          | **Sub-scope of I5**                                            | 随 I5 闭合               |
| I7  | Review sandbox API          | `review_sandbox_contract.yaml`  | `R1_SCAFFOLD`    | 1/3  | contract            | R4          | contract only                                                  | B04_05 + B04_01          |
| I8  | Diagnostics API (read-only) | `diagnostics_api_contract.yaml` | `R1_SCAFFOLD`    | 0/3  | —                   | R4          | **零** `/api/diagnostics/*` 路由                               | B04_01 子集              |

### 3.J Governance, security, and deferred product modules

| ID  | Module                             | Design authority                     | Rating                      | 批/3 | Milestone             | Close round | Evidence                                                             | 活票 / 归属（§1.8）                  |
| --- | ---------------------------------- | ------------------------------------ | --------------------------- | ---- | --------------------- | ----------- | -------------------------------------------------------------------- | ------------------------------------ |
| J1  | Reference adoption governance      | `reference_adoption_guardrails.yaml` | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | R3FR-07 static guards | R5          | `tests/test_reference_adoption_guardrails.py`                        | Batch05：无 reference runtime import |
| J2  | No-action semantics guard          | `agent_module.md`                    | `R1_SCAFFOLD`               | 1/3  | static pattern tests  | R4          | guardrail tests only；无 agent runtime                               | B04_02 + B04_05                      |
| J3  | Release / security packaging       | Batch05 cards                        | `R1_SCAFFOLD`               | 0/3  | partial CI            | R5          | `test_production_gate.py` · `.github/workflows/ci.yml`               | B05-01..03 only                      |
| J4  | Docs / task entrypoint consistency | `MIGRATION_MAP.md`                   | `R2_MINIMAL_VERTICAL_SLICE` | 2/3  | docs index loop       | R5          | `tests/test_docs_specs_indexed.py` · `test_loop_engineering_flow.py` | Batch05 manifest alignment           |
| J5  | `web_search` live API (deferred)   | `R3H-WEB-SEARCH` ADR                 | `R3_STAGED_FIXTURE_CLOSED`  | 1/3  | mock port only        | Post-R4     | `web_search_evidence_port.py` · `tests/test_web_evidence_adapter.py` | **DEFERRED_POST_ROUND4**             |
| J6  | Log audit / structured ops logging | `log_audit_contract.yaml`            | `R1_SCAFFOLD`               | 0/3  | —                     | R5          | contract only；无 ndjson pipeline                                    | Batch05 observability 或 ADR         |
| J7  | User input privacy boundary        | `user_input_privacy_contract.yaml`   | `R1_SCAFFOLD`               | 0/3  | —                     | R4          | **无** `tests/test_privacy_contract.py`                              | 随 I2/I3 闭合                        |

### 3.K Model input governance (spec-only track)

| ID  | Module                            | Design authority                              | Rating                         | 批/3 | Milestone                                 | Close round | Evidence                                                                  | 活票 / 归属（§1.8）      |
| --- | --------------------------------- | --------------------------------------------- | ------------------------------ | ---- | ----------------------------------------- | ----------- | ------------------------------------------------------------------------- | ------------------------ |
| K1  | Model input whitelist / readiness | `specs/model_inputs/**`                       | **`R3_STAGED_FIXTURE_CLOSED`** | 2/3  | DCP-06：**5/11** 行 `clean_replay_proven` | R4→R5       | `layer1_source_whitelist.yaml` · `test_layer1_p0_dcp06_cleanReplayProven` | **M-G1-03**（G1 子范围） |
| K2  | Layer1 five-axis indicator specs  | `specs/layer1_axes/restructured_axes_v1_1/**` | **`R3_STAGED_FIXTURE_CLOSED`** | 1/3  | DCP-06：每轴 1 P0 测                      | R4→R5       | 五轴 YAML + G1 clean e2e；**非**全指标 catalog                            | **M-G1-03**（G1 子范围） |
| K3  | Layer3 chain registries           | `specs/layer3_global_industry_chains/**`      | `R3_STAGED_FIXTURE_CLOSED`     | 1/3  | registry docs                             | R4+         | JSON/YAML registries；loader 仍 staged bundle                             | **Sub-scope of G3**      |

---

## 3.1 Design doc aliases (not separate completion tracks)

| Doc file                                                | Parent ID | Note                             |
| ------------------------------------------------------- | --------- | -------------------------------- |
| `fastapi_and_frontend.md`                               | I1, I3    | compat index only                |
| `data_validation_write_concurrency.md`                  | B1–B3     | compat index only                |
| `source_route_plan.md`, `source_capability_registry.md` | C1        | Round2.6 split of C1             |
| `datasource_service.md`                                 | C2        |                                  |
| `qmt_xtdata_adapter.md`                                 | C3        | single-source deep spec          |
| `backtest_review_lifecycle.md`                          | I5        | lifecycle contract for I5        |
| `README.md` (modules index)                             | —         | navigation only                  |
| `docs/api/fastapi_routes.md`                            | I1, I8    | route catalog for Round4         |
| `docs/api/agent_tool_contracts.md`                      | I2        | agent tool surface               |
| `docs/architecture/05_module_map.md`                    | —         | historical; **superseded by §3** |
| `specs/layer1_axes/restructured_axes_v1_1/**`           | K2 → G1   | per-axis specs                   |
| `specs/layer3_global_industry_chains/**`                | K3 → G3   | chain registries                 |
| `specs/model_inputs/*.yaml`                             | K1        | whitelist rows                   |
| `specs/frontend/page_contracts.yaml`                    | I3        | page/data-shape contract         |

---

## 3.2 Coverage verification log

### Pass E — 2026-07-02（四路 agent 代码审计 @ `68f70206`）

| 轨  | 范围                    | 方法          | 关键结论                                             |
| --- | ----------------------- | ------------- | ---------------------------------------------------- |
| E1  | A1–A7, B1–B3, C1–C4, J5 | 代码 + pytest | C3 11源 e2e 全 replay；B1 无主库写；A3 staged 为主   |
| E2  | D1–D4, E1–E7, F0, H1    | 代码 + pytest | D1 **3/3** 批；E2/F0 **窄**；E5 唯一 R5              |
| E3  | G1–G6, K1–K3            | 代码 + pytest | **无** G\* 模块级 R4；G5 mootdx 唯一 sync→clean 全链 |
| E4  | I1–I8, J1–J7            | 代码 + vitest | Round4 **未开工**；与旧表一致                        |

**Wave 4 子集里程碑（已代码验证，不抬升整模块 Rating）：**

| 规划 ID   | Milestone                                   | 代码锚点                                                    |
| --------- | ------------------------------------------- | ----------------------------------------------------------- |
| R3-DCP-05 | 11 源 incremental replay + clean upsert e2e | `tests/test_*_incremental_e2e.py` ×11                       |
| R3-DCP-06 | L1 五轴 P0 clean read                       | `tests/test_layer1_*_clean_e2e.py`                          |
| R3-DCP-07 | L2-VIX only（**≠ G2 成品**）                | `tests/test_layer2_vix_clean_e2e.py` → **M-G2-FULL**        |
| R3-DCP-08 | US_EQ only（**≠ G4 成品**）                 | `tests/test_layer4_us_equity_clean_e2e.py` → **M-G4-FULL**  |
| R3-DCP-09 | bounded backfill + nightly CI               | `tests/test_qmd_data_backfill_cli.py`                       |
| R3-DCP-10 | mootdx→Layer5 provenance（**≠ G5 成品**）   | `tests/test_layer5_mootdx_bar_clean_e2e.py` → **M-G5-FULL** |

### Pass D — 2026-07-01（Wave 1–3 @ `893e6e2b`）

（历史记录保留；Pass E 已覆盖 Wave 4 并修正 G/D 批/3。）

### Pass C — 2026-06-29c（`authority_graph.yaml` v2 ↔ §3）

（`rating_index` 51 ID；22 graph nodes — 结构未变，Pass E 更新 **Rating 值** 与 Evidence 列。）

### Pass B — 2026-06-29b（`specs/` + `docs/` 映射）

（契约→模块映射仍有效；见历史表。）

---

## 3.3 Known stale artifacts（非本文件 SSOT）

| Artifact                                          | 归档 / 现行路径                                                                                                                           | 读法                                                                        |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `R3_DCP_TO_ISSUES_INDEX.md`                       | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/` | **只读** CLOSED 证据；下一入口 → **M-PASS-01** / 路线图 §3.7                |
| `R3H_PASS_EXECUTION_PLAN.md`                      | 同上目录（stub）· 全文 → `R3H_PASS_EXECUTION_PLAN.archived-20260702.md`                                                                   | **已归档** @ 2026-07-02；活规划 → 根 `PROJECT_IMPLEMENTATION_ROADMAP.md` §3 |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md`              | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/`                                                                        | Round3 批次地图（历史）；非开工 SSOT                                        |
| `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` §3 | 同上 archive                                                                                                                              | 覆盖地图；R3G WriteManager 叙事过时 → 用 MCR §3 **B1/E5**                   |
| `project_map.generated.md`                        | `docs/generated/`                                                                                                                         | 需 `loop_maintain.py --fix`                                                 |
| `.trellis/tasks/07-02-wave4-*`                    | `.trellis/tasks/archive/`                                                                                                                 | merge 后 Trellis 已批量归档                                                 |

---

## 4. Planning consequences（用户裁决 @ 2026-07-02 对齐）

- Design/contract files remain **complete-product targets**; Rating 列跟踪 **已证明** 的实现 scope（§0.3.2）。
- **PASS** = `PROJECT_IMPLEMENTATION_ROADMAP.md` **§6.1 v2** + MCR 无 R3 假完成（§0.3.1）；**禁止**任务 CLOSED / tmp seed / 全 mock e2e 冒充。
- **新票**须标明 Module ID、Rating 跃迁、设计权威路径；**milestone-only** 须在卡标题写明且不得隐含整模块升级。
- **模块完整落地：** G2/G4 等按 `docs/modules/` **成品 scope** — 单 **Plan→Execute** 流程内多切片，**统一** A1–A8（§0.3.2 · 路线图 §1.7）。
- **禁止**同一模块成品拆成多张独立完整流程任务；**禁止**「第二 P0 传感器」「8 源 CLI」等碎片化为新完整流程（见路线图 §1.7–§1.8）。
- **M-DATA-03：** 11 源真网硬要求；无资格源 → ADR + 占位 + 逻辑完整（§0.3.3）。
- **Round4 product：** I1–I7, J2 — **R0–R1**；须 **M-PASS-01** 后 B04 开工。
- **真链最低标准（活卡 AC）：** `sync incremental → clean → Layer` **同库** e2e；隔离库验收，不污染主库。

---

## 5. 后续规划入口（与路线图 §3 v2 对齐 · 非任务卡）

| 优先级 | 票 ID            | 模块                  | 预期 Rating / 里程碑                    |
| ------ | ---------------- | --------------------- | --------------------------------------- |
| **P0** | **M-DATA-03**    | C3,D1,E1,E2,F0        | 真网 scope R3→R4；开工前源资格 grill-me |
| **P0** | **M-G1-03**      | G1,K1,K2              | G1 R3→R4 完整五轴                       |
| **P1** | **M-G2-FULL**    | G2                    | 九组资产 R3→R4                          |
| **P1** | **M-G4-FULL**    | G4                    | 各 market_id R3→R4                      |
| **P1** | **M-G5-FULL**    | G5, A3                | G5 R2→R4 完整证据链                     |
| **P0** | **M-PASS-01**    | C1,C4,B3,G6,E4 + 门禁 | `PASS_ROUND4_REAL_DATA_READY`           |
| P3     | Round4 B04_01 起 | I1, I8                | R1→R2（PASS 后）                        |

**历史 Wave 5 `R3H-05-GATE`** 并入 **M-PASS-01**；旧 §5 P2「8 源 CLI」已由 **M-DATA-03 十一源** 取代。
