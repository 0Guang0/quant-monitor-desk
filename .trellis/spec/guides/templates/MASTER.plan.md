# 执行计划 — {{任务标题}}

> **LEGACY（plan_protocol v3）：** 新任务默认 v4 — 使用 `frozen/*.md` + `EXECUTION_INDEX.md` + `AUDIT.plan.md`。见 `complex-task-planning-protocol.md` §0.0。

> **Execute（v3）：** 本文件 + `implement.jsonl` + `context_pack.json`  
> **Audit（v3）：** `AUDIT.plan.md` · **索引：** `research/source-index.md` 或 `EXECUTION_INDEX.md`

**契约：** Plan 已冻结垂直切片（§8）、测试契约（§5）、停止条件（§1.5）。Execute 不得重新切片，不得改 §5 冻结的测试 purpose。

---

## 0. 元信息

| 字段            | 值                                               |
| --------------- | ------------------------------------------------ |
| 任务 slug       | `{{slug}}`                                       |
| 索引            | `research/source-index.md` · `context_pack.json` |
| Audit           | `AUDIT.plan.md`                                  |
| analysis_waiver | `false`                                          |

### 0.1 Execute 必读 manifest（E4）

Phase 0 **逐条 Read `implement.jsonl`**（清单以文件为准；**不**写 boot-reads 或「已读」自述，Audit 用 diff/代码验）。  
动态闭包：`research/context-closure.md`。

---

## 1. 目标与目的

### 1.1 目标 | 1.2 目的 | 1.3 前置 | 1.4 约束

- **目标：** {{可交付物}}
- **目的：** {{业务价值}}
- **前置：** {{gate / 前置 batch}}
- **约束：** {{staged-only / 禁止 live / …}}

### 1.5 停止条件（可追加 · loop 必填）

> **与 §1.4 约束不同：** 触发即 **中断 Execute**（禁止继续勾 §9、禁止 finish-work）。  
> 下表 **1–4 为常见示例，不是上限**；Plan/用户须按本任务 **追加** 行（如：预算耗尽、同一 §9 步重试 >N 次、外部依赖不可用）。  
> **至少 1 条**须为「本任务特有、可判定」的停止条件，避免 agent 无限跑。

| #   | 事件                        | 处理                   |
| --- | --------------------------- | ---------------------- |
| 1   | {{gate 未关}}               | 禁止 start 或立即停止  |
| 2   | {{HARD_STOP / 写库失败}}    | 中止；回滚；不勾 GREEN |
| 3   | {{scope 偏离任务卡}}        | 退回 Plan              |
| 4   | {{RED 异常 / 非本步全库红}} | 停当前 §9 步           |
| 5+  | {{用户/任务自定义}}         | {{…}}                  |

### 1.6 原计划归并

| 来源           | 内容                    |
| -------------- | ----------------------- |
| `NNN_*.md`     | {{任务卡边界}}          |
| `DECISIONS.md` | {{决策}}                |
| 纠偏           | 见 `source-index.md` §A |

---

## 2. 架构与设计

**2.1 架构** {{边界/数据流}} · **2.2 设计** {{关键流程}} · **2.3 规则** {{GLOBAL + 本任务}} · **2.4 契约** {{路径}} · **2.5 决策** {{摘录}}

---

## 3. 需求与场景矩阵（≥3 · BDD）

| 场景# | Given | When  | Then  | AC   | 测试（§5.2） | 验证 Tier（§6） |
| ----- | ----- | ----- | ----- | ---- | ------------ | --------------- |
| S1    | {{…}} | {{…}} | {{…}} | AC-1 | 成功/失败列  | Tier B          |
| S2    | {{…}} | {{…}} | {{…}} | AC-2 | {{…}}        | {{…}}           |
| S3    | {{…}} | {{…}} | {{…}} | AC-3 | {{…}}        | {{…}}           |

**3.1 需求说明：** {{能做什么/不能做什么}}  
**3.2 范围：** in {{…}} · out/defer {{…}}

---

## 4. 预期结果

| #    | 预期结果 | 验证链         |
| ---- | -------- | -------------- |
| AC-1 | {{…}}    | S1 → §9.x → §6 |
| AC-2 | {{…}}    | {{…}}          |

---

## 5. 测试契约（Execute 写代码 · Plan 写契约）

> purpose **冻结**；改 purpose 须回 Plan。  
> **测试设计写在下方 §5.3**（用例名 + 断言语义）；Execute 在 **§5.1 的 `tests/*.py`** 实现代码（禁止改 purpose）。

### 5.0 规范（testing-guidelines 提炼 + 本任务）

1. 注释：`purpose` / `target` / `verifies` / `failure_meaning`
2. {{本任务额外条款}}

### 5.1 测试文件（路径写死）

| 路径                  | 目标文件               | purpose（冻结） | §9 步   |
| --------------------- | ---------------------- | --------------- | ------- |
| `tests/test_{{x}}.py` | `backend/app/{{m}}.py` | {{…}}           | 9.1–9.2 |

### 5.2 成功/失败语义（引用场景 S#）

| 能力  | 成功怎么测 | 失败怎么测 | 场景 | 边界            |
| ----- | ---------- | ---------- | ---- | --------------- |
| {{…}} | {{…}}      | {{…}}      | S1   | {{能测/不能测}} |

### 5.3 用例设计（Plan 冻结 · 正文不进独立 research 文件）

| 测试文件（§5.1）      | `test_*` 名称             | 断言语义     | 场景 | RED 命令（Execute）                    |
| --------------------- | ------------------------- | ------------ | ---- | -------------------------------------- |
| `tests/test_{{x}}.py` | `test_{{tracer}}_success` | {{成功断言}} | S1   | `pytest …::test_{{tracer}}_success -v` |
| 同上                  | `test_{{tracer}}_failure` | {{失败断言}} | S1   | `pytest …::test_{{tracer}}_failure -v` |

### 5.4 四层测试

| 层   | 环境      | 命令           | 通过   | 证据 |
| ---- | --------- | -------------- | ------ | ---- |
| 单元 | local/ci  | `{{pytest …}}` | exit 0 |      |
| 集成 | local/ci  | `{{…}}`        | {{…}}  |      |
| 管道 | prod-path | `{{…}}`        | {{…}}  |      |
| E2E  | prod-path | `{{…}}`        | {{…}}  |      |

---

## 6. 验证（场景 S# → Tier；不重复 §3 表）

| Tier | 环境      | 命令        | 场景  | 通过条件 | 勾  |
| ---- | --------- | ----------- | ----- | -------- | --- |
| A    | local/ci  | `pytest -q` | S1–S3 | exit 0   | [ ] |
| B    | prod-path | `{{…}}`     | S2    | {{…}}    | [ ] |
| C    | prod-path | `{{smoke}}` | S3    | {{…}}    | [ ] |

**6.1 交接门槛：** §9 证据齐 · §5.1 文件已建 · S1–S3 有对应用例或 explicit 不可测 · §5.4+§6 B/C 已跑 · §1.5 未触发

---

## 7. Red Flags

| 风险                      | 预防                     |
| ------------------------- | ------------------------ |
| 横向停步                  | 按 §8 垂直切片做到交付物 |
| 无 RED 勾 §9              | RED 必须先 FAIL          |
| 改 purpose / 自造测试路径 | 只许 §5.1                |
| Execute 跑 trellis-check  | → Audit A1               |

---

## 8. 实现顺序（Plan 已垂直切片）

| 序  | ID      | 交付物（完标准） | 依赖    | AC   |
| --- | ------- | ---------------- | ------- | ---- |
| 1   | SLICE-1 | {{…}}            | gate    | AC-1 |
| 2   | SLICE-2 | {{…}}            | SLICE-1 | AC-2 |

---

## 9. 实现步骤（RED/GREEN · 仅 Execute Skill）

### 9.0 Boot

| RED/GREEN 命令  | 证据                            | 绑定 Execute Skill                | 已执行 |
| --------------- | ------------------------------- | --------------------------------- | ------ |
| `{{pytest -q}}` | `9.0-red.txt` / `9.0-green.txt` | trellis-execute · gitnexus-impact | [ ]    |

### 9.1 SLICE-1

| 字段               | 内容                                                               |
| ------------------ | ------------------------------------------------------------------ |
| 切片               | SLICE-1（§8 序 1）                                                 |
| RED / GREEN        | `{{cmd}}` → `9.1-red.txt` / `9.1-green.txt`                        |
| 绑定 Execute Skill | test-driven-development · karpathy-guidelines · testing-guidelines |
| 通过               | RED FAIL；GREEN 0；§5.2 覆盖 S1                                    |
| 已执行             | [ ]                                                                |

### 9.2 SLICE-2

| 字段               | 内容                                                 |
| ------------------ | ---------------------------------------------------- |
| 切片               | SLICE-2                                              |
| RED / GREEN        | `{{…}}`                                              |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 通过               | §5.2 覆盖 S2                                         |
| 已执行             | [ ]                                                  |

---

## 10. Execute 交接 DoD

- [ ] §9 证据齐 · Boot 产物齐 · §5.4+§6 证据 · §11 Skill 必做 `[x]` · `validate-execute-handoff` 0 · 未 finish-work

---

## 11. Execute Skill 冻结

| Skill                      | 本任务          | 绑定       | 已读 | 已执行 |
| -------------------------- | --------------- | ---------- | ---- | ------ |
| trellis-execute            | 必做            | Boot       | [ ]  | [ ]    |
| test-driven-development    | 必做            | §9 RED     | [ ]  | [ ]    |
| incremental-implementation | 必做            | §9 SLICE   | [ ]  | [ ]    |
| karpathy-guidelines        | 必做            | GREEN      | [ ]  | [ ]    |
| testing-guidelines         | 必做            | 写测       | [ ]  | [ ]    |
| gitnexus-impact            | 必做            | 改 symbol  | [ ]  | [ ]    |
| systematic-debugging       | 条件            | DEBUG      | [ ]  | [ ]    |
| trellis-implement          | {{inline/派发}} | Execute    | [ ]  | [ ]    |
| trellis-check              | **不用**        | → Audit A1 | —    | —      |

路径见 `execute-skill-paths.yaml`。Audit → `AUDIT.plan.md`。
