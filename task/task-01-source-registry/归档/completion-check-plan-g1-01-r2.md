# completion-check

- 角色：`plan`
- 日期：`2026-07-11`
- 对应 plan：`task/task-01-source-registry/task_plan.md` · `gate1-integration-spec.md` · `g1-01-wiring-inventory.md`
- 对象范围：Task-01 的 **Plan 开工声称**——补齐后的 G1-01 清单是否已消除上一轮 `completion-check-plan-g1-01.md` 的 CC-3/CC-4 缺口，从而使计划达到 `PLAN-READY`（可进入工作包 1、2 与 G1-02 RED）。**不**审定实现完成或 R4。
- 声称：补齐后的 G1-01 清单已足以使计划成为 `PLAN-READY`。
- 权威：`MIGRATION_MAP.md` 索引的 data source / ADR-017 / `source_provenance_quality_contract.yaml`；本票 `README.md`、`task_plan.md`、`gate1-integration-spec.md`；`specs/contracts/data_cli_contract.yaml`；`pyproject.toml` console scripts。
- 正式入口：`qmd-data`、`qmd-init-db`、`qmd-sync-registry`、**`qmd-ops`**、`DataSourceService`、`DataSyncOrchestrator.bootstrap`、验收 spine / `ensure_isolated_db`。
- 声称档位：`product_default`、`dry_run`、`gate_live`、`override_runtime`、`staged_fixture`；不得互相升格。

> 审计方法：独立对照当前仓库；GitNexus `context(SourceRegistry.sync_to_db)` + ripgrep `sync_to_db(`；Read `scripts/init_db.py`、`orchestrator.bootstrap`、`acceptance_isolation.py`、`source_route_db_acceptance.py`、`scripts/qmd_ops.py`、`pyproject.toml`。不采信清单 §5 自勾选。本轮**不为达成 `PLAN-READY` 缩减入口集合或弱化档位边界**。

## 逐对象关账记录

| CC | 具体场景示范 | 本对象运行事实 | 证据 / 反证 | Verdict | 闭环控制 |
|---|---|---|---|---|---|
| CC-0 对靶 | 用户要「所有正式入口同规 + 档位不混」的可执行蓝图，交付却把「补了两个 sync 入口」当成蓝图已完备。 | 用户目标仍是：G1-01 全量可审计接线 → Plan `PLAN-READY` → 再 RED。清单已补 E-REG-03/04、E-ACC-ISO-01，但本轮声称把「局部缺口闭合」升格为「计划可开工完备」。 | 反证：上一轮 FAIL 仅是必要条件；CORE 要求列全有效入口与档位。若只验证「两行是否写上」而放过其它 console script / 隔离绕过 / 未降档子命令，即代理完成。 | **FAIL** | 拒绝「清单补缺 = PLAN-READY」。重审门槛：正式 packaging 入口、registry 写入面、策略选路面与明确降档的 sibling CLI 均有逐行 owner/档位/反证，且无过陈述边界。 |
| CC-1 证伪 | 计划写了反证，但执行时仍可用测试 patch / skip 校验冒充正式档位。 | 计划与清单为 P-*、OVERRIDE、dry-run 设计了反证方向；测试专属 monkeypatch 与部分 `sync_to_db` 夹具已部分登记。Plan 阶段不要求运行变红。 | 测试治理：本轮不把任何 pytest 绿灯当作清单完备或可开工证明。反证设计仍要求：移除 overlay / 重引 override / 跳过隔离时，正式 outcome 必须可观察变红。 | PASS | Execute 时绑定命令、配置 revision、存储根与档位；`service_path_support.sync_to_db` 等测试写入须删除/改写/迁移，不得支持 G1-08。 |
| CC-2 验真 | ADR/overlay/多 Validation 全链仅文档存在，计划却当已交付。 | 计划诚实保留 draft capability、无 overlay、Validation 仅取首项等为待实施；G1-01 是盘点而非实现。 | 反证：清单写 overlay=`none`、§2.2 记录 validation 列表截断；未伪称能力已落地。 | PASS | 实现验收仍须正式成功/失败链与持久化；本 PASS 不表示能力存在。 |
| CC-3 同路 | 补了 `qmd-init-db` 与 bootstrap，但仍有正式入口或暗门未入表。 | **已核实补上的生产 `sync_to_db` 调用方**：`init_basic`、`init_db --sync-registry`、`bootstrap`、`ensure_isolated_db`、`scripts/sync_registry.py` 均有行。**仍未闭合：** (1) `pyproject.toml` 有 console script **`qmd-ops`**，§4 表未登记；其 `accept-source-route-db` / `data` 余参可进入验收写入与 data CLI。(2) `SourceRouteDbAcceptanceSpine.execute(..., skip_data_root_validation=True)` 可跳过 `resolve_matrix_data_root` 仍走 `_bootstrap_acceptance_db`→`ensure_isolated_db`→`sync_to_db`，清单未登记该暗门。(3) `qmd data health` / `revision-audit` / `reconcile` / `quality-check` 仅在 §4 散文出现，无逐行档位/责任/反证（是否选源未降档说明）。(4) `tests/service_path_support.py` 与 `tests/test_audit_remediation.py` 亦调用 `sync_to_db`，E-TEST 未完整覆盖。 | 证据：`pyproject.toml` L31–34；`scripts/qmd_ops.py` L70–126；`source_route_db_acceptance.py` L261–283、L301–304；`acceptance_isolation.py` L61–87（**无**内置 assert）；grep `sync_to_db(`。反证：只核对上一轮两个缺口就宣称「入口全量」会被暗门与未列表 packaging 入口推翻。 | **FAIL** | 更新清单：登记 `qmd-ops`（含子命令与档位）；显式登记 `skip_data_root_validation` 绕过及其禁止升格规则；为 health/revision-audit/reconcile/quality-check 补降档行或写明「不经 RoutePlan / 不写 registry」的 N/A-POLICY 验收边界；补全测试侧 `sync_to_db` 降档。然后**独立**重跑本 Plan 审计。 |
| CC-4 验档 | 隔离 helper 被写成「调用前必须 assert」，实际 API 不强制，且存在 skip 校验。 | E-ACC-ISO-01 将存储根约束表述为「必须在调用前经 `assert_isolated_live_data_root`」；但 `ensure_isolated_db` / `_ensure_isolated_db_cached` **自身不校验**隔离，任意 `data_root` 都会 migrate + `sync_to_db`。`execute(skip_data_root_validation=True)` 进一步允许跳过 matrix 根校验。E-REG-03/04 的「实际写入」档位声明正确，但验收隔离档位边界被过陈述。 | 证据：`acceptance_isolation.py` L61–87；`source_route_db_acceptance.py` L277–283；`phase1_acceptance._prepare_phase1_connection` 直接 `ensure_isolated_db` 无本地 assert。反证：把「约定」写成「保证」会使 Execute 误用低档/错误根证据。 | **FAIL** | 改写 E-ACC-ISO-01：区分 API 真实行为 vs 调用方约定；登记 `skip_data_root_validation` 为危险档位/禁止发布证据；写清 canonical 根误用的反证。不得用「调用方应该会 assert」掩盖无强制边界。 |
| CC-5 对表 | 权威要求稳定 registry + 受控 overlay，计划允许继续靠内存 override。 | 计划仍将 OVERRIDE-MEM 归 G1-02 删除，并与 ADR-017 对齐；未把 override 当合法启用机制。Validation 全链差距归属 G1-03。 | 反证：清单未隐瞒 overlay 未实现与 validation 截断。 | PASS | design 变更仍须用户评审 + promote；本 PASS 不放行实现偏航。 |
| CC-6 清债 | OVERRIDE 只登记不删，或把入口盘点缺口当以后再说。 | OVERRIDE 生产调用方仍指向 G1-02（Plan 允许）。**入口盘点缺口不是可后置债**：CC-3/CC-4 的漏登/过陈述必须在 Plan 重开前修清单。 | 反证：用「G1-02 再清」掩盖 G1-01 盘点不完整 → 违反「登记不能支持当前关账」。 | PASS | 盘点缺口先修清单再重审 Plan；OVERRIDE 实现债留 G1-02 从共享根因消除。 |
| CC-7 守闸 | 为让计划「可开工」而忽略未授权/隔离未强制等诚实未完成。 | 计划保持 fail-closed 与 UI/G1-08 未完成门；但若批准 `PLAN-READY` 同时容忍隔离边界过陈述，会把未完成包装成可执行完备。 | 反证：无外部密钥/环境 blocker 阻止补清单；缺口是文档/盘点可立即修。 | PASS | 未授权路径继续拒绝；隔离未强制保持诚实描述。`CC-7 PASS` ≠ 计划完备。 |

## Summary

- 首个决定性缺口：`CC-0` / 随即 `CC-3` — 补齐上一轮两个 `sync_to_db` 入口后，仍把「局部闭合」升格为「入口全量 / PLAN-READY」；遗漏 `qmd-ops` packaging、`skip_data_root_validation` 暗门，以及多项 CLI 无逐行降档。
- 最终状态：`PLAN-OPEN`
- 声称结论：`denied`（拒绝「补齐后清单已足以 PLAN-READY」）
- 闭环控制：按 CC-3/CC-4 修订 `g1-01-wiring-inventory.md`（不得缩范围、不得把约定写成 API 保证），再独立重跑 Plan completion-check。仅当本文件八行均无 FAIL/UNKNOWN 时，才可判 `PLAN-READY`。模块实现 R4 仍为 `OPEN`（`completion-check-audit.md`）。

`PLAN-READY` 仅表示计划可执行，不表示实现完成；`CLOSED`/发布仍须在 G1-08 后由独立 Execute/Audit 判定。
