# GPT 多窗口审计复核报告

> **输入：** `修复建议-临时文件.md`（ponytail / gstack / Anthropic skills 合并审计）  
> **复核日期：** 2026-06-17  
> **复核方式：** 对照当前仓库源码 + pytest/ruff/production_gate  
> **标签：** `CONFIRMED` 属实 · `PARTIAL` 部分属实/按路线图延后 · `REJECTED` 不成立 · `FIXED` 本次已修 · `DEFERRED` 已文档化延后

---

## 1. 总览

| 来源章节 | 条目约数 | 本次 FIXED | DEFERRED | REJECTED/PARTIAL |
|----------|---------|------------|----------|------------------|
| WriteManager / 写入安全 | 8 | 6 | 1 | 1 |
| 数据源 / Fetch 合约 | 12 | 4 | 6 | 2 |
| ResourceGuard / DuckDB | 6 | 3 | 2 | 1 |
| CI / 供应链 | 15 | 4 | 9 | 2 |
| API / 前端 | 8 | 0 | 8 | 0 |
| Agent 安全 | 6 | 0 | 6 | 0 |
| 文档 / Release | 10 | 1 | 8 | 1 |
| 架构 / 战略（未标 P 级） | 20+ | 0 | 15+ | 5+ |

**结论：** 审计中 **可立即在 Round 2 前完成的代码级 P0/P1 已修复**；API/前端/Agent/真实 FetchPort/Release 95 分门禁属 **Round 3–5**，见 `REPAIR.plan.md` §Deferred。

---

## 2. P0 复核

| ID | 审计描述 | 复核 | 处理 |
|----|----------|------|------|
| **WM-P0-1** | `WriteManager` 默认 `StubValidationGate()` | **CONFIRMED** | **FIXED** — 必须显式传入 gate；新增 `create_test_write_manager()` |
| **WM-P0-2** | 失败 audit 绕过单写锁（裸 `duckdb.connect`） | **CONFIRMED** | **FIXED** — `own_transaction=True` 时在同 writer 连接上 BEGIN→audit→COMMIT |
| **WM-P0-3** | `upsert_by_pk` 空 PK / staging 重复 / `SELECT *` | **CONFIRMED** | **FIXED** — PK 非空校验、staging 去重、显式列 INSERT |
| **FR-P0-1** | `FileRegistry` 硬编码 `stub-pass-registry` | **CONFIRMED** | **FIXED** — 构造时注入 `validation_report_id`；测试显式传 stub |
| **API-P0-1** | FastAPI 仅 `/health` placeholder | **CONFIRMED** | **DEFERRED → Round 4** |
| **DS-P0-1** | 真实 FetchPort 未落地 | **CONFIRMED** | **DEFERRED → Batch C/D** |
| **DOC-P0-1** | README Polars vs pyproject 不一致 | **CONFIRMED** | **FIXED** — README 移除 Polars Lazy；未使用的 polars/pyarrow 不加依赖（ponytail 最小化） |
| **NP-P0-1** | `NOT_PUBLISHED_YET` 需 publish 语义 | **CONFIRMED** | **FIXED** — `FetchResult` validator 强制 error_message 含 publish |
| **AG-P0-1** | Agent runtime sandbox 未实现 | **CONFIRMED** | **DEFERRED → Round 5 / PR-6** |
| **Round01 P0-1~4** | clean checkout / vite / reader pragma / RG | 见 `GPT_ROUND01_REPAIR_STATUS.md` | **已修复（前序 Repair）** |

---

## 3. P1 复核

| ID | 审计描述 | 复核 | 处理 |
|----|----------|------|------|
| **P1-1 schema_hash** | 仅 hash 顶层 key | **CONFIRMED** | **FIXED** — canonical shape fingerprint |
| **P1-2 as_of** | `end_time[:10]` 过宽 | **CONFIRMED** | **FIXED** — ISO/date 校验，非法 → FAILED |
| **P1-3 fetch_log DB CHECK** | 缺 migration 005 | **CONFIRMED** | **DEFERRED → Batch C**（DuckDB ALTER CHECK 需表重建策略） |
| **P1-4 SourceRegistry tombstone** | YAML 删除源残留 DB | **CONFIRMED** | **FIXED** — `sync_to_db(tombstone_missing=True)` |
| **P1-5 安全 CI** | gitleaks/bandit/pip-audit/CodeQL | **PARTIAL** | **PARTIAL FIXED** — permissions、dependabot、production_gate；其余 **DEFERRED → Batch D** |
| **P1-6 覆盖率/mypy** | fail_under 75、无 mypy | **CONFIRMED** | **DEFERRED → Batch D**（当前维持 75，核心模块单独 95 为下一阶段） |
| **P1-7 max_temp_directory_size** | ConnectionManager 未设置 | **CONFIRMED** | **FIXED** |
| **P1-8 FileRegistry parse_status** | 注册即 `parsed/ok` | **CONFIRMED** | **FIXED** — `raw_saved` / `pending_validation` |
| **P1-9 BaseAdapter 吞异常** | 全变 FAILED | **PARTIAL** | **DEFERRED** — Skeleton 已用 `PortError`；系统错误分层 **Batch C** |
| **P1-10 Release manifest** | 无 MANIFEST.json | **CONFIRMED** | **DEFERRED → Round 5** |
| **P1-11 依赖锁定** | 无 lockfile | **PARTIAL** | **DEFERRED** — frontend 有 package-lock；Python uv.lock **Batch D** |

---

## 4. P2 / P3 / 未标级项

| 主题 | 复核 | 阶段 |
|------|------|------|
| ResourceGuard 动作闭环（Orchestrator WARN/PAUSE） | **CONFIRMED 未实现** | Round 3 Batch D |
| 前端 placeholder → contract UI | **CONFIRMED** | Round 4 |
| `.cursor/hooks` bandit / CODEOWNERS | **PARTIAL** | Batch D |
| OpenSSF Scorecard / action SHA pin / SBOM | **CONFIRMED 缺失** | Batch D / Round 5 |
| make dev 单命令 bootstrap | **CONFIRMED 缺失** | Round 5 DevEx |
| data lineage / provenance hash chain | **CONFIRMED 缺失** | Round 5+ |
| 层间强约束 runtime enforce | **PARTIAL** | 随各 Batch 契约测试递增 |
| boot auto-bootstrap guard | **PARTIAL** | README 已文档化 init_db；自动化 **Round 5** |
| Agent read-only 仅文档 | **CONFIRMED** | Round 5 PR-6 |
| `.env` 暴露面 / vault | **PARTIAL** | `.env.example` 已规范；vault **Round 5** |
| 文档 dedupe（fastapi_and_frontend 等） | **PARTIAL** | Round 5 文档一致性门禁 |
| P2-5 pytest.ini | **REJECTED** | 项目用 pyproject `[tool.pytest.ini_options]` |
| NOT_PUBLISHED_YET 已被折叠成 EMPTY | **REJECTED** | 当前 fetch_log 已映射 `not_published` |
| create_adapter 默认 StubFetchPort | **REJECTED** | Batch B 已修复 |

---

## 5. 本次验收命令

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
python -m compileall -q backend scripts tests
python scripts/production_gate.py
python scripts/check_doc_links.py
cd frontend && npm ci && npm audit --audit-level=high && npm run typecheck && npm run build
```

---

## 6. 与 Round 01 Repair 关系

Round 01（`06-17-round01-remediation`）已关闭 clean checkout、reader pragma、vite、ResourceGuard 阈值等项。  
本任务覆盖 **GPT 临时文件中新一批 WriteManager / FileRegistry / Fetch 合约 / CI 加固**，不重复已关闭项。
