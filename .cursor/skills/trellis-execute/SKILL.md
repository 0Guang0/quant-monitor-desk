---
name: trellis-execute
description: >-
  Executes Trellis complex tasks one slice at a time with RED/GREEN evidence.
  Use when in_progress, after task.py start, on EXECUTION_INDEX or frozen steps,
  or dispatching trellis-implement. RED reads test-driven-development; SLICE
  reads incremental-implementation; scope unclear triggers grill-gate block.
---

# Trellis Execute

**Leading word — slice：** 一次只完成 INDEX §1 的一个 Step。

| 层级       | 文件                                            |
| ---------- | ----------------------------------------------- |
| 工程契约   | [principles.md](principles.md)                  |
| 条件 skill | [reference.md](reference.md)                    |
| 澄清门     | `.trellis/spec/guides/grill-gate.md`            |
| 路径表     | `.trellis/spec/guides/execute-skill-paths.yaml` |

**SSOT：** `frozen/*.md` + `EXECUTION_INDEX.md` + `implement.jsonl` · v4.1：`research/00-EXECUTION-ENTRY.md`

---

## Phase 0 Boot（任务级一次）

| #   | 动作                                                         | 完成条件                                            |
| --- | ------------------------------------------------------------ | --------------------------------------------------- |
| 0a  | Read `agent-toolchain.md` + 本 skill + `principles.md`       | 能复述当前 slice AC 与边界                          |
| 0b  | Read `implement.jsonl` 每一行；v4.1：ENTRY §5.2 + 当前切片 § | 无盲区；有盲区 → **grill-gate block**               |
| 0c  | GitNexus `impact()` 扫将改 symbol                            | blast radius 已记录                                 |
| 0d  | append `execute-skill-reads.jsonl`                           | 含 `trellis-execute` · `trellis-execute-principles` |
| 0e  | `validate-execute-boot <task-dir>`                           | exit 0                                              |

---

## 每 slice

```text
impact() → RED → [DEBUG?] → GREEN → SLICE → 证据 + [x]
```

### RED — Read `test-driven-development`

1. Read `test-driven-development`
2. Read `testing-guidelines` + `karpathy-guidelines`；写/改 `test_*` + 五字段 docstring
3. INDEX **RED 命令** → **必须 FAIL**
4. `execute-evidence/{step}-red.txt`

**完成条件：** RED 失败 + 证据在盘。禁止写正式实现。

### DEBUG（条件）

触发：RED 意外 PASS · GREEN 后仍 FAIL · 同错修 2 轮 · 栈与 INDEX 不符

→ [reference.md §DEBUG](reference.md#debug) → 回到 RED

**完成条件：** 根因已写明；`execute-skill-reads.jsonl` 含 DEBUG skill；再跑 RED。

### GREEN — `test-driven-development` 的 GREEN 步

1. Read `karpathy-guidelines` + `testing-guidelines`
2. **ponytail** 最小正式代码使 RED 变绿
3. 触发则必 Read：[reference.md](reference.md) 条件节
4. **GREEN 命令** → **必须 PASS**
5. `execute-evidence/{step}-green.txt`

**完成条件：** GREEN PASS；已触发条件 skill 已 Read。

### SLICE — Read `incremental-implementation`

1. Read `incremental-implementation`
2. 触发则必 Read：`observability-and-instrumentation`
3. `uv run pytest -q` → exit 0
4. 勾 `[x]`；`execute-skill-reads.jsonl` 追加本步 skill

**完成条件：** 全库 pytest 绿；测试 **目的/目标** 未为通过而改写。

改 symbol 前：`impact()`。

---

## 收尾

| #   | 动作                          | 完成条件       |
| --- | ----------------------------- | -------------- |
| H1  | `execute-skill-evaluation.md` | 存在           |
| H2  | `validate-execute-handoff`    | exit 0         |
| H3  | Audit A1–A8                   | 勿 finish-work |

pre-merge（主会话）：handoff 绿 + Audit PASS 后可选 `shipping-and-launch` → [reference.md](reference.md#shipping-and-launch-pre-merge)

---

## trellis-implement

子 agent：`.cursor/agents/trellis-implement.md` — 与本 skill 一致；不 commit。

## 禁止

多 step 一批 · 无 RED/GREEN 勾 `[x]` · 先正式代码后 `test-driven-development` · 改测试目的换绿 · 跳过已触发条件 skill · Matt `/implement` · **grill-gate 未解除就写码**
