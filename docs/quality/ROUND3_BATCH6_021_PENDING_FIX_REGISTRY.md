# Round 3 Batch 6 — 021 Layer3 Snapshot 待偿还清单（追加登记）

> **Authority:** 021 主会话对抗性复核（2026-06-24）残余风险；**不阻塞** 021/022 staged 闭环（均已合并 `master`）。  
> **配对文档:** `docs/AUDIT_DEFERRED_REGISTRY.md` · `docs/UNRESOLVED_ISSUES_REGISTRY.md` · `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §Batch 6  
> **基准:** `master` @ `d49e21d3` · 2026-06-24

---

## 待偿还 — Batch 6 owner

| ID             | 问题                                                                                                                                                      | 清理阶段    | 任务挂钩                                                                                             | 关闭条件                                                                                              |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| R3-B6-021-O-01 | `_bar_for_trade_date` 对 `bars[]` 中非 mapping 元素 `continue` 跳过，未在 schema 层 fail-closed                                                           | **Batch 6** | `layer3 build-snapshot` CLI · `snapshot_builder.py` · `docs/modules/layer3_industry_shock_anchor.md` | manifest/bar schema 校验拒绝非法元素 + pytest（如 `test_layer3Snapshot_malformedBarElement_rejects`） |
| R3-B6-021-O-02 | `test_layer3Snapshot_deterministicRebuild_sameInputsSameHash` 仅断言 `parameter_hash` 与 `latest_price`，未覆盖完整 `IndustryChainDailySnapshotRow` tuple | **Batch 6** | `tests/test_layer3_snapshot_builder.py` · A8 G7                                                      | 同输入两次 `build()` 对全 row 字段（及约定 lineage 字段）相等或 frozen hash 一致                      |

**来源证据:** `.trellis/tasks/06-24-round3-021-layer3-snapshot/research/main-session-adversarial-recheck-021.md`
