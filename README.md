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

历史规划/协调文档见 `docs/archive/` 与 `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/`（含 `ROUND3_BATCH_IMPLEMENTATION_MAP.md`、`R3H_PASS_EXECUTION_PLAN.archived-20260702.md`、旧版路线图备份）。旧 `ROUND_*` / Wave / DCP 任务卡为**只读证据**，不得再作顺序执行入口。

`docs/` 与 `specs/` 以 `MANIFEST.json` 中登记的修复包为权威口径。项目实施阶段产生的 Trellis/Batch 补充材料（如 `docs/implementation_tasks/**/plans/`、`DECISIONS.md`）不得覆盖上述权威文件。

## 项目地图与不可回退保护

`MIGRATION_MAP.md` 是当前项目级地图，用于精准索引每个模块对应的设计文档、契约、定义、规则、执行任务与实现目录入口。

必须保持以下边界：`docs/` 与 `specs/` 是设计文档、契约、定义、规则、计划、验收与治理资料目录，不是运行时代码目录，也不是功能实现地址。

未来重建 `MIGRATION_MAP.md` 或文档索引时，不得删除下列保护性条款；以下两节从旧 `MIGRATION_MAP.md` 逐字迁移到本 README 作为更稳定的保护入口。

## 上下文三层追溯模型

本仓库的实施上下文必须按三层传递，避免 Plan、Execute、Audit 角色各自读取不同来源后产生偏差：

```text
第一层：设计文档 / 契约 / 规则 / 定义 / registry / schema / ADR
        ↓  Plan 阶段读取、比对、过滤、去噪、归并
第二层：docs/implementation_tasks/** 原始执行任务
        ↓  Plan 阶段转写为冻结的 Trellis 复杂任务计划
第三层：.trellis/tasks/**/MASTER.plan.md + AUDIT.plan.md + REPAIR.plan.md + jsonl manifest
        ↓  Execute / Audit / Repair 按冻结计划执行、审计、修复
实现代码 / 测试 / registry 更新 / 证据产物
```

### 三层各自职责

| 层级                        | 权威内容                                                                                                | 典型路径                                                                                                                                          | 主要责任                               | 不得做的事                                                                  |
| --------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | --------------------------------------------------------------------------- |
| 第一层：设计/契约/规则/定义 | 项目真实意图、业务语义、schema、接口契约、source 角色、资源边界、用户已拍板决策                         | `docs/modules/**`、`docs/ops/**`、`docs/architecture/**`、`docs/adr/**`、`docs/decisions/**`、`specs/**`、`docs/*REGISTRY.md`、`MIGRATION_MAP.md` | 提供实现依据和审计依据                 | 不得当作运行时代码落点；不得被 Trellis 临时计划覆盖                         |
| 第二层：原始执行任务        | 每个 round / task 的范围、输入文件、输出文件、验收命令、边界约束                                        | `docs/implementation_tasks/**`                                                                                                                    | 帮 Plan 定位“要做什么、读什么、验什么” | 不得直接替代第一层契约；不得默认成为 Execute/Audit manifest                 |
| 第三层：Trellis 冻结计划    | Plan 阶段过滤后形成的可执行计划、Source Context Index、Audit Source Trace、Repair 入口和 jsonl manifest | `.trellis/tasks/**/MASTER.plan.md`、`AUDIT.plan.md`、`REPAIR.plan.md`、`implement.jsonl`、`audit.jsonl` / `check.jsonl`                           | 是 Execute / Audit / Repair 的直接入口 | 不得丢失第一层/第二层关键上下文；不得把过时原始任务原文无过滤地推给 Execute |

### 角色读取规则

| 角色    | 必须读取                                                                                                                               | 可读取                                                     | 默认不读取                                  |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------- |
| Plan    | 第一层权威来源、第二层原始任务、`MIGRATION_MAP.md`、`docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`、Trellis planning protocol | 历史 `.trellis/tasks/**` 作为 trace                        | 不能只读原始任务就直接生成执行计划          |
| Execute | 当前 Trellis `MASTER.plan.md`、`implement.jsonl` 中列出的 Execute must-read 文件                                                       | MASTER Source Context Index 标明必须读原文的设计/契约/代码 | 默认不直接读全部原始任务卡或全部 docs/specs |
| Audit   | 当前 `AUDIT.plan.md`、`audit.jsonl` / `check.jsonl`、MASTER Source Context Index、需要核验的证据文件                                   | 被 AUDIT Source Trace 标明的原文路径                       | 默认不重新发明任务范围                      |
| Repair  | `REPAIR.plan.md`、审计报告、失败证据、MASTER/AUDIT 中指定的上下文                                                                      | 必要时回溯第一层/第二层定位偏差来源                        | 默认不扩大修复范围                          |

### Plan 阶段必须产出的追溯字段

每个 Trellis `MASTER.plan.md` 必须包含 Source Context Index，至少说明：

| 字段                | 含义                                                                          |
| ------------------- | ----------------------------------------------------------------------------- |
| Source path         | 原始来源路径，例如设计文档、契约、规则、原始任务或 registry                   |
| Type                | design / contract / rule / schema / registry / original-task / code-reference |
| Used by             | 哪个 deliverable、AC、测试或审计项使用它                                      |
| Summary in plan     | 是否已被 MASTER 无损总结                                                      |
| Must read original? | Execute/Audit 是否必须读原文                                                  |
| Reason              | 为什么必须读、为什么已过滤、或为什么可只读总结                                |

每个 `AUDIT.plan.md` 必须包含 Audit Source Trace，至少能追溯：

```text
item ID / task ID → source document → acceptance criterion → code/test evidence → registry or deferred update
```

### 每个 round 完成后的偏差定位方法

每完成一个 round，审计角色应按下面顺序排查偏差来源：

1. **第一层缺失**：设计文档、契约、规则、定义、schema、registry 本身是否缺内容、冲突或过时。
2. **第二层缺失**：原始执行任务是否漏列必要输入、输出、验收命令或边界约束。
3. **Plan 归并缺失**：Trellis `MASTER.plan.md` 是否没有把第一层/第二层关键上下文写入 Source Context Index。
4. **Manifest 缺失**：`implement.jsonl` / `audit.jsonl` 是否没有列出无法无损总结、必须读原文的文件。
5. **Execute 偏差**：执行代码是否偏离 MASTER、契约或已拍板决策。
6. **Audit 偏差**：审计是否只看测试通过而没有核对 source trace、registry 更新和业务语义。

偏差修复时，必须先标明偏差属于哪一层，再决定是修设计/契约、修原始任务、修 Trellis 计划、修 manifest，还是修代码/测试。

### 当前关键索引入口

| 场景                                | 入口                                                                                                                                                                                  |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **活规划 / 下一批工单**             | `PROJECT_IMPLEMENTATION_ROADMAP.md` §3 · `docs/implementation_tasks/README.md`                                                                                                        |
| **模块完成度（Pass E）**            | `MODULE_COMPLETION_RATING.md` §3                                                                                                                                                      |
| 全项目模块定位                      | `MIGRATION_MAP.md`                                                                                                                                                                    |
| 普通文档导航                        | `docs/INDEX.md`                                                                                                                                                                       |
| Plan 上下文桥                       | `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`                                                                                                                               |
| Round3 六批次上下文索引（历史）     | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                                                  |
| R3H PASS 逐源表 / Wave 叙事（历史） | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_PASS_EXECUTION_PLAN.archived-20260702.md` |
| Round3 DB inspect CLI 冻结设计      | `docs/ops/db_inspect_cli.md`、`specs/contracts/ops_db_inspect_contract.yaml`                                                                                                          |
| Trellis 复杂任务协议                | `.trellis/spec/guides/complex-task-planning-protocol.md`                                                                                                                              |

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

**2026-07-02 起：** 不再按 `ROUND_0` → `ROUND_5` 顺序执行。旧 Wave/DCP 任务包已迁入 `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/`（只读证据）。

**新开工** 以 **模块闭环队列 v2** 为准（`PROJECT_IMPLEMENTATION_ROADMAP.md` §3）：

| 优先级 | 票 ID                                         | 业务一句话                                |
| ------ | --------------------------------------------- | ----------------------------------------- |
| **P0** | **M-DATA-03**                                 | 11 主源真网增量→写库→巡检（隔离库）       |
| **P0** | **M-G1-03**                                   | 五轴按设计完整落地（真链，非仅 seed）     |
| **P1** | **M-G2-FULL** / **M-G4-FULL** / **M-G5-FULL** | Layer2/4/5 按设计权威完整落地             |
| **P0** | **M-PASS-01**                                 | `PASS_ROUND4_REAL_DATA_READY`（末位门禁） |

Round4 产品面（B04）须在 **M-PASS-01** 通过后开工。每个新票 Plan 冻结前仍须读全局契约（`GLOBAL_*.md`）及该票列出的设计/契约；前端页面布局、视觉风格、交互方式在正式实现前必须由用户确认（D-08）。

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
