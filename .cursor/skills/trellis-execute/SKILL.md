---
name: trellis-execute
description: "Complex-task Execute Phase 0 boot + §8.x step protocol. MUST Read first when task.py start entered Execute (MASTER.plan.md present). Blocks coding until boot artifacts exist."
---

# Trellis Execute Protocol

> **读者：Execute agent（复杂任务）**  
> **触发：** `task.py start` 后、`task.json.status=in_progress`、任务目录含 `MASTER.plan.md`  
> **禁止：** 未完成 Phase 0 即修改 `backend/`、`tests/`、`scripts/` 业务逻辑

Skill 路径表：`.trellis/spec/guides/execute-skill-paths.yaml`（Plan 冻结路径；Execute 按表 Read）。

---

## Phase 0 · Boot（门禁 — 无业务代码）

完成下列全部项后，在 `research/execute-boot.md` 末尾写 **`Phase 0 complete`**，并 append `research/execute-skill-reads.jsonl`。

**Manifest amend（E18）：** Phase 0/6.pre 发现 `implement.jsonl` 缺口 → `task.py add-context` + `research/manifest-amend.md` + **补读**后方能写业务代码。

门禁：`python .trellis/scripts/task.py validate-execute-boot <task-dir>` → exit 0。

| #   | 动作                                                                                                 | 产出                                              | 禁止跳过 |
| --- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------- | -------- |
| 0a  | GitNexus `query` + 将改 symbol 的 `impact()` + `detect_changes`                                      | `research/gitnexus-execute-summary.md`            | ✓        |
| 0a2 | **L2 闭包（E16）：** 对 MASTER §4/§6 触点 `impact(upstream)`                                         | `research/context-closure.md`                     | ✓        |
| 0b  | **Read 全文** MASTER §0–§12；**inline 以 MASTER 为准**                                               | `research/execute-boot.md` + `8.0-boot-reads.txt` | ✓        |
| 0b2 | Read `research/integration-ledger.md`；对 strategy≠inline 项按 **extract/for** 读 implement 路径     | 同上                                              | ✓        |
| 0c  | **Read 本文件** + `execute-skill-paths.yaml` 中 Boot 段 skill                                        | `execute-skill-reads.jsonl` 首行                  | ✓        |
| 0d  | **Read** `context_pack.json`（implement 槽位 2）+ `research/context-router-output.md`（loop 启用时） | `8.0-boot-reads.txt` 含 context_pack 条目         | ✓        |

**execute-boot.md 最低结构：**

```markdown
# Execute Boot — {slug}

## AC 摘要（来自 MASTER §2）

## §8 执行顺序

## Red Flags（来自 MASTER §7）

## §10 验收命令清单

## Phase 0 complete
```

**execute-skill-reads.jsonl 行格式（每 Read 一条）：**

```json
{"phase":"boot","skill":"trellis-execute","path":".cursor/skills/trellis-execute/SKILL.md"}
{"phase":"boot","skill":"gitnexus-impact","action":"impact(SymbolName)","risk":"LOW|MEDIUM|HIGH"}
```

---

## Phase 1 · 每 §8.x 步（垂直切片 — 禁止跨步批量编辑）

**Red Flag：** 单次编辑同时完成多个 §8 步 / >100 行且无中间 pytest → 停止，回退当前步。

### 1 · RED（必须先 FAIL）

1. **Read** `test-driven-development` @ paths yaml
2. 只写/启用 **本步** tracer 测试（完整正文在 `research/*-tests.md`）
3. 跑 MASTER 本步 **RED 命令** → **必须 FAIL/ERROR**
4. 写入 `research/execute-evidence/{step}-red.txt`（含 exit code + 末 20 行输出）
5. Append skill-reads：`{"phase":"8.x","skill":"test-driven-development","before":"RED"}`

### 2 · GREEN（最小实现）

1. **Read** `testing-guidelines` + `karpathy-guidelines` @ paths yaml
2. 若本步绑定 **source-driven-development**：Read 该 skill + MASTER/implement 指定 API 源文件
3. 写 **最小** 实现使本步 GREEN 命令 PASS
4. 写入 `research/execute-evidence/{step}-green.txt`
5. Append skill-reads：testing-guidelines、karpathy-guidelines（及 source-driven 若触发）

### 3 · SLICE（再进下一步）

1. **Read** `incremental-implementation` @ paths yaml
2. 跑 **全库** `pytest -q`（或 MASTER 指定）→ 必须 exit 0
3. 勾 MASTER §8.x **已执行** + 填 RED/GREEN 证据列
4. 可选：`python .trellis/scripts/task.py validate-execute-step <task-dir> 8.x`

### 4 · DEBUG（仅 RED 非预期）

1. **Read** `systematic-debugging` @ paths yaml
2. 写 `research/execute-debug/{step}.md`（根因 + 修复）
3. 不得 silent fix

---

## Phase 2 · 收尾（§9 / §10 / handoff）

1. GitNexus `detect_changes`（对照 `master` 或 task base_branch）
2. 跑 MASTER §9 四层 + §10 Tier；Execute prod-path 用 `QMD_DATA_ROOT=data`
3. Audit 独立环境：`QMD_DATA_ROOT=.audit-sandbox/data`（≠ Execute 证据库）
4. 写 `research/execute-skill-evaluation.md`（对照 skill-reads.jsonl，禁止纯自评）
5. `python .trellis/scripts/task.py validate-execute-handoff <task-dir>` → exit 0
6. §11 交接 Audit；**勿** `finish-work`

---

## trellis-implement 二选一（MASTER §12 写死）

| 模式       | 要求                                                          |
| ---------- | ------------------------------------------------------------- |
| **派发**   | 每 §8.x 可派 subagent；留 `research/trellis-implement-log.md` |
| **inline** | 主会话 Execute；§12 标 inline；boot 文件声明 inline           |

---

## 自检清单（handoff 前）

- [ ] `execute-boot.md` 含 `Phase 0 complete`
- [ ] `execute-skill-reads.jsonl` 覆盖 §12 必做 + 已触发条件 skill
- [ ] 每个已勾 §8 步有 `{step}-red.txt`（含 FAIL 信号）与 `{step}-green.txt`（含 PASS 信号）
- [ ] §12 **已读** 列必做 skill 全 `[x]`
- [ ] `validate-execute-handoff` exit 0
