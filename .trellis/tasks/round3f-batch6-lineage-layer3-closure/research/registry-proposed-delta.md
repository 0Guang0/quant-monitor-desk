# Registry Proposed Delta — B3F-LIN (主会话批处理草案)

> **禁止** 本分支直接 commit 三件套 RESOLVED 行。主会话 + B3F-REG 合并后批处理。

**分支：** `fix/round3f-batch6-lineage-layer3-registry-closure`  
**基线：** `master` @ `7f628c9`  
**3D.3 说明：** B01-LIN（`06bcfde1`）仅 **partial hygiene**；下列四项 **registry 全闭合** 归本分支证据 + 主会话。

---

## PROPOSED — `R3-B6-021-O-01`

| 字段 | 值 |
|------|-----|
| 当前状态 | DEFERRED |
| **PROPOSED** | **RESOLVED** |
| 证据 | `test_layer3Snapshot_malformedBarElement_rejects` · `test_b3fLin_r3fL301_malformedBarElement_failClosed` · `snapshot_builder._bar_for_trade_date` fail-closed on non-dict `bars[]` |
| 残余 | 无（staged schema 边界） |

---

## PROPOSED — `R3-B6-021-O-02`

| 字段 | 值 |
|------|-----|
| 当前状态 | DEFERRED |
| **PROPOSED** | **RESOLVED** |
| 证据 | `test_layer3Snapshot_deterministicRebuild_sameInputsSameHash` 全 `IndustryChainDailySnapshotRow` + 约定 lineage 字段 |
| 残余 | 无 |

---

## PROPOSED — `R3Y-LINEAGE-VR-001`

| 字段 | 值 |
|------|-----|
| 当前状态 | DEFERRED |
| **PROPOSED** | **RESOLVED**（staged WM 路径） |
| 证据 | `test_layer2Snapshot_lineageIncludesFetchIdsAndHashes` · `test_layer2Snapshot_lineageVrMismatch_rejects` · `assert_lineage_matches_validation_report` |
| 残余 | production-live fetch_log 全链 E2E 仍归 Round 3G+；**非** false-close |

---

## PROPOSED — `ADV-R3X-LINEAGE-001`

| 字段 | 值 |
|------|-----|
| 当前状态 | DEFERRED |
| **PROPOSED** | **PARTIAL → RESOLVED（contract-scoped）** + **re-defer** DB 持久化子范围 |
| 已闭合子范围 | L3 `Layer3LineageBuilder` fail-closed · L3 build `LINEAGE_REQUIRED_FIELDS` · L4 upstream 传播 · `test_marketSnapshot_lineageUpstreamFromLayer3` |
| **re-defer** | L3/L4 production DuckDB `axis_snapshot_lineage` 全量写回 E2E（owner Round 3G / migration 轨） |
| 证据 | `closure-evidence-manifest.yaml` · B01-LIN `lin01-partial-closure-scope.md` 对齐 |

---

## PROPOSED — Wave-B reconcile (`R3F-LIN-03`)

| 动作 | 说明 |
|------|------|
| 更新 `ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` §2 | 移入 §1 已关闭 或标注 Batch 3F evidence |
| `UNRESOLVED_ITEM_TASK_COVERAGE.md` | 增 B3F-LIN 行（merge 后） |
| `RESOLVED_ISSUES_REGISTRY.md` | 增 `R3F-B3F-LIN` 批处理行（主会话） |

**不得宣称：** 3D.3 已全关；production clean write；live source 默认启用。
