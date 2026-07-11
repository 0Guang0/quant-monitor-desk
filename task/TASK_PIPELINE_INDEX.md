# Phase 1 流水线 Task 索引

> **结构：** 19 个**平级** task，无子票；自上游（registry）至入库（write-manager），再编排、Job、入口、总关账。  
> **编制：** 2026-07-10  
> **每票三件套：** `task_plan.md` · `findings.md` · `progress.md`

---

## 实施顺序（严格线性）

```text
01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09
→ 10 → 11 → 12 → 13 → 14 → 15 → 16
→ 17 → 18 → 19
```

| 序  | 目录                                                                    | 流水线阶段             |
| --- | ----------------------------------------------------------------------- | ---------------------- |
| 01  | [task-01-source-registry](task-01-source-registry/)                     | 源注册与 capability    |
| 02  | [task-02-source-route-plan](task-02-source-route-plan/)                 | 路由计划               |
| 03  | [task-03-resource-guard](task-03-resource-guard/)                       | 资源守卫（fetch 前）   |
| 04  | [task-04-datasource-fetch](task-04-datasource-fetch/)                   | 正式抓取               |
| 05  | [task-05-raw-store](task-05-raw-store/)                                 | Raw / fetch_log        |
| 06  | [task-06-staging](task-06-staging/)                                     | Staging                |
| 07  | [task-07-data-quality-validator](task-07-data-quality-validator/)       | 质量校验               |
| 08  | [task-08-source-conflict-validator](task-08-source-conflict-validator/) | 冲突校验               |
| 09  | [task-09-write-manager](task-09-write-manager/)                         | **入库（clean 写口）** |
| 10  | [task-10-sync-orchestrator](task-10-sync-orchestrator/)                 | 编排核心 / 状态机      |
| 11  | [task-11-job-incremental](task-11-job-incremental/)                     | Job：增量              |
| 12  | [task-12-job-backfill](task-12-job-backfill/)                           | Job：回补              |
| 13  | [task-13-job-full-load](task-13-job-full-load/)                         | Job：全量              |
| 14  | [task-14-job-reconcile](task-14-job-reconcile/)                         | Job：冲突重抓          |
| 15  | [task-15-job-revision-audit](task-15-job-revision-audit/)               | Job：修订审计          |
| 16  | [task-16-job-data-quality](task-16-job-data-quality/)                   | Job：质量巡检          |
| 17  | [task-17-cli-data-commands](task-17-cli-data-commands/)                 | CLI 四命令             |
| 18  | [task-18-scheduler](task-18-scheduler/)                                 | Scheduler profile      |
| 19  | [task-19-phase1-gate](task-19-phase1-gate/)                             | P1-GATE 总关账         |

---

## 与旧目录

| 旧路径                 | 新路径                                                             |
| ---------------------- | ------------------------------------------------------------------ |
| `task-16-layer1-full/` | 内容逐步迁入 `task-19-phase1-gate/`（PRD · INVENTORY · 历史 plan） |
| `归档/`                | 已完成票，保留；与 `task-01-source-registry` **编号不同**          |

---

## 全局 SSOT

- 防遗漏全量统计：`task-19-phase1-gate/PHASE1_COMPLETION_INVENTORY.md`（自 `task-16-layer1-full` 迁入）
- 产品口径：`task-19-phase1-gate/PHASE1_PRD.md`
