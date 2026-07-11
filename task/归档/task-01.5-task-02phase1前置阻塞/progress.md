# task-01.5 · Progress

> **更新：** 2026-07-10  
> **状态：** 🟢 **ALL GREEN** — S1–S7 · Phase F ✅  
> **解锁：** **task-01.5 已绿，可开工 task-02 Slice 0-N**

---

## 1. 总览

| 维度 | 状态 | 说明 |
|------|------|------|
| 计划文档 | 🟢 | `task_plan.md` · `findings.md` · `note.md` |
| 查码 / GitNexus | 🟢 | impact 已记入 findings §2 |
| S1 指针清扫 | ✅ | 2026-07-09 |
| S2 ADR/文档 | ✅ | 2026-07-09 |
| S3 沙箱统一 | ✅ | 2026-07-10 · CP-2 |
| S4 Tier 重命名 | ✅ | 2026-07-10 · CP-2 |
| S5 backfill 交易日 | ✅ | 2026-07-10 · CP-3 · AUD-DOUBT-01～16 关账 |
| S6 legacy CLI 删除 | ✅ | B12 2026-07-10 |
| S7 B11 复杂度重构 | ✅ | 2026-07-09 |
| S7+ P2/P3 可观测性 | ✅ | 2026-07-09 |
| Phase F 关账 | ✅ | AUD-F-01/02 · FIND-5-01 · 2026-07-10 |
| `uv run pytest -q` | 🟢 | exit 0（Phase F 复验） |
| phase-scripts rg 卫生 | 🟢 | `check_task015_s3_s4_rg_compliance.py --strict` PASS |

---

## 2. 会话日志

### 2026-07-10 · Phase F 整票关账

- **AUD-F-01：** 复核 `findings.md` §3 TEMP A1–A10、B11–B19 全 **已修复**（B1–B10 按设计保留）。
- **AUD-F-02 / FIND-5-01：** 统一 §9/§10 措辞；`task-02/progress.md` 写解锁行。
- **验证：** `uv run pytest -q` exit 0 · CP-4 满足。

---

### 2026-07-10 · S6 B12 legacy CLI 删除关账

- 删 `raise_retired_legacy_command` · `run_limited_production_entry` 退役桩。
- 契约/测试改「CLI 无此命令」；`rg` 零命中（task 文档除外）。
- **验证：** `uv run pytest -q` exit 0 · `test_dataCliContract_sandboxCleanWriteNotRegistered`

---

### 2026-07-10 · S3–S5 关账 + AUD-DOUBT + 测试卫生对齐

- **S5：** orchestrator/scheduler/baostock `truncate_to_cap=True`；CLI fail-closed；`bounded_backfill_cap.yaml` closure 扩展。
- **AUD-DOUBT-01～16：** 见 `findings.md` §9.1b；pytest 全绿。
- **testing-guidelines：** 删 `test_s3_s4_task_compliance.py`（artifact-guard）；rg 迁 `phase-scripts/check_task015_s3_s4_rg_compliance.py`。
- **验证：** `uv run pytest -q` exit 0 · `phase-scripts/... --strict` PASS。

---

### 2026-07-09 · S7+ 可观测性 P2/P3 + 安全体检收尾

- **P2：** `run_context.py` · `requested_by` 贯通写入审计。
- **P3：** `write_telemetry.py` stderr JSON。
- **验证：** `uv run pytest -q` exit 0。

---

### 2026-07-09 · S7 B11 复杂度重构关账

- C901 清零 · ADR-004 修订 · pytest 全绿。

---

### 2026-07-09 · S1∥S2 实现关账

- 指针/ADR 清扫 · pytest 全绿。

---

## 3. 切片 checklist（与 task_plan 同步）

| 切片 | 状态 | 证据路径 | AC-CLOSE-2 |
|------|------|----------|------------|
| S1 A1–A10 | ✅ | `rg` 零命中 · pytest | N/A |
| S2 B15–B17 + ADR-011 | ✅ | ADR 修订 | N/A |
| S3 B13 | ✅ | `phase-scripts/check_task015_s3_s4_rg_compliance.py --strict` · `test_resolveMatrixDataRoot_*` | N/A |
| S4 B14/B18 | ✅ | `live_prod_source_tiers.py` · rg harness 零命中 | N/A |
| S5 B19 | ✅ | `test_bounded_backfill_cap.py` · orchestrator 4 片测 · CP-3 | 见 `note.md` §S5 |
| S6 B12 | ✅ | `test_dataCliContract_sandboxCleanWriteNotRegistered` · rg 零命中 | N/A |
| S7 B11 | ✅ | C901 · ADR-004 | N/A |
| S7+ P2/P3 | ✅ | `note.md` §S7+ | 见 `note.md` |
| Phase F | ✅ | AUD-F-01/02 · FIND-5-01 · CP-4 | N/A |

---

## 4. task-02 解锁

**task-01.5 已绿，可开工 Slice 0-N**（2026-07-10）

条件已全部满足：

1. 上表全部 ✅（含 Phase F）
2. `findings.md` §3 / §9.3 无本票「待修复」
3. `uv run pytest -q` exit 0
4. `task-02-layer1-full/progress.md` 已同步解锁行

**说明：** §9.2 跨票项已 **迁入 task-02 §7**（仍开放 · 禁止再阶段外置）；**AUD-DOUBT-12** 本票已关（`incremental_gold_path_*`）。不阻塞本票关账。

---

## 5. 测试记录

| 日期 | 命令 | 结果 |
|------|------|------|
| 2026-07-10 | `uv run pytest -q` | exit 0（Phase F） |
| 2026-07-10 | `uv run pytest -q` | exit 0 |
| 2026-07-10 | `uv run python phase-scripts/check_task015_s3_s4_rg_compliance.py --strict` | exit 0 |
| 2026-07-09 | `uv run pytest -q` | exit 0（S7+） |
