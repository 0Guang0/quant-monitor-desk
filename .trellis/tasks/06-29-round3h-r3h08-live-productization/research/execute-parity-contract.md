# Execute 子 agent 强制双铁律（派发 SSOT）

> **用户裁决 @ 2026-06-29（合并表述）**  
> Execute 子 agent 须同时满足以下两条，**缺一不可**：

## 铁律 A — 与主会话模板完全一致

Execute 的**完整流程**必须与「主会话若亲自 Execute」**完全一致**：

- SSOT：`agent-toolchain.md` → `.cursor/skills/trellis-execute/SKILL.md` → `reference.md` → `principles.md` → `.cursor/rules/project-global.mdc` → 本任务 `research/00-EXECUTION-ENTRY.md`
- **禁止** legacy v3/v4.0 · **禁止**子 agent 简化版 / 跳步 / 一批多步
- **仅允许与主会话不同：** `git commit` / `git push` / `finish-work`（主会话在用户授权后处理）

## 铁律 B — 参考项目三等级 · 先 Read 源码再执行

必须根据 Plan 调研结论（`reference-adoption-r3h08.md`），在**每个切片 RED 之前**实际 Read `参考项目/**` 登记源码，再写 QMD 代码：

- 严格按 **L1 / L2 / L3 / architecture_only / forbidden** 执行（`specs/contracts/reference_adoption_guardrails.yaml`）
- **禁止**不打开参考项目源码、**禁止**不从零臆造 port/编排/解析逻辑
- **禁止** runtime import / sys.path / 执行期读参考路径（P0）
- 证据：矩阵/测试须 cite `参考路径 + 行号 + 等级`（见 §7 + `EXTERNAL-INDEX.md` §D）

---

## 1. 与主会话的差异（仅三项）

| 项                       | 主会话               | Execute 子 agent |
| ------------------------ | -------------------- | ---------------- |
| Boot · 切片 · TDD · 收尾 | trellis-execute 全文 | **相同**         |
| 参考源码 Read + 三等级   | 必做                 | **相同**         |
| commit / finish-work     | 可能                 | **禁止**         |

---

## 2. Phase 0 Boot（全部完成才进 Slice 1）

| #   | 必做                           | 路径 / 命令                                                                                                                                                                             |
| --- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0a  | Read                           | `agent-toolchain.md` · `trellis-execute/SKILL.md` · `reference.md` · `principles.md` · `project-global.mdc`                                                                             |
| 0b  | Read **Execution Bundle 全文** | `00-EXECUTION-ENTRY.md` · ENTRY §5.1 **每一个** `research/*` · `EXTERNAL-INDEX.md` §A · `implement.jsonl` **每一行** · `to-issues-slices.md` 当前 § · `EXECUTION_INDEX.md` §1 当前 Step |
| 0b+ | Read **本文件 + 参考门禁**     | **`execute-parity-contract.md`（本文件）** · `reference-adoption-r3h08.md` §7 · `EXTERNAL-INDEX.md` §D                                                                                  |
| 0c  | GitNexus                       | 将改 symbol `impact()`                                                                                                                                                                  |
| 0d  | 机械门                         | `python .trellis/scripts/task.py validate-execute-boot <task-dir>` **exit 0**                                                                                                           |

**Grill-gate：** 说不清 → `grill-gate.md` → 问用户 → 解除前禁止 RED。

**书面复述通过后方可 RED：** ENTRY §1 AC · 本步切片范围 · 禁止项 · §D 本步参考文件列表 · 各文件采纳等级。

---

## 3. 每 Slice 循环（一次只做 INDEX §1 一步）

```text
[铁律B] §D+§7 参考源码 Read（磁盘只读）
  → 当前切片 § → impact()
  → Read /test-driven-development
  → RED → [DEBUG?] → GREEN → SLICE
  → 代码/测试（qmd_owned · 含 cite）
  → INDEX [x]
```

### 3.1 相位必做 Read（`reference.md` · 与主会话相同）

| 相位          | 必做 Read                                                                 |
| ------------- | ------------------------------------------------------------------------- |
| Boot          | §2                                                                        |
| RED/GREEN     | `/test-driven-development` · `karpathy-guidelines` · `testing-guidelines` |
| DEBUG         | `systematic-debugging` → `diagnosing-bugs` → `gitnexus-debugging`         |
| GREEN（触发） | `source-driven-development` · `deprecation-and-migration`                 |
| SLICE         | `incremental-implementation`                                              |

### 3.2 禁止（铁律 A + B）

- 一批做完 INDEX 多步 · 未 RED 就 GREEN · 未 GREEN 就 `[x]` · 改测试目的换绿
- `execute-evidence/*.txt` · `execute-skill-reads.jsonl` · `context-closure.md`
- **不 Read 参考源码就从零造** · runtime import 参考树
- grill-gate 未解除就写码 · 跳 `validate-execute-boot` / `validate-execute-handoff`

### 3.3 证据

代码 + `uv run pytest -q`；触 backend/docs/specs → `loop_maintain.py --fix`

---

## 4. 收尾（顺序固定 · 与主会话相同）

1. 对抗性自检（不落盘）
2. `uv run pytest -q` exit 0
3. `validate-execute-handoff` exit 0
4. `detect_changes()` 摘要
5. **勿** finish-work · **勿** commit

---

## 5. 回报主会话

1. INDEX `[x]` 列表
2. 变更文件 + AC→测试
3. boot/handoff 验证输出
4. pytest 摘要
5. detect_changes 摘要
6. **参考 cite 清单**（路径+行号+等级）
7. grill-me 未决项（应为 0）

---

## 6. 主会话派发 prompt 必含句（原文）

```text
Execute 子 agent 强制双铁律：
(1) 完整流程与主会话亲自 Execute 完全一致（trellis-execute SSOT；仅禁止 commit/finish-work）
(2) 每个切片 RED 前必须 Read reference-adoption-r3h08.md §7 + EXTERNAL-INDEX.md §D 的参考项目源码，严格 L1/L2/L3，禁止不参考从零造
必读：research/execute-parity-contract.md
```
