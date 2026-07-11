# completion-check

- 角色：`plan`
- 日期：`2026-07-11`
- 对应 plan：`task/task-01-source-registry/task_plan.md`
- 对象范围：Task-01 的 R4 实施计划，复审 G1-01 正式入口/档位/责任清单是否已消除上一轮 Plan 审计的 CC-3、CC-4 前置缺口；不审定实现完成。
- 声称：G1-01 清单已足以使计划成为 `PLAN-READY`，可进入工作包 1、2 与 G1-02 的 RED。
- 权威：`MIGRATION_MAP.md` 索引的 `docs/modules/design/data_sources.md`、`docs/decisions/design/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md`、`specs/contracts/design/source_provenance_quality_contract.yaml`、`specs/datasource_registry/source_registry.yaml`，以及本票 `README.md` / `task_plan.md` / `gate1-integration-spec.md`。
- 正式入口：`qmd-data data`（route-preview / sync / backfill / full-load / live-fetch / init-basic / scheduler / incremental）、`qmd-sync-registry`、`qmd-init-db`、`DataSourceService`、`DataSyncOrchestrator.bootstrap`；验收/测试入口另行降档登记。
- 声称档位：`product_default`、`dry_run`、`gate_live`、`override_runtime`、`staged_fixture`；不得互相升格。

> 审计方法：独立读取权威与当前源码；GitNexus 于本轮刷新至 HEAD 后执行 `query/context`；运行 `python -m pytest -q tests/test_source_registry.py tests/test_qmd_data_cli.py tests/test_sync_orchestrator.py`（exit 0）。测试仅用于核实既有可观察契约，不作为“清单已全量”或 R4 已实现的证明。

## 逐对象关账记录

| CC | 具体场景示范 | 本对象运行事实 | 证据 / 反证 | Verdict | 闭环控制 |
|---|---|---|---|---|---|
| CC-0 对靶 | 用户要所有正式数据源入口共享受控策略，交付却只列最容易看到的 CLI。 | `task_plan.md` 仍保留 R1–R10、工作包 1–6 与 G1-02～G1-08；G1-01 只是开工前的全量接线盘点，未被误报为 R4 或发布完成。 | 反证：清单和 `gate1-integration-spec.md` 均把 `override_runtime`、fixture 与 dry-run 明确排除为发布证据；本记录也不把测试绿灯升格为实现结论。 | PASS | 后续 Execute/Audit 必须仍覆盖 R1–R10 与 G1-02～G1-08；本次只否定/允许计划开工声称。 |
| CC-1 证伪 | 测试注入启用 source/domain 后仍绿，正式默认路径却会拒绝。 | 计划已为 P-DAILY / P-MINUTE / P-MACRO / P-SUPP 声明正式默认 outcome、档位、反证，并将 `service_path_support.py` 和 adapter helper 的测试专属注入列为 G1-02 处置对象。 | 当前针对性 pytest exit 0；按测试治理文件，这仅是既有回归证据。反证设计为移除受控配置、重现内存 override、或主源失败时，正式入口必须在 route plan/status/reason/事件处变红，不能由测试 patch 代替。 | PASS | G1-02 起每个新增/改写测试须绑定正式 outcome、输入、配置 revision、存储根和档位；测试专属 patch 必须删除、改写或迁移，不能用于 G1-08。 |
| CC-2 验真 | ADR 已接受、schema 已出现，但 overlay、候选链、恢复与归档仅有文档壳。 | 计划将 capability 成品、默认域可调度性、唯一策略接缝、消费者迁移、风险传播、回补归档与发布演练拆为工作包 1–6、G1-02～G1-08；当前 `draft` capability、`macro_supplementary` 无可调度 Primary、持久化 overlay 未实现均被诚实列为待实施。 | 反证：`g1-01-wiring-inventory.md` 明确 overlay 为 `none`，且列出 Validation 多源仅取首项的实际差距；没有把这些缺口伪称已实现。 | PASS | Execute 必须按正式成功/失败链、持久化、回读与消费面逐项验收；接口、计划、ADR、测试存在均不得替代实现证据。 |
| CC-3 同路 | `qmd-sync-registry` 和 `qmd-data data init-basic` 被列出，但另一个正式同步入口仍可能写入不同 registry 状态。 | G1-01 已充分登记 RoutePlan、CLI、scheduler、主要 OVERRIDE 消费者和测试注入；但其 §1.1 / §4 漏列两个当前真实的 registry 同步调用方：`qmd-init-db` → `scripts.init_db:main`（仅 `--sync-registry` 时写入）与 `DataSyncOrchestrator.bootstrap(sync_registry=True)`。 | 刷新后的 GitNexus `context(SourceRegistry.sync_to_db)` 直接列出 `init_basic`、`scripts/init_db.py:main`、`DataSyncOrchestrator.bootstrap`、验收隔离 bootstrap 等调用方；`pyproject.toml` 还登记 `qmd-init-db` console script。清单只登记前者的 `init-basic`，未给遗漏入口同参输入、策略路径、档位、存储/事件断言和反证。 | FAIL | 更新 G1-01：新增 `qmd-init-db --sync-registry`（N/A-POLICY、实际 DB 写入）与 `DataSyncOrchestrator.bootstrap(sync_registry=True)`（程序化运维 bootstrap）行；把 `_ensure_isolated_db_cached` 明确登记为验收隔离而非产品入口。每行须补 owner、输入、档位、`QMD_DATA_ROOT`/DB 目标、可观察写入及反证；随后独立重跑本 Plan 审计。 |
| CC-4 验档 | dry-run 清单看似完整，却遗漏一个直接写入真实 DB 的操作入口。 | 清单对已列的 CLI / scheduler / acceptance spine 区分了 `dry_run`、`product_default`、`gate_live`、`override_runtime` 与 `staged_fixture`；但遗漏的 `qmd-init-db --sync-registry` 和 orchestrator bootstrap 没有档位、隔离根或写入约束。 | 反证：`scripts/init_db.py` 在 `--sync-registry` 下迁移后直接执行 `sync_to_db`；这不是 `qmd-data data init-basic` 的 dry-run。未登记时，计划无法证明执行阶段不会以隔离预览冒充其真实写入行为。 | FAIL | 同 CC-3 的三行补全后，将写入入口标为实际写入档位，指定隔离/生产 DB 根、授权和回读断言；验收隔离 helper 只允许作为 `gate_live` / test evidence，不得升格为产品默认。 |
| CC-5 对表 | 权威要求稳定 registry + 持久化 overlay，计划却允许 CLI 内存 patch 继续作为启用机制。 | 计划和清单正确把 registry 基础状态、未来持久化 overlay、RoutePlan 候选链、来源/质量标签、可信最终库/连续监控区/审计归档语义与 ADR-017 对齐；所有已发现 `OVERRIDE-MEM` 消费者归入 G1-02。 | 反证：清单没有隐瞒当前 overlay 尚未实现、Validation 多源只取首项和 `use_fallback` 限制；这些均作为实施缺口而非权威偏差被处理。 | PASS | 后续涉及 design 字段、存储形态或外部契约变更时，先取得用户评审、中文 ADR 与 design→runtime promote；不得以 runtime mirror 或 override 修改反推权威。 |
| CC-6 清债 | 每个 CLI/job 各自继续 `object.__setattr__` 或覆盖 platform gate，只在台账中说以后统一。 | 对 `enabled_source_registry` 的刷新后 GitNexus context 显示的生产调用方，均已在 G1-01 §1.3–1.4 登记并指向 G1-02；测试专属同类注入也被单独登记。 | 反证：任一新增的生产 `object.__setattr__`、role 重写或 `_platform_allows` 覆盖会违反 G1-02 的删除/迁移验收，不能以本清单或测试通过关闭。遗漏的 registry 同步入口属于 CC-3/4 的盘点缺口，不被降格为技术债。 | PASS | G1-02 必须从共享策略根因消除 OVERRIDE-MEM，并对 sibling caller 重验；无 owner / 任务 ID / 再验收入口的后置不得成立。 |
| CC-7 守闸 | 缺授权或 capability 时为让计划“可跑”而默认启用，或把 sandbox 结果说成生产可用。 | 计划保持 fail-closed：默认关闭、未授权、能力不匹配或不可归一化数据均不得进入可信最终库；UI 与 G1-08 发布演练仍是未完成门。 | 反证：P-MINUTE、P-MACRO 与 P-SUPP 的拒绝/风险语义被写入清单；`override_runtime` 和 `staged_fixture` 明示不得升格。没有外部客观 blocker 阻止补齐遗漏行。 | PASS | 未授权路径继续返回受控拒绝；补齐 CC-3/4 后重审。即使转为 `PLAN-READY`，也只允许开工，不能宣称 R4、合并发布或生产上线。 |

## Summary

- 首个决定性缺口：`CC-3` — G1-01 的“全部正式入口”清单遗漏 `qmd-init-db --sync-registry` 与 `DataSyncOrchestrator.bootstrap(sync_registry=True)` 两个当前 `sync_to_db` 调用方。
- 最终状态：`PLAN-OPEN`。
- 声称结论：拒绝“G1-01 已足以令计划 `PLAN-READY`”的声称；这不是外部 blocker，也不改变模块实现/R4 仍为 OPEN 的结论。
- 闭环控制：按 CC-3 / CC-4 补齐并审阅三类遗漏（两个实际入口 + 一个验收隔离入口的降档边界），逐行声明输入、owner、策略路径、档位、DB 根、可观察写入与反证；再以刷新后的 GitNexus 和当前代码独立重跑 Plan completion-check。仅当八个 CC 行均无 FAIL/UNKNOWN 时，才可判 `PLAN-READY`。

`PLAN-READY` 仅表示计划可执行，不表示实现完成；`CLOSED`/发布仍须在 G1-08 后由独立 Execute/Audit completion-check 判定。
