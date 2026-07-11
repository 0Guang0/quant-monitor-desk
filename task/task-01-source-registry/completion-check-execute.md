# completion-check

- 角色：`execute`
- 日期：`2026-07-11`
- 对应 plan：`task/task-01-source-registry/task_plan.md` 工作包 3 · 3A；票 `.scratch/task-01-g1-02-enable-seam/issues/03-ask-activation-overlay.md`
- 对象范围：票 **03** 仅「问开关 API + `source_activation_overlay` 持久化（隔离根可测）」；**不含** 3B 安检接线、3C/E-TEST 夹具迁移、4a/4b/4x ESR 清零、G1-02 整切片、模块 R4、3-OBS 遥测管道、管理员撤销 CLI
- 声称：票 03 AC 执行关账（≠ G1-02 CLOSED / ≠ R4）
- 权威：ADR-018 · `docs/modules/design/data_sources.md` §5.2.1 · `g1-02-execution-brief.md` §1.1 / §6 3A · 票 03 AC
- 正式入口：`ask_activation` / `write_activation_overlay`（库 API 接缝）+ `apply_migrations`→`017_source_activation_overlay`；**尚未**成为 CLI/RoutePlanner 生产调用面（属票 04+）
- 声称档位：`product_default`（无 overlay 拒绝 P-MACRO）+ `sandbox`（隔离根正规 overlay 允许）；非 live / 非 G1-08

## 逐对象关账记录

### 对象 A · 票 03 问开关 + overlay 持久化

| CC        | 具体场景示范                                         | 本对象运行事实                                                                                                                                                                            | 证据 / 反证                                                                                                                                                                               | Verdict | 闭环控制                                                             |
| --------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | -------------------------------------------------------------------- |
| CC-0 对靶 | 用户要业务表与审计表一致，交付只证明 job `COMPLETED` | 用户要票 03：三键→三字段、§5.2.1 表、隔离根可测、禁 setattr/force 后门。交付即该接缝，未把 pytest 绿或 G1-02 整包冒充目标                                                                 | 票 03 AC 四条；实现 `activation_overlay.py` + `017_*.sql`；明确不声称 ESR 迁移                                                                                                            | PASS    | 关账仅票 03；升格 G1-02/R4 须新 claim                                |
| CC-1 证伪 | 集成测注入 `fetch_port` 且只断言无异常               | 覆盖集合：①三字段契约 ②setattr 不放行 ③sandbox overlay 允许 vs 产品库拒绝 ④overlay.enabled=false 拒 ⑤base 启用允许 ⑥sandbox 标记强制 ⑦迁移建表。删除 overlay 行后同参重回 DISABLED_SOURCE | `uv run pytest -q tests/test_activation_overlay.py tests/test_schema_migration.py` 绿；手工 `DELETE FROM source_activation_overlay` → `DISCRIMINATION_OK`；已删 meta-testing `hasattr` 测 | PASS    | 再引入内存读 `SourceRecord.is_enabled` 或忽略 overlay 时上述测必须红 |
| CC-2 验真 | 权威要求校验→双写→回读，实现只转状态                 | 原子：迁移建表、write 落库（operator/time/reason/revision）、ask 回读最新未撤销、无 force_enable。撤销**列**已齐；撤销**API**/3-OBS/安检接线不在本票 AC                                   | 表可 INSERT/SELECT；ask 读 DB 非内存；`sandbox=True` 无标记 → ValueError                                                                                                                  | PASS    | 本 claim 不含 revoke CLI / RoutePlanner 接线；若声称含之则改 FAIL    |
| CC-3 同路 | CLI 用 overlay 启用可写，scheduler 读默认 registry   | 声称入口仅库 API 问开关；生产 CLI/增量仍走 ESR（**范围外**，票 06–08）。同库 ask 同参一致；产品库 vs 沙箱库分裂是**有意档位差**非入口分裂                                                 | inventory 仍列 ESR；本票未改 `enabled_source_registry`（CRITICAL，有意不迁）                                                                                                              | PASS    | 若声称「正式 CLI 已同路」→ FAIL；当前声称未含                        |
| CC-4 验档 | 报告标 live，fetch_id 含 replay                      | 证据分档：product_default 无 overlay 拒 P-MACRO；sandbox 隔离路径写 `[sandbox]` overlay 后允许。未标 live/product-enabled                                                                 | 双 DuckDB 路径测试；`sandbox=True` 强制 reason 含 sandbox                                                                                                                                 | PASS    | 禁止用 sandbox 允许升格「产品已默认启用」                            |
| CC-5 对表 | 权威失败码被吞成 exit 0                              | 形：DDL 对齐 §5.2.1 字段；义：拒绝=`DISABLED_SOURCE`（ERROR_CODE_GUIDE），允许 reason 空串不自造成功码；行为：最新未撤销 overlay 优先于 DB base；效果：P-MACRO 产品拒 / 沙箱允            | design DDL vs `017_*.sql` / `schema.sql`；测试断言 reason_code                                                                                                                            | PASS    | 改 DDL 字段须再审阅 design；本轮未改 design 语义                     |
| CC-6 清债 | 三处 monkeypatch 代替共享根因                        | 本轮修：删 meta-testing hasattr；补 overlay deny / base allow / sandbox 标记；纠正 INGESTION_TABLES 漂移。ESR 旁路属后续票，非本轮可关且未用来支撑本 claim                                | 测试文件 diff；impact(ESR)=CRITICAL → 不在本切片强迁                                                                                                                                      | PASS    | ESR/3B/3C 严格后置票 04–08；不支撑本 claim CLOSED 以外对象           |
| CC-7 守闸 | 缺密钥切 mock 仍报 live PASS                         | 诚实未完成：RoutePlanner 消费、CLI 迁出 ESR、E-TEST 夹具、FRED 合并、模块 R4、撤销管理 CLI、3-OBS 日志管道。状态保持 OPEN 于更大对象                                                      | HANDOFF / brief 依赖图；台账 `T01-ENABLE-FRED-MERGE-001`                                                                                                                                  | PASS    | CC-7 PASS≠G1-02 完成；更大对象仍 OPEN                                |

## Summary

- 首个决定性缺口：none（修复后：原 meta-testing / 缺 deny 路径 / sandbox 标记未强制 / INGESTION 断言漂移已闭环）
- 最终状态：`CLOSED`
- 声称结论：`permitted`（**仅**票 03 AC）
- 闭环控制：再验入口 = `uv run pytest -q tests/test_activation_overlay.py tests/test_schema_migration.py`；人为删 overlay 行或去掉 sandbox 标记校验须使对应断言失败；不得将本记录当作 G1-02 / R4 / ESR 清零关账

## 测试资产治理（TEST-EVIDENCE-GOVERNANCE）

| 资产                                                        | 角色                | 处置                           |
| ----------------------------------------------------------- | ------------------- | ------------------------------ |
| `test_askActivation_returnsThreeFieldDecision`              | 核心契约            | 保留                           |
| `test_askActivation_baseEnabledSource_allowsWithoutOverlay` | 核心 / 回落 base    | 保留                           |
| `test_askActivation_ignoresInMemorySetattrBypass`           | 回归 / 禁撬门       | 保留                           |
| `test_sandboxOverlay_allowsWhileProductDefaultStillDenies`  | 核心 / 档位         | 保留                           |
| `test_overlayEnabledFalse_deniesEvenWhenBaseEnabled`        | 核心 / 正规拒绝     | 保留（替原 hasattr meta-test） |
| `test_writeSandboxOverlay_requiresSandboxMarker`            | 边界 / ADR-018 标记 | 保留                           |
| `test_migrationCreatesSourceActivationOverlayTable`         | contract / 迁移     | 保留                           |
| 原 `test_activationOverlay_moduleHasNoForceEnableBackdoor`  | meta-testing        | **已删除**                     |
