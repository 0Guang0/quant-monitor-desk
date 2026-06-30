# Audit A7 报告 — B3V-DATA schema_hash fail-closed

| 字段       | 值                                                                                                    |
| ---------- | ----------------------------------------------------------------------------------------------------- |
| 维度       | **A7** Ops / DBA / SRE                                                                                |
| 任务       | `round3v-schema-hash-fail-closed` · Manifest `B3V-C02`                                                |
| Worktree   | `C:/Users/Guang/Desktop/quant-monitor-desk-wt-b3v-data`                                               |
| 分支       | `fix/round3v-schema-hash-fail-closed`（实现已 merge `0e3316a2`；worktree 仅余 task 文档未提交）       |
| 模式       | **只读 Audit**（不改代码、不 commit、不写 production DB）                                             |
| Agent 模板 | `agents/database-administrator.md` · `agents/sre-engineer.md` · `agents/devops-incident-responder.md` |
| 对抗权威   | `agents/audit-adversarial-authority.md`                                                               |
| 审计日期   | 2026-06-28                                                                                            |

---

## 1. AUDIT.plan §1 A7 冻结条件

| 项        | 冻结要求                | 审计结论                                                                                                               |
| --------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| migration | 无改动                  | **PASS** — 实现 commit `1bc0260d` 未触及 `backend/app/db/migrations/`、`scripts/init_db.py`、`specs/schema/schema.sql` |
| registry  | 无 registry 文件改动    | **PASS** — 未触及 `specs/datasource_registry/source_registry.yaml`、`source_capabilities.yaml`、`UNRESOLVED_*`         |
| 通过条件  | 零 schema/registry diff | **PASS** — 见 §2                                                                                                       |

**说明：** 本任务 A7 主判据为**静态边界**（零 schema/registry diff），与 MASTER「无 migration」一致。标准 A7「两遍 init_db + kill migrate」因无 migration 面 **不适用**；以 gate fail-closed 异常场景 + migration 回归 pytest 替代（§3.7）。

---

## 2. Diff 范围核对（schema / registry / 数据面）

### 2.1 实现 commit 变更清单（`git diff --name-only 1bc0260d^..1bc0260d`）

| 文件                                                | 类别                 | A7 相关                                                            |
| --------------------------------------------------- | -------------------- | ------------------------------------------------------------------ |
| `backend/app/db/validation_gate.py`                 | 应用逻辑（只读 SQL） | 读 `fetch_log` / `file_registry` / `validation_report`；无 DDL/DML |
| `backend/app/datasources/adapters/skeleton_base.py` | Adapter 推导         | 有界 CSV/Parquet schema_hash；临时 DuckDB 内存连接 + `mkstemp`     |
| `specs/contracts/data_adapter_contract.md`          | 契约                 | 非 schema/registry                                                 |
| `tests/test_db_validation_gate.py`                  | 测试                 | sandbox tmp DB                                                     |
| `tests/test_adapter_skeletons.py`                   | 测试                 | sandbox tmp_path                                                   |
| `tests/test_data_adapter_contract.py`               | 测试                 | 静态契约                                                           |
| `tests/test_catalog.yaml`                           | 测试目录             | 非 schema                                                          |

### 2.2 显式未触及路径（对抗性 diff + grep）

- `specs/schema/schema.sql`
- `backend/app/db/migrations/**`
- `scripts/init_db.py`
- `specs/datasource_registry/source_registry.yaml`
- RawStore / sync / layer5 生产写路径（MASTER §1.5 禁止）

### 2.3 运行时数据路径影响（DBA）

| 组件                                             | 写库？                        | 说明                                                                   |
| ------------------------------------------------ | ----------------------------- | ---------------------------------------------------------------------- |
| `DbValidationGate`                               | **否**                        | 仅 `SELECT`；经 `ConnectionManager.reader()`                           |
| `SkeletonAdapterBase._infer_parquet_schema_hash` | **否**                        | `duckdb.connect()` 内存实例 + `tempfile.mkstemp`；`finally` 删临时文件 |
| `SkeletonAdapterBase.fetch`                      | 经既有 RawStore/file_registry | 未改 RawStore 实现体；仍走既有 register 路径                           |

**DOUBT（DBA）：** 第二次 init 是否仅「不报错」而数据已损坏？→ 本 diff **无 migration**，schema 不变；回归依赖 `test_schema_migration.py`（10 passed，见 §3.7）。

---

## 3. §3.7 运维证据表

### 3.1 Database Administrator（幂等 / schema 一致性）

| 步骤                          | 命令                                                                                                            | exit     | 关键输出 / 证据                                                       |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------- |
| schema/registry diff 静态检查 | `git diff --name-only 1bc0260d^..1bc0260d -- backend specs/schema scripts/init_db.py specs/datasource_registry` | 0        | 仅 `validation_gate.py`、`skeleton_base.py`                           |
| migration 回归（pytest）      | `uv run pytest tests/test_schema_migration.py -q --tb=no`                                                       | **0**    | `..........` **10 passed**                                            |
| init_db 两遍幂等              | `QMD_DATA_ROOT=<sandbox> python scripts/init_db.py` ×2                                                          | **SKIP** | 只读 Audit 不写盘；由「零 migration diff」+ migration pytest 间接覆盖 |
| kill migrate 异常             | —                                                                                                               | **N/A**  | 本任务无 migration 改动；AUDIT.plan 未要求                            |

**环境注记：** Windows 下复用已存在 `--basetemp` 目录时曾出现 `FileNotFoundError`（3 ERROR）；去掉 `--basetemp` 或清理目录后 10/10 绿。属 sandbox 卫生问题，非 migration 逻辑回归。

### 3.2 SRE Engineer（fail-closed / 可靠性）

| 场景                     | 命令                                                                                                                            | exit           | 日志 / 证据                                                   |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------- | -------------- | ------------------------------------------------------------- |
| Gate 全量回归            | `uv run pytest tests/test_db_validation_gate.py -q --tb=no`                                                                     | **0**          | **16 passed**                                                 |
| Gate 缺 schema_hash 拒绝 | `tests/test_db_validation_gate.py::test_missingSchemaHashOnStructuredFetch_rejects`                                             | 含于 16 passed | `ValidationRejected` + `schema_hash_changed without approval` |
| schema_hash 漂移拒绝     | `test_schemaHashDriftWithoutApproval_rejects`                                                                                   | 含于 16 passed | 负向未削弱（B3V-AUD-05）                                      |
| A8 冻结子集（交叉）      | `uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q --tb=no` | **0**          | **106 passed**                                                |

**DOUBT（SRE）：** 异常后是否静默成功？→ `test_missingSchemaHashOnStructuredFetch_rejects` 显式 `ValidationRejected`；skeleton 对缺 hash 返回 `SCHEMA_DRIFT`（非 SUCCESS），与 Execute `9.4-green.txt` 一致。

### 3.3 DevOps Incident Responder（RCA / 事故面）

| 检查项                    | 结论                                                                                           |
| ------------------------- | ---------------------------------------------------------------------------------------------- |
| 生产 DuckDB mutation 路径 | diff 无 WriteManager / migration / clean-write 新入口                                          |
| 依赖链断裂点              | 仅 validation 读路径 + adapter 推导；无新 hop                                                  |
| Execute evidence 可 RCA   | `9.0-green.txt`（126 passed）、`9.1`–`9.4` 分步 green 含真实 pytest 输出                       |
| 缓解手段仍有效            | `manual_patch` / `schema_migration` write_mode 豁免未删；`SCHEMA_DRIFT` quality_flags 仍 block |

---

## 4. 计划外发现

| ID  | 发现                                                                                        | 严重度       | 说明                                                                                                       |
| --- | ------------------------------------------------------------------------------------------- | ------------ | ---------------------------------------------------------------------------------------------------------- |
| F1  | `validation_gate.py` 中 `_STRUCTURED_FILE_TYPES` 已定义未使用                               | NON-BLOCKING | 结构化判定走 path 后缀 + `file_registry.file_type` 查询；死常量可后续清理                                  |
| F2  | Gate 结构化 fallback 查 `file_registry` 最近 `json/csv/parquet`（`LIMIT 1`，未绑 `job_id`） | NON-BLOCKING | 可能过度判定 structured（偏向 fail-closed）；与 A4-02 交叉                                                 |
| F3  | Parquet schema 推导每次 fetch 创建临时文件 + 内存 DuckDB                                    | NON-BLOCKING | 有 `_CSV_SCHEMA_PREFIX_BYTES` 有界；temp 文件 `finally` 清理；高并发 temp I/O 与 A6 交界（本任务 A6 SKIP） |
| F4  | Gate 对无后缀 `raw_file_paths` 且 registry 无结构化历史时 fail-open                         | NON-BLOCKING | `current_hash is None` → `return False`；契约 defer B02-DATA-05 registry 闭合后收紧                        |
| F5  | Windows `--basetemp` 复用导致 pytest setup ERROR                                            | NON-BLOCKING | 审计/CI 应清理 basetemp 或使用唯一路径；不影响 A7 主判据                                                   |

**对抗搜索声明：** 已对照 `specs/schema/`、`migrations/`、`datasource_registry/`、init/backup 文档、`validation_gate` SQL、`skeleton_base` 临时 DuckDB 路径；除上表外无计划外 DB 污染或 migration 面。

---

## 5. 判定

| 维度                    | 判定             | 理由                                                                     |
| ----------------------- | ---------------- | ------------------------------------------------------------------------ |
| **AUDIT.plan A7**       | **PASS**         | 零 schema/registry/migration diff；变更限于 gate 只读逻辑与 adapter 推导 |
| DBA 幂等 adjunct        | **PASS（间接）** | migration pytest 10/10；无 schema 变更                                   |
| SRE fail-closed adjunct | **PASS**         | gate 16/16；A8 子集 106/106；Execute 分步 evidence 可复现                |
| Incident 生产写面       | **PASS**         | 无新 production clean-write / migration 路径                             |

### 移交主会话 / 其他维度

- **B02-DATA-05** registry 闭合仍 deferred（主会话）；本 A7 不判 registry 行闭合。
- **F1** 死常量可由 Execute/Repair 顺手删除（非 A7 必达）。
- **F4** 与 A4/A8 已记录；registry 闭合后建议补 gate 回退路径单测。

---

## 6. 参考命令（sandbox 复现）

```bash
# A7 静态（实现 commit）
git diff --name-only 1bc0260d^..1bc0260d -- backend specs/schema scripts/init_db.py specs/datasource_registry

# migration 回归
uv run pytest tests/test_schema_migration.py -q --tb=no

# gate fail-closed
uv run pytest tests/test_db_validation_gate.py -q --tb=no

# A8 交叉子集
uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q --tb=no

# init 幂等（需写 sandbox，非只读 Audit 时）
QMD_DATA_ROOT=<task>/.audit-sandbox/data uv run python scripts/init_db.py
QMD_DATA_ROOT=<task>/.audit-sandbox/data uv run python scripts/init_db.py
```

---

_A7 只读审计完成（2026-06-28 复审计）。未修改仓库业务代码。_
