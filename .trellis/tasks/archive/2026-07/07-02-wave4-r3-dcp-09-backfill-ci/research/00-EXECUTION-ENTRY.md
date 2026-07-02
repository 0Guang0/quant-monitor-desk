# R3-DCP-09 执行入口 — 路由地图（Execute SSOT）

> **角色：** 本任务 **唯一 Execute 读入口**  
> **任务目录：** `.trellis/tasks/07-02-wave4-r3-dcp-09-backfill-ci/`  
> **活卡（包外）：** `EXTERNAL-INDEX.md` → `R3_DCP_09_BOUNDED_BACKFILL_CI.md`  
> **协议：** Plan v4.1 · `plan-skill-outputs.yaml`

---

## 1. 目的 · 价值 · 完成条件

| 维度         | 内容                                                                 |
| ------------ | -------------------------------------------------------------------- |
| **目的**     | 有界 backfill CLI + CI nightly 连网验收分层                          |
| **价值**     | Wave 4 DCP-09；关 Wave3 验收台账四项                                 |
| **评级**     | D1 R4 巩固（有界 backfill 产品路径）                                 |
| **完成条件** | S00–S06 全绿 · `validate-plan-freeze` 已 PASS · Audit PASS           |
| **不在范围** | 无 cap FullLoad · 24 源 cron · Tier B/C backfill · FRED live primary |

---

## 2. 约束 · 规则

| 类别     | 约束                                            | 详述                          |
| -------- | ----------------------------------------------- | ----------------------------- |
| ADR-030  | 双层 cap：31 天/片 + max_shards                 | `docs/decisions/ADR-030-*.md` |
| ADR-025  | Sync 必须 datasource_service                    | fail-closed                   |
| 金路径   | `BackfillShardRunner` / `plan_backfill_shards`  | 禁止 adapter bypass           |
| 参考采纳 | L 梯见 `reference-adoption-dcp09.md`            | guardrails.yaml               |
| 真网     | nightly only；`QMD_ALLOW_LIVE_FETCH` + 隔离库   | ADR-027                       |
| CI       | PR `ci.yml` 不跑 network；nightly workflow 专责 | `docs/ops/nightly_ci.md`      |

---

## 3. 验证命令

```bash
uv run pytest tests/test_sync_orchestrator.py -k backfill -q
uv run python scripts/wave3_isolated_production_acceptance.py --quick
uv run pytest -q -m network tests/test_batch275_live_pilot_gate.py::test_livePilot_phase3RawOnly_threeRequestsLive
uv run python scripts/wave3_live_production_acceptance.py --fail-on-severity HIGH,CRITICAL
uv run pytest -q
uv run python scripts/loop_maintain.py
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/07-02-wave4-r3-dcp-09-backfill-ci
```

证据：`research/execute-evidence/sNN-green.txt`

---

## 4. ADR 索引

| ADR                                                                                        | 标题                                | 切片    |
| ------------------------------------------------------------------------------------------ | ----------------------------------- | ------- |
| [ADR-030](../../../../docs/decisions/ADR-030-bounded-backfill-cap-and-ci-nightly.md)       | 有界 backfill cap + CI nightly 分层 | **S00** |
| [ADR-025](../../../../docs/decisions/ADR-025-r3h10-sync-fail-closed-datasource-service.md) | Sync fail-closed service            | S01–S02 |
| [ADR-027](../../../../docs/decisions/ADR-027-r3h08-product-live-env-gate.md)               | Product live env gate               | S04–S05 |

---

## 5. 执行包阅读规则

### 5.1 包内文件地图

| 文件                          | Skill                       | 摘要                   |
| ----------------------------- | --------------------------- | ---------------------- |
| `00-EXECUTION-ENTRY.md`       | trellis-plan 5e             | 本路由                 |
| `EXTERNAL-INDEX.md`           | trellis-plan 5e             | 包外 §A/B/C            |
| `plan-boot.md`                | P0                          | Boot 复述              |
| `to-issues-slices.md`         | to-issues                   | **切片 AC SSOT**       |
| `plan-task-breakdown.md`      | planning-and-task-breakdown | 任务/CP                |
| `plan-spec.md`                | spec-driven-development     | 技术规格               |
| `plan-context.md`             | context-engineering         | 上下文/路由            |
| `plan-doubt-review.md`        | doubt-driven-development    | 怀疑审查               |
| `reference-adoption-dcp09.md` | trellis-research            | 参考 L1/L2/L3          |
| `project-overview.md`         | GitNexus 1a                 | 子系统                 |
| `gitnexus-summary.md`         | GitNexus 1b                 | 冲击面                 |
| `plan-consolidation.md`       | trellis-plan 5e             | 分流对照               |
| `integration-audit.md`        | trellis-before-dev          | 集成审计               |
| `plan-audit-dcp09.md`         | Plan 对抗审计               | findings + disposition |

### 5.2 切片开工前必读

1. 本文件 §1–§4
2. `to-issues-slices.md` 当前切片行
3. `reference-adoption-dcp09.md`
4. ADR-030
5. 活卡 `R3_DCP_09_BOUNDED_BACKFILL_CI.md`（EXTERNAL-INDEX §A 第 1 行）
6. **其余包外必读：** `EXTERNAL-INDEX.md` §A 第 2–8 行

### 5.3 执行情境路由

| 情境          | 再读                                                            |
| ------------- | --------------------------------------------------------------- |
| S00 cap       | `plan-spec.md` · `bounded_backfill_cap.yaml` sketch             |
| S01 CLI       | `data_commands.py` sync 先例 · `orchestrator.run_backfill`      |
| S03 quick     | `wave3_isolated_production_acceptance.py` steps 表              |
| S04 nightly   | `docs/ops/nightly_ci.md` · `.github/workflows/nightly.yml`      |
| S05 live gate | `wave3_live_production_acceptance.py` findings / plan_alignment |

---

## 6. Execute 顺序指针

见 `to-issues-slices.md` 依赖图：S00 → S01 → S02 → (S03 ∥ S04) → S05 → S06

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。
