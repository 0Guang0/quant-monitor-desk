# GitNexus + CodeGraph Execute 前刷新摘要（6.pre）

> **任务：** `06-17-round2-batch-a-sources` · Batch A Execute 开场  
> **日期：** 2026-06-17  
> **HEAD：** `3d7f93a`（Round 0/1 remediation + schema contract 扩展）  
> **不覆盖：** Plan 阶段 `research/gitnexus-summary.md`

---

## 1. 索引刷新

| 工具 | 命令 | 结果 |
|------|------|------|
| **GitNexus** | `node .gitnexus/run.cjs analyze` | **成功** · 增量：changed=30, added=9 · **2,231 nodes · 2,688 edges · 19 clusters · 18 flows** |
| **CodeGraph** | `npx @colbymchenry/codegraph sync` + `index` | **成功** · 111 files · **920 nodes · 2,315 edges** · index up to date |

---

## 2. GitNexus 关键查询（Batch A 相关）

| 查询 | 结论 |
|------|------|
| `query("schema migration apply_migrations ingestion datasource")` | 命中 `apply_migrations` → `init_db` → `ConnectionManager`；**无** SourceRegistry / FetchLogWriter / BaseDataAdapter 流程 |
| `impact(apply_migrations, upstream, includeTests)` | **HIGH** — 47 符号；d=1 含 `test_schema_migration`×6、`init_db.main`、smoke/raw_store/write_manager 等 |
| `impact(ConnectionManager, upstream, includeTests)` | **MEDIUM** — 6 符号 |
| `context(WriteManager)` | 入向：file_registry + 测试；**无** `backend/app/datasources/` |
| `detect_changes(compare, master)` | 低危：文档/AGENTS 变更；无代码 symbol 影响 |

**解读：** 003 landing 将 HIGH 冲击 migration 上游；ingestion 层 Execute 前在图中为空白，Execute 后需再次 `analyze`。

---

## 3. CodeGraph 关键查询

| 命令 | 结论 |
|------|------|
| `status` | 920 nodes · WAL journal OK |
| `query apply_migrations` | 函数 @ `migrate.py:54`；6+ 测试 import |
| `explore migration schema datasource` | 46 symbols；`verify_applied_checksums` **无** 覆盖测试 |
| `impact apply_migrations` | **51 affected symbols**（与 GitNexus 同阶） |
| `node WriteManager` | 9 methods @ `write_manager.py`；无 datasources 边 |

**GitNexus vs CodeGraph：** `apply_migrations` blast radius **一致（HIGH）**；ingestion 符号 **均为 0**（代码未建）。

---

## 4. 当前 codebase 快照（对抗审计基线）

| 项 | 值 |
|----|-----|
| pytest 收集 | **105** tests |
| migrations | `001_foundation` · `002_registry_hardening`（无 003） |
| `backend/app/datasources/` | 仅 `__init__.py` |
| `specs/schema/schema.sql` | 含 `source_registry` + **`fetch_log`**（v1.3 remediation） |
| `tests/test_schema_contract.py` | 6 表（001/002）；003 扩展 **Execute §8.1 待实现** |
| `tests/conftest.py` | 7 行（§8.0 扩展 **Execute 待实现**） |
| CI | pytest+cov+ruff+compileall+grep（v1.3 · Tier B/C 仍非 CI） |

---

## 5. 对抗审计结论（双 agent · remediation 完成）

**Plan BLOCK → 已解除（MASTER v1.3）** — 全表：`research/adversarial-audit-remediation.md`

| 类别 | 状态 |
|------|------|
| P0–P3 plan/文档/CI/schema | **已修复** |
| Execute §8 代码（E1–E11） | **未修复 · 待实现**（remediation 明确列出） |
| Batch D / B / C 延后项 | **未修复 · 已标注批次** |

---

## 6. Execute 6.pre 勾选

- [x] GitNexus analyze
- [x] CodeGraph sync/index
- [x] 对抗审计（双 agent）
- [x] MASTER v1.3 + remediation 全表
- [ ] Execute §8.0 启动（**代码 · 仍未做**）
