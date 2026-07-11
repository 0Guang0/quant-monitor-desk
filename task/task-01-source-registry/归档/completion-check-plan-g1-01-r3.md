# completion-check

- 角色：`plan`
- 日期：`2026-07-11`
- 对应 plan：`task/task-01-source-registry/task_plan.md` · `gate1-integration-spec.md` · `g1-01-wiring-inventory.md`
- 对象范围：Task-01 的 **Plan 开工声称**——按 r2 闭环修订后的 G1-01 清单是否已消除 `completion-check-plan-g1-01-r2.md` 的 CC-3/CC-4 缺口，从而使计划达到 `PLAN-READY`（可进入工作包 1、2 与 G1-02 RED）。**不**审定实现完成或 R4。
- 声称：修订后的 G1-01 清单已足以使计划成为 `PLAN-READY`。
- 权威：`MIGRATION_MAP.md` 索引的 data source / ADR-017 / `source_provenance_quality_contract.yaml`；本票 `README.md`、`task_plan.md`、`gate1-integration-spec.md`；`specs/contracts/data_cli_contract.yaml`；`pyproject.toml` console scripts。
- 正式入口：`qmd-data`、`qmd-init-db`、`qmd-sync-registry`、`qmd-ops`、`DataSourceService`、`DataSyncOrchestrator.bootstrap`、验收 spine / `ensure_isolated_db` / `skip_data_root_validation`。
- 声称档位：`product_default`、`dry_run`、`gate_live`、`override_runtime`、`staged_fixture`、`danger_skip_isolation`；不得互相升格。

> 审计方法：独立对照当前仓库；**不采信**清单 §5 自勾选与上一轮执行者摘要。GitNexus `context(sync_to_db)` + ripgrep `sync_to_db(` / `skip_data_root_validation`；Read `pyproject.toml`、`scripts/qmd_ops.py`、`acceptance_isolation.py`、`source_route_db_acceptance.py`、`source_route_db_acceptance_matrix.py`、`backend/app/cli/main.py`。本轮**不为达成 `PLAN-READY` 缩减入口集合或弱化档位边界**。测试治理：pytest 绿灯不支持本声称；E-TEST-* 仅盘点。

## 逐对象关账记录

| CC | 具体场景示范 | 本对象运行事实 | 证据 / 反证 | Verdict | 闭环控制 |
|---|---|---|---|---|---|
| CC-0 对靶 | 用户要「正式入口全量 + 档位边界诚实」的可执行蓝图；交付把「r2 五项勾完」当成完备。 | 用户目标：G1-01 可审计接线 → `PLAN-READY` → 再 RED。修订清单已覆盖 r2 点名的 packaging / 暗门 / sibling CLI / 测试 sync / E-ACC-ISO 诚实改写；但 E-ACC-SKIP-01 仍把「CLI 从不传 skip」写成事实，与矩阵正式入口不符 → 目标链在「档位边界诚实」处断裂。 | 反证：若只核对 §5 勾选即放行 READY，会把残留过陈述带进 Execute。 | **FAIL** | 拒绝当前 `PLAN-READY` 声称。门槛：E-ACC-SKIP / E-OPS-03 表述与 `qmd-ops` 单目标 vs `--all-documented-sources` 真实传参一致后再独立重审。 |
| CC-1 证伪 | 计划写了反证，执行仍可用 skip/patch 冒充正式档位。 | Plan 阶段：P-*、OVERRIDE、dry-run、`danger_skip_isolation` 均有反证方向；E-TEST-* 标明不得作发布证据。不要求本轮运行变红。 | 覆盖集合（计划设计）：选源入口 §1.2–1.5；registry 写入 E-REG-*；ops/验收 E-OPS/E-ACC-*；sibling E-CLI-40～43。反证设计：移除 override / 非隔离根 / skip 未先验校验时应可观察失败或降档。测试治理：不把 pytest 绿当作清单完备。 | PASS | Execute 须绑定命令、配置 revision、存储根与档位；测试 `sync_to_db`/monkeypatch 不得支持 G1-08。 |
| CC-2 验真 | ADR/overlay/多 Validation 仅文档存在，计划却当已交付。 | 计划诚实：overlay=`none`、capability draft、validation 列表截断归 G1-03；G1-01 是盘点非实现。 | 反证：清单未伪称能力已落地。 | PASS | 本 PASS ≠ 能力存在；实现仍须正式成功/失败链。 |
| CC-3 同路 | r2 漏登的 packaging/暗门/sibling/测试写入仍缺行。 | **已核实闭合 r2 列项：** (1) §4 + E-OPS-01～03 登记 `qmd-ops`（`db-inspect`/`data` 转发/`accept-source-route-db`）；(2) E-ACC-SKIP-01 登记 `skip_data_root_validation`；(3) E-CLI-40～43 降档 health/revision-audit/reconcile/quality-check；(4) E-TEST-01/05/06 覆盖 `service_path_support` / `test_audit_remediation` / `test_source_registry` 的 `sync_to_db`。(5) 生产 `sync_to_db` 调用方与 grep 对齐：`init_basic`、`init_db`、`sync_registry`、`bootstrap`、`ensure_isolated_db` + 测试侧。`main.py` 全部 `data` 子命令均有选源行或 §1.5b 降档行。 | 证据：`pyproject.toml` L31–34；清单 §1.5b/§1.6/§1.7/§4；grep `sync_to_db(`；`main.py` parsers。反证：再搜 packaging 仅四脚本且均入表。**残留不属「漏入口」而属档位表述：** 见 CC-4。 | PASS | 入口集合相对 r2 已列全；后续 Execute 同参横测仍属 G1-02+。 |
| CC-4 验档 | 把「约定/局部路径」写成全局保证。 | E-ACC-ISO-01 **已**诚实：API 自身不 assert，任意 `data_root` 可写。**仍 FAIL：** E-ACC-SKIP-01 写「正式 `qmd-ops accept-source-route-db` CLI **不**传此参数（默认 False）」；但 `execute_documented_matrix`（`qmd-ops … --all-documented-sources`）在已 `resolve_matrix_data_root` 后仍传 `skip_data_root_validation=cm is not None`（恒为 True）。单目标 `spine.execute` 默认 False 属实，不能概括整个 CLI。危险档位与「矩阵复用 skip」混写，Execute 可能误判正式矩阵路径为「从未 skip」或反之把已先验隔离的矩阵升格/降错档。 | 证据：`source_route_db_acceptance_matrix.py` L761–774；`qmd_ops.py` L124–134；`source_route_db_acceptance.py` L277–283；对照清单 E-ACC-SKIP-01 末句。反证：读清单会得到「CLI 永不 skip」，跑 `--all-documented-sources` 即推翻。 | **FAIL** | 改写 E-ACC-SKIP-01（及必要时 E-OPS-03）：区分 (A) 无先验 `resolve_matrix_data_root`/`assert` 的 API skip → `danger_skip_isolation`；(B) 矩阵在已 resolve 后跳过重复校验 → 仍依赖先验隔离，不得单独证明隔离，也不得写成「CLI 不传参」。然后独立重审。 |
| CC-5 对表 | 权威要求 overlay，计划靠内存 override。 | OVERRIDE→G1-02；validation 全链→G1-03；未把 override 当合法启用。 | 反证：overlay=`none` 诚实。 | PASS | design 变更仍须评审 + promote。 |
| CC-6 清债 | 盘点缺口以后再说，或 OVERRIDE 挡 READY。 | OVERRIDE 实现债属 G1-02（严格阶段后置，Plan 允许）。**CC-4 过陈述不是可后置债**——属 G1-01 盘点边界，须修清单再审。 | 反证：用「G1-02 再清」掩盖档位表述错误 → 登记不能支持当前 READY。 | PASS | 修 E-ACC-SKIP 表述后重审；OVERRIDE 仍归 G1-02 共享根因删除。 |
| CC-7 守闸 | 为 READY 掩盖未授权/隔离未强制。 | 计划保持 fail-closed、UI/G1-08 未完成；隔离 API 未强制已诚实。无外部密钥 blocker 阻止改一句清单。 | 反证：缺口可立即改文档，非客观 BLOCKED。 | PASS | `CC-7 PASS` ≠ 计划完备。 |

## Summary

- 首个决定性缺口：`CC-0` / 随即 `CC-4` — r2 点名项大体已入表，但 E-ACC-SKIP-01 仍过陈述「正式 CLI 不传 `skip_data_root_validation`」，与 `qmd-ops --all-documented-sources` → `execute_documented_matrix` 事实冲突。
- 最终状态：`PLAN-OPEN`
- 声称结论：`denied`（拒绝「修订后清单已足以 PLAN-READY」）
- 闭环控制：仅改清单档位表述（区分危险 API skip vs 矩阵先验隔离后的重复校验跳过）→ 再独立 Plan completion-check。**不得**为本轮放行而删掉暗门行或把矩阵路径升格为 `product_default`。模块实现 R4 仍为 `OPEN`。

`PLAN-READY` 仅表示计划可执行，不表示实现完成；`CLOSED`/发布仍须在 G1-08 后由独立 Execute/Audit 判定。
