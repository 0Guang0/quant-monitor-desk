# completion-check

- 角色：`plan`
- 日期：`2026-07-11`
- 对应 plan：`task/task-01-source-registry/task_plan.md` · `gate1-integration-spec.md` · `g1-01-wiring-inventory.md`
- 对象范围：Task-01 **G1-01 接线清单**是否足以支撑 `PLAN-READY`（可进入工作包 1/2 与 G1-02 RED）。**不**审定实现完成、R4 或 G1-08。
- 声称：修订后的 `g1-01-wiring-inventory.md` 已是完整、诚实、可执行的 Gate 1A 开工蓝图 → `PLAN-READY`。
- 权威：`gate1-integration-spec.md`（G1-01：正式入口、fallback 顺序/窗口、责任、同参命令）；`task_plan.md`；ADR-017 / **ADR-018**；`MIGRATION_MAP.md` 索引契约；`pyproject.toml`；源码现状。
- 正式入口（本轮独立重推）：`qmd-data` / `qmd-ops` / `qmd-init-db` / `qmd-sync-registry`；`DataSourceService`；`DataSyncOrchestrator.bootstrap`；验收 spine / matrix / `ensure_isolated_db` / `skip_data_root_validation`；`source_route_matrix_bridge`；§1.4 OVERRIDE 工厂。
- 声称档位：`product_default` · `dry_run` · `gate_live` · `override_runtime` · `staged_fixture` · `danger_skip_isolation`（不得互相升格）。

> 审计方法（对抗式 · **不继承** r5 行级 verdict，只把 r5 闭环控制当「须核对的修复项」）：**不采信**清单 §5 勾选、progress 口头「已修订」、gate1 状态标语。独立核对：`pyproject.toml` 四脚本；`main.py` 全部 data 子命令；`data_commands._gold_path_backfill_route_preview` L304–331；`source_route_matrix_bridge.py`；rg `sync_to_db(` / `skip_data_root_validation` / `def enabled_.*_source_registry`；matrix `preview_route_payload`→`load_incremental_route_bundle`；ADR-018 + `T01-ENABLE-FRED-MERGE-001`。pytest 绿**不**支持本声称。

## 逐对象关账记录

| CC | 具体场景示范 | 本对象运行事实 | 证据 / 反证 | Verdict | 闭环控制 |
|---|---|---|---|---|---|
| CC-0 对靶 | 用户要可执行接线蓝图，交付用勾选/旧 PASS 代替入口事实。 | 用户目标仍是 G1-01 全量可审计接线蓝图（入口、策略路径、档位、反证、责任、同参）。清单含四 packaging、选源 CLI、sibling 降档、registry 写入、OVERRIDE 全表、P-*、责任矩阵、ADR-018 overlay=`none`。**未**把实现完成或 R4 塞进本声称；标题状态写明须独立重审。 | 反证：仅信 §5 勾选则假 READY。本轮以源码对照，不采信勾选。目标链完整。 | PASS | 对靶成立；完备性由 CC-3/5 独立判定。 |
| CC-1 证伪 | 计划无反证，执行用 patch/skip 冒充正式档位。 | Plan 层已为 P-*、OVERRIDE vs SSOT、E-CLI-20「只清 fred 漏 else」、E-OPS-03b「skip 不单独证明隔离」、E-ACC-SKIP-01 `danger_skip_isolation`、bridge 零调用仍须处置设计反证方向。不要求本轮运行变红。 | 覆盖集合：正式入口 + 暗门 + 档位升格禁令。测试不得支撑 READY。 | PASS | Execute 须绑定命令/根/档位；pytest 不支撑本声称。 |
| CC-2 验真 | 把 overlay/多 Validation 当已交付。 | 清单诚实：overlay=`none（ADR-017/018 待 G1-02）`；validation 列表截断→G1-03；G1-01=盘点非实现；OVERRIDE→G1-02。 | 反证：未伪称开关本或两层接缝已落地。 | PASS | ≠ 能力存在；≠ 实现关账。 |
| CC-3 同路 | packaging/暗门/`sync_to_db`/OVERRIDE 漏登。 | **已独立核对闭合：** (1) `pyproject` 四脚本 ↔ §4；(2) `main.py` 全部 data 子命令有选源行或 §1.5b 降档；(3) rg `sync_to_db(`：生产/运维=init_basic、init_db、sync_registry、acceptance_isolation、orchestrator.bootstrap；测试=E-TEST-*；(4) `skip_data_root_validation` 仅 `execute` API + `execute_documented_matrix` ↔ E-ACC-SKIP / E-OPS-03b；(5) 全部 `enabled_*_source_registry` 工厂 ∈ §1.4 或共享 ESR（E-INC-BUNDLE / E-CLI-13/20）；(6) **r5 缺口已消：** `E-ACC-BRIDGE-01` 登记 `run_matrix_spine_for_source` / `try_delegate_tier_acceptance`（零外部调用、可写 registry、删除/迁移条件）。rg 仅 bridge 自身命中，与「dead 可调用面」一致。 | 反证：再搜可写 registry / OVERRIDE 暗门——未发现新的未登程序化入口。 | PASS | G1-02 须按表清 OVERRIDE；bridge 须按删除条件处置，不得口头漏登。 |
| CC-4 验档 | 「CLI 永不 skip」或「API 已强制隔离」过陈述。 | E-OPS-03a/03b、E-ACC-SKIP-01、E-ACC-ISO-01、E-ACC-BRIDGE-01 档位与源码一致：CLI 先验 resolve；matrix 在 resolve 后传 skip=True；无先验 skip=`danger_skip_isolation`；`ensure_isolated_db` 不内置 assert。E-CLI-20 档位含 `override_runtime`，不升格 `product_default`。 | 反证：未发现新的过陈述绝对句。 | PASS | Execute 证据须标明先验是否发生。 |
| CC-5 对表 | 计划策略路径与源码形义不符。 | **r5 CC-5 已对齐源码：** E-CLI-20 = **OVERRIDE-MEM（全金路径）**：fred+`macro_series`→`build_fred_incremental_preview_service`；else→`enabled_source_registry`+`_platform_allows=True`（`data_commands.py` L304–331）。明确「不是仅 fred 专用」。E-ACC-01：matrix preview 经 `build_incremental_preview_service`→`load_incremental_route_bundle`（**含 baostock**）= OVERRIDE；live baostock 另轨。E-INC-FRED：编排壳≠第二套启用权威；挂钩 ADR-018 / `T01-ENABLE-FRED-MERGE-001`（待修复清单有行）。§2 候选/回补与 YAML/ADR 差距归属诚实。 | 反证：若仍写「fred 专用」则 FAIL——当前正文已改。形似反证：只清 fred 分支漏 else → 清单反证列已点名。 | PASS | 实现须按全金路径清 OVERRIDE；不得只拆 fred builder。 |
| CC-6 清债 | 盘点缺口后置，或把可修清单债当 READY。 | r5 清单自身债（E-CLI-20 错述、bridge 漏登、E-ACC-01 易误导）**已在清单正文修复**，属本轮 Plan 闭环，非阶段外置。OVERRIDE 实现债 / overlay / FRED 合并 → G1-02～G1-08（ADR-018 严格阶段后置，有 owner/台账）。本轮无新增未登入口债。 | 反证：未用「NON-BLOCKING」放过可修清单错。 | PASS | 实现债不支撑 READY；READY 仅=蓝图可执行。 |
| CC-7 守闸 | 为 READY 掩盖未授权/未实现。 | overlay 未实现、OVERRIDE 待删、validation 截断、UI/G1-08、FRED 合并最迟 G1-08 保持未完成；无 mock 顶替。无外部密钥 blocker 挡计划盘点。清单**未**自勾 PLAN-READY。 | 反证：未发现用替身补绿计划缺口。 | PASS | `CC-7 PASS` ≠ 实现完成；仅表示延期诚实。 |

## Summary

- 首个决定性缺口：`none`
- 最终状态：`PLAN-READY`
- 声称结论：`permitted`（允许进入 G1-02 / 工作包 RED；**禁止**解读为实现或 R4 完成）
- 闭环控制：G1-01 计划关账成立。下一步以清单 §1–§3 为开工蓝图开 G1-02 RED（两层接缝 / 清 OVERRIDE，含 E-CLI-20 全金路径与 E-ACC-BRIDGE-01 处置）。Execute/Audit 须独立跑；pytest 绿与 §5 勾选不得单独证明实现关账。

`PLAN-READY` 仅表示计划可执行，不表示实现完成。Summary 不覆盖行级事实；本轮八行无 FAIL/UNKNOWN。
