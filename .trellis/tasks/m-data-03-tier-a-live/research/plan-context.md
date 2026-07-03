# M-DATA-03 Context Engineering（Plan R2）

## 命名澄清

| 术语              | 含义                            |
| ----------------- | ------------------------------- |
| **上下文 L1–L5**  | 信息层次（本文件）              |
| **借鉴 L1/L2/L3** | 仅 `参考项目/**`                |
| **仓内直接复用**  | DCP-05/R3H 已有代码，不进借鉴梯 |

## Context Hierarchy（L1–L5）

| Level | 映射                                                                        |
| ----- | --------------------------------------------------------------------------- |
| L1    | `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.1 · `plan-revision-r2.md` §2         |
| L2    | `tier-a-live-inventory.md` · `plan-spec.md`                                 |
| L3    | `EXTERNAL-INDEX.md` §C · `gitnexus-summary.md`                              |
| L4    | `live_tier_a_evidence_v1.yaml` · ADR-034/027/025 · `plan-spec.md` Interface |
| L5    | `to-issues-slices.md` R2                                                    |

## PROJECT CONTEXT

```text
任务：M-DATA-03 Plan R2 — 11 源 R4 真网完整验收
证据：live_tier_a_evidence_v1（统一信封 + source_bindings）
门控：F0 四族 + B2 主路径 + E2 inspect；禁止 SKIP
dispatch：全量去重；mootdx 进 platform matrix
失败：FAIL_FIXABLE 必修 · FAIL_EXTERNAL 须 ADR
完成：plan-revision-r2.md §2 十条 AC
```

## Level 3 源码表（R2 触点）

| 组件           | 路径                                                  |
| -------------- | ----------------------------------------------------- |
| Acceptance CLI | `scripts/tier_a_live_acceptance.py`                   |
| Dispatch       | `backend/app/ops/tier_a_live_incremental_dispatch.py` |
| F0             | `backend/app/ops/data_health/`                        |
| B2             | `backend/app/validation/data_quality_validator.py`    |
| E2             | `backend/app/ops/db_inspect/`                         |
| 11 源 ops      | `backend/app/ops/*_incremental_*.py`                  |
| Contract       | `specs/contracts/live_tier_a_evidence_v1.yaml`        |

## 按 R2 切片必读

| 切片          | 必读                                                  |
| ------------- | ----------------------------------------------------- |
| S-R2-EVIDENCE | contract · `plan-spec.md` pipeline                    |
| S-R2-F0       | `data_health_cli.md` · 四族 profile · EasyXT L2 模板  |
| S-R2-B2       | `data_validation_and_conflict.md` · `source_bindings` |
| S-R2-DISPATCH | `gitnexus-summary.md` · impact() · platform matrix    |
| S-R2-CI       | plan-spec CI AC                                       |
| S-R2-ACCEPT   | contract `acceptance_report` · ADR-034                |

## §5.2 开工必读（→ ENTRY 对齐）

1. `00-EXECUTION-ENTRY.md` §1–§4
2. `plan-revision-r2.md` §2
3. `to-issues-slices.md` 当前切片
4. `live_tier_a_evidence_v1.yaml`
5. `reference-adoption-m-data-03.md` §0
6. ADR-034 · ADR-027
7. `EXTERNAL-INDEX.md` §A

## §5.3 情境路由（→ ENTRY 对齐）

| 情境            | 读                                         |
| --------------- | ------------------------------------------ |
| 能否 SKIP F0？  | **否** — `plan-revision-r2.md` §2.3        |
| 证据放哪？      | contract `envelope` · manifest 文件名      |
| dispatch 改哪？ | 去重金路径；禁止平行 registry              |
| 外部失败？      | `failure_class=external_environment` + ADR |
| 旧 R1 证据？    | `research/archive/non-plan/execute/` 只读  |
