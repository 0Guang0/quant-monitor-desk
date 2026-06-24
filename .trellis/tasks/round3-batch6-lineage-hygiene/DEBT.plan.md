# Repair/Debt Lite Plan — B01-LIN (round3-batch6-lineage-hygiene)

> **Playbook ID:** `B01-LIN` · **Agent:** `B01-LIN` · **Model:** `composer-2.5`  
> **task_track:** `debt-lite` · **Phase:** Plan only（本分支禁止 Execute / registry commit）

---

## Source of truth

| 项 | 值 |
| --- | --- |
| **Roadmap** | `PROJECT_IMPLEMENTATION_ROADMAP.md` Batch **3D.3** |
| **Registry（读）** | `docs/quality/ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` §2 · `docs/quality/ROUND3_BATCH6_021_PENDING_FIX_REGISTRY.md` |
| **Registry（写）** | `docs/AUDIT_DEFERRED_REGISTRY.md` · `docs/UNRESOLVED_ISSUES_REGISTRY.md` · `docs/RESOLVED_ISSUES_REGISTRY.md` — **仅 proposed delta；主会话批处理** |
| **协调** | `docs/quality/coordination/BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §2.5/§2.6/§3.8/§5.3/§8.3 |
| **Hardening** | `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_HARDENING_RULES.md` §1–§10 |
| **审计来源** | `docs/quality/adversarial_audit_report.md` · `.trellis/tasks/archive/2026-06/06-23-round3-post-r3x-strict-audit/review-evidence/R3Y-AUD-05-lineage.md` · `R3Y-AUD-07-test-quality.md` |
| **021 残余** | `.trellis/tasks/archive/2026-06/06-24-round3-021-layer3-snapshot/research/main-session-adversarial-recheck-021.md` |
| **base branch** | `master` @ `0bd9bf02` |
| **target branch** | `fix/round3-batch6-lineage-and-layer3-hygiene` |
| **worktree** | `C:\Users\Guang\Desktop\quant-monitor-desk-wt-b01-lin` |
| **Trellis task-dir** | `.trellis/tasks/round3-batch6-lineage-hygiene/` |

### Task ID → Registry ID 映射

| Roadmap Task ID | Registry / Audit ID | 清理阶段 | 关闭语义 |
| --- | --- | --- | --- |
| `R3D-L3-01` | `R3-B6-021-O-01` | Batch 6 | malformed `bars[]` fail-closed |
| `R3D-L3-02` | `R3-B6-021-O-02` | Batch 6 | 确定性重建全 row tuple 断言 |
| `R3D-LIN-01` | `ADV-R3X-LINEAGE-001` | Batch 6 | L3/L4 **contract-scoped** snapshot lineage pytest（非全量 DB 持久化） |
| `R3D-LIN-02` | `R3Y-LINEAGE-VR-001` | Batch 6 · AUD-05 | Layer2 VR→lineage 绑定；sandbox 不得 synthetic ID 冒充 |
| `R3D-TEST-01` | `R3Y-TEST-DEPTH-001` | Batch 6 hygiene · AUD-07 | **lineage 簇** per-ID runtime-strong pytest 或 wont-fix ADR |

---

## Boundary（Playbook §2.5 / §2.6）

### Owns（可写）

| 路径 | 用途 |
| --- | --- |
| `backend/app/layer3_chains/**` | L3 snapshot/lineage 卫生修复 |
| `backend/app/layer4_markets/lineage.py` · `market_structure.py`（窄改） | L4 lineage 与 L3 上游 ID 传播 |
| `backend/app/layer2_sensors/lineage.py` · `snapshot_builder.py` · `snapshot_writer.py`（窄改） | VR→lineage 绑定（`R3D-LIN-02`） |
| `backend/app/core/snapshot_lineage.py` | **仅**当 L2/L3/L4 共享校验需单点修复且无其它分支锁时 |
| `tests/test_layer3_snapshot_builder.py` | L3 卫生 + 确定性 + malformed |
| `tests/test_layer4_market_structure.py` | L4 lineage 深度（在 L3 切片内或 LIN-S3） |
| `tests/test_layer2_sensor_loader.py` | VR→lineage WM 路径断言 |
| `tests/test_snapshot_lineage_kernel.py` | 共享 kernel 回归（若触及） |
| `.trellis/tasks/round3-batch6-lineage-hygiene/**` | 计划 / 证据 / proposed registry delta |

### Must not own（禁止）

| 路径 / 行为 | 原因 |
| --- | --- |
| `backend/app/layer5_evidence/**` · `specs/contracts/layer5_evidence_contract.yaml` | **B01-023** 独占；冲突时 **023 优先** |
| `docs/AUDIT_DEFERRED_REGISTRY.md` 等三件套 **直接 commit 闭合** | 主会话 §7.4 批处理 |
| **Schema 扩大**（migration、新表列、contract 新必填字段） | 与 023 / Batch 6 migration 轨冲突 |
| `backend/app/ops/**` · `datasources/**` · `db/**` · registry YAML | Playbook §2.5 其它分支锁 |
| production clean write · live fetch 默认启用 · production-live 声称 | Hardening §1 |

### Production / data boundary

- Staged fixture / tmp_path DuckDB only；无 `data/duckdb/quant_monitor.duckdb` 写。
- 无新生产数据源；无全市场/全历史扫描。

### Explicit non-goals

- 不实现 L5 evidence chain ingestion（`023`）。
- 不闭合 `R3-B2.75-REQ2-EM` · `R3-PROMPT14-AKSHARE-VAL-01` · `B2.5-O-05`（属 C02/C04）。
- 不扩展 PROMPT_15 全量 73 项伞测深度（`R3D-TEST-01` 仅限 **lineage 簇**；其余 ID 写 wont-fix 指向 owner）。
- 不声称 `ADV-R3X-LINEAGE-001` **全量** cross-layer DuckDB lineage 写回已闭合（021/022 已 defer；本分支最多 **contract + staged envelope** 闭合）。

---

## Execute 工程纪律（冻结供 Execute agent）

**Boot 前 MUST Read：** `agent-toolchain.md` · `.cursor/skills/trellis-execute/SKILL.md` · `BATCH_01_HARDENING_RULES.md` · 本 `DEBT.plan.md` 全文。

| 规则 | 要求 |
| --- | --- |
| TDD | 每切片：RED → `execute-evidence/{slice}-red.txt` → GREEN → `{slice}-green.txt` |
| Ponytail | `backend/` · `tests/**` 同标准；最小 diff |
| 测试 docstring | 五字段（覆盖范围 / 测试对象 / 目的目标 / 验证点 / 失败含义） |
| GitNexus | 改符号前 `impact()`；提交前 `detect_changes()` |
| Registry | 仅 `research/proposed-registry-delta.md`；禁止 agent 直接 RESOLVED 行 |
| 全量 pytest | 每切片 GREEN 后 `uv run pytest -q` |

---

## Vertical slices（§2.7 `/to-issues` 等价）

> **顺序：** 垂直切片；禁止单文件水平扫完全部 ID。建议 Execute 序：**LIN-S1 → LIN-S2 → LIN-S3 → LIN-S4 → LIN-S5**。

| Slice | Source ID | AC（可验证） | Allowed files | Forbidden | Verification | Evidence path |
| --- | --- | --- | --- | --- | --- | --- |
| **LIN-S1** | `R3D-L3-01` / `R3-B6-021-O-01` | `_bar_for_trade_date` 对 `bars[]` 非 `dict` 元素 **raise** `Layer3SnapshotError`（禁止 `continue` 静默跳过）；新增 `test_layer3Snapshot_malformedBarElement_rejects` | `snapshot_builder.py` · `test_layer3_snapshot_builder.py` | schema/migration · L5 | `uv run pytest tests/test_layer3_snapshot_builder.py::test_layer3Snapshot_malformedBarElement_rejects -q` | `execute-evidence/LIN-S1-{red,green}.txt` |
| **LIN-S2** | `R3D-L3-02` / `R3-B6-021-O-02` | `test_layer3Snapshot_deterministicRebuild_sameInputsSameHash` 断言 **完整** `IndustryChainDailySnapshotRow` 字段 + 约定 lineage 字段（`parameter_hash` · `source_fetch_ids` · `source_content_hashes` · `upstream_snapshot_ids` 等）；两次 `build()` 全等 | `test_layer3_snapshot_builder.py`（实现无改或仅暴露 tuple 比较 helper） | 削弱既有断言 · L5 | `uv run pytest tests/test_layer3_snapshot_builder.py::test_layer3Snapshot_deterministicRebuild_sameInputsSameHash -q` | `execute-evidence/LIN-S2-{red,green}.txt` |
| **LIN-S3** | `R3D-LIN-01` / `ADV-R3X-LINEAGE-001` | L3 **与** L4 staged builder 产出 lineage envelope 满足 `LINEAGE_REQUIRED_FIELDS`；L4 `upstream_snapshot_ids` 与 L3 `snapshot_id` **传播** 有 runtime 测；补 L3 `upstream_snapshot_ids` 负例（空 fetch/hash）若缺 | `layer3_chains/**` · `layer4_markets/lineage.py` · `market_structure.py`（窄） · `test_layer3_snapshot_builder.py` · `test_layer4_market_structure.py` · `test_snapshot_lineage_kernel.py`（若需） | L5 · DB migration · 声称全量 DB lineage 闭合 | `uv run pytest tests/test_layer3_snapshot_builder.py tests/test_layer4_market_structure.py tests/test_snapshot_lineage_kernel.py -q -k lineage` | `execute-evidence/LIN-S3-{red,green}.txt` · `research/lin01-partial-closure-scope.md` |
| **LIN-S4** | `R3D-LIN-02` / `R3Y-LINEAGE-VR-001` | Layer2 WM 写路径：lineage envelope 的 `source_fetch_ids`/`source_content_hashes` **与** `validation_report` JSON 一致；**负向**：VR 含 `fetch-A`、envelope 填 `fetch-B` 须 fail-closed；禁止测试仅用 synthetic tuple 而不读 DB lineage 列 | `layer2_sensors/lineage.py` · `snapshot_builder.py` · `snapshot_writer.py`（窄） · `test_layer2_sensor_loader.py` | L5 · ops/staged · registry commit | `uv run pytest tests/test_layer2_sensor_loader.py -q -k "lineage or WriteManager"` | `execute-evidence/LIN-S4-{red,green}.txt` |
| **LIN-S5** | `R3D-TEST-01` / `R3Y-TEST-DEPTH-001` | 产出 `research/test-depth-report.md`：lineage 簇 ID 表（runtime-strong / upgraded / wont-fix）；对 AUD-07 **lineage 缺口**（L05-W1/W2）至少 1 条新 runtime-strong 或文档化 wont-fix；非 lineage 项（SYNC/CAP/mutation）→ wont-fix + owner | `tests/test_layer2_sensor_loader.py` · `tests/test_layer3_snapshot_builder.py` · `tests/test_layer4_market_structure.py` · `research/test-depth-report.md` | 改 PROMPT_15 伞测目的 · registry commit | 报告 + `uv run pytest tests/test_layer2_sensor_loader.py tests/test_layer3_snapshot_builder.py tests/test_layer4_market_structure.py -q` | `execute-evidence/LIN-S5-report.md` · `research/test-depth-report.md` |

### LIN-S4 实现提示（Plan 冻结，Execute 可选路径）

1. **首选（ponytail）：** 在 `Layer2SnapshotWriter` commit 前，若提供 `validation_report_id`，从 VR 行读取 `source_fetch_ids_json` / `source_content_hashes_json`，断言 ⊆ envelope（mirroring `layer1_axes/lineage.py` L77–107）。
2. **备选：** `Layer2LineageBuilder.build_from_validation_report(...)` 单入口；调用方不得手填 synthetic tuple。
3. **测试：** 扩展 `test_layer2Snapshot_writeViaWriteManager`（或同级）读取 `axis_snapshot_lineage` JSON 列，对标 `test_layer1Observation_lineageIncludesFetchIdsAndHashes`。

### LIN-S3 与 `ADV-R3X-LINEAGE-001` 闭合策略

| 子范围 | B01-LIN 可闭合？ | 证据 |
| --- | --- | --- |
| L3/L4 staged envelope + contract pytest | **是** | LIN-S3 pytest 绿 |
| L3/L4 production DuckDB lineage 表写回 | **否** | owner **B01-023** / Batch 6 migration；主会话 **re-defer** 子项或保持 DEFERRED |
| Registry `ADV-R3X-LINEAGE-001` → RESOLVED | **主会话** | 依赖 `research/proposed-registry-delta.md` + 上表分工 |

---

## Proposed registry delta（Execute 产出，主会话提交）

Execute 结束时写入 `research/proposed-registry-delta.md`（模板）：

```markdown
## Proposed closures (coordinator merge only)

| ID | Proposed status | Evidence | Residual / re-defer |
| --- | --- | --- | --- |
| R3-B6-021-O-01 | RESOLVED | LIN-S1 pytest + commit | — |
| R3-B6-021-O-02 | RESOLVED | LIN-S2 pytest | — |
| R3Y-LINEAGE-VR-001 | RESOLVED or PARTIAL | LIN-S4 pytest | 若仅 staged WM 路径闭合，注明 production fetch_log E2E defer |
| ADV-R3X-LINEAGE-001 | PARTIAL→RESOLVED* | LIN-S3 pytest | *全量 DB 写回 re-defer → 023 |
| R3Y-TEST-DEPTH-001 | PARTIAL | LIN-S5 report | 非 lineage 项仍 OPEN / wont-fix |
```

---

## Merge gate（Playbook §8.3）

```bash
uv sync --locked
# 切片验收（逐条 PASS 后）
uv run pytest tests/test_layer3_snapshot_builder.py -q
uv run pytest tests/test_layer4_market_structure.py -q
uv run pytest tests/test_layer2_sensor_loader.py -q -k "lineage or WriteManager"
uv run pytest tests/test_snapshot_lineage_kernel.py -q
# 全量
uv run pytest -q
uv run ruff check backend/app/layer2_sensors backend/app/layer3_chains backend/app/layer4_markets tests/test_layer2_sensor_loader.py tests/test_layer3_snapshot_builder.py tests/test_layer4_market_structure.py
uv run python -m compileall backend scripts tests
uv run python scripts/loop_maintain.py
```

**Evidence path:** `.trellis/tasks/round3-batch6-lineage-hygiene/execute-evidence/merge_gate_report.md`

**Track A 合并序：** WL 之后或与 WL 交换（§7.2 #2）；避让未合并 **B01-023** 的 `layer5_evidence` 冲突。

---

## 阻塞项与协调依赖

| # | 阻塞 / 风险 | 严重度 | 缓解 |
| --- | --- | --- | --- |
| **B-01** | **B01-023** 独占 `layer5_evidence/**`；本分支不得改 | **硬** | 只读 L5 fixture；冲突时 023 优先 |
| **B-02** | Registry 三件套 agent **禁止 commit 闭合** | **硬** | `proposed-registry-delta.md` → 主会话 §7.4 |
| **B-03** | `ADV-R3X-LINEAGE-001` **全量** DB lineage 与 023 / migration 重叠 | **中** | LIN-S3 仅 contract 闭合；残余 re-defer 写清 owner |
| **B-04** | LIN-S4 触及 `layer2_sensors` 与 **B01-SP3/DH2** 无冲突，但与未来 L2 功能扩展可能同文件 | **低** | Execute 前 `impact()`；窄 diff |
| **B-05** | `core/snapshot_lineage.py` 多分支共享 | **中** | 改前查 §2.5 锁；优先在 layer 内局部 guard |
| **B-06** | `R3Y-TEST-DEPTH-001` 全量 73 项超出 B01-LIN 边界 | **低** | LIN-S5 限定 lineage 簇 + wont-fix 表 |
| **B-07** | Playbook / manifest 未提交即开 worktree（§9） | **流程** | 主会话确认 playbook 已 merge |

**无硬阻塞 Plan 冻结：** 五项 registry ID 均可映射到垂直切片；Execute 可开工 pending B-01/B-02 纪律确认。

---

## Plan 质检（§3.9 checklist）

- [x] §3.1 共用底座已读并摘要入本文 Source / Boundary
- [x] §3.8 B01-LIN 索引**每一行**已入 DEBT.plan 或 §3.10 核对表（零遗留）
- [x] `manifest` §1.1 `B01-LIN` 分支/禁止项与本文一致
- [x] Playbook §5.3 精简线映射（`R3D-LIN-*`/`R3D-L3-*`/`R3D-TEST-01`）+ `layer5_evidence/**` 禁止已冻结
- [x] `GLOBAL_TASK_TEMPLATE` / `BATCH_01_HARDENING_RULES.md` §1–§10 边界已写入
- [x] `specs/context/authority_graph.yaml` layer2/3/4 邻接已核对（与 Boundary Owns 一致）
- [x] §2.5/§2.6 文件锁已抄入 Boundary
- [x] `/to-issues` 等价垂直切片表已冻结（§ Vertical slices）
- [x] 无 MASTER.plan（debt-lite 正确）
- [x] registry commit 禁止已明示；仅 `research/proposed-registry-delta.md`
- [x] 遗漏项已写回 DEBT.plan；复检零遗留

### §3.10 Plan 质检输出

| 路径 | 已入 DEBT.plan | 摘要一句 | 遗漏风险 |
| --- | --- | --- | --- |
| Playbook §3.1 协调/审计/registry | 是 | 共用底座 + hardening + Wave B registry | 低 |
| Playbook §3.8 `ADV-R3X-LINEAGE-001` | 是 | LIN-S3 contract-scoped；DB 写回 re-defer → 023 | 低 |
| Playbook §3.8 `R3Y-LINEAGE-VR-001` | 是 | LIN-S4 VR↔envelope fail-closed | 低 |
| Playbook §3.8 `R3-B6-021-O-01` / `O-02` | 是 | LIN-S1/S2 malformed + 全 tuple | 低 |
| Playbook §3.8 `R3Y-TEST-DEPTH-001` | 是 | LIN-S5 lineage 簇报告 + wont-fix | 低 |
| Playbook §3.8 `adversarial_audit_report.md` | 是 | AUD-05/07 母报告；子证据 R3Y-AUD-05/07 | 低 |
| Playbook §3.8 `layer3_chains/**` · `layer4_markets/**` · `layer2_sensors/**` | 是 | Boundary Owns + 切片 allowed | 低 |
| `BATCH_01_TASK_CARD_MANIFEST.md` §1.1 `B01-LIN` | 是 | debt-lite · 3D.3 · 禁 L5 | 低 |
| Playbook §5.3 精简线纪律 | 是 | 五 Task ID 映射；修复 malformed/lineage pytest | 低 |
| `ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` §2 | 是 | 五项待偿还入 slices | 低 |
| `ROUND3_BATCH6_021_PENDING_FIX_REGISTRY.md` | 是 | O-01/O-02 → LIN-S1/S2 | 低 |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` 3D.3 | 是 | R3D-LIN/L3/TEST 表对齐 | 低 |
| `BATCH_01_HARDENING_RULES.md` §1–§10 | 是 | staged-only · 禁 production-live 措辞 | 低 |
| `GLOBAL_TASK_TEMPLATE.md` | 是 | debt-lite 无 forward 卡；纪律并入 Boundary/Execute | 低 |
| `snapshot_lineage_contract.yaml` | 是 | contract-scoped；不扩 schema | 中 — Execute 不得加列 |
| `specs/context/authority_graph.yaml` layer2/3/4 | 是 | Owns 与 authority_graph 路径一致 | 低 |
| `R3Y-AUD-05-lineage.md` | 是 | LIN-S4 VR 绑定缺口 | 低 |
| `R3Y-AUD-07-test-quality.md` | 是 | LIN-S5 lineage 簇深度 only | 中 — 勿膨胀为全量伞测 |
| 021 adversarial recheck | 是 | LIN-S1/S2 malformed + tuple 来源 | 低 |

---

## Remaining deferred（Plan 阶段预判）

| ID | Execute 后预期 | Owner |
| --- | --- | --- |
| `ADV-R3X-LINEAGE-001` DB 写回子范围 | re-defer 或随 023 闭合 | B01-023 |
| `R3Y-TEST-DEPTH-001` 非 lineage 项 | wont-fix / Batch 6 其它 | 主会话 |
| `WAVE-B-HYG-02` registry 措辞 normalize | 可选 | 主会话 |

---

## Plan QC Agent-2 裁决（B01-LIN）

| 项 | 结果 |
| --- | --- |
| **Verdict** | **PASS** |
| **§3.8 零遗留** | 是（§3.10 已逐行核对） |
| **五切片全覆盖** | LIN-S1..S5 ↔ R3D-L3-01/02 · R3D-LIN-01/02 · R3D-TEST-01 |
| **可进 Execute LIN-S1** | **是** — pending B-01（禁 L5）/ B-02（registry 仅 proposed delta）纪律确认 |

---

_文档版本：2026-06-25 · B01-LIN Plan QC Agent-2 · debt-lite frozen PASS_
