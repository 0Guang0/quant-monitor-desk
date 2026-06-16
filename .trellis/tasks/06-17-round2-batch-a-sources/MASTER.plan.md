# MASTER 计划 — Round 2 Batch A（011 source_registry + 012 adapter contract）

> **Execute 入口（唯一全文）** · v1.3 · 2026-06-17  
> 已纳入 Composer 2.5 **双 agent 对抗审计**全量修订（Alpha 14 + Beta 16，去重后 **26 项** → 见 `research/adversarial-audit-remediation.md`）  
> `plans/011_012_batch_a.plan.md` 仅索引 · **§8 = TDD 全文**

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-17-round2-batch-a-sources` |
| 关联 Round | `ROUND_2_DATA_INGESTION_VALIDATION` Batch **A** |
| 决策 | `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md` |

### 0.1 门控

| 项 | 值 |
|----|-----|
| **Round 0/1 修复** | **已通过**（`d218162..3d7f93a` · pytest **105**/105 · coverage ≥75% · npm audit 0 high · doc links OK · schema contract 6 表） |
| **6.pre** | GitNexus + CodeGraph 刷新 → `research/gitnexus-execute-summary.md`（**不覆盖** Plan 阶段 `gitnexus-summary.md`） |
| **Plan 对抗审计** | Alpha + Beta → `research/adversarial-audit-agent-*.md`；**remediation 全表** → `research/adversarial-audit-remediation.md` |
| **Plan BLOCK** | **已解除**（v1.3 文档/plan/CI/schema 修订完成；**代码实现**仍待 Execute §8） |
| **Execute prod-path** | 默认 `<repo>/data`（环境变量 **`QMD_DATA_ROOT`**，未设时等同 `data/`） |
| **Audit sandbox** | **`QMD_DATA_ROOT=.audit-sandbox/data`**（禁止用裸 `DATA_ROOT` env） |
| **默认分支** | `master`（`detect_changes` / CI 对照；仓库无 `main`） |
| **Execute 后再索引** | §8.4 实现 ingestion 模块后 **`node .gitnexus/run.cjs analyze`** + **`npx @colbymchenry/codegraph sync`**（P3-2） |
| **验收** | §8 证据 + §10 勾 → Audit |

**Execute 开场白：**

```text
Round 2 Batch A Execute：6.pre → 只读 MASTER + implement.jsonl + DECISIONS → 严格 §8.0→8.5 顺序 → §10 → §11 交接 Audit。
```

---

## 1. 目标

1. migration **003**：`source_registry` + `fetch_log`
2. YAML → `SourceRegistry`；Primary/Validation/FallbackPolicy；拒绝 Shadow/Emergency
3. `FetchRequest`/`FetchResult`（Pydantic v2，见 §6.3 权威说明）
4. `FetchLogWriter`：成功/失败/异常均落库
5. `BaseDataAdapter` 模板：registry + adapter 域校验 → fetch → **always** log；不写 clean

**本批不做：** vendor adapter（B）、Orchestrator（D）、ValidationGate 替换（C）、真实联网。

---

## 2. 预期结果（A5 trace-ac）

| # | 预期结果 | 验证链 |
|---|----------|--------|
| AC-1 | 003 创建两表 + migration + **schema contract** 回归 | §8.1 Step 4–6 + `test_schema_contract` 003 扩展 |
| AC-2 | domain_roles Primary=baostock @ market_bar_1d | §8.2 + 默认 seed 测试 |
| AC-3 | Shadow **与** Emergency → `LegacyRoleError` | §8.2 bad_shadow / bad_emergency |
| AC-4 | disabled 源 + 非法 domain 阻断 | §8.2 assert_enabled + assert_domain_allowed |
| AC-5 | 7 种 status + FetchRequest 必填 | §8.3 parametrized |
| AC-6 | 失败/异常仍写 fetch_log + error_type | §8.4 Writer + adapter 异常测试 |
| AC-7 | 每次 fetch **恰好** 1 条 log | §8.4 SUCCESS/EMPTY/两次调用 |
| AC-8 | init_db 幂等 + prod 库含两表 | §8.5 + §10 B |

---

## 3. 边界与范围

### 3.1 In scope

- `backend/app/datasources/*`、`004_ingestion_sources.sql`
- `tests/conftest.py`（**扩展** Batch A helpers，不删 Round 0/1 fixture）
- `tests/fixtures/source_registry_*.yaml`
- `tests/test_source_registry.py`、`tests/test_data_adapter_contract.py`
- **修改** `tests/test_schema_migration.py`（003 回归 · §8.1 Step 4 **强制**）
- **修改** `tests/test_schema_contract.py`（003 两表列契约 · §8.1 Step 5 **强制**）

### 3.2 Out of scope · 明确豁免

| 项 | Batch A 口径 |
|----|----------------|
| Contract rule 2（raw/staging **文件**证据） | **Batch B** vendor adapter 写 raw；Batch A 仅要求 `FetchResult.staging_table`/`raw_file_paths` **字段可携带**并在 SUCCESS fixture 中非空；**不**写真实 raw 文件；**不**断言 DuckDB 内 staging 表存在（Batch C 前补校验 · §8.6） |
| Contract rule 5（silent fallback） | **禁止**换 source_id；§8.4 负向测试 |
| `job_id` | `fetch(..., job_id=None)` 默认 NULL；Batch D Orchestrator 传入 |
| ValidationGate / WriteManager | 不修改 |

### 3.3 已确认

- 路径 `backend/app/datasources/`；四批次 Batch A = 011+012

---

## 4. 技术设计摘要

```text
YAML → SourceRegistry.load() → validate_domain_roles()
    → sync_to_db(con)   # UPSERT, allowed_domain as JSON array string
BaseDataAdapter.fetch(con, req, job_id=None)
    → assert_enabled → assert_domain_allowed → assert supported_domains
    → try _fetch_impl except → FetchResult(FAILED)
    → FetchLogWriter.write (always)
```

---

## 5. 依赖与切片

```text
§8.0 stub → fixtures → conftest → collect-only
§8.1 migration 003 + test_schema_migration + test_schema_contract
§8.2 SourceRegistry
§8.3 FetchRequest/Result
§8.4 FetchLogWriter + BaseDataAdapter (+ writer-lock 集成测)
§8.5 回归 + init_db + rg 守门
```

**§8.2 前置：** §8.1 Step 7 必须完成。

---

## 6. 接口契约

**原则：** 边界校验；Adapter **禁止** `WriteManager` import；错误类型一致。

### 6.1 类型与异常 · 完整 SourceRecord（19 列对齐 schema.sql L13–33）

```python
@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    source_name: str
    source_type: str
    allowed_domains: frozenset[str]       # DB: allowed_domain VARCHAR JSON array
    trust_level: int
    license_type: str
    official_api: bool
    is_enabled: bool
    default_priority: int
    rate_limit_policy: str
    auth_required: bool
    requires_local_client: bool
    expected_frequency: str
    expected_lag: str
    timezone: str
    fallback_allowed: bool
    validation_only: bool
    notes: str
    # updated_at: set by sync_to_db to CURRENT_TIMESTAMP on write
```

异常：`LegacyRoleError` · `DomainNotAllowedError` · `SourceDisabledError` · `SourceNotFoundError` · `InvalidRegistryError`（malformed YAML / unknown domain_roles 引用 / 非法 fallback_policy / Primary 绑定 disabled 或 license_type=unknown）

### 6.2 SourceRegistry · DomainRoleBinding

```python
@dataclass(frozen=True)
class DomainRoleBinding:
    """Batch D Orchestrator 稳定 getter 契约（§8.6）。"""
    primary_source_id: str
    validation_source_id: str | None
    fallback_policy: str

def _allowed_domains_to_db(domains: frozenset[str]) -> str:
    """json.dumps(sorted(domains)) — 固定格式，Batch B 同口径解析。"""

def _record_to_db_row(rec: SourceRecord) -> dict[str, object]:
    """19 列映射；allowed_domain = _allowed_domains_to_db(...)。"""

class SourceRegistry:
    DEFAULT_YAML: Path = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"

    def load(self, path: Path | None = None) -> None:
        """解析 YAML（默认 DEFAULT_YAML）；拒绝 Shadow/Emergency；
        _validate_domain_roles()：primary 必须 enabled 且 license_type != 'unknown'。"""

    def get_domain_roles(self, data_domain: str) -> DomainRoleBinding: ...

    def sync_to_db(self, con) -> int:
        """**冻结：** DuckDB `INSERT OR REPLACE` 按 source_id UPSERT（禁止 DELETE+INSERT 全表）；
        `updated_at = CURRENT_TIMESTAMP` 每次写入刷新；
        返回 upsert 行数；第二次 sync 行数不变、updated_at 递增（§8.2 测试）。
        **con 必须**来自 `ConnectionManager.writer()`（生产/init_db）；单元测试 `migrated_con` 例外见 DECISIONS §5。"""
```

**Legacy YAML  banned 示例（非 role 名本身）：**

- `domain_roles.x.primary: Shadow` 或 `validation: Emergency`
- 顶层键 `shadow_source:` / `emergency_source:` 若作为 role 别名也拒绝

### 6.3 FetchRequest / FetchResult

> **权威：** Batch A 用 **Pydantic v2**（`specs/contracts/data_adapter_contract.md`）。**勿抄** `docs/modules/data_sources.md` §5.5 dataclass 示例。

**FetchResult.status（Batch A · 7 态，与 contract md 一致）：**

`SUCCESS` · `EMPTY_RESPONSE` · `AUTH_FAILED` · `RATE_LIMITED` · `NETWORK_ERROR` · `SCHEMA_DRIFT` · `FAILED`

**`NOT_PUBLISHED_YET`：** `data_sources.md` §5.7 第 8 态 — **Batch B+** vendor adapter；Batch A **不**纳入 parametrized 测试（§8.3 注释保留）。

```python
class FetchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    source_id: str
    data_domain: str
    market_id: str | None = None
    instrument_id: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    cursor: str | None = None
    force_refresh: bool = False

class FetchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    source_id: str
    data_domain: str
    status: Literal[
        "SUCCESS", "EMPTY_RESPONSE", "AUTH_FAILED", "RATE_LIMITED",
        "NETWORK_ERROR", "SCHEMA_DRIFT", "FAILED",
    ]
    raw_file_paths: list[str] = Field(default_factory=list)
    staging_table: str | None = None
    row_count: int = 0
    content_hash: str | None = None
    schema_hash: str | None = None
    as_of_timestamp: str | None = None
    publish_timestamp: str | None = None
    fetch_time: str
    error_message: str | None = None
```

**SUCCESS 证据字段互斥（Batch A · P1-3）：** `EMPTY_RESPONSE` 路径 `staging_table is None` 且 `raw_file_paths == []`；SUCCESS 路径 FakeAdapter **必须**非空（§8.4）；Batch A **不**断言 staging 表在 DuckDB 中存在。

### 6.4 FetchLogWriter · 列映射 · error_type

> **`fetch_log.error_type` 权威：** 本表为 **fetch 审计列** lowercase 分类，**≠** `data_sync_orchestrator.md` §13.8 job `error_type`（如 `NETWORK_TIMEOUT`）。Batch D 负责 job 级映射。

**`_ERROR_TYPE_MAP`（完整 · Batch A 实现必须一致）：**

| FetchResult.status | fetch_log.error_type |
|--------------------|----------------------|
| SUCCESS | `NULL` |
| EMPTY_RESPONSE | `empty` |
| AUTH_FAILED | `auth` |
| RATE_LIMITED | `rate_limit` |
| NETWORK_ERROR | `network` |
| SCHEMA_DRIFT | `schema` |
| FAILED | `failed` |

| fetch_log 列 | 来源 | Batch A 默认 |
|--------------|------|--------------|
| fetch_id | uuid4 | 生成 |
| run_id | result.run_id | 必填 |
| job_id | 参数 | NULL 可 |
| source_id / data_domain | result | 必填 |
| market_id / instrument_id | req 或参数 | NULL 可 |
| request_params_hash | SHA256(req.model_dump_json()) | SUCCESS 路径 **非空**（§8.4）；未传 req → NULL |
| status | result.status | 必填 |
| row_count | result.row_count | 0 |
| raw_file_paths | json.dumps(result.raw_file_paths) | `[]` → `"[]"` |
| content_hash / schema_hash | result | NULL 可 |
| as_of_timestamp / publish_timestamp | parse ISO → TIMESTAMP | NULL 可 |
| fetch_time | parse result.fetch_time | 必填 |
| latency_ms | 未测 | NULL |
| retry_count | 固定 | 0 |
| error_type | `_ERROR_TYPE_MAP[status]` | §8.4 断言 |
| error_message | result.error_message | 失败必填 |

**连接契约（P0-3）：** 生产 / `init_db` / Tier B 路径下 `FetchLogWriter.write()` 的 `con` **必须**来自 `ConnectionManager.writer()`。`fetch_log` 为审计表，不经 WriteManager，但不得另开裸 rw 连接写 prod 库。

**DB 错误：** `write()` 不吞异常；closed connection **必须** propagate（§8.4 **非 optional**）。

### 6.5 BaseDataAdapter

```python
def fetch(
    self,
    req: FetchRequest,
    *,
    con,
    job_id: str | None = None,
) -> FetchResult:
    self.registry.assert_enabled(req.source_id)
    self.registry.assert_domain_allowed(req.source_id, req.data_domain)
    if req.data_domain not in self.supported_domains:
        raise DomainNotAllowedError(...)
    # ↑ 以上校验失败：**不写** fetch_log，直接 raise（§8.4 0-row 测试）
    try:
        result = self._fetch_impl(req)
    except Exception as exc:
        result = FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="FAILED",
            fetch_time=_utc_now_iso(),
            error_message=str(exc),
        )
    self._log_writer.write(
        con, result, req=req, job_id=job_id,
        market_id=req.market_id, instrument_id=req.instrument_id,
    )
    return result
```

**FetchLogWriter.write 签名：**

```python
def write(
    self,
    con,
    result: FetchResult,
    *,
    req: FetchRequest | None = None,
    job_id: str | None = None,
    market_id: str | None = None,
    instrument_id: str | None = None,
) -> str:
    """返回 fetch_id。req 非空时写入 request_params_hash。"""
```

**禁止：** `_fetch_impl` 内换 `source_id`（silent fallback · §8.4 测试）。

---

## 7. Red Flags

| Red Flag | 预防 |
|----------|------|
| Shadow/Emergency | LegacyRoleError + 双 fixture |
| silent fetch / 异常无 log | §6.5 try/except + §8.4 |
| pre-impl 校验仍写 log | disabled/domain 失败 **0 条** fetch_log（§8.4） |
| silent fallback 换源 | §8.4 `test_fetch_implDoesNotSwitchSourceId` |
| Adapter 写 clean | 禁止 WriteManager；§8.5 `grep -riE` |
| 整库 schema.sql | 仅 003 两表 |
| 真实联网 | FakeAdapter |
| SUCCESS 无 evidence 字段 | FakeAdapter SUCCESS 必带 staging_table + raw_file_paths（§3.2 豁免真实文件） |

---

## 8. 实现步骤（TDD 全文）

### 8.0 共享测试基础设施（**先于 8.1** · bootstrap 顺序 **强制**）

> **P0-4：** 禁止在 §8.0 创建 `004_ingestion_sources.sql` 或测试正文（TDD 违反）。003 仅在 §8.1 RED 之后。

| Step | 动作 | 验证 |
|------|------|------|
| **0a** | 创建 **最小 stub**（仅占位，可 `raise NotImplementedError`）：`backend/app/datasources/__init__.py`、`fetch_result.py`、`source_registry.py`、`fetch_log.py`、`base_adapter.py` | `python -c "from backend.app.datasources.fetch_result import FetchRequest"` |
| **0b** | 创建 `tests/fixtures/*.yaml`（见下方清单） | 文件存在 |
| **0c** | 扩展 `tests/conftest.py`（见下方代码；保留 `PROJECT_ROOT`） | import OK |
| **0d** | `pytest --collect-only -q` | **105+** 收集、无 import 错误 |

**§8.1 再创建：** `004_ingestion_sources.sql` · `tests/test_source_registry.py` · `tests/test_data_adapter_contract.py`

**§8.0 Step 0b — fixture 清单：**

| 文件 | 用途 |
|------|------|
| `source_registry_valid.yaml` | 2 源 + 1 `domain_roles`（**单元测试**；≠ repo 全量 seed） |
| `source_registry_disabled_baostock.yaml` | assert_enabled 负向 |
| `bad_shadow.yaml` | LegacyRoleError |
| `bad_emergency.yaml` | LegacyRoleError |
| `bad_unknown_primary.yaml` | 不存在的 source_id |
| `bad_unknown_license_primary.yaml` | Primary 绑定 `license_type: unknown` 源 |
| `bad_invalid_fallback.yaml` | `fallback_policy: not_a_real_policy` |
| `malformed.yaml` | `sources: [` |

`bad_shadow.yaml` — 复制 valid，`domain_roles.market_bar_1d.validation: Shadow`

`bad_emergency.yaml` — 复制 valid，`domain_roles.market_bar_1d.primary: Emergency`

**§8.0 Step 0c — 在 `tests/conftest.py` 追加：**

```python
import json
from pathlib import Path
import duckdb
import pytest
from backend.app.db.migrate import apply_migrations
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.source_registry import SourceRegistry

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture
def registry_yaml_fixture() -> Path:
    return FIXTURES / "source_registry_valid.yaml"

@pytest.fixture
def bad_shadow_yaml() -> Path:
    return FIXTURES / "bad_shadow.yaml"

@pytest.fixture
def bad_emergency_yaml() -> Path:
    return FIXTURES / "bad_emergency.yaml"

@pytest.fixture
def bad_unknown_primary_yaml() -> Path:
    return FIXTURES / "bad_unknown_primary.yaml"

@pytest.fixture
def bad_unknown_license_primary_yaml() -> Path:
    return FIXTURES / "bad_unknown_license_primary.yaml"

@pytest.fixture
def bad_invalid_fallback_yaml() -> Path:
    return FIXTURES / "bad_invalid_fallback.yaml"

@pytest.fixture
def malformed_yaml() -> Path:
    return FIXTURES / "malformed.yaml"

@pytest.fixture
def disabled_registry():
    p = FIXTURES / "source_registry_disabled_baostock.yaml"
    reg = SourceRegistry(p)
    reg.load()
    return reg

@pytest.fixture
def loaded_registry(registry_yaml_fixture):
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    return reg

@pytest.fixture
def migrated_con():
    def _open(tmp_path):
        db = tmp_path / "t.duckdb"
        con = duckdb.connect(str(db))
        apply_migrations(con)
        return con
    return _open

def request_for(source_id: str, domain: str = "market_bar_1d") -> FetchRequest:
    return FetchRequest(run_id="run-1", source_id=source_id, data_domain=domain)

@pytest.fixture
def success_result():
    def _make():
        return FetchResult(
            run_id="run-1", source_id="baostock", data_domain="market_bar_1d",
            status="SUCCESS", row_count=42, fetch_time="2026-06-17T10:00:00Z",
            staging_table="stg_batch_a_smoke",
            raw_file_paths=["/data/raw/baostock/run-1.parquet"],
            content_hash="abc", schema_hash="def",
        )
    return _make

@pytest.fixture
def network_error_result():
    def _make():
        return FetchResult(
            run_id="run-1", source_id="baostock", data_domain="market_bar_1d",
            status="NETWORK_ERROR", row_count=0,
            fetch_time="2026-06-17T10:00:00Z", error_message="timeout",
        )
    return _make

@pytest.fixture
def empty_response_result():
    def _make():
        return FetchResult(
            run_id="run-1", source_id="baostock", data_domain="market_bar_1d",
            status="EMPTY_RESPONSE", row_count=0,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table=None, raw_file_paths=[],
        )
    return _make
```

- [ ] **Step 0d：** `pytest --collect-only -q` 无 import 错误

| 字段 | 内容 |
|------|------|
| Skill | TDD |
| 验证 | fixtures 存在 + stub import + collect-only |
| 已执行 | [ ] |

---

### 8.1 migration 003

| 字段 | 内容 |
|------|------|
| Skill | TDD · source-driven-development |
| 验证 | `pytest tests/test_schema_migration.py tests/test_schema_contract.py -k "Ingestion or ingestion or appliedVersions" -v` |
| 前置 | §8.0 **0d** 完成 |
| 已执行 | [ ] |

**Canonical 测试位置（P2-3 · 禁止重复）：** migration 表存在 / applied_versions → **仅** `tests/test_schema_migration.py`；列契约 → **仅** `tests/test_schema_contract.py`。**禁止**在 `test_source_registry.py` 写 `includesIngestionTables`。

- [ ] **Step 1 RED：** 在 `tests/test_schema_migration.py` 追加（完整，无 `...`）：

```python
INGESTION_TABLES = frozenset({"source_registry", "fetch_log"})

def test_applyMigrations_freshDb_includesIngestionTables() -> None:
    con = duckdb.connect(":memory:")
    applied = apply_migrations(con)
    assert "004_ingestion_sources" in applied
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert INGESTION_TABLES.issubset(tables)

def test_appliedVersions_afterMigration_containsIngestion() -> None:
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    assert applied_versions(con) == frozenset({
        "001_foundation",
        "002_registry_hardening",
        "004_ingestion_sources",
    })
```

- [ ] **Step 2 RED：** `pytest tests/test_schema_migration.py -k "Ingestion or appliedVersions" -v` → FAIL

- [ ] **Step 3：** 实现 `backend/app/db/migrations/004_ingestion_sources.sql`（列 **对齐** `specs/schema/schema.sql` `source_registry` + `fetch_log`）

- [ ] **Step 4 GREEN：** Step 2 PASS

- [ ] **Step 5 RED（schema contract · P0-2）：** 扩展 `tests/test_schema_contract.py`：

```python
INGESTION_CONTRACT_TABLES = ("source_registry", "fetch_log")

def test_ingestionMigrationColumns_existInSchemaContract() -> None:
    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")
    migration_text = (MIGRATIONS / "004_ingestion_sources.sql").read_text(encoding="utf-8")
    for table in INGESTION_CONTRACT_TABLES:
        mig_cols = _table_columns(migration_text, table)
        assert mig_cols, f"{table} missing from 003 migration"
        contract_cols = _table_columns(schema_text, table)
        assert contract_cols, f"{table} missing from schema.sql"
        assert mig_cols.issubset(contract_cols), (
            f"{table}: migration columns missing from schema.sql: {mig_cols - contract_cols}"
        )
```

- [ ] **Step 6 GREEN：** Step 5 PASS

- [ ] **Step 7：** `pytest tests/test_schema_migration.py tests/test_schema_contract.py -q` 全绿

**已知限制（文档化 · 非 Batch A 阻塞）：** `verify_applied_checksums` 仍无 dedicated 测试（CodeGraph 标注）；003 内容校验由 Step 5 contract 测试覆盖。

---

### 8.2 SourceRegistry

| 字段 | 内容 |
|------|------|
| 前置 | **§8.1 Step 7 完成** |
| 验证 | `pytest tests/test_source_registry.py -v` |
| 已执行 | [ ] |

**测试清单（先 RED 后实现 §6.1–6.2）：**

```python
# AC-2
def test_load_validYaml_parsesPrimaryDomainRoles(registry_yaml_fixture): ...
def test_defaultYaml_loadsFromRepoSeed():  # P3-4 · SourceRegistry.DEFAULT_YAML = specs/datasource_registry/source_registry.yaml
    reg = SourceRegistry()
    reg.load()
    roles = reg.get_domain_roles("market_bar_1d")
    assert roles.primary_source_id == "baostock"
    assert isinstance(roles, DomainRoleBinding)

# AC-3
def test_load_yamlWithShadowRole_raisesLegacyRoleError(bad_shadow_yaml): ...
def test_load_yamlWithEmergencyRole_raisesLegacyRoleError(bad_emergency_yaml): ...

# AC-4 + P1-11
def test_load_primaryUnknownLicense_raises(bad_unknown_license_primary_yaml): ...
def test_load_yaml_unknownPrimaryReference_raises(bad_unknown_primary_yaml): ...
def test_load_invalidFallbackPolicy_raises(bad_invalid_fallback_yaml): ...
def test_load_malformedYaml_raises(malformed_yaml): ...
def test_getSource_unknownId_raisesSourceNotFoundError(loaded_registry): ...

# F-13 · 合法 FallbackPolicy（data_sources.md §5.3）
@pytest.mark.parametrize("policy", [
    "retry_same_source", "use_validation_source_with_flag", "use_last_good_cache",
    "mark_missing", "manual_review_required", "skip_until_next_publish",
])
def test_load_validFallbackPolicy_succeeds(policy, tmp_path, registry_yaml_fixture): ...

# AC-4
def test_assertDomainAllowed_unknownDomain_raises(loaded_registry): ...
def test_assertEnabled_disabledSource_raisesSourceDisabledError(disabled_registry): ...

# sync · P0-4 / P1-7 / P2-1
def test_syncToDb_insertsSourceRows(tmp_path, registry_yaml_fixture): ...
def test_syncToDb_roundTrip_preservesAllColumns(tmp_path, registry_yaml_fixture):
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    reg.sync_to_db(con)
    row = con.execute("""
        SELECT rate_limit_policy, auth_required, allowed_domain
        FROM source_registry WHERE source_id='baostock'
    """).fetchone()
    assert row[0]  # rate_limit_policy non-empty
    assert json.loads(row[2])  # allowed_domain JSON array

def test_syncToDb_calledTwice_isIdempotent(tmp_path, registry_yaml_fixture):
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    n1 = reg.sync_to_db(con)
    n2 = reg.sync_to_db(con)
    assert n1 == n2
    count = con.execute("SELECT COUNT(*) FROM source_registry").fetchone()[0]
    assert count == n1

def test_syncToDb_secondCall_updatesUpdatedAt(tmp_path, registry_yaml_fixture):  # P1-4
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    reg.sync_to_db(con)
    t1 = con.execute(
        "SELECT updated_at FROM source_registry WHERE source_id='baostock'"
    ).fetchone()[0]
    reg.sync_to_db(con)
    t2 = con.execute(
        "SELECT updated_at FROM source_registry WHERE source_id='baostock'"
    ).fetchone()[0]
    assert t2 >= t1
```

- [ ] 实现 `source_registry.py` → 全文件 GREEN

---

### 8.3 FetchRequest / FetchResult

| 验证 | `pytest tests/test_data_adapter_contract.py -k "FetchRequest or FetchResult" -v` |
| 已执行 | [ ] |

```python
import pytest
from pydantic import ValidationError
from backend.app.datasources.fetch_result import FetchRequest, FetchResult

CONTRACT_STATUSES = [
    "SUCCESS", "EMPTY_RESPONSE", "AUTH_FAILED", "RATE_LIMITED",
    "NETWORK_ERROR", "SCHEMA_DRIFT", "FAILED",
]
# NOT_PUBLISHED_YET: Batch B+ only (data_sources.md §5.7) — intentionally excluded

@pytest.mark.parametrize("status", CONTRACT_STATUSES)
def test_fetchResult_allContractStatuses_areAccepted(status):
    r = FetchResult(
        run_id="r", source_id="s", data_domain="d",
        status=status, fetch_time="2026-06-17T10:00:00Z",
    )
    assert r.status == status

def test_fetchRequest_missingRunId_raisesValidationError():
    with pytest.raises(ValidationError):
        FetchRequest(source_id="s", data_domain="d")

def test_fetchResult_stagingTableField_roundTrips():  # P3-3
    r = FetchResult(
        run_id="r", source_id="s", data_domain="d", status="SUCCESS",
        fetch_time="2026-06-17T10:00:00Z", staging_table="stg_x",
    )
    assert r.staging_table == "stg_x"
```

---

### 8.4 FetchLogWriter + BaseDataAdapter

| 验证 | `pytest tests/test_data_adapter_contract.py -v` |
| 已执行 | [ ] |

**imports（P2-3 · 测试文件顶部）：**

```python
import json
import pytest
from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.datasources.fetch_log import FetchLogWriter
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.source_registry import SourceDisabledError, DomainNotAllowedError
# + conftest helpers: migrated_con, loaded_registry, disabled_registry, request_for, ...
```

**FetchLogWriter 测试：**

```python
def test_write_successResult_insertsFetchLogRow(tmp_path, success_result, request_for):
    con = migrated_con(tmp_path)
    req = request_for("baostock")
    fetch_id = FetchLogWriter().write(con, success_result(), req=req, job_id="job-1")
    row = con.execute(
        "SELECT status, row_count, job_id, raw_file_paths, error_type, request_params_hash FROM fetch_log WHERE fetch_id=?",
        [fetch_id],
    ).fetchone()
    assert row[0] == "SUCCESS" and row[1] == 42 and row[2] == "job-1"
    assert json.loads(row[3]) == ["/data/raw/baostock/run-1.parquet"]
    assert row[4] is None
    assert row[5]  # request_params_hash non-empty when req passed (F-07)

def test_write_failedResult_stillPersists(tmp_path, network_error_result):
    con = migrated_con(tmp_path)
    fetch_id = FetchLogWriter().write(con, network_error_result())
    row = con.execute(
        "SELECT status, error_type FROM fetch_log WHERE fetch_id=?", [fetch_id]
    ).fetchone()
    assert row[0] == "NETWORK_ERROR" and row[1] == "network"

def test_write_closedConnection_propagates(tmp_path, success_result):  # 非 optional
    con = migrated_con(tmp_path)
    con.close()
    with pytest.raises(duckdb.Error):
        FetchLogWriter().write(con, success_result())

def test_write_underWriterLock_insertsFetchLogRow(tmp_path, success_result, request_for):  # P0-3 集成
    from backend.app.db.connection import ConnectionManager
    db = tmp_path / "writer.duckdb"
    cm = ConnectionManager(db_path=db)
    apply_migrations(cm.writer())
    req = request_for("baostock")
    fetch_id = FetchLogWriter().write(cm.writer(), success_result(), req=req)
    row = cm.writer().execute(
        "SELECT COUNT(*) FROM fetch_log WHERE fetch_id=?", [fetch_id]
    ).fetchone()[0]
    assert row == 1
    cm.close()
```

**BaseDataAdapter · FakeAdapter：**

```python
class FakeAdapter(BaseDataAdapter):
    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d"})
    def _fetch_impl(self, req):
        return FetchResult(
            run_id=req.run_id, source_id=self.source_id, data_domain=req.data_domain,
            status="SUCCESS", row_count=1, fetch_time="2026-06-17T10:00:00Z",
            staging_table="stg_test", raw_file_paths=["/tmp/x"],
        )

def test_fetch_disabledSource_raisesBeforeImpl_andWritesNoFetchLog(...):  # pre-impl · 0 rows
def test_fetch_unsupportedDomainOnAdapter_raises_andWritesNoFetchLog(...): ...
def test_fetch_successResult_writesExactlyOneFetchLogRow(...):  # AC-7
def test_fetch_calledTwice_writesTwoRows(...):  # AC-7
def test_fetch_alwaysWritesFetchLog_evenOnEmptyResponse(empty_response_result, ...): ...
def test_fetch_emptyResponse_hasNoStagingEvidence(empty_response_result, ...):  # P1-3
def test_fetch_implRaises_stillWritesFetchLogAndReturnsFailed(...):  # P0-3
def test_fetch_implDoesNotSwitchSourceId(...):  # P1-10
def test_fetch_success_carriesEvidenceFields(...):  # P1-5
```

- [ ] 实现 `fetch_log.py`、`base_adapter.py` → GREEN
- [ ] 更新 `datasources/__init__.py`

---

### 8.5 全量回归 + prod-path

| 验证 | §10 Tier A/B/C |
| 已执行 | [ ] |

```powershell
# Tier A（本地全量）
pytest tests/test_source_registry.py tests/test_data_adapter_contract.py -v
pytest -q --cov=backend --cov-fail-under=75
ruff check .
python -m compileall backend scripts
# P2-1 · 与 CI / AUDIT A3 同口径
grep -riE "WriteManager|write_manager" backend/app/datasources/ && exit 1 || true
# PowerShell 等价：if (Select-String -Path backend/app/datasources/* -Pattern 'WriteManager|write_manager' -Quiet) { exit 1 }

# Tier B · P1-9（默认 QMD_DATA_ROOT=data/）
python scripts/init_db.py
python -c "import duckdb; from pathlib import Path; p=Path('data/duckdb/quant_monitor.duckdb'); con=duckdb.connect(str(p)); print(sorted(r[0] for r in con.execute('SHOW TABLES').fetchall()))"
# 输出须含 source_registry, fetch_log
python scripts/init_db.py   # 第二次幂等

# Tier C · prod-path（F-01 修正）
$env:QMD_DATA_ROOT="data"; pytest -q

# P3-1 · 可选（Batch A 不阻塞 Execute）
# monkeypatch QMD_DATA_ROOT + fetch smoke — 完整交叉见 Batch D smoke
```

**通过条件：** 全库 `pytest -q` exit 0；coverage ≥75%（与 CI 一致）；**不硬编码**测试计数（基线 105 @ `3d7f93a` + Batch A 增量）。

---

### 8.6 下游接口

| 下游 | 依赖 | Batch A 交付 |
|------|------|----------------|
| Batch B | `BaseDataAdapter`、真实 raw 文件 + rule 2 落地 | 字段可携带；**不**校验 `FileRegistry.local_path` 对齐（Batch B 偿还） |
| Batch C | `FetchResult.status`、`staging_table` 字段 | SUCCESS 证据字段规则 §6.3；**不**断言 staging 表存在于 DuckDB |
| Batch D | `job_id` 参数、`DomainRoleBinding`（§6.2 已冻结） | `get_domain_roles()` 公共 API + writer 锁集成测 |
| Batch D smoke | ResourceGuard + ingestion 共存（P3-1） | **未在 Batch A 实现** — 见 remediation §未修复 |

---

## 9. 测试层次

| 层次 | 命令 | 通过 |
|------|------|------|
| 单元 | `pytest tests/test_source_registry.py tests/test_data_adapter_contract.py -v` | 全绿 |
| 集成 | `pytest -q` | exit 0 |
| 管道 | `init_db` ×2 @ `data/` | 幂等 |
| smoke | `pytest tests/test_schema_migration.py -q` | 含 003 |

---

## 10. 验收 Tier

| Tier | 环境 | 命令 | 通过条件 | CI 覆盖 | 勾 |
|------|------|------|----------|---------|-----|
| A | ci + local | Batch A 单测 + `pytest -q --cov-fail-under=75` + ruff + compileall + grep WriteManager | 全绿/无匹配 | **pytest+cov+ruff+compileall+grep**（`.github/workflows/ci.yml`） | [ ] |
| B | prod-path | `init_db` + SHOW TABLES（默认 `QMD_DATA_ROOT=data/`） | 含两表 + 幂等 | **否**（Execute/Audit 手工 · A7） | [ ] |
| C | prod-path | `$env:QMD_DATA_ROOT='data'; pytest -q` | exit 0 | **否**（prod-path 隔离） | [ ] |

---

## 11. Execute 交接

- [ ] §8 证据 + §10 勾 + §12 勾
- [ ] **交接 Audit**（勿 finish-work）

---

## 12. Execute Skill

| Skill | 本任务 | 绑定 | 已执行 |
|-------|--------|------|--------|
| test-driven-development | 必做 | §8.0–8.4 | [ ] |
| incremental-implementation | 必做 | §8.x 顺序 | [ ] |
| source-driven-development | 条件 | §8.1 SQL | [ ] |
| systematic-debugging | 条件 | RED | [ ] |
| trellis-implement | 必做 | Execute | [ ] |

**Audit → `AUDIT.plan.md`**

---

## 13. 对抗审计 remediation 索引

> **全表（26 项逐项状态）：** `research/adversarial-audit-remediation.md`  
> **原始报告：** `research/adversarial-audit-agent-alpha.md` · `research/adversarial-audit-agent-beta.md`

| 类别 | 说明 |
|------|------|
| **已修复（v1.3 文档/plan/CI/schema）** | P0 四项 + 全部 P1–P3 plan 修订；见 remediation 表「状态=已修复」 |
| **待 Execute §8 实现（非遗漏）** | stub、003、测试代码、ingestion 模块 — plan 已写清，**代码尚未落地** |
| **明确未修复 / 延后** | remediation 表「状态=Execute 待实现」或「Batch B+ 偿还」 — **不得静默忽略** |
