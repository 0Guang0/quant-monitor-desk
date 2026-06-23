# R3Y-AUD-01 — R3X closed claims 反证

**Result:** WARN

**Worktree:** `quant-monitor-desk-wt-review-r3-post-r3x-strict-audit` @ `61436a51`  
**Agent:** `r3y-aud-01-closed-claims` · A5 completion + doubt-driven-development  
**Date:** 2026-06-23

---

## 目标与反证假设

**CLAIM（待反证）：** PROMPT_11–17 / R3X merge_gate 宣称的 FIXED / CLOSED / ALREADY_CLOSED 项均已进入 runtime path，并有可复现测试与 execute-evidence 支撑。

**反证假设：**

1. merge_gate_report 自述不可当事实；须 code trace + pytest + 原始 green.txt 三角验证。
2. PROMPT_15 伞测 `test_r3x_residual_open_items_closure.py` 可能只覆盖 Master Checklist 子集，其余靠「回归绿」空口闭合。
3. PROMPT_12/13 曾 defer 的项可能在 PROMPT_15 被标 FIXED 而无新增证据。
4. SYNC / PILOT / STAGE 类闭合项可能仍存在 adapter 或 raw INSERT 旁路。

---

## 读取文件（含 call path 追溯）

| 类别                       | 路径                                                                                                                                               |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| 派发 / 任务卡              | `research/parallel-audit-dispatch.md`, `docs/.../R3Y_post_r3x_strict_adversarial_audit.md` § R3Y-AUD-01                                            |
| PROMPT 卡                  | `PROMPT_11`–`PROMPT_17` under `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/`                                                                |
| Merge 自述（**非事实源**） | `.trellis/tasks/fix-round3-r3x-residual-open-items-closure/execute-evidence/merge_gate_report.md`                                                  |
|                            | `.trellis/tasks/fix-round3-data-source-routing-blockers/merge_gate_report.md`                                                                      |
|                            | `.trellis/tasks/fix-round3-db-write-validation-blockers/execute-evidence/merge_gate_report.md`                                                     |
|                            | `.trellis/tasks/fix-round3-post14-audit-staged-pilot/execute-evidence/merge_gate_report.md`                                                        |
|                            | `.trellis/tasks/fix-round3-ponytail-pilot-prep-bucket-a/execute-evidence/merge_gate_report.md`                                                     |
| Execute evidence 抽检      | `fix-round3-ponytail-pilot-prep-bucket-a/execute-evidence/DS-02-green.txt`（有真实 pytest 行）                                                     |
|                            | `fix-round3-post14-audit-staged-pilot/execute-evidence/slice1-pytest-green.txt`（35 dots，无逐用例名）                                             |
|                            | **PROMPT_15 任务目录：仅 `merge_gate_report.md`，无 `*-green.txt`**                                                                                |
| Runtime — route            | `backend/app/datasources/route_planner.py` L143/173/198/200                                                                                        |
| Runtime — sync             | `backend/app/sync/orchestrator.py` L127–204, `runners.py` L49–72/144–153/173–205/391–398/715–726                                                   |
| Runtime — pilot            | `backend/app/ops/live_pilot_phase2.py` `preview_live_pilot`, `live_pilot_phase3.py` `run_live_pilot_raw_only` L140–212                             |
| Runtime — stage            | `backend/app/layer1_axes/ingestion.py` L500–518 `_register_clean_file_registry_rows`; `storage/staged_evidence.py`（仅定义，**backend 无调用方**） |
| Runtime — write            | `backend/app/db/write_manager.py` `UNSUPPORTED_MODES` L52/395                                                                                      |
| 伞测                       | `tests/test_r3x_residual_open_items_closure.py`（18 cases）                                                                                        |
| 旁路测试仍存在             | `tests/test_sync_orchestrator.py` 多处 `adapter=` 直传（L175/299/328/372/401/517/557）                                                             |

---

## 核查方法（code trace + pytest）

### 必跑命令与完整输出

```bash
cd quant-monitor-desk-wt-review-r3-post-r3x-strict-audit
uv run pytest tests/test_r3x_residual_open_items_closure.py -q --tb=short
```

```
..................                                                       [100%]
```

- **exit code:** 0
- **collected:** 18 tests（`pytest --co -v` 核对）
- **耗时:** ~11.7s

### A5 证据抽检（最弱 2 行）

| 原声称                                                              | 复跑命令                                                                                                                        | exit      | 与 Execute 一致？                      |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------- | -------------------------------------- |
| PROMPT_15 merge_gate: `python -m pytest -q` exit 0                  | 未在本 issue 全量复跑（范围外）；伞测 18/18 绿                                                                                  | 0（子集） | **不可证** — 无 green.txt 存档         |
| PROMPT_15: ADV-R3X-SYNC-001 FIXED（orchestrator→DataSourceService） | code trace `orchestrator.run_incremental(..., datasource_service=...)` + `test_sync_orchestrator.py` 3 处 `datasource_service=` | —         | **部分** — adapter 旁路仍在            |
| PROMPT_15 execute-evidence `*-green.txt`                            | 目录列举                                                                                                                        | —         | **不一致** — 文件不存在，仅 merge 自述 |

### green.txt 真实性（2 件）

| 文件                                                                       | 判定                                                         |
| -------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `fix-round3-ponytail-pilot-prep-bucket-a/execute-evidence/DS-02-green.txt` | 合格 — 含具体 pytest 用例名与 PASSED                         |
| `fix-round3-r3x-residual-open-items-closure/execute-evidence/`             | **不合格** — 无 green.txt；merge_gate 仅粘贴 `# exit 0` 占位 |

---

## Findings

### [HIGH/WARN] F-01 — PROMPT_15 闭合证据链薄弱：73 项 FIXED 仅 18 项伞测 + 无 execute green.txt

- **Location:** `.trellis/tasks/fix-round3-r3x-residual-open-items-closure/execute-evidence/merge_gate_report.md` L149–154; `tests/test_r3x_residual_open_items_closure.py`
- **Description:** merge_gate 宣称 Master Checklist **0 OPEN / 73 闭合**，但任务 execute-evidence **仅有** merge_gate_report；Tests 节仅 `# exit 0` 注释，无终端捕获。伞测 18 条仅映射约 18 个 ADV ID，其余 55 项标为 FIXED 或 ALREADY_CLOSED 依赖「回归绿」或它处测试，**未在 PROMPT_15 证据目录可审计**。
- **Impact:** 无法独立证明 PROMPT_15 全量闭合；审计若采信 merge 自述则构成 false closure risk。
- **PoC:** `glob execute-evidence/*-green.txt` under PROMPT_15 task → 0 files；`pytest --co` → 18 ≠ 73。
- **Recommendation:** 协调者要求 PROMPT*15 补 `full-pytest-green.txt` + 按 checklist 行的 RED/GREEN 映射；伞测扩展或附 `test_r3x*\*` 交叉索引表。

### [HIGH/WARN] F-02 — ADV-R3X-SYNC-001「FIXED」但 adapter 旁路未禁绝

- **Location:** `backend/app/sync/orchestrator.py` L127–156, L166–204; `backend/app/sync/runners.py` L325–328; `tests/test_sync_orchestrator.py` L175+
- **Description:** `run_incremental` / `run_backfill` 在 `datasource_service` 非空时注入 `fetch_callable`（经 `DataSourceService.fetch`），但 **`adapter=` 参数仍公开**且与 `fetch_callable` 二选一。测试套件大量仍用 `adapter=` 走 `_fetch_with_guard`，**不经过 route planner / service 生产路径**。
- **Impact:** 生产集成若误传 `adapter=`，可绕过 PROMPT_12/15 路由审计与 `REQUESTED_SOURCE_OVERRIDDEN_BY_ROUTE` 记录。
- **PoC:** `orch.run_incremental(spec, adapter=_BackfillCountAdapter(), clean_table="t")` 仍合法（见 test_sync_orchestrator 既有模式）。
- **Recommendation:** 生产入口 fail-closed：非 test profile 禁止 `adapter=`；或文档降级 SYNC-001 为 PARTIAL 并在 registry 标 UNRESOLVED。

### [WARN] F-03 — PROMPT_12/13 defer 项在 PROMPT_15 标 FIXED 的追溯缺口

- **Location:** PROMPT_12 merge_gate L28–36（defer ADV-A2-002/004/009/010/012）vs PROMPT_15 merge_gate L85–89（同 ID **FIXED**）
- **Description:** PROMPT*12 @ `8961691a` 将 ADV-A2-002 等标 deferred；PROMPT_15 @ `ae542970` 声称同批 ID 已 FIXED（如 health_check stub、cninfo domains、tdx 工厂）。**代码侧部分属实**（`test_advA2_002*_`, `test*advA2_004*_`, `test*advA2_009*\*` 在伞测绿），但 **无 PROMPT_12→15 的增量 evidence 文件**证明何时、何 commit 闭合。
- **Impact:** 审计无法区分「PROMPT_12 已覆盖」vs「PROMPT_15 新修」；merge 叙事可能 overstated。
- **Recommendation:** closed-claim matrix 对跨 PROMPT 重复 ID 附 `git log -S` / commit SHA 列。

### [WARN] F-04 — ADV-R3X-PILOT-001/002、ADV-R3X-STAGE-001 无伞测回归

- **Location:** `live_pilot_phase3.py` L153–212（`service.fetch`）；`ingestion.py` L500–518；`tests/test_batch275_live_pilot_gate.py`；无 `test_r3x_residual_*` 条目
- **Description:** Code trace 支持 PILOT-001（`run_live_pilot_raw_only` → `preview_live_pilot` → `DataSourceService.fetch`）与 STAGE-001（Layer1 用 `_register_clean_file_registry_rows` + WriteManager，**非** `register_staged_file_registry_rows`）。但 **PROMPT_15 伞测未覆盖**；依赖 `test_batch275_live_pilot_gate.py` / `test_staged_pilot.py`（PROMPT_14/POST14 证据）。
- **Impact:** PROMPT_15 单独 merge 不能证明 pilot/stage 闭合；属 cross-PROMPT 证据依赖。
- **Recommendation:** 伞测增加 smoke 或 merge_gate 显式引用 POST14/PROMPT_14 test 名。

### [INFO] F-05 — ADV-R3X-WRITE-001 代码已修复且有 runtime 路径

- **Location:** `runners.py` L397 `source_used=fetch_result.source_id`（incremental）; L725（backfill shard）
- **Description:** `_write_clean` 默认 `spec.source_id`，但 fetch 成功路径显式传入 `fetch_result.source_id`。**与 merge 声称一致**；伞测未单列，由 `test_sync_orchestrator` / backfill 套件间接覆盖。
- **Verdict:** VERIFIED（code）；测试 PARTIAL。

### [INFO] F-06 — ADV-R3X-SYNC-003 CONFLICT_CHECK_SKIPPED 已进入 runtime

- **Location:** `runners.py` L144–153
- **Description:** `conflict_staging_table is None` 时 emit `CONFLICT_CHECK_SKIPPED` 事件。无伞测；`test_sync_orchestrator` 未断言该 event type。
- **Verdict:** VERIFIED（code）；测试 GAP。

### [INFO] F-07 — PROMPT_14/POST14 staged pilot 闭合证据较强（非 PROMPT_15）

- **Location:** `fix-round3-post14-audit-staged-pilot/execute-evidence/merge_gate_report.md` + `slice1-pytest-green.txt`
- **Description:** ADV-POST14-A-_ 多数有 `test*staged_pilot.py::test*_`逐条映射；A-004 移除 staged pilot 对`register_staged_file_registry_rows`双写。与当前 backend grep 一致（**仅**`staged_evidence.py` 定义，无生产调用方）。
- **Verdict:** VERIFIED for POST14 slice；PROMPT_15 对 STAGE-001 的闭合为 **继承** 关系。

---

## 反证结论（修复是否进入 runtime）

| 维度                    | 结论                                                                                                                                   |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **修复真实性（整体）**  | **PARTIAL** — 抽查的 route/write/pilot/stage 代码改动多数存在于 HEAD `61436a51`；但 PROMPT_15 73 项闭合 **不能** 仅凭 merge_gate 采信  |
| **测试覆盖**            | **GAP** — 伞测 18/73；12 项 ALREADY_CLOSED 无本 agent 独立全量回归记录                                                                 |
| **Evidence 可信度**     | **WARN** — PROMPT_15 无 green.txt；PROMPT_16/POST14 有合格样本                                                                         |
| **旁路**                | **WARN** — SYNC adapter= 仍可用；`register_staged_file_registry_rows` 仍存在于 API（仅测试/文档引用，生产 Layer1/staged_pilot 已绕行） |
| **merge report 当事实** | **拒绝** — 已用 code trace 纠偏多处                                                                                                    |

**AC 评分（PROMPT_15 Master Checklist 整体）：** **3/5** — 实现存在且伞测子集绿；追溯链缺 execute green + 大量 per-ID 测试缺口。

---

## 阻塞项 / 建议

### 不阻塞本 issue 单独 PASS 的理由

- 必跑伞测 18/18 绿；核心 route/write/pilot 代码 trace 与 merge **方向一致**；POST14/PROMPT_16 evidence 质量高于 PROMPT_15。

### 建议（协调者 / AUD-08）

1. **WARN 升级条件：** 若生产 sync 入口不禁止 `adapter=`，应将 ADV-R3X-SYNC-001 在 registry 回退为 UNRESOLVED。
2. 要求 PROMPT_15 补全 `execute-evidence/*-green.txt` 与 checklist→test 映射。
3. AUD-07 应量化「测试仅 import/存在性」比例；AUD-02/03/04 继续验证旁路。
4. **不因此 issue 单独 BLOCK pilot v2** — 但 AUD-08 应携带 SYNC-001 旁路 WARN。

---

## DOUBT 记录

- Cross-model：非交互子 agent，跳过（announce only）。
- merge_gate 73/73 闭合：**不可证**；降为「代码+子集测试支持多数 HIGH 项，证据链不完整」。
- v0 monolithic AUD-01 亦 WARN（SYNC-001）；本审计独立复现并扩展 evidence 抽检结论。
