# Round 3 波次 A — Merge Coordinator Slice Plans

> 协调者：主会话 · 基准 `master` @ `61436a51` · 2026-06-23  
> 硬约束：`R3-B2.75-REQ2-EM` DEFERRED；全程 **staged-only**，不得声称 production-live。

---

## 并行波次 A 总览

| Slice                               | Owner                 | Base     | Target branch                                     | Worktree                                                   |
| ----------------------------------- | --------------------- | -------- | ------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------- |
| **020** Layer3 loader               | `implement-agent-020` | `master` | `feature/round3-020-layer3-loader`                | `../quant-monitor-desk-wt-020-layer3-loader`               | **已合并 master** · Audit PASS · archived               |
| **PROMPT_18** post-R3X strict audit | 7× 并行 module agent  | `master` | `review/round3-post-r3x-strict-adversarial-audit` | `../quant-monitor-desk-wt-review-r3-post-r3x-strict-audit` | **已合并 master** · WARN_ALLOW_WITH_CONTROLS · archived |

**PROMPT_18 派发：** `research/parallel-audit-dispatch.md`（review worktree 任务目录）

**Core file 锁：** 020 独占 `backend/app/layer3_chains/` + `tests/test_layer3_loader.py`；PROMPT_18 只读，无写锁冲突。

**串行后续：**

- 波次 B：PROMPT_19 — 等 **PROMPT_18 v2 AUD-08** gate（非 v0 单 agent 结论）
- 波次 C：PROMPT_20 — 等 PROMPT_19 evidence

**派发（v2）：** 7 个并行 module agent（R3Y-AUD-01…07 各一）；AUD-08 由协调者在 01–07 落盘后合成 gate。见 `parallel-audit-dispatch.md`。

---

## Slice 020 — Layer 3 industry chain loader

### Source of truth

| 项               | 值                                                                                                |
| ---------------- | ------------------------------------------------------------------------------------------------- |
| Task card        | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/020_implement_layer3_industry_chain_loader.md` |
| Contract         | `specs/contracts/layer3_loader_contract.yaml`                                                     |
| Registry inputs  | `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/*`                        |
| Module doc       | `docs/modules/layer3_industry_shock_anchor.md`                                                    |
| 019 前置         | merged @ `c940a8d0`；`R3-B3-STAGED-DOWNSTREAM-GATE` CLOSED                                        |
| Trellis task dir | `.trellis/tasks/06-23-round3-020-layer3-loader/`（Plan freeze 后）                                |

### Boundary

**Allowed files**

- `backend/app/layer3_chains/**`
- `tests/test_layer3_loader.py`
- `tests/fixtures/layer3_*`（若需 staged fixture）
- `.trellis/tasks/06-23-round3-020-layer3-loader/**`（任务工件）
- `research/`、`execute-evidence/`（任务内）

**Forbidden files**

- `backend/app/layer2_sensors/`（019 已归档）
- `backend/app/layer4_markets/`、`backend/app/layer5_evidence/`（后续 batch）
- `backend/app/datasources/`、`backend/app/db/`、`backend/app/ops/`、`backend/app/validators/`
- `specs/contracts/snapshot_lineage_contract.yaml`（023A 写权限；020 只读消费）
- `specs/datasource_registry/**`、`configs/datasource.yml`
- `docs/AUDIT_DEFERRED_REGISTRY.md`、`docs/UNRESOLVED_ISSUES_REGISTRY.md`、`docs/RESOLVED_ISSUES_REGISTRY.md`
- `data/duckdb/quant_monitor.duckdb`（production DB）
- 任何 production-live fetch / clean write 到生产路径

**Production / data boundary**

- Staged-only：registry 自 `specs/layer3_global_industry_chains/` 或 task fixture 加载
- 若写 sandbox/staging 表，必须经 `DuckDBWriteManager` + `DbValidationGate`
- 无 live vendor fetch；`event_only` 私有公司不得作普通日频价格锚

**Explicit non-goals**

- Layer3 snapshot builder（021）
- Layer4/5、FastAPI 路由、前端
- 修改 lineage contract schema
- production-live 声称

### Vertical slices（Plan 阶段 `/to-issues` 细化）

| Slice                    | AC                                               | 验证                               |
| ------------------------ | ------------------------------------------------ | ---------------------------------- |
| 8.0 Boot                 | implement.jsonl 全读；基线 pytest                | `8.0-red/green`                    |
| 8.1 Registry load        | chain/anchor/node/edge/cross-chain 加载 + 唯一性 | contract hard rules                |
| 8.2 Reference validation | node/edge 引用存在；anchor.node_id 存在          | fail-fast errors                   |
| 8.3 event_only           | 私有公司 event_only 不作普通价格锚               | semantic test                      |
| 8.4 P0 source            | P0_CORE / P0_EVENT anchors 有 source_keys        | contract §source_validation_status |
| 8.5 Staged gate          | 不声称 production-live                           | batch25/batch3 gate tests          |
| 8.6 Handoff              | validate-execute-handoff exit 0                  | merge_gate_report                  |

### Verification（merge gate）

```bash
uv sync --locked
uv run pytest tests/test_layer3_loader.py -q
uv run pytest tests/test_batch3_staged_downstream_gate.py tests/test_batch25_production_data_gate.py -q
uv run pytest tests/test_round3_audit_registry_alignment.py -q
uv run ruff check backend/app/layer3_chains tests/test_layer3_loader.py
uv run python -m compileall backend/app/layer3_chains tests/test_layer3_loader.py
uv run python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/06-23-round3-020-layer3-loader
```

**Evidence path：** `.trellis/tasks/06-23-round3-020-layer3-loader/execute-evidence/`、`merge_gate_report.md`、`audit_matrix.json`（Audit 后）

**020 Plan（已 freeze，待核实）：** worktree `.trellis/tasks/06-23-round3-020-layer3-loader/` — `validate-plan-freeze` exit 0；**未** `task.py start`。核实项：空占位 `test_layer3_loader.py`、authority_graph warning、`R3-B2.75-REQ2-EM` DEFERRED。

---

## Slice PROMPT_18 — Post-R3X strict adversarial audit

### Source of truth

| 项           | 值                                                                                                                |
| ------------ | ----------------------------------------------------------------------------------------------------------------- |
| PROMPT       | `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_18_review_round3_post_r3x_strict_adversarial_audit.md` |
| Task card    | `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_post_r3x_strict_adversarial_audit.md`           |
| Evidence dir | `.trellis/tasks/06-23-round3-post-r3x-strict-audit/review-evidence/`                                              |

### Boundary

**Allowed files（仅本 slice 任务目录）**

- `.trellis/tasks/06-23-round3-post-r3x-strict-audit/**`
- `.trellis/workspace/Guang/journal-1.md`（协调者 session 记录，可选）

**Forbidden（绝对禁止修改）**

- `backend/**`、`frontend/**`、`scripts/**`（除只读运行 pytest）
- `specs/**`、`configs/**`、`docs/**`（registry、quality、modules）
- `data/**`、production DB、migrations
- 任何实现/spec/registry/DB 变更

**Production / data boundary**

- 只读审计；安全 pytest only；无 source fetch；无 disabled source 启用

### Vertical issues（R3Y-AUD-01 … 08）— v2 并行

| Issue | 模块/agent                     | 产出                             |
| ----- | ------------------------------ | -------------------------------- |
| 01    | closed claims / merge evidence | `R3Y-AUD-01-closed-claims.md`    |
| 02    | `backend/app/datasources/`     | `R3Y-AUD-02-source-route.md`     |
| 03    | db/storage/sync write gate     | `R3Y-AUD-03-write-validation.md` |
| 04    | ops staged pilot               | `R3Y-AUD-04-staged-pilot.md`     |
| 05    | layer2/5 lineage               | `R3Y-AUD-05-lineage.md`          |
| 06    | registry 三件套                | `R3Y-AUD-06-registry.md`         |
| 07    | test depth                     | `R3Y-AUD-07-test-quality.md`     |
| 08    | **协调者**（等 01–07）         | `review.report.md` + gate        |

v0 单 agent 浅表结论：`review-evidence/v0-monolithic/`（仅供对比）

### Verification（只读）

```bash
uv run pytest tests/test_r3x_residual_open_items_closure.py -q
uv run pytest tests/test_staged_pilot.py -q
uv run pytest tests/test_datasource_service.py tests/test_source_route_planner.py tests/test_source_capabilities.py -q
uv run pytest tests/test_db_validation_gate.py tests/test_write_manager.py tests/test_raw_store.py -q
uv run pytest tests/test_layer2_sensor_loader.py tests/test_layer5_evidence_foundation.py -q
uv run pytest tests/test_round3_audit_registry_alignment.py -q
uv run python scripts/check_doc_links.py
```

**Merge gate：** 默认 **不合并实现**；用户批准后仅归档 `review.report.md` + issue matrix。

**派发：** 主会话编排 A1–A8 或单 review agent；`audit-a1-spec.md` + `doubt-driven-development`；model 由协调者指定。

---

## Merge coordinator checklist（Phase 8D §8）

- [x] Protocol baseline visible（`master` @ `61436a51`）
- [x] Base / target branch named
- [x] Owner agent named
- [x] Source ID mapped
- [x] Allowed / forbidden files listed
- [x] Production boundary explicit
- [x] Verification commands explicit
- [x] No core file group conflict between A-wave slices
