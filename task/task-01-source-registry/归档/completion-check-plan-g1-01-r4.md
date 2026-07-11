# completion-check

- 角色：`plan`
- 日期：`2026-07-11`
- 对应 plan：`task/task-01-source-registry/task_plan.md` · `gate1-integration-spec.md` · `g1-01-wiring-inventory.md`
- 对象范围：Task-01 的 **Plan 开工声称**——按 r3 闭环改写 skip 表述后的 G1-01 清单，是否足以使计划达到 `PLAN-READY`（可进入工作包 1、2 与 G1-02 RED）。**不**审定实现完成或 R4。
- 声称：修订后的 G1-01 清单已足以使计划成为 `PLAN-READY`。
- 权威：`MIGRATION_MAP.md` 索引的 data source / ADR-017；本票 `README.md`、`task_plan.md`、`gate1-integration-spec.md`；`specs/contracts/data_cli_contract.yaml`；`pyproject.toml` console scripts。
- 正式入口：`qmd-data`、`qmd-init-db`、`qmd-sync-registry`、`qmd-ops`（含 `--target` / `--all-documented-sources`）、`DataSourceService`、`DataSyncOrchestrator.bootstrap`、验收 spine / `ensure_isolated_db` / 无先验隔离的 `skip_data_root_validation`。
- 声称档位：`product_default`、`dry_run`、`gate_live`、`override_runtime`、`staged_fixture`、`danger_skip_isolation`；不得互相升格。

> 审计方法：独立对照当前仓库；**不采信**清单 §5 自勾选。ripgrep `sync_to_db(` / `skip_data_root_validation`；Read `pyproject.toml`、`scripts/qmd_ops.py` L106–168、`source_route_db_acceptance.py` L261–305、`source_route_db_acceptance_matrix.py` L753–774、`acceptance_isolation.py` L61–88、`backend/app/cli/main.py` parsers。本轮**不为达成 `PLAN-READY` 缩减入口或弱化档位**。测试治理：pytest 不支持本声称；E-TEST-* 仅盘点。

## 逐对象关账记录

| CC | 具体场景示范 | 本对象运行事实 | 证据 / 反证 | Verdict | 闭环控制 |
|---|---|---|---|---|---|
| CC-0 对靶 | 用户要可执行接线蓝图，交付用勾选代替入口/档位事实。 | 用户目标：G1-01 全量可审计接线 → `PLAN-READY` → G1-02 RED。清单现含：四 packaging 脚本、全部 `qmd-data` 子命令（选源行或 §1.5b 降档）、registry 写入面、OVERRIDE 消费者、E-OPS-03a/03b 与 E-ACC-SKIP-01 的 skip 二分、同参探针 P-*、候选顺序与回补核实、责任矩阵。未把实现完成塞进本声称。 | 反证：若仍存在与源码冲突的档位绝对句，则代理完成。本轮对照源码未发现此类冲突。 | PASS | 本 PASS 仅放行计划开工；实现 R4 / G1-08 另审。 |
| CC-1 证伪 | 计划无反证，执行可用 patch/skip 冒充正式档位。 | Plan 为 P-*、OVERRIDE vs SSOT、dry-run、`danger_skip_isolation`、E-OPS-03b「skip 不单独证明隔离」设计了可观察反证方向。不要求本轮运行变红。 | 覆盖集合：§1.2–1.5 选源；E-REG-* 写入；E-OPS/E-ACC；E-CLI-40～43。反证点：非隔离根、无先验 skip、移除 override 后 outcome 应变。测试治理：E-TEST 不得支持 G1-08。 | PASS | Execute 须绑定命令、配置 revision、存储根与档位。 |
| CC-2 验真 | 把 overlay/capability/多 Validation 当已交付。 | 清单诚实：overlay=`none`、capability draft、validation 列表截断→G1-03；G1-01=盘点。 | 反证：未伪称能力落地。 | PASS | ≠ 能力存在。 |
| CC-3 同路 | packaging/暗门/sibling/`sync_to_db` 仍漏登。 | **与源码对齐：** (1) `pyproject` 四脚本均入 §4；(2) `main.py` 全部 data 子命令有选源或降档行；(3) 生产 `sync_to_db`：`init_basic`/`init_db`/`sync_registry`/`bootstrap`/`ensure_isolated_db` + 测试 E-TEST-01/03/05/06；(4) `skip` 仅 `execute` API 与 `execute_documented_matrix`；后者归 E-OPS-03b，无先验归 E-ACC-SKIP-01；(5) OVERRIDE 生产消费者在 §1.4。 | 证据：上列文件与 grep。反证：另搜 `skip_data_root_validation` 无第三生产调用方；测试无该参数调用。 | PASS | Execute 同参横测属 G1-02+；本 PASS 不证明同路已实现。 |
| CC-4 验档 | 「CLI 永不 skip」或「API 已强制隔离」过陈述。 | **r3 缺口已消除：** E-OPS-03a=`--target`、默认 skip=False、CLI 先 assert；E-OPS-03b=`--all-documented-sources` **会** skip=True，但仅在 `resolve_matrix_data_root` 之后，档位 `gate_live` 且写明 skip 不单独证明隔离；E-ACC-SKIP-01=无先验仍 skip→`danger_skip_isolation`；E-ACC-ISO-01=API 不 assert。与 `qmd_ops.py` / `matrix.py` L761–774 / `acceptance.py` L277–283 / `acceptance_isolation.py` L61–88 一致。 | 反证：再读清单找「CLI 不传 skip」类绝对句——已删除。不得把 E-OPS-03b 误标 danger，也不得把 E-ACC-SKIP 升格 gate_live。 | PASS | Execute 证据须标明先验 assert/resolve 是否发生；无先验 skip 永久禁作发布证据。 |
| CC-5 对表 | 计划允许内存 override 当正式启用。 | OVERRIDE→G1-02 删除；validation 全链→G1-03；ADR-017 差距诚实。 | 反证：未把 override 当合法启用机制。 | PASS | design 变更仍须评审+promote。 |
| CC-6 清债 | 盘点缺口后置，或 OVERRIDE 挡 READY。 | OVERRIDE/测试 monkeypatch 属 G1-02（严格阶段后置，有 owner）。**盘点档位过陈述已在本轮修清单**，无开放盘点债支撑本 READY。 | 反证：未发现仍须本轮修清单才能 READY 的漏登。 | PASS | OVERRIDE 实现债不支撑本 READY，也不阻止 Plan READY。 |
| CC-7 守闸 | 为 READY 掩盖未授权/未实现。 | fail-closed、无 overlay、UI/G1-08、capability draft 保持未完成；无外部密钥 blocker 挡计划。 | 反证：未用 mock 顶替未授权。 | PASS | `CC-7 PASS` ≠ 实现完成。 |

## Summary

- 首个决定性缺口：无
- 最终状态：`PLAN-READY`
- 声称结论：`permitted`（允许计划开工；**禁止**解读为实现 / R4 / 发布完成）
- 闭环控制：可进入工作包 1、2 与 G1-02 RED。Execute 验收须走正式入口 + 声明档位 + 同参反证；E-OPS-03b 的 skip 不得单独当隔离证明；E-ACC-SKIP-01 / E-TEST-* 不得支持 G1-08。模块 R4 仍为 `OPEN`（`completion-check-audit.md`）。

`PLAN-READY` 仅表示计划可执行，不表示实现完成；`CLOSED`/发布仍须在 G1-08 后由独立 Execute/Audit 判定。
