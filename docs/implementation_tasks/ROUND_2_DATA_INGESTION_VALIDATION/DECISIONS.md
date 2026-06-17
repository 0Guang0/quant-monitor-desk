# Round 2 已确认决策

> 本文记录 Round 2 各批次开工前用户已拍板的架构与范围决策。实现阶段不得 silent override；若需变更，先更新本文并征得用户确认。
>
> **四批次 Execute 顺序：** A（011+012）→ B（013）→ C（015+016）→ D（014）

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

- [ ] `pytest -q` 全绿（Round 1 基线 **105** @ `3d7f93a` + Batch A 增量；**不硬编码**最终计数，见 MASTER §8.5）
- [ ] `ruff check .` 通过
- [ ] `python scripts/init_db.py` 在 prod-path 应用 **`004_ingestion_sources`**（并保留 **`003_resource_guard_metrics`**）且二次幂等
- [ ] `source_registry.yaml` 可被加载且 DB sync 行数 ≥ 1
- [ ] `FetchLogWriter` 对 SUCCESS 与 NETWORK_ERROR 均落库
