# Zero-Open Signoff — B3V-DATA `round3v-schema-hash-fail-closed`

| 字段              | 值                                     |
| ----------------- | -------------------------------------- |
| 分支              | `fix/round3v-schema-hash-fail-closed`  |
| Worktree          | `quant-monitor-desk-wt-b3v-data`       |
| 策略              | `BATCH_3V_ZERO_OPEN_CLOSURE_POLICY.md` |
| **OPEN 计数**     | **0**                                  |
| **BLOCKING 计数** | **0**                                  |

## 门禁复验（Repair 会话）

| 门禁            | 命令                                                                                                                                                     | exit |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- |
| Execute handoff | `python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/round3v-schema-hash-fail-closed`                                                | 0    |
| AUDIT A8 子集   | `uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q --basetemp=.audit-sandbox/pytest` | 0    |
| loop/catalog    | `uv run python scripts/loop_maintain.py --fix`                                                                                                           | 0    |
| 分支 commit     | Execute 交付物 + 任务 evidence + loop 生成物已入库                                                                                                       | —    |
| registry 三件套 | **未 commit**（见 `registry-ready.md`）                                                                                                                  | —    |

## BLOCKING 闭合

| ID     | 原发现                                          | 闭合方式                                 | 证据                                           |
| ------ | ----------------------------------------------- | ---------------------------------------- | ---------------------------------------------- |
| A1-B01 | 实现与任务工件未 commit                         | **FIX** — git commit 允许文件 + 任务目录 | 本 Repair commit                               |
| A1-B02 | `datasource-adapters.md` schema_hash 与契约漂移 | **FIX** — 更新 §3 Contracts 表           | `.trellis/spec/backend/datasource-adapters.md` |

## NON-BLOCKING 闭合

| ID             | 闭合方式              | 说明                                                                                                                        |
| -------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| A1-N01         | **RE-DEFER**          | Tier C 全量 pytest 失败为 ResourceGuard/docs 索引卫生；owner=主会话 CI；closure=`loop_maintain --fix` + normal profile 全绿 |
| A1-N02         | **FIX**               | E501 `test_db_validation_gate.py` UPDATE 行折行                                                                             |
| A1-N03         | **RE-DEFER**          | GitNexus 索引陈旧；owner=merge coordinator；closure=`node .gitnexus/run.cjs analyze` post-merge                             |
| A1-N04         | **WONT-FIX**          | 模块文档可选补强；契约+spec 已同步，AC 不强制                                                                               |
| A1-N05         | **ACCEPTED**          | 9.0-red 基线语义已记入 A5；切片 RED 9.2/9.3 有效                                                                            |
| A5-§4.3        | **RE-DEFER**          | audit-prod-path 全库 pytest 未绿；与 A1-N01 同因；MASTER §0.1 Tier A only                                                   |
| A5-evidence薄  | **ACCEPTED**          | 9.3/9.4 green 可独立复现；A5 抽检 2 passed                                                                                  |
| ADV-01         | **ACCEPTED**          | MASTER §2.2 首写 fail-open 为设计内                                                                                         |
| ADV-02         | **ACCEPTED**          | 有界 payload + ponytail 天花板                                                                                              |
| ADV-03         | **FIX**               | G-03 registry 回退单测                                                                                                      |
| G-01           | **FIX**               | `@pytest.mark.parametrize` 三后缀 gate 测                                                                                   |
| G-02           | **RE-DEFER**          | owner=B02-DATA-05/B3V-C05；phase=registry merge；closure=schemaless 正向 gate 测                                            |
| G-03           | **FIX**               | `test_missingSchemaHash_registryFallback_rejects`                                                                           |
| G-04           | **WONT-FIX**          | `row_count>0` 条件为设计内；契约已述                                                                                        |
| G-05           | **RE-DEFER**          | owner=B02-DATA-05；closure=多写入路径 integration                                                                           |
| G-06           | **WONT-FIX**          | 单元分层已覆盖 AC；E2E 非本切片                                                                                             |
| G-07           | **RE-DEFER**          | owner=项目契约策略；与 write_contract 全局 defer 一致                                                                       |
| A4-01..07      | **ACCEPTED/RE-DEFER** | 与 G/ADV 映射；无新 OPEN                                                                                                    |
| A3-PLAN-01..03 | **ACCEPTED**          | fail-closed 偏安全；scope 外                                                                                                |
| A6-NB-1..2     | **ACCEPTED**          | 有界 I/O 备忘                                                                                                               |
| A7-F1..F4      | **ACCEPTED**          | 死常量/环境/有界 I/O                                                                                                        |
| A2 建议项      | **WONT-FIX**          | Ponytail 可选收缩；非 OPEN                                                                                                  |
| B02-DATA-05    | **RE-DEFER**          | `registry-ready.md` proposed delta；主会话 §7.3                                                                             |

## A1–A8 报告 OPEN 行

| 报告     | 修复前 OPEN | 修复后                                     |
| -------- | ----------- | ------------------------------------------ |
| audit-a1 | 2 BLOCKING  | 0                                          |
| audit-a2 | 0           | 0                                          |
| audit-a3 | 0           | 0                                          |
| audit-a4 | 0           | 0                                          |
| audit-a5 | 1 NB (§4.3) | 0（re-defer 登记）                         |
| audit-a6 | 0           | 0                                          |
| audit-a7 | 0           | 0                                          |
| audit-a8 | 7 NB gaps   | 0（G-01/G-03 FIX；其余 re-defer/wont-fix） |

## 签收

**Zero-open Repair PASS** — 分支可进入 coordinator merge 队列；`VR-DATA-001` registry 行待主会话应用 `registry-ready.md` delta。
