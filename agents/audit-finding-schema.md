# Audit Findings Schema（A1–A8 关账 SSOT）

> **Leading word — FAIL：** 本维 findings 表**任一行非占位** → §维度裁决 = **FAIL**。  
> **Boot：** `agents/audit-boot-v4.1.md` · 权威：`agents/audit-adversarial-authority.md`

## 报告路径

| 维  | 落盘路径                      |
| --- | ----------------------------- |
| A1  | `research/audit-a1-report.md` |
| A2  | `research/audit-a2-report.md` |
| A3  | `research/audit-a3-report.md` |
| A4  | `research/audit-a4-report.md` |
| A5  | `research/audit-a5-report.md` |
| A6  | `research/audit-a6-report.md` |
| A7  | `research/audit-a7-report.md` |
| A8  | `research/audit-a8-report.md` |

## 报告结构（顺序固定）

1. **元信息**（可选）— 维、任务、`plan_protocol_version: 4.1`、模板、日期
2. **维度证据** — 各模板 §3.x checklist / 命令 / 追溯表（legwork；**不以自述为 PASS**）
3. **§维度裁决** — 见下
4. **§计划内问题** — findings 表
5. **§计划外发现** — findings 表（对抗性；无则占位行 + 对抗搜索声明）

## §维度裁决

仅允许：**PASS** | **FAIL** | **SKIP**（仅 A6 且 AUDIT.plan §1/§2 已冻结 SKIP）。

**总裁决** 仅 **A9 主会话** 写入 `audit.report.md` §4.2 — 单维报告 **禁止** 写「总裁决」。

| 条件                                                            | 裁决                                         |
| --------------------------------------------------------------- | -------------------------------------------- |
| §计划内 + §计划外 两表均为占位行（无 finding）且 checklist 满足 | **PASS**                                     |
| 任一张 findings 表有 ≥1 行非占位                                | **FAIL**                                     |
| A6 Plan 冻结 SKIP                                               | **SKIP**（须写 SKIP 理由；**不算** finding） |

**禁止**作为维度裁决：`PASS_WITH_FIXES`、`PASS_WITH_GAPS`、`REQUEST CHANGES`、`0 BLOCKING`、`有 P0 但 PASS` 等。

## Findings 表（两节同表头）

```markdown
## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
```

### 占位行（无 finding 时各表一行）

`| — | — | 无 | — | — | — | — |`

计划外 additionally：`已对抗搜索：<范围>`（占位行下一行 prose）。

### 列约束

| 列           | 要求                         |
| ------------ | ---------------------------- |
| **ID**       | `A{n}-P{0-3}-{seq}`          |
| **P**        | 仅 **P0**–**P3**             |
| **修复方案** | 可执行；禁止空泛「后续优化」 |
| **验证**     | Repair 可复跑命令或断言      |

### P 级

| P      | 含义                                      |
| ------ | ----------------------------------------- |
| **P0** | merge / finish-work 前必须修              |
| **P1** | Repair 必须修                             |
| **P2** | Repair 必须修或 **阶段外置**（绑任务 ID） |
| **P3** | 仍进表、仍 **FAIL**；仅可阶段外置         |

**禁止** findings 表使用：BLOCKING、NON-BLOCKING、HIGH、MEDIUM、LOW、IMPORTANT。

### 计划内 vs 计划外

| 节             | 内容                                                                                                |
| -------------- | --------------------------------------------------------------------------------------------------- |
| **计划内问题** | 对照 AUDIT.plan §1/§2、ENTRY §1/§2、`to-issues-slices.md` AC、本维 checklist                        |
| **计划外发现** | 活卡 Red Flags、契约、plan-doubt-review / integration-audit 缺口；**不得**因 ENTRY/INDEX 已列而省略 |

## 关账完成条件（A1–A8 每维）

- [ ] Boot v4.1 完成（`audit-boot-v4.1.md` checklist）
- [ ] 报告已落盘
- [ ] §维度裁决 ∈ {PASS, FAIL, SKIP}
- [ ] findings 非占位 → 裁决 = **FAIL**
- [ ] 每行含 P0–P3、修复方案、验证

## A9 主会话合并

步骤与门禁：`agents/audit-boot-v4.1.md` §A9 合并。

1. 读 A1–A8 §计划内 + §计划外 **全文** → `audit.report.md` §4.1 · `research/audit-repair-ledger.md`（模板：`.trellis/spec/guides/templates/audit-repair-ledger.md`）
2. `audit_matrix.json`：`pass` | `fail` | `skip` | `fail_then_fixed`
3. 任维 `fail` 或 §4.1 非占位 → **FAIL** → REPAIR.plan
4. `python .trellis/scripts/task.py validate-audit-handoff <task-dir>` **exit 0**
5. Repair 复验：`validate-repair-close` exit 0 + `EXECUTION_INDEX.md` §2.1 Tier + `uv run pytest -q` exit 0

**legacy 范例：** `tasks/archive/` 内 `NON-BLOCKING` / `fixed` / `deferred` 台账 **勿模仿**。

**disposition：** A9 建账 **待修复** | **阶段外置** → Repair 关账 **已修复** | **阶段外置**（`project-global.mdc` §无遗留）。

**阶段外置：** 须登记 **`docs/quality/待修复清单.md`** + **`PROJECT_IMPLEMENTATION_ROADMAP.md`**（两份必登；finish-work 后仍读）。
