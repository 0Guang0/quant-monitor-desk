# Execute 补账 — §8.1–§8.4 RED 证据 + Karpathy / Testing 对照

> **角色：** Execute（补录，非 Audit）  
> **日期：** 2026-06-17  
> **说明：** 初轮 Execute 为批量实现，未留 RED 日志。本文按 MASTER §8.1–§8.4 **补录 RED→GREEN 证据链**；其中 §8.1/§8.3/§8.4 为 **2026-06-17 补跑实测**，§8.2 依据 §8.0 stub 契约推断（未 mutate 源码重放，避免污染工作区）。

---

## 1. RED 证据总表

| 切片 | 先行测试（Tracer / 代表） | RED 命令 | RED 失败类型 | 补录方式 |
|------|---------------------------|----------|--------------|----------|
| **§8.1** | `test_applyMigrations_freshDb_includesIngestionTables` | 见 §2.1 | `AssertionError` + `FileNotFoundError` | **实测** |
| **§8.2** | `test_load_validYaml_parsesPrimaryDomainRoles` | 见 §2.2 | `NotImplementedError` | **契约推断** |
| **§8.3** | `test_fetchRequest_missingRunId_raisesValidationError` | 见 §2.3 | `Failed: DID NOT RAISE ValidationError` | **实测** |
| **§8.4** | `test_write_successResult_insertsFetchLogRow` | 见 §2.4 | `NotImplementedError` | **实测** |

**GREEN 统一验证（当前仓库状态）：**

```powershell
pytest tests/test_schema_migration.py tests/test_schema_contract.py -k "Ingestion or ingestion or appliedVersions" -q
pytest tests/test_source_registry.py -v
pytest tests/test_data_adapter_contract.py -v
```

---

## 2. 分步 RED→GREEN 证据

### 2.1 §8.1 — migration 004

**Plan 顺序：** Step 1 写 RED 测试 → Step 2 确认 FAIL → Step 3 写 `004_ingestion_sources.sql` → Step 4–6 GREEN。

**先行 RED 测试：**

- `tests/test_schema_migration.py::test_applyMigrations_freshDb_includesIngestionTables`
- `tests/test_schema_contract.py::test_ingestionMigrationColumns_existInSchemaContract`

**补录 RED 复现（临时移走 migration 文件后跑测，已恢复）：**

```powershell
# 仅补录演示；勿在生产分支保留
Move-Item backend\app\db\migrations\004_ingestion_sources.sql backend\app\db\migrations\004_ingestion_sources.sql.redbak
pytest tests/test_schema_migration.py::test_applyMigrations_freshDb_includesIngestionTables `
       tests/test_schema_contract.py::test_ingestionMigrationColumns_existInSchemaContract -v --tb=short
Move-Item backend\app\db\migrations\004_ingestion_sources.sql.redbak backend\app\db\migrations\004_ingestion_sources.sql
```

**实测 RED 输出（摘要）：**

```
FAILED test_applyMigrations_freshDb_includesIngestionTables
  assert "004_ingestion_sources" in applied
  AssertionError: assert '004_ingestion_sources' in ['001_foundation', '002_registry_hardening', '003_resource_guard_metrics']

FAILED test_ingestionMigrationColumns_existInSchemaContract
  FileNotFoundError: ...\004_ingestion_sources.sql
```

**GREEN 实现：** `backend/app/db/migrations/004_ingestion_sources.sql`（列对齐 `specs/schema/schema.sql`）。

**GREEN 验证：** 上述两测试 + `test_appliedVersions_afterMigration_containsIngestion` 全 PASS。

---

### 2.2 §8.2 — SourceRegistry

**Plan 顺序：** §8.1 Step 7 完成后 → 写 `tests/test_source_registry.py` RED → 实现 `source_registry.py` GREEN。

**先行 RED 测试（Tracer bullet）：**

```python
def test_load_validYaml_parsesPrimaryDomainRoles(registry_yaml_fixture):
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    roles = reg.get_domain_roles("market_bar_1d")
    assert roles.primary_source_id == "baostock"
```

**§8.0 stub 契约（MASTER Step 0a）：** `source_registry.py` 仅占位，`load()` 应 `raise NotImplementedError`。

**推断 RED 行为（未 mutate 源码重放）：**

```
NotImplementedError
  at SourceRegistry.load()
  during test_load_validYaml_parsesPrimaryDomainRoles
```

**负向 RED 测试（无需实现即可 RED）：** 以下测试在 **任何** 未实现/空壳 loader 上均应先 FAIL（实现后 GREEN）：

| 测试 | 期望异常 |
|------|----------|
| `test_load_yamlWithShadowRole_raisesLegacyRoleError` | `LegacyRoleError` |
| `test_load_yamlWithEmergencyRole_raisesLegacyRoleError` | `LegacyRoleError` |
| `test_load_primaryUnknownLicense_raises` | `InvalidRegistryError` |
| `test_assertEnabled_disabledSource_raisesSourceDisabledError` | `SourceDisabledError` |

**GREEN 实现：** `backend/app/datasources/source_registry.py`（`SourceRecord`、`DomainRoleBinding`、UPSERT `sync_to_db`）。

**GREEN 验证：** `pytest tests/test_source_registry.py -v` → **21 passed**。

---

### 2.3 §8.3 — FetchRequest / FetchResult

**先行 RED 测试（Tracer bullet）：**

```python
def test_fetchRequest_missingRunId_raisesValidationError():
    with pytest.raises(ValidationError):
        FetchRequest(source_id="s", data_domain="d")
```

**补录 RED 复现（临时替换为无 `run_id` 必填约束的 minimal Pydantic 模型，已恢复）：**

```
FAILED test_fetchRequest_missingRunId_raisesValidationError
  Failed: DID NOT RAISE ValidationError
```

**含义：** stub 模型允许缺 `run_id` → 测试正确 RED；完整模型加 `run_id: str` + `extra="forbid"` 后 GREEN。

**parametrize RED（7 status）：** `test_fetchResult_allContractStatuses_areAccepted` — stub 若 `status: str` 无 Literal 约束仍可能 GREEN，但 **contract 价值在 GREEN 后** 与 `data_adapter_contract.md` 对齐；初 RED 阶段可用非法 status 字符串验证 Literal 拒绝（未单独补跑）。

**GREEN 验证：**

```powershell
pytest tests/test_data_adapter_contract.py -k "FetchRequest or FetchResult" -v
```

→ **10 passed**（含 7 态 parametrized）。

---

### 2.4 §8.4 — FetchLogWriter + BaseDataAdapter

**FetchLogWriter Tracer RED 测试：**

```python
def test_write_successResult_insertsFetchLogRow(...):
    fetch_id = FetchLogWriter().write(con, success_result(), req=req, job_id="job-1")
    # assert row status == SUCCESS, row_count == 42, error_type is None, ...
```

**补录 RED 复现（`FetchLogWriter.write` stub → `NotImplementedError`，已恢复）：**

```
FAILED test_write_successResult_insertsFetchLogRow
  NotImplementedError
  at FetchLogWriter.write(...)
```

**BaseDataAdapter Tracer RED 测试（代表行为，非 I/O stub）：**

| 测试 | RED 条件（实现前） | GREEN 断言（业务语义） |
|------|-------------------|------------------------|
| `test_fetch_disabledSource_raisesBeforeImpl_andWritesNoFetchLog` | 未校验 disabled | `SourceDisabledError` + fetch_log 行数 **0** |
| `test_fetch_implRaises_stillWritesFetchLogAndReturnsFailed` | 未 catch 异常 | `status==FAILED` + log 行数 **1** |
| `test_fetch_implDoesNotSwitchSourceId` | silent fallback | result/log 的 `source_id==baostock` |
| `test_write_underWriterLock_insertsFetchLogRow` | 未接 ConnectionManager | writer 锁下 INSERT 成功 |

**GREEN 验证：** `pytest tests/test_data_adapter_contract.py -v` → **22 passed**。

---

## 3. Karpathy Guidelines 对照

| 原则 | Batch A 实践 | 符合？ | 说明 |
|------|-------------|--------|------|
| **1. Think Before Coding** | 遵循 MASTER §6 契约、DECISIONS 路径/004 序号、拒绝 Shadow/Emergency | ✅ | 假设来自 Plan 冻结，未 silent override |
| **2. Simplicity First** | 5 个模块文件；无多余抽象层；无 Batch B+ 功能 | ✅ | 无 speculative config / 未请求特性 |
| **3. Surgical Changes** | 仅 `datasources/*`、004 migration、Batch A 测试/fixtures/conftest | ✅ | 未改 WriteManager / ValidationGate |
| **4. Goal-Driven Execution** | AC-1~8 + §10 Tier A/B/C 可验证 | ✅ | 初轮缺 RED 日志；本文补 RED 链 |

**Karpathy 提醒项（非阻塞）：**

- `disabled_registry` fixture 将 Primary 设为 `qmt_xtdata` 以通过 `load()` 校验 — 属 **测试数据设计**，已在 Execute 汇总说明，非过度工程。

---

## 4. Testing Guidelines 对照

| 规则 | Batch A 测试实践 | 符合？ | 说明 |
|------|-----------------|--------|------|
| **1. Mock Only External I/O** | **无** `mock`/`patch`；YAML 真实 fixture；DuckDB 用 `tmp_path` + `migrated_con` | ⚳ **项目决策优先** | `DECISIONS.md` §5 / MASTER §8 要求真实 YAML + 隔离 DuckDB；与 guideline「mock DB」在 **集成测层**  intentionally 不同 |
| **2. Assert Behavior** | 断言 `primary_source_id`、`error_type`、`fetch_log` 行数、JSON 列值 | ✅ | 未 assert 私有方法调用次数 |
| **3. Business-Semantic Assertion** | 如 `assert roles.primary_source_id == "baostock"`、`assert row[1] == "network"` | ✅ | 无「仅 assertNotNull」类空断言 |
| **4. Full Input Spectrum** | 正常 / 负向 YAML / disabled / 非法 domain / 7 status / 异常 `_fetch_impl` | ✅ | parametrized fallback_policy ×6 |
| **5. Name Tests** | `test_load_yamlWithShadowRole_raisesLegacyRoleError` 等 | ✅ | 与 Round 1 `test_applyMigrations_*` camelCase 风格一致 |
| **6. Five-Step Workflow** | coverage **94%**；gate **≥75%**；Batch A 单测 43 条 | ✅ | Scope→Generate→Gate 已做；Refactor 留 Audit |

**Testing 偏差说明（可接受）：**

1. **真实 DuckDB 非 mock** — Round 2 DECISIONS 明确要求；FetchLogWriter / sync_to_db 测的是 **持久化行为**，mock 连接会削弱 AC-6/AC-7。
2. **Writer 锁集成测** — `test_write_underWriterLock_insertsFetchLogRow` 用真实 `ConnectionManager`，符合 DECISIONS P0-3。
3. **测试内嵌 `EmptyAdapter` 类** — 仅覆盖 EMPTY_RESPONSE 路径，属 contract 测试常见写法，未污染生产包。

---

## 5. Execute 欠账闭合状态

| 欠账项 | 状态 |
|--------|------|
| §8.1 RED 实测证据 | ✅ 本文 §2.1 |
| §8.2 RED 证据 | ✅ 本文 §2.2（stub 契约 + 负向测试清单；未 mutate 源码重放） |
| §8.3 RED 实测证据 | ✅ 本文 §2.3 |
| §8.4 RED 实测证据 | ✅ 本文 §2.4 |
| Karpathy Guidelines 对照 | ✅ 本文 §3 |
| testing-guidelines 对照 | ✅ 本文 §4 |
| 当前仓库 GREEN 复检 | ✅ 补录后 tracer 测试 3/3 passed |

**仍未属于 Execute 范围（归 Audit）：** `trellis-check` 完整 Step 1–6 报告、交叉层 formal sign-off → 见 `AUDIT.plan.md`。

---

## 6. 初轮 Execute 与本次补账的差异（诚实记录）

| 项目 | 初轮 | 补账后 |
|------|------|--------|
| TDD 时序 | 实现与测试同批写入 | RED 证据已文档化 + 三节实测 |
| §8.0 stub | 直接写完整实现 | 补录确认 §8.0 应为 NotImplementedError stub |
| Karpathy / testing-guidelines | 未读 | 已读并对照本文 §3–§4 |
