# GitNexus 代码库分析 — Round 2 Batch B（013 adapter skeletons）

> **Phase 1** · 工具：GitNexus MCP `query` + `context` · 2026-06-17

---

## 1. 任务触点

| 符号 / 模块 | 路径 | Batch B 关系 |
|-------------|------|--------------|
| `BaseDataAdapter` | `backend/app/datasources/base_adapter.py` | 五类 skeleton **必须**继承；`fetch()` 模板方法已冻结 |
| `FetchRequest` / `FetchResult` | `fetch_result.py` | Pydantic v2 契约；SUCCESS 需 raw/staging 证据 |
| `SourceRegistry` | `source_registry.py` | 五源 `source_id` 与 `allowed_domains` 对齐 YAML |
| `FetchLogWriter` | `fetch_log.py` | skeleton 经 `BaseDataAdapter.fetch` 自动落库 |
| `RawStore` | `backend/app/storage/raw_store.py` | Batch B **落地** contract rule 2：真实 raw 文件 |
| `FileRegistry` | `backend/app/storage/file_registry.py` | 经 WriteManager；**本批不强制** adapter 注册（Batch C/D） |
| 测试基线 | `tests/test_data_adapter_contract.py` | FakeAdapter 模式；Batch B 新增 `test_adapter_skeletons.py` |

## 2. 调用图（GitNexus context · BaseDataAdapter）

**子类（测试）：** FakeAdapter、ExplodingAdapter、WrongSourceAdapter、NarrowDomainAdapter、EmptyAdapter — 均在 contract 测试内。

**Batch B 将新增：** `backend/app/datasources/adapters/*` 五个 vendor 类 + factory。

**上游：** 无 HTTP/API 路由；Batch D Orchestrator 将调用 factory（§8.6 冻结 `create_adapter`）。

## 3. 五源 registry 对照（`source_registry.yaml`）

| source_id | 类名（计划） | supported_domains | 特殊 |
|-----------|-------------|-------------------|------|
| `qmt_xtdata` | `QmtXtdataAdapter` | market_bar_1m, market_bar_1d | `requires_local_client` → AUTH_FAILED 路径 |
| `baostock` | `BaostockAdapter` | market_bar_1d, fundamental | Primary @ market_bar_1d |
| `akshare` | `AkshareAdapter` | market_bar_1d, capital_flow | vendor_api stub |
| `cninfo` | `CninfoAdapter` | announcement | `NOT_PUBLISHED_YET` 可选态 |
| `yahoo_finance` | `YahooFinanceAdapter` | market_bar_1d | `validation_only=true` |

## 4. 风险与约束

1. **禁止** adapter 内 import WriteManager / 写 clean 表。
2. **禁止** 真实 HTTP/SDK 联网；外部 I/O 经 `FetchPort` 协议注入 mock。
3. **必须** SUCCESS 路径写 `RawStore` 真实文件（非仅字段占位）。
4. Batch A 基线 **182** tests @ `ab8d1eb`；Batch B 增量须保持 `pytest -q` 全绿 + cov ≥75%。
5. 路径归一：`backend/app/datasources/adapters/`（非任务文件字面量 `backend/sources/`）。

## 5. 建议 §8 切片顺序

```text
8.0 stubs + conftest(raw_store) + collect-only
8.1 FetchPort + SkeletonAdapterBase + RawStore 集成
8.2 BaostockAdapter（垂直切片）
8.3 QmtXtdataAdapter（local client / AUTH）
8.4 Akshare + Cninfo
8.5 Yahoo + factory
8.6 回归 + prod-path
```

## 6. GitNexus 查询记录

- `query`: "adapter skeleton datasources BaseDataAdapter fetch implementation"
- `context`: `BaseDataAdapter` — 5 test subclasses，无 production adapter  yet
