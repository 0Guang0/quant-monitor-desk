# R3H-10 — DataSourceService SSOT（STAGED-PILOT-SSOT）

> **性质：** Batch 3H **活任务卡**（Wave 级对外名片）— **留在** `docs/implementation_tasks/`，**不迁入** Trellis `research/`  
> **Execute 规格 SSOT：** `.trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot/research/00-EXECUTION-ENTRY.md`  
> **索引：** 已列入 Execute 包 `EXTERNAL-INDEX.md` §A1 · Wave `WAVE1_...INDEX.md` §1  
> **Wave:** 1a · **Module ID:** **C2**（主）· **E4**（收敛）  
> **评级移动:** `R3_STAGED_FIXTURE_CLOSED` → `R4_SANDBOX_REAL_DATA_OR_REHEARSAL`  
> **PASS 登记:** `STAGED-PILOT-SSOT`

---

## 0. 本卡与 Execute 包的分工

| 本卡（活卡）                                       | Execute 包（`research/`）                 |
| -------------------------------------------------- | ----------------------------------------- |
| Wave/issue 追踪 · 模块 ID · 阻塞/下游              | 切片 · 验收 · 必读清单 · 情境路由         |
| 每次切片开工前 **必读**（`EXTERNAL-INDEX.md` §A1） | 每次切片开工前 **必读**（包内 10 份全文） |

## 1. 业务目标

Sync、`qmd data` CLI、rehearsal 脚本 **统一经 `DataSourceService`**；消除对 fetch port 的产品级 bypass；`live_pilot` / `staged_pilot` 仅 **rehearsal**，不得替代 Wave 2 `R3H-08` 产品 live。

## 2. 不在范围

- R3H-08 真网 live 产品化
- 新 migration DDL
- Round4 API

## 3. 验收

见 INDEX §1 Acceptance criteria；Audit PASS 后 C2 行可更新证据。切片验收见 Execute 包 `to-issues-slices.md`。

## 4. 阻塞

- R3H-06 ✅
- Batch 3V ✅

## 5. 下游

**R3H-07** 须等本卡 **CLOSED**。

## 6. Execute 包（多文件 SSOT）

| 入口                 | 路径                                                                                        |
| -------------------- | ------------------------------------------------------------------------------------------- |
| **总路由地图**       | `.trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot/research/00-EXECUTION-ENTRY.md` |
| 外部仓库索引         | `…/research/EXTERNAL-INDEX.md`                                                              |
| 薄执行计划（仅 GAP） | `…/EXECUTION_PLAN.md`                                                                       |
| 垂直切片             | `…/research/to-issues-slices.md`                                                            |

**ADR：** [ADR-025](../../../../docs/decisions/ADR-025-r3h10-sync-fail-closed-datasource-service.md)（S10-01 fail-closed）
