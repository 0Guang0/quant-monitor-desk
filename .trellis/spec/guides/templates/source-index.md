# 来源索引 — {{任务标题}}

> **Plan / Audit 读本文件** · Execute 只读 `implement.jsonl` + `context_pack.json`  
> 替代已删除的 `input-inventory.md` 与 `original-plan-trace.md`（legacy 任务可保留旧文件）

---

## A. 血缘追溯

| 字段          | 值                                                 |
| ------------- | -------------------------------------------------- |
| Round / Batch | `{{ROUND_* / Batch N}}`                            |
| Item ID       | `{{019}}`                                          |
| 任务卡        | `docs/implementation_tasks/{{ROUND}}/{{NNN}}_*.md` |
| Batch 地图    | `{{ROUND*_BATCH_IMPLEMENTATION_MAP.md}}`           |
| gate / 分支   | `{{gate}}` / `{{feature/...}}`                     |

### AC 映射 → MASTER §4

| 任务卡        | MASTER AC | 验证链 |
| ------------- | --------- | ------ |
| {{§9 预期 1}} | AC-1      | §9.1   |

### 路径纠偏

{{无则写「无」}}

---

## B. 输入 manifest（E1 · implement.jsonl 来源）

| 路径                                     | 类别   | manifest  | extract / for |
| ---------------------------------------- | ------ | --------- | ------------- |
| `docs/implementation_tasks/.../NNN_*.md` | 任务卡 | required  | Plan          |
| `docs/modules/{{module}}.md`             | spec   | required  | AC-x          |
| `backend/app/...`                        | 接线   | inherited | §9.x          |
| `tests/test_{{feature}}.py`              | 测试   | deferred  | §5.1          |

---

## C. 六类覆盖自检

| 类别 | 路径                    | [ ] |
| ---- | ----------------------- | --- |
| 决策 | `ROUND_*/DECISIONS.md`  |     |
| 规则 | `GLOBAL_*.md`           |     |
| 架构 | `docs/architecture/...` |     |
| 需求 | 任务卡 + MASTER §3      |     |
| 契约 | `specs/contracts/...`   |     |
| 接线 | 前置 handoff            |     |

**索引完整**

---

## D. 机器路由

由 `uv run python scripts/context_router.py --task <dir>` 写入 **`context_pack.json`**（权威）。本段不重复列举；Audit 可读 JSON 或运行 router 查看摘要。

---

## E. implement.jsonl 槽位

1. `MASTER.plan.md` · 2. `context_pack.json` · 3. `trellis-execute/SKILL.md` · 4+ ledger `required`
