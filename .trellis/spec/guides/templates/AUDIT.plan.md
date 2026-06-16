# Audit 计划 — {{任务标题}}

> **读者：** 主会话 + A1–A8 子 agent  
> **必读：** 本文 + `audit.jsonl` · 各维执行 **§2** · A5 另读 MASTER **§2** · A1 另读 `check.jsonl` · Execute **§10 证据只读**（非复跑）

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| 任务 slug | `{{slug}}` |
| audit.jsonl | 第一条 = 本文件 |
| 验证词典 | `.trellis/spec/guides/audit-skill-registry.md` §2（Plan 填 §2 时查阅） |

**编排规则：**

1. **7.pre（主会话 · Execute 交接后）**：刷新 GitNexus / CodeGraph → `research/gitnexus-audit-summary.md`。
2. **7.0（主会话）**：汇总 **§2 各维验证证据** + Execute §10 证据索引（只读）→ `audit.report.md` §2。
3. **7.1–7.8**：按 §1 派发 **A1–A8**；各 agent 执行 **§2 本维冻结验证** + GitNexus/CodeGraph（§3）。
4. **7.9（主会话）**：A9 汇总 §4 / §4.3。
5. **PASS（无 §4.3）** → Phase 9；**PASS_WITH_FIXES / FAIL** → `REPAIR.plan.md` → Phase 8。

---

## 1. 维度 — Agent — Skill 冻结清单

| 维度 | Agent ID | 执行者 | Skill（冻结） | 本任务 | GitNexus | `@` 指令（派发用） | 产出 | 已执行 |
|------|----------|--------|---------------|--------|----------|-------------------|------|--------|
| A1 | audit-spec | 子 agent | trellis-check | 必做 | 必用 | 执行 §2 A1 行；对照 check.jsonl | §3.1 | [ ] |
| A2 | audit-ponytail | 子 agent | ponytail-review | 必做 | 建议 | 执行 §2 A2 行 | §3.2 | [ ] |
| A3 | audit-security | 子 agent | security-and-hardening | {{}} | 必用 | 执行 §2 A3 行 | §3.3 | [ ] |
| A4 | audit-quality | 子 agent | code-review-and-quality | 必做 | 建议 | 执行 §2 A4 行 | §3.4 | [ ] |
| A5 | audit-completion | 子 agent | verification-before-completion | 必做 | 必用 | 执行 §2 A5 行 | §3.5 | [ ] |
| A6 | audit-perf | 子 agent | {{}} | {{}} | 必用 | 执行 §2 A6 行 | §3.6 | [ ] |
| A7 | audit-ops | 子 agent | — | {{}} | 必用 | 执行 §2 A7 行 | §3.7 | [ ] |
| A8 | audit-test-gap | 子 agent | — | 必做 | 必用 | 执行 §2 A8 行 | §3.8 | [ ] |
| **A9** | **—** | **主会话** | — | 必做 | 已刷新 | 汇总 A1–A8；写 §4（**非子 agent**） | §4 | [ ] |

---

## 2. 维度验证矩阵（Plan 冻结 · Audit 执行 · 非 MASTER §10）

> 每维 **至少一行**；命令/检查须 **正交于** Execute §10（除非 A5 条件抽检）。  
> 写库/CLI 行 **必须** 使用 audit-sandbox，路径 ≠ Execute `DATA_ROOT`。  
> 验证类型：`static` | `read-only` | `review-only` | `trace-ac` | `pytest-isolated` | `cli-sandbox`

| 维 | 验证类型 | 命令 / 检查 | 环境 | 隔离策略 | 通过条件 | 证据 → | 已执行 |
|----|----------|---------------|------|----------|----------|--------|--------|
| **A1** | read-only | trellis-check；diff vs `check.jsonl`；GitNexus query 未在 implement.jsonl 声明的依赖 | local | 无写 | 无未授权 spec 偏离；无 ghost 依赖 | §3.1 | [ ] |
| **A2** | review-only | ponytail-review：仅 over-engineering；每项 Lxx + net lines | — | — | 无必删 bloat 或已列 §4.3 | §3.2 | [ ] |
| **A3** | static | 威胁面清单；`rg` 密钥/硬编码 URL；SQL/路径注入点 | local | 无写 | 无 P0/P1 未缓解项 | §3.3 | [ ] |
| **A4** | review-only | code-review-and-quality：正确性/可读性/边界/错误处理 | — | — | 无阻塞 review 项或已列 §4.3 | §3.4 | [ ] |
| **A5** | trace-ac | 逐条对照 MASTER §2 AC ↔ §8/§9/§10 验证链；证据完整性 1–5 分 | local | 无写 | 每条 AC 可追溯；均 ≥4 分 | §3.5 | [ ] |
| **A5** | cli-sandbox | **条件**：Execute §10 B/C 证据可疑时，抽检 1 行于 `AUDIT_DATA_ROOT={{.audit-sandbox/}}` | audit-sandbox | 独立 DATA_ROOT | 与 Execute 声称一致 | §3.5 | [ ] |
| **A6** | cli-sandbox | `{{perf 命令，如 time/scripts/profile_*.py}}` | audit-sandbox | `.audit-sandbox/` | 指标 ≤ {{阈值}} | §3.6 | [ ] |
| **A7** | cli-sandbox | `DATA_ROOT={{.audit-sandbox/data}} {{init/migrate CLI}}` 幂等 walkthrough；查日志/锁 | audit-sandbox | 独立 DATA_ROOT | 幂等成立；失败可观测 | §3.7 | [ ] |
| **A8** | pytest-isolated | `pytest {{tests/audit/ 或 -k audit_}} --tmp-path {{}}` 补 MASTER §7 Red Flags / 边界 | audit-sandbox | tmp DB / `@pytest.mark.audit` | 新测全绿或缺口入 §4.3 | §3.8 | [ ] |

### 2.1 Plan 填表说明（`{{}}` 占位符 · 必读）

Plan 复制 §2 到任务 `AUDIT.plan.md` 后，**必须**把占位换成**本任务可执行**的内容；留 `{{}}` = 未冻结 = 禁止 `task.py start`。

| 占位 | 填什么 | 示例（005 schema） |
|------|--------|-------------------|
| `{{init/migrate CLI}}` | 本任务真实 CLI + 参数 | `python scripts/init_db.py` |
| `{{tests/audit/ 或 -k audit_}}` | A8 补测路径或 pytest 选择器 | `tests/test_schema_migration.py -k checksum` |
| `--tmp-path {{}}` | 临时目录（可写 `.audit-sandbox/pytest`） | `--basetemp=.audit-sandbox/pytest` |
| `{{perf 命令…}}` / `{{阈值}}` | 仅 **A6 要做性能审计时** 填写 | 见 §2.2 |

**原则：** 命令须与 Execute §10 **不同或更严**（正交验证）；写库须用 **audit-sandbox**，不得用 Execute 验收库路径。

### 2.2 A6「无性能要求」时怎么写（跳过 · 须书面理由）

本任务若无 hot path、SLA、Profiling 需求，**不要留空 A6**，按下面做：

**§1 表：** A6 行 `本任务` 列写 **不用**；Skill 列写 **—**；`@` 写「§2.2 已跳过」。

**§2 表：** 保留 **一行** A6，例如：

| 维 | 验证类型 | 命令 / 检查 | 环境 | 隔离策略 | 通过条件 | 证据 → | 已执行 |
|----|----------|-------------|------|----------|----------|--------|--------|
| **A6** | — | **本任务跳过** — {{一句理由，如：schema 初始化无性能 SLA}} | — | — | N/A（Plan 已记录跳过） | §3.6 注「SKIP」 | — |

Audit 阶段 A6 agent **不跑命令**，在 audit.report §3.6 写：`SKIP — 理由：…`（与 §2 一致）。

**若有性能要求：** 删掉跳过行，改填 §2.1 中 perf 命令与阈值，§1 A6 标 **必做**。

---

## 3. 工具要求（7.pre + 各维度 agent）

### 3.0 7.pre — 主会话（派发 A1–A8 之前 · 必做）

```bash
npx gitnexus analyze
# CodeGraph：刷新 implement.jsonl 触点
```

- 产出：`research/gitnexus-audit-summary.md`
- **未完成 7.pre 不得派发维度 agent**

### 3.1 各维度 agent 必做

- 读 `gitnexus-audit-summary.md`
- 执行 **§2 本维全部行**（非 MASTER §10 默认复跑）
- ≥1 次 GitNexus query/context 或 CodeGraph → 写入 audit.report §3.x

---

## 4. 验收汇总（7.0 · 主会话）

汇总 **§2 各维** 结果 + Execute §10 证据路径（只读引用）→ `audit.report.md` §2。

---

## 5. Audit DoD

- [ ] 7.pre 完成
- [ ] §2 每维至少一行 **已执行 + 证据非空**
- [ ] A1–A8 完成；A9 主会话 §4 已写
- [ ] PASS / PASS_WITH_FIXES / FAIL 已勾选

---

## 6. 编排器开场白（主会话）

```text
Execute 已交接（6.pre 已完成）。主会话 7.pre → gitnexus-audit-summary.md。
按 §1 派发 A1–A8：各 agent 执行 §2 本维验证（audit-sandbox，非复跑 MASTER §10）。
汇总 §2 证据 → audit.report §2；A9 写 §4/§4.3。
PASS_WITH_FIXES → REPAIR.plan.md → Repair。
```
