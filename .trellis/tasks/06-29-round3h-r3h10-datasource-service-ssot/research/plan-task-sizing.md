# Plan 加固 — planning-and-task-breakdown

> **Skill:** `planning-and-task-breakdown` · **日期：** 2026-06-29

## 依赖图（已垂直切片）

```text
S10-BOOT（只读矩阵）
  ├→ S10-01 ─→ S10-03 ─→ S10-05 ─┐
  └→ S10-02 ─→ S10-04 ────────────┴→ S10-CLOSE
```

**串行纪律：** Wave 1 内禁止 R3H-10 ∥ R3H-07；切片内 S10-01/02 可在无文件锁冲突时同 PR。

---

## 任务规模评估

| 切片      | 规模     | 预估触达文件                                                             | 风险                     |
| --------- | -------- | ------------------------------------------------------------------------ | ------------------------ |
| S10-BOOT  | **XS**   | 0–1（证据 txt）                                                          | 低                       |
| S10-01    | **S**    | `orchestrator.py`, `runners.py`, `test_sync_orchestrator.py`             | 中 — 生产 profile 语义   |
| S10-02    | **S**    | `datasource_service_contract.yaml`, `test_data_cli_contract.py`          | 低                       |
| S10-03    | **XS**   | docs + 1 测                                                              | 低                       |
| S10-04    | **M**    | `interface_probe.py`, `test_datasource_service.py`                       | 中 — 旁路面              |
| S10-05    | **L→拆** | `ops/*_fetch_ports`, `datasources/fetch_ports/*`, `test_staged_pilot.py` | **高** — 建议**单独 PR** |
| S10-CLOSE | **XS**   | audit/registry 登记                                                      | 低                       |

**S10-05 过大信号：** 双轨收敛 + audit 登记；遵守「一 PR 一切片」时不得与 S10-04 混并。

---

## Checkpoint（每 2–3 切片）

| Checkpoint | 完成后                     | 验证                                             |
| ---------- | -------------------------- | ------------------------------------------------ |
| **CP-1**   | S10-BOOT + S10-01 + S10-02 | 全量 pytest；矩阵 OPEN 项 ≤4                     |
| **CP-2**   | S10-03 + S10-04            | `interface_probe` 矩阵行 ❌→✅ 或 rehearsal 明示 |
| **CP-3**   | S10-05 + S10-CLOSE         | STAGED-PILOT-SSOT CLOSED；解锁 R3H-07            |

---

## 风险与缓解

| 风险                                                                      | 影响 | 缓解                                      |
| ------------------------------------------------------------------------- | ---- | ----------------------------------------- |
| S10-05 diff 过大 review 困难                                              | 高   | 单独 PR；每源薄委托 + 测锚定              |
| runner 已有 `adapter or fetch_callable required` 与 orchestrator 语义重复 | 中   | S10-01 统一错误文案 + orchestrator 早失败 |
| 契约 active 后旧 draft 测试 RED                                           | 中   | S10-02 先 RED 契约 gate 再改 yaml         |
| 误删 pilot 模块                                                           | 高   | 切片 Out of scope 已写；只收敛实现        |

---

## planning-and-task-breakdown 验证清单

- [x] 每切片有验收标准（`to-issues-slices.md`）
- [x] 每切片有验证命令（pytest + evidence）
- [x] 依赖顺序正确
- [x] 无 XL 单片（S10-05 已标单独 PR）
- [x] Checkpoint 已定义
