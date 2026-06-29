# grill-gate — 澄清流程门（Plan + Execute SSOT）

> **不改** `grill-me` 等 skill 正文。漏洞在 Trellis 把澄清当 **写文件步骤**，而非 **block 等用户**。  
> 读者：Plan · Execute · 主会话派发者

**Leading word — block：** 流程触发澄清类 skill → 本相位 **block**，直到对话出现 **用户消息**。

---

## 何时 block

AC、边界、完成条件、架构二选一、用户授权 — 说不清且 frozen/ENTRY/INDEX/代码库 **不能** 唯一确定 → block。

**不 block：** 冻结卡或仓库已有明文答案（回报时 cite 路径）。

---

## block 期间（唯一合法动作）

1. **对话提问** — 优先 `AskQuestion`；否则一条消息一个阻塞问题
2. **停** — Plan 不 freeze；Execute 不进 RED；不写 `backend/` 生产代码
3. **用户回复后** — 才可记录决策或继续

**完成条件（解除 block）：** 用户消息直接回答阻塞点，或用户写明「按你推荐 / 你定」。

---

## 禁止（流程伪 grill）

| 禁止                                           | 为何                          |
| ---------------------------------------------- | ----------------------------- |
| 未问就写 `research/*-session.md` 自问自答      | 产出 ≠ 用户决策               |
| 写「用户认为…」「用户确认…」但 **无** 对话原文 | 伪造授权                      |
| 一次写满 Q1–Qn + 自编 A                        | 跳过 block                    |
| 为勾 plan.freeze / 过门禁而造 session          | 流程表演                      |
| Execute 新建 `grill-me-session.md`             | Plan 工件；Execute 只 live 问 |
| 说不清仍猜 scope 写码或冻结                    | 违反 gate                     |

---

## Plan（Phase 2a / 3）

`research/grill-me-session.md`（或 interview/brainstorm 等价）**仅当** 每个已决条目含：

- **问题**
- **用户原话**（或「用户：按推荐」）
- **落盘决策一句**

仍 open 的项 **不得** 进 frozen / ENTRY / §9。

**完成条件：** session 无「待用户确认」占位；或有 open items 且 **freeze 未勾该项**。

---

## Execute（Boot / slice 前）

- 只在对话问；**不** 新建 `research/*-session.md`
- block 解除前：禁止 RED、禁止生产代码
- 用户回复后：对话回报即可（**不**写 `execute-skill-reads.jsonl`）

**完成条件：** 能复述当前 slice AC；无未决阻塞点。

---

## 与 skill 的关系

| 场景                      | 遵守                       |
| ------------------------- | -------------------------- |
| 用户手动 `/grill-me`      | skill 原文；本 gate 不覆盖 |
| Plan/Execute **流程触发** | **必须** 本 gate           |

登记：`plan-skill-paths.yaml` · `execute-skill-paths.yaml` → `trigger_ref` 指向本文件。
