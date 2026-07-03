# 019 Plan/Audit Review Report

> **Branch:** `review/round3-019-plan-audit`  
> **Worktree:** `../quant-monitor-desk-wt-review-round3-019-plan-audit`  
> **Base:** `master` @ `76ea3471`  
> **Reviewed implementation branch:** `feature/round3-019-layer2-sensor` @ `ff8fe791`  
> **Reviewer lane:** read-only (PROMPT_09)  
> **Date:** 2026-06-22

---

## Verdict: **WARN**

`feature/round3-019-layer2-sensor` 的 Plan/Audit 与实现 **未触发任何阻塞级清单项**，staged-only、数据源边界、防双算、lineage、WriteManager/ResourceGuard 与 023A 核心文件所有权均符合 Batch 3 gate。  
**019 可继续**（合并至 `integration/round3`），但建议在合并前将 `AUDIT.plan.md` 阻塞检查清单勾选完成，并显式记录已 defer 的模块范围，避免后续任务误读为 production-ready 或完整 Layer2 流水线。

---

## Pre-flight（分支 / gate）

| Check                                 | Status | Evidence                                                                        |
| ------------------------------------- | ------ | ------------------------------------------------------------------------------- |
| `R3-B3-STAGED-DOWNSTREAM-GATE` CLOSED | ✅     | `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md` §Gate status                    |
| `019_plan_audit_review.md` exists     | ✅     | `docs/implementation_tasks/ROUND_3_REVIEW/019_plan_audit_review.md`             |
| 019 plan artifacts available          | ✅     | `.trellis/tasks/06-22-round3-019-layer2-sensor/MASTER.plan.md`, `AUDIT.plan.md` |
| Review worktree created               | ✅     | `review/round3-019-plan-audit` @ `76ea3471`                                     |

---

## Reviewed artifacts

### Protocol / map

- `AGENTS.md`, `CLAUDE.md` — Plan/Execute gate 与 Repair/Debt Lite 协议
- `.trellis/workflow.md`, `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`

### Task / module / contract

- `docs/implementation_tasks/ROUND_3_REVIEW/019_plan_audit_review.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md`
- `docs/modules/layer2_cross_asset_sensor.md`
- `specs/contracts/layer2_sensor_contract.yaml`
- `specs/contracts/snapshot_lineage_contract.yaml`
- `specs/datasource_registry/source_registry.yaml`（只读，019 分支无 diff）
- `specs/datasource_registry/source_capabilities.yaml`（只读，019 分支无 diff）
- `docs/AUDIT_DEFERRED_REGISTRY.md`, `docs/UNRESOLVED_ISSUES_REGISTRY.md`

### Implementation branch primary artifacts

- `.trellis/tasks/06-22-round3-019-layer2-sensor/MASTER.plan.md`
- `.trellis/tasks/06-22-round3-019-layer2-sensor/AUDIT.plan.md`
- `.trellis/tasks/06-22-round3-019-layer2-sensor/execute-evidence/merge_gate_report.md`
- `.trellis/tasks/06-22-round3-019-layer2-sensor/research/original-plan-trace.md`
- `backend/app/layer2_sensors/*`（46 files, +2676 LOC vs master）
- `tests/test_layer2_sensor_loader.py`（32 tests）
- `tests/fixtures/layer2_cross_asset_registry_fixture.yaml`

---

## Blocker checklist (PROMPT §4)

| #   | Criterion                                            | Result   | Evidence                                                                                                                                                                                 |
| --- | ---------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 019 声称 production-live readiness                   | **PASS** | `MASTER.plan.md` §0 标题与 §16 八条 staged 限制；`sensor_loader.py` L72–77 拒绝 `mode != staged_fixture_only`；`merge_gate_report.md` 明确无 production DB mutation                      |
| 2   | `tdx_pytdx` 作生产源或 Primary                       | **PASS** | `ALLOWED_PRIMARY_SOURCES = {"staged_fixture"}`（`sensor_loader.py` L53）；`observation.py` L79–81 拒绝 `source == "tdx_pytdx"`；`test_stagedSource_rejectsTdxPytdx_viaBuilder`           |
| 3   | 默认 live FRED / 外部 vendor 写入                    | **PASS** | 无 fetch/orchestrator 集成；registry `primary_source` 仅 `staged_fixture`；`B2.5-O-05` / `R3-B2.75-REQ2-EM` 在 MASTER §16 显式引用                                                       |
| 4   | Eastmoney hist 静默 fallback 至 TDX/Sina/QMT/xqshare | **PASS** | 019 未实现 CrossAssetFetcher / route planner；无 fallback 路由代码；fixture-only 输入                                                                                                    |
| 5   | 缺少 `double_count_guard` 语义                       | **PASS** | `double_count_guard.py` + registry 校验；`test_doubleCountGuard_*`, `test_vixAxisInput_*`, `test_noAcceptedChannel_notModelEligible`                                                     |
| 6   | 缺少 no-future-data 测试                             | **PASS** | `reject_future_observation` 覆盖 trade_time / as_of_timestamp / fetch_time；`test_snapshotRejectsFuture*`；`test_incrementalRebuildPreservesAsOfBoundary`                                |
| 7   | 绕过 WriteManager / ResourceGuard                    | **PASS** | `Layer2SnapshotWriter`, `Layer2ObservationWriter`, `Layer2RollEventWriter`, `CrossAssetRegistryWriter` 均经 WriteManager；`assert_resource_guard_allows` 于 snapshot/observation writer  |
| 8   | 修改 Layer3/4/5 runtime 越界                         | **PASS** | MASTER §1 非目标列出 Layer3/4/5、FastAPI；diff 仅 `backend/app/layer2_sensors/`；`guard_layer2_writeback` 防止回写 Layer1                                                                |
| 9   | 019 与 023A 同时写 `snapshot_lineage_contract.yaml`  | **PASS** | `git diff master...feature/round3-019-layer2-sensor -- specs/contracts/snapshot_lineage_contract.yaml` 为空；MASTER §0「023A lineage 对接」明确只读 contract、写 `axis_snapshot_lineage` |

**阻塞项：0**

---

## Thematic assessment

### 1. Staged-only 语义

- **合规。** MASTER §16 完整引用 `BATCH3_STAGED_DOWNSTREAM_GATE.md`、`final_registry_update.md` staged 口径、`018A` §13、`UNRESOLVED_ISSUES_REGISTRY`（`PILOT_FAIL_SOURCE` / `R3-B2.75-REQ2-EM`）、`production_live_pilot_policy.md`、`B2.5-O-05` DEFERRED。
- 实现层：`CrossAssetRegistryLoader` 强制 `mode: staged_fixture_only`；sandbox 表经 `ensure_layer2_staging_tables`；merge gate 记录无 production migration。
- **注意：** `instrument_id: FRED:VIXCLS` 出现在 fixture 元数据（`layer2_cross_asset_registry_fixture.yaml` L10），但 `primary_source: staged_fixture`，不构成 live FRED 调用；建议在 AUDIT 或 fixture 注释中写明「标识符仅作映射，非 live 源」。

### 2. 数据源边界

- Primary 白名单仅 `staged_fixture`；无 live vendor adapter 接线。
- `tdx_pytdx` 在 observation 层 fail-closed。
- `fallback_policy` 字段存在于 registry schema，但 019 **未实现**任何运行时 fallback——符合 gate（无静默降级），但后续实现 fetch 时必须复用 SourceRoutePlanner 显式策略，不得在此字段上硬编码 silent switch。

### 3. 防双算（double_count_guard）

- Registry 规则：`is_axis_input` → `display_only=true` + `eligible_for_model=false` + `double_count_guard=layer1_axis_input_display_only`。
- 运行时：`assert_model_eligible` 阻断 axis input 进入 model aggregation；`for_model=True` 路径对 VIX 抛 `DoubleCountGuardError`。
- `NO_ACCEPTED_CHANNEL` 资产不可 model-eligible；quality flag 传播至 snapshot。

### 4. Snapshot lineage / 未来数据

- Lineage 写入共享表 `axis_snapshot_lineage`（`layer_id=layer2`），字段与 `snapshot_lineage_contract.yaml` 对齐（`LINEAGE_REQUIRED_FIELDS`）。
- `Layer2LineageBuilder` 拒绝 agent 文本进入 `source_dataset_ids`。
- 测试覆盖 contract 三项：`test_snapshotRejectsFuture*`、`test_snapshotLineageContainsSourceHashes`、`test_incrementalRebuildPreservesAsOfBoundary`。
- `upstream_snapshot_ids` 经 `test_upstreamSnapshotIds_propagateToLineage` 验证。

### 5. WriteManager / ResourceGuard

- 所有 clean 写入路径：staging → `DbValidationGate` → `WriteManager`；测试含 `test_layer2Snapshot_writeViaWriteManager`、`test_layer2Observation_writeViaWriteManager`、`test_futuresRollEvent_persistedViaWriteManager`。
- ResourceGuard：`test_crossAssetSnapshotBuilder_resourceGuardBlocksBatchBuild`（HARD_STOP）+ 真实实例 decision 测试。

### 6. 核心文件所有权（023A）

- 019 未修改 `snapshot_lineage_contract.yaml`、`source_registry.yaml`、`source_capabilities.yaml`。
- MASTER 与 `project-map-omission-check.md` 明确 023A 拥有 contract 写权限；019 使用既有 `axis_snapshot_lineage` 表（migration 011）。

### 7. 测试强度

- 32 项语义测试，非仅存在性检查；AC-019-1..8 在 `original-plan-trace.md` 与 `AUDIT.plan.md` 有映射。
- **缺口（非阻塞）：** 无 end-to-end staging→DQ→conflict 流水线测试（与 MASTER 非目标一致）；无 Layer2 API 契约测试（FastAPI defer）。

---

## Findings

### Blockers

_无_

### Non-blockers（应在合并前或合并时处理）

| ID        | Finding                                                                        | Location                                                             | Required fix                                                                                      |
| --------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| F-019-R01 | `AUDIT.plan.md` §阻塞级检查全部为 `[ ]`，与 §8 已执行 / merge_gate PASS 不一致 | `.trellis/tasks/06-22-round3-019-layer2-sensor/AUDIT.plan.md` L26–32 | 实现分支将六项勾选为 `[x]` 或附 audit 执行日期                                                    |
| F-019-R02 | 模块 doc §7 描述完整抓取流水线，MASTER 明确 defer DQ/conflict 全流水线         | `docs/modules/layer2_cross_asset_sensor.md` §7 vs MASTER §1 非目标   | 在 MASTER §1 或 `merge_gate_report.md` Deferred 中交叉引用模块 §12 任务拆分序号，避免 020+ 误跳过 |
| F-019-R03 | Fixture `FRED:VIXCLS` instrument_id 可能被误读为 live FRED primary             | `tests/fixtures/layer2_cross_asset_registry_fixture.yaml` L10        | 增加 YAML 注释或 AUDIT 注记：`primary_source=staged_fixture` 为准                                 |

### Suggestions

| ID       | Suggestion                                                                          | Rationale                            |
| -------- | ----------------------------------------------------------------------------------- | ------------------------------------ |
| S-019-01 | 合并后由 023A 分支统一演进 `snapshot_lineage_contract.yaml`；019 保持只读           | 避免并行 contract drift              |
| S-019-02 | 下一 slice（fetcher / API）须新开任务卡并重新过 Batch3 gate                         | 019 范围已正确收窄为 staged skeleton |
| S-019-03 | `R3-B2.75-01` 在 MASTER 引用；registry 主表为 `BLOCK-R3-002` 别名——保持二者同步即可 | 命名别名，非语义冲突                 |

---

## Verification commands（reviewer 基线 @ master）

```text
uv run pytest tests/test_batch3_staged_downstream_gate.py -q          → 通过
uv run pytest tests/test_round3_audit_registry_alignment.py -q        → 通过
uv run pytest tests/test_unresolved_item_task_coverage.py -q          → 通过
uv run pytest tests/test_trellis_audit_trace_authority.py -q          → 通过
```

合计 **18 passed**（review 基线 `76ea3471`）。

实现分支自述（未在本 review worktree 重跑全量）：

```text
pytest tests/test_layer2_sensor_loader.py -q  → 32 passed（merge_gate_report.md）
validate-execute-handoff                      → PASSED
```

---

## Proceed / fix / decision

| Question                 | Answer                                                                                                 |
| ------------------------ | ------------------------------------------------------------------------------------------------------ |
| **019 是否可继续？**     | **是** — staged-only Layer2 sensor skeleton 可合并至 `integration/round3`                              |
| **是否必须修复阻塞项？** | **否** — 无阻塞项                                                                                      |
| **是否需要用户决策？**   | **否** — 除非用户希望将 scope 扩展至 live fetch / production migration / FastAPI（均超出本任务非目标） |
| **合并前建议**           | 在 `feature/round3-019-layer2-sensor` 上完成 F-019-R01（AUDIT 清单勾选）                               |

---

## Summary

`feature/round3-019-layer2-sensor` 的 MASTER/AUDIT 与实现一致地锚定在 **staged-only downstream**：gate 已关闭、无 production-live 声称、无 live 源默认、无静默 fallback、`double_count_guard` 与三重 no-future-data 边界有语义测试、clean 写入经 WriteManager/ResourceGuard、lineage 写共享表且不抢 023A contract 所有权。  
审查结论为 **WARN**（非 BLOCK）：主要因 AUDIT 计划清单未勾选及文档 scope 对齐细节；**不阻止 019 继续合并**，建议在合并前完成 AUDIT 清单 closure。
