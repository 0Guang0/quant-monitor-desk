---
name: trellis-execute
description: "Complex-task Execute. MUST Read after task.py start. Blocks code until Phase 0 boot passes."
---

# Trellis Execute（薄 skill）

> **读者：Execute** · **必读：** `agent-toolchain.md` + `MASTER.plan.md` + `implement.jsonl` + `context_pack.json`（**不读** `source-index.md`）

## Phase 0 Boot

| #   | 动作                                           | 产出                          |
| --- | ---------------------------------------------- | ----------------------------- |
| 0a  | GitNexus query + `impact()` + `detect_changes` | `gitnexus-execute-summary.md` |
| 0b  | Read MASTER §0–§11 + implement.jsonl **每条**  | —                             |
| 0c  | Read `context_pack.json`                       | —                             |
| 0d  | append `execute-skill-reads.jsonl`             | 首行本 skill                  |

`validate-execute-boot <task-dir>` → exit 0（仅校验 `context-closure.md`）。

## 门控速查

| 项   | 规则                                                             |
| ---- | ---------------------------------------------------------------- |
| 逐步 | **仅 §9.x**；证据 `execute-evidence/{step}-red/green.txt`        |
| 测试 | §5.1 路径；注释对齐 §5 purpose（**不可改 purpose**）             |
| 验收 | §5.4 四层 + §6 Tier；B/C = **prod-path**（`QMD_DATA_ROOT=data`） |
| 过线 | §9 步：RED FAIL + GREEN PASS + 证据 + `[x]`                      |
| 交接 | `validate-execute-handoff` → §10；**勿** finish-work             |

## 每 §9.x

1. **RED** — `test-driven-development`；测试须 FAIL → `{step}-red.txt`
2. **GREEN** — `karpathy-guidelines` + `testing-guidelines` → `{step}-green.txt`
3. **SLICE** — `incremental-implementation`；全库 `pytest -q` → 0
4. **DEBUG** — `systematic-debugging`（RED 异常时）

改 symbol 前：`impact()`。Skill 表以 MASTER §11 为准。

## 收尾

§5.4 + §6 → `execute-skill-evaluation.md` → `validate-execute-handoff` → Audit。
