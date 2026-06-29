# Batch 3H Task Card Manifest

> **Batch:** Round 3H Real Data Production Entry  
> **总施工图：** `PROJECT_IMPLEMENTATION_ROADMAP.md`（模块轨道版）  
> **PASS SSOT：** `R3H_PASS_EXECUTION_PLAN.md`  
> **当前下一入口（写死）：** **`R3H-10` → `R3H-07` 串行** — `WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md`  
> **Completion rule:** PASS 前闭合 Wave 1–5；每活卡推动至少一级 **Module ID** 评级（`MODULE_COMPLETION_RATING.md` §2）。

---

## 1. 历史任务卡（R3H-01～04 · CLOSED）

| Task ID | Active card                                      | Source coverage        | Module | 状态                    |
| ------- | ------------------------------------------------ | ---------------------- | ------ | ----------------------- |
| R3H-01  | `R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md`   | 宏观六源               | C3     | CLOSED @ 2026-06-28     |
| R3H-02  | `R3H_02_MARKET_DATA_ADAPTERS.md`                 | 市场五源               | C3     | CLOSED；CAL-US → R3H-07 |
| R3H-03  | `R3H_03_CN_MARKET_ADAPTERS.md`                   | CN 十源                | C3     | CLOSED                  |
| R3H-04  | `R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md` | kalshi/poly/web_search | C3, G6 | CLOSED；web_search mock |
| R3H-06  | `R3H_06_CLEAN_SCHEMA.md`                         | 三域 clean schema      | B1, A2 | CLOSED @ 2026-06-29     |

---

## 2. PASS 收口波次（Wave 1–5 · 活轨）

> 波次编号与根目录路线图 §3 对齐。旧 PASS 文档「Wave 1 = R3H-06」已归档 — R3H-06 归入 **历史**。

| Wave   | Task ID       | Active card                         | Module ID          | 评级移动 | 并行              | INDEX                  |
| ------ | ------------- | ----------------------------------- | ------------------ | -------- | ----------------- | ---------------------- |
| **1a** | **R3H-10**    | `R3H_10_DATASOURCE_SERVICE_SSOT.md` | **C2**, E4         | R3→R4    | **串行先**        | `WAVE1_...INDEX.md` §1 |
| **1b** | **R3H-07**    | `R3H_07_US_TRADING_CALENDAR.md`     | **G4**, C3         | R3→R4    | **blocked by 10** | `WAVE1_...INDEX.md` §2 |
| 2a–d   | R3H-08A–D     | （待建）                            | C3, A3, B\*, G6    | R3→R4    | 四轨可并行        | 待建 WAVE2 INDEX       |
| 3      | R3-DCP-01..03 | PASS §4                             | D1, E1, E2         | R3→R4    | 01∥02             | 待建 R3_DCP INDEX      |
| 4      | R3-DCP-05..10 | PASS §4                             | G1, G2, G4, G5, D1 | R3→R4    | 部分并行          | 待建；**五轴全绿**     |
| 5a–e   | R3H-05A..E    | `R3H_05_*.md`                       | 全表               | 审计     | A–E 并行          | 活卡                   |
| 5f     | R3H-05-GATE   | 同上                                | 全表               | PASS     | **串行最后**      | 活卡                   |

**当前 Execute 入口：** 仅 **R3H-10**。R3H-07 在 R3H-10 Audit PASS 前 **禁止** Plan/Execute。

---

## 3. Cross-task constraints

- **Wave 1 串行：** R3H-10 CLOSED → R3H-07（默认无并行）。
- **Wave 2：** R3H-08 四子轨可并行；单 agent 建议串行 **08C→08A→08B→08D**。
- **R3H-06** 已 CLOSED — **禁止** 他轨并行 migration DDL。
- **R3H-05** 仅 Wave 5 GATE — 不得实现缺失 adapter。
- Shared registry 变更 → coordinator 批 merge（playbook §3）。
- 无 adapter + evidence 不得标 READY。

---

## 4. Shared files（coordinator review）

```text
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/datasource_service_contract.yaml
specs/verification/contract_coverage.yaml
docs/modules/data_sources.md
docs/modules/source_route_plan.md
tests/test_catalog.yaml
```

---

## 5. Batch-level acceptance

Batch 3H **CLOSED** 当且仅当：

1. Wave 1–5 全部 CLOSED；`R3H-05-GATE` = **`PASS_ROUND4_REAL_DATA_READY`**。
2. 24 业务源 live→正确 Tier（web_search 真 API = DEFERRED_POST_ROUND4）。
3. **G12 五轴** pytest 全绿（Wave 4 · 用户裁决）。
4. baostock+fred 增量产品路径可演示（Wave 3）。
5. Round4 manifest 可开工；Batch6 项不挡 PASS（见路线图 §5.2）。

---

## 6. 追溯注记

- **web_search：** mock READY；真 API post-R4。
- **CN 日历：** R3H-03 Q12 已闭合；US → R3H-07。
- **G10/G14 FRED：** R3H-01 已闭合。
- **旧入口「下一 R3H-05」已废止** — 05 仅 Wave 5。
