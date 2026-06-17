# REPAIR 计划 — GPT 多窗口审计（修复建议-临时文件.md）

> **Phase 8 · 复杂任务协议** · 输入：`AUDIT_VERIFICATION.md`  
> **状态：** Execute 完成（2026-06-17）· 延后项见 §4

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-17-gpt-audit-remediation` |
| 前置 | `修复建议-临时文件.md` 逐项复核 |
| 完成标准 | §3 全部 FIXED 项绿 + §4 DEFERRED 有明确阶段 |

---

## 1. 本次已执行修复（FIXED）

### Batch G-A — 写入与证据链

| 步骤 | 文件 | 变更 |
|------|------|------|
| G-A.1 | `backend/app/db/write_manager.py` | 禁止默认 stub gate；失败 audit 同连接；upsert 守卫 |
| G-A.2 | `backend/app/storage/file_registry.py` | 构造注入 `validation_report_id`；`raw_saved`/`pending_validation` |
| G-A.3 | `tests/test_write_manager.py` | `create_test_write_manager`；audit/upsert 新测 |
| G-A.4 | `backend/app/storage/file_registry.py` | **对抗性审计补修**：`own_transaction=True`，失败 validation 时 audit 不被外层 txn 回滚 |

### Batch G-B — Fetch 合约

| 步骤 | 文件 | 变更 |
|------|------|------|
| G-B.1 | `backend/app/datasources/fetch_result.py` | `NOT_PUBLISHED_YET` publish 语义 |
| G-B.2 | `backend/app/datasources/adapters/skeleton_base.py` | shape schema_hash；ISO as_of |
| G-B.3 | `tests/test_data_adapter_contract.py` 等 | 合约回归测 |

### Batch G-C — 资源与注册表

| 步骤 | 文件 | 变更 |
|------|------|------|
| G-C.1 | `backend/app/core/resource_guard.py` | `_dir_size_gb` 扫描预算 |
| G-C.2 | `backend/app/db/connection.py` | `max_temp_directory_size` |
| G-C.3 | `backend/app/datasources/source_registry.py` | YAML 缺失源 tombstone |

### Batch G-D — 治理与文档

| 步骤 | 文件 | 变更 |
|------|------|------|
| G-D.1 | `.github/workflows/ci.yml` | `permissions` + `concurrency` + production_gate |
| G-D.2 | `.github/dependabot.yml` | pip/npm/actions 每周 |
| G-D.3 | `scripts/production_gate.py` | stub/contract/dependabot 检查 |
| G-D.4 | `README.md` | 移除未安装 Polars 声明 |

---

## 2. §5 验收（Tier）

| Tier | 命令 | 预期 |
|------|------|------|
| A | `pytest -q` | 全绿 |
| A | `ruff check .` | 0 error |
| A | `python scripts/production_gate.py` | PASS |
| B | `pytest tests/test_write_manager.py tests/test_raw_store.py -q` | 写入/注册绿 |
| B | `pytest tests/test_adapter_skeletons.py -q` | Fetch 合约绿 |
| C | `python scripts/check_doc_links.py` | exit 0 |
| C | `cd frontend && npm audit --audit-level=high && npm run build` | 绿 |

---

## 3. 审计项 → 状态映射（精简）

| 审计 ID | 状态 |
|---------|------|
| WriteManager stub 默认 / audit 锁 / upsert | **FIXED** |
| FileRegistry stub-pass / parse_status | **FIXED** |
| NOT_PUBLISHED_YET / schema_hash / as_of | **FIXED** |
| ResourceGuard 扫描预算 / DuckDB temp 上限 | **FIXED** |
| SourceRegistry tombstone | **FIXED** |
| README Polars | **FIXED** |
| CI permissions + dependabot + production_gate | **FIXED** |
| API/前端 placeholder | **DEFERRED** |
| 真实 FetchPort ×5 | **DEFERRED** |
| Agent sandbox | **DEFERRED** |
| fetch_log DB CHECK migration | **DEFERRED** |
| CodeQL/gitleaks/bandit/pip-audit/mypy/cov95 | **DEFERRED** |
| Release MANIFEST / FINAL_AUDIT | **DEFERRED** |
| Orchestrator ResourceGuard 动作 | **DEFERRED** |

---

## 4. §Deferred 计划阶段

| 阶段 | Trellis / 路线图 | 内容 |
|------|------------------|------|
| **Batch C** | Round 2 Batch C PRD | `005_fetch_log_constraints.sql`；`DbValidationGate`；Port 异常分层 |
| **Batch D** | Round 2 Batch D | `security.yml`：gitleaks、pip-audit、bandit；Windows matrix；cov 90→95 |
| **Round 3** | Orchestrator Execute | ResourceGuard WARN/PAUSE/HARD_STOP 动作闭环 |
| **Round 4** | FastAPI + Frontend | `/api/data-health` 等；分页；Playwright；非 placeholder UI |
| **Round 5** | Release gate | `MANIFEST.json`、`FINAL_AUDIT_REPORT.md`、CodeQL、action SHA pin、AgentToolRegistry |

每项延后必须在对应阶段 PR 的 `implement.md` 中引用本表 ID，合并时关闭。

---

## 5. 禁止事项

- 不得在 production 路径恢复 `WriteManager(...)` 无 gate 或 `stub-pass-*` validation id（`production_gate.py` 会 fail）
- 不得在未完成 Round 4 前宣称 API/前端 production ready
- 不得跳过 Batch C 直接加 polars 依赖（除非 Layer 1 代码真实需要）
