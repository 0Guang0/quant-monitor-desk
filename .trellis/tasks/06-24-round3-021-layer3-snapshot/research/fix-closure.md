# Phase 7 Re-audit Fix Closure — 021 Layer3 Snapshot Builder

**分支：** `feature/round3-021-layer3-snapshot`  
**基线：** `fdf5d4e8`（Execute + partial Phase 7 fix）  
**收口日期：** 2026-06-24

---

## A8 — test-gap

| ID  | 严重度   | 处置                     | 证据                                                                                                    |
| --- | -------- | ------------------------ | ------------------------------------------------------------------------------------------------------- |
| G1  | BLOCKING | **已闭合**（`fdf5d4e8`） | `test_layer3Snapshot_tradeDateMismatch_rejects`                                                         |
| G2  | NB       | **已闭合**（`fdf5d4e8`） | `test_layer3Snapshot_missingManifestHashes_rejects`                                                     |
| G3  | NB       | **已闭合**               | `test_layer3Snapshot_missingManifestFetchIds_rejects`                                                   |
| G4  | NB       | **已闭合**               | `test_layer3Snapshot_missingL5Manifest_rejects`                                                         |
| G5  | NB       | **已闭合**               | `test_layer3Snapshot_invalidManifestYaml_rejects`                                                       |
| G6  | NB       | **已闭合**               | `test_snapshotLineage_agentOutputsNotSource_rejectsAgentProse`                                          |
| G7  | NB       | **已闭合**               | `test_layer3Snapshot_deterministicRebuild_sameInputsSameHash`                                           |
| G8  | NB       | **已闭合**               | 全部 22 条 `test_*` 含四元组（覆盖/对象/目的/验证点/失败含义）                                          |
| G9  | NB       | **defer**                | event_only 误有价负向价值低；代码 `event_only` 分支不读 L5 bar，已有正向测 `eventOnly_skipsPriceFields` |

---

## A4 — code-reviewer

| ID          | 处置                     | 证据                                                                                                         |
| ----------- | ------------------------ | ------------------------------------------------------------------------------------------------------------ |
| D-1 / OOF-1 | **document + ponytail**  | `snapshot_builder.py` event_only 分支注释：fetch/hash 取自 staged manifest 全局；升级路径 022+ anchor 级指纹 |
| D-2 / OOF-2 | **已闭合**（`fdf5d4e8`） | `_bar_for_trade_date` 必填字段 guard + `test_layer3Snapshot_missingBarField_rejects`                         |
| D-3 / OOF-3 | **已闭合**（`fdf5d4e8`） | `_parse_ts` tz-aware guard + 单元/集成测                                                                     |
| OOF-4       | **defer**                | `price_proxy_needs_feed` — MASTER §3.2 Batch 5+；loader 已识别状态                                           |
| OOF-5       | **defer**                | `pct_change_1d` 恒 None — fixture 单日 bar 无 prev close；设计 §8.12.6 staged 子集                           |
| OOF-6       | **已闭合**               | 核心文件纳入 commit（见 NB-1）                                                                               |
| OOF-7       | **已闭合**               | `_parse_bar_close` → `Layer3SnapshotError` + `test_layer3Snapshot_nonNumericClose_rejects`                   |

---

## A1 — audit-spec

| ID   | 处置       | 证据                                                                |
| ---- | ---------- | ------------------------------------------------------------------- |
| NB-1 | **已闭合** | `snapshot_builder.py` / `lineage.py` / fixture 已 tracked 并 commit |
| NB-2 | **已闭合** | `node .gitnexus/run.cjs analyze` exit 0（9097 nodes）               |

---

## A3 — security

| ID   | 处置                 | 证据                                                                                                     |
| ---- | -------------------- | -------------------------------------------------------------------------------------------------------- |
| UF-1 | **已闭合**           | `_resolve_l5_bundle_root` PROJECT_ROOT 白名单 + `test_layer3Snapshot_l5BundleOutsideProjectRoot_rejects` |
| UF-2 | **defer + ponytail** | `_read_l5_manifest` 注释：本地 ops 可含路径；HTTP/CLI 切片须 redact                                      |
| UF-3 | **defer + ponytail** | `_read_l5_manifest` 注释：无 max_bytes；staged_fixture_only 信任边界                                     |
| UF-4 | **已闭合**           | 同 G6                                                                                                    |
| UF-5 | **已闭合**           | 同 NB-1                                                                                                  |
| UF-6 | **已闭合**           | 同 NB-2                                                                                                  |

---

## A6 — performance (SKIP 维持)

| ID   | 处置                 | 证据                                                                       |
| ---- | -------------------- | -------------------------------------------------------------------------- |
| NB-1 | **defer + ponytail** | `build()` 注释：021 无 ResourceGuard；Batch 6 CLI / live ingest 须挂 guard |
| NB-2 | **defer + ponytail** | `_bar_for_trade_date` 注释：O(bars) 线性扫；生产化加索引或 max_bars cap    |
| NB-3 | **defer + ponytail** | 模块头注释：每次 build 重读 manifest；Batch 6 批量重建可 memoize           |

**A6 判定维持 SKIP** — 无 hot path / 无冻结 perf 阈值；结构性备忘已 ponytail 标注升级路径。

---

## 验证

| 命令                                                     | 结果           |
| -------------------------------------------------------- | -------------- |
| `uv run pytest tests/test_layer3_snapshot_builder.py -q` | 22 passed      |
| `uv run pytest -q`                                       | exit 0（全量） |
| `node .gitnexus/run.cjs analyze`                         | exit 0         |

---

## Ponytail 自检

1. **YAGNI** — 未加 ResourceGuard stub、bar 索引、manifest 缓存；仅 UF-1/OOF-7 等廉价共享 guard。
2. **复用** — `_parse_bar_close`、`_resolve_l5_bundle_root` 单点；lineage 仍薄封装 L2 模式。
3. **无新依赖** — 仅 stdlib + 既有 yaml/config。
4. **最小 diff** — 测试 mutation 改 copy 至 `.audit-sandbox/layer3_l5_mutations/` 以兼容 UF-1。
5. **天花板已标注** — event_only provenance、YAML 体积、线性 bar 扫、manifest 重读、路径 redaction 均有 `ponytail:` 注释与本文 defer 行。
