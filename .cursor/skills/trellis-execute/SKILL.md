---
name: trellis-execute
description: "Complex-task Execute. MUST Read after task.py start. Blocks code until Phase 0 boot passes."
---

# Trellis Execute（v4 · 薄 skill）

> **读者：Execute** · **v4 必读：** `frozen/*.md` + `EXECUTION_INDEX.md` + `implement.jsonl` + `context_pack.json`  
> **v3 遗留：** `MASTER.plan.md` + `implement.jsonl`

## Phase 0 Boot

| #   | 动作                                                  | 产出                          |
| --- | ----------------------------------------------------- | ----------------------------- |
| 0a  | GitNexus query + `impact()` + `detect_changes`        | `gitnexus-execute-summary.md` |
| 0b  | Read frozen 卡 + EXECUTION_INDEX + implement **每条** | —                             |
| 0c  | Read `context_pack.json`                              | —                             |
| 0d  | append `execute-skill-reads.jsonl`                    | 首行本 skill                  |

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
