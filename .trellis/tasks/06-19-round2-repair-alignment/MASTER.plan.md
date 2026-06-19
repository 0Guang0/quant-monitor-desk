# MASTER 计划 — Round 2.5 Repair Alignment

> **Execute 入口** · v1.0 · 2026-06-19  
> **Gate:** PASS required before Trellis task **017** (Round 3 Layer 1)

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-19-round2-repair-alignment` |
| 关联 | PR #14 修复包导入后对抗审计遗留 |
| 跟踪 | `docs/quality/ROUND2_REPAIR_ALIGNMENT_TRACKER.md` |

### 0.1 门控

| 项 | 值 |
|----|-----|
| **前置** | `master` post PR #14 merge · pytest 372+ green |
| **阻塞** | 未完成本计划 **不得** 启动 `017_implement_layer1_axis_loader.md` |
| **验收** | §2 AC 全绿 + tracker R2.5 行 DONE + full pytest/ruff |

---

## 1. 目标

闭合修复包导入后的 Round 2 契约漂移（非 Round 3 建模、非 Round 4 API）：

1. D-11：`DISABLED_SOURCE` + domain gating
2. `schema.sql` 对齐 migration 007 `write_audit_log`
3. `load_api_limits()` query budget 不可被 configs 覆盖
4. 文档诚实度（handoff / gap ledger partial）
5. legacy role 契约测试

**本批不做：** backfill 闭环、真实 FetchPort、`run_reconcile` 重抓、Layer 1–5、API 路由。

---

## 2. 预期结果（AC）

| ID | 预期结果 | 验证 |
|----|----------|------|
| R2.5-1 | `cn_equity_minute_bar` 调度前返回 `DISABLED_SOURCE`（写 fetch_log，不调 vendor） | `test_disabledPrimaryDomain_*` |
| R2.5-2 | `write_audit_log` 含 007 全部 ADD COLUMN（含 `traceback_digest`） | `test_syncAuditMigration007_*` |
| R2.5-3 | configs/spec `api_limits` 不能覆盖 query budget 四键 | `test_loadApiLimits_queryBudgetNotOverridden*` |
| R2.5-4 | `ROUND3_HANDOFF` 标明 R2.5 gate；gap ledger **partial** | 文档 diff |
| R2.5-5 | Shadow/Emergency + top-level `shadow_source` 拒绝 | `test_legacySourceRoles_*` |

---

## 3. Round 3 同步偿还（记录在 tracker，**不在本 Execute 实现**）

| ID | 项 |
|----|-----|
| R3-PARTIAL-1 | Backfill 不经 validator/clean — 文档或实现闭环 |
| R3-PARTIAL-2 | 首个真实 FetchPort 或 `run_full_load` 骨架 |
| R3-PARTIAL-3 | `run_reconcile` 真重抓 |

Round 3 Trellis MASTER 创建时必须从 tracker 复制以上 ID。

---

## 4. §8 TDD 步骤

### 8.1 R2.5-1 DISABLED_SOURCE

- [x] `FetchStatus` 含 `DISABLED_SOURCE`
- [x] `SourceRegistry.assert_domain_schedulable` + `disabled_fallback_source_ids`
- [x] `BaseDataAdapter.fetch` domain 检查先于 `assert_enabled`，返回 `DISABLED_SOURCE`
- [x] `test_disabledPrimaryDomain_returnsDisabledSource`（registry + adapter）
- [x] `test_fallbackDisabledByDefault_isSkippedUntilConfigured`

### 8.2 R2.5-2 schema 007

- [x] `specs/schema/schema.sql` 补 `traceback_digest` 等 007 列
- [x] `test_schema_contract` 扩展 007 `write_audit_log`

### 8.3 R2.5-3 api_limits

- [x] `QUERY_BUDGET_KEYS` 跳过合并
- [x] `test_loadApiLimits_queryBudgetNotOverriddenByLowerPriorityYaml`

### 8.4 R2.5-4 docs

- [x] `ROUND2_REPAIR_ALIGNMENT_TRACKER.md`
- [x] `ROUND3_HANDOFF.md` gate 段
- [x] `REPAIR_IMPORT_CODE_GAP_LEDGER.md` → partial

### 8.5 R2.5-5 legacy roles

- [x] `test_legacySourceRoles_forbiddenAsSourceRoles`
- [x] `test_legacySourceRoles_forbiddenTopLevelKeys`

### 8.6 全量回归

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\ruff.exe check .
.venv\Scripts\ruff.exe format --check .
```

---

## 5. 交接 Round 3

PASS 后：

1. Archive 或 complete 本 Trellis task
2. 更新 `ROUND3_HANDOFF.md` 移除 R2.5 阻塞
3. 创建 Round 3 task 时 MASTER §3 列入 R3-PARTIAL-1/2/3
4. 启动 `017_implement_layer1_axis_loader.md`
