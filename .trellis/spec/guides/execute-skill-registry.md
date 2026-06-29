# Execute 阶段 Skill 候选词典

> **读者：Plan agent**（填 MASTER §12 时查阅）  
> **Execute agent 不读本文** — 只认任务内 **MASTER §12 Execute Skill 冻结清单**  
> **Plan 协议：** [complex-task-planning-protocol.md §2.4 / §7.2](./complex-task-planning-protocol.md)

---

## 0. 定位（与 MASTER §12 的关系）

| 层级                | 内容                                                   |
| ------------------- | ------------------------------------------------------ |
| **本文**            | Skill **候选词典**                                     |
| **MASTER §8–§10**   | **Execute 验收契约**（Plan 冻结；Execute 只认 MASTER） |
| **AUDIT.plan §2**   | **Audit 维度验证矩阵**（A1–A8；audit-sandbox）         |
| **MASTER §12**      | Execute Skill 冻结：必做/条件/不用 + 绑定 §8           |
| **MASTER §8**       | 每步做什么；Skill 列须与 §12 一致                      |
| **implement.jsonl** | spec / 源码路径                                        |

**Execute 禁止：** 按本文「触发路由表」自行决定是否 `@` skill。未在 §12 列出或标 **不用** 的 skill 不得使用。

---

## 1. Plan 填 §12 时的典型必做栈

复杂任务 §12 **至少**应覆盖（标 **必做** 或说明 **不用** 理由）：

```text
test-driven-development
incremental-implementation（每 slice SLICE 必做）
karpathy-guidelines · testing-guidelines
systematic-debugging · diagnosing-bugs（条件）
source-driven-development · deprecation-and-migration · observability-and-instrumentation（条件）
trellis-implement 或 inline（二选一）
```

**不在 Execute §12：** trellis-check、ponytail-review、verification-before-completion → **AUDIT.plan.md §1**。

---

## 2. 候选 Skill 词典

| Skill                                          | 典型绑定             | Plan 填 §12 建议                                           |
| ---------------------------------------------- | -------------------- | ---------------------------------------------------------- |
| Superpowers **test-driven-development**        | §8/§9 每步 RED       | 复杂任务 → **必做**                                        |
| addy **incremental-implementation**            | 每 slice SLICE       | Trellis slice → **必做**（见 `execute-skill-paths.yaml`）  |
| addy **source-driven-development**             | §8 指定步            | 外部 API/契约 → **条件**                                   |
| addy **deprecation-and-migration**             | §8 删改/迁移步       | 破坏性变更 → **条件**                                      |
| addy **observability-and-instrumentation**     | ops/写路径步         | 可观测交付 → **条件**                                      |
| Superpowers **systematic-debugging**           | DEBUG 分支           | **条件**                                                   |
| **diagnosing-bugs**                            | systematic 后仍卡住  | **条件**                                                   |
| Matt **`/implement`**                          | —                    | Execute **禁止**（用 trellis-execute + 上表）              |
| **trellis-implement**                          | 派发                 | **必做** 或 inline **不用**（二选一）                      |
| **trellis-check**                              | Audit A1             | **Execute 不用** → AUDIT §1 Skill + **§2 A1 行**           |
| Superpowers **verification-before-completion** | Audit A5 / Repair    | **Execute 不用** → AUDIT §2 A5；Repair 复跑 **MASTER §10** |
| addy **security-and-hardening**                | §8 指定步 / Audit A3 | 无 auth/密钥 → Execute **不用**                            |
| addy **browser-testing-with-devtools**         | §8 UI 步             | 无 UI → **不用**                                           |
| addy **doubt-driven-development**（Execute）   | §8 指定步            | Plan **5d 必做**；Execute 仅 §12 写明步 **条件**           |
| Superpowers **requesting-code-review**         | 大 PR                | 默认 **不用**；用户要求则 **条件**                         |
| mattpocock **handoff**                         | context 将爆         | 默认 **不用**                                              |
| **trellis-before-dev**                         | Execute 启动         | Plan 5c 已做 → Execute **不用**                            |

**禁止并行：** TDD + mattpocock tdd；Execute 阶段重复跑 Audit 专用 skill（trellis-check / verification-before-completion）。

**User Rule（始终 · 须写入 MASTER §12，不得仅依赖 Cursor 全局 rule）：** karpathy-guidelines、testing-guidelines、GitNexus impact（AGENTS.md）

---

## 3. addy Skill 说明（Plan 写 §12 时参考）

### incremental-implementation

`test-driven-development` 管 RED/GREEN；incremental 管 **slice 合入纪律**（全量 pytest、scope 不漂）。Trellis 每 INDEX §1 step 的 SLICE 相位 **必 Read** — 与是否跨文件无关。

### source-driven-development

Plan SDD 定验什么；source-driven 定按官方文档怎么写。§12 **条件**行须写：绑定 §8.x + 文档 URL。

### doubt-driven-development

- **Plan 5d（必做）：** 主会话对抗审查 §6–8 → 修订 MASTER §7/§8/§12 + **AUDIT §1/§2** → 记 plan.freeze。
- **Execute：** 仅当 §12 某行 **条件** 且绑定具体 §8 步（如 migration 幂等声称前）。**子 agent 禁止。**

### api-and-interface-design

**Plan Phase 4**，非 Execute 默认。产出在 MASTER §6。

### context-engineering

不 invoke；jsonl + MASTER 单源即落地。

---

## 4. 禁止事项

- Execute 读本文并按触发条件**自选** skill
- Execute 使用 §12 未列或标 **不用** 的 skill
- 子 agent 内 doubt-driven-development
- 未跑 MASTER §10 就 finish-work
- **未跑 RED 或未填 RED 证据就勾选 §8「已执行」**
- **在 MASTER §8 内嵌完整测试文件（>2 个 `def test_*`）**
- **跳过 Phase 0 Boot 直接写业务代码**（handoff 脚本会 BLOCK）
- **未 append execute-skill-reads.jsonl 就声称已 Read skill**

---

## 6. Execute Boot Skill 路由（Plan 填 §12「路径」列）

路径权威表：`.trellis/spec/guides/execute-skill-paths.yaml`

| Phase     | Skill                                           | 默认 repo 路径                        |
| --------- | ----------------------------------------------- | ------------------------------------- |
| Boot      | trellis-execute · principles · grill-me（条件） | `.cursor/skills/trellis-execute/`     |
| Boot      | gitnexus-impact                                 | AGENTS.md + MCP                       |
| RED       | test-driven-development                         | 见 yaml                               |
| RED/GREEN | karpathy-guidelines / testing-guidelines        | 见 yaml                               |
| GREEN     | source-driven-development                       | 见 yaml（条件）                       |
| GREEN     | deprecation-and-migration                       | 见 yaml（条件）                       |
| SLICE     | incremental-implementation                      | 见 yaml                               |
| SLICE     | observability-and-instrumentation               | 见 yaml（条件）                       |
| DEBUG     | systematic-debugging → diagnosing-bugs          | 见 yaml（条件）                       |
| pre-merge | shipping-and-launch                             | 见 yaml（条件；主会话）               |
| 派发      | trellis-implement（子 agent，非 skill）         | `.cursor/agents/trellis-implement.md` |

**Mechanical gates:** `validate-execute-step`（逐步）· `validate-execute-handoff`（交接）

---

## 5. §12 冻结清单行模板（Plan 复制进 MASTER）

```markdown
| Skill                          | 本任务 | 绑定 §8 | 触发（写死）             | `@` 指令                         | 已执行 |
| ------------------------------ | ------ | ------- | ------------------------ | -------------------------------- | ------ |
| test-driven-development        | 必做   | 8.1–8.n | 每步写代码前             | 按 Superpowers TDD：先写失败测试 | [ ]    |
| incremental-implementation     | 必做   | 8.1–8.n | 每切片 GREEN 后再下一片  | 本切片测过再动下一文件           | [ ]    |
| source-driven-development      | 条件   | 8.2     | 仅 §8.2 实现 DuckDB 事务 | 查 DuckDB 官方文档后写 migrate   | [ ]    |
| systematic-debugging           | 条件   | 当前步  | pytest RED               | 按 systematic-debugging 排查     | [ ]    |
| security-and-hardening         | 不用   | —       | 本任务无 auth            | —                                | —      |
| trellis-check                  | 不用   | —       | → Audit A1               | —                                | —      |
| verification-before-completion | 不用   | —       | → Audit A5 / Repair      | —                                | —      |
```
