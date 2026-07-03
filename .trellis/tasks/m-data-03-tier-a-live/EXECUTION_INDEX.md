# 执行索引 — M-DATA-03（Plan R2 · v4.1）

> Plan 薄索引 · Execute 首读：`research/00-EXECUTION-ENTRY.md`

## 0. 元数据

| 字段              | 值                                             |
| ----------------- | ---------------------------------------------- |
| slug              | `m-data-03-tier-a-live`                        |
| protocol          | `4.1`                                          |
| plan_revision     | **R2** @ 2026-07-03                            |
| status            | **planning**                                   |
| evidence_contract | `specs/contracts/live_tier_a_evidence_v1.yaml` |

## 1. R2 切片（Execute 步骤表）

| Step | 切片          | Plan      |
| ---- | ------------- | --------- |
| R2.1 | S-R2-EVIDENCE | [x] |
| R2.2 | S-R2-F0       | AC 已冻结 |
| R2.3 | S-R2-B2       | AC 已冻结 |
| R2.4 | S-R2-DISPATCH | AC 已冻结 |
| R2.5 | S-R2-ACCEPT   | AC 已冻结 |
| R2.6 | S-R2-CI       | AC 已冻结 |

切片 AC SSOT：`research/to-issues-slices.md`  
用户 AC SSOT：`research/plan-revision-r2.md` §2

## 2. Plan 包路径

| 类   | 路径                                                 |
| ---- | ---------------------------------------------------- |
| 入口 | `research/00-EXECUTION-ENTRY.md`                     |
| 口径 | `research/plan-revision-r2.md`                       |
| 规格 | `research/plan-spec.md`                              |
| 契约 | `specs/contracts/live_tier_a_evidence_v1.yaml`       |
| 冻结 | `plan.freeze.md` · `frozen/M_DATA_03_TIER_A_LIVE.md` |

## 3. 验证（Plan freeze）

```bash
uv run python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/m-data-03-tier-a-live 5e
uv run python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/m-data-03-tier-a-live
```

## 4. 归档（非 Plan）

`archive/` · `research/archive/` — 见 `research/plan-revision-r2.md` §5

## 5. Audit 追溯

R2 Execute 完成后 Audit；历史见 `archive/audit/` · `research/archive/non-plan/`
