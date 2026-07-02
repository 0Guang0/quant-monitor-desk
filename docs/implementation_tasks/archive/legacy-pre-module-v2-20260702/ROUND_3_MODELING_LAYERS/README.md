# ROUND 3 MODELING LAYERS

本目录包含 017–023 共 7 个正式 implementation task 文件，并新增 `018A_layer1_observation_ingestion_bridge.md` 作为 Batch 2.5 强制桥接执行文件、`018B_production_live_pilot_gate.md` 作为 Batch 2.75 受控生产/live 数据试点门禁文件、`018C_tdx_pytdx_low_cost_probe.md` 作为 Batch 2.75 后续低成本数据接口候选源 sidecar probe 任务，另新增 `023A_layer5_evidence_foundation.md` 作为完整 `023` 之前的最小证据地基切片。真实数据相关 readiness 必须按 `017` → `018` → `018A` → `018B` → `018C`（仅在 Batch 2.75 Request 2 evidence reconciliation 后）→ `019` 顺序推进；但 Batch 2.75 closeout 为 `PILOT_FAIL_SOURCE` 且相关 deferred rows 标记为不阻塞 019 时，`019` 可作为 staged-only downstream batch 继续推进，前提是 MASTER/AUDIT 显式引用 `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`，不得声称 production-live readiness。`023A` 可与 `019` 并行但只能做最小 evidence foundation，不得实现完整 Layer5。

**Round 3 early（不在本目录编号内）：** 本地 DuckDB 只读检查 CLI — 冻结设计为 `../../ops/db_inspect_cli.md`，契约为 `../../../specs/contracts/ops_db_inspect_contract.yaml`；设计冻结后执行者只能按该设计实现。见 `../ROUND3_EARLY_CLOSE_PLAN.md`、`../../ROUND3_HANDOFF.md` 与 `../../../ROUND3_BATCH_IMPLEMENTATION_MAP.md`。

执行前读取：

- `../GLOBAL_EXECUTION_RULES.md`
- `../GLOBAL_TESTING_POLICY.md`
- `../GLOBAL_RESOURCE_LIMITS.md`
- `../GLOBAL_TASK_TEMPLATE.md`

本目录文件不是临时文件，最终交付包应保留。
