# Execute 阶段 Skill 候选词典（v4.2 默认 · v4.1 legacy）

> **读者：Plan agent**（冻结 Execute Skill 栈时查阅）  
> **Execute agent 不读本文** — 只认 **`execute-skill-paths.yaml`** + `trellis-execute/SKILL.md`

## 0. 定位（v4.2）

| 层级                           | 内容                                                |
| ------------------------------ | --------------------------------------------------- |
| **本文**                       | Skill **候选词典**                                  |
| **`trellis-execute/SKILL.md`** | Boot 读 `EXECUTION_PLAN`（v4.2）或 ENTRY 包（v4.1） |
| **`EXECUTION_INDEX.md` §1/§2** | 步骤 · AC · Tier                                    |

## 1. v4.2 典型必做栈

```text
trellis-execute（Boot 读 EXECUTION_PLAN + implement.jsonl + INDEX）
/test-driven-development（每 slice RED/GREEN）
incremental-implementation（每 slice SLICE）
karpathy-guidelines · testing-guidelines
reference.md + principles.md + agent-toolchain.md §Execute（条件 skill）
```

## 2. v4.1 legacy 栈（归档/在途只读）

```text
trellis-execute（Boot 读 ENTRY + research + EXTERNAL §A + 路由表）
…（同上 TDD 栈）
```

---

## 3. 条件 skill（见 agent-toolchain.md §Execute）

| Skill                               | 绑定      | Plan 冻结建议         |
| ----------------------------------- | --------- | --------------------- |
| `source-driven-development`         | GREEN     | **条件**              |
| `deprecation-and-migration`         | GREEN     | **条件**              |
| `observability-and-instrumentation` | SLICE     | **条件**              |
| `systematic-debugging`              | DEBUG     | **条件**              |
| `diagnosing-bugs`                   | DEBUG     | **条件**              |
| `grill-me`                          | Boot      | **条件** → grill-gate |
| `shipping-and-launch`               | pre-merge | **条件**              |

触发细则 → `agent-toolchain.md` §Execute — 条件 skill（**总表 + 细则**）+ `execute-skill-paths.yaml` `conditional_reads`。

---

## 4. 候选 Skill 词典

| Skill                                      | 典型绑定                                      | Plan 建议                   |
| ------------------------------------------ | --------------------------------------------- | --------------------------- |
| **`/test-driven-development`**             | 每 slice RED/GREEN（**必做** · 含系统化流程） | 复杂任务 → **必做**         |
| addy **incremental-implementation**        | 每 slice SLICE                                | **必做**                    |
| addy **source-driven-development**         | 指定切片                                      | **条件**                    |
| addy **deprecation-and-migration**         | 删改/迁移                                     | **条件**                    |
| addy **observability-and-instrumentation** | ops/写路径                                    | **条件**                    |
| Superpowers **systematic-debugging**       | DEBUG                                         | **条件**                    |
| addy **diagnosing-bugs**                   | DEBUG 加深                                    | **条件**                    |
| **trellis-implement**                      | 子 agent                                      | **必做** 或 inline **不用** |
| **grill-me**                               | scope 不清                                    | **条件** → grill-gate block |

---

## Legacy

v3/v4.0 **MASTER §12** → `templates/plan.freeze.legacy-v3-v40.md`
