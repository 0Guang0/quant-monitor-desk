# Design — Round 2 Batch D

> 见 `MASTER.plan.md` §4–6

- 状态机与 ID 策略：`sync_job_contract.yaml` + `data_sync_orchestrator.md` §13
- 编排链：ResourceGuard → Adapter → Validators → Gate → WriteManager
- 路径：`backend/app/sync/`（非任务卡字面量 `backend/sync/`）
