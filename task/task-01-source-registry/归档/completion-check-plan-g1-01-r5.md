# completion-check

- 角色：`plan`
- 日期：`2026-07-11`
- 对应 plan：`task/task-01-source-registry/task_plan.md` · `gate1-integration-spec.md` · `g1-01-wiring-inventory.md`
- 对象范围：Task-01 **G1-01 接线清单**是否足以支撑 `PLAN-READY`（可进入工作包 1/2 与 G1-02 RED）。**不**审定实现完成、R4 或 G1-08。
- 声称：当前 `g1-01-wiring-inventory.md` 已是完整、诚实、可执行的 Gate 1A 开工蓝图 → `PLAN-READY`。
- 权威：`gate1-integration-spec.md`（G1-01 交付：正式入口、fallback 顺序/窗口、责任、同参命令）；`task_plan.md` G1-01 相关；`MIGRATION_MAP.md` 索引契约；`pyproject.toml` console scripts；源码现状。
- 正式入口（本轮独立重推）：`qmd-data` / `qmd-ops` / `qmd-init-db` / `qmd-sync-registry`；`DataSourceService`；`DataSyncOrchestrator.bootstrap`；验收 spine / matrix / `ensure_isolated_db` / `skip_data_root_validation`；以及仍可调用的 ops 程序化封装（含无调用方暗门）。
- 声称档位：`product_default` · `dry_run` · `gate_live` · `override_runtime` · `staged_fixture` · `danger_skip_isolation`（不得互相升格）。

> 审计方法（对抗式 · 不继承 r4）：**不采信**清单 §5 勾选、r4 Summary、`gate1-integration-spec` 内「r4=PLAN-READY」标语。独立 ripgrep `sync_to_db(` / `skip_data_root_validation` / `enabled_source_registry`；Read `pyproject.toml`、`backend/app/cli/main.py`、`scripts/qmd_ops.py`、`acceptance_isolation.py`、`source_route_db_acceptance.py`、`source_route_db_acceptance_matrix.py`、`data_commands._gold_path_backfill_route_preview`、`source_route_matrix_bridge.py`；GitNexus `context(enabled_source_registry)`。测试治理：pytest 绿**不**支持本声称；E-TEST-* 仅盘点。

## 逐对象关账记录

| CC | 具体场景示范 | 本对象运行事实 | 证据 / 反证 | Verdict | 闭环控制 |
|---|---|---|---|---|---|
| CC-0 对靶 | 用户要可执行接线蓝图，交付用勾选/旧 PASS 代替入口事实。 | 用户目标仍是 G1-01 全量可审计接线蓝图。清单主体仍朝该目标（四 packaging、data 子命令、registry 写入、OVERRIDE、P-*、责任矩阵）。**未**把实现完成塞进本声称。但蓝图内已出现与源码冲突的策略路径陈述（见 CC-5），若据此开工会漏清债。 | 反证：信任 §5/r4 则假 READY。本轮不采信勾选；以源码对照。 | PASS | 对靶成立≠蓝图完备；完备性由 CC-3/5 否决 READY。 |
| CC-1 证伪 | 计划无反证，执行用 patch/skip 冒充正式档位。 | Plan 层：P-*、OVERRIDE vs SSOT、dry-run、`danger_skip_isolation`、E-OPS-03b「skip 不单独证明隔离」均有反证方向。不要求本轮运行变红。测试不得支撑 READY。 | 覆盖集合设计存在；但 E-CLI-20 对 OVERRIDE 范围写错会削弱「移除 override 后应变」的设计覆盖（非 fred 金路径）。仍以 CC-5 记形义偏差。 | PASS | Execute 须绑定命令/根/档位；pytest 不支撑本声称。 |
| CC-2 验真 | 把 overlay/多 Validation 当已交付。 | 清单仍诚实：overlay=`none`；validation 列表截断→G1-03；G1-01=盘点非实现。 | 反证：未伪称能力落地。 | PASS | ≠ 能力存在。 |
| CC-3 同路 | packaging/暗门/`sync_to_db`/OVERRIDE 消费者漏登。 | **已核对仍对齐：** (1) `pyproject` 四脚本；(2) `main.py` data 子命令有选源或 §1.5b 降档；(3) 生产 `sync_to_db` 五处 + 测试 E-TEST；(4) `skip` 仅 `execute` API 与 `execute_documented_matrix`；(5) §1.4 E-INC-* 覆盖多数 OVERRIDE 工厂。**本轮新发现缺口：** `backend/app/ops/source_route_matrix_bridge.py` 的 `run_matrix_spine_for_source` / `try_delegate_tier_acceptance` 可调用 `SourceRouteDbAcceptanceSpine.execute`（默认会 `resolve_matrix_data_root`；无 cm 时 `_bootstrap_acceptance_db`→`ensure_isolated_db`→`sync_to_db`），属可写 registry / 可跑验收选源的程序化入口；全库无调用方，但**未入表也未 N/A-POLICY/dead 降档**。同级 helper（`ensure_isolated_db`）已登记，本暗门未登 = 入口集合不闭合。 | 证据：Read bridge L21–62；rg 仅自身命中。反证：若「零调用即可省略」成立，则任何可 import 写库暗门都可永久漏登——与 G1-01「列出所有正式入口」及本契约冲突。 | FAIL | 补行（含档位/反证）或显式降档（dead/N/A-POLICY + 删除条件）后重审；禁止口头「没人用」。 |
| CC-4 验档 | 「CLI 永不 skip」或「API 已强制隔离」过陈述。 | 复读 E-OPS-03a/03b、E-ACC-SKIP-01、E-ACC-ISO-01：与 `qmd_ops.py` L124–161、`matrix.py` L761–774（`skip_data_root_validation=cm is not None`）、`acceptance.py` L277–283、`acceptance_isolation.py` L61–88 **一致**。E-OPS-03b 的 `gate_live` 依赖先验 assert/resolve，skip 不单独证明隔离——诚实保留。 | 反证：未发现新的「API 自带隔离」绝对句。 | PASS | Execute 证据须标明先验是否发生。 |
| CC-5 对表 | 计划策略路径/OWNER 与源码形义不符。 | **决定性偏差：** E-CLI-20 策略路径写作 `OVERRIDE-MEM（fred 专用 builder）`。源码 `data_commands._gold_path_backfill_route_preview`：fred 走 `build_fred_incremental_preview_service`；**else 对任意非 fred `source_id` 同样** `enabled_source_registry(...)` + `planner._platform_allows = lambda: (True,None)`。GitNexus `context(enabled_source_registry)` 将 `_gold_path_backfill_route_preview` 列为生产调用方。蓝图「fred 专用」与源码冲突 → G1-02 可能只拆 fred builder、漏清 backfill 全金路径 OVERRIDE。**次要偏差：** E-ACC-01 写「baostock 专用 builder」，但 matrix `preview_route_payload`→`load_incremental_route_bundle` 对 **含 baostock 在内的全部** matrix 目标预览均为 OVERRIDE；live baostock 才是专用 builder。E-INC-BUNDLE 间接覆盖共享根，但 E-ACC-01 行内形义仍易误导。 | 证据：`data_commands.py` L304–331；`source_route_db_acceptance_matrix.py` L380–411；GitNexus callers。反证：若按清单字面只清 fred backfill override，非 fred `qmd-data data backfill` 仍 OVERRIDE-MEM。 | FAIL | 修正 E-CLI-20（及必要时 E-ACC-01/§1.4）策略路径为「全金路径 OVERRIDE」并与源码锚点一致后重审。 |
| CC-6 清债 | 盘点缺口后置，或把可修清单债当 READY。 | OVERRIDE 实现债→G1-02（严格阶段后置，有 owner）仍可接受。**本轮盘点事实错误与漏登属于清单自身可修债**，不得在未修时宣称 PLAN-READY。本报告以 FAIL 拒绝 READY，而非把缺口登记后仍放行。 | 反证：未用「NON-BLOCKING」放过 CC-3/5。 | PASS | 修复清单缺口是重入 Plan 的门槛，不是阶段外置实现债。 |
| CC-7 守闸 | 为 READY 掩盖未授权/未实现。 | overlay 未实现、OVERRIDE 待删、validation 截断、UI/G1-08 保持未完成；无用 mock 顶替未授权。无外部密钥 blocker 挡计划盘点。 | 反证：未发现用替身补绿计划缺口。 | PASS | `CC-7 PASS` ≠ 计划完备或实现完成。 |

## Summary

- 首个决定性缺口：`CC-5` — E-CLI-20 将 backfill 标成「fred 专用」OVERRIDE，源码对非 fred 金路径同样 `enabled_source_registry` + 强制 `_platform_allows`
- 最终状态：`PLAN-OPEN`
- 声称结论：`denied`（拒绝 `PLAN-READY`）
- 闭环控制：在 `g1-01-wiring-inventory.md` 中 (1) 按源码修正 E-CLI-20（及交叉引用）策略路径与反证覆盖；(2) 为 `source_route_matrix_bridge` 补正式行或 N/A-POLICY/dead 降档（含删除条件）；(3) 建议澄清 E-ACC-01 preview=OVERRIDE（含 baostock）vs live baostock builder 双轨；然后重新跑独立 Plan completion-check。**禁止**用 pytest 绿或勾选 §5 证明 READY。

`PLAN-READY` 仅表示计划可执行，不表示实现完成。本轮 **无** `PLAN-READY`。Summary 不覆盖行级 FAIL。
