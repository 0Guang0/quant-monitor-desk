# Plan 冻结记录 — {{任务标题}}

> **读者：Plan agent** · Execute / Audit **不读** · 勿写入 implement.jsonl / audit.jsonl

---

## 1. Plan 阶段 Skill 执行记录

| Phase  | Skill                                     | 路径                                         | 产出                              | 已完成 |
| ------ | ----------------------------------------- | -------------------------------------------- | --------------------------------- | ------ |
| boot   | trellis-plan                              | `.cursor/skills/trellis-plan/SKILL.md`       | `research/plan-boot.md`           | [ ]    |
| 1a     | gitnexus-plan（轻量概览）                 | AGENTS.md + MCP                              | `research/project-overview.md`    | [ ]    |
| 2a     | trellis-brainstorm                        | `.cursor/skills/trellis-brainstorm/SKILL.md` | `prd.md`、MASTER §1–3             | [ ]    |
| 2b     | spec-driven-development                   | 见 `plan-skill-paths.yaml`                   | MASTER §3 场景 + §4 AC            | [ ]    |
| 条件   | domain-modeling                           | `~/.claude/skills/domain-modeling/SKILL.md`  | `CONTEXT.md`                      | [ ]    |
| 3      | grill-me / interview-me / grill-with-docs | 见 yaml / mattpocock                         | `research/grill-me-session.md` 等 | [ ]    |
| 3.5    | to-issues                                 | `~/.claude/skills/to-issues/SKILL.md`        | 垂直切片工单（Plan 专用）         | [ ]    |
| 1b     | gitnexus-plan（深度分析）                 | AGENTS.md + MCP                              | `research/gitnexus-summary.md`    | [ ]    |
| 4      | brainstorming / api-and-interface-design  | 见 yaml                                      | MASTER §2                         | [ ]    |
| 条件   | codebase-design / prototype               | 见 mattpocock                                | 接口设计 / 原型                   | [ ]    |
| 5a     | planning-and-task-breakdown               | 见 yaml                                      | MASTER §8 垂直切片顺序            | [ ]    |
| 5b     | writing-plans                             | MASTER §5（§5.3 用例设计）+ §9 步骤          | [ ]                               |
| 5c     | trellis-before-dev                        | `.cursor/skills/trellis-before-dev/SKILL.md` | implement/check jsonl             | [ ]    |
| **5d** | **doubt-driven-development**              | 见 yaml                                      | AUDIT §1/§2 修订                  | [ ]    |

---

## 2. Plan 贡献溯源 & 5d 结论

（同前模板 §2 / §2.1）

### 2.5 Plan 阶段须人工填写（模板 ≠ 终稿）

从 **templates/** 复制到任务目录的是**骨架**；`task.py start` 前 Plan agent 必须按**本任务真实情况**改实，否则 Execute/Audit 拿到的是空命令。

| 须人工做什么               | 在哪改                                         | 说明                                                                                                                                                                                                  |
| -------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **替换 `{{}}` 占位符**     | `AUDIT.plan.md` **§2**（及 MASTER 里同类占位） | 模板里的 `{{init/migrate CLI}}`、`{{perf 命令}}` 等是**占位**，须换成**本任务可执行的**命令、路径、通过条件。**留 `{{}}` = 未冻结，禁止 start。** 详表 → [AUDIT 模板 §2.1](./templates/AUDIT.plan.md) |
| **无性能要求时写 A6 SKIP** | `AUDIT.plan.md` **§1 + §2**                    | 不是每个任务都要做性能审计。若无 hot path/SLA：§1 A6 标 **不用**；§2 保留一行 **「本任务跳过 — {理由}」**（勿留 perf 占位）。详步骤 → [AUDIT 模板 §2.2](./templates/AUDIT.plan.md)                    |
| **有性能要求时填 A6**      | 同上                                           | 删掉 SKIP 行，填 perf 命令与阈值；§1 A6 标 **必做**                                                                                                                                                   |

**示范：** `.trellis/tasks/06-16-005-schema-init/AUDIT.plan.md`（A6 已 SKIP + 其余维已任务化）。

---

## 3. 冻结自检（`task.py start` 前全勾）

### 3.0 双契约 one-pager（Plan agent 扫这一页）

> 完整条款见 [complex-task-planning-protocol.md §2.8–§2.10](./complex-task-planning-protocol.md)。下表 = 出厂检验单。

| ✓   | Execute 验收契约（MASTER）                                | ✓   | Audit 维度验证契约（AUDIT）                       |
| --- | --------------------------------------------------------- | --- | ------------------------------------------------- |
| [ ] | §0.1 / §8 切片顺序 / §9 步骤 / §5 测试契约 / §6 验证 已填 | [ ] | §1 A1–A8 Skill + **A9 主会话**                    |
| [ ] | §6 Tier B/C = **Execute prod-path**（真实 DATA_ROOT）     | [ ] | **§2 矩阵 A1–A8 全覆盖**（无留空 `{{}}`）         |
| [ ] | §10 = 交接 Audit（非 finish-work）                        | [ ] | §2 写库行用 **audit-sandbox** ≠ Execute DATA_ROOT |
| [ ] | §12 无 trellis-check / ponytail / verification            | [ ] | **A6**：必做 perf **或** §2.2 跳过行 + 理由       |
| [ ] | 6.pre → `gitnexus-execute-summary.md`（research 例外）    | [ ] | §3 7.pre → `gitnexus-audit-summary.md`            |
| [ ] | implement.jsonl 第一条 = MASTER                           | [ ] | audit.jsonl 第一条 = AUDIT.plan.md                |

**一条过关：** 左列 = Execute 跑什么（§5.4 + §6）；右列 = 各审计维**各自**跑什么（默认不复跑 §6 同行命令）。

### 3.0a Plan Phase 产出门禁（Phase 0 → 5d 必检）

| ✓   | 检查项                                                                                                                                     |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| [ ] | Phase 1a `research/project-overview.md` 已产出（≤1 页）或 MASTER §0 `analysis_waiver: true`                                                |
| [ ] | Phase 3 质疑记录已产出（`research/grill-me-session.md` 或等价）                                                                            |
| [ ] | Phase 3.5 切片工单列表已产出（必须 ≥2 个垂直切片；单切片仅当任务只涉及 1 个 MASTER §2 AC 且零跨模块依赖时允许，否则退回 Phase 2 重新拆分） |
| [ ] | Phase 1b `research/gitnexus-summary.md` 已产出或 MASTER §0 `analysis_waiver: true`                                                         |
| [ ] | Phase 4 已完成 **或** MASTER §0 已注明跳过理由（「§9 已足够清晰」）                                                                        |
| [ ] | Phase 5d 已完成（主会话 CLAIM→DOUBT→RECONCILE）；`plan.freeze.md` §2 已记录结论                                                            |

### 3.0b 原计划包门禁（Plan agent 必勾）

| ✓   | 检查项                                                                         |
| --- | ------------------------------------------------------------------------------ |
| [ ] | 已读 `docs/implementation_tasks/README.md` + `GLOBAL_*.md`（4 个）             |
| [ ] | 已读本 Round `README.md` + `DECISIONS.md`                                      |
| [ ] | 已读本批 `NNN_*.md` 任务卡及 §3 输入文件（specs / architecture）               |
| [ ] | `research/source-index.md` 已产出（§A 血缘 + §B manifest + §C 六类 + §D 路由） |
| [ ] | `MASTER.plan.md` §0 索引入口 + §1.6「原计划归并」+ §1.5「停止条件」已填        |
| [ ] | `MASTER.plan.md` §5 测试契约（§5.1 路径写死 + §5.2 成功/失败 + ≥3 场景）已填   |
| [ ] | `implement.jsonl` 含 GLOBAL 四文件 + 本批任务卡且路径存在                      |

### 3.0c Context Packing Gate v3

| ✓   | 检查项                                                                      |
| --- | --------------------------------------------------------------------------- |
| [ ] | `research/source-index.md` §C「索引完整」                                   |
| [ ] | `research/integration-ledger.md`                                            |
| [ ] | `research/integration-audit.md`（PASS；含 doc-gap + adversarial + closure） |
| [ ] | `meta.manifest_protocol_version: "3"`                                       |
| [ ] | `implement.jsonl` 全条 `extract:/for:`（V7）；ledger anchor 可解析（V8）    |

| ✓   | 检查项                                                                  |
| --- | ----------------------------------------------------------------------- |
| [ ] | `plan-manifest-audit.md` stub 或 integration-audit 含 manifest 节       |
| [ ] | `implement.jsonl` 覆盖 source-index §B `required` + MASTER §2.4/§5.4/§6 |
| [ ] | `check.jsonl` ⊆ `implement.jsonl`（E14）                                |
| [ ] | `task.json` `predecessor_tasks`（若有前置 Batch）                       |
| [ ] | `suggest-implement-context` 缺失 ≤5                                     |
| [ ] | MASTER **§0.3** + **§9.0** 指向 implement/ledger（禁止 §9.0 路径枚举）  |

```bash
python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/<slug> P0-index
python .trellis/scripts/patch_implement_from_ledger.py .trellis/tasks/<slug>
python .trellis/scripts/task.py suggest-implement-context .trellis/tasks/<slug>
python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/<slug> 5c
python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/<slug> 5e
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/<slug>
```

### 3.0d Manifest Gate（E15 · 与 3.0c 一并勾选）

| ✓   | 检查项                                                  |
| --- | ------------------------------------------------------- |
| [ ] | `plan.freeze.md` Manifest Gate / Context Packing 节已勾 |
| [ ] | `validate-plan-freeze` exit 0                           |

### 3.1 MASTER（Execute）

- [ ] **§0.1 门控速查** 已填（怎么测 / 怎么验收 / 什么叫过 / prod-path / **6.pre**）
- [ ] **§1.5 停止条件** 已填（≥1 条可执行停损）
- [ ] **§8 垂直切片顺序** 已填（每行有交付物定义）
- [ ] §9 每步：**通过条件 + 环境 + 证据列** 已填；**无 Plan skill 名**
- [ ] §5.4 四层 **全部 ✅**；B/C 行 prod-path
- [ ] §6 Tier **Execute 专用**；B/C prod-path
- [ ] `research/gitnexus-execute-summary.md` 路径已在 §0.1/6.pre 约定（Execute **例外可读**）
- [ ] §10 仅为 **Execute 交接 Audit**（非任务完成；无 finish-work）
- [ ] §11 Execute Skill 无留空；**不含** trellis-check / ponytail / **Plan skill**

### 3.2 AUDIT.plan.md

- [ ] §1 **A1–A8** Skill 冻结（**A8** = testing-guidelines；全部含 `+ doubt-driven-development`）；**A9 = 主会话**
- [ ] **§2 已任务化**：无未替换 `{{}}`（占位须按真实任务替换，见 **§2.5** / AUDIT §2.1）
- [ ] **A6**：§2 已填 perf **或** §2.2 SKIP 行 + 理由（§1 标「不用」）；**A6 跳过不影响 A5/A7/A8 audit-prod-path**
- [ ] §2 写库/CLI 行（A5 抽检、A6/A7/A8）隔离路径 **≠** Execute DATA_ROOT
- [ ] §2 **A5 扩展为 4 行**（追溯 + 必做抽检 + 证据文件真实性 + audit-prod-path）；无遗漏
- [ ] §2 **A7/A8 audit-prod-path** 行已填写；`AUDIT_PROD_ROOT` 验证步骤已包含
- [ ] §2 **对抗性触发器** 列 A1–A8 全覆盖（无留空）；**扩展权限** 列已填写
- [ ] §3 **7.pre** GitNexus 要求已写
- [ ] A2 ponytail + A1 trellis-check 已写；**全部 A1-A8 Skill 含 doubt-driven-development**
- [ ] `audit.jsonl` 第一条 = AUDIT.plan.md

- [ ] `audit.jsonl` **未含** plan.freeze / implement.jsonl

### 3.3 REPAIR（模板就绪）

- [ ] Audit 后若 §4.3 有项 → 主会话生成任务内 `REPAIR.plan.md`
- [ ] `repair-skill-registry.md` 已链入 index

### 3.4 jsonl

- [ ] implement.jsonl 第一条 = MASTER
- [ ] check.jsonl 供 A1；无 Plan 协议
- [ ] `research/plan-boot.md` 含 **Phase P0 complete**
- [ ] `research/source-index.md` 存在（或 legacy `original-plan-trace.md`）
- [ ] `research/plan-skill-reads.jsonl` 覆盖 freeze 必做 skill
- [ ] `validate 通过`

### 3.0v4 冻结三件套（plan_protocol_version: "4" · Execute/Audit 必读）

| ✓   | Execute 验收（冻结卡 + 索引）                         | ✓   | Audit（AUDIT + 索引 §5）             |
| --- | ----------------------------------------------------- | --- | ------------------------------------ |
| [ ] | `frozen/*.md` 含 §8 停止条件 + §9 步骤 + §10 测试契约 | [ ] | `AUDIT.plan.md` §2 无 `{{}}` 占位符  |
| [ ] | `EXECUTION_INDEX.md` §1 RED/GREEN + §2 验收 Tier      | [ ] | 索引 §5 Audit 追溯集已填             |
| [ ] | §3 仅列 **不可无损内联** 的原文路径                   | [ ] | `audit.jsonl` 第一条 = AUDIT.plan.md |
| [ ] | §4 已内联来源与冻结卡章节对照                         | [ ] | A6：perf 或 SKIP + 理由              |
| [ ] | `task.py freeze-task-card` 已执行                     | [ ] | 7.pre → `gitnexus-audit-summary.md`  |
| [ ] | `implement.jsonl` 第一条 = frozen 卡（自动生成）      | [ ] | A1/A5/A8 倒查 frozen + 索引 §3       |

### 3.0e Plan consolidation（v4 · Phase 5e · `freeze-task-card` 之前）

| ✓   | 检查项                                                                                      |
| --- | ------------------------------------------------------------------------------------------- |
| [ ] | `research/plan-consolidation.md` 存在且含 **`Phase 5e complete`**                           |
| [ ] | 表中每个已存在的 `research/*` 草稿有 `merged` / `pointer` / `n/a` 落点                      |
| [ ] | 可执行结论已写入**活任务卡**（非仅 plan-boot / grill-me）                                   |
| [ ] | `EXECUTION_INDEX.md` §4 已填（有 research 草稿时不得空）                                    |
| [ ] | `prd.md` 为薄索引（`thin-index: true` 或 ≤25 行且含 `frozen/`）                             |
| [ ] | `validate-plan-freeze` exit 0（含 5e + **Triad gate**：pointer/§4/implement/不读 research） |

### 3.6 validate-plan-freeze（机器门禁）

`task.py start` 前须 exit 0（失败则禁止 `planning → in_progress`，可用 `--force` 人工 override）：

```bash
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/<slug>
```

**粘贴最近一次输出（Plan agent 填写）：**

```text
(paste exit 0 output or N/A if task predates validator)
```

### 3.7 批准

- [ ] 用户「计划批准」→ `task.py start`

---

## 4. 修订记录

| 版本 | 日期     | 变更                                            |
| ---- | -------- | ----------------------------------------------- |
| v0.5 | {{date}} | §3.0 双契约 one-pager；AUDIT §2.1/§2.2 填表说明 |
| v0.4 | {{date}} | 双契约；AUDIT §2 维度验证矩阵 A1–A8             |
| v0.3 | {{date}} | §0.1 门控；A9 主会话；7.pre；REPAIR 自检        |
| v0.2 | {{date}} | 增加 AUDIT.plan + audit.jsonl 自检              |
