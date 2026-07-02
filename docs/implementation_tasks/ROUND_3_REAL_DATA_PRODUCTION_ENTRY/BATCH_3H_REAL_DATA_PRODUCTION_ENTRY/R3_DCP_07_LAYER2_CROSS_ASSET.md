# R3-DCP-07 — Layer2 跨资产传感器绑真市况源（最小竖切）

> **规划 ID：** R3-DCP-07  
> **Wave：** 4c · **并行轨 0708-A**  
> **Trellis：** `.trellis/tasks/07-02-wave4-r3-dcp-07-layer2/` · Plan v4.1  
> **Module：** G2 Layer2 cross-asset sensors · K1 model input（消费行对齐）  
> **评级：** G2 `R3→R4`  
> **前置：** R3-DCP-05 ✅ @ `c2258363` · R3-DCP-06 ✅ @ `6c6cdd73`  
> **分支：** `feature/wave4-r3-dcp-07-layer2`  
> **Worktree：** `../quant-monitor-desk-wt-dcp07`  
> **状态：** 🟢 Repair 关账 · Audit PASS 路径

---

## 1. Goal（人话）

Layer2 跨资产传感器目前主要靠 **staged fixture** 跑通 loader/snapshot；本票选 **一条** cross-asset 传感器（P0 锚点资产），从 **DCP-05 写入的 Tier A clean**（如 `security_bar_1d` / `axis_observation`）读真市况 → 产出可断言 snapshot/lineage → pytest 绿，**不再以 staged_fixture_only 作为唯一输入**。

---

## 2. 价值

- Wave 4 主线：G2 最小竖切，解锁 `MODULE_COMPLETION_RATING` G2 R3→R4
- 承接 `ACC-LAYER-E2E-LIVE-001` 的 **L2 子集**（L3–L5 余量 → DCP-08/10 + Wave 5）
- 为 Wave 5 `R3H-05-GATE` Layer 绑定审计提供 L2 真 clean 证据

---

## 3. 约束

| 约束 | 要求 |
| ---- | ---- |
| 输入 SSOT | **Tier A clean**；禁止 staged fixture 冒充 PASS |
| 金路径 | 读 clean → Layer2 loader/snapshot builder → lineage（`fetch_log` / VR 绑定按仓内契约） |
| 真网 | 默认 replay/clean 种子；live 须 env-gate + 隔离库 |
| Schema | **无新 migration**（R3H-06 + 015 已封）除非 Plan 审计证明必需且 ADR |
| 范围 | **一条** P0 传感器竖切；禁止五资产一次全落地 |
| 参考项目 | Plan L1/L2/L3 **仅** `参考项目/**`；仓内 `layer2_sensors` = 承接，不进借鉴梯 |
| Registry | 若动 `cross_asset_registry` / capabilities → 主会话排队 merge |

---

## 4. 架构触点

```text
Tier A clean (DCP-05) → security_bar_1d / axis_observation
        ↓
CrossAssetRegistryLoader（扩 clean 读路径）
        ↓
CrossAssetSnapshotBuilder → lineage（source_fetch_id / content_hash）
        ↓
replay e2e pytest（读 clean 非 fixture）
```

**设计权威：** `docs/modules/layer2_cross_asset_sensor.md` · `backend/app/layer2_sensors/`

---

## 5. Acceptance criteria

- [x] 一条 P0 cross-asset 传感器从 **Tier A clean** 读入并产出可断言 snapshot
- [x] 新增/扩展 `tests/test_layer2_*_clean_e2e.py`（或等价）GREEN
- [x] lineage 含 `source_fetch_id` / content 可追溯字段（对齐现有 `test_layer2Snapshot_lineageIncludesFetchIdsAndHashes` 契约）
- [x] `ACC-LAYER-E2E-LIVE-001` **L2 子集**关账证据写入 repair ledger
- [x] `research/reference-adoption-dcp07.md` 含参考项目 L1/L2/L3（非仓内）
- [x] Plan v4.1 包齐；`validate-plan-freeze` exit 0
- [x] `uv run pytest -q` exit 0

---

## 6. 非目标

- L2 全资产矩阵一次落地
- L2 VR/fetch_log 全量持久化（`R3Y-LINEAGE-VR-001` → Batch 6）
- L3/L4/L5 全链 E2E（DCP-08/10）
- FRED live primary（`B2.5-O-05`）

---

## 7. Trellis 入口

`.trellis/tasks/07-02-wave4-r3-dcp-07-layer2/research/00-EXECUTION-ENTRY.md`（Plan 产出）
