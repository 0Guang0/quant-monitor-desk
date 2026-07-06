# Quant Monitor Desk

Local-first quantitative monitoring console: trusted data, five-layer modeling, evidence-chain monitoring, read-only Agent explanation, human confirmation.

**Not** an auto-trading system on day one. The workflow is:

```text
Trusted data → Multi-layer modeling → Evidence monitoring → Agent summary → Human review
```

## Stack

| Layer    | Technology                                                                      |
| -------- | ------------------------------------------------------------------------------- |
| Backend  | Python 3.11+, FastAPI, Pydantic, DuckDB (Parquet export via DuckDB when needed) |
| Frontend | Vite, React, TypeScript (layout is placeholder until user confirms UI)          |
| Specs    | YAML / JSON / SQL contracts under `specs/`                                      |
| Tooling  | `uv` + `uv.lock` (Python); `npm ci` + `package-lock.json` (frontend)            |

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
  docs/archive/         历史规划/协调文档（只读）
  specs/                Machine-readable contracts and domain specs
  PROJECT_IMPLEMENTATION_ROADMAP.md   活规划 SSOT（模块闭环队列 v2）
  MODULE_COMPLETION_RATING.md         模块完成度评级（Pass E）
  MIGRATION_MAP.md      Docs/specs navigation map (authoritative design index)
  MANIFEST.json         Repaired implementation docs package manifest (2026-06-19)
  FINAL_AUDIT_REPORT.md Repaired package audit closure record
```

**活 SSOT（新开工只看）：** `PROJECT_IMPLEMENTATION_ROADMAP.md` §3 · `MODULE_COMPLETION_RATING.md` · `docs/implementation_tasks/README.md`。

历史规划/协调文档见 `docs/archive/` 与 `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/`（含 `ROUND3_BATCH_IMPLEMENTATION_MAP.md`、`R3H_PASS_EXECUTION_PLAN.archived-20260702.md`、旧版路线图备份）。旧 `ROUND_`\* / Wave / DCP 任务卡为**只读证据**，不得再作顺序执行入口。

`docs/` 与 `specs/` 以 `MANIFEST.json` 中登记的修复包为权威口径。项目实施阶段产生的 Trellis/Batch 补充材料（如 `docs/implementation_tasks/**/plans/`、`DECISIONS.md`）不得覆盖上述权威文件。

## 项目地图与不可回退保护

`MIGRATION_MAP.md` 是当前项目级地图，用于精准索引每个模块对应的设计文档、契约、定义、规则、执行任务与实现目录入口。

必须保持以下边界：`docs/` 与 `specs/` 是设计文档、契约、定义、规则、计划、验收与治理资料目录，不是运行时代码目录，也不是功能实现地址。

未来重建 `MIGRATION_MAP.md` 或文档索引时，不得删除下列保护性条款；以下两节从旧 `MIGRATION_MAP.md` 逐字迁移到本 README 作为更稳定的保护入口。

## 上下文三层追溯模型

本仓库的实施上下文必须按三层传递，避免 Plan、Execute、Audit 角色各自读取不同来源后产生偏差：

```text
第一层：设计文档 / 契约 / 规则 / 定义 / registry / schema / ADR
        ↓
第二层：
        ↓  Plan 阶段转写为冻结的任务计划
第三层：
        ↓  Execute / Audit / Repair 按冻结计划执行、审计、修复
实现代码 / 测试 / registry 更新 / 证据产物
```

### 三层各自职责

| 层级                        | 权威内容                                                                        | 典型路径                                                                                                                                          | 主要责任               | 不得做的事                                          |
| --------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | --------------------------------------------------- |
| 第一层：设计/契约/规则/定义 | 项目真实意图、业务语义、schema、接口契约、source 角色、资源边界、用户已拍板决策 | `docs/modules/**`、`docs/ops/**`、`docs/architecture/**`、`docs/adr/**`、`docs/decisions/**`、`specs/**`、`docs/*REGISTRY.md`、`MIGRATION_MAP.md` | 提供实现依据和审计依据 | 不得当作运行时代码落点；不得被 Trellis 临时计划覆盖 |
|                             |                                                                                 |                                                                                                                                                   |                        |                                                     |
|                             |                                                                                 |                                                                                                                                                   |                        |                                                     |

### 每个 round 完成后的偏差定位方法

每完成一个 round，审计角色应按下面顺序排查偏差来源：

1. **第一层缺失**：设计文档、契约、规则、定义、schema、registry 本身是否缺内容、冲突或过时。
2. **第二层缺失**：原始执行任务是否漏列必要输入、输出、验收命令或边界约束。
3. **Plan 归并缺失**：Trellis `MASTER.plan.md` 是否没有把第一层/第二层关键上下文写入 Source Context Index。
4. **Manifest 缺失**：`implement.jsonl` / `audit.jsonl` 是否没有列出无法无损总结、必须读原文的文件。
5. **Execute 偏差**：执行代码是否偏离 MASTER、契约或已拍板决策。
6. **Audit 偏差**：审计是否只看测试通过而没有核对 source trace、registry 更新和业务语义。

偏差修复时，必须先标明偏差属于哪一层，再决定是修设计/契约、修原始任务、修 Trellis 计划、修 manifest，还是修代码/测试。

## 3. 旧口径禁止恢复

- 不得恢复 `Primary / Shadow / Emergency` 作为数据源角色模型。
- 当前权威模型为 `Primary / Validation / FallbackPolicy`。
- 旧数据源角色 `Shadow` / `Emergency` 不能作为 source role、default role、fallback role、API role、DB role 或前端 source-role 展示恢复。
- Layer 1 `SHADOW` 诊断标签是窄例外：允许出现在明确带诊断/旁证语义的 Layer 1 indicator 条目、`shadow_diagnostics` 分组、`schema_note` 或说明文档中；不得进入 `source_registry` 角色字段，不得接管 clean 主值。若不在 `shadow_diagnostics` 分组下，必须显式写明 `diagnostic_only` / `evidence_only` / `does_not_replace_main_indicator` 或同等约束。

## 4. MANIFEST 角色说明

- `MANIFEST.json` 是最终发布输出，不是 `036_create_final_release_manifest.md` 的必需输入。
- 如果仓库里已有旧 `MANIFEST.json`，执行角色只能把它作为对比参考，不能把它视为权威输入。

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
```

1. Install frontend:

```bash
cd frontend && npm ci && npm run typecheck && npm run build
```

**pip 备用路径**（仅当本机未安装 `uv` 时）：`pip install -e ".[dev]"`，须同步说明原因，不得替代 `uv.lock` 主路径。见 `specs/contracts/runtime_versions.md`。

`pytest -q` 在干净 checkout 上可不预先创建 `data/duckdb/`；`init_db.py` 仍用于 prod-path CLI 与 Tier B 验收。

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
