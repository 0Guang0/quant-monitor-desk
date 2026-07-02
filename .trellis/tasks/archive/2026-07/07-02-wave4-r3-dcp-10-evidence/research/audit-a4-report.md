# Audit A4 — 代码质量 / mootdx provenance e2e

| 字段                  | 值                               |
| --------------------- | -------------------------------- |
| 维度                  | A4（audit-quality）              |
| 任务                  | 07-02-wave4-r3-dcp-10-evidence   |
| 分支                  | feature/wave4-r3-dcp-10-evidence |
| plan_protocol_version | 4.1                              |
| 日期                  | 2026-07-02                       |
| 模板                  | `agents/code-reviewer.md`        |

---

## 维度证据

### Boot / 对抗动作

- 已 Read：`agents/audit-adversarial-authority.md`、`agents/audit-boot-v4.1.md`、`agents/audit-finding-schema.md`、`AUDIT.plan.md`、`research/00-EXECUTION-ENTRY.md`、`research/to-issues-slices.md`、`frozen/R3_DCP_10_LAYER5_EVIDENCE_BINDING.md`、`docs/decisions/ADR-031-dcp10-layer5-evidence-provenance-binding.md`、`research/reference-adoption-dcp10.md` §4、`research/plan-doubt-review.md`、`research/integration-audit.md`。
- 已审 diff（工作区未提交）：`evidence_bundle.py`、`layer5_evidence/provenance.py`、`tests/test_layer5_provenance_bridge.py`、`tests/test_layer5_mootdx_bar_clean_e2e.py`。
- 已对照 AUDIT.plan §2 A4 要点：「mootdx bar clean e2e 可断言 provenance」。
- 已 Grep `bundle_layer5_provenance` / `build_source_provenance_from_bundle` 调用面；已读 `foundation.py` provenance 校验与 `conftest_layer_smoke.py` 既有 layer5 smoke 模式。

### 验证命令

```bash
uv run pytest tests/test_layer5_provenance_bridge.py tests/test_layer5_mootdx_bar_clean_e2e.py -q   # 4 passed
uv run pytest tests/test_cn_market_adapters.py::test_layer_cn_baostockReplay_layer5FactualSourceProvenance tests/test_layer5_evidence_foundation.py -q  # 7 passed
uv run pytest -q   # exit 0（全量，~6min）
```

### git diff 摘要

| 文件                                                     | 变更                                                                                                    |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `backend/app/datasources/normalizers/evidence_bundle.py` | `bundle_layer5_provenance` 增 `clean_table` 参数；`source_dataset_ids` 编码 schema/version/clean/domain |
| `backend/app/layer5_evidence/provenance.py`              | 新增 `build_source_provenance_from_bundle`；fetch_id/content_hash fail-closed                           |
| `tests/test_layer5_provenance_bridge.py`                 | S01 三用例：ADR-031 映射、foundation 校验、缺 fetch_id 负向                                             |
| `tests/test_layer5_mootdx_bar_clean_e2e.py`              | S02 e2e：incremental → raw bundle → provenance → foundation + lineage                                   |

### 五轴审查

| 轴           | 评估                       | 要点                                                                                                                                                                              |
| ------------ | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **正确性**   | 良（桥接）/ 中（e2e 断言） | S01 单元测完整覆盖 ADR-031 dataset id 编码；S02 e2e 仅断言 `source_fetch_ids`/`source_content_hashes` 与 bundle 一致，**未**断言 `schema_hash`→`source_dataset_ids`（见 finding） |
| **错误处理** | 良 / 有缺口                | `build_source_provenance_from_bundle` 对空 fetch_id/content_hash 抛 `ValueError`；仅 fetch_id 有单测，content_hash 负向缺失                                                       |
| **可读性**   | 良                         | `provenance.py` 薄桥接；测试五字段 docstring 齐全；e2e 复用 `incremental_mootdx_support`                                                                                          |
| **架构**     | 良（ponytail）             | 扩展共享 `bundle_layer5_provenance` 而非新 dataclass；Layer5 读 bundle 尾段，符合 ADR-031 / reference-adoption                                                                    |
| **安全**     | 可接受                     | 无密钥；`tmp_path` 隔离；ResourceGuard monkeypatch 与 DCP-05 e2e 同模式                                                                                                           |

### §3.4 轴表

| 轴       | 发现                                        | 证据                                                                  |
| -------- | ------------------------------------------- | --------------------------------------------------------------------- |
| 正确性   | e2e 未断言 schema_hash / source_dataset_ids | `tests/test_layer5_mootdx_bar_clean_e2e.py` L84–85                    |
| 错误处理 | content_hash 缺失无单测                     | `provenance.py` L21–22；`test_layer5_provenance_bridge.py` 仅 L84–101 |
| 可读性   | —                                           | —                                                                     |
| 架构     | raw bundle 选取 `candidates[-1]` 无过滤     | `test_layer5_mootdx_bar_clean_e2e.py` L32–38                          |
| 安全     | —                                           | —                                                                     |

### 做得好的地方

- `build_source_provenance_from_bundle` 极简（ponytail），fail-closed 对齐 digital-oracle 纪律。
- S01 对 ADR-031 四段 `source_dataset_ids` 有逐字段断言，且经 `EvidenceFoundationValidator` 校验。
- S02 证明同 run incremental 的 raw bundle 与 Layer5 lineage envelope 三字段对齐；拒绝 `fetch-staged-001`。
- `bundle_layer5_provenance` 向后兼容：既有 adapter layer5 smoke（cn_market 等）全绿。

### DOUBT 对抗搜索

已搜索：`tests/test_layer5_*`、`evidence_bundle.py`、`layer5_evidence/provenance.py`、`foundation.py`、`conftest_layer_smoke.py`、`to-issues-slices.md` S02 AC、`reference-adoption-dcp10.md` §4 hash 纪律、`plan-doubt-review.md` Cycle 2。

---

## §维度裁决

**FAIL**

（§计划内 2 条 + §计划外 2 条非占位 finding）

---

## 计划内问题

| ID       | P   | 标题                                        | 锚点                                                                                                                                          | 根因                                                                                                  | 修复方案                                                                                                                                                                                                                | 验证                                                         |
| -------- | --- | ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| A4-P2-01 | P2  | e2e 未断言 schema_hash / source_dataset_ids | `tests/test_layer5_mootdx_bar_clean_e2e.py` L84–85；`to-issues-slices.md` S02 AC「source_fetch_id + content_hash + schema_hash match bundle」 | S02 e2e 只比对 fetch_id/content_hash，ADR-031 第三锚 schema_hash 编码未在同 run 路径复验              | 在 e2e 中增加：`schema_hash = bundle["schema_hash"]`；`assert f"schema:{schema_hash}@{bundle['schema_version']}" in provenance.source_dataset_ids`；并断言 `clean:`/`domain:` 条目与 bundle 一致（可复用 S01 断言模式） | `uv run pytest tests/test_layer5_mootdx_bar_clean_e2e.py -q` |
| A4-P2-02 | P2  | 缺 content_hash fail-closed 单测            | `backend/app/layer5_evidence/provenance.py` L21–22；`tests/test_layer5_provenance_bridge.py`（无对称用例）                                    | S01 仅测空 `source_fetch_id`；`reference-adoption-dcp10.md` §2.2 要求 hash 必填，缺测则回归可静默退化 | 新增 `test_layer5Provenance_missingContentHash_raises`：finalize bundle 含 fetch_id 但 `content_hash=""` → `pytest.raises(ValueError, match="content_hash")`                                                            | `uv run pytest tests/test_layer5_provenance_bridge.py -q`    |

---

## 计划外发现

| ID       | P   | 标题                                   | 锚点                                                                                       | 根因                                                                                                           | 修复方案                                                                                                                                                                             | 验证                                                                                                 |
| -------- | --- | -------------------------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| A4-P2-03 | P2  | raw bundle 选取逻辑脆弱                | `tests/test_layer5_mootdx_bar_clean_e2e.py` L32–38 `_load_raw_bundle_from_incremental_run` | `sorted(glob(...))[-1]` 在同日多 instrument/多 bundle 时可能绑错 provenance，e2e 静默通过但证据链错位          | 按 `source_id=mootdx` + `data_domain=cn_equity_daily_bar` 过滤；或 glob 后断言 `len(candidates)==1`；或读 bundle 内 `bars[0].instrument_id == SYMBOL` 再选用                         | `uv run pytest tests/test_layer5_mootdx_bar_clean_e2e.py -q`                                         |
| A4-P3-01 | P3  | bundle 缺 schema_version 默认 macro 版 | `backend/app/datasources/normalizers/evidence_bundle.py` L109–110                          | 未 finalize 的 bundle 缺 `schema_version` 时被标为 `official_macro_evidence_v1`，`source_dataset_ids` 跨域误标 | ponytail：缺 `schema_version` 时不写入 schema/version dataset id（或要求调用方先 `finalize_bundle` 并在 docstring 注明）；加单测：无 schema_version 的 dict 不应产出 macro schema id | `uv run pytest tests/test_layer5_provenance_bridge.py tests/test_cn_market_adapters.py -k layer5 -q` |

已对抗搜索：`tests/test_layer5_*`、`backend/app/layer5_evidence/`、`backend/app/datasources/normalizers/evidence_bundle.py`、`tests/conftest_layer_smoke.py`、`research/reference-adoption-dcp10.md`、`research/plan-doubt-review.md` Cycle 2、`tests/incremental_mootdx_support.py`、DCP-05 `test_mootdx_incremental_e2e.py` 对照。

---

## Verification Story

| 项               | 结果                                            |
| ---------------- | ----------------------------------------------- |
| 测试 reviewed    | 是 — S01/S02 全文 + foundation/lineage 触点     |
| pytest 复跑      | 是 — 任务测 4/4；全量 `uv run pytest -q` exit 0 |
| Security checked | 是 — 无密钥；tmp_path 隔离                      |
| Build verified   | 否 — 未跑 loop_maintain / 独立 build            |
