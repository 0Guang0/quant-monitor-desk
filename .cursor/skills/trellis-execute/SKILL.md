---
name: trellis-execute
description: >-
  Executes Trellis complex tasks one slice at a time.
  Boot reads ENTRY + research + routing table; RED/GREEN via /test-driven-development.
  Mid-flow only code/tests; finish with adversarial self-check (no prose/jsonl/txt).
---

# Trellis Execute

**Leading word — slice：** 一次只完成 INDEX §1 的一个 Step。

| 层级           | 文件                                                                   |
| -------------- | ---------------------------------------------------------------------- |
| 工程契约       | [principles.md](principles.md)                                         |
| **必做 skill** | [reference.md](reference.md) + `execute-skill-paths.yaml`              |
| **条件 skill** | [`agent-toolchain.md`](../../agent-toolchain.md) §Execute — 条件 skill |
| 全局规则       | [project-global.mdc](../../rules/project-global.mdc)                   |
| 澄清门         | `.trellis/spec/guides/grill-gate.md`                                   |
| **TDD**        | **`/test-driven-development`**（见 reference · RED/GREEN 必做）        |

**SSOT：** `frozen/*.md` + `EXECUTION_INDEX.md` + `implement.jsonl` · v4.1：`research/00-EXECUTION-ENTRY.md`

**证据 = 实际代码与测试结果**（自检修复后的 git 状态 + `uv run pytest -q`）。不单独落盘 handoff 表、txt、skill-reads jsonl。

---

## Phase 0 Boot（开工前 · 读清再动手）

| #   | 动作                                                                                                   | 完成条件                                            |
| --- | ------------------------------------------------------------------------------------------------------ | --------------------------------------------------- |
| 0a  | Read `agent-toolchain.md` + 本 skill + **`reference.md`** + `principles.md` + **`project-global.mdc`** | 必做/条件 skill 纪律已加载                          |
| 0b  | Read **Execution Bundle**（ENTRY 路由 + 上下文）                                                       | 见下表                                              |
| 0c  | GitNexus `impact()` 扫将改 symbol                                                                      | blast radius 已心里有数                             |
| 0d  | `validate-execute-boot <task-dir>`                                                                     | exit 0（v4.1 不要求 context-closure 等 prose 工件） |

### 0b 读什么（完整理解后再执行）

| 层                     | 路径                                                      | 作用                                           |
| ---------------------- | --------------------------------------------------------- | ---------------------------------------------- |
| **路由地图**           | `research/00-EXECUTION-ENTRY.md`                          | 目的 · 铁律 · §5.1 文件表 · §5.2/§5.3 读法     |
| **包内规格**           | ENTRY §5.1 登记的 **全部** `research/*`                   | Plan skill 产出（切片 AC、spec、架构等）       |
| **路由表（包外权威）** | `EXTERNAL-INDEX.md` §A + `implement.jsonl` **每一行**     | 活卡、ADR、契约 yaml、规则、参考采纳等上层权威 |
| **当前步**             | `to-issues-slices.md` **当前切片 §** + INDEX §1 当前 Step | 本刀范围与 AC                                  |

**不写**「读了哪些文件」清单；**不填** audit / bundle-gap / consolidation 表。

---

## 执行中途（每 slice）

```text
当前切片 § → impact() → Read /test-driven-development → RED → [DEBUG?] → GREEN → SLICE → 代码/测试 → INDEX [x]
```

- **读：** 当前切片 § · INDEX 当前 Step · §5.3 / EXTERNAL §B 仅当本步触及 · **RED/GREEN 前 Read `/test-driven-development`**
- **写：** 代码 · 测试 · INDEX / frozen 勾 `[x]`
- **禁止中途：** audit 报告 · handoff 长文 · `execute-evidence/*.txt` · `execute-skill-reads.jsonl` · 任何「已 Read skill X」落盘

RED/GREEN **按 `/test-driven-development`**（必做 · 见 [reference.md](reference.md)）；**条件 skill** 触发/细则见 [agent-toolchain.md](../../agent-toolchain.md) §Execute — 条件 skill。**证明在测试与代码里**，不在 txt。

---

## 收尾（全部步 `[x]` 后 · 交 Audit 前）

### 对抗性自检（执行者自己做 · 不落盘表）

对照 ENTRY §1/§2 + 当前切片 AC + 路由表权威，**不相信文档自述**，用代码与测试找遗漏：

1. diff 是否 silent 扩大 scope？
2. 每条 AC 是否有测试或等价可验证行为？
3. 活卡 Red Flags / 契约 fail-closed 是否在代码里体现？
4. 发现缺口 → **先修**（可修明显错误/问题）；修完再跑 `uv run pytest -q`

**可跳过自检**（仍允许 handoff）—— 正式关账由 **Audit A1–A8** 负责。自检是质量强化，不是填表门禁。

### Handoff 机械门

```bash
python .trellis/scripts/task.py validate-execute-handoff <task-dir>
```

通过条件（v4.1）：INDEX/frozen 步已 `[x]` · manifest-amend 链（若有）· **loop 四件套**（`task_track: complex` 时：`context_pack.json` · `loop_manifest.json` · `evidence_index.json` · `check_task_evidence` 绿）。**不要** `finish-work` 直到 Audit PASS。

缺口覆盖（下沉丢失 / 执行偏差 / 计划外）→ **Audit only** · `agents/audit-coverage-model.md`

---

## 禁止

多 step 一批 · 未按 `/test-driven-development` 走完 RED/GREEN 就勾 `[x]` · 改测试目的换绿 · slice 间填 audit/Plan 表 · **grill-gate 未解除就写码**
