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
- 只许 §12 冻结 Skill；§8 每步须 **证据** 非空才能勾选
- **禁止**宣称任务完成（完成在 Audit → Repair → Finish 之后）

---

## 0.1 门控速查：怎么测 · 怎么验收 · 什么叫过

> Execute **必读**。无证据 = 未执行 = 未过。

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
3. Audit 验收见 **`AUDIT.plan.md` §2 维度验证矩阵**（Execute **不读、不填**）。

### 什么叫过（单步 / 整任务）

| 范围 | 什么叫过 |
|------|----------|
| **§8 单步** | 验证命令满足 **通过条件** + **证据非空** + 已执行 `[x]` |
| **§9 单层** | 该行命令 exit 0 且满足通过条件 + Execute 证据已填 |
| **§10 单行** | 通过条件满足 + Execute 证据已填 |
| **Execute 交接（§11）** | §8/§9/§10 Execute 侧全勾 + 证据齐；**仍不算任务完成** |
| **任务完成** | Audit PASS（无 §4.3）→ Phase 9；或有 §4.3 → Repair 关项 → §5 复验 → Phase 9 |

### prod-path 定义

与生产相同的 `DATA_ROOT`、配置加载、CLI/写锁；可本机/staging；**禁止**用 `:memory:` 代替 Tier B/C 的 PASS。

**Execute 开场白：**

```text
进入 Execute。读 MASTER + implement.jsonl。
按 §0.1 门控：§8 逐步+证据，§9 四层，§10 Tier Execute 先跑。
严格 §12。§11 交接 Audit；勿 finish-work。
```

**Execute 开始前（6.pre）：** GitNexus/CodeGraph 刷新 → `research/gitnexus-execute-summary.md`；读摘要 + 至少 1 次 query/context。

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
| {{…}} | {{…}} |

---

## 8. 实现步骤（逐步通过条件 + 证据）

> Skill 汇总见 §12。无 **证据** 禁止勾 **已执行**。

### 8.1 {{步骤}}

| 字段 | 内容 |
|------|------|
| 做什么 | {{…}} |
| Skill（§12） | {{test-driven-development}} |
| 验证命令 | `{{pytest …}}` |
| **通过条件** | exit 0；{{关键输出片段}} |
| **环境** | local / ci / prod-path |
| **证据** | Execute 填：日志路径或粘贴输出 |
| 已执行 | [ ] |

### 8.2 {{步骤}}

| 字段 | 内容 |
|------|------|
| 做什么 | {{…}} |
| Skill（§12） | {{…}} |
| 验证命令 | `{{…}}` |
| **通过条件** | {{…}} |
| **环境** | {{…}} |
| **证据** | |
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

**prod-path 定义：** 真实 `DATA_ROOT`、项目配置加载、CLI/写锁与生产一致（可本机，非 `:memory:` 代验收）。

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

- [ ] §8 每步 **已执行 + 证据非空**
- [ ] §9 四层 **Execute 证据** 已填
- [ ] §10 Tier A/B/C Execute 已跑并勾选（B/C 须 prod-path）
- [ ] §12 Execute Skill **必做** 行已勾选
- [ ] **未** finish-work（等 Audit → Repair → Finish）

---

## 12. Execute Skill 冻结清单

> 词典：`.trellis/spec/guides/execute-skill-registry.md`（Execute 不读）

| Skill | 本任务 | 绑定 §8 | 触发 | `@` 指令 | 已执行 |
|-------|--------|---------|------|----------|--------|
| test-driven-development | 必做 | 8.x | 每步写代码前 | {{…}} | [ ] |
| incremental-implementation | 必做 | 8.x | 每切片 GREEN 后 | {{…}} | [ ] |
| source-driven-development | 条件/不用 | 8.x | {{写死}} | {{…}} | [ ] |
| systematic-debugging | 条件 | 当前步 | pytest RED | {{…}} | [ ] |
| trellis-implement | 必做/不用 | {{…}} | {{…}} | {{…}} | [ ] |

**Audit 用 Skill + 验证 → `AUDIT.plan.md` §1 + §2**（不进 MASTER §12）。

---

**Plan 记录 → `plan.freeze.md` · Audit → `AUDIT.plan.md` · Repair → `REPAIR.plan.md`（Audit 后生成）**
