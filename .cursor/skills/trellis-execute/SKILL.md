---
name: trellis-execute
description: "Complex-task Execute. MUST Read after task.py start. Blocks code until Phase 0 boot passes."
---

# Trellis Execute（v4 / v4.1）

> **读者：Execute**  
> **v4.1：** `research/00-EXECUTION-ENTRY.md` + 包内 skill 产出 + `EXTERNAL-INDEX.md` §A；`frozen`/`EXECUTION_INDEX` 为薄指针  
> **v4.0 遗留：** `frozen/*.md` + `EXECUTION_INDEX.md` 全文

## Phase 0 Boot

| #      | 动作                                                                     | 产出         |
| ------ | ------------------------------------------------------------------------ | ------------ |
| 0a     | GitNexus `impact()`（改 symbol 前）                                      | —            |
| 0b-v41 | Read `research/00-EXECUTION-ENTRY.md` → 完成 **§5.2 开工必读** checklist | —            |
| 0b-v41 | Read `to-issues-slices.md` **当前切片** §                                | —            |
| 0b-v40 | Read frozen + EXECUTION_INDEX + implement **每条**                       | —            |
| 0c     | Read `implement.jsonl` slot2（通常 ENTRY）                               | —            |
| 0d     | append `execute-skill-reads.jsonl`                                       | 首行本 skill |

执行中：按 ENTRY **§5.3** / `EXTERNAL-INDEX` §B/C 情境路由打开源码与契约。

`validate-execute-boot <task-dir>` → exit 0（`context-closure.md`）。

## 门控速查（v4）

| 项   | 规则                                                                                    |
| ---- | --------------------------------------------------------------------------------------- |
| 逐步 | **EXECUTION_INDEX §1** Step ↔ 冻结卡 §9.x；证据 `execute-evidence/{step}-red/green.txt` |
| 测试 | 冻结卡 §10；注释对齐 purpose（**不可改 purpose**）                                      |
| 验收 | 索引 §2 Tier；B/C = **prod-path**（`QMD_DATA_ROOT=data`）                               |
| 过线 | RED FAIL + GREEN PASS + 证据 + `[x]`                                                    |
| 交接 | `validate-execute-handoff` → Audit；**勿** finish-work                                  |

## 每步

1. **RED** — `test-driven-development` → `{step}-red.txt`
2. **GREEN** — `karpathy-guidelines` + `testing-guidelines` → `{step}-green.txt`
3. **SLICE** — `incremental-implementation`；全库 `pytest -q` → 0

改 symbol 前：`impact()`。Skill 表以冻结任务卡 **§14 Execute Skill 冻结** 为准。

## 收尾

索引 §2 + 冻结卡 §11 → `execute-skill-evaluation.md` → `validate-execute-handoff` → Audit。
