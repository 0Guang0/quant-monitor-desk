# MASTER 计划 — Round 0 项目脚手架（000–004 · retrospective）

> **Execute 入口** · Audit → `AUDIT.plan.md` · Repair → `REPAIR.plan.md`（Execute 不读）

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-17-round0-scaffold-audit` |
| 关联 Round | `ROUND_0_PROJECT_SCAFFOLD`（000–004） |
| Audit | `AUDIT.plan.md` |
| Repair | `REPAIR.plan.md`（Audit 后按需） |
| retrospective | 代码已实现（2026-06） |

Execute：见 **§0.1 门控**；6.pre → §8 证据 → §9 → §10 → §11 交接 Audit。

### 0.1 门控（摘要）

- **6.pre：** `research/gitnexus-execute-summary.md`（research 例外可读）
- **怎么测：** §9 四层；B/C = 仓库根验收（本 Round 无 DuckDB prod-path）
- **怎么验收：** §10 Execute 专用；Audit 见 AUDIT **§2**
- **什么叫过：** §8 证据 + §10 勾；任务完成 = Audit → Repair? → Finish

---

## 1. 目标

建立 quant-monitor-desk 项目骨架、全局执行规则、配置模板、测试基线与文档索引，使后续 Round 可独立执行。

---

## 2. 预期结果（A5 trace-ac 追溯用）

| # | 预期结果 | 验证链 |
|---|----------|--------|
| AC-1 | 全局规则四文件存在且可被测试引用 | §10 A + test_global_execution_rules |
| AC-2 | 目录骨架与 `docs/architecture/07` 一致 | §10 A + test_project_scaffold |
| AC-3 | 配置模板与 `.env.example` 可加载 | §10 A + test_config_templates |
| AC-4 | `docs/INDEX.md` 索引完整 | §10 A + test_documentation_index |
| AC-5 | FastAPI 占位可 import / smoke | §10 A + test_backend_smoke |

---

## 3. 范围与边界

- **含：** 000–004 五个任务；Round 0 测试（约 26 项）
- **不含：** DuckDB migration、WriteManager、数据源（Round 1+）

---

## 7. Red Flags

| Red Flag | 预防 |
|----------|------|
| `scripts/__init__.py` 使 CLI 变 package | 已删除 |
| conftest 未使用 fixture | 已移除 |
| 文档目录结构与实布局漂移 | 07_project_directory_structure 已同步 |

---

## 8. 实现步骤（retrospective · 已执行）

### 8.1–8.6 000–004 + backend smoke

各步验证：`pytest` 对应 test 文件；**证据** 2026-06 实现 + 三次审计修复；**已执行** [x]

---

## 9. 测试层次（四层必做）

| 层次 | 必做 | 环境 | 命令 | 通过条件 |
|------|------|------|------|----------|
| 单元 | ✅ | local | pytest Round 0 tests | 全绿 |
| 集成 | ✅ | local | pytest -q | exit 0 |
| 管道 | ✅ | prod-path | compileall backend scripts | exit 0 |
| smoke | ✅ | prod-path | ruff check . | 0 |

---

## 10. 验收 Tier 表（Execute 专用）

| Tier | 环境 | 命令 | 通过条件 | Execute 勾 |
|------|------|------|----------|------------|
| A | ci | pytest Round 0 test files -q | 全绿 | [x] |
| A | ci | ruff check . | 0 | [x] |
| B | prod-path | python -m compileall backend scripts | exit 0 | [x] |
| C | prod-path | pytest -q（全库 93/93） | exit 0 | [x] |

---

## 11. Execute 交接 DoD

- [x] §8/§9/§10/§12 完成
- [x] **交接 Audit**（勿 finish-work）

---

## 12. Execute Skill 冻结

| Skill | 本任务 | 已执行 |
|-------|--------|--------|
| test-driven-development | 必做 | [x] |
| incremental-implementation | 必做 | [x] |
| trellis-implement | 不用 | — |
