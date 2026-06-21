# Original Plan Trace — round3-batch2-75-live-pilot

## Round / Batch

- **Round:** 3
- **Batch:** 2.75
- **Trellis slug:** `06-21-round3-batch2-75-live-pilot`
- **Map alias:** `R3-B2.75-PROD-LIVE-PILOT`
- **Map item IDs:** `R3-B2.75-01`, `GLOBAL-P2-01`, `B2.5-O-05`, `R3-B25-PERF-BUDGET-01`, `R3-B25-HYG-03`

## 任务卡清单（NNN → 路径）

| ID   | 路径                                                                                   | 类型                                   |
| ---- | -------------------------------------------------------------------------------------- | -------------------------------------- |
| 018B | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md` | 正式 alias 执行文件（非 017–023 编号） |

## AC 映射（任务卡预期结果 → MASTER §2）

| 018B 章节        | 任务卡预期                | MASTER AC                  |
| ---------------- | ------------------------- | -------------------------- |
| §0 scope ledger  | 四条工作流 + not-in-scope | AC-PM1..AC-PM4, §1.3 table |
| §3 + §3.1        | 授权字段 + 三 micro-pilot | AC-P0-1..4                 |
| §4 Phase -1      | registry 对账             | AC-PM1..AC-PM4             |
| §5 Phase 0       | 授权证据                  | AC-P0-1..4                 |
| §6 Phase 1       | 只读 baseline             | AC-P1-1..2                 |
| §7 Phase 2       | route dry-run             | AC-P2-1..3                 |
| §8 Phase 3       | raw-only micro-fetch      | AC-P3-1..5                 |
| §9 Phase 4       | sandbox validation        | AC-P4-1..4                 |
| §10 Phase 4.5    | perf budget               | AC-P45-1..3                |
| §11 Phase 5      | PILOT\_\* + handoff       | AC-P5-1..4                 |
| §12 registry     | 三份 registry             | AC-P5-3, AC-REG-1          |
| §13 verification | pytest 命令               | §9–§10                     |

## 输入文件已读（specs / architecture / modules）

| 路径                                                         | 类别           | manifest                         |
| ------------------------------------------------------------ | -------------- | -------------------------------- |
| `018B_production_live_pilot_gate.md`                         | original-task  | Plan only                        |
| `production_live_pilot_policy.md`                            | rule           | summarized §0.7                  |
| `batch275_user_authorization_2026-06-21.md`                  | authorization  | **required** Execute             |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                         | index          | Plan only                        |
| `source_registry.yaml`                                       | registry       | **required** Execute             |
| `source_capabilities.yaml`                                   | registry       | **required** Execute             |
| `source_route_contract.yaml`                                 | contract       | **required** Execute             |
| `datasource_service_contract.yaml`                           | contract       | **required** Execute             |
| `ops_db_inspect_contract.yaml`                               | contract       | **required** Execute             |
| `data_quality_rules.yaml`                                    | contract       | **required** Phase 4             |
| `write_contract.yaml`                                        | contract       | pointer (no default clean write) |
| `resource_limits.yaml`                                       | contract       | **required** §10                 |
| `docs/modules/datasource_service.md`                         | design         | **required** Execute             |
| `docs/modules/source_route_plan.md`                          | design         | **required** Execute             |
| `docs/ops/db_inspect_cli.md`                                 | ops            | **required** Execute             |
| `backend/app/datasources/service.py`                         | inherited code | **required** Execute             |
| `backend/app/datasources/route_planner.py`                   | inherited code | **required** Execute             |
| `backend/app/ops/db_inspector.py`                            | inherited code | **required** Execute             |
| `backend/app/ops/live_pilot.py`                              | Execute 新建   | deferred                         |
| `scripts/production_equivalent_smoke.py`                     | script         | Phase 4.5 pointer                |
| `06-20-round3-batch2-5-layer1-obs-ingest/execute-evidence/*` | prior evidence | trace only — staged              |

## 路径纠偏

| 任务卡声明                                                  | 实际                                                    |
| ----------------------------------------------------------- | ------------------------------------------------------- |
| `docs/quality/batch275_user_authorization_2026-06-21.md`    | 018B §3.1 指定；Plan 阶段已创建                         |
| `fred` live pilot                                           | **不存在** `source_id=fred`；禁止绕过 registry          |
| Batch 2.5 `ingestion_evidence.capture_task_phase3_evidence` | 使用 staged fixture — **不得**用于 Batch 2.75 live 证据 |
