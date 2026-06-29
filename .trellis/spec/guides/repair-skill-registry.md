# Repair 阶段 — Skill 候选词典

> **读者：Plan agent**（Audit 后填 `REPAIR.plan.md`）/ **Repair 执行者**  
> **Boot SSOT：** `agents/repair-boot-v4.1.md`  
> **原则：** 直接修根因；禁止用兜底/绕过代替修复（见协议 §2.6）

---

## 1. 何时进入 Repair

- `audit.report.md` §4 结论为 **FAIL**（任维 fail 或 §4.3 findings 非空）
- **PASS** 且 §4.3 仅占位 → **跳过 Repair**，直接 Finish

---

## 2. 默认 Repair Skill 栈（少于 Plan，但不可为零）

| Skill                                          | 典型用途                                     | Repair 默认                             |
| ---------------------------------------------- | -------------------------------------------- | --------------------------------------- |
| Superpowers **systematic-debugging**           | 定位根因                                     | **必做**（有 bug 时）                   |
| Superpowers **test-driven-development**        | 修代码+测试                                  | **必做**                                |
| addy **incremental-implementation**            | 多文件修                                     | 条件                                    |
| addy **source-driven-development**             | 框架 API 修                                  | 条件                                    |
| Superpowers **verification-before-completion** | 修完复验 **INDEX §2.1** + `uv run pytest -q` | **必做**                                |
| addy **security-and-hardening**                | 安全项修复                                   | 条件（来自 A3）                         |
| ponytail-review                                | 删 bloat                                     | **不用**（Repair 只实现 A2 已批准删改） |

**禁止：** 用额外 wrapper/静默吞异常/假通过测试等「防御性工程」代替修根因。

---

## 3. REPAIR.plan.md §1 行模板

| 来源 ID | 问题 | 根因修复（非兜底） | Skill | 验证命令 | 通过条件 | 已修复 |
| ------- | ---- | ------------------ | ----- | -------- | -------- | ------ |

---

## 4. 遗留规则

仅以下可记入 **§2 Deferred**（须写理由 + 后续任务 ID）：

- 故意设计（ENTRY §2 / `plan-doubt-review` 已记录）
- 依赖后续 ROUND 任务
- 需单独立项的大重构

其余 **全部在本轮 Repair 关闭**。

---

## 5. Repair 复验 vs Audit §2

| 阶段            | 跑什么                                                             |
| --------------- | ------------------------------------------------------------------ |
| **Audit**       | AUDIT.plan **§1** 维度验证（audit-sandbox；非 INDEX §2.1 全复跑）  |
| **Repair 收尾** | **INDEX §2.1** Tier A/B/C + `uv run pytest -q`（Execute 回归门禁） |
| **复 Audit**    | 仅用户明确要求时重跑 AUDIT §2                                      |
