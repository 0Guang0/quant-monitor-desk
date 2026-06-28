# Plan Consolidation — R3H-06 Clean Schema (Wave 1)

> **Phase 5e complete** · Execute **不读**本表以外的 `research/*` Plan 草稿

## 5e 完备性（分流 + 自检）

| 内容类型                  | 落点                                   | Execute 读法 |
| ------------------------- | -------------------------------------- | ------------ |
| 可无损精简的可执行结论    | 活任务卡 → `frozen/*.md`；**INDEX §4** | frozen       |
| 不可精简 / 精简必丢信息   | **INDEX §3** `must-read`               | 原文         |
| Plan 过程记录、已无新结论 | `n/a`                                  | 不读         |
| 仅 Audit 追溯             | `pointer`（`integration-audit.md`）    | Audit 可读   |

冻结前自问：Execute **只读** frozen + INDEX + implement.jsonl 能否跑 §9？**能**（待 freeze-task-card 复制活卡）。

```bash
python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/06-29-round3h-r3h06-clean-schema 5e
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-29-round3h-r3h06-clean-schema
```

## 对照表

| 来源                                        | 结论类型                       | 落点                       | 状态    |
| ------------------------------------------- | ------------------------------ | -------------------------- | ------- |
| `research/plan-boot.md`                     | 边界/授权                      | frozen §2.8 / §8           | merged  |
| `research/brainstorm-session.md`            | 方案否决/采纳                  | frozen §1.1                | merged  |
| `research/spec-driven-development-notes.md` | 契约→测试 + cn_announcement 列 | frozen §5–§6 + INDEX §2    | merged  |
| `research/project-overview.md`              | 基线/偏离                      | frozen §5                  | merged  |
| `research/grill-me-session.md`              | 决策 Q&A                       | frozen §1.1 / §8 / §9      | merged  |
| `research/gitnexus-summary.md`              | impact/触碰面                  | frozen §4                  | merged  |
| `research/to-issues-slices.md`              | S0–S10 依赖                    | INDEX §0.1 / §1；frozen §9 | merged  |
| `research/adversarial-audit-report.md`      | B01–B10 闭环                   | INDEX §4 / §5              | merged  |
| `research/integration-ledger.md`            | 内联 vs §3                     | INDEX §3/§4 规则           | n/a     |
| `research/integration-audit.md`             | 对抗/GAP                       | frozen §10；Audit          | pointer |

**Execute GAP（仅 Execute 交付）：**

- `tests/test_r3h06_clean_schema.py` — 9.0 创建
- `backend/app/db/migrations/013_clean_domain_tables.sql` — 9.1–9.2
- `backend/app/db/migrations/014_stg_foundation_ohlcv.sql` — 9.3
- `backend/app/ops/sandbox_clean_write/clean_write_targets.py` — 9.5
- `specs/schema/schema.sql` 增 `cn_announcement_clean` — 9.2

**Phase 5e complete**
