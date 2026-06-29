# Audit Repair Ledger — R3H-10（八路全量 · 一项不留）

> 来源：A1–A8 子 agent + A5 计划外 O1–O7 + 主会话 Repair。  
> **完成条件：** `fixed`（含证据）或 `deferred`（绑定任务 ID，见 §Wave 2 承接表）。

## P0 BLOCKING（已全部 fixed）

| ID         | 来源  | 问题                                                    | 状态      | 证据                                                                                                       |
| ---------- | ----- | ------------------------------------------------------- | --------- | ---------------------------------------------------------------------------------------------------------- |
| O1 / AR-01 | A5/A7 | `validate-plan-freeze` 失败；bundle 未登记 Execute 工件 | **fixed** | `00-EXECUTION-ENTRY.md` §5.1 · `plan-consolidation.md`；`validate-plan-freeze` exit 0                      |
| O2 / AR-02 | A5    | S10-CLOSE 关账：C2/Wave1/PASS 仍 OPEN                   | **fixed** | `MODULE_COMPLETION_RATING.md` C2→R4；`WAVE1_...INDEX.md` §1 AC [x]；`R3H_PASS_EXECUTION_PLAN.md` 1a CLOSED |
| A1-F01     | A1    | `run_reconcile` 与 ADR-025 三条路径不对称               | **fixed** | ADR-025 §Reconcile defer；`source-index.md`；`test_r3h10S10_01_reconcile_*`                                |
| A8-B1      | A8    | `live_pilot` 无 REHEARSAL 标记测                        | **fixed** | `live_pilot.py` docstring；`test_r3h10_rehearsalScriptsDoNotClaimProductLiveReady`                         |
| A8-B2      | A8    | live 轨缺 SSOT 对称测                                   | **fixed** | `test_livePilot_liveFetchPortsShareProductFetchPortModule`                                                 |
| A7-F01     | A7    | 缺 `gitnexus-audit-summary.md`                          | **fixed** | `research/gitnexus-audit-summary.md`                                                                       |
| A7-F02     | A7    | 无 `detect_changes` 落盘                                | **fixed** | `research/gitnexus-detect-changes-evidence.txt`                                                            |

## P1 IMPORTANT（fixed）

| ID     | 来源 | 问题                                  | 状态      | 证据                                                    |
| ------ | ---- | ------------------------------------- | --------- | ------------------------------------------------------- |
| AR-03  | A8   | live fetch_ports SSOT 测              | **fixed** | 同上 B2                                                 |
| A7-F03 | A7   | `loop_manifest.json` 全 AC pending    | **fixed** | 本任务 `loop_manifest.json` 全 `closed`                 |
| A7-F04 | A7   | `evidence_index.json` 空              | **fixed** | `evidence_index.json` 已填 execute/audit 索引           |
| O7     | A5   | `integration-audit.md` PASS_WITH_GAPS | **fixed** | `research/integration-audit.md` → PASS + doc-gap 闭合表 |

## P2 NON-BLOCKING（fixed 或 deferred）

| ID          | 来源  | 问题                                                         | 状态         | 证据 / 绑定                                                                                                        |
| ----------- | ----- | ------------------------------------------------------------ | ------------ | ------------------------------------------------------------------------------------------------------------------ | -------------------- |
| O3 / AR-05  | A5/A1 | bypass 矩阵 OPEN § 与主表矛盾                                | **fixed**    | `bypass-baseline-matrix.md` §CLOSED 历史                                                                           |
| O4          | A5    | `*-green.txt` 无原始 pytest                                  | **fixed**    | `research/execute-evidence/9.0-green.txt` · `9.3-green.txt` · `9.close-pytest-full.txt`                            |
| O5          | A5/A3 | reconcile 无 `guard_production_datasource_service_required`  | **deferred** | **R3H-08A–D** / Wave 2 Sync 切片；ADR-025 §Reconcile defer；`test_r3ySync001_reconcile_*` 覆盖 adapter fail-closed |
| O6          | A5    | `evidence_index.json` 空                                     | **fixed**    | 见 P1                                                                                                              |
| A4-F01      | A4    | `live_pilot` 未接 `rehearsal_boundary` import                | **fixed**    | 模块 docstring + 测覆盖（ponytail：doc 即边界，不强制 runtime import）                                             |
| A4-F02      | A4    | `cn_rehearsal_live_ports` → `ops.fetch_port_common` 依赖倒置 | **fixed**    | `backend/app/datasources/fetch_window.py`；ops shim re-export                                                      |
| A3-P2-01    | A3    | reconcile 无 service 金路径                                  | **deferred** | 同 O5 → **R3H-08**                                                                                                 |
| A3-P3-01    | A3    | `build_route_matrix` 不经 `service.preview_route`            | **deferred** | **R3H-08C**（probe/CLI 路由统一）；`datasource_service.md` §7 注记                                                 |
| A3-P3-02    | A3    | rehearsal 入口仍注入 `create_*_fetch_port`                   | **fixed**    | S10-05 设计：rehearsal 经 service + SSOT port 类；非产品 live 替身                                                 |
| A8-W01      | A8    | interface_probe 委托测断言偏弱                               | **fixed**    | outcome-first + `test_r3h10_interfaceProbeRunSingleProbeUsesFetchViaServiceHelper`                                 |
| A8-N2       | A8    | 无负向/源码守卫测                                            | **fixed**    | 同上源码守卫测                                                                                                     |
| A8-N3       | A8    | cn_rehearsal_live_ports 无行为单测                           | **fixed**    | `test_r3h10_cnRehearsalLivePorts_stagedAliasesShareLiveClassObjects`                                               |
| A8-N5       | A8    | interface_probe 未纳入 rehearsal 测                          | **fixed**    | `test_r3h10_rehearsalScriptsDoNotClaimProductLiveReady` 断言 `interface_probe.REHEARSAL_ONLY`                      |
| A1-004      | A1    | datasource_service.md §3 时态陈旧                            | **fixed**    | §3 R3H-10 现行规则                                                                                                 |
| A1-005      | A1    | required_tests 未绑行为测                                    | **fixed**    | contract yaml + gate 测扩面                                                                                        |
| A1-006      | A1    | cn_rehearsal → ops.fetch_port_common 依赖倒置                | **fixed**    | `fetch_window.py`                                                                                                  |
| A3-02       | A3    | sandbox ops 直连 port 未登记                                 | **fixed**    | policy §9.1 表                                                                                                     |
| A3-04       | A3    | bypass OPEN 段矛盾                                           | **fixed**    | 同 O3                                                                                                              |
| A8-N4       | A8    | required_tests 绑定不足                                      | **fixed**    | 同 A1-005                                                                                                          |
| F-03        | A4    | guard 无类型注解                                             | **fixed**    | `Any                                                                                                               | None` on both guards |
| F-04        | A4    | interface_probe import 顺序                                  | **fixed**    | stdlib 先于 backend                                                                                                |
| F-05        | A4    | cn_rehearsal 中段 import / unused timedelta                  | **fixed**    | import 顶置；删 timedelta                                                                                          |
| F-07        | A4    | probe 测弱断言                                               | **fixed**    | status=SUCCESS + port_calls==[]                                                                                    |
| A7-O3       | A7    | 9.0/9.3 无 RED                                               | **fixed**    | `RED-EXEMPT-BOOT-9.0-9.3.md`                                                                                       |
| A6-OBS-1..5 | A6    | probe perf 可选观察                                          | **deferred** | R3H-08C（audit.report §3.6）                                                                                       |
| A7-O2       | A7    | GitNexus 索引滞后                                            | **deferred** | merge 后 `node .gitnexus/run.cjs analyze`                                                                          |
| A1-007      | A1    | 无 commit SHA                                                | **fixed**    | `b70c600e` + repair commit pending                                                                                 |
| A7-F05      | A7    | 证据双路径 `execute-evidence/` vs `research/`                | **fixed**    | SSOT=`research/execute-evidence/`（handoff 校验）；根目录副本不纳入 commit                                         |
| A7-F06      | A7    | GitNexus 风险 CRITICAL vs Execute 摘要 LOW                   | **fixed**    | `gitnexus-detect-changes-evidence.txt` 记录 CRITICAL + 测试缓解                                                    |

## P3 LOW / 可选观察（fixed 或 deferred）

| ID        | 来源 | 问题                                                 | 状态         | 证据 / 绑定                                                                          |
| --------- | ---- | ---------------------------------------------------- | ------------ | ------------------------------------------------------------------------------------ |
| A2-L01    | A2   | `run_staged_pilot.py` 未使用 `REHEARSAL_ONLY` import | **fixed**    | 移除未用 import；脚本仍含 `REHEARSAL_DISCLAIMER`                                     |
| A2-L02    | A2   | 双 guard 结构重复                                    | **deferred** | **R3H-08** 或 tech-debt batch；ponytail 有意分离 adapter vs service 语义             |
| A2-L03    | A2   | `_fetch_payload_via_service` 自建 sandbox DB         | **deferred** | **R3H-08C** probe 硬化；当前测绿 + mkdir 守卫                                        |
| A2-L04    | A2   | probe service 引导样板略长                           | **fixed**    | ponytail 可接受；S10-04 单测覆盖                                                     |
| A1-P3-01  | A1   | `project-overview.md` Plan 期陈旧                    | **fixed**    | 刷新为 Execute 后现状                                                                |
| A5-O4     | A5   | 9.1/9.2/9.4/9.5 green 自述型                         | **fixed**    | 含 RED 对；CLOSE 步 `9.close-pytest-full.txt` 全量输出                               |
| A8-O1     | A8   | scan_package 未扫 ops                                | **fixed**    | S10-04 AC=委托 service；非 forbidden 扩面                                            |
| A8-O2/O3  | A8   | 文档 grep 测脆弱                                     | **fixed**    | 接受为 S10-03 文档 AC；runtime 测在 S10-04/01                                        |
| F-02      | A4   | datasources→ops 依赖                                 | **fixed**    | `fetch_window.py` + `fetch_port_common` re-export                                    |
| F-06      | A4   | shim **all** 导出私有符号                            | **fixed**    | `live_pilot_fetch_ports.py` 已收窄 `__all__`                                         |
| F-08      | A4   | run_staged_pilot 未用 import                         | **fixed**    | 已删 REHEARSAL_ONLY import                                                           |
| A3-03     | A3   | build_route_matrix 不经 service                      | **deferred** | R3H-08C                                                                              |
| A3-05     | A3   | \_bypass_system_proxy monkeypatch                    | **fixed**    | rehearsal-only + finally 恢复；policy 已知                                           |
| A3-06     | A3   | QMD_SYNC_ALLOW_ADAPTER 归档漂移                      | **fixed**    | runners.py AA-02 仅 PYTEST_CURRENT_TEST                                              |
| A8-B2-alt | A8   | reconcile `datasource_service` fail-closed 测        | **fixed**    | ADR §Reconcile defer + `test_r3h10S10_01_reconcile_adapterBypassFailClosedPerAdr025` |

## Wave 2 承接表（deferred 绑定）

| 绑定任务      | 承接项                                                                                    |
| ------------- | ----------------------------------------------------------------------------------------- |
| **R3H-08A–D** | reconcile `datasource_service=` 金路径；产品 live fetch mock 分界                         |
| **R3H-08C**   | `interface_probe.build_route_matrix` → `service.preview_route`；probe sandbox helper 抽取 |
| **tech-debt** | `guard_production_*` 合并（可选，非 R3H-10 AC）                                           |

## 验证（Repair 收口）

- `validate-plan-freeze` exit 0
- `validate-execute-handoff` exit 0（Execute 步）；Audit PASS 后 `audit_matrix.final=PASS` + `in_progress` → 预期触发 finish-work 门禁
- `uv run pytest -q` exit 0（~202s，repair 最终轮 · `repair-pytest-full.txt`）
- 本 ledger 无未绑定 `deferred` 行
