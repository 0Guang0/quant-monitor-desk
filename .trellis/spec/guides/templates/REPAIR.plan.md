# Repair 计划 — {{任务标题}}

> **读者：Repair 执行者**（主会话或 `repair-agent`）  
> **输入：** `audit.report.md` §3–§4.3（Audit 产出）  
> **原则：** 修根因，不兜底；§2 Deferred 以外不得遗留  
> **产出：** 更新 `audit.report.md` §5 复验；必要时补丁 MASTER §8/§10

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `{{slug}}` |
| Audit 报告 | `audit.report.md` |
| Repair Skill 词典 | `.trellis/spec/guides/repair-skill-registry.md` |

**开场白：**

```text
进入 Repair。读 audit.report.md §4.3 与本文 §1。
逐项修根因（禁止防御性绕过）；每项填证据；跑 §2 复验命令。
Deferred 仅 §3 已批准项；其余全关才进 Finish。
```

---

## 1. 修复项清单（来自 audit.report §4.3）

| ID | 维度 | 问题 | 根因修复方案 | Skill（冻结） | 验证命令 | 通过条件 | 证据 | 已修复 |
|----|------|------|--------------|---------------|----------|----------|------|--------|
| F-1 | A3 | {{…}} | {{直接改 X，非加 wrapper}} | systematic-debugging; TDD | `{{pytest …}}` | {{…}} | | [ ] |

---

## 2. Repair Skill 冻结（不得自选）

| Skill | 本任务 | 绑定修复项 | `@` 指令 | 已执行 |
|-------|--------|------------|----------|--------|
| systematic-debugging | 必做/条件 | F-* | {{…}} | [ ] |
| test-driven-development | 必做 | 每项代码改动 | 先 RED 再 GREEN | [ ] |
| verification-before-completion | 必做 | 收尾 | 复跑 **MASTER** §10 Tier | [ ] |

---

## 3. 批准遗留（Deferred · 须极少）

| ID | 问题 | 遗留理由 | 后续任务/ADR |
|----|------|----------|--------------|
| | | 故意设计 / 后续 ROUND / 大重构 | |

---

## 4. Repair 完成 DoD

- [ ] §1 全部可修项 **已修复 + 证据**
- [ ] §3 Deferred 已用户确认（若有）
- [ ] **复跑 MASTER §10** Tier A/B/C 全绿（Execute 回归门禁；**非** AUDIT §2 全矩阵）
- [ ] `audit.report.md` §5 复验已更新
- [ ] 主会话签字 → Finish
