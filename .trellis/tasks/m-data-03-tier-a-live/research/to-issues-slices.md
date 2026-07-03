# M-DATA-03 — `/to-issues` 垂直切片（Plan R2）

> **SSOT：** 切片 AC 仅本文件 · 用户 AC：`plan-revision-r2.md` §2  
> **R1 基线：** 已交付；证据归档 `research/archive/non-plan/execute/`

---

## R2 依赖图（SSOT · 开发/合并统一）

```text
S-R2-EVIDENCE
  ├→ S-R2-F0 ──┐
  └→ S-R2-B2 ──┼→ S-R2-DISPATCH → S-R2-ACCEPT → S-R2-CI
               └→ (F0 ∥ B2 可并行开发；merge 均须在 DISPATCH 之前)
```

| 规则          | 说明                                                            |
| ------------- | --------------------------------------------------------------- |
| 开发并行      | F0 agent ∥ B2 agent（不同文件组）可在 EVIDENCE merge 后同时开工 |
| DISPATCH 阻塞 | `Blocked by: S-R2-EVIDENCE`；不得与 EVIDENCE 并行               |
| 合并顺序      | **EVIDENCE → (F0 ∥ B2) → DISPATCH → ACCEPT → CI**（强制）       |
| 文件锁        | 见 `parallel-dispatch-protocol.md` §6                           |

---

## R2 切片总表

| Slice             | What to build                           | Acceptance criteria                                                                                                  | Blocked by              | 测试 / 证据                                                                                            |
| ----------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------ |
| **S-R2-EVIDENCE** | `live_tier_a_evidence_v1` manifest 落盘 | 契约测覆盖 11 `source_bindings`；**一次** `--report` run 产生 11 份 `live_tier_a_evidence_manifest.json`（每源一份） | —                       | `test_live_tier_a_evidence_contract.py` · `loop_maintain --fix` 登记                                   |
| **S-R2-F0**       | 四族 profile；删 SKIP                   | 11 源 F0 非 FAIL/BLOCKED；无 skip 路径                                                                               | S-R2-EVIDENCE           | `test_data_health_*`                                                                                   |
| **S-R2-B2**       | acceptance 接 `validate_table`          | 11 源按 `source_bindings`                                                                                            | S-R2-EVIDENCE           | `test_tier_a_live_b2_acceptance.py`                                                                    |
| **S-R2-DISPATCH** | 去平行 registry；mootdx matrix          | 金路径唯一；matrix 含 mootdx；**无** `_live_sync_registry` / mock 旁路（grep + 测）                                  | S-R2-EVIDENCE           | dispatch 测 · `detect_changes`                                                                         |
| **S-R2-ACCEPT**   | `--report` JSON + 11/11 live + E2 + MCR | exit 0；11 行；每源 E2 inspect 非 FAIL；MCR C3/D1/E1/E2/F0/B2→R4 引用 `r2-tier-a-live-accept-evidence.md`            | S-R2-F0 · B2 · DISPATCH | `test_tier_a_live_acceptance_report.py` · `archive/non-plan/execute/r2-tier-a-live-accept-evidence.md` |
| **S-R2-CI**       | `.github/workflows`                     | nightly `--quick`；workflow_dispatch；**失败**上传 `failure_artifact`                                                | S-R2-ACCEPT 本地绿      | workflow 文件                                                                                          |

**首步机械：** S-R2-EVIDENCE 创建 `required_tests` 三文件后 `uv run python scripts/loop_maintain.py --fix`。

---

## 每源 R2 AC（统一验收层）

| #   | 验证点                                               |
| --- | ---------------------------------------------------- |
| 1   | `live_tier_a_evidence_manifest.json` 符合 contract   |
| 2   | sync COMPLETED + clean 行 ≥ 1                        |
| 3   | B2 `validate_table` 满足 `source_bindings`           |
| 4   | E2 `DbInspector.inspect()` **非 FAIL**（11/11）      |
| 5   | F0 四族 profile 非 FAIL/BLOCKED                      |
| 6   | `failure_class` 按 `failure_class_canonical` mapping |
| 7   | **禁止 SKIP** / inspect-only-without-health          |

---

## Out of scope

- 新 migration · Layer · Round4 · 主库 · Tier B/C cron · 阶段外置
