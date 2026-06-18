# PRD — Round 2 Batch D DataSyncOrchestrator

> 复杂任务薄索引：全文见 `MASTER.plan.md` §1–3

## 目标

交付 Round 2 最后一批：**DataSyncOrchestrator**，把 Batch A–C 的 registry、adapter、validator、gate、WriteManager 串成可测试的同步任务状态机，并偿还 DECISIONS §9 中与编排相关的延后台账。

## 已确认事实（代码库）

- Batch C Audit PASS；312 tests；`READY_FOR_BATCH_D: yes`
- 无 `backend/app/sync/*` 实现；sync 表仅在 `schema.sql` 定义
- 运行时链路见 `docs/architecture/03_runtime_flows.md`

## 验收标准（→ MASTER §2）

- AC-1…AC-12 见 MASTER §2（可运行 §10 命令验证）

## 范围外

- Layer 1–5 建模（Round 3）
- API/前端/Agent 生产化（Round 4）
- 真实 vendor HTTP/SDK
- 全量 security CI / CodeQL sprint
