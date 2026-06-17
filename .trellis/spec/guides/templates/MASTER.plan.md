# MASTER 计划 — {{任务标题}}

> **Execute 入口**  
> Execute：**本文件 + `implement.jsonl`**。Audit 见同目录 **`AUDIT.plan.md`**（Execute **不读**）。  
> `prd` / `design` / `implement` 为 ≤15 行索引。

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| 任务 slug | `{{slug}}` |
| Audit 计划 | `.trellis/tasks/{{slug}}/AUDIT.plan.md` |
| 分析豁免 | `analysis_waiver: false` |
| Plan 冻结自检 | `plan.freeze.md`（Execute **不读**） |

**Execute 可读范围：** §0、**§0.1 门控速查**、§1–§12  

**Execute 硬性要求：**

- 不读 `AUDIT.plan.md`、Plan 协议、registry
- 只许 §12 冻结 Skill；§8 每步须 **RED/GREEN 证据** 非空才能勾选
- **禁止**宣称任务完成（完成在 Audit → Repair → Finish 之后）
- **禁止**在 §8 内嵌完整测试模块；完整 pytest 放 `research/§8.x-tests.md`

---

## 0.1 门控速查：怎么测 · 怎么验收 · 什么叫过

> Execute **必读**。无证据 = 未执行 = 未过。

### Execute 逐步循环（每 §8.x 步 **强制**）

1. **读** 本步「绑定 §12 Skill」对应 SKILL.md
2. **RED**：只写/启用本步 tracer 测试 → 跑 **RED 命令** → **必须 FAIL** → 写入 **RED 证据**
3. **GREEN**：最小实现 → 跑 **GREEN 命令** → **必须 PASS** → 写入 **GREEN 证据**
4. **勾** 本步「已执行」；**禁止**未填证据勾选
5. **incremental**：全库 pytest 仍绿后再进入 §8.(x+1)
6. RED 不符合预期 → **systematic-debugging**（§12 条件 Skill）

**Red Flag：** 单次编辑跨多个 §8 步 / >100 行且无 pytest → 停止，回退当前步。

### User Rule → §12 映射（Plan 必须写入 §12 表）

| User Rule | MASTER §12 行 |
|-----------|---------------|
| karpathy-guidelines | 必做 · Execute 全程 |
| testing-guidelines | 必做 · 写/改测试时 |
| GitNexus impact（AGENTS.md） | 必做 · 改 symbol 前 |

### 怎么测（§9 · 四层全部必做）

| 层次 | 在哪测 | 通过条件（摘要） |
|------|--------|------------------|
| 单元 | local/ci | 命令 exit 0；断言业务语义（非仅不抛异常） |
| 集成 | local/ci | 多模块/DB 协作行为符合 §2 |
| 管道/集成链 | **prod-path** | 真实 DATA_ROOT + CLI/写锁路径跑通 |
| E2E/smoke | **prod-path** | 端到端链路可观测结果与 §2 一致 |

**6.pre（Execute 开始前）：** GitNexus/CodeGraph 刷新 → `research/gitnexus-execute-summary.md`；读摘要 + 至少 1 次 query/context 再写非 trivial 代码。

### 怎么验收（§10 · Execute 专用回归门禁）

1. Execute **跑** §10 每一行，填 **证据** + Execute 勾。
2. Tier **B/C 必须 prod-path**（见 §9 定义）。
3. 交接 Audit 前：`python .trellis/scripts/task.py validate-execute-handoff <task-dir>`
4. Audit 验收见 **`AUDIT.plan.md` §2 维度验证矩阵**（Execute **不读、不填**）。

### 什么叫过（单步 / 整任务）

| 范围 | 什么叫过 |
|------|----------|
| **§8 单步** | RED 已 FAIL + GREEN 已 PASS + **证据非空** + 已执行 `[x]` |
| **§9 单层** | 该行命令 exit 0 且满足通过条件 + Execute 证据已填 |
| **§10 单行** | 通过条件满足 + Execute 证据已填 |
| **Execute 交接（§11）** | §8/§9/§10 Execute 侧全勾 + 证据齐 + handoff 脚本 PASS |
| **任务完成** | Audit PASS（无 §4.3）→ Phase 9；或有 §4.3 → Repair 关项 → §5 复验 → Phase 9 |

### prod-path 定义

与生产相同的 `QMD_DATA_ROOT`（默认 `data/`）、配置加载、CLI/写锁；可本机/staging；**禁止**用 `:memory:` 代替 Tier B/C 的 PASS。

**Execute 开场白：**

```text
进入 Execute。读 MASTER + implement.jsonl。
6.pre → 严格 §8.x 逐步循环（RED 证据 → GREEN 证据）→ §9 → §10 → validate-execute-handoff → §11 Audit。
严格 §12。勿 finish-work。
```

**Plan 开工前：** `python .trellis/scripts/task.py validate-plan-freeze <task-dir>` → 用户批准 → `task.py start`。

---

## 1. 目标

### 1.1 一句话目标

{{…}}

### 1.2 非目标

- {{…}}

---

## 2. 预期结果（A5 trace-ac 追溯用）

| # | 预期结果 | 验证链 |
|---|----------|--------|
| 1 | {{…}} | §10 Tier {{A/B/C}} / 测试 {{name}} |
| 2 | {{…}} | {{…}} |

---

## 3. 范围与边界

{{…}}

---

## 4. 代码地图

| 路径 | 操作 |
|------|------|
| {{path}} | 创建/修改 |

---

## 5. 模式与约束

{{…}}

---

## 6. 接口/契约（若有）

{{…}}

---

## 7. Red Flags

| Red Flag | 预防 |
|----------|------|
| 水平切片（§8 全文一次粘贴） | §8 仅 tracer；research/ 存完整测试 |
| 无 RED 证据勾选 §8 | RED 命令必须先 FAIL |
| Execute 跑 trellis-check | 复杂任务 → Audit A1 |
| {{…}} | {{…}} |

---

## 8. 实现步骤（逐步 RED/GREEN + 证据）

> Skill 汇总见 §12。**禁止**内嵌 >2 个完整 `def test_*`；其余放 `research/§8.x-tests.md`。  
> 无 **证据** 禁止勾 **已执行**。

### 8.1 {{步骤}}

| 字段 | 内容 |
|------|------|
| 做什么 | {{…}} |
| 绑定 §12 Skill | {{test-driven-development}} |
| **RED 命令** | `{{pytest …::test_tracer -v}}`（实现前） |
| **RED 证据** | `research/execute-evidence/8.1-red.txt` 或粘贴 FAIL 摘要 |
| **GREEN 命令** | `{{pytest … -v}}` |
| **GREEN 证据** | `research/execute-evidence/8.1-green.txt` |
| **通过条件** | RED 必须 FAIL；GREEN exit 0；{{关键断言}} |
| **环境** | local / ci / prod-path |
| 已执行 | [ ] |

### 8.2 {{步骤}}

| 字段 | 内容 |
|------|------|
| 做什么 | {{…}} |
| 绑定 §12 Skill | {{incremental-implementation}} |
| **RED 命令** | `{{…}}` |
| **RED 证据** | |
| **GREEN 命令** | `{{…}}` |
| **GREEN 证据** | |
| **通过条件** | {{…}} |
| **环境** | {{…}} |
| 已执行 | [ ] |

---

## 9. 测试层次（复杂任务四层 **全部必做**）

> 禁止 ❌。`:memory:` 仅可用于 Tier A 单元；**Tier B/C 须 prod-path**。

| 层次 | 必做 | 环境 | 命令 | 通过条件 | 测试文件/路径 | Execute 证据 |
|------|------|------|------|----------|---------------|--------------|
| 单元 | ✅ | local/ci | `{{pytest tests/unit…}}` | exit 0 | {{path}} | |
| 集成 | ✅ | local/ci | `{{…}}` | {{…}} | {{path}} | |
| 管道/集成链 | ✅ | **prod-path** | `{{init_db + migration…}}` | {{…}} | {{path}} | |
| E2E/smoke | ✅ | **prod-path** | `{{…}}` | {{…}} | {{path}} | |

**prod-path 定义：** 真实 `QMD_DATA_ROOT`、项目配置加载、CLI/写锁与生产一致（可本机，非 `:memory:` 代验收）。

---

## 10. 验收 Tier 表（Execute 专用 · Plan 冻结）

> **仅 Execute** 执行。Audit 见 `AUDIT.plan.md` §2，不在本表填勾。

| Tier | 环境 | 命令 | 通过条件 | Execute 证据 | Execute 勾 |
|------|------|------|----------|--------------|------------|
| A | local/ci | `pytest -q` | exit 0 | | [ ] |
| A | local/ci | `ruff check .` | exit 0 | | [ ] |
| B | prod-path | `{{python scripts/init_db.py}}` | {{库文件存在+migration 行}} | | [ ] |
| B | prod-path | `{{migration 幂等复跑}}` | 第二次 applied=[] | | [ ] |
| C | prod-path | `{{smoke test}}` | {{…}} | | [ ] |

---

## 11. Execute 交接 DoD（≠ 任务完成）

- [ ] §8 每步 **已执行 + RED/GREEN 证据非空**
- [ ] §9 四层 **Execute 证据** 已填
- [ ] §10 Tier A/B/C Execute 已跑并勾选（B/C 须 prod-path）
- [ ] §12 Execute Skill **必做** 行已 `[x]`
- [ ] `task.py validate-execute-handoff` exit 0
- [ ] **未** finish-work（等 Audit → Repair → Finish）

---

## 12. Execute Skill 冻结清单

> Plan 填表；Execute **只认本表**，不读 execute-skill-registry.md。

| Skill | 本任务 | 绑定 §8 | 触发 | 证据 | 已执行 |
|-------|--------|---------|------|------|--------|
| test-driven-development | 必做 | 8.x | 每步 RED 前 | research/*evidence* | [ ] |
| incremental-implementation | 必做 | 8.x | 每步 GREEN 后 | 同上 | [ ] |
| karpathy-guidelines | 必做 | 全程 | 写代码前 | §12 对照笔记 | [ ] |
| testing-guidelines | 必做 | 8.x 测试 | 写/改测试 | 同上 | [ ] |
| gitnexus-impact | 必做 | 改 symbol | impact() | 摘要或 MCP 输出 | [ ] |
| source-driven-development | 条件/不用 | 8.x | {{写死}} | {{URL/笔记}} | [ ] |
| systematic-debugging | 条件 | 当前步 | pytest RED 异常 | 根因笔记 | [ ] |
| trellis-implement | inline/必做 | Execute | 派发或主会话 | 实现报告 | [ ] |
| trellis-check | **不用** | — | → Audit A1 | — | — |

**Audit 用 Skill + 验证 → `AUDIT.plan.md` §1 + §2**（不进 MASTER §12）。

---

**Plan 记录 → `plan.freeze.md` · Audit → `AUDIT.plan.md` · Repair → `REPAIR.plan.md`（Audit 后生成）**
