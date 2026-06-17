# MASTER 计划 — Round 2 Batch B（013 core adapter skeletons）

> **Execute 入口（唯一全文）** · **v1.1** · 2026-06-17  
> v1.1：对抗审计 26 项全量修订 · `research/adversarial-audit-remediation.md`  
> v1.0 5d：`research/plan-5d-doubt-review.md`

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-17-round2-batch-b-adapters` |
| 关联 Round | `ROUND_2_DATA_INGESTION_VALIDATION` Batch **B** |
| 前置 | Batch A PASS @ `ab8d1eb`（182 tests · cov 93%） |
| 决策 | `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md` |
| analysis_waiver | `false` |

### 0.1 门控速查

| 项 | 值 |
|----|-----|
| **Batch A checkpoint** | 已通过（DECISIONS §8 全勾） |
| **6.pre** | GitNexus/CodeGraph 刷新 → `research/gitnexus-execute-summary.md` |
| **Execute 后再索引** | §8.6 完成后 `node .gitnexus/run.cjs analyze` + `npx @colbymchenry/codegraph sync`（偿还 Batch A P3-7） |
| **Execute prod-path** | `QMD_DATA_ROOT` 默认 `<repo>/data` |
| **Audit sandbox** | `QMD_DATA_ROOT=.audit-sandbox/data` |
| **基线测试数** | **182** collected @ Plan 冻结 |
| **默认分支** | `master`（`detect_changes` 对照） |

**Execute 开场白：**

```text
Round 2 Batch B Execute：6.pre → MASTER + implement.jsonl + DECISIONS → §8.0→8.6 逐步 RED/GREEN（证据非空）→ §9/§10 → detect_changes → validate-execute-handoff → §11 Audit → GitNexus 再索引。
SUCCESS：RawStore 真实文件 + 可选 FileRegistry.register；禁止 adapters 内 import WriteManager。
```

---

## 1. 目标

### 1.1 一句话

交付五个 vendor adapter skeleton + factory；可注入 FetchPort；SUCCESS 写真实 raw 文件并 **可选** 登记 FileRegistry（偿还 Batch A §8.6）；cninfo 未发布语义经 EMPTY_RESPONSE 覆盖。

### 1.2 子交付物

| ID | 交付 | 路径 |
|----|------|------|
| B-1 | FetchPort + Stub/Unavailable/Failure ports | `adapters/fetch_port.py` |
| B-2 | SkeletonAdapterBase | `adapters/skeleton_base.py` |
| B-3 | 五 vendor adapter | `adapters/*.py` |
| B-4 | `create_adapter()` factory | `adapters/__init__.py` |
| B-5 | 测试 | `tests/test_adapter_skeletons.py` |

### 1.3 非目标

- 真实 HTTP/SDK、Orchestrator、ValidationGate 替换、migration 005。
- **不** 扩展 `FetchResult.status` 第 8 态 Literal（`NOT_PUBLISHED_YET` 用 **EMPTY_RESPONSE + error_message** 偿还 DECISIONS GPT-NOT-PUBLISHED）。
- DuckDB staging 表存在性校验（Batch C）。
- `scripts/sync_registry.py` / init_db 自动 sync（**defer Batch D** · DECISIONS GPT-init_db）。
- GPT-SEC-CI gitleaks（**并行 sprint，非本 Execute 阻塞**）。

---

## 2. 预期结果（A5 trace-ac）

| # | 预期结果 | 验证链 |
|---|----------|--------|
| AC-1 | 五 adapter + factory 可 import | §8.5 + §10 A |
| AC-2 | SUCCESS → 磁盘 raw + `raw_file_paths` + **content_hash 与 RawStore 一致** | §8.1 + §10 A |
| AC-3 | parametrized PortError → status + fetch_log error_type | §8.1 + §10 A |
| AC-4 | QMT AUTH_FAILED **与** SUCCESS 两路径 | §8.3 |
| AC-5 | adapters 无 WriteManager import | §10 grep |
| AC-6 | registry source_id/domains 对齐 | §8.2–8.5 |
| AC-7 | yahoo `validation_only` 可查询 | §8.5 |
| AC-8 | 全库 pytest + cov ≥75% | §10 A/C |
| AC-9 | **FileRegistry**：register 后 `local_path` = `FetchResult.raw_file_paths[0]` | §8.1 + §10 B |
| AC-10 | **cninfo** 未发布 → EMPTY_RESPONSE + 业务 error_message + fetch_log | §8.4 |

---

## 3. 范围与边界

### 3.1 In scope

- `backend/app/datasources/adapters/**`
- `tests/test_adapter_skeletons.py`、`tests/conftest.py`（`raw_data_root`、`file_registry_stack`）
- **Batch A 偿还：** raw 文件 + FileRegistry 对齐（Beta §6）；cninfo 未发布语义（GPT-NOT-PUBLISHED）
- `backend/app/datasources/__init__.py` export 更新

### 3.2 Out of scope · 显式 defer

| 项 | 偿还批次 | 说明 |
|----|----------|------|
| staging DuckDB 表校验 | Batch C | GPT-staging-DB |
| YAML tombstone | Batch D | GPT-P2-2 |
| init_db 自动 sync_registry | Batch D | GPT-init_db |
| ResourceGuard 交叉 smoke | Batch D | GPT-P3-6 |
| fetch_log DB CHECK | Batch C 前 | GPT-P1-5-DB |
| gitleaks / hooks CI | 并行 sprint | GPT-SEC-CI（非阻塞） |

### 3.3 已确认

`research/grill-me-session.md`（v1.1 已与 MASTER 对齐）

---

## 4. 技术设计摘要

```text
create_adapter(source_id, registry, data_root, fetch_port=None, file_registry=None)
  → VendorAdapter(SkeletonAdapterBase)
  → BaseDataAdapter.fetch(con, req)
      → FetchPort.fetch_payload(req)
      → RawStore.save → SavedFile
      → [optional] FileRegistry.register(saved)
      → FetchResult(SUCCESS, raw_file_paths, content_hash, row_count=1)
      → FetchLogWriter.write(...)
```

---

## 5. 依赖与切片

```text
§8.0 stubs + conftest + collect-only (≥1 tracer)
§8.1 FetchPort + SkeletonAdapterBase + raw + FileRegistry + parametrized failures
§8.2 BaostockAdapter
§8.3 QmtXtdataAdapter (AUTH + SUCCESS)
§8.4 Akshare + Cninfo (+ unpublished EMPTY)
§8.5 Yahoo + factory
§8.6 回归 + ci_ingestion_smoke + GitNexus 再索引
```

---

## 6. 接口契约

### 6.1 FetchPort

```python
class FetchPort(Protocol):
    def fetch_payload(self, req: FetchRequest) -> FetchPayload: ...

class PortError(Exception):
    status: Literal["AUTH_FAILED", "RATE_LIMITED", "NETWORK_ERROR", "SCHEMA_DRIFT", "EMPTY_RESPONSE", "FAILED"]
    message: str
```

### 6.2 SkeletonAdapterBase

```python
class SkeletonAdapterBase(BaseDataAdapter):
    def __init__(
        self,
        registry: SourceRegistry,
        *,
        raw_store: RawStore,
        fetch_port: FetchPort,
        file_registry: FileRegistry | None = None,
    ) -> None:
        super().__init__(registry)  # BaseDataAdapter 仅收 registry
        self._raw_store = raw_store
        self._fetch_port = fetch_port
        self._file_registry = file_registry

    def _resolve_as_of(self, req: FetchRequest) -> str:
        """end_time[:10] if set else UTC date YYYY-MM-DD."""

    def _fetch_impl(self, req: FetchRequest) -> FetchResult:
        # PortError → status=exc.status, row_count=0, error_message=exc.message
        # SUCCESS → row_count=1（skeleton 固定：1 payload = 1 logical unit）
        # saved = raw_store.save(...); optional file_registry.register(saved)
        # return FetchResult(..., raw_file_paths=[saved.local_path], content_hash=saved.content_hash)
```

**PortError → fetch_log.error_type（与 `fetch_log.py` 一致）：**

| status | error_type |
|--------|------------|
| SUCCESS | NULL |
| EMPTY_RESPONSE | empty |
| AUTH_FAILED | auth |
| RATE_LIMITED | rate_limit |
| NETWORK_ERROR | network |
| SCHEMA_DRIFT | schema |
| FAILED | failed |

**边界：** adapters 包 **禁止** `WriteManager` import；`FileRegistry` **允许** 构造函数注入（登记经 WriteManager 在 storage 层完成）。

### 6.3 create_adapter

```python
def create_adapter(
    source_id: str,
    registry: SourceRegistry,
    data_root: Path,
    *,
    fetch_port: FetchPort | None = None,
    file_registry: FileRegistry | None = None,
) -> BaseDataAdapter:
    """fetch_port is None → 各 vendor 默认 StubFetchPort()。
    file_registry is None → 不登记（单测可省略；集成测应注入）。"""
```

| source_id | 类 |
|-----------|-----|
| qmt_xtdata | QmtXtdataAdapter |
| baostock | BaostockAdapter |
| akshare | AkshareAdapter |
| cninfo | CninfoAdapter |
| yahoo_finance | YahooFinanceAdapter |

### 6.4 Cninfo 未发布（GPT-NOT-PUBLISHED 偿还）

`UnpublishedPort` 抛 `PortError(EMPTY_RESPONSE, "announcement not published yet")` — **不** 扩 contract 8 态。

---

## 7. Red Flags

| Red Flag | 预防 |
|----------|------|
| FileRegistry 与 raw 路径不一致 | AC-9 §8.1 |
| SUCCESS 无 content_hash | AC-2 |
| factory fetch_port=None 行为未测 | §8.5 |
| 跳过 ci_ingestion_smoke | §10 Tier B |
| 未 GitNexus 再索引 | §8.6 |

---

## 8. 实现步骤

> 完整 pytest → `research/batch-b-section8-tests.md`

### 8.0 基础设施

| 字段 | 值 |
|------|-----|
| 绑定 §12 | test-driven-development · incremental-implementation |
| RED 命令 | `pytest tests/test_adapter_skeletons.py --collect-only -q` |
| RED 预期 | ERROR（模块不存在） |
| GREEN 命令 | 同上 |
| GREEN 预期 | **≥1** test collected（占位 tracer 名 `test_adapterPackage_importable`） |
| 环境 | local |
| RED 证据 | exit 4 · `ERROR: file or directory not found: tests/test_adapter_skeletons.py` |
| GREEN 证据 | exit 0 · `tests/test_adapter_skeletons.py: 1` collected |
| 已执行 | [x] |

**动作：** adapters 包 stub；`test_adapterPackage_importable`；conftest 追加 `raw_data_root`、`file_registry_stack(tmp_path)`（ConnectionManager + WriteManager + FileRegistry + RawStore）。

---

### 8.1 FetchPort + SkeletonAdapterBase + FileRegistry

| 字段 | 值 |
|------|-----|
| 绑定 §12 | test-driven-development · source-driven-development |
| RED | `pytest tests/test_adapter_skeletons.py::test_skeletonAdapterBase_successWritesRawFile -v` → FAIL |
| GREEN | 同上 → PASS |
| RED 命令 | 同上 |
| GREEN 命令 | `pytest tests/test_adapter_skeletons.py::test_skeletonAdapterBase_successWritesRawFile tests/test_adapter_skeletons.py::test_skeletonAdapterBase_registersFileRegistryWhenInjected tests/test_adapter_skeletons.py::test_portErrors_mapStatusAndFetchLog -v` |
| 通过条件 | raw 文件存在；content_hash 一致；FileRegistry 行 local_path 对齐；parametrized port failures |
| 环境 | local · tmp_path |
| RED 证据 | exit 1 · `ModuleNotFoundError: fetch_port` |
| GREEN 证据 | exit 0 · 8 passed（3 tests × parametrized） |
| 已执行 | [x] |

| 字段 | 值 |
|------|-----|
| 绑定 §12 | test-driven-development |
| RED | `test_baostockAdapter_matchesRegistryDomains` FAIL |
| GREEN | PASS · `fundamental` domain |
| 环境 | local |
| RED/GREEN 证据 | RED ModuleNotFoundError baostock · GREEN exit 0 PASS fundamental |
| 已执行 | [x] |

| 字段 | 值 |
|------|-----|
| 绑定 §12 | test-driven-development |
| RED | `test_qmtAdapter_localClientMissing_returnsAuthFailed` FAIL |
| GREEN | AUTH 测 PASS + **`test_qmtAdapter_stubClient_successWritesRaw`** PASS |
| 环境 | local |
| RED/GREEN 证据 | RED ModuleNotFoundError qmt_xtdata · GREEN 2 passed AUTH+SUCCESS |
| 已执行 | [x] |

| 字段 | 值 |
|------|-----|
| 绑定 §12 | test-driven-development |
| RED | akshare/cninfo/unpublished 测试 FAIL |
| GREEN | PASS · AC-10 |
| 环境 | local |
| RED/GREEN 证据 | RED import fail · GREEN 4 passed（2 parametrize + unpublished） |
| 已执行 | [x] |

| 字段 | 值 |
|------|-----|
| 绑定 §12 | test-driven-development |
| RED | factory + validation_only + `create_adapter` default port FAIL |
| GREEN | PASS |
| 环境 | local |
| RED/GREEN 证据 | RED create_adapter missing · GREEN 3 passed |
| 已执行 | [x] |

| 字段 | 值 |
|------|-----|
| 绑定 §12 | incremental-implementation |
| GREEN 命令 | §10 全 Tier + GitNexus analyze |
| 通过条件 | 全绿；ci_ingestion_smoke ok；GitNexus 索引刷新 |
| 环境 | local + prod-path |
| GREEN 证据 | 200 passed · cov 93.72% · ruff 0 · compileall 0 · grep WriteManager 0 · init_db×2 ok · smoke ok · prod pytest 0 · GitNexus analyze 0 |
| 已执行 | [x] |

```powershell
pytest -q --cov=backend --cov-fail-under=75
ruff check .
python -m compileall backend scripts tests
if (Select-String -Path backend/app/datasources/adapters/* -Pattern 'WriteManager|write_manager' -Quiet) { exit 1 }
python scripts/init_db.py
python scripts/init_db.py
QMD_DATA_ROOT=data python scripts/ci_ingestion_smoke.py
$env:QMD_DATA_ROOT="data"; pytest -q
node .gitnexus/run.cjs analyze
npx @colbymchenry/codegraph sync
```

---

## 9. 测试层次

| 层次 | 命令 | 通过条件 | Execute 证据 |
|------|------|----------|--------------|
| 单元 | `pytest tests/test_adapter_skeletons.py -v` | 全绿 | exit 0 · 18 passed |
| 集成 | `pytest -q` | exit 0 | exit 0 · 200 passed |
| 管道 | `init_db` ×2 @ `data/` | 幂等 | applied none ×2 |
| smoke/E2E | `QMD_DATA_ROOT=data python scripts/ci_ingestion_smoke.py` | exit 0 · 004 两表 | ok tables fetch_log+source_registry |

---

## 10. 验收 Tier

| Tier | 环境 | 命令 | 通过条件 | Execute 勾 | Execute 证据 |
|------|------|------|----------|------------|--------------|
| A | ci/local | pytest+cov+ruff+compileall+grep | 全绿 | [x] | cov 93.72% · ruff 0 · grep 0 |
| B | prod-path | init_db×2 + **ci_ingestion_smoke** + prod raw 抽检（可选 ls data/raw） | 幂等 · smoke ok | [x] | init_db×2 · smoke ok |
| C | prod-path | `$env:QMD_DATA_ROOT='data'; pytest -q` | exit 0 | [x] | 200 passed |

---

## 11. Execute 交接

- [x] §8 RED/GREEN 证据非空
- [x] §9/§10 证据已填
- [x] `python .trellis/scripts/task.py detect_changes` 或 `detect_changes({scope: "compare", base_ref: "master"})` — 范围符合预期
- [x] `validate-execute-handoff` exit 0
- [x] §8.6 GitNexus 再索引完成
- [x] **交接 Audit**（勿 finish-work）

---

## 12. Execute Skill 冻结

| Skill | 本任务 | 绑定 §8 | 触发 | 已执行 |
|-------|--------|---------|------|--------|
| test-driven-development | 必做 | §8 每步 | 每步 | [x] |
| incremental-implementation | 必做 | §8.0–8.6 | 跨文件 | [x] |
| source-driven-development | 条件 | §8.1 RawStore/FileRegistry | 读 storage API | [x] |
| systematic-debugging | 条件 | RED 非预期 | pytest fail | [x] |
| trellis-implement | 必做 | Execute | 派发 | [x] |
| karpathy-guidelines | 必做 | 全程 | User Rule | [x] |
| testing-guidelines | 必做 | 测试 | User Rule | [x] |
| GitNexus impact | 必做 | 改 symbol 前 | impact() | [x] |

---

## 13. Batch A 延后偿还索引

| Batch A 项 | Batch B 处置 |
|------------|--------------|
| Beta §6 raw ↔ FileRegistry | **§8.1 AC-9 偿还** |
| GPT-NOT-PUBLISHED | **§8.4 AC-10 EMPTY_RESPONSE** |
| Batch A rule 2 真实 raw | **§8.1 RawStore** |
| P3-7 GitNexus 再索引 | **§8.6** |
| ci_ingestion_smoke 回归 | **§10 Tier B** |
| GPT-init_db / GPT-SEC-CI / staging / tombstone / ResourceGuard | **§3.2 defer** |

完整对抗审计表 → `research/adversarial-audit-remediation.md`
