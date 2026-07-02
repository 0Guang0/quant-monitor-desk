# R3-DCP-09 — 有界 backfill + 连网验收 CI 分层

> **规划 ID：** R3-DCP-09  
> **Wave：** 4e · **并行轨 0910-A**  
> **Trellis：** `.trellis/tasks/wave4-r3-dcp-09-backfill-ci/` · Plan v4.1 · debt-lite  
> **Module：** D1 Sync orchestration · E3 production gate · CI  
> **评级：** D1 `R4` 巩固（有界 backfill 产品路径）  
> **前置：** R3-DCP-05 ✅ · Wave 3 验收脚本已入库 @ `93b2c82`  
> **分支：** `feature/wave4-r3-dcp-09-backfill-ci`  
> **Worktree：** `../quant-monitor-desk-wt-dcp09`  
> **状态：** 🔴 OPEN · Plan 阶段

---

## 1. Goal（人话）

增量路径（DCP-01/02/05）已通，但 **有界 backfill**（cap 分片、非无上限 FullLoad）与 **连网验收 CI** 仍未产品化。本票让 backfill 走金路径可测可 CLI，并把 Wave 3 验收脚本分层接入 CI nightly（`--run-network` 子集 + live acceptance findings 硬门禁）。

---

## 2. 价值

- 台账关账：`WAVE3-ACC-OPT-01`、`ACC-LIVE-NETWORK-CI-001`、`ACC-LIVE-ACCEPT-NIGHTLY-001`、`LIVE-NETWORK-GATE-001`
- Wave 4 运维可信度：operator 可重复跑有界 backfill + nightly 连网回归

---

## 3. 约束

| 约束 | 要求 |
| ---- | ---- |
| 金路径 | `BackfillShardRunner` / `plan_backfill_shards`；禁止 adapter bypass |
| 有界 | **必须** cap 分片；禁止无上限 FullLoad（Batch 6 余量显式 non-goal） |
| 真网 | env-gate；隔离库；默认 CI 不跑 live（nightly profile） |
| 脚本 | `wave3_isolated_production_acceptance.py` `--quick` 或 nightly-only 全量 |
| 脚本 | `wave3_live_production_acceptance.py` nightly + findings 硬门禁 |
| 参考项目 | L1/L2/L3 **仅** `参考项目/**`（如 OpenBB fetcher 分片概念） |
| 主库 | 禁止 silent canonical 写 |

---

## 4. 架构触点

```text
qmd data backfill（或等价 CLI）→ cap shards
  → DataSyncOrchestrator / BackfillShardRunner
  → clean upsert（隔离库）

CI nightly:
  pytest --run-network <batch275 phase3 子集>
  python scripts/wave3_live_production_acceptance.py
```

**设计权威：** `docs/modules/data_sync_orchestrator.md` §backfill · `backend/app/sync/jobs.py`

---

## 5. Acceptance criteria

- [ ] 有界 backfill CLI/路径：cap 分片 + replay e2e 绿
- [ ] `wave3_isolated_production_acceptance.py` quick/nightly 分层（`WAVE3-ACC-OPT-01`）
- [ ] CI nightly 配置或文档化入口：`pytest --run-network` 子集（`ACC-LIVE-NETWORK-CI-001`）
- [ ] `wave3_live_production_acceptance.py` nightly profile + findings 门禁（`ACC-LIVE-ACCEPT-NIGHTLY-001`）
- [ ] `research/reference-adoption-dcp09.md` 含参考项目 L1/L2/L3
- [ ] Plan v4.1 包齐；`validate-plan-freeze` exit 0
- [ ] `uv run pytest -q` exit 0

---

## 6. 非目标

- 无 cap FullLoad（Batch 6）
- 24 源 production cron（Batch 6 / Round4 壳）
- Tier B/C backfill 全矩阵
- FRED live primary

---

## 7. Trellis 入口

`.trellis/tasks/wave4-r3-dcp-09-backfill-ci/research/00-EXECUTION-ENTRY.md`（Plan 产出）
