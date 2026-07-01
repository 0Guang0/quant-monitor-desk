# Round 0 / Round 1 待修复文件清单（GPT 审计复核）

> **复核方式：** 主会话逐项对照代码 + 命令（Composer 2.5 子 agent 两次派发均被中断，未完成独立双审）。  
> **复核日期：** 2026-06-17  
> **结论标签：** `CONFIRMED` 属实 · `PARTIAL` 部分属实/有设计豁免 · `REJECTED` 不成立 · `GAP` 能力缺口（非 GPT 标号但需修）

---

## 1. 复核总览

| 级别                | 条目数 | 确认需修 | 部分/政策 | 驳回  |
| ------------------- | ------ | -------- | --------- | ----- |
| P0                  | 4      | 4        | 0         | 0     |
| P1                  | 5      | 3        | 2         | 0     |
| 安全（未标 P）      | 4      | 2        | 2         | 0     |
| 质量门禁（§九 GAP） | 6      | 6        | 0         | 0     |
| P2 / 维护性         | 5      | 0        | 5         | 0     |
| **合计**            | **24** | **15**   | **9**     | **0** |

**Round 2 准入建议：** 先完成 **Repair Batch A + B**（P0 + 核心 P1），再启动 Batch A Execute；质量门禁（Batch D）可与 Round 2 并行但应在首个 Round 2 PR 合并前落地。

---

## 2. P0 — 必须修复

| ID       | GPT 描述                                               | 复核          | 证据                                                                                                                                                                                                                                                                                                                                                                                                     | 待修文件                                                                                                                                                                          |
| -------- | ------------------------------------------------------ | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P0-1** | clean checkout 下 `pytest -q` 失败（缺 `data/duckdb`） | **CONFIRMED** | `tests/test_project_scaffold.py` L20–30 要求 `data/duckdb` 目录存在；`.gitignore` L18 忽略 `data/duckdb/`；`git ls-files data/` 无输出（目录未入库）；`init_db.py` L12 仅在运行脚本时 `mkdir`，**pytest 不会调用**                                                                                                                                                                                       | `tests/test_project_scaffold.py` · `README.md` · 可选 `scripts/ensure_data_dirs.py`                                                                                               |
| **P0-2** | 前端 3 个 high severity（vite/esbuild）                | **CONFIRMED** | `npm audit`：`esbuild` GHSA-gv7w-rqvm-qjhr；`vite@^6.0.3` · `@vitejs/plugin-react@^4.3.4` 依赖链；`npm audit fix --force` 提示升至 vite@8（breaking）                                                                                                                                                                                                                                                    | `frontend/package.json` · `frontend/package-lock.json` · 或 `docs/ops/security_exception.md`                                                                                      |
| **P0-3** | `reader()` 未应用 DuckDB 资源 pragma                   | **CONFIRMED** | `connection.py` L171–178：`reader()` 仅 `connect(read_only=True)`；`_apply_pragmas` 仅在 `writer()` L164 调用；`test_duckdb_connection.py` 仅测 writer pragma，**无 reader 用例**                                                                                                                                                                                                                        | `backend/app/db/connection.py` · `tests/test_duckdb_connection.py`                                                                                                                |
| **P0-4** | ResourceGuard 配置字段未完全生效                       | **PARTIAL**   | `evaluate()` 仅用 memory/disk/project*size/process_rss（`resource_guard.py` L72–120）；`duckdb_temp_max_gb` / `cache*_*gb`/`system*__pct`在`configs/resource_limits.yaml`与 contract 中存在但未读。**DECISIONS.md Round 1 §7 明确**`cache__`、`system\__\_pct`留 Round 2+；GPT 建议 Round 1 全接入与 DECISIONS 冲突 → 按 **准入条件** 至少接入`duckdb_temp_max_gb` + cache 目录 guard，其余可标 Deferred | `backend/app/core/resource_guard.py` · `configs/resource_limits.yaml` · `tests/test_resource_guard.py` · `docs/implementation_tasks/ROUND_1_DATA_FOUNDATION/DECISIONS.md`（澄清） |

---

## 3. P1 — 建议修复

| ID       | GPT 描述                                       | 复核                | 证据                                                                                                                                                                                                                      | 待修文件                                                                                                                                                                             |
| -------- | ---------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **P1-1** | `docs/INDEX.md` 坏链接                         | **CONFIRMED**       | L10 指向 `01_context_and_problem.md`（实为 `01_context_and_scope.md`）；L15 指向 `06_phase_plan.md`（实为 `09_phase_plan.md`）                                                                                            | `docs/INDEX.md`                                                                                                                                                                      |
| **P1-2** | `schema.sql` 与 migrations 关系不清            | **PARTIAL**         | DECISIONS §3 已写「migrations 运行时 truth · schema.sql 只读参考」；**缺口**是无自动化对齐测试，Round 2 易 drift                                                                                                          | `docs/implementation_tasks/ROUND_1_DATA_FOUNDATION/DECISIONS.md`（加一节）· **新建** `tests/test_schema_contract.py` · `specs/schema/schema.sql` · `backend/app/db/migrations/*.sql` |
| **P1-3** | `own_transaction=False` 失败审计开新连接有风险 | **PARTIAL**         | `write_manager.py` L144–164 已实现独立 `audit_con`；`test_write_manager.py` L234–248 验证外层 txn 不被 rollback。**残余风险**：外层已持 write lock 时再开第二写连接可能锁冲突（单进程 FileRegistry 路径下可复现理论风险） | `backend/app/db/write_manager.py` · `tests/test_write_manager.py` · `backend/app/storage/file_registry.py`                                                                           |
| **P1-4** | FileRegistry 并发重复注册                      | **PARTIAL**         | 单 writer 锁下串行安全；`test_register_duplicateHash_returnsSameFileId` 覆盖同进程重复。**多进程**两 writer 先后预查为空仍可能双写 — `content_hash` 无 DB 唯一约束时无法优雅 dedupe                                       | `backend/app/db/migrations/002_registry_hardening.sql`（若加 UNIQUE）· `backend/app/storage/file_registry.py` · `tests/test_raw_store.py`                                            |
| **P1-5** | `.cursor/` / `.trellis/` 是否入库              | **PARTIAL（政策）** | `.cursor/` 与 `.trellis/` 已大量 `git ls-files` 跟踪；为 Trellis 工作流 intentional。**需文档化**边界，非代码 bug                                                                                                         | `README.md` 或 `docs/ops/agent_workflow_boundaries.md` · `.gitignore`（若决定 workspace 不入库）                                                                                     |

---

## 4. 安全（GPT §六）

| ID        | 描述                                   | 复核          | 证据                                                                                                                    | 待修文件                                                                   |
| --------- | -------------------------------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| **SEC-1** | 前端 high vuln                         | 同 **P0-2**   | 见上                                                                                                                    | 见上                                                                       |
| **SEC-2** | `.cursor/hooks` 执行 Python            | **PARTIAL**   | `.cursor/hooks/inject-*.py` 存在；仅 Cursor 环境生效。需文档说明信任边界                                                | `docs/ops/agent_workflow_boundaries.md`                                    |
| **SEC-3** | `.trellis/workspace` 过程记录          | **PARTIAL**   | 任务日志在 `.trellis/tasks/`；是否 ignore 属政策                                                                        | `.gitignore` · Trellis 文档                                                |
| **SEC-4** | `QMD_DATA_ROOT=` 空字符串 → `Path("")` | **CONFIRMED** | `config.py` L9：`Path(os.getenv("QMD_DATA_ROOT", PROJECT_ROOT / "data"))` — 空 env 不走 default；`.env.example` L8 为空 | `backend/app/config.py` · `.env.example` · **新建** `tests/test_config.py` |

---

## 5. 质量门禁缺口（GPT §九，未标 P 级）

| ID        | 描述                                  | 复核          | 证据                                                                       | 待修文件                                                        |
| --------- | ------------------------------------- | ------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **GAP-1** | 无 `npm audit` CI 门禁                | **CONFIRMED** | 无 `.github/workflows/`；`frontend/package.json` 无 audit script           | **新建** `.github/workflows/ci.yml` 或 `scripts/ci_frontend.sh` |
| **GAP-2** | 无 coverage 门禁                      | **CONFIRMED** | `pyproject.toml` 无 pytest-cov / coverage 配置                             | `pyproject.toml` · `tests/` · CI workflow                       |
| **GAP-3** | 无 docs link check                    | **CONFIRMED** | 无 link checker script；P1-1 坏链未自动发现                                | **新建** `scripts/check_doc_links.py` · CI                      |
| **GAP-4** | 无 schema contract vs migrations 测试 | **CONFIRMED** | 仅 `test_schema_migration.py` 测 migration 行为，未对照 `schema.sql` 列/表 | **新建** `tests/test_schema_contract.py`                        |
| **GAP-5** | 无 reader pragma 测试                 | **CONFIRMED** | `test_duckdb_connection.py` 无 reader 分支                                 | `tests/test_duckdb_connection.py`                               |
| **GAP-6** | clean checkout pytest（同 P0-1）      | **CONFIRMED** | 见 P0-1                                                                    | 见 P0-1                                                         |

---

## 6. P2 / 维护性（GPT §八）

| ID       | 描述                                      | 复核         | 建议                                                                   |
| -------- | ----------------------------------------- | ------------ | ---------------------------------------------------------------------- | -------------------------------- |
| **P2-1** | `ops_and_performance_v1_2.md` 旧文件名    | **PARTIAL**  | 文件仍存在且 INDEX 可链；属命名 legacy                                 | Round 5 或轻量 alias/README 注记 |
| **P2-2** | `fastapi_and_frontend.md` vs 拆分模块重复 | **PARTIAL**  | 需人工读 diff；非阻塞                                                  | 文档索引加「canonical」注记      |
| **P2-3** | validation 相关 module 文档重叠           | **PARTIAL**  | 同上                                                                   | 同上                             |
| **P2-4** | `.trellis/.cursor` 仓库噪音               | 同 **P1-5**  | 政策项                                                                 | 见 P1-5                          |
| **P2-5** | GPT 提 `pytest.ini`                       | **REJECTED** | 项目用 `pyproject.toml` `[tool.pytest.ini_options]`，无独立 pytest.ini | 无需修                           |

---

## 7. 按文件聚合的修复清单

| 文件                                                             | 关联 ID     | 动作                                                                      |
| ---------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------- |
| `tests/test_project_scaffold.py`                                 | P0-1        | 改为断言 `init_db`/脚本可创建目录，或移除对 git 跟踪 runtime 目录的硬要求 |
| `README.md`                                                      | P0-1, P1-5  | 补充 clean checkout 步骤；Agent/Trellis 边界                              |
| `backend/app/db/connection.py`                                   | P0-3, GAP-5 | `reader()` 调用 `_apply_pragmas`（或 read 专用变体）                      |
| `tests/test_duckdb_connection.py`                                | P0-3, GAP-5 | 新增 reader pragma 断言                                                   |
| `backend/app/config.py`                                          | SEC-4       | 空 `QMD_DATA_ROOT` / `QMD_CONFIGS_ROOT` fallback                          |
| `.env.example`                                                   | SEC-4       | 注释说明勿留空或删空行                                                    |
| `tests/test_config.py`                                           | SEC-4       | **新建**                                                                  |
| `frontend/package.json` (+ lock)                                 | P0-2, GAP-1 | 升级 vite 链或记录 security exception                                     |
| `backend/app/core/resource_guard.py`                             | P0-4        | 接入 temp/cache 阈值（按 Repair 批次 B 范围）                             |
| `tests/test_resource_guard.py`                                   | P0-4        | 补 temp/cache 用例                                                        |
| `docs/INDEX.md`                                                  | P1-1, GAP-3 | 修正链接                                                                  |
| `docs/implementation_tasks/ROUND_1_DATA_FOUNDATION/DECISIONS.md` | P1-2, P0-4  | 明确 schema 双源规则 + 未接入阈值时间表                                   |
| `tests/test_schema_contract.py`                                  | P1-2, GAP-4 | **新建** foundation 表列对齐                                              |
| `backend/app/db/write_manager.py`                                | P1-3        | 评估失败 audit 是否复用 `con`（仅 own_transaction=False）                 |
| `backend/app/storage/file_registry.py`                           | P1-4        | 唯一约束冲突 → 返回既有 file_id                                           |
| `.github/workflows/ci.yml`                                       | GAP-1–3     | **新建** pytest + ruff + npm audit + link check                           |
| `pyproject.toml`                                                 | GAP-2       | pytest-cov + fail_under                                                   |
| `scripts/check_doc_links.py`                                     | GAP-3       | **新建**                                                                  |
| `docs/ops/security_exception.md`                                 | P0-2        | 若暂不升级 vite                                                           |
| `docs/ops/agent_workflow_boundaries.md`                          | P1-5, SEC-2 | **新建**（可选）                                                          |

---

## 8. 与 Round 1 Trellis Audit 的关系

Round 1 `06-17-round1-foundation-audit` 结论为 **PASS**、§4.3 无项。本清单来自 **外部 GPT 全仓 zip 审计**，覆盖 Round 1 Audit **未测**维度（clean checkout、npm audit、reader pragma、schema contract、CI 门禁）。二者不矛盾：Round 1 Audit 验证的是 **已 Execute 的 AC**；本清单是 **Round 2 准入加固**。

---

## 9. 验证命令（Repair 完成后必跑）

```bash
# 模拟 clean checkout（无 data/duckdb）
# Windows: Remove-Item -Recurse -Force data\duckdb -ErrorAction SilentlyContinue
pytest -q
ruff check .
python -m compileall -q backend scripts tests
cd frontend && npm ci && npm audit && npm run typecheck && npm run build
python scripts/check_doc_links.py   # Repair Batch D 后
pytest --cov=backend --cov-fail-under=...   # Repair Batch D 后
```
