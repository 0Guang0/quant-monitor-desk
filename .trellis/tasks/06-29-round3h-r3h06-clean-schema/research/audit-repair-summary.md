# Audit Repair Summary — R3H-06 Clean Schema

> **日期：** 2026-06-29 · **分支：** `feature/round3h-r3h06-clean-schema` · **Repair agent：** trellis-implement

## 计数

| 类别         | 合计   | fixed  | deferred | pending（主会话）      |
| ------------ | ------ | ------ | -------- | ---------------------- |
| P0 BLOCKING  | 4      | 4      | 0        | 0（R-B03 commit 除外） |
| P1 IMPORTANT | 4      | 4      | 0        | 0                      |
| P2 / NB      | 28     | 22     | 6        | 0                      |
| **合计**     | **36** | **30** | **6**    | **1**（R-B03 commit）  |

## 核心修复

1. **R-B01（最高优先）** — `_non_target_row_count` 按表选择 key 列（`axis_observation`→`indicator_id`），fred promote execute 不再 BinderException。
2. **R-I01–R-I04** — 新增 10 条 `test_r3h06_clean_schema.py` 测（macro E2E、三域幂等、OHLCV、域路由负向、披露校验）；FRED bridge 测改走 `populate_macro_from_bundle`。
3. **R-B04/B05** — `execute-evidence/9.{1..10}-*.txt` 重录真实 pytest/rg 输出；`evidence_index.json` 已索引。
4. **R-B02** — `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0.0 G3/G4/G6 标 **已闭合 @ R3H-06**。

## 仍 deferred（不阻 Repair 复审计）

| ID               | 原因                                                                               |
| ---------------- | ---------------------------------------------------------------------------------- |
| R-B03            | 主会话 commit（用户批准）                                                          |
| A4-12            | before_proof 与 DB COUNT 对齐 — Wave 3 深化                                        |
| A4-05            | 幂等列快照 — 可选；COUNT+OHLCV 已够 G6                                             |
| A1-NB01/02/04/05 | coordinator manifest / GitNexus analyze / 测去重 / prd 状态 — merge 或 finish-work |
| A8-P2-06         | market_bar_clean 专用 pytest — rg 门禁已在 9.8 证据                                |

## pytest

```text
uv run pytest -q --basetemp=.audit-sandbox/pytest
→ exit 0 @ 2026-06-29（全库绿）
```

**注：** 全库连续跑时偶发 `test_r3g02AuditCli_writesDecisionReport` FileNotFoundError（顺序污染）；单测与多数全库跑绿。与 R3H-06 diff 无直接因果。

## 主要修改文件

| 文件                                                              | 变更                                                        |
| ----------------------------------------------------------------- | ----------------------------------------------------------- |
| `backend/app/ops/sandbox_clean_write/limited_production_entry.py` | 域感知 `_non_target_row_count`                              |
| `backend/app/ops/sandbox_clean_write/rehearsal_loader.py`         | `populate_staging_for_target`、披露校验、删 fred bar 死路径 |
| `backend/app/ops/sandbox_clean_write/rehearsal_runner.py`         | 统一 staging dispatch                                       |
| `backend/app/ops/sandbox_clean_write/clean_write_targets.py`      | yahoo defer 注释                                            |
| `specs/contracts/ops_db_inspect_contract.yaml`                    | `cn_announcement_clean` key_table                           |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                               | G3/G4/G6 状态对齐                                           |
| `tests/test_r3h06_clean_schema.py`                                | +10 测（22 total）                                          |
| `tests/test_migration_coverage.py`                                | `CLEAN_DOMAIN_MIGRATED_TABLES`                              |
| `tests/test_round3g_limited_production_clean_write.py`            | OHLCV + FRED macro bridge                                   |
| `tests/test_official_macro_adapters.py`                           | macro staging 路径对齐                                      |
| `tests/db_helpers.py`                                             | 合并 INSERT helper                                          |
| `execute-evidence/*`                                              | 真实 RED/GREEN/FULL 输出                                    |

## 下一步（主会话）

1. 用户批准后 **commit**（R-B03）
2. 重跑 A4/A5/A8 关键测确认 Repair PASS
3. `finish-work` 前更新 `prd.md` 状态（A1-NB05）
