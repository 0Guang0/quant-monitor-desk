# MASTER 计划 — Round 3 Batch 1 Early Ops

> **Execute 入口**  
> Execute：本文件 + `implement.jsonl`。Audit 见 `AUDIT.plan.md`（Execute 不读）。  
> **Gate：** 本任务 PASS 后才能启动 Round 3 Batch 2（`017` + `018`）。

---

## 0. 元信息

| 字段                      | 值                                                                                              |
| ------------------------- | ----------------------------------------------------------------------------------------------- |
| 任务 slug                 | `06-20-round3-batch1-early-ops`                                                                 |
| 原计划来源                | `ROUND3_EARLY_CLOSE_PLAN.md` + `ROUND3_BATCH_IMPLEMENTATION_MAP.md` Batch 1（无 `NNN_` 任务卡） |
| 前置 gate                 | Round 2.6 Contract + Routing Service Gate archived PASS                                         |
| Audit 计划                | `.trellis/tasks/06-20-round3-batch1-early-ops/AUDIT.plan.md`                                    |
| 分析豁免                  | `analysis_waiver: false`                                                                        |
| manifest_protocol_version | `3`                                                                                             |

### 0.1 原计划任务

| 字段     | 值                                                                                                                                          |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Round    | Round 3 Batch 1                                                                                                                             |
| 原始任务 | `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`；`docs/ROUND3_HANDOFF.md`；`ROUND_3_MODELING_LAYERS/README.md`（边界）               |
| Item IDs | `DOC-R3-001`, `DOC-R3-002`, `R2.6-IMPL-8`, `DB-R3-001`, `DB-R3-002`, `R3-PARTIAL-2`, `R3-EARLY-DB-INSPECT-CLI`, `R3-EARLY-PROD-SCALE-BENCH` |
| 排除     | `017`–`023`                                                                                                                                 |

### 0.2 门控速查

- 只实现 `db_inspect_cli.md` **Phase A**；禁止 future phases（source probe、data health、ops report）。
- DuckDB **只读**；禁止 migration、WriteManager、网络、QMT/xqshare 默认启用（**D-11 已拍板**）。
- 禁止复用 `.tmp/inspect_db.py`。
- 实现目录：`backend/app/ops/`、`scripts/`、`tests/` — **不得**在 `docs/`/`specs/` 写运行时代码（**README §2**）。
- 依赖与验收命令以 `specs/contracts/runtime_versions.md` 为权威；Python 用 `uv sync --locked` / `uv run`（**D-01**）。
- 每步 RED/GREEN 证据必填。

### 0.7 GLOBAL 与已拍板决策摘要（inline）

**GLOBAL_EXECUTION_RULES（摘录）：** 无 drive-by refactor；不恢复 Primary/Shadow/Emergency 旧命名；Agent 禁止自由 SQL/联网/直写 clean；不绕过 `DuckDBWriteManager`；默认不做大范围扫描。

**GLOBAL_TESTING_POLICY（摘录）：** RED 先于 GREEN；断言须含业务语义（status、counts、registry 字段），禁止仅 `assert fn()` 无内容检查。

**GLOBAL_RESOURCE_LIMITS（摘录）：** inspect 默认 `--profile eco`；`scan_limited=true`；禁止无界 raw/parquet 全量扫描。

**PENDING_USER_DECISIONS（本批相关）：**

- **D-01**：`uv.lock` 为 Python 锁文件权威；不得擅自改用 Poetry。
- **D-11**：QMT 第一版默认禁用；`R2.6-IMPL-8` 仅 user-authorized staging；inspect CLI 不得提供 `--enable-qmt`。

**前置 gate（AC-PRE）：** `.trellis/tasks/archive/2026-06/06-19-round2-6-routing-service-gate/audit.report.md` 为 Round 2.6 Routing Service Gate archived PASS 证据。

### 0.8 项目边界（README 摘要）

- `docs/`、`specs/` 为设计/契约/规则目录，**不是**运行时代码实现地址。
- `MANIFEST.json` 修复包为 docs 权威口径；Trellis 补充材料不得覆盖 MANIFEST 权威文件。
- Execute 只读 MASTER + `implement.jsonl`；不默认读取全部 `docs/implementation_tasks/**` 原始任务卡。

### 0.3 Execute 强制必读清单（零遗漏）

**规则：** Execute Phase 0 Boot **必须 Read `implement.jsonl` 中每一条**。读完后在 `execute-evidence/8.0-boot-reads.txt` 记录「路径 + 一行要点」。

**v3 读法：** 先读 `research/integration-ledger.md`（§0.4）。禁止用 §8.0 路径枚举替代 implement 清单。

**6.pre：** GitNexus 刷新 → `research/gitnexus-execute-summary.md`。

### 0.4 上下文打包（协议 v3）

Execute 以 MASTER inline 为准；ledger 规定 pointer 原稿的 extract/for。

### 0.5 Execute 开场白（可复制）

```text
进入 Execute。MUST Read .cursor/skills/trellis-execute/SKILL.md。
Phase 0 Boot（§0.3 implement.jsonl 全读 + integration-ledger）→ §8.x → §9/§10 → §11 Audit。勿 finish-work。
```

### 0.6 Source Context Index

| 路径                                                          | 分类                        | Execute manifest                 |
| ------------------------------------------------------------- | --------------------------- | -------------------------------- |
| `README.md`                                                   | rule                        | **是** — 项目边界与 Execute 读法 |
| `docs/quality/PENDING_USER_DECISIONS.md`                      | decision                    | **是** — D-01/D-11 等已拍板      |
| `specs/contracts/runtime_versions.md`                         | rule                        | **是** — uv/验收命令权威         |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3 Batch 1               | 可总结                      | 否                               |
| `MIGRATION_MAP.md` §6 inspect CLI                             | 可总结                      | 否                               |
| `research/three-layer-trace.md`                               | Plan trace                  | 否                               |
| `docs/ROUND3_HANDOFF.md`                                      | business                    | **是** — DOC-R3-001 编辑目标     |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                          | decision                    | **是** — 八项 OPEN 状态来源      |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                            | decision                    | **是** — 闭合项移入              |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/README.md` | rule                        | **是** — 017–023 边界            |
| `specs/schema/schema.sql`                                     | contract                    | **是** — key_tables 表名权威     |
| `docs/modules/data_sources.md`                                | architecture                | **是** — evidence.latest_fetch   |
| `GLOBAL_EXECUTION_RULES.md` 等 GLOBAL\_\*                     | 可总结                      | **是** — §0.7 对照原稿           |
| `docs/ops/db_inspect_cli.md` §5–§11 Phase A                   | **不可无损总结**            | **是**                           |
| `specs/contracts/ops_db_inspect_contract.yaml`                | **不可无损总结**            | **是**                           |
| `backend/app/db/connection.py` (`reader()`)                   | **不可无损总结**            | **是**                           |
| `docs/modules/write_manager.md`                               | 可总结（inspect 禁 writer） | 否                               |
| `tests/test_vendor_fetch_e2e.py`                              | inherited                   | 条件（§8.4）                     |
| `tests/test_sync_jobs.py`                                     | inherited                   | 条件（§8.4）                     |
| `scripts/production_equivalent_smoke.py`                      | **不可无损总结**            | **是**（§8.5）                   |
| `017`–`023` 任务卡                                            | **已过滤**                  | 否 — Batch 2+                    |

---

## 1. 目标

### 1.1 一句话目标

在 Round 3 建模前，交付冻结的只读 DB inspect CLI（Phase A），并以 inspect 输出 + 文档/registry 更新闭合 Batch 1 八项 early 证据缺口。

### 1.2 非目标

- Layer 1–5 建模（`017`–`023`）。
- Live QMT/Yahoo/xqshare validation（`R2.6-IMPL-8` 保持 defer + 文档）。
- Migration 008、`source_health_snapshot`、free SQL、网络 probe。
- `backend/app/cli/main.py` 正式 packaging（v1 仅用 transitional `scripts/qmd_ops.py`）。

### 1.3 子交付物表（Item ID → AC）

| Item ID                     | MASTER AC   | 类型                |
| --------------------------- | ----------- | ------------------- |
| `R3-EARLY-DB-INSPECT-CLI`   | AC-CLI-1..5 | 实现                |
| `DB-R3-001`                 | AC-DB-1     | 证据                |
| `DB-R3-002`                 | AC-DB-2     | 证据                |
| `DOC-R3-001`                | AC-DOC-1    | docs                |
| `DOC-R3-002`                | AC-DOC-2    | docs                |
| `R3-PARTIAL-2`              | AC-E2E-1    | registry + 测试引用 |
| `R3-EARLY-PROD-SCALE-BENCH` | AC-BENCH-1  | 证据                |
| `R2.6-IMPL-8`               | AC-OPS-1    | defer 维持 + 文档   |

---

## 2. 预期结果（A5 trace-ac 追溯用）

| ID         | 预期结果                                                                                                                                                                                                      | 验证链                                 |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | ----------------------- |
| AC-PRE     | Round 2.6 Contract + Routing Service Gate archived PASS（见 `06-19-round2-6-routing-service-gate/audit.report.md`）；`uv sync --locked` + `pytest -q` 基线 green。                                            | §8.0; archived audit                   |
| AC-CLI-1   | `backend/app/ops/db_inspector.py` 实现 inspect 核心；输出含 contract 必填 top-level 字段。                                                                                                                    | §8.1; `tests/test_ops_db_inspector.py` |
| AC-CLI-2   | `scripts/qmd_ops.py db-inspect` transitional CLI 调用同一实现；支持 `--format text                                                                                                                            | json`。                                | §8.2; CLI smoke + tests |
| AC-CLI-3   | 只读不变量：无 migration/writer/sync fetch；测试 DB 字节级不变。                                                                                                                                              | §8.1; mutation tests                   |
| AC-CLI-4   | `key_tables` 含 contract 列表；`data_root` raw/parquet counts；`deferred_item_mapping` 非空；top-level `schema` + `evidence` 块齐全。                                                                         | §8.1; JSON shape tests                 |
| AC-CLI-5   | 缺 DB → `FAIL`；schema-only → `WARN`；语义 status 非仅“不抛错”。                                                                                                                                              | §8.1; edge case tests                  |
| AC-DB-1    | 对项目 `data/` 运行 inspect，记录 raw/parquet=0 或存在性；registry `DB-R3-001` → RESOLVED（documented absence 可接受）。                                                                                      | §8.3; inspect JSON + registry          |
| AC-DB-2    | inspect 证明 `read_only_open=true` + key table row counts；`DB-R3-002` → RESOLVED。                                                                                                                           | §8.3; inspect JSON + registry          |
| AC-DOC-1   | `ROUND3_HANDOFF.md` 顶部写明 R2.6 Contract + Routing Service Gate archived PASS。                                                                                                                             | §8.3; doc diff                         |
| AC-DOC-2   | `ROUND3_EARLY_CLOSE_PLAN.md` 声明 `AUDIT_DEFERRED_REGISTRY.md` wins on conflict。                                                                                                                             | §8.3; doc diff                         |
| AC-E2E-1   | `R3-PARTIAL-2` → RESOLVED：`test_vendor_fetch_e2e.py` service-path + `test_sync_jobs.py` full_load skeleton 为 closure evidence。                                                                             | §8.4; pytest + registry                |
| AC-BENCH-1 | `production_equivalent_smoke.py --use-service-path` 输出归档至 `execute-evidence/8.5-smoke-output.json`；`R3-EARLY-PROD-SCALE-BENCH` → RESOLVED（`R2.6-IMPL-7` 仅 Audit 交叉引用，不可替代本批 smoke 证据）。 | §8.5; smoke output + registry          |
| AC-OPS-1   | `R2.6-IMPL-8` 保持 DEFERRED；inspect/CLI 无 `--enable-qmt`；handoff 文档化 user-authorized staging 路径。                                                                                                     | §8.3; rg + registry                    |
| AC-GATE    | 全量 backend 门禁 green；blocks Batch 2 解除。                                                                                                                                                                | §9–§10                                 |

---

## 3. 范围与边界

### 3.1 允许修改/创建

- `backend/app/ops/__init__.py`
- `backend/app/ops/db_inspector.py`
- `backend/app/ops/models.py`（可选，或与 inspector 同文件）
- `scripts/qmd_ops.py`
- `tests/test_ops_db_inspector.py`
- `docs/ROUND3_HANDOFF.md`
- `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`（如闭合项移入）
- `research/execute-evidence/**`（Execute 产出）

### 3.2 Out of scope · 显式 defer

| 项                                                | 偿还批次                | 说明                         |
| ------------------------------------------------- | ----------------------- | ---------------------------- |
| Layer 1–5 建模 `017`–`023`                        | Batch 2–5               | 本批禁止实现                 |
| Migration 008 / `source_health_snapshot`          | Batch 6                 | —                            |
| Live QMT/Yahoo/xqshare soak                       | user-authorized staging | `R2.6-IMPL-8` 保持 DEFERRED  |
| `qmd data health` / `source probe` / `ops report` | future phases           | `db_inspect_cli.md` §12      |
| `backend/app/cli/main.py` packaging               | Round 5                 | v1 transitional CLI only     |
| `run_full_load` 完整 runner                       | Round 3+                | 本批仅 skeleton/E2E 引用闭合 |

### 3.3 禁止修改

- `backend/app/db/migrations/**`
- `frontend/**`
- Layer 1–5 模块（`backend/app/layer*`）
- `.tmp/inspect_db.py` 或任何临时脚本复用

### 3.4 只读 DB / 无网络边界（MASTER 强制）

- inspect 仅 `ConnectionManager.reader()` 或 `duckdb.connect(read_only=True)`。
- 禁止调用：`apply_migrations`、`ConnectionManager.writer()`、`DuckDBWriteManager`、sync fetch、adapter factory。
- v1 禁止 CLI flags：`--sql`, `--write`, `--migrate`, `--allow-network`, `--enable-qmt`, `--enable-xqshare`, `--show-secrets`, `--full-scan`。

---

## 4. 代码地图

| 路径                                                   | 操作                                 |
| ------------------------------------------------------ | ------------------------------------ |
| `backend/app/ops/db_inspector.py`                      | **创建** — `DbInspector.inspect()`   |
| `backend/app/ops/models.py`                            | **创建**（可选）— report dataclasses |
| `scripts/qmd_ops.py`                                   | **创建** — `db-inspect` subcommand   |
| `tests/test_ops_db_inspector.py`                       | **创建** — 语义 + no-mutation        |
| `docs/ROUND3_HANDOFF.md`                               | 更新 DOC-R3-001                      |
| `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md` | 更新 DOC-R3-002                      |
| registries                                             | 更新 Batch 1 item 状态               |

---

## 5. 实现切片（§8 顺序）

1. **8.1** DbInspector 核心 + RED tests（mutation、JSON shape、status rules）
2. **8.2** `qmd_ops.py` CLI wrapper + CLI smoke
3. **8.3** Docs + registry 对齐（DOC/DB/OPS items）
4. **8.4** R3-PARTIAL-2 registry 闭合（引用既有 E2E + full_load skeleton）
5. **8.5** Production-equivalent smoke 证据归档
6. **8.6** 全量 Tier A/B 门禁

---

## 6. 接口/契约

- CLI：`python scripts/qmd_ops.py db-inspect [--db] [--data-root] [--format text|json] [--limit N] [--include-path-check] [--profile eco]`
- Python：`DbInspector(db_path, data_root, *, limit=20, include_path_check=True, profile="eco").inspect() -> InspectReport`
- Output：匹配 `ops_db_inspect_contract.yaml` `required_output_fields` + `key_tables` 列表
- Status：`PASS` | `WARN` | `FAIL` per `db_inspect_cli.md` §9.2

---

## 7. Red Flags

| Red Flag                             | 预防                             |
| ------------------------------------ | -------------------------------- |
| 调用 writer/migration                | AC-CLI-3 mutation test 必须 FAIL |
| 实现 source probe / data health      | 超出 Phase A；停止               |
| 在 inspect 中启用 QMT                | 禁止 flag；AC-OPS-1              |
| 全表扫描 raw/parquet 无 limit        | `scan_limited=true`；eco profile |
| 把 docs 当实现路径                   | GLOBAL_EXECUTION_RULES           |
| 合并 017 axis loader                 | BATCH_MAP 禁止                   |
| R3-PARTIAL-2 要求 live vendor 无授权 | 用 fixture E2E + skeleton 闭合   |

---

## 8. 实现步骤（RED/GREEN）

### 8.0 Boot gate

| 字段       | 内容                                                                                                                                                                                         |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 按 **§0.3** 读 `implement.jsonl` 全表 + `research/integration-ledger.md`；6.pre GitNexus；基线 pytest。                                                                                      |
| RED 命令   | `uv run python -c "import sys; from pathlib import Path; p=Path('.trellis/tasks/06-20-round3-batch1-early-ops/research/execute-boot.md'); sys.exit(0 if p.is_file() else 1)"`（repo 根执行） |
| GREEN 命令 | 创建 `research/execute-boot.md` + `uv sync --locked` + `uv run pytest -q --co -q`                                                                                                            |
| RED 证据   | `execute-evidence/8.0-red.txt`                                                                                                                                                               |
| GREEN 证据 | `execute-evidence/8.0-boot-reads.txt`, `execute-evidence/8.0-baseline.txt`                                                                                                                   |
| Skill      | trellis-execute Phase 0                                                                                                                                                                      |
| 已执行     | [x]                                                                                                                                                                                          |

### 8.1 DbInspector core

| 字段       | 内容                                                                                                                                                                                                                                |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 实现 `db_inspector.py`：read-only open、schema、key_tables counts、data_root scan、evidence block、`deferred_item_mapping`。表名插值须经 identifier 校验（`db_inspect_cli.md` §8.3）。                                              |
| RED 命令   | `uv run pytest tests/test_ops_db_inspector.py::test_dbInspect_missingDb_returnsFail tests/test_ops_db_inspector.py::test_dbInspect_deferredItemMapping_nonEmpty tests/test_ops_db_inspector.py::test_dbInspect_dbFile_unchanged -q` |
| GREEN 命令 | `uv run pytest tests/test_ops_db_inspector.py -q`                                                                                                                                                                                   |
| RED 证据   | `execute-evidence/8.1-red.txt`                                                                                                                                                                                                      |
| GREEN 证据 | `execute-evidence/8.1-green.txt`                                                                                                                                                                                                    |
| 通过条件   | AC-CLI-1,3,4,5；JSON 含 `schema`/`evidence`；**仅**断言 `data/duckdb/quant_monitor.duckdb` 字节不变（`ConnectionManager.reader()` 可创建 `data/cache/duckdb_tmp`，不视为 DB mutation）。                                            |
| Skill      | test-driven-development, incremental-implementation, karpathy-guidelines, testing-guidelines, GitNexus impact                                                                                                                       |
| 已执行     | [x]                                                                                                                                                                                                                                 |

### 8.2 Transitional CLI

| 字段       | 内容                                                                                    |
| ---------- | --------------------------------------------------------------------------------------- |
| 做什么     | `scripts/qmd_ops.py db-inspect` 薄包装；无重复逻辑。                                    |
| RED 命令   | `uv run pytest tests/test_ops_db_inspector.py::test_qmdOps_cli_invokesSameInspector -q` |
| GREEN 命令 | `uv run python scripts/qmd_ops.py db-inspect --format json`                             |
| RED 证据   | `execute-evidence/8.2-red.txt`                                                          |
| GREEN 证据 | `execute-evidence/8.2-green.txt`                                                        |
| 通过条件   | AC-CLI-2；与 8.1 同一 backend 模块。                                                    |
| Skill      | test-driven-development, api-and-interface-design                                       |
| 已执行     | [x]                                                                                     |

### 8.3 Docs + DB registry evidence

| 字段       | 内容                                                                                                                                                                                                                                                                                                              |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| 做什么     | 更新 handoff/early-close plan；对项目 `data/` 运行 inspect；更新三份 registry。                                                                                                                                                                                                                                   |
| RED 命令   | `uv run python -c "import pathlib,re,sys; t=pathlib.Path('docs/UNRESOLVED_ISSUES_REGISTRY.md').read_text(encoding='utf-8'); sys.exit(1 if re.search(r'DB-R3-001.\*RESOLVED                                                                                                                                        | DOC-R3-001.\*PASS', t) else 0)"`（闭合前须 fail） |
| GREEN 命令 | `uv run python scripts/qmd_ops.py db-inspect --db data/duckdb/quant_monitor.duckdb --data-root data --format json > .trellis/tasks/06-20-round3-batch1-early-ops/execute-evidence/8.3-inspect.json` + 更新 registries + `uv run python scripts/check_doc_links.py` + `rg "Round2.6.*PASS" docs/ROUND3_HANDOFF.md` |
| RED 证据   | `execute-evidence/8.3-red.txt`                                                                                                                                                                                                                                                                                    |
| GREEN 证据 | `execute-evidence/8.3-green.txt`, `execute-evidence/8.3-inspect.json`                                                                                                                                                                                                                                             |
| 通过条件   | AC-DB-1,2,DOC-1,2,OPS-1；registry 行状态与 inspect JSON 一致。                                                                                                                                                                                                                                                    |
| Skill      | incremental-implementation                                                                                                                                                                                                                                                                                        |
| 已执行     | [x]                                                                                                                                                                                                                                                                                                               |

### 8.4 R3-PARTIAL-2 closure

| 字段       | 内容                                                                                                                                                                                                                                                    |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 复跑 fixture service-path E2E + `test_sync_jobs` full_load skeleton；更新 registry `R3-PARTIAL-2` → RESOLVED。                                                                                                                                          |
| RED 命令   | `uv run python -c "import sys; t=open('docs/UNRESOLVED_ISSUES_REGISTRY.md',encoding='utf-8').read(); sys.exit(0 if 'R3-PARTIAL-2' in t and 'RESOLVED' not in t.split('R3-PARTIAL-2')[1][:200] else 1)"`                                                 |
| GREEN 命令 | `uv run pytest tests/test_vendor_fetch_e2e.py::test_vendorFixtureFetch_e2eThroughDataSourceServicePath tests/test_sync_jobs.py -q -k full_load` + `rg R3-PARTIAL-2 docs/UNRESOLVED_ISSUES_REGISTRY.md docs/AUDIT_DEFERRED_REGISTRY.md`（须见 RESOLVED） |
| RED 证据   | `execute-evidence/8.4-red.txt`                                                                                                                                                                                                                          |
| GREEN 证据 | `execute-evidence/8.4-green.txt`                                                                                                                                                                                                                        |
| 通过条件   | AC-E2E-1；registry 已更新（非仅 pytest 绿）。                                                                                                                                                                                                           |
| Skill      | testing-guidelines                                                                                                                                                                                                                                      |
| 已执行     | [x]                                                                                                                                                                                                                                                     |

### 8.5 Prod-equivalent bench evidence

| 字段       | 内容                                                                                                                                                                                                                              |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 运行 smoke；归档 JSON；更新 `R3-EARLY-PROD-SCALE-BENCH` → RESOLVED。                                                                                                                                                              |
| RED 命令   | `uv run python -c "import sys; t=open('docs/UNRESOLVED_ISSUES_REGISTRY.md',encoding='utf-8').read(); sys.exit(0 if 'R3-EARLY-PROD-SCALE-BENCH' in t and 'RESOLVED' not in t.split('R3-EARLY-PROD-SCALE-BENCH')[1][:200] else 1)"` |
| GREEN 命令 | `uv run python scripts/production_equivalent_smoke.py --use-service-path` + 复制输出至 `execute-evidence/8.5-smoke-output.json` + registry 更新                                                                                   |
| RED 证据   | `execute-evidence/8.5-red.txt`                                                                                                                                                                                                    |
| GREEN 证据 | `execute-evidence/8.5-smoke-green.txt`, `execute-evidence/8.5-smoke-output.json`                                                                                                                                                  |
| 通过条件   | AC-BENCH-1；smoke 文件非空且 registry RESOLVED。                                                                                                                                                                                  |
| Skill      | incremental-implementation                                                                                                                                                                                                        |
| 已执行     | [x]                                                                                                                                                                                                                               |

### 8.6 Final gates

| 字段       | 内容                                                                      |
| ---------- | ------------------------------------------------------------------------- |
| 做什么     | 全量 §9 §10。                                                             |
| RED 命令   | `uv run python scripts/production_gate.py`（预期 Execute 收尾前仍可能红） |
| GREEN 命令 | 见 §10 Tier A/B（含 `uv sync --locked`）                                  |
| RED 证据   | `execute-evidence/8.6-red.txt`                                            |
| GREEN 证据 | `execute-evidence/8.6-final-gates.txt`                                    |
| 通过条件   | AC-GATE。                                                                 |
| Skill      | verification-before-completion（Audit 主责）                              |
| 已执行     | [x]                                                                       |

---

## 9. 四层测试

| 层     | 范围                              | 命令                                                                                                                                                                                                                          |
| ------ | --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A 单元 | `test_ops_db_inspector.py`        | `uv run pytest tests/test_ops_db_inspector.py -q`                                                                                                                                                                             |
| B 集成 | vendor E2E + sync jobs 引用       | `uv run pytest tests/test_vendor_fetch_e2e.py tests/test_sync_jobs.py -q`                                                                                                                                                     |
| C 管道 | CLI + smoke + contract acceptance | `uv run python scripts/qmd_ops.py db-inspect --format json` + `uv run python scripts/production_equivalent_smoke.py --use-service-path` + `uv run pytest tests/test_documentation_index.py tests/test_project_scaffold.py -q` |
| D E2E  | 项目 data root inspect（只读）    | `uv run python scripts/qmd_ops.py db-inspect --db data/duckdb/quant_monitor.duckdb --data-root data`                                                                                                                          |

---

## 10. Tier 验收

### Tier A（每步 GREEN 后）

> 命令权威：`specs/contracts/runtime_versions.md` §4（D-01：`uv sync --locked`）。

```bash
uv sync --locked
uv run pytest tests/test_ops_db_inspector.py -q
uv run ruff check backend/app/ops scripts/qmd_ops.py tests/test_ops_db_inspector.py
```

### Tier B（§8.6 收尾）

```bash
uv sync --locked
uv run pytest -q
uv run pytest -q --cov=backend --cov-fail-under=85
uv run ruff check .
uv run ruff format --check .
uv run python scripts/production_gate.py
uv run python scripts/check_doc_links.py
uv run pytest tests/test_documentation_index.py tests/test_project_scaffold.py -q
```

### Tier C

N/A — 无 frontend 变更。

---

## 11. Audit 交接

- Execute 完成 §8–§10 后运行 `validate-execute-handoff`。
- 交接 `AUDIT.plan.md` + `audit.jsonl`；**不** `finish-work`。
- Audit 须验证：no-mutation、JSON shape、`deferred_item_mapping`、registry 更新、§7 Red Flags。

---

## 12. Execute Skill 冻结清单

| Skill                       | 本任务   | 绑定 §8    | 触发                             | @ 指令                                                                   | 已执行 |
| --------------------------- | -------- | ---------- | -------------------------------- | ------------------------------------------------------------------------ | ------ |
| trellis-execute             | 必做     | 8.0        | Phase 0 Boot                     | Read trellis-execute SKILL.md                                            | [x]    |
| test-driven-development     | 必做     | 8.1–8.2    | 每步写码前                       | RED 先于 GREEN                                                           | [x]    |
| incremental-implementation  | 必做     | 8.1–8.5    | 跨文件切片                       | 每步仅改 §4 地图内文件                                                   | [x]    |
| karpathy-guidelines         | 必做     | 8.1+       | RED 后 GREEN 前                  | 最小正确 diff                                                            | [x]    |
| testing-guidelines          | 必做     | 8.1–8.4    | 语义断言                         | 禁止 call-only tests                                                     | [x]    |
| GitNexus impact (AGENTS.md) | 必做     | 8.1 前     | 改 `connection.py` 或新建 ops 前 | `impact(ConnectionManager.reader)`；新建后 `impact(DbInspector.inspect)` | [x]    |
| api-and-interface-design    | 条件     | 8.2        | CLI 步                           | 对齐 contract args                                                       | [x]    |
| systematic-debugging        | 条件     | 当前失败步 | pytest RED                       | 仅失败步                                                                 | [ ]    |
| trellis-check               | **不用** | —          | Audit A1                         | —                                                                        | —      |
| doubt-driven-development    | **不用** | —          | Plan 5d 已完成                   | —                                                                        | —      |

---

## 13. 原计划归并表

| 原始来源                              | Item / 主题                         | MASTER 归并                                     |
| ------------------------------------- | ----------------------------------- | ----------------------------------------------- |
| `README.md`                           | docs/specs 非实现边界               | §0.8, §3.1                                      |
| `PENDING_USER_DECISIONS.md`           | D-01/D-11                           | §0.7, AC-OPS-1, §10                             |
| `runtime_versions.md`                 | uv/验收命令                         | §8.0, §10                                       |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md`  | Batch 1 八项                        | §0.1, §1.3, §2                                  |
| `UNRESOLVED_ISSUES_REGISTRY.md`       | OPEN/DEFERRED 状态                  | AC-DB/DOC/E2E 闭合前对照                        |
| `ROUND3_HANDOFF.md`                   | entry gate                          | AC-DOC-1, §8.3                                  |
| `ROUND3_EARLY_CLOSE_PLAN.md`          | inspect CLI + prod scale + live QMT | §1.1, §8.1–8.5, AC-CLI-\*, AC-BENCH-1, AC-OPS-1 |
| `016F`                                | smoke design                        | AC-BENCH-1 trace, §8.5                          |
| `ops_db_inspect_contract.yaml`        | machine contract                    | §6, AC-CLI-\*                                   |
| `schema.sql`                          | key_tables 表名                     | §6, AC-CLI-4                                    |
| `data_sources.md`                     | fetch_log / latest_fetch            | §6 evidence block                               |
| `06-19-round2-6-routing-service-gate` | 前置 PASS                           | AC-PRE                                          |
