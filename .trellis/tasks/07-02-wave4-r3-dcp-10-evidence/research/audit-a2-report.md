# Audit A2 — Ponytail（R3-DCP-10 Layer5 证据绑真源）

> **维：** A2 ponytail-review  
> **协议：** plan_protocol_version 4.1  
> **模板：** `agents/audit-a2-ponytail.md`  
> **日期：** 2026-07-02  
> **diff 基线：** 工作区变更（`feature/wave4-r3-dcp-10-evidence` · 含未提交 Execute 产出）

---

## 维度证据 §3.2

### Boot / diff 记录

| 项                                | 证据                                                                                                                                                                                                                                                                                          |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `git diff --stat`（已跟踪）       | 5 files · +367 / −473（`test_catalog.yaml` loop 重排占大头）                                                                                                                                                                                                                                  |
| `git diff --numstat`（生产+契约） | `evidence_bundle.py` +20/−2 · 台账/roadmap 各 +2/−2                                                                                                                                                                                                                                           |
| 未跟踪 Execute 产出               | `provenance.py`（29 LOC）· `test_layer5_provenance_bridge.py`（102 LOC）· `test_layer5_mootdx_bar_clean_e2e.py`（130 LOC）· ADR-031                                                                                                                                                           |
| **代码净增合计（本票逻辑）**      | ~281 LOC（bridge + 两测模块 + bundle 扩展）                                                                                                                                                                                                                                                   |
| S01 触及                          | `evidence_bundle.py:99-125` · `layer5_evidence/provenance.py` · `test_layer5_provenance_bridge.py`                                                                                                                                                                                            |
| S02 触及                          | `test_layer5_mootdx_bar_clean_e2e.py` · 复用 `tests/incremental_mootdx_support.py`                                                                                                                                                                                                            |
| S03 触及                          | `docs/quality/待修复清单.md` · `PROJECT_IMPLEMENTATION_ROADMAP.md`（G5 子集关账措辞）                                                                                                                                                                                                         |
| DOUBT 搜索范围                    | `backend/app/layer5_evidence/provenance.py` · `backend/app/datasources/normalizers/evidence_bundle.py` · `tests/test_layer5_*.py` · `tests/incremental_mootdx_support.py` · 对照 `tests/test_mootdx_incremental_e2e.py` · `tests/conftest_layer_smoke.py` · `cn_market.py` 既有 layer5 helper |

### ponytail 注释核对

| 锚点                                                       | 状态                                                                |
| ---------------------------------------------------------- | ------------------------------------------------------------------- |
| ADR-031 §Alternatives `schema_hash` → `source_dataset_ids` | 有意简化；不扩 `SourceProvenance` dataclass                         |
| `provenance.py`                                            | 无 `ponytail:` 注释；29 LOC 单函数桥，无 class 包装                 |
| `bundle_layer5_provenance` dataset id 列表                 | ADR-031 / `reference-adoption-dcp10.md` §4 显式 AC — **不算 bloat** |

### 候选删改（file:line · ponytail 梯级）

| 候选删改                                                                                                         | ponytail 梯级                               | 备注                                                                      |
| ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------- |
| `test_layer5_mootdx_bar_clean_e2e.py:51-77` 与 `test_mootdx_incremental_e2e.py:36-63` 重复 incremental bootstrap | 梯级 2（复用 `incremental_mootdx_support`） | ~27 LOC 同形；见 A2-P2-001                                                |
| `layer5_evidence/provenance.py` 全文（29 LOC）                                                                   | —（计划内 AC）                              | ADR-031 + S01 明确要求 bridge 模块；dict→`SourceProvenance` + fail-closed |
| `evidence_bundle.py:99-125` `bundle_layer5_provenance` 扩展 (+18 net)                                            | —（计划内 AC）                              | ADR-031 schema/domain/clean dataset id 编码                               |
| `test_layer5_provenance_bridge.py` 三测（102 LOC）                                                               | —（切片设计）                               | S01 tracer-bullet；各测独立五字段 purpose                                 |
| `_load_raw_bundle_from_incremental_run` 单调用                                                                   | 梯级 2                                      | ~8 LOC — **不计 ≥20 行 finding**                                          |
| `cn_market_bundle_layer5_provenance` vs `build_source_provenance_from_bundle`                                    | 梯级 2                                      | 前者返回 dict smoke；后者 Layer5 包 QMD 桥 — 分层正确                     |
| `conftest_layer_smoke.assert_layer5_factual_source_record` 未含 `source_dataset_ids`                             | —                                           | S01 需 ADR-031 四段 dataset id 断言；旧 helper 不适用                     |

### A4 交叉引用

- `provenance.py` 内 `ValueError`（缺 fetch_id/content_hash）与 `cn_market.py:200` read fail-closed **语义重叠**但触面不同（任意 bundle dict vs CN read 路径）；A4 可评错误模型一致性，A2 不重复开项。
- `bundle_layer5_provenance` 扩展无额外 wrapper/factory 层。

### Checklist

- [x] `git diff --stat` 已记录 Lxx / net lines
- [x] 每候选附 `file:line` + ponytail 梯级
- [x] A4 交叉引用（fail-closed 重叠已标注）
- [x] 阻塞 vs 建议已区分（本维仅 P2 建议删改，无 P0/P1 过度工程）

---

## §维度裁决

**FAIL**

（§计划内 1 条非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                                                      | 锚点                                                                                                                                          | 根因                                                                                                                                                                                                                                                                        | 修复方案                                                                                                                                                                                                                                                                                                                                          | 验证                                                                                                                                                                                                 |
| --------- | --- | --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A2-P2-001 | P2  | S02 e2e 重复 mootdx incremental bootstrap 未进共享 helper | `tests/test_layer5_mootdx_bar_clean_e2e.py:51-77` · 对照 `tests/test_mootdx_incremental_e2e.py:36-63` · `tests/incremental_mootdx_support.py` | DCP-05 S08 已建 `incremental_mootdx_support`（`bootstrap_db`/`seed_watermark_row`/`build_service`/`incremental_spec`），但 S02 仍内联 ~27 行 ResourceGuard monkeypatch + watermark 窗 + `run_incremental` + clean 行查询，与 DCP-05 e2e 首测同形，违反 ponytail 梯级 2 复用 | 在 `incremental_mootdx_support.py` 增加 `run_mootdx_replay_incremental(tmp_path, monkeypatch, *, job_id, seed_date="2024-06-24") -> tuple[ConnectionManager, Path, SyncResult]`（可选同文件 `fetch_security_bar_row(con, trade_date)`）；`test_layer5_mootdx_bar_clean_e2e.py` 与 `test_mootdx_incremental_e2e.py` 首测（及同形用例）改调共享函数 | `uv run pytest tests/test_layer5_mootdx_bar_clean_e2e.py tests/test_mootdx_incremental_e2e.py -q`；`rg "seed_watermark_row\(con, \"2024-06-24\"\)" tests/test_layer5_mootdx_bar_clean_e2e.py` 无命中 |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`backend/app/layer5_evidence/provenance.py` · `evidence_bundle.py` · 全部 `tests/test_layer5_*.py` · `incremental_mootdx_support.py` · `test_mootdx_incremental_e2e.py` · `conftest_layer_smoke.py` · `cn_market.py` layer5 helper · ADR-031 / `reference-adoption-dcp10.md` §4 映射表。除 §计划内 incremental bootstrap 重复外，未发现净增 ≥20 行且可删的单消费者 wrapper、计划外重复错误处理样板，或未请求抽象。`test_catalog.yaml` 大 diff 为 loop 登记重排，非 Execute 逻辑膨胀。

---

## Verification Story

- **Tests reviewed:** yes — S01 三测五字段 docstring 对齐 ADR-031；S02 e2e 覆盖 fetch→clean→Layer5 provenance + lineage 对齐
- **Build verified:** yes — `uv run pytest tests/test_layer5_provenance_bridge.py tests/test_layer5_mootdx_bar_clean_e2e.py -q` exit 0（4 passed）
- **Security checked:** yes（A2 范围）— 无参考项目 runtime import；无 WriteManager bypass；bridge 仅读 bundle 字段

### What's Done Well

- **最小 bridge 模块**：`provenance.py` 29 LOC 单函数，无 class/factory；ADR-031 拒绝扩 dataclass 的 ponytail 决策已落地（`schema_hash` → `source_dataset_ids`）。
- **SSOT 扩展而非分叉**：`bundle_layer5_provenance` _additive_ 扩展 dataset id 编码，复用既有 `schema_hash_for_version`；domain normalizer 仍一行转发。
- **切片测粒度合理**：S01 单测与 S02 e2e 职责分离；fail-closed 负向测保留独立 purpose。
- **fixtures 复用**：S01/S02 共用 `MOOTDX_REPLAY` / `incremental_mootdx_support.SYMBOL` / `FIXTURE_DATE`，与 DCP-05 P0 竖切一致。
