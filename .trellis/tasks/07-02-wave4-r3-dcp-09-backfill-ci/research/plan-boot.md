# Plan Boot — R3-DCP-09 有界 backfill + CI nightly

> **轨道：** Wave 4e · Plan v4.1  
> **日期：** 2026-07-02  
> **活卡：** `R3_DCP_09_BOUNDED_BACKFILL_CI.md`  
> **分支：** `feature/wave4-r3-dcp-09-backfill-ci`

---

## Phase P0 complete

### 1. 做什么

把 **有界 backfill**（cap 分片、非无上限 FullLoad）产品化为 `qmd data backfill` 金路径 CLI，并分层接入 **CI nightly**：`pytest --run-network` batch275 子集 + `wave3_live_production_acceptance.py` findings 硬门禁；`wave3_isolated_production_acceptance.py` 增加 `--quick` 省掉重复 `pytest_full`。

### 2. 价值

- 关台账：`WAVE3-ACC-OPT-01` · `ACC-LIVE-NETWORK-CI-001` · `ACC-LIVE-ACCEPT-NIGHTLY-001` · `LIVE-NETWORK-GATE-001`
- Wave 4 运维可信度：operator 可重复跑有界 backfill + nightly 连网回归

### 3. 约束

| 约束   | 要求                                                                 |
| ------ | -------------------------------------------------------------------- |
| 金路径 | `BackfillShardRunner` / `plan_backfill_shards`；禁止 adapter bypass   |
| 有界   | 必须 cap 分片；禁止无上限 FullLoad                                   |
| 真网   | env-gate；隔离库；默认 PR CI 不跑 live（nightly profile）            |
| 参考   | L1/L2/L3 仅 `参考项目/**`；禁止 EasyXT silent fallback 进 sync       |
| 前置   | R3-DCP-05 ✅ · Wave 3 验收脚本已入库 @ `93b2c82`                     |

### 4. 架构触点

`qmd data backfill` → cap shards → `DataSyncOrchestrator.run_backfill` → clean upsert（隔离库）

CI nightly：`.github/workflows/nightly.yml` → `--run-network` 子集 → live acceptance

### 5. 成功标准

活卡 §5 + `validate-plan-freeze` exit 0 + Execute 后 `uv run pytest -q`

### 6. P0 已读清单

- [x] `R3_DCP_09_BOUNDED_BACKFILL_CI.md`
- [x] `docs/modules/data_sync_orchestrator.md` §13.4.3 / §13.7 / §13.11
- [x] `backend/app/sync/jobs.py` · `runners.py` · `orchestrator.py`
- [x] `scripts/wave3_isolated_production_acceptance.py` · `wave3_live_production_acceptance.py`
- [x] `tests/test_production_equivalent_smoke_budget.py`
- [x] `.github/workflows/ci.yml`
- [x] `docs/quality/待修复清单.md` §4（WAVE3-ACC-OPT-01 等）
- [x] `specs/contracts/reference_adoption_guardrails.yaml`
- [x] 参考项目路径对齐（DCP-05 同路径；OpenBB fetcher 分片概念 L3）

### 7. 与 DCP-05 差异

| 项       | DCP-05              | DCP-09                          |
| -------- | ------------------- | ------------------------------- |
| 任务类型 | incremental         | **backfill**（有界分片）        |
| CLI      | `qmd data sync`     | **`qmd data backfill`**         |
| CI       | PR 默认 replay      | **nightly** `--run-network`     |
| 验收     | 源 incremental e2e  | Wave 3 验收脚本分层 + findings |
