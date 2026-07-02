# Audit A7 — tmp_path 隔离 / 主库零污染（R3-DCP-10）

| 元信息   | 值                                 |
| -------- | ---------------------------------- |
| 维度     | A7 隔离库 / 无生产 DuckDB 写       |
| 任务     | `07-02-wave4-r3-dcp-10-evidence`   |
| 协议     | `plan_protocol_version: 4.1`       |
| 模板     | `agents/database-administrator.md` |
| 审计日期 | 2026-07-02                         |

---

## 维度证据 §3.7

### 0. 审计范围（AUDIT.plan §2 · EXECUTION_INDEX §2 AC）

| 路径                                                     | 角色                                                |
| -------------------------------------------------------- | --------------------------------------------------- |
| `tests/test_layer5_provenance_bridge.py`                 | S01 — bundle → SourceProvenance 映射（无 DB）       |
| `tests/test_layer5_mootdx_bar_clean_e2e.py`              | S02 — mootdx replay → clean → Layer5 provenance e2e |
| `tests/incremental_mootdx_support.py`                    | 共享 `bootstrap_db` / `build_service`               |
| `backend/app/layer5_evidence/provenance.py`              | S01 provenance bridge（纯 dict 映射）               |
| `backend/app/datasources/normalizers/evidence_bundle.py` | `bundle_layer5_provenance` 扩展                     |
| `tests/test_layer5_evidence_foundation.py`               | 回归 — foundation / lineage 单测                    |
| `tests/test_layer5_evidence_chain.py`                    | 回归 — staged 证据链                                |
| `tests/test_mootdx_incremental_e2e.py`                   | 回归 — DCP-05 mootdx 增量基线                       |

**计划内 AC：** AUDIT.plan §2 A7 = `tmp_path` 隔离；`to-issues-slices.md` §垂直切片规则 4：默认 replay，live 须 env-gate + 隔离库（**非本票 AC**）。

### 1. Grep：`ConnectionManager` · `DATA_ROOT` · `duckdb` · `quant_monitor` · `QMD_DATA_ROOT`

| 文件                                                     | 命中                                                                      | 判定                                                                     |
| -------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `tests/test_layer5_provenance_bridge.py`                 | **0**                                                                     | 只读 `PROJECT_ROOT/tests/fixtures/replay/.../mootdx_daily_replay.json`   |
| `tests/test_layer5_mootdx_bar_clean_e2e.py`              | `tmp_path` ×3；经 `bootstrap_db(tmp_path)`                                | 显式 sandbox                                                             |
| `tests/test_layer5_evidence_foundation.py`               | **0**                                                                     | 纯内存 dataclass / validator                                             |
| `tests/test_layer5_evidence_chain.py`                    | **0**                                                                     | `tests/fixtures/layer5_staged_evidence/*.json` + `_FakeEvidenceReadPort` |
| `tests/incremental_mootdx_support.py`                    | `ConnectionManager(db_path=tmp_path/"mootdx_incr.duckdb")`                | 无默认路径                                                               |
| `backend/app/layer5_evidence/*`（含 `provenance.py`）    | **0**                                                                     | 不 import DB / storage                                                   |
| `backend/app/datasources/normalizers/evidence_bundle.py` | **0**                                                                     | 纯 bundle 哈希与 provenance 字段提取                                     |
| layer5 相关测全范围                                      | **0** 条 `quant_monitor.duckdb` / `data/duckdb/` / `QMD_DATA_ROOT` 硬编码 | —                                                                        |

### 2. `bootstrap_db` 写面追溯

```text
tmp_path/mootdx_incr.duckdb              ← apply_migrations + incremental upsert（security_bar_1d）
tmp_path/mootdx_incr.duckdb.write.lock   ← ConnectionManager 写锁
tmp_path/raw/raw/*/cn_equity_daily_bar/  ← 同 run fetch bundle JSON（S02 读 provenance）
```

- `build_service(cm, raw_root)` 将 `DataSourceService.data_root` 绑定调用方传入的 `tmp_path/raw`，非 `DATA_ROOT`。
- `create_mootdx_fetch_port(..., use_mock=True)` — replay fixture，无真网写面。
- S02 中 Layer5 `EvidenceFoundationValidator` / `Layer5LineageBuilder` 仅在内存构造 record/envelope，**不**持久化 DuckDB。

### 3. `tmp_path` 覆盖率（DB / 文件写触达）

| 模块                                  |   测数 | 需 DB/写 | `tmp_path` 或等价隔离 | 无 DB 测说明                |
| ------------------------------------- | -----: | -------: | --------------------: | --------------------------- |
| `test_layer5_provenance_bridge.py`    |      3 |        0 |                     — | 只读 replay fixture         |
| `test_layer5_mootdx_bar_clean_e2e.py` |      1 |        1 |                   1/1 | —                           |
| `test_layer5_evidence_foundation.py`  |      6 |        0 |                     — | 内存 validator / lineage    |
| `test_layer5_evidence_chain.py`       |      7 |        0 |                     — | staged JSON + fake port     |
| `test_mootdx_incremental_e2e.py`      |      5 |        5 |                   5/5 | 回归基线，同 `bootstrap_db` |
| **合计**                              | **22** |    **6** |               **6/6** | 16 测无 DB 触达             |

### 4. Layer5 生产路径 — 无默认 `ConnectionManager`

| 检查项                                                                               | 结果                                         |
| ------------------------------------------------------------------------------------ | -------------------------------------------- |
| `layer5_evidence/provenance.py` import `ConnectionManager` / `duckdb` / `DATA_ROOT`  | 否                                           |
| `bundle_layer5_provenance` / `build_source_provenance_from_bundle` 打开 DB           | 否（dict in → dataclass out）                |
| `EvidenceFoundationValidator` / `Layer5LineageBuilder` 生产 fallback 到 canonical DB | 否                                           |
| `EvidenceReadPort` 契约                                                              | builder 经 port 注入，不 import 具体 storage |

### 5. GitNexus 追溯

| 调用                                                                                              | 结果                                                                                                                                        | 用于 A7 的结论                                       |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `query({search_query: "layer5 evidence provenance mootdx tmp_path", repo: "quant-monitor-desk"})` | 返回 `layer5_evidence/foundation.py`、`lineage.py`、`test_layer5_evidence_foundation.py` 等定义；**无** layer5 → `ConnectionManager` 执行流 | Layer5 校验/血缘与 DB 写路径解耦                     |
| `query({search_query: "build_source_provenance_from_bundle bundle_layer5_provenance", ...})`      | 命中 `layer5_evidence` 定义；未编入独立 process                                                                                             | S01 桥接为纯映射，非 DB hot path                     |
| `context({name: "ConnectionManager", repo: "quant-monitor-desk"})`                                | 确认 `writer()`/`reader()` 经 `_apply_pragmas`；incoming 含 `scripts/init_db.py`、sync/orchestrator 等                                      | DCP-10 测均显式 `db_path=tmp_path/...`，不经默认构造 |
| `impact({target: "ConnectionManager", direction: "upstream"})`                                    | risk=**HIGH**，43 上游符号                                                                                                                  | 横切基础设施；本票测路径已注入隔离 `db_path`         |
| `context({name: "bundle_layer5_provenance"})` / `build_source_provenance_from_bundle`             | **索引未收录**（DCP-10 新符号）                                                                                                             | 以 grep + 源码 Read 复验：无 DB 依赖                 |

### 6. 独立复跑

```text
uv run pytest \
  tests/test_layer5_provenance_bridge.py \
  tests/test_layer5_mootdx_bar_clean_e2e.py \
  tests/test_layer5_evidence_foundation.py \
  tests/test_layer5_evidence_chain.py \
  tests/test_mootdx_incremental_e2e.py -q
```

| exit | 结果      |
| ---: | --------- |
|    0 | 22 passed |

### 7. 基础设施观察（非 DCP-10 引入 · 不进 findings）

`ConnectionManager._apply_pragmas` 在 `writer()`/`reader()` 时可能对 `DATA_ROOT/cache/duckdb_tmp` 执行 `mkdir`（DuckDB spill）；**不**打开 `quant_monitor.duckdb`。本票全部 DuckDB 数据与 migration 落在 `tmp_path/mootdx_incr.duckdb`；与 DCP-05/DCP-06 e2e 同型。全文件系统沙箱化属 `ConnectionManager` 横切升级，非本票 AC。

---

## §维度裁决

**PASS**

---

## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：DCP-10 全 8 文件路径 + `tests/incremental_mootdx_support.py` 的 `ConnectionManager|DATA_ROOT|duckdb|quant_monitor|QMD_DATA_ROOT`；`backend/app/layer5_evidence/` 全包 import 面；`ConnectionManager._apply_pragmas` DATA_ROOT cache 侧效应；`to-issues-slices.md` live/隔离库边界；GitNexus `query`/`context`/`impact` 对 Layer5 与 ConnectionManager；S02 raw bundle glob 仅读 `tmp_path/raw`；`plan-boot.md` ADR-027 replay 默认策略。
