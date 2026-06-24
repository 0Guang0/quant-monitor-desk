# Plan Boot — B01-FRED

> Phase P0 complete

## 用户目标

为 Layer1 宏观 P0 序列建立 **FRED-only**、用户授权、受资源限制的 sandbox/raw 试跑路径；证明 FRED 可作为未来宏观主干候选被安全接入，但**不得**声称 production-live 或写 production clean table。

## 依赖

| 依赖 | 状态 | Plan 策略 |
| ---- | ---- | --------- |
| B01-WL (`B01-C01`) Layer1 P0 macro 白名单 | **未合并（并行 Plan/Execute）** | 只读引用 `specs/layer1_axes/**` + `R3D_model_input_whitelist.md`；WL 合并后切换 SSOT 至 `specs/model_inputs/**` |
| Batch 01 playbook + hardening | 已读 | 边界 §2.5/§2.6 写入 MASTER §3 |
| Live 联网授权 | **用户/coordinator 2026-06-24 已授权** | Plan 含 hardening §3 YAML 模板；**Execute FRED-07 方可 live fetch** |

## AC 草稿

- `fred` registry/capability：disabled-by-default / sandbox-candidate
- P0 series：`DGS10`, `T10Y3M`, `VIXCLS`, `SP500`, `DFII10`（≤5）
- Mocked + dry-run 必绿；live 可选且受 cap
- `B2.5-O-05`：FRED-only 证据关闭或 re-defer
- **不改** `data_health.py` 主体（DH2 负责 v2 集成）

## 原计划已读

- [x] `docs/implementation_tasks/README.md`
- [x] `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.6 Batch 01
- [x] GLOBAL×4
- [x] `ROUND_3_DATA_PRODUCTION_READINESS/README.md`
- [x] `R3E_fred_authorized_sandbox_pilot.md`（forward）
- [x] `PROMPT_04_debt_r3b275_fred_staged_semantics.md`（legacy L04）
- [x] `018B_production_live_pilot_gate.md`（legacy L05）
- [x] `R3Y_readonly_data_health_v1.md`（legacy L03，只读）
- [x] `BATCH_01_*` manifest / hardening / adversarial audit
- [x] `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §3.1 + §3.4 + §2.5–§2.7 + §4

## 当前 Round batch map

已读 `ROUND3_BATCH_IMPLEMENTATION_MAP.md` — Batch 01 协调包；FRED = `B01-C02`；合并 Track A 序 3（**WL 须先合并**）。

**Phase P0 complete**
