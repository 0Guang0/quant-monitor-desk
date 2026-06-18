# Round 2 已确认决策

> 本文记录 Round 2 各批次开工前用户已拍板的架构与范围决策。实现阶段不得 silent override；若需变更，先更新本文并征得用户确认。
>
> **四批次 Execute 顺序：** A（011+012）→ B（013）→ C（015+016）→ D（014）
>
> **Trellis：** Plan/Execute 边界以本文件为准。`MASTER.plan.md` 与本文冲突时，**先改 DECISIONS 再改 MASTER**。

---

## 1. 目录约定（继承 Round 1）

**决策：统一使用 `backend/app/*`；数据源模块落在 `backend/app/datasources/`。**

| 模块 | 路径 |
|------|------|
| 数据源注册与 Adapter 契约 | `backend/app/datasources/` |
| DuckDB migration | `backend/app/db/migrations/` |
| CLI 入口 | `scripts/`（根目录） |

正式任务文件中的 `backend/sources/` 字面量 **归一化** 为 `backend/app/datasources/`（与 `docs/architecture/07_project_directory_structure.md` 一致）。

---

## 2. Round 2 四批次边界

| 批次 | 任务 | 本批交付 | 本批不做 |
|------|------|----------|----------|
| **A** | 011+012 | source_registry YAML/DB、Adapter 契约、fetch_log 写入 | 真实 adapter 实现、Orchestrator、Validator 替换 |
| B | 013 | 5 个 adapter skeleton | 真实联网抓取 |
| C | 015+016 | DataQualityValidator、SourceConflictValidator、ValidationGate 真实现 | Orchestrator 集成 |
| D | 014 | DataSyncOrchestrator + Round 2 ingestion smoke | Layer 建模 |

---

## 3. Batch A — Schema（migration 004）

**决策：Batch A 仅追加 ingestion 基础表，不建 sync/validation 全量表。**

> **序号说明：** Round 1 repair 已占用 `003_resource_guard_metrics.sql`（扩展 `resource_guard_log` 列）。Batch A ingestion 使用 **`004_ingestion_sources.sql`**。

migration `004_ingestion_sources.sql` 仅包含：

| 表名 | 用途 |
|------|------|
| `source_registry` | YAML 同步后的源元数据（列以 `specs/schema/schema.sql` 裁剪） |
| `fetch_log` | Adapter 每次 fetch 的结构化审计（列以 `docs/modules/data_sources.md` §5.6 为准） |

**不做（留给后续批次）：**

- `data_sync_job` / `job_event_log` → Batch D
- `validation_report` / `source_conflict` / `manual_review_queue` → Batch C
- `source_health_snapshot` → Batch B 或更后（本批只预留 YAML 字段，不建表）

**权威来源（Batch A 修订 · 对抗审计 P0-2）：**

- `specs/schema/schema.sql` — **`source_registry` 与 `fetch_log` 列定义**（`fetch_log` 已与 `data_sources.md` §5.6 对齐写入 schema.sql，消除双权威）
- `specs/datasource_registry/source_registry.yaml` — 源配置与域角色
- `specs/contracts/data_adapter_contract.md` — FetchRequest/FetchResult 契约（**Pydantic v2**；勿抄 `data_sources.md` §5.5 dataclass 示例）

---

## 4. Batch A — 数据源角色口径

**决策：统一使用 `Primary` / `Validation` / `FallbackPolicy`；禁止恢复 `Primary / Shadow / Emergency` 旧三源命名。**

- YAML 与运行时校验：若出现 `Shadow`、`Emergency`（作为 role 值）→ **启动/加载失败**。
- `FallbackPolicy` 是 **策略枚举**（如 `retry_same_source`），不是第三个外部 source_id。
- 每个 `(data_domain, role)` 最多绑定一个 `source_id`；Primary 源必须 `is_enabled=true` 且 `license_type` 非 `unknown`（生产路径；测试 YAML 可放宽）。

---

## 5. Batch A — Adapter 契约范围

**决策：Batch A 只交付抽象契约 + fetch_log 落库，不交付具体 vendor adapter。**

- `BaseDataAdapter` 为 ABC；测试用 `FakeAdapter` / `RecordingAdapter`（仅 tests 或 `datasources/_testing.py`）。
- Adapter **不得**写 clean 表；失败也必须返回 `FetchResult` 并写 `fetch_log`。
- **`fetch_log` / `source_registry` 写路径（对抗审计 P0-3）：** 生产与 `init_db` 路径下，`sync_to_db()` 与 `FetchLogWriter.write()` 的 `con` **必须**来自 `ConnectionManager.writer()`（与 Round 1 单写锁一致）。`fetch_log` 为审计表，不经 WriteManager，但必须在 writer 连接上 INSERT。
- **单元测试例外：** `migrated_con(tmp_path)` 可用裸 `duckdb.connect` 仅限 `tmp_path` 隔离库；Batch A **必须**含 ≥1 条 writer 锁下写 `fetch_log` 的集成测（见 MASTER §8.4）。
- registry 校验失败（disabled / domain / unsupported）在 `_fetch_impl` **之前** raise → **不写** `fetch_log`。
- **不**引入 Polars/Pandas（与 Round 1 一致，留给 ETL heavy 批次）。
- **不**真实 HTTP/SDK 联网（Batch B skeleton 仍 mock I/O）。

---

## 6. Batch A — 依赖库

**决策：Batch A 不新增运行时依赖**（沿用 Round 0/1：`pydantic`、`pyyaml`、`duckdb`）。

---

## 7. 测试与 TDD（全 Round 2 继承）

1. 先红后绿再 refactor（`/karpathy-guidelines` + `/testing-guidelines`）
2. 集成测试用 `tmp_path` DuckDB；Execute Tier B/C 用 **`QMD_DATA_ROOT=data/`**（应用读 `QMD_DATA_ROOT`，见 `backend/app/config.py`；**禁止**文档/命令中使用裸 `DATA_ROOT` 环境变量名）
3. Mock 仅用于 DB 连接注入、时钟、UUID；registry 解析与 role 判定用真实 YAML fixture
4. **`sync_to_db` UPSERT（P1-4）：** 冻结为 DuckDB **`INSERT OR REPLACE`** 按 `source_id`；禁止全表 DELETE+INSERT（避免 Batch D 读空窗）

---

## 8. Batch A 完成后 Checkpoint

在进入 Batch B（013）前必须全绿：

- [x] `pytest -q` 全绿（**182** passed @ `ab8d1eb` · cov **93%**）
- [x] `ruff check .` 通过
- [x] `python scripts/init_db.py` 在 prod-path 应用 **`004_ingestion_sources`**（并保留 **`003_resource_guard_metrics`**）且二次幂等
- [x] `source_registry.yaml` 可被加载且 DB sync 行数 ≥ 1（prod-path **5 rows** @ `data/`）
- [x] `FetchLogWriter` 对 SUCCESS 与 NETWORK_ERROR 均落库
- [x] GPT 审计 **P0-1** `SourceMismatchError` 阻断（prod-path 冒烟 + 单测）

---

## 9. Batch A 未完整实现 / 延后偿还登记（GPT 复审 @ `ab8d1eb`）

> **规则：** 下列项已在代码/contract/docstring 中 **显式标注**，不得 silent override。变更偿还批次须先更新本表。

| ID | 未完整实现 | 当前缓解 | **建议修复阶段** | 权威文档 |
|----|-----------|----------|------------------|----------|
| **GPT-P1-5-DB** | `fetch_log` / `source_registry` 缺 DB 层 CHECK / NOT NULL | Pydantic `FetchResult` + `FetchLogWriter._validate_for_persist` 应用层双保险 | **Batch D** — 对已应用的 004 表追加约束（005 仅覆盖新 validation 表，见已偿还） | 本表 · `fetch_log.py` |
| **GPT-P2-2** | YAML 删除的 source 在 DB 中残留（`sync_to_db` 仅 UPSERT，不 tombstone） | `sync_to_db` docstring 声明行为 | **Batch D** — Orchestrator 引入 `registry_generation` / `removed_from_yaml_at` 或 disabled 策略 | `source_registry.py` · Batch D 014 |
| **GPT-init_db** | `scripts/init_db.py` 只跑 migration，不调用 `SourceRegistry.sync_to_db()` | 测试 + 手工/prod 脚本覆盖 sync | **Batch D** — 与 Orchestrator 启动钩子一并接入；或 Batch B 末增加可选 `scripts/sync_registry.py` | DECISIONS §8 · Execute eval |
| **GPT-P3-6** | ResourceGuard + ingestion 交叉 smoke | Round 1 ResourceGuard 独立测试 | **Batch D** — DataSyncOrchestrator smoke（MASTER §8.6） | `adversarial-audit-remediation.md` P3-6 |
| **GPT-SEC-CI** | 无 gitleaks / `.cursor/hooks` 静态安全扫描 | 文档化信任边界 `docs/ops/agent_workflow_boundaries.md` | **Batch B 并行** — CI 硬化 sprint（非 Batch A 阻塞） | Round 1 repair backlog 同类 |
| **A2-shrink** | ~10 行 optional inline（FetchStatus 别名等） | MASTER §6 冻结符号名 | **Info** — 可选 Repair，非阻塞 | audit.report §4.3 |

### 已偿还（勿再标为延后）

| ID | 原登记 | 偿还批次 | 证据 |
|----|--------|----------|------|
| **GPT-NOT-PUBLISHED** | Batch B+ 纳入第 8 态 | **Batch B GPT repair** | `FetchStatus` / `PortErrorStatus` / `fetch_log` `not_published` · `UnpublishedPort` · `specs/contracts/data_adapter_contract.md` |
| **GPT-staging-DB** | SUCCESS 不校验 DuckDB staging 存在 | **Batch C Execute + Repair** | `DataQualityValidator` SUCCESS evidence / staging row 校验 · `test_batch_c_validation_flow` |
| **GPT-P1-5-DB-validation** | validation/conflict 四表 DB 约束 | migration 005 内联约束 | **Batch C migration 005** | `005_ingestion_validation.sql` |

---

## 10. Batch B 完成后 Checkpoint（013 + GPT repair）

在进入 Batch C（015+016）前必须全绿：

- [x] 5 个 vendor skeleton + `FetchPort` / `create_adapter` / `create_test_adapter`
- [x] GPT repair P0/P1 全关闭（`NOT_PUBLISHED_YET`、禁默认 Stub、FileRegistry 生产必填等）
- [x] `pytest tests/test_adapter_skeletons.py tests/test_data_adapter_contract.py` 全绿
- [x] PR #2 合并 + GPT repair 文档/契约同步（本 commit）
- [x] 延后项见 §9 与 `BATCH_B_REPAIR_STATUS.md` §延后台账

### Batch B 仍开放 / 延后（显式登记）

| ID | 内容 | 阶段 | 说明 |
|----|------|------|------|
| **B-D2** | `PortErrorStatus` ↔ `FetchStatus` 共享类型别名 | Batch D | 测试已防 drift；过早抽象增加耦合 |
| **B-D3** | 真实 Port 凭证/错误消息脱敏 | Batch D | skeleton 层已对齐；`write_audit_log` 与 `FetchLogWriter` 共用 `error_redaction`（Batch C Repair） |
| **B-D4** | `_resolve_as_of` ISO 严格校验 | 按需 Batch C | RawStore `_safe_segment` 已防路径穿越 |
| **B-P2-1** | adapter metadata（`adapter_id`、`requires_auth` 等） | Batch C/D | skeleton 仅 `source_id` + domains |
| **B-P2-2** | Trellis 归档瘦身规则 | 流程建议 | 每批仅保留 MASTER/AUDIT/implement 摘要 |
| **B-P1-6-full** | Orchestrator fetch 前 ResourceGuard | Batch D | skeleton `max_payload_bytes` 10MB 已做短期防呆 |

完整 GPT 审查处置表：`.trellis/tasks/archive/2026-06/06-17-round2-batch-b-adapters/research/gpt-post-merge-review.md`

### Batch C Execute Checkpoint（015+016）

Batch C Execute has delivered the validation/conflict primitives and is ready for
independent Audit, but it is not marked complete until Audit PASS.

- [x] migration `005_ingestion_validation.sql` creates `validation_report`,
  `data_quality_log`, `source_conflict`, and `manual_review_queue`.
- [x] `DbValidationGate` reads persisted `validation_report` rows and rejects
  missing/FAILED/cannot-write/manual-review reports.
- [x] `DataQualityValidator` validates staging rows, persists validation reports
  and data-quality findings, and rejects SUCCESS fetches without staging/raw
  evidence.
- [x] `SourceConflictValidator` detects tolerance warnings, severe conflicts,
  source-methodology differences, persists `source_conflict`, and routes severe
  conflicts through reconcile-first policy (`record_unresolved_reconcile` after
  failed reconcile); open severe conflicts block clean writes via `DbValidationGate`.
- [x] `DataQualityValidator` implements `layer1_rules` + `layer3_rules` from
  `data_quality_rules.yaml` (incl. `MISSING_SOURCE_USED`, `INVALID_AMOUNT`).
- [x] `write_audit_log` redacts secrets via shared `error_redaction` util.
- [x] `PortErrorStatus` / `FetchStatus` drift is covered by tests; persisted
  fetch error messages redact token/password/api_key/apikey/secret/
  authorization/bearer-shaped secrets.
- [x] End-to-end validation flow is covered:
  DataQualityValidator -> SourceConflictValidator -> DbValidationGate ->
  WriteManager.

Batch C explicitly did not implement DataSyncOrchestrator, real vendor Ports,
API/frontend production UI, Agent sandbox, release manifest, or full security CI.

### Batch A 验收命令（GPT §十二 · 2026-06-17 复跑 @ `ab8d1eb`）

```text
pytest -q --cov=backend --cov-fail-under=75  → 182 passed, 93% cov, exit 0
ruff check .                                  → All checks passed
python -m compileall -q backend scripts tests → exit 0
QMD_DATA_ROOT=data python scripts/ci_ingestion_smoke.py → ok (init_db ×2 幂等, 004, 两表)
SourceRegistry.load + sync_to_db @ data/      → 5 rows
SourceMismatchError prod smoke                → 0 fetch_log on mismatch
```
