# R3X_ponytail_low_touch_bucket_c — Ponytail 桶 C（validators / config / util 低冲突）

## 1. 任务性质

Phase 8D Repair/Debt Lite 切片。与 `feature/round3-real-data-staged-pilot`（PROMPT_14）**并行**，不得触碰 14 的核心文件组。

目标：消化 ponytail 扫描中 **低冲突、非结构性** 债务，拉升 validators / core / util 模块分数，不改变 staged pilot 或 production-live 语义。

## 2. 分支

- 分支：`debt/round3-ponytail-low-touch`
- 基准：`master` @ 协调者指定 commit
- 合并目标：`master`（经 merge gate）
- Worktree：`../quant-monitor-desk-wt-debt-r3-ponytail-low-touch`

## 3. 范围（IN）

| ID    | 模块       | 问题摘要                                     |
| ----- | ---------- | -------------------------------------------- |
| VA-01 | validators | 删除 `common.py` 薄包装，调用方直引实现      |
| VA-02 | validators | 合并重复 helper（与 VA-01 同批）             |
| SC-03 | core       | `resource_guard.py` 8 路信号改为 data-driven |
| SC-04 | config     | 补 `get_resource_profile()` 非法值测试       |
| SC-05 | util       | `error_redaction.py` 无引用 — 删除或接入 ops |
| SC-06 | config     | `CONFIGS_ROOT` 双源 — `api_limits` 用单源    |
| VA-07 | validators | LOW：YAML vs Python rule_id 双轨文档化       |
| VA-08 | validators | LOW：`_table_exists` quote_ident 副作用清理  |

权威扫描：`docs/quality/PONYTAIL_MODULE_SCAN_20260622.md` §4.7–4.8。

## 4. 允许文件

- `backend/app/validators/**`
- `backend/app/core/resource_guard.py`
- `backend/app/config.py`
- `backend/app/api_limits.py`（若存在）
- `backend/app/util/**`
- `tests/test_data_quality_validator.py`
- `tests/test_source_conflict_validator.py`
- `tests/test_resource_guard.py`
- `tests/test_config.py`
- 新增窄测试文件（若需）
- `.trellis/tasks/debt-round3-ponytail-low-touch/**`

## 5. 禁止文件（与 PROMPT_14 互斥）

- `backend/app/ops/**`
- `backend/app/datasources/**`
- `backend/app/storage/**`
- `backend/app/db/**`
- `backend/app/sync/**`
- `backend/app/layer1_axes/**`
- `backend/app/layer2_sensors/**`
- `specs/contracts/**`（除非 VA-07 仅文档引用、零契约变更）
- production DB 写入、live 网络、vendor 真调用

## 6. 工程纪律

- TDD：RED → evidence → GREEN
- `/karpathy-guidelines`、`/testing-guidelines`、`/ponytail` full
- 每个测试 docstring：覆盖范围、测试对象、目的/目标
- GitNexus `impact()` 于符号编辑前
- 修复后 `python -m pytest -q` 全绿
- 不得为通过测试而改测试目的

## 7. 交付

- `.trellis/tasks/debt-round3-ponytail-low-touch/execute-evidence/merge_gate_report.md`
- 每项 RED/GREEN 摘要
- production DB no-mutation 证明（若触数据路径；本切片预期无需）
- 单 commit；不 merge、不 push
