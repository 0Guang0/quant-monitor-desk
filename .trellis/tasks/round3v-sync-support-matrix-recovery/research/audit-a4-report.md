# A4 audit-quality — B3V-SYNC support matrix & crash-window recovery

> Dimension: Code Quality (A4 only)  
> Scope: B3V-SYNC Execute 实现（`fb1cf4c6` feat + 分支 Plan QC 文档 diff）  
> Worktree: `C:\Users\Guang\Desktop\quant-monitor-desk-wt-b3v-sync`  
> Skills: `code-review-and-quality` + `doubt-driven-development`  
> Authority: `agents/code-reviewer.md` · `agents/audit-adversarial-authority.md` · `B02_04` · ADR-001  
> Mode: **只读**（无代码修复）

---

## Verdict: **PASS**

实现与 `B02_04` VR-SYNC-002/001、`sync_job_contract.yaml`、ADR-001 写提交→COMPLETED 分离语义一致：契约 parity、reserved `DeferredJobTypeError`、incremental crash-window hook + `recover_stuck_writing_job` 恢复路径闭环。测试含五字段中文 docstring，Playbook §8.4 子集 9 passed。无 P0 逻辑/安全阻塞；下列为 NON-BLOCKING 计划外缺口与可维护性建议。

---

## 审查范围

| 文件                                            | 变更摘要                                                                        |
| ----------------------------------------------- | ------------------------------------------------------------------------------- |
| `backend/app/sync/contract.py`                  | 新增：契约 loader、`DeferredJobTypeError`、implemented/reserved 常量            |
| `backend/app/sync/orchestrator.py`              | `run_full_load` deferred；`recover_stuck_writing_job` utility；handler registry |
| `backend/app/sync/runners.py`                   | `post_write_pre_complete_hook`（pytest-only）；写后 hook 注入点                 |
| `specs/contracts/sync_job_contract.yaml`        | implemented/reserved/utility_operations/deferred_error SSOT                     |
| `tests/test_sync_orchestrator.py`               | parity、deferred、crash-window、recovery、hook guard 共 9 用例                  |
| `tests/test_r3x_residual_open_items_closure.py` | advA3_016 → `DeferredJobTypeError`                                              |
| `tests/conftest.py`（分支 diff）                | R3H-04 prediction auth bootstrap — **非 B3V-SYNC 业务代码**                     |

---

## 轴评分（1–5）

| 轴             | 分  | 理由                                                                                                         |
| -------------- | --- | ------------------------------------------------------------------------------------------------------------ |
| Correctness    | 4   | incremental crash→WRITING+write_id→recovery→COMPLETED 主路径正确；recovery 不校验 clean 表实际行（见 A4-01） |
| Readability    | 4   | `contract.py` 职责清晰；`DeferredJobTypeError` 字段自描述；handler registry 结构一致                         |
| Architecture   | 4   | utility 与 schedulable job_type 分离符合契约；hook 仅 incremental runner 可注入（见 OP-01）                  |
| Error handling | 4   | deferred/hook/recovery fail-closed 到位；unknown job 用 KeyError 与非法状态 ValueError 不一致（A4-02）       |
| Test quality   | 4   | 五字段齐全、语义断言（行数不变、status 序列）；utility_operations parity 不在 §8.4 主文件子集内（A4-05）     |

---

## §3.4 发现表

| 轴              | ID    | 发现                                                                                                                                                                                               | 阻塞?        | 证据                                                                                |
| --------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | ----------------------------------------------------------------------------------- |
| Correctness     | A4-01 | `recover_stuck_writing_job` 仅检查 `status=WRITING` 且 `write_id` 非空，**不验证** clean 表是否已有对应写入；若 DB 异常导致 write_id 落库但 clean 行缺失，recovery 仍 transition COMPLETED         | NON-BLOCKING | `orchestrator.py:281-297`；runbook 要求运维先确认 clean 行                          |
| Error handling  | A4-02 | unknown `job_id` 抛 `KeyError`，非法状态抛 `ValueError`；调用方/CLI 需捕获两种异常，与 deferred 的 `DeferredJobTypeError` 三分支                                                                   | NON-BLOCKING | `orchestrator.py:288-294`                                                           |
| Maintainability | A4-03 | `IMPLEMENTED_JOB_TYPES` / `RESERVED_JOB_TYPES` 在 `contract.py` 硬编码，与 YAML SSOT 双轨；parity 测试防漂移但未消除重复源                                                                         | NON-BLOCKING | `contract.py:14-17` + `test_syncJobContract_implementedTypes_matchRuntimeCallables` |
| Observability   | A4-04 | recovery 路径跳过 incremental 正常路径的 `ITEM_SUCCESS` 事件，仅 `transition(COMPLETED)`；审计链与 happy path 不对称                                                                               | NON-BLOCKING | `orchestrator.py:296-297` vs `runners.py:507-518`                                   |
| Test            | A4-05 | `test_syncJobContract_implementedTypes_matchRuntimeCallables` 未断言 `utility_operations` ↔ registry `kind=utility`；该断言在 `test_r3f_br_backfill_reconcile_closure.py`，不在 Playbook §8.4 子集 | NON-BLOCKING | Playbook §8.4 仅 `test_sync_orchestrator.py`                                        |
| Scope           | A4-06 | 分支 `master..HEAD` diff 含 `tests/conftest.py` R3H-04 bootstrap，与 B3V-SYNC 无关；Execute 代码已在 `fb1cf4c6`，Plan QC 提交未改 sync 实现                                                        | NON-BLOCKING | `tests/conftest.py:54-69`（分支 diff）                                              |

---

## 计划外发现

| ID    | 场景                                                                                                                                                       | 若只按 MASTER §9 / Playbook §8.4 用例测会漏什么                               | 严重度                                                                   |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| OP-01 | Backfill shard 写后 COMPLETED 仍在 `with cm.writer()` 内 transition，**无** `post_write_pre_complete_hook`；ADR-001 窗口对 backfill 未测、无 recovery 覆盖 | backfill crash-window 仍可能 COMPLETED/WRITING 语义与 incremental 不一致      | NON-BLOCKING（任务卡 SYNC-05 聚焦 incremental；backfill defer Round 3F） |
| OP-02 | `recover_stuck_writing_job` 可被任意调用方 invoke，无 auth/ops profile guard（与 pytest hook guard 对比）                                                  | 非 ops 路径误恢复 CREATED 已被 ValueError 拦住；误恢复合法 WRITING 需运维纪律 | NON-BLOCKING                                                             |
| OP-03 | `load_sync_job_contract()` 契约文件缺失/损坏时直接 IO/YAML 异常上浮，无 typed contract error                                                               | 部署缺契约时 orchestrator import 即失败（fail-fast，可接受）                  | 信息性                                                                   |

**对抗搜索声明：** 已对照 `B02_04` §4 forbidden、ADR-001、`sync_job_contract.yaml`、`contract.py`、`orchestrator.py` handler registry、`runners.py` incremental 写后 hook 时序（writer 块结束→hook→COMPLETED）、9 条 B3V slice pytest、advA3_016、runbook、`registry_proposed_delta.yaml`。`write_contract.yaml` / WriteManager diff 为空（A3 约束满足）。

---

## DOUBT（对抗性）

| Claim                                             | Attack                                                                                                          | Result                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| 「reserved full_load 不得裸 NIE」                 | `run_full_load` → `raise_deferred_job_type`；advA3_016 + parity 测试                                            | **成立**                                   |
| 「写成功、COMPLETED 前 crash → WRITING+write_id」 | hook 在 writer 事务提交后、COMPLETED 前；`test_syncJob_incremental_crashWindow_*`                               | **成立**                                   |
| 「recovery 不 double write」                      | recovery 仅 status transition；`rows_after == rows_before` 断言                                                 | **成立**                                   |
| 「生产不能注入 crash hook」                       | `sync_adapter_bypass_allowed()` 仅 `PYTEST_CURRENT_TEST`；`test_syncJob_incremental_hook_rejectedOutsidePytest` | **成立**                                   |
| 「recovery 安全可盲调」                           | 不验 clean 表；WRITING+write_id 即可 COMPLETED                                                                  | **部分成立** — A4-01；runbook 要求人工确认 |

**必选 DOUBT 结论（file:line）：** `orchestrator.py:291-297` — recovery 在 `write_id` 存在时无条件 `transition(COMPLETED)`，不校验 WriteManager 写入是否在 clean 表可观测；与 runbook 步骤 1「Confirm clean table rows」形成 **code/runbook 分工** 而非代码内 fail-closed。计划未写此边界；若需 defense-in-depth 可在 recovery 前查 write ledger/clean 行数。

---

## Checklist（code-reviewer.md）

- [x] 无 P0 逻辑/安全阻塞
- [x] 错误处理可观测（deferred 含 code/owner/phase/docs_anchor；hook/recovery fail-closed）
- [x] 风格与邻近模块一致（ponytail：pytest-only hook；最小 recovery 实现）
- [x] 测试变更保留 purpose（中文五字段）
- [x] 判定基于 diff 与 pytest，非覆盖率 KPI

---

## 验证结果

| 检查                        | 命令                                                                                                                                                                   | 结果                                                                   |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| B3V slice pytest            | `uv run pytest tests/test_sync_orchestrator.py -k "syncJobContract or syncJob_reserved or syncJob_incremental or syncJob_recover" -q --basetemp=.audit-sandbox/pytest` | **PASS**（9 passed）                                                   |
| advA3_016                   | `uv run pytest tests/test_r3x_residual_open_items_closure.py::test_advA3_016_orchestratorDeferredRunners -q`                                                           | **PASS**                                                               |
| Ruff                        | `uv run ruff check backend/app/sync/contract.py backend/app/sync/orchestrator.py backend/app/sync/runners.py`                                                          | **PASS**                                                               |
| 全量 pytest（Execute 证据） | `research/execute-evidence/full-pytest-green.txt`                                                                                                                      | 1744 passed；34 failed 为 Round3G bootstrap 预存 gap，**非本任务引入** |

---

## 做得好的地方

- `DeferredJobTypeError` 结构化字段 + 稳定 message，满足 VR-SYNC-002「不得裸 NIE」。
- Hook 置于 writer 事务 **之外**、COMPLETED **之前**，精确模拟 ADR-001 crash window。
- `post_write_pre_complete_hook` pytest-only guard 与 `sync_adapter_bypass_allowed` 同一模式，无生产 env 后门。
- `recover_stuck_writing_job` 注册为 `kind=utility`，与 schedulable `job_types` 分离，契约注释清晰。
- 测试 `rows_after == rows_before` 直接验证「不 double write」语义，非 tautological status 断言。
- registry proposed delta 诚实保留 `D2-P1-1` full_load runner OPEN，不夸大关账。

---

## A4 门控结论

| 项            | 值                                                                                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 维度          | A4 Code Quality                                                                                                                                        |
| 结论          | **PASS**                                                                                                                                               |
| BLOCKING 计数 | 0                                                                                                                                                      |
| 建议跟进      | A4-01 → 可选 recovery 前 write ledger 校验；A4-05 → Playbook §8.4 增 utility parity 或 cross-ref r3f closure 测；OP-01 → Round 3F backfill crash slice |

_审计时间：2026-06-28 · 只读 · 未修改生产代码_
