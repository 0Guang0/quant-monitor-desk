# Vertical Slices — Round 3 Batch 2.5 (Plan 3.5 · to-issues)

> Parent: Trellis `06-20-round3-batch2-5-layer1-obs-ingest` / `R3-B2.5-L1-OBS-INGEST` / `018A`  
> 映射 MASTER §8.0–8.6 · 严格串行（Audit A0–A4 门控）

---

## Slice 1 — VS-1 — Execute boot & baseline

| 字段             | 值                                                 |
| ---------------- | -------------------------------------------------- |
| **Title**        | Boot + implement.jsonl 全读 + pytest 基线          |
| **Type**         | AFK                                                |
| **Blocked by**   | None — Batch 2 archived PASS                       |
| **MASTER**       | §8.0                                               |
| **User stories** | 执行者能安全进入五阶段摄取，不遗漏 manifest 上下文 |

### What to build

完成 Execute Phase 0 Boot：`implement.jsonl` 与 `integration-ledger` 全读、基线 pytest 绿、产出 `execute-boot.md` 与 boot 证据。不实现业务摄取逻辑。

### Acceptance criteria

- [ ] `research/execute-boot.md` 存在且记录 implement 全读
- [ ] `uv sync --locked` 成功
- [ ] `execute-evidence/8.0-boot-reads.txt` 与 `8.0-baseline.txt` 存在

---

## Slice 2 — VS-2 — Phase 0 contract & DB gate

| 字段           | 值                              |
| -------------- | ------------------------------- |
| **Title**      | Pre-ingestion DB/设计/契约 gate |
| **Type**       | AFK                             |
| **Blocked by** | Slice 1                         |
| **MASTER**     | §8.1 · AC-P0-1..4               |
| **Audit**      | A0                              |

### What to build

对照 018A §5 产出 `phase0_source_context_matrix.md` 与 `phase0_db_contract_gate.md`；跑通 Phase 0 pytest 集（含新增 gate 测试）；分类 schema.sql 滞后与 FRED/registry 对齐 gap；证明 `layer1_axes` 不 import `create_adapter`。

### Acceptance criteria

- [ ] Phase 0 指定 pytest 命令全绿
- [ ] 所有偏差标为 BLOCKER / DEFERRED / OUT_OF_SCOPE
- [ ] Audit A0 PASS

---

## Slice 3 — VS-3 — Phase 1 read-only inventory

| 字段           | 值                         |
| -------------- | -------------------------- |
| **Title**      | 只读 DB/data-root 基线清单 |
| **Type**       | AFK                        |
| **Blocked by** | Slice 2（A0 PASS）         |
| **MASTER**     | §8.2 · AC-P1-1..2          |
| **Audit**      | A1                         |

### What to build

只读 DB inspect，产出 `phase1_before_ingestion_inventory.json/.md`，覆盖 018A §8 Phase 1 关键表行数与 data-root 文件计数；全程零 mutation。

### Acceptance criteria

- [ ] 清单字段符合 `ops_db_inspect_contract.yaml`
- [ ] 明确标注 DB 为 fixture/staged/空 schema-only
- [ ] Audit A1 PASS

---

## Slice 4 — VS-4 — Phase 2 route dry-run

| 字段           | 值                                               |
| -------------- | ------------------------------------------------ |
| **Title**      | 指标 allowlist + route preview（无 fetch/write） |
| **Type**       | AFK                                              |
| **Blocked by** | Slice 3（A1 PASS）                               |
| **MASTER**     | §8.3 · AC-P2-1..3                                |
| **Audit**      | A2                                               |

### What to build

使用冻结指标 **`ENV-E1-DGS10`**（AC-P2-0）；生成 `phase2_route_preview.json/.md`；dry-run 前后 `axis_observation`/`fetch_log` 行数不变；disabled 源返回契约状态而非静默 fallback。

### Acceptance criteria

- [ ] 每个选中指标有 SourceRoutePlan
- [ ] `phase2_no_mutation_proof.md` 记录行数对比
- [ ] pipeline route 测试绿
- [ ] Audit A2 PASS

---

## Slice 5 — VS-5 — Phase 3 micro-fetch staging

| 字段           | 值                                                      |
| -------------- | ------------------------------------------------------- |
| **Title**      | 微摄取 → raw/fetch_log 证据（无 clean write）           |
| **Type**       | AFK（默认 staged/fixture）；**HITL** 若启用 live 外部源 |
| **Blocked by** | Slice 4（A2 PASS）                                      |
| **MASTER**     | §8.4 · AC-P3-1..3                                       |
| **Audit**      | A3                                                      |

### What to build

经 DataSourceService 完成单窗口 micro-fetch；持久化 route 证据、fetch_log、raw/file_registry；**不**写 clean `axis_observation`。默认使用 staged fixture（非 live FRED/QMT）。

### Acceptance criteria

- [ ] route 证据早于 fetch_log
- [ ] `axis_observation` 行数 Phase 3 前后不变
- [ ] ResourceGuard 在 fetch 前检查
- [ ] live 源须有用户授权证据路径（若使用）
- [ ] Audit A3 PASS

---

## Slice 6 — VS-6 — Phase 4 clean write + snapshots + lineage

| 字段           | 值                                                            |
| -------------- | ------------------------------------------------------------- |
| **Title**      | validation → WriteManager → observation → snapshots → lineage |
| **Type**       | AFK                                                           |
| **Blocked by** | Slice 5（A3 PASS）                                            |
| **MASTER**     | §8.5 · AC-P4-1..5, AC-TRACE-1                                 |
| **Audit**      | A4                                                            |

### What to build

将 staging 证据映射为 observation 行；经 DataQualityValidator、SourceConflictValidator（如适用）、DbValidationGate、WriteManager 写入 clean `axis_observation`；重建 feature/interpretation snapshot 与 `axis_snapshot_lineage`（含真实 fetch ids/hashes，staged 须标注）；post-inspect delta。

### Acceptance criteria

- [ ] validation 失败 / severe conflict / manual review 阻断 clean write
- [ ] lineage 非空 `source_fetch_ids` + `source_content_hashes`
- [ ] `phase4_inventory_delta.md` 仅预期表变化
- [ ] Audit A4 PASS

---

## Slice 7 — VS-7 — Final regression & handoff

| 字段           | 值                                     |
| -------------- | -------------------------------------- |
| **Title**      | 全量门禁 + registry + Batch 3 handoff  |
| **Type**       | AFK                                    |
| **Blocked by** | Slice 6（A4 PASS）                     |
| **MASTER**     | §8.6 · AC-GATE, AC-REG-1, AC-HANDOFF-1 |
| **Audit**      | A5                                     |

### What to build

跑 §10 Tier A/B；更新 deferred/resolved registry；写出 Batch 3 handoff 字段（ingestion type、allowed scope、limitations）。

### Acceptance criteria

- [ ] `pytest -q` 与 production_gate 绿
- [ ] `final_registry_update.md` 含 handoff 模板字段
- [ ] Audit A5 PASS

---

## HITL 说明

| 场景                               | 类型     | 处理                          |
| ---------------------------------- | -------- | ----------------------------- |
| 默认 staged/fixture 摄取           | AFK      | MASTER §0.2 已冻结            |
| Phase 3/4 启用 live QMT/FRED/Yahoo | **HITL** | 须用户授权证据；未授权则 STOP |
| 可选窄 CLI `qmd_layer1_ingest.py`  | **HITL** | MASTER 显式批准后才实现       |

## 依赖图

```text
S1 → S2 → S3 → S4 → S5 → S6 → S7
     A0   A1   A2   A3   A4   A5
```

对应 MASTER §5 与 `research/layer1-ingestion-gate-tests.md` / `layer1-ingestion-pipeline-tests.md`。
