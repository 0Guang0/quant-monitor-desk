# Audit Report — {{slug}}

> Findings SSOT：`agents/audit-finding-schema.md` · 各维 `research/audit-a{n}-report.md`

## 1. 元信息

| 字段          | 值                                 |
| ------------- | ---------------------------------- |
| GitNexus 刷新 | {{7.pre 时间}}                     |
| 摘要文件      | research/gitnexus-audit-summary.md |

---

## 2. 维度裁决汇总

| 维  | 报告 | 裁决               | 证据路径                    |
| --- | ---- | ------------------ | --------------------------- |
| A1  |      | pass / fail        | research/audit-a1-report.md |
| A2  |      | pass / fail        | research/audit-a2-report.md |
| A3  |      | pass / fail        | research/audit-a3-report.md |
| A4  |      | pass / fail        | research/audit-a4-report.md |
| A5  |      | pass / fail        | research/audit-a5-report.md |
| A6  |      | pass / fail / skip | research/audit-a6-report.md |
| A7  |      | pass / fail        | research/audit-a7-report.md |
| A8  |      | pass / fail        | research/audit-a8-report.md |

**规则：** 任维 `fail` 或下方 §4.3 非空 → 总裁决 **FAIL**。禁止 `PASS_WITH_FIXES` / `PASS_WITH_GAPS`。

### Execute INDEX §2.1 证据索引（只读引用 · 非 Audit 复跑结论）

| Tier | Execute 证据路径/摘要 |
| ---- | --------------------- |
|      |                       |

---

## 3. 分维度详情（引用各维报告 §维度证据）

> 全文见 `research/audit-a{n}-report.md`；本节可摘要，**findings 以各维 §计划内/§计划外 为准**。

### 3.1 A1 · Spec

### 3.2 A2 · 过度工程

### 3.3 A3 · 安全

### 3.4 A4 · 代码质量

### 3.5 A5 · 完成情况

### 3.6 A6 · 性能

### 3.7 A7 · 运维

### 3.8 A8 · 测试缺口

---

## 4. 风险与结论（A9 · 主会话）

### 4.1 Findings 合并（→ `research/audit-repair-ledger.md`）

从 A1–A8 **§计划内 + §计划外** 去重合并（A9 六步见 `agents/audit-boot-v4.2.md`；v4.1：`audit-boot-v4.1.md`）。Ledger 模板：`.trellis/spec/guides/templates/audit-repair-ledger.md`。

| ID  | P   | 维度 | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | ---- | -------- | ---- |

### 4.2 结论

- [ ] **PASS** — 全维 pass/skip 且 §4.1 仅占位行 → Phase 9
- [ ] **FAIL** — 任维 fail 或 §4.1 有 finding → REPAIR.plan → Phase 8

### 4.3 修复项（→ REPAIR.plan §1）

与 §4.1 同 ID；Repair 按 P0→P1→P2→P3 关账（`project-global.mdc` §无遗留）。

### 4.4 阶段外置（文档登记 · 与 ledger 同步）

每项 **阶段外置** 须在关账前完成登记（客观上依赖后续阶段交付物）：

| ID  | 问题 | 绑定阶段/任务 | 依赖/承接 | 登记位置                                                           |
| --- | ---- | ------------- | --------- | ------------------------------------------------------------------ |
|     |      |               |           | `docs/quality/待修复清单.md` · `PROJECT_IMPLEMENTATION_ROADMAP.md` |

ledger `登记位置` 列须含上述 **两路径**。

---

## 5. Repair 复验（Phase 8 后）

| 项                                          | 结果 | 证据 |
| ------------------------------------------- | ---- | ---- |
| §4.3 全部关闭或 §4.4 已登记                 |      |      |
| **INDEX §2.1** Tier 复跑（Repair 回归门禁） |      |      |
| `uv run pytest -q` exit 0                   |      |      |

> Repair **复跑 EXECUTION_INDEX §2.1 Tier** + `uv run pytest -q`，不重跑 AUDIT §1 全矩阵（除非用户要求复 Audit）。

**复验 PASS → Phase 9 Finish**
