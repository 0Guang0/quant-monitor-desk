# Agent 工具路由（场景 · 全员必读）

> **路径：** 仓库根 `agent-toolchain.md`  
> 角色**必做 skill 路径**见：`plan-skill-paths.yaml` · **`execute-skill-paths.yaml`（Execute 必做）** · `audit-skill-paths.yaml`  
> **Execute 必做相位/TDD 分轨：** `.cursor/skills/trellis-execute/reference.md` + `principles.md`（不在本文件重复）

## GitNexus MCP（按场景）

| 场景                       | 用                                                                | 不用               |
| -------------------------- | ----------------------------------------------------------------- | ------------------ |
| 不熟模块、找入口           | `query` + skill `gitnexus-exploring`                              | 全库盲 grep        |
| **改函数/类前**            | MCP `impact()` + `gitnexus-impact-analysis`                       | 直接改             |
| 提交前看改动面             | MCP `detect_changes()`                                            | 只看 git diff 肉眼 |
| 测试红、栈对不上、回归不明 | `systematic-debugging` → `diagnosing-bugs` → `gitnexus-debugging` | 反复猜改           |
| rename / 拆模块 / 提取     | MCP `rename` + `gitnexus-refactoring`                             | find-replace       |
| 不知道 MCP 参数            | `gitnexus-guide`                                                  | 乱试工具           |

**阶段锁死（非可选）：** Plan 1a/1b、Execute boot+改码、Audit 7.pre + 各维 ≥1 次 query/context — 见各 phase yaml。

## grill-gate（澄清类 skill · Plan + Execute）

流程触发 `grill-me` / `interview-me` 等 → **block 等用户回复**，不是写自问自答 session。细则：`.trellis/spec/guides/grill-gate.md`

| 场景                 | block 时做                                     | 禁止                      |
| -------------------- | ---------------------------------------------- | ------------------------- |
| Plan Phase 2a/3 澄清 | 对话提问；有回复后才写 `research/*-session.md` | 未问就写「用户认为…」     |
| Execute scope 不清   | 对话提问；解除前不进 RED                       | Execute 新建 session 文件 |

## Skill 歧义（相似项选一）

| 场景                   | 用                                                            | 不用                           |
| ---------------------- | ------------------------------------------------------------- | ------------------------------ |
| Plan 质问需求          | `grill-me` 等 + **grill-gate**（block 后再写 session）        | 未问用户就写 session           |
| Plan 垂直切片          | `to-issues` + `planning-and-task-breakdown`                   | 手写 MASTER §8 无切片          |
| Execute 先写失败测试   | **`/test-driven-development`**（必做 · 见 execute reference） | 先写实现                       |
| Execute 实现与测试规范 | `karpathy-guidelines` + `testing-guidelines`（必做）          | 自创风格                       |
| Execute 需求不明       | `grill-me` + **grill-gate**（条件 · 见下表）                  | 猜 scope · 写 session 自问自答 |
| Execute 验规范         | **等 Audit A1**                                               | `trellis-check`                |
| Audit 对抗性质疑       | 各维 `doubt-driven-development`（冻结在 audit-agent 模板）    | 只走 happy path                |

---

## Execute — 条件 skill（SSOT · 触发才 Read）

> **Execute 必做**（Boot/RED/GREEN/SLICE 相位、TDD 分轨、karpathy/testing）→  
> `.cursor/skills/trellis-execute/reference.md` + `principles.md` + `execute-skill-paths.yaml`

| Skill                               | 相位      | 路径（磁盘 · 权威见 yaml）                                  | 触发                                                         | 完成条件                                     |
| ----------------------------------- | --------- | ----------------------------------------------------------- | ------------------------------------------------------------ | -------------------------------------------- |
| `grill-me`                          | Boot      | `.claude/skills/grill-me/SKILL.md`                          | scope/AC/边界说不清 → **grill-gate**                         | 用户回复后解除 block                         |
| `systematic-debugging`              | DEBUG     | Superpowers `systematic-debugging/SKILL.md`                 | RED 意外 PASS · GREEN 仍 FAIL · 同错 ≥2 轮 · 栈与 INDEX 不符 | 根因已写明 → 回到 `/test-driven-development` |
| `diagnosing-bugs`                   | DEBUG     | `.claude/skills/diagnosing-bugs/SKILL.md`                   | systematic 后仍卡住                                          | 同上                                         |
| `gitnexus-debugging`                | DEBUG     | `gitnexus-debugging` skill                                  | DEBUG 链末栈/调用仍不明                                      | 同上                                         |
| `source-driven-development`         | GREEN     | `.agents/skills/source-driven-development/SKILL.md`         | 外部 API/契约/SDK · `specs/contracts` 新字段                 | 实现与契约一致                               |
| `deprecation-and-migration`         | GREEN     | `.agents/skills/deprecation-and-migration/SKILL.md`         | deprecate/remove/migrate/双轨 · 破坏性 API                   | 旧路径 fail-closed 或显式可用                |
| `observability-and-instrumentation` | SLICE     | `.agents/skills/observability-and-instrumentation/SKILL.md` | ops/写路径/pipeline · AC 要 log/metric/trace                 | 变更路径有可检索信号                         |
| `shipping-and-launch`               | pre-merge | `.agents/skills/shipping-and-launch/SKILL.md`               | Audit PASS 后 merge/PR 前（主会话）                          | 不替代 handoff/Audit                         |

### 条件 skill 细则（触发才 Read · 证据在代码/测试 · 不写 jsonl）

#### DEBUG

**触发：** RED 意外 PASS · GREEN 后仍 FAIL · 同错修 ≥2 轮 · 栈与 INDEX 不符

**顺序：** `systematic-debugging` → `diagnosing-bugs` → `gitnexus-debugging` → 回到 RED（仍按 `/test-driven-development`）

**完成条件：** 根因已写明；继续 RED/GREEN（不写 jsonl 落盘）。

#### source-driven-development

**GREEN 前 Read：** 外部 API/契约/SDK 语义；`specs/contracts` 新字段；adapter 与第三方对齐。

**不必：** 纯内部 refactor、仅改测试/注释。

**完成条件：** 实现与契约/文档引用一致（证据在代码与测试中）。

#### deprecation-and-migration

**GREEN 前 Read：** deprecate/remove/rename/migrate/双轨；public API 破坏性变更；registry tombstone。

**完成条件：** 旧路径显式可用或 fail-closed；迁移步骤在代码/测试可验证。

#### observability-and-instrumentation

**SLICE 前 Read：** ops/写路径/pipeline；AC 要求 log/metric/trace；`backend/app/ops/` 等。

**完成条件：** 变更路径有可检索信号；无无引用全局指标。

#### shipping-and-launch（pre-merge）

**主会话；** handoff 绿 + Audit PASS 后、merge/PR 前可选 Read。

**完成条件：** 不替代 handoff 门禁与 Audit 关账。

---

## Loop engineering（complex 轨道 · 与 Execute/Audit 对齐）

> **判定：** `task.json` → `meta.task_track: complex`（v4/v4.1 三件套默认 complex）· 详见 `AGENTS.md` §Loop engineering · `complex-task-planning-protocol.md` §0 Loop

| 阶段                | 产物                                             | 门禁                                               |
| ------------------- | ------------------------------------------------ | -------------------------------------------------- |
| **Plan freeze**     | `context_pack.json` · `loop_manifest.json`       | `validate-plan-freeze` 自动 `context_router`       |
| **Execute 中**      | 新测/新 docs/specs/backend 包                    | `loop_maintain.py --fix` · `authority_graph.yaml`  |
| **Execute handoff** | `evidence_index.json`（索引 execute/audit 证据） | `validate-execute-handoff` → `check_task_evidence` |
| **Audit 关账**      | `audit_matrix.json` · ledger                     | A7/A9 更新 loop_manifest AC 状态                   |

**v4.1 不变：** loop 管 **路由/索引/AC 机械关账**；Execute **不写** execute-evidence txt / skill-reads jsonl。

---

## Trellis CLI（常用）

| 场景              | 命令                                                              |
| ----------------- | ----------------------------------------------------------------- |
| Plan 冻结         | `python .trellis/scripts/task.py validate-plan-freeze <task-dir>` |
| Execute handoff   | `validate-execute-handoff`（v4.1：代码/测试 + `[x]`）             |
| 刷新 context_pack | `uv run python scripts/context_router.py --task <task-dir>`       |
| 地图/catalog 过期 | `uv run python scripts/loop_maintain.py`（`--fix` 写回）          |

## 读本文件之后

- **Plan** → `trellis-plan` + `plan-skill-paths.yaml`
- **Execute 必做** → `trellis-execute/reference.md` + `principles.md` + `execute-skill-paths.yaml`
- **Execute 条件** → 本文件 **§Execute — 条件 skill**
- **Audit** → `AUDIT.plan.md` + `audit-skill-paths.yaml` + `agents/*.md`
