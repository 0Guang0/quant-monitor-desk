# Quant Monitor Desk

Local-first quantitative monitoring console: trusted data, five-layer modeling, evidence-chain monitoring, read-only Agent explanation, human confirmation.

**Not** an auto-trading system on day one. The workflow is:

```text
Trusted data → Multi-layer modeling → Evidence monitoring → Agent summary → Human review
```

## Stack

| Layer    | Technology                                                             |
| -------- | ---------------------------------------------------------------------- |
| Backend  | Python 3.11+, FastAPI, Pydantic, DuckDB (Parquet export via DuckDB when needed) |
| Frontend | Vite, React, TypeScript (layout is placeholder until user confirms UI) |
| Specs    | YAML / JSON / SQL contracts under `specs/`                             |
| Tooling  | `uv` + `uv.lock` (Python); `npm ci` + `package-lock.json` (frontend)   |

## Repository layout

```text
quant-monitor-desk/
  backend/              Application code
  frontend/             Dashboard shell (placeholder UI)
  scripts/              CLI entry points
  tests/                pytest suite
  configs/              Local configuration templates
  data/                 Runtime data (gitignored)
  docs/                 Architecture, modules, ops, implementation tasks
  specs/                Machine-readable contracts and domain specs
  MIGRATION_MAP.md      Docs/specs navigation map (authoritative design index)
  MANIFEST.json         Repaired implementation docs package manifest (2026-06-19)
  FINAL_AUDIT_REPORT.md Repaired package audit closure record
```

`docs/` 与 `specs/` 以 `MANIFEST.json` 中登记的修复包为权威口径。项目实施阶段产生的 Trellis/Batch 补充材料（如 `docs/implementation_tasks/**/plans/`、`DECISIONS.md`）不得覆盖上述权威文件。

## Getting started

1. Read `MIGRATION_MAP.md` and `docs/INDEX.md`.
2. Read global rules under `docs/implementation_tasks/GLOBAL_*.md`.
3. Read `specs/contracts/runtime_versions.md`（D-01：`uv.lock` 为 Python 主锁文件）。
4. Copy `.env.example` to `.env.local` and adjust paths if needed（D-03；空 `QMD_DATA_ROOT` 使用 `<repo>/data`）。
5. Install backend（默认）:

```bash
uv sync --locked
uv run python scripts/init_db.py
uv run pytest -q
uv run ruff check .
uv run python -m compileall -q backend scripts tests
uv run python scripts/check_doc_links.py
```

6. Install frontend:

```bash
cd frontend && npm ci && npm run typecheck && npm run build
```

**pip 备用路径**（仅当本机未安装 `uv` 时）：`pip install -e ".[dev]"`，须同步说明原因，不得替代 `uv.lock` 主路径。见 `specs/contracts/runtime_versions.md`。

`pytest -q` 在干净 checkout 上可不预先创建 `data/duckdb/`；`init_db.py` 仍用于 prod-path CLI 与 Tier B 验收。

### Agent / Trellis workflow

本仓库跟踪 `.cursor/`（IDE hooks）与 `.trellis/`（任务规格与工作流脚本）。信任边界与干净 checkout 步骤见 [`docs/ops/agent_workflow_boundaries.md`](docs/ops/agent_workflow_boundaries.md)。

## Implementation rounds

按顺序执行 `docs/implementation_tasks/`：

Round 0（scaffold）→ Round 1（data foundation）→ Round 2（ingestion）→ Round 3（modeling）→ Round 4（API/frontend/agent）→ Round 5（release）。

每个任务执行前读取该任务列出的输入文件、spec、contract、schema。前端页面布局、视觉风格、交互方式在正式实现前必须由用户确认（D-08）。

## 审计修复包（2026-06-19）

本仓库已导入 `quant_monitor_implementation_docs_v1` 修复包（见 `MANIFEST.json`、`FINAL_AUDIT_REPORT.md`）。重点新增/强化：

- `specs/contracts/api_security_contract.yaml` — API 分页与查询预算权威
- `specs/contracts/runtime_versions.md` — `uv.lock` 与验收命令
- `specs/datasource_registry/source_registry.yaml` — Primary / Validation / FallbackPolicy
- `docs/ops/*_policy.md` — secret、migration、并发、Agent/前端安全等
- `docs/quality/staged_acceptance_policy.md` — 分阶段验收

执行角色进入实施前，必须先读 `MIGRATION_MAP.md`、`docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md`、`specs/contracts/runtime_versions.md` 与 `docs/quality/staged_acceptance_policy.md`。

**修复包导入记录**：Phase 1–3 已完成（见 [`docs/quality/REPAIR_IMPORT_CODE_GAP_LEDGER.md`](docs/quality/REPAIR_IMPORT_CODE_GAP_LEDGER.md)，状态 closed）。修复包列出的部分 Round 4+ 契约测试仍待后续任务实现。

## 用户已拍板决策 D-01 至 D-12

执行角色不得再把以下事项作为未决项（权威记录：`docs/quality/PENDING_USER_DECISIONS.md`）：

```text
D-01 Python 依赖锁文件：采用 uv.lock；pip-tools 仅备用；不采用 Poetry。
D-02 API 鉴权：dev 可关闭但只能本机 loopback；prod 必须启用 Bearer token。
D-03 Secret 存储：第一版 .env.local；只提交 .env.example；CI 必须 secret scan。
D-04 Notification：默认前端 Notification Center；邮件可选；不启用多 webhook。
D-05 留存：raw/audit/report/notification 默认 1 年；提供手动归档按钮/CLI。
D-06 Migration：破坏性变更走备份恢复；非破坏性可无 down SQL。
D-07 Trellis/Cursor：每轮只保留 MASTER/AUDIT/DECISIONS；细碎 evidence 归档。
D-08 前端 UI：正式实现前必须提醒用户确认信息架构和交互，不写死 UI。
D-09 Layer 标准化：完整标准化字段仅 Layer 1；Layer 2-5 按需局部扩展。
D-10 设计包边界：设计包只放 docs/specs/tasks；源码和测试结果以 Git commit + CI 终审。
D-11 QMT：第一版默认禁用，用户配置并确认授权后启用。
D-12 Agent 来源：只读固定 source adapter + 用户手动导入文本；禁止自由联网搜索。
```

## Resource profile

默认模式为 **eco**。见 `configs/resource_limits.yaml`（运行时）与 `specs/contracts/resource_limits.yaml`（契约；API 分页权威见 `specs/contracts/api_security_contract.yaml`）。

## Rules

文档类文件请尽量用中文来撰写。
