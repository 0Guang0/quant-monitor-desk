# M-G1-03 协调者交接 — 主会话必读（Composer 2.5 派发制）

> **读者：** 下一主会话（**协调者**，不亲自写 Phase 1/2 业务代码）  
> **位置：** 仓库根目录 `M_G1_03_COORDINATOR_HANDOFF.md`（唯一协调交接 SSOT）  
> **用户裁决 @ 2026-07-04：** 认同 S03∥S04、S08–S12 五批并行；**整轮 M-G1-03 完成前主会话不得停下问用户是否继续**；整轮结束后停交用户**最终验收**。

---

## 1. 你在做什么（30 秒）

| 项           | 值                                                                                                                                       |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **票**       | M-G1-03 Layer1 + Sync 架构解耦                                                                                                           |
| **Trellis**  | `.trellis/tasks/07-04-m-g1-03-layer1-full/` · `status: in_progress`                                                                      |
| **结构**     | Phase 1（S01–S06）→ P1-GATE → P1 对抗审计×3 → P1 修复×1 → Phase 2（S07→S08–S12→S13）→ P2-GATE → Audit A1–A8 并行 → 修复×1 → 用户最终验收 |
| **你的角色** | 派发 agent → 验收 → 更新本文件 §6 进度 → **自动推进下一步**（不问用户）                                                                  |
| **硬约束**   | **零技术债** · **零阶段外置** · **禁止防御性工程**（§10.1）· 全部 agent `**composer-2.5`**（**禁止\*\* `composer-2.5-fast`）             |

**业务目标（一句话）：** 在 M-DATA-03 已闭合前提下，完成 Sync 子系统完整落地 + 62 指标真链，使 G1/K1/K2 **MCR ≥ R4**。

---

## 2. 权威文档（勿重复读全文 — 按层加载）

按 **context-engineering** 层级，协调者与子 agent 只加载**当前刀**所需：

| 层           | 路径                                                                                     | 何时读                                                                                                                                                      |
| ------------ | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| L1 规则      | `c:\Users\Guang\Desktop\全局规则.txt` · `.cursor/rules/project-global.mdc` · `AGENTS.md` | 每派发前协调者扫一遍；子 agent Boot 必读（所有角色必须全程遵守。并且对于本M-G1-03任务，整票任务全程不接受任何阶段外置与遗留技术债务。所有发现必须全部修复） |
| L2 计划      | `.trellis/tasks/07-04-m-g1-03-layer1-full/EXECUTION_PLAN.md`                             | 子 agent 全文；协调者按 Step 读锚点                                                                                                                         |
| L2 量化验收  | 同目录 `EXECUTION_INDEX.md` §0.1 L0–L4 · §1 当前行 · §2 AC 行 · §2.2/§2.3 GATE           | **验收 SSOT**                                                                                                                                               |
| L2 必读路由  | `EXECUTION_INDEX.md` §3 + `implement.jsonl` 每行                                         | 子 agent Boot                                                                                                                                               |
| L2 竖切      | `research/to-issues-slices.md`                                                           | 派发 Issue 文案                                                                                                                                             |
| L3 设计/契约 | §3 manifest 中 [2]–[5] 与当前 Step 相关文件                                              | 子 agent 按切片加载                                                                                                                                         |
| L4 证据      | pytest/脚本输出、隔离库日志                                                              | 验收时                                                                                                                                                      |

**禁止：** 协调者/session 亲自实现 S01–S13 业务代码（仅验收、派发、本文件 §6 勾进度、极薄元数据编辑）。

---

## 3. 子 agent 统一 Boot（与主会话亲自 Execute 一致）

每个 **Execute / Repair** agent 的 Task 描述**必须**包含：

```text
模型：composer-2.5（禁止 fast）
票：M-G1-03 · Trellis .trellis/tasks/07-04-m-g1-03-layer1-full
角色：<Execute-S0x | P1-ADV-n | Repair-P1 | Audit-Ax | Repair-Final>
Slice：<S01|…|S13>

Boot（按序 Read，未读完禁止写码）：
1. c:\Users\Guang\Desktop\全局规则.txt
2. agent-toolchain.md + .cursor/skills/trellis-execute/SKILL.md + reference.md + principles.md
3. EXECUTION_PLAN.md（当前 P1-xx / P2-xx 锚点）
4. EXECUTION_INDEX.md §1 当前 Step 行 + §2 对应 AC 五列卡 + §2.2/§2.3（若 GATE）
5. implement.jsonl 每一行（至少本步相关 + slot1/2）
6. frozen/M_G1_03_LAYER1_FULL.md
7. /test-driven-development + /testing-guidelines + /karpathy-guidelines
8. §3 manifest 中本步 for 列文件（勿一次加载 62 轴 YAML）

执行中途：GitNexus impact() → RED → GREEN → 更新 INDEX §1 [x] + 运行证据
禁止：改测试目的/目标换绿（可改测试实现，不可改证明什么）· seed/mock 冒充真链 · 阶段外置 · 技术债口头 defer
禁止：未请求需求的抽象、依赖、样板；测试堆无关 case
禁止：防御性工程（见 §10.1）— 发现缺陷须根因修复，不得嵌套/绕开/包一层糊弄
交付：改动文件列表 · 命令输出 · §1「量化 Done」对照 · 真实流程运行证据（非仅文档）
```

**Audit agent** 额外 Read：`agents/audit-boot-v4.2.md` · `agents/audit-coverage-model.md` · `AUDIT.plan.md` · 只读自己维度。

---

## 4. 派发与并行策略（用户已确认）

### 4.1 Phase 1 Execute

| 序  | Step        | Agent      | 并行     | Blocked by | 关账（协调者验收）                                                   |
| --- | ----------- | ---------- | -------- | ---------- | -------------------------------------------------------------------- |
| 1   | **S01**     | Execute×1  | 串行     | —          | §1 S01 Done 全勾 · 专测/脚本绿 · L4                                  |
| 2   | **S02**     | Execute×1  | 串行     | S01        | 同上                                                                 |
| 3a  | **S03**     | Execute×1  | **∥ 3b** | S02        | 分别验收后再 S05                                                     |
| 3b  | **S04**     | Execute×1  | **∥ 3a** | S02        | 同上                                                                 |
| 4   | **S05**     | Execute×1  | 串行     | S03+S04    | boundary GREEN                                                       |
| 5   | **S06**     | Execute×1  | 串行     | S05        | scheduler+五 job                                                     |
| 6   | **P1-GATE** | **协调者** | —        | S06        | `EXECUTION_INDEX.md` §2.2 八条 + `uv run pytest -q` + macro e2e 证据 |

### 4.2 Phase 1 对抗审计 → 修复

| 轮              | Agent           | 并行             | 模型                              |
| --------------- | --------------- | ---------------- | --------------------------------- |
| ADV-1 契约/边界 | P1-ADV-1        | 3 个**同时派发** | composer-2.5                      |
| ADV-2 机制/编排 | P1-ADV-2        | 同上             | composer-2.5                      |
| ADV-3 运行/冒充 | P1-ADV-3        | 同上             | composer-2.5                      |
| 汇总            | **协调者**      | —                | 建 finding ledger，**无阶段外置** |
| 修复            | **Repair-P1×1** | 串行             | composer-2.5 · 根因修尽           |
| 复验            | **协调者**      | —                | P1-GATE 仍满足 → 进 Phase 2       |

**ADV 派发要点：** 对照 `EXECUTION_PLAN` P1-GATE + §2.2；主动找缺口/漏洞/双轨真相/代理测冒充。

### 4.3 Phase 2 Execute

| 序  | Step              | Agent      | 并行         | Blocked by             |
| --- | ----------------- | ---------- | ------------ | ---------------------- |
| 1   | **S07**           | Execute×1  | 串行         | P1-GATE                |
| 2   | **S08** macro     | Execute×1  | **五批并行** | S07                    |
| 2   | **S09** COT       | Execute×1  | 同上         | S07                    |
| 2   | **S10** CN bar    | Execute×1  | 同上         | S07                    |
| 2   | **S11** US/crypto | Execute×1  | 同上         | S07                    |
| 2   | **S12** filings   | Execute×1  | 同上         | S07                    |
| 3   | **协调者**        | —          | 五批验收后   | 62 行覆盖无漏/无重复   |
| 4   | **S13**           | Execute×1  | 串行         | S08+…+S12              |
| 5   | **P2-GATE**       | **协调者** | —            | §2.3 + MCR G1/K1/K2≥R4 |

### 4.4 正式 Audit → 修复 → 停

| 轮           | Agent                                                        | 并行          |
| ------------ | ------------------------------------------------------------ | ------------- |
| A1…A8        | **8 个 Audit agent，一维一个**                               | **全并行**    |
| 汇总         | 协调者 ledger                                                | —             |
| Repair-Final | **1 个修复 agent**                                           | 串行 · 零遗留 |
| 复验         | `uv run pytest -q` · audit PASS · `validate-execute-handoff` | —             |
| **停止**     | **仅此时**请用户做**最终验收**                               | —             |

**禁止** `finish-work` 直到 Audit PASS（Trellis 铁律）。

---

## 5. 协调者验收清单（每 agent 回报后必做）

1. 对照 `EXECUTION_INDEX.md` §1 该行 **量化 Done** 是否可勾（有证据，非口头）。
2. **L4：** 所列专测/脚本命令 exit 0（非 skip；RED 占位已去除并实现）。
3. **L2–L3：** 契约/结构断言（如 executor 唯一、CLI 登记、无 layer fetch）。
4. **反防御性工程：** diff 无「只包一层/绕开/吞异常/旁路」而无根因修；去掉绕开层后问题不得复现（见 §10.1）。
5. **反冒充：** §2 五列卡「反冒充」列无命中。
6. 更新 **§6 进度表** → **立即派发下一步**（不问用户）。
7. 并行刀：等**该层全部**验收通过再进下一串行闸门。
8. **逐功能闭环（每刀/每批必满足，缺一即 FAIL）：**
   - [ ] 真实流程可运行（非 mock 糊弄、非仅文档声称）
   - [ ] 与本刀/本批 AC 一致，无未声明缺口
   - [ ] 对应测试/验收已跑且通过
9. **完成判定以实际代码与真实运行为准**，不以文档勾选或 agent 自述为准；须**完全完成**（无部分完成、无偏离、无漏洞/缺口），否则 **FAIL**。

**Pass ≠ 旧测绿。** 以 INDEX §1 RED/GREEN 关账列为准，不以代理测为准。

---

## 6. 进度（协调者维护 — 开工时快照）

> 新主会话：**先读本节 → 从第一个 `[ ]` 继续派发**。

| 阶段   | Step/闸门        | 状态  | 最后验收时间 | 备注                             |
| ------ | ---------------- | ----- | ------------ | -------------------------------- |
| P1     | S01              | `[ ]` | —            | RED stub 已建；registry 脚本占位 |
| P1     | S02              | `[ ]` | —            |                                  |
| P1     | S03              | `[ ]` | —            | 可与 S04 并行                    |
| P1     | S04              | `[ ]` | —            | 可与 S03 并行                    |
| P1     | S05              | `[ ]` | —            |                                  |
| P1     | S06              | `[ ]` | —            |                                  |
| P1     | P1-GATE          | `[ ]` | —            | 协调者人工 §2.2                  |
| P1     | ADV-1/2/3        | `[ ]` | —            | 可并行                           |
| P1     | Repair-P1        | `[ ]` | —            |                                  |
| P2     | S07              | `[ ]` | —            |                                  |
| P2     | S08              | `[ ]` | —            | 五批可并行                       |
| P2     | S09              | `[ ]` | —            |                                  |
| P2     | S10              | `[ ]` | —            |                                  |
| P2     | S11              | `[ ]` | —            |                                  |
| P2     | S12              | `[ ]` | —            |                                  |
| P2     | S13              | `[ ]` | —            |                                  |
| P2     | P2-GATE          | `[ ]` | —            | MCR R4                           |
| Audit  | A1–A8            | `[ ]` | —            | 8 agent 并行                     |
| Audit  | Repair-Final     | `[ ]` | —            |                                  |
| **终** | **用户最终验收** | `[ ]` | —            | **唯一允许问用户的停止点**       |

**已完成基建（勿重复）：** Plan frozen · `EXECUTION_INDEX` §1–§2 加固 · `task.py start` · `implement.jsonl` · M-DATA-03 CLOSED。

---

## 7. Task 工具派发模板（复制改 Slice）

```text
Task tool · subagent_type: generalPurpose（或 trellis-implement / trellis-check 若可用）
model: composer-2.5

<粘贴 §3 Boot 块>

本刀范围：EXECUTION_PLAN <P1-xx> + EXECUTION_INDEX §1 <Sx> 行全文。
关账命令：见 INDEX §1 GREEN 列。
完成后只返回：diff 摘要 · 命令 exit 码 · §1 Done 勾选对照 · 运行证据路径。
```

**并行示例（S03+S04）：** 同一消息发 **两个** Task，不同 `description`（S03 / S04），`model` 均为 composer-2.5；**等两个都回报**再验收并派 S05。

---

## 8. 协调者主循环（禁止中途问用户）

```text
while §6 存在未完成 Execute/Audit/Repair 行:
    确定下一刀（遵守 Blocked-by 与并行规则）
    派发 composer-2.5 agent(s)
    验收 → 更新 §6 → 写一行简短 dispatch log（可选 .trellis/tasks/.../coordinator-log.md）
当 §6 除「用户最终验收」外全 [x]:
    validate-execute-handoff + audit PASS 证据
    更新本文件 §6 终行
    停下 → 向用户提交关账材料（ledger · AC · pytest · MCR）
```

---

## 9. Suggested skills（下一主会话 / 子 agent）

| 角色              | 建议 invoke                                                                                         |
| ----------------- | --------------------------------------------------------------------------------------------------- |
| **协调者**        | `/context-engineering` · `trellis-execute`（验收对照）· `trellis-check` · `grill-me`（仅矛盾时）    |
| **Execute agent** | `trellis-execute` · `/test-driven-development` · `/testing-guidelines` · `gitnexus-impact-analysis` |
| **P1-ADV agent**  | `code-review-and-quality` · `security-and-hardening`（ADV-3）                                       |
| **Repair agent**  | `trellis-execute` · `debugging-and-error-recovery` · `无遗留`（`全局规则.txt`）                     |
| **Audit agent**   | `agents/audit-boot-v4.2.md` 路由 · `review` · 单维不切其他维                                        |

---

## 10. 红线与混淆处理

### 10.1 工程契约红线（`全局规则.txt` · 协调者与所有 agent 强制）

| 红线               | 要求                                                                                                                                                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **禁止过度工程**   | **禁止**未请求需求的抽象、依赖、样板                                                                                                                                                                                |
| **禁止堆测**       | **禁止**测试堆无关 case（只断言本步目的所需行为）                                                                                                                                                                   |
| **全局禁止改目的** | **禁止**为让测试绿而改 **目的/目标**（可改测试实现，不可改证明什么）                                                                                                                                                |
| **完成判定**       | **以实际代码与真实运行为准**，不以文档为准                                                                                                                                                                          |
| **完全完成**       | 真实流程下须能运行、无偏离、**无部分完成**（必须完全完成）、无漏洞/缺口；否则 **FAIL**                                                                                                                              |
| **禁止防御性工程** | 发现 xxx 问题后，**不得**用嵌套、绕开、包一层、吞异常、旁路、假数据等方式让表面通过；**必须**在共享根因处一次修掉（对齐 `全局规则.txt` 禁止捷径 · 绕过根因）。有意简化仅允许 `ponytail:` 注释并写明天花板与升级路径 |

**防御性工程（本票定义）：** 测试/审计/运行暴露了真实缺陷，却不去改**出错的那条机制**，而是在外层加 guard、换调用路径、缩小断言、mock 掉失败分支、复制一份「安全版」逻辑等，使**当前刀**变绿但**根因仍在**。验收与 Repair 须追问：「若去掉这层包装，原问题是否复现？」— 是则 **FAIL**。

### 10.2 每刀/每批完成条件（验收勾选 · 缺一即 FAIL）

- [ ] 真实流程可运行（非 mock 糊弄、非仅文档声称）
- [ ] 与本批 AC 一致，无未声明缺口
- [ ] 对应测试/验收已跑且通过

### 10.3 运行时混淆处置

| 情况                                                    | 动作                                                    |
| ------------------------------------------------------- | ------------------------------------------------------- |
| agent 想用 fast 模型                                    | **拒绝**，改 composer-2.5 重派                          |
| agent 想阶段外置/技术债                                 | **拒绝**，Repair 根因修                                 |
| agent 加未请求抽象/依赖/无关测试                        | **拒绝**，要求 ponytail 回退                            |
| agent 改测试 docstring 目的/目标换绿                    | **FAIL**，重派 Execute/Repair                           |
| agent 用防御性工程（包一层/绕开/吞异常/旁路）代替根因修 | **FAIL**，要求删除绕开层并在共享根因处真修后重派        |
| 文档已勾 [x] 但代码/流程未落地                          | **FAIL**，不以文档为准                                  |
| 部分完成却宣称本刀 Done                                 | **FAIL**，继续 Execute 直至完全完成                     |
| INDEX 与 PLAN 冲突                                      | **以 PLAN AC 为准**，同步修 INDEX（协调者派小修 agent） |
| pytest 全绿但 §1 Done / §10.2 未满足                    | **FAIL**，继续 Execute                                  |
| 并行刀一个 FAIL                                         | **不推进**下一串行步，派 Repair 或重跑该刀              |

---

_本文件由协调会话生成 @ 2026-07-04。进度以 §6 为准；计划/AC 以 `EXECUTION_PLAN.md` + `EXECUTION_INDEX.md` 为准。_
