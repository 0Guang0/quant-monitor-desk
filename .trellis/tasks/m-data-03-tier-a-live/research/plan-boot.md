# Plan Boot — M-DATA-03 Tier A Live（Plan R2）

> **轨道：** complex · Plan v4.1 · **Revision R2** @ 2026-07-03  
> **活卡：** `docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/M_DATA_03_TIER_A_LIVE.md`

---

## Phase P0 complete

### 1. 做什么

在 **隔离库** 上为 11 个 Tier A 源交付 **R4 真网完整验收**：统一证据信封、`live_tier_a_evidence_v1` 契约、F0 四族 profile、B2 主验证器、dispatch 去重、CI 回归 — **禁止 SKIP 当过关**。

### 2. 为什么做

- 用户 grill（2026-07-03）：R1 partial F0 + SKIP 叙事作废；整票须诚实 R4
- 路线图 §0.3.4：11/11 live；MCR C3/D1/E1/E2/F0/B2 → R4 sandbox scope
- M-G1-03 依赖真网 clean + 完整 post-write 门控

### 3. 做到什么算完成（R2 AC）

**完整 10 条枚举见 `plan-revision-r2.md` §2（不得仅读本摘要）。** 摘要：

1. `live_tier_a_evidence_v1` 实现 + 11 源 manifest
2. 统一验收 JSON；`failure_class`；**无 SKIP**
3. F0 四族 profile
4. B2 `validate_table` 11/11
5. **E2** `DbInspector.inspect()` 非 FAIL（11/11）
6. dispatch 去重 + mootdx matrix
7. CI + **失败 artifact**
8. `pytest` + 11/11 live exit 0
9. **MCR** C3/D1/E1/E2/F0/B2 → R4
10. 关账证据 `archive/non-plan/execute/r2-tier-a-live-accept-evidence.md`

### 4. 约束复述

| 约束      | 要求                                           |
| --------- | ---------------------------------------------- |
| 权威顺序  | `docs/` + `specs/` > `参考项目/**` > 仓内代码  |
| 证据 SSOT | `specs/contracts/live_tier_a_evidence_v1.yaml` |
| 金路径    | DCP-05 + `DataSourceService`（R2 去重包装层）  |
| 真网闸    | `QMD_ALLOW_LIVE_FETCH=1` + 隔离 `DATA_ROOT`    |
| 失败      | `FAIL_FIXABLE` 必修 · `FAIL_EXTERNAL` 须 ADR   |
| DDL       | **无**新 migration（ADR-028）                  |
| 阶段外置  | **0**（本票必须 R4 闭合）                      |

### 5. 架构触点（R2 统一流水线 · SSOT = plan-spec.md）

```text
env闸 → live sync (incremental → clean)
  → live_tier_a_evidence_manifest.json
  → B2 validate_table
  → E2 DbInspector.inspect
  → F0 run_data_health_profile (四族)
  → acceptance report JSON
```

### 6. P0 已读清单

- [x] 活卡 · ROADMAP §0.3.3–0.3.4 · MCR §3.C–E
- [x] `plan-revision-r2.md`（用户 grill 口径）
- [x] `live_tier_a_evidence_v1.yaml` · `data_quality_rules.yaml`
- [x] DCP-05 归档（仓内管道基线）
- [x] ADR-034 · ADR-027 · ADR-025 · ADR-028
- [x] GitNexus 1a/1b · reference-adoption · tier-a-live-inventory

### 7. 与 R1 Execute 基线

R1 已交付 replay/live 主干（11 e2e harness）。**非 Plan 产物**已归档至 `research/archive/non-plan/execute/`；R2 Plan 在其上定义完整 R4 口径，不重复 R1 切片。
