# Module Completion Rating

> **Purpose:** operator-facing status snapshot for planning and audit only.  
> **Not a design authority:** design documents, architecture documents, contracts, and rule definitions describe the desired complete product shape. They should not be downgraded with implementation-status labels.  
> **Planning authority:** execution plans and task cards must use this file to avoid claiming a module is complete when only scaffold, staged fixture, or partial-scope evidence exists — **未达 R4（声明 scope 能力真落地）不得称模块完成**。  
> **Evidence rule (Pass E):** **Rating 列只信可执行代码 + pytest/vitest**；已 CLOSED 任务卡 / Plan 产物 **不**自动抬升评级；子集竖切记 **Milestone** 列，不得写入 Rating 列。  
> **Reference adoption:** rating movements for R3FR batches must also satisfy `specs/contracts/reference_adoption_guardrails.yaml` (`license_gate`, max three batches per module).  
> **Machine index:** `specs/context/authority_graph.yaml` · `docs/generated/project_map.generated.md` · 活规划 → `PROJECT_IMPLEMENTATION_ROADMAP.md` §3。  
> **Last reconciled:** **2026-07-04** — 三批法则 Batch1→R4 · Batch2→R5 · Batch3→R6 · 活规划 → `PROJECT_IMPLEMENTATION_ROADMAP.md` §0.1 · §1.2 · §3

---

## 0. 评级快照（2026-07-04）

| 维度              | 结论                                                        |
| ----------------- | ----------------------------------------------------------- |
| **R6 可完整发布** | **0 / 51**                                                  |
| **R5 运维收尾**   | E5（1）· 余模块 R5 未关                                     |
| **R4 能力真落地** | B1, B2, C2, C3, D1, E1, E2, E4, F0（9）· 证明环境多为隔离库 |
| **R3 及以下**     | 41 · 声明 scope 能力/机制未完整落地                         |

### 0.1 分布明细（51 Module ID）

| Rating | 数量 | 代表模块                                       |
| ------ | ---- | ---------------------------------------------- |
| R0     | 6    | D3, E7, I2, I4, I5, I6                         |
| R1     | 12   | A6, D2, E6, H1, I1, I3, I7, I8, J2, J3, J6, J7 |
| R2     | 6    | A7, C4, D4, E3, G5, J4                         |
| R3     | 17   | A1–A5, B3, C1, G1–G4, G6, J1, J5, K1–K3        |
| R4     | 9    | B1, B2, C2, C3, D1, E1, E2, E4, F0             |
| R5     | 1    | E5                                             |
| R6     | 0    | —                                              |

---

## 1. Rating scale

> **规划语义（SSOT · 用户确认 @ 2026-07-04）：**  
> **R4** = 声明 scope 内能力、功能、机制 **真实落地**（可端到端跑通，非 mock 冒充）  
> **R5** = **运维、监控、使用/运行手册** 与生产 posture 收尾  
> **R6** = **完整商业可发布**（Batch05 发布 manifest 确认）  
> 下列 **枚举名** 保留历史字面（如 `SANDBOX`）；以本段规划语义为准。

| Level                               | Meaning                                                                                                                                                          | Can be called complete?                |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `R0_NOT_STARTED`                    | No meaningful runtime implementation beyond placeholder files or planning docs.                                                                                  | No                                     |
| `R1_SCAFFOLD`                       | API/module skeleton, contracts, or placeholders exist but no useful executable vertical slice.                                                                   | No                                     |
| `R2_MINIMAL_VERTICAL_SLICE`         | A bounded end-to-end slice (historical milestone; **not** the formal Batch 1 target — new work targets **R4** in Batch 1).                                       | No, only minimal slice complete        |
| `R3_STAGED_FIXTURE_CLOSED`          | The module runs against staged fixtures with validation, lineage/evidence, and negative tests.                                                                   | No, staged only — not full capability  |
| `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | **Capability complete** for declared scope: real pipelines/mechanisms work end-to-end with honest tests (proof often in isolated DB / sandbox; not ops/release). | No — **功能已落地，未运维收尾/未发布** |
| `R5_LIMITED_PRODUCTION_ENTRY`       | **Ops wrap:** runbooks, monitoring, on-call posture, operator docs; production entry caps/rollback where applicable.                                             | No — **可运维，未完整发布**            |
| `R6_FULL_PRODUCTION_STABLE`         | **Full release:** R4+R5 done for declared scope; regression suite green; release manifest; no open blocker.                                                      | **Yes**                                |

### 1.1 Milestone vs Rating（Pass E 规则）

| 列              | 含义                                                   | 禁止                        |
| --------------- | ------------------------------------------------------ | --------------------------- |
| **Rating**      | 模块**当前**在量表上的级别（全声明 scope）             | 用任务 CLOSED 直接改 Rating |
| **Milestone**   | 已交付的**有界竖切**（可引用 DCP/R3H ID）              | 把子集写成「模块已达 R4」   |
| **Close round** | 预计 **R6 完整发布** 轮次（如 Batch05）                | 与 Rating 混为一谈          |
| **批/3**        | 向 **R6** 已消耗的实现批次（上限 3；见 §1.2 三批法则） | 用审计 finding 数充批次     |

**子集达标不抬升整模块的典型例：** DCP-06 五轴 P0 clean read → Milestone ✅；G1 Rating 仍 **R3**（声明 scope 五轴真链未落地，非 R4）。

### 1.2 R4 / R5 / R6 三档（商业发布路径）

| 级别   | 规划一句话                                                        | 能否对外「完整发布」 | 典型交付物                                                                                         |
| ------ | ----------------------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------- |
| **R4** | 设计 authority **声明 scope** 内，能力/功能/机制 **真实落地**     | **否**               | 真链代码 + pytest/验收；证明环境常为 `.audit-sandbox` / 隔离库（**隔离库 ≠ 降级 R4**，仅证明环境） |
| **R5** | 在 R4 之上，**运维、监控、使用/运行手册** 与生产 posture **收尾** | **否**               | runbook · 告警/指标 · 备份恢复 · operator CLI 文档 · 主库/生产闸 manifest 条目                     |
| **R6** | R4+R5 完成 + 回归全绿 + **真实商业生产跑通** + 无开放 blocker     | **是**               | **Batch 3** 发布 manifest（Batch05）；模块可随产品 **完整发布**                                    |

**整产品：** 51 个 Module ID 均须 **R6**（`PROJECT_IMPLEMENTATION_ROADMAP.md` §5.3）。子范围（I6⊂I5、K2/K3⊂G1/G3）随父模块 R6。

**三批法则（路线图 §1.2 · 用户确认 @ 2026-07-04）：** 从零到商业真生产 **至多三批** — **Batch 1→R4**（完整功能/机制真落地）· **Batch 2→R5**（运维/监控/手册收尾）· **Batch 3→R6**（完整商业真生产）。R4 后 **再两轮**（R5+R6）即发布；**禁止第四批**。

| 批  | Rating | 能否完整发布 |
| --- | ------ | ------------ |
| 1   | R4     | 否           |
| 2   | R5     | 否           |
| 3   | R6     | **是**       |

**典型路径：**

| 模块族                | Batch 1 →R4                                | Batch 2 →R5             | Batch 3 →R6             |
| --------------------- | ------------------------------------------ | ----------------------- | ----------------------- |
| 数据管道 B/C/D/E/F    | 真 sync→clean→inspect（**9 模块已在 R4**） | runbook/monitor         | Batch05 真生产 manifest |
| 建模 G/K              | M-G\*-FULL 全 scope 真链                   | 面板/告警/operator 文档 | Batch05                 |
| 产品 I/J              | Round4 B04 全 API/前端/Agent（**R4**）     | 通知/隐私/运维文档      | Batch05                 |
| Batch6 D2/D3/D4/H1/A6 | 补能力至 R4                                | 同 Batch05 Batch 2      | Batch05                 |

**当前缺口：** **R6=0** · **R5** 仅 E5 部分触及 · **G1–G4 仍 R3**（未 R4 能力落地）。

---

## 2. Anti-overengineering completion rule

For every module or major feature after this file lands:

1. The **first implementation batch** (Batch 1) must deliver **`R4`** capability complete for the declared scope — not a permanent stop at R2/R3 staged fixtures.
2. The module must reach `R6_FULL_PRODUCTION_STABLE` in **no more than three implementation batches** (Batch 1→R4 · Batch 2→R5 · Batch 3→R6); see `PROJECT_IMPLEMENTATION_ROADMAP.md` §1.2.
3. Existing partially implemented modules must use their **next implementation batch** to close the **next rating gap** directly (e.g. R3→R4 in one batch), unless a written ADR narrows the module boundary.
4. Future task cards must distinguish:
   - **Batch 1 / capability complete** (→ R4);
   - **Batch 2 / ops wrap** (→ R5);
   - **Batch 3 / release gate** (→ R6);
   - **milestone only** (bounded subset — does not move Rating).
5. Repeated micro-slices such as “add one metric”, “add one flag”, “add one registry note”, or “add one narrow test” without moving the module to the next rating level are treated as overengineering unless they are part of the same batch PR.
6. Every **new** task card must cite **Module ID** (§3) and which **rating movement** it will deliver — if only a milestone, say so explicitly.

**Batch column (`批/3`):** implementation batches already spent toward **R6** (max 3 per §1.2); not Trellis task count. Pre-rule Wave/DCP batches still count toward the cap.

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

| ID  | Module                          | Design authority                                | Rating                              | 批/3 | Milestone                                     | Close round | Evidence                                                                                                                                                                                | 活票 / 归属（§1.8）                                         |
| --- | ------------------------------- | ----------------------------------------------- | ----------------------------------- | ---- | --------------------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| B1  | WriteManager + DbValidationGate | `validators`, `docs/modules/write_manager.md`   | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3H-06 upsert · R3G sandbox promote           | R3→R5       | `write_manager.py` · `tests/test_write_manager.py` · `test_round3g_limited_production_clean_write.py`（**仅** `.audit-sandbox`；`test_PromoteRunner_refusesCanonicalProductionDbPath`） | Batch05 main-DB posture smoke 或 manifest 声明 sandbox-only |
| B2  | Data quality validator          | `validators`, `data_quality_rules.yaml`         | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3H-08 profiles · sandbox live validate_table | R3→R5       | `validators/data_quality.py` · `test_data_quality_validator.py` · `test_tier_a_live_b2_acceptance.py`                                                                                   | Batch05                                                     |
| B3  | Source conflict validator       | `validators`, `data_validation_and_conflict.md` | `R3_STAGED_FIXTURE_CLOSED`          | 2/3  | R3H-08 live outcomes                          | R3          | `validators/source_conflict.py` · `tests/test_source_conflict_validator.py`                                                                                                             | **M-PASS-01**                                               |

### 3.C Data sources and routing

| ID  | Module                                       | Design authority                           | Rating                              | 批/3 | Milestone                                  | Close round | Evidence                                                                                                         | 活票 / 归属（§1.8）             |
| --- | -------------------------------------------- | ------------------------------------------ | ----------------------------------- | ---- | ------------------------------------------ | ----------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| C1  | Source registry / capability / route planner | `datasources`, `source_route_plan.md`      | `R3_STAGED_FIXTURE_CLOSED`          | 2/3  | R3H-01～04 reconcile                       | R3          | `source_registry.yaml` · `tests/test_source_registry.py` · `test_tierA_incremental_registry.py`                  | **M-PASS-01**                   |
| C2  | DataSourceService facade                     | `datasources`, `datasource_service.md`     | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3H-10 bypass guards                       | R3→R4       | `datasources/service.py` · `tests/test_datasource_service.py` · `test_sync_orchestrator.py`（R3H-10 / R3Y-SYNC） | 历史 CLOSED；**M-PASS-01** 审计 |
| C3  | Vendor adapters / provider fetch ports       | `datasources`, `fetch_ports/*`             | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3H-08 live gate · sandbox live acceptance | R3→R4       | `fetch_ports/*` · 11× `test_*_incremental_e2e.py` · `test_tier_a_live_harness.py`                                | Batch05                         |
| C4  | Provider catalog / auth-license gate         | `provider_catalog.yaml`, `license_gate.py` | `R2_MINIMAL_VERTICAL_SLICE`         | 2/3  | R3FR-05 catalog tests                      | R3→R5       | `tests/test_provider_catalog.py` · `license_gate.py`                                                             | **M-PASS-01**                   |

### 3.D Sync, scheduling, and task reliability

| ID  | Module                         | Design authority                                 | Rating                              | 批/3    | Milestone                               | Close round | Evidence                                                                                        | 活票 / 归属（§1.8）                                 |
| --- | ------------------------------ | ------------------------------------------------ | ----------------------------------- | ------- | --------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| D1  | Data sync orchestration        | `sync_orchestrator`, `data_sync_orchestrator.md` | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | **3/3** | DCP-01/02/05/09 · sandbox live dispatch | R3→R5       | `sync/orchestrator.py` · `tier_a_live_incremental_dispatch.py` · `test_tier_a_live_dispatch.py` | Batch05                                             |
| D2  | Task idempotency / retry / DLQ | `docs/ops/idempotency_retry_dlq_policy.md`       | `R1_SCAFFOLD`                       | 0/3     | —                                       | Batch6      | 政策文档 only；**无** `idempotency_key` runtime                                                 | Batch6 store/replay 或 ADR 收窄为 write upsert 足够 |
| D3  | Sync scheduler / cron product  | `data_sync_orchestrator.md` §CLI                 | `R0_NOT_STARTED`                    | 0/3     | —                                       | R4→R5       | 无 scheduler 模块；仅 `qmd data` 手动触发                                                       | R4：scheduler shell 调 D1 同一 entrypoint           |
| D4  | Source health snapshot writer  | `ADR-024`, `source_health_writer.py`             | `R2_MINIMAL_VERTICAL_SLICE`         | 1/3     | isolated writer test                    | Batch6      | `ops/source_health_writer.py` · `tests/test_source_health_snapshot.py`（`:memory:`）            | Batch6 production migration                         |

### 3.E Ops, CLI, and sandbox entry

| ID  | Module                                         | Design authority                  | Rating                              | 批/3 | Milestone                                | Close round | Evidence                                                                               | 活票 / 归属（§1.8）              |
| --- | ---------------------------------------------- | --------------------------------- | ----------------------------------- | ---- | ---------------------------------------- | ----------- | -------------------------------------------------------------------------------------- | -------------------------------- |
| E1  | `qmd data` CLI                                 | `docs/ops/data_health_cli.md`     | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | DCP-01/02/05 router · sandbox live CLI   | R3→R5       | `cli/data_commands.py` · `test_tier_a_live_dispatch.py` · `test_qmd_data_cli.py`       | Batch05                          |
| E2  | Ops DB inspect + verification matrix           | `docs/ops/db_inspect_cli.md`      | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | DCP-03 · sandbox per-source inspect      | R3→R5       | `ops/db_inspector.py` · `test_tier_a_live_dispatch.py`                                 | Batch05                          |
| E3  | Production gate + equivalent smoke             | `scripts/production_gate.py`      | `R2_MINIMAL_VERTICAL_SLICE`         | 1/3  | gate scripts                             | R5          | `tests/test_production_gate.py` · `test_production_equivalent_smoke_budget.py`         | Batch05 integration smoke owner  |
| E4  | Live / staged pilot runners                    | `production_live_pilot_policy.md` | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3H-08 ProductLiveGate                   | R3          | `ops/live_pilot*.py` · `product_live_gate.py` · `tests/test_staged_pilot.py`           | **M-PASS-01**                    |
| E5  | Sandbox clean write / limited production entry | `ops/sandbox_clean_write`         | `R5_LIMITED_PRODUCTION_ENTRY`       | 3/3  | R3G promote · **R5 运维/生产闸部分就绪** | R6 confirm  | `limited_production_entry.py` · `tests/test_round3g_limited_production_clean_write.py` | Batch05 · R5→R6                  |
| E6  | Backup / recovery / disk thresholds            | `backup_and_recovery.md`          | `R1_SCAFFOLD`                       | 1/3  | —                                        | R5          | ops 文档；无 automated backup runner                                                   | Batch05 runbook + optional smoke |
| E7  | Ops report CLI                                 | `docs/ops/ops_report_cli.md`      | `R0_NOT_STARTED`                    | 0/3  | —                                        | R4→R5       | design only                                                                            | B04_04 或 ADR defer              |

### 3.F Data health (operator profiles)

| ID  | Module             | Design authority           | Rating                                         | 批/3 | Milestone                                      | Close round | Evidence                                                                                         | 活票 / 归属（§1.8） |
| --- | ------------------ | -------------------------- | ---------------------------------------------- | ---- | ---------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------ | ------------------- |
| F0  | Data health engine | `ops/data_health_profiles` | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` **（窄）** | 2/3  | DCP-03 · sandbox Tier A profiles in acceptance | R3→R5       | `data_health_profiles/` · `test_data_health_tier_a_profiles.py` · `test_tier_a_live_dispatch.py` | Batch05             |

### 3.G Modeling layers (Layer1–5) — Pass E 重灾区

| ID  | Module                     | Design authority                               | Rating                          | 批/3 | Milestone（≠ Rating）                                           | Close round | Evidence                                                                                                                                     | 活票 / 归属（§1.8）         |
| --- | -------------------------- | ---------------------------------------------- | ------------------------------- | ---- | --------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| G1  | Layer1 axes / regime panel | `layer1_axes`, `layer1_global_regime_panel.md` | **`R3_STAGED_FIXTURE_CLOSED`**  | 2/3  | **DCP-06**：五轴 P0 clean **读** e2e（tmp seed）                | R4→R5       | `clean_observation_reader.py` · `tests/test_layer1_*_clean_e2e.py` · `test_layer1_five_axis_panel_clean_smoke.py`；ingestion 默认 **staged** | **M-G1-03**                 |
| G2  | Layer2 cross-asset sensors | `layer2_cross_asset_sensor.md`                 | **`R3_STAGED_FIXTURE_CLOSED`**  | 2/3  | **DCP-07**：**仅 L2-VIX** clean replay                          | R4→R5       | `sensor_loader.py`（`production_clean_replay` + fred 白名单）· `tests/test_layer2_vix_clean_e2e.py`；设计九组资产 **未**覆盖                 | **M-G2-FULL**               |
| G3  | Layer3 industry chains     | `layer3_industry_shock_anchor.md`              | `R3_STAGED_FIXTURE_CLOSED`      | 1/3  | 021/022 staged snapshots                                        | R4+         | `loader.py` / `snapshot_builder.py` **仅** `staged_fixture_only` · `tests/test_layer3_*.py`                                                  | Round4 初（非 PASS 硬门禁） |
| G4  | Layer4 market structure    | `layer4_market_structure.md`                   | **`R3_STAGED_FIXTURE_CLOSED`**  | 2/3  | **DCP-08**：**仅 US_EQ** `tier_a_clean`                         | R4→R5       | `market_structure.py` · `tests/test_layer4_us_equity_clean_e2e.py`；CN_A 仍 staged                                                           | **M-G4-FULL**               |
| G5  | Layer5 evidence / security | `layer5_security_evidence.md`                  | **`R2_MINIMAL_VERTICAL_SLICE`** | 2/3  | **DCP-10**：mootdx bar→provenance（**唯一** sync→clean 全链测） | R4→R5       | `tests/test_layer5_mootdx_bar_clean_e2e.py` · `provenance.py`；foundation 测仍 `STAGED_PROVENANCE`                                           | **M-G5-FULL**               |
| G6  | Manual review staging      | `manual_review_staging.py`                     | `R3_STAGED_FIXTURE_CLOSED`      | 1/3  | R3H-08D live bundle（**不写 clean**）                           | R3          | `tests/test_no_clean_write_for_web_evidence.py` · kalshi/polymarket replay                                                                   | **M-PASS-01**               |

> **Rating 说明：** 升到 **R4** 须声明 scope 内能力/机制 **真落地**（非 staged 子集冒充）；**R5**=运维收尾 · **R6**=完整发布。G\* 当前 **未达 R4**。

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

## 3.2 Rating 复核说明

- **本文件 §3 的 Rating / 批/3 / Close round 列** 为模块评级唯一 SSOT。
- **Milestone / Evidence 列** 仅指向可复验 **pytest/代码** 锚点，用于支撑 Rating 判定；**不是** Trellis 关账证据。
- 历史审计 Pass（E/D/C/B）、任务 CLOSED、ADR 关账表 → `PROJECT_IMPLEMENTATION_ROADMAP.md` · archived Trellis · `docs/decisions/ADR-*.md`。

---

## 4. Planning consequences（评级规则 · 非活工单）

- Design/contract files remain **complete-product targets**; **Rating 列**只跟踪已证明的实现 scope。
- **禁止**用任务 CLOSED、tmp seed、staged 子集或全 mock e2e 抬高至 **R4**。
- 新票须标明 Module ID 与 **Rating 跃迁**（R4 能力 / R5 运维 / R6 发布）；milestone-only 不得隐含整模块升级。
- 活工单队列见 **`PROJECT_IMPLEMENTATION_ROADMAP.md` §3**（不在本文件重复）。
- **R4 真链最低标准（数据/建模）：** `sync → clean → Layer` 同库 e2e；证明环境可隔离，**不污染主库**。
