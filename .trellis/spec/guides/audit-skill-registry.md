# Audit 阶段 — 维度 / Agent / Skill 候选词典

> Plan 填 `AUDIT.plan.md` §1（Skill）与 **§2（维度验证矩阵）** 时查阅。**Audit agent 不读本文。**

---

## 1. 标准维度 — Skill 冻结

| ID | 名称 | Agent | 执行者 | Skill |
|----|------|-------|--------|-------|
| A1 | Spec | audit-spec | 子 agent | trellis-check |
| A2 | 过度工程 | audit-ponytail | 子 agent | ponytail-review |
| A3 | 安全 | audit-security | 子 agent | security-and-hardening |
| A4 | 代码质量 | audit-quality | 子 agent | code-review-and-quality |
| A5 | 完成情况 | audit-completion | 子 agent | verification-before-completion |
| A6 | 性能 | audit-perf | 子 agent | 项目脚本 / systematic-debugging |
| A7 | 运维 | audit-ops | 子 agent | — |
| A8 | 测试缺口 | audit-test-gap | 子 agent | — |
| A9 | 风险汇总 | — | **主会话** | — |

---

## 2. 维度验证默认模板（Plan 写入 AUDIT.plan §2）

> **与 MASTER §10 无关。** Execute 验收冻在 MASTER；Audit 验证冻在 AUDIT §2。  
> 验证类型：`static` | `read-only` | `review-only` | `trace-ac` | `pytest-isolated` | `cli-sandbox`

| 维 | 验证焦点 | 验证类型 | 典型命令 / 检查 | 环境 | 隔离 | 通过条件（摘要） |
|----|----------|----------|-----------------|------|------|------------------|
| **A1** | Spec 合规、依赖完整 | read-only | trellis-check；diff vs check.jsonl；GitNexus 未声明依赖 | local | 无写 | 无未授权偏离 |
| **A2** | 过度工程 | review-only | ponytail-review；Lxx + net lines | — | — | 无必删 bloat |
| **A3** | 安全 | static | 威胁面；密钥/URL grep；注入点 | local | 无写 | 无 P0/P1 未缓解 |
| **A4** | 代码质量 | review-only | code-review-and-quality 多轴 | — | — | 无阻塞项 |
| **A5** | AC 完成度、证据可信 | trace-ac | 逐条 MASTER §2 ↔ 验证链；1–5 分 | local | 无写 | AC 均可追溯 ≥4 |
| **A5** | （条件）证据抽检 | cli-sandbox | 可疑 Tier B/C **1 行**于 AUDIT_DATA_ROOT | audit-sandbox | 独立 DATA_ROOT | 与 Execute 声称一致 |
| **A6** | 性能/资源 | cli-sandbox | profiling / 资源脚本 | audit-sandbox | `.audit-sandbox/` | 指标 ≤ 阈值 |
| **A7** | 运维/幂等/日志 | cli-sandbox | init/migrate  walkthrough | audit-sandbox | 独立 DATA_ROOT | 幂等；失败可观测 |
| **A8** | 测试缺口 | pytest-isolated | 补 §7 Red Flags / 边界用例 | audit-sandbox | tmp DB / `@audit` marker | 新测绿或入 §4.3 |

### 2.1 谁需要 prod-path-like（audit-sandbox）

| 角色 | audit-sandbox | Execute prod-path | 真实生产 |
|------|---------------|-------------------|----------|
| Execute §9 B/C、§10 B/C | 否 | **必须** | 否 |
| A1–A4 | 否 | 否 | 否 |
| A5 追溯 | 否 | 否（读证据） | 否 |
| A5 抽检 | **必须** | 否 | 否 |
| A6、A7、A8（A6 **未跳过**时） | **必须** | 否 | 否 |
| A6 **Plan 跳过** | 否 | 否 | 否 |
| Repair 收尾 | 否 | **复跑 MASTER §10 B/C** | 否 |

### 2.2 Plan 填 §2：`{{}}` 与 A6 跳过

- **`{{}}` 占位符**：Plan 须换成可执行命令/路径；留空 = 未冻结。说明见 [AUDIT 模板 §2.1](./templates/AUDIT.plan.md)。
- **A6 无性能要求**：§1 标「不用」；§2 写 SKIP 行 + 一句理由；Audit 在 §3.6 注 SKIP。说明见 [AUDIT 模板 §2.2](./templates/AUDIT.plan.md)。

---

## 3. GitNexus / CodeGraph

| 时机 | 产出 |
|------|------|
| 6.pre（Execute） | `gitnexus-execute-summary.md` |
| 7.pre（Audit） | `gitnexus-audit-summary.md` |
| A1–A8 | 读 audit 摘要 + ≥1 query → audit.report §3.x |

---

## 4. 双契约速查

| 契约 | 文件 | 执行者 |
|------|------|--------|
| Execute 验收 | MASTER §8–§10 | Execute |
| Audit 维度验证 | AUDIT §2 | A1–A8 |
| Repair 回归 | MASTER §10 | Repair |

---

## 5. A9 / Repair / Finish

- A9 主会话：§3.x → §4 / §4.3
- PASS（无 §4.3）→ Phase 9
- PASS_WITH_FIXES / FAIL → REPAIR.plan → Phase 8
