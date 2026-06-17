# Plan 冻结记录 — {{任务标题}}

> **读者：Plan agent** · Execute / Audit **不读** · 勿写入 implement.jsonl / audit.jsonl

---

## 1. Plan 阶段 Skill 执行记录

| Phase | Skill | 产出 | 已完成 |
|-------|-------|------|--------|
| 1 | GitNexus | research/gitnexus-summary.md | [ ] |
| 2a–2b | trellis-brainstorm + SDD | MASTER §1–3 | [ ] |
| 3 | grill-me / interview-me | §7 | [ ] |
| 4 | brainstorming / api-and-interface-design | §4–6 | [ ] |
| 5a–5c | breakdown + writing-plans + trellis-before-dev | §8、jsonl | [ ] |
| **5d** | **doubt-driven-development** | §7/§8/§12、**AUDIT §1/§2** 修订；**§8 无完整测试函数体**（仅 tracer + research/） | [ ] |

---

## 2. Plan 贡献溯源 & 5d 结论

（同前模板 §2 / §2.1）

### 2.5 Plan 阶段须人工填写（模板 ≠ 终稿）

从 **templates/** 复制到任务目录的是**骨架**；`task.py start` 前 Plan agent 必须按**本任务真实情况**改实，否则 Execute/Audit 拿到的是空命令。

| 须人工做什么 | 在哪改 | 说明 |
|--------------|--------|------|
| **替换 `{{}}` 占位符** | `AUDIT.plan.md` **§2**（及 MASTER 里同类占位） | 模板里的 `{{init/migrate CLI}}`、`{{perf 命令}}` 等是**占位**，须换成**本任务可执行的**命令、路径、通过条件。**留 `{{}}` = 未冻结，禁止 start。** 详表 → [AUDIT 模板 §2.1](./templates/AUDIT.plan.md) |
| **无性能要求时写 A6 SKIP** | `AUDIT.plan.md` **§1 + §2** | 不是每个任务都要做性能审计。若无 hot path/SLA：§1 A6 标 **不用**；§2 保留一行 **「本任务跳过 — {理由}」**（勿留 perf 占位）。详步骤 → [AUDIT 模板 §2.2](./templates/AUDIT.plan.md) |
| **有性能要求时填 A6** | 同上 | 删掉 SKIP 行，填 perf 命令与阈值；§1 A6 标 **必做** |

**示范：** `.trellis/tasks/06-16-005-schema-init/AUDIT.plan.md`（A6 已 SKIP + 其余维已任务化）。

---

## 3. 冻结自检（`task.py start` 前全勾）

### 3.0 双契约 one-pager（Plan agent 扫这一页）

> 完整条款见 [complex-task-planning-protocol.md §2.8–§2.10](./complex-task-planning-protocol.md)。下表 = 出厂检验单。

| ✓ | Execute 验收契约（MASTER） | ✓ | Audit 维度验证契约（AUDIT） |
|---|---------------------------|---|----------------------------|
| [ ] | §0.1 / §8 / §9 / §10 已填；**§10 无 Audit 列** | [ ] | §1 A1–A8 Skill + **A9 主会话** |
| [ ] | §10 B/C = **Execute prod-path**（真实 DATA_ROOT） | [ ] | **§2 矩阵 A1–A8 全覆盖**（无留空 `{{}}`） |
| [ ] | §11 = 交接 Audit（非 finish-work） | [ ] | §2 写库行用 **audit-sandbox** ≠ Execute DATA_ROOT |
| [ ] | §12 无 trellis-check / ponytail / verification | [ ] | **A6**：必做 perf **或** §2.2 跳过行 + 理由 |
| [ ] | 6.pre → `gitnexus-execute-summary.md`（research 例外） | [ ] | §3 7.pre → `gitnexus-audit-summary.md` |
| [ ] | implement.jsonl 第一条 = MASTER | [ ] | audit.jsonl 第一条 = AUDIT.plan.md |

**一条过关：** 左列 = Execute 跑什么；右列 = 各审计维**各自**跑什么（默认不复跑 §10 同行命令）。

### 3.1 MASTER（Execute）

- [ ] **§0.1 门控速查** 已填（怎么测 / 怎么验收 / 什么叫过 / prod-path / **6.pre**）
- [ ] §8 每步：**通过条件 + 环境 + 证据列** 已填
- [ ] §9 四层 **全部 ✅**（无 ❌）；B/C 行 prod-path
- [ ] §10 Tier **Execute 专用**（无 Audit 列）；B/C prod-path
- [ ] `research/gitnexus-execute-summary.md` 路径已在 §0.1/6.pre 约定（Execute **例外可读**）
- [ ] §11 仅为 **Execute 交接 Audit**（非任务完成；无 finish-work）
- [ ] §12 Execute Skill 无留空；**不含** trellis-check / ponytail

### 3.2 AUDIT.plan.md

- [ ] §1 **A1–A8** Skill 冻结；**A9 = 主会话**
- [ ] **§2 已任务化**：无未替换 `{{}}`（占位须按真实任务替换，见 **§2.5** / AUDIT §2.1）
- [ ] **A6**：§2 已填 perf **或** §2.2 SKIP 行 + 理由（§1 标「不用」）
- [ ] §2 写库/CLI 行（A5 抽检、A6/A7/A8）隔离路径 **≠** Execute DATA_ROOT
- [ ] §3 **7.pre** GitNexus 要求已写
- [ ] A2 ponytail + A1 trellis-check 已写
- [ ] `audit.jsonl` 第一条 = AUDIT.plan.md

- [ ] `audit.jsonl` **未含** plan.freeze / implement.jsonl

### 3.3 REPAIR（模板就绪）

- [ ] Audit 后若 §4.3 有项 → 主会话生成任务内 `REPAIR.plan.md`
- [ ] `repair-skill-registry.md` 已链入 index

### 3.4 jsonl

- [ ] implement.jsonl 第一条 = MASTER
- [ ] check.jsonl 供 A1；无 Plan 协议
- [ ] `validate 通过`

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

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.5 | {{date}} | §3.0 双契约 one-pager；AUDIT §2.1/§2.2 填表说明 |
| v0.4 | {{date}} | 双契约；AUDIT §2 维度验证矩阵 A1–A8 |
| v0.3 | {{date}} | §0.1 门控；A9 主会话；7.pre；REPAIR 自检 |
| v0.2 | {{date}} | 增加 AUDIT.plan + audit.jsonl 自检 |
