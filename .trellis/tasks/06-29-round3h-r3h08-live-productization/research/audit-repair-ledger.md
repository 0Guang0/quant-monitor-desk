# Audit Repair Ledger — 06-29-round3h-r3h08-live-productization

> **Repair 关账：** 2026-06-30 · RB-01 + RB-02 · disposition 均为 **已修复**

| ID        | P   | 维  | 标题                                  | disposition | 绑定任务  | 依赖/承接             | 登记位置 / 证据                                                                                     |
| --------- | --- | --- | ------------------------------------- | ----------- | --------- | --------------------- | --------------------------------------------------------------------------------------------------- |
| A1-P1-01  | P1  | A1  | CLI live_fetch 绕过 DataSourceService | 已修复      | R3H-08-R1 | service 金路径        | `data_commands.live_fetch`→`build_product_live_service().fetch`; `test_r3h08_05_qmdDataLiveFetch_*` |
| A1-P1-02  | P1  | A1  | baostock 委托 cn_rehearsal            | 已修复      | R3H-08-R4 | S08-02                | `baostock_port` replay-only; `test_r3h08_08a_cnPrimary_productLiveOptIn[baostock]`                  |
| A1-P1-03  | P1  | A1  | coingecko 工厂缺 asset_ids            | 已修复      | R3H-08-R4 | Tier B 工厂           | `SOURCE_LIVE_DEFAULTS` asset*ids; `test_r3h08_08b_tierB*\*[coingecko]`                              |
| A1-P1-04  | P1  | A1  | tdx_pytdx 无工厂                      | 已修复      | R3H-08-R4 | Tier B 工厂           | `create_tdx_pytdx_fetch_port`; `test_r3h08_08b_tierB_*[tdx_pytdx]`                                  |
| A1-P2-01  | P2  | A1  | kalshi/poly smoke 旁路                | 已修复      | R3H-08-R2 | env gate              | product path `use_mock=False`+gate; smoke→`prediction_market_live_smoke_gate`                       |
| A1-P2-02  | P2  | A1  | BOOT 矩阵过时                         | 已修复      | R3H-08-R7 | 文档                  | `live-tier-baseline-matrix.md` LiveTierRouter **已建**                                              |
| A2-P1-001 | P1  | A2  | tier 表双轨                           | 已修复      | R3H-08-R5 | live_tier_router SSOT | `live_tier_router.py` sole SSOT; `test_r3h08_liveTierRouter_*`                                      |
| A2-P1-002 | P1  | A2  | product_live_ports 巨型工厂           | 已修复      | R3H-08-R5 | architecture §3.3     | `SOURCE_LIVE_DEFAULTS`+dynamic import                                                               |
| A2-P2-001 | P2  | A2  | 三重 ProductLiveGate                  | 已修复      | R3H-08-R5 | gate 单点             | `gate_live_fetch_port` shared helper                                                                |
| A2-P2-002 | P2  | A2  | mock-delegate 类膨胀                  | 已修复      | R3H-08-R5 | fetch_ports           | inline factory per port                                                                             |
| A2-P2-003 | P2  | A2  | CN replay 三份拷贝                    | 已修复      | R3H-08-R5 | 08A                   | `cn_product_live_replay` shared helper                                                              |
| A3-P1-01  | P1  | A3  | ProductLiveGate 不完整 ADR-027 链     | 已修复      | R3H-08-R1 | ADR-027               | `gate_live_fetch_port` env+ResourceGuard                                                            |
| A3-P1-02  | P1  | A3  | live_fetch 绕过 service               | 已修复      | R3H-08-R1 | §3.4                  | `live_fetch` dry_run=False→`build_product_live_service`                                             |
| A3-P1-03  | P1  | A3  | live_fetch 无 ResourceGuard           | 已修复      | R3H-08-R1 | sync_plan 对齐        | `test_r3h08_05_liveFetch_rejectsWhenResourceGuardHardStop`                                          |
| A3-P2-01  | P2  | A3  | Tier C smoke 旁路                     | 已修复      | R3H-08-R2 | ADR-027               | `test_r3h08_08d_tierC_productLiveGate` ProductLiveGate                                              |
| A3-P2-02  | P2  | A3  | live_fetch 无 READY                   | 已修复      | R3H-08-R1 | §3.4                  | `test_r3h08_05_liveFetch_rejectsWhenRouteNotReady`                                                  |
| A3-P1-04  | P1  | A3  | port 级无 env gate                    | 已修复      | R3H-08-R2 | 全源 gate             | `gate_live_fetch_port` in live factories                                                            |
| A3-P2-03  | P2  | A3  | datasources→ops 倒置                  | 已修复      | R3H-08-R5 | 边界矩阵              | smoke gate→`prediction_market_live_smoke_gate.py`                                                   |
| A3-P2-04  | P2  | A3  | reconcile 未绑 gated service          | 已修复      | R3H-08-R1 | ADR-025               | `test_r3h08_05_reconcile_acceptsDatasourceService`                                                  |
| A3-P3-01  | P3  | A3  | authority_graph 未登记                | 已修复      | R3H-08-R7 | loop_maintain         | `loop_maintain.py --fix` OK; datasources mapped                                                     |
| A4-P1-01  | P1  | A4  | live-fetch CLI 未接入                 | 已修复      | R3H-08-R1 | S08-05                | `main.py` live-fetch; `test_r3h08_05_qmdDataLiveFetch_cliSubprocessDryRun`                          |
| A4-P1-02  | P1  | A4  | live_fetch 无 ResourceGuard           | 已修复      | R3H-08-R1 | service 对齐          | `test_r3h08_08d_tierC_productLiveGate_resourceGuard`                                                |
| A4-P1-03  | P1  | A4  | live_fetch 无 READY                   | 已修复      | R3H-08-R1 | §3.4                  | `test_r3h08_05_liveFetch_rejectsWhenRouteNotReady`                                                  |
| A4-P1-04  | P1  | A4  | port 绕过 gate                        | 已修复      | R3H-08-R2 | 22 源                 | port factories `gate_live_fetch_port` when `use_mock=False`                                         |
| A4-P2-01  | P2  | A4  | live_fetch 绕过 service               | 已修复      | R3H-08-R1 | 金路径                | `test_r3h08_08c_serviceGoldPath_stagedFixtureModeFalse`                                             |
| A4-P2-02  | P2  | A4  | live_fetch 负向测缺口                 | 已修复      | R3H-08-R3 | 安全测                | `test_r3h08_05_liveFetch_rejectsWithoutEnv` + guard/route                                           |
| A4-P2-03  | P2  | A4  | Tier C smoke 双轨                     | 已修复      | R3H-08-R2 | smoke vs product      | product gate vs ops smoke separated                                                                 |
| A5-P1-01  | P1  | A5  | Tier B 九源缺测                       | 已修复      | R3H-08-R3 | LIVE-PROD-24          | `test_r3h08_08b_tierB_*` ×9 parametrized                                                            |
| A5-P2-01  | P2  | A5  | INDEX 缺 §2.1                         | 已修复      | R3H-08-R6 | Execute 补            | `EXECUTION_INDEX.md` §2.1 Tier 复验矩阵                                                             |
| A5-P2-02  | P2  | A5  | audit-sandbox 未建                    | 已修复      | R3H-08-R6 | basetemp              | `.audit-sandbox/.gitkeep` bootstrap                                                                 |
| A5-P2-03  | P2  | A5  | ResourceGuard AC 无测                 | 已修复      | R3H-08-R3 | S08-04                | `test_r3h08_08d_tierC_productLiveGate_resourceGuard`                                                |
| A5-P3-01  | P3  | A5  | probe 无追溯链                        | 已修复      | R3H-08-R3 | R3H-10 链接           | `test_r3h08_05_probeTracer_*` + INDEX §2.1                                                          |
| A5-P2-04  | P2  | A5  | Tier C 无 fetch_payload 测            | 已修复      | R3H-08-R3 | 08D                   | `test_r3h08_08d_tierC_productLiveFetch_payload`                                                     |
| A5-P3-02  | P3  | A5  | BOOT 矩阵漂移                         | 已修复      | R3H-08-R7 | 文档                  | `live-tier-baseline-matrix.md` LiveTierRouter 已建                                                  |
| A8-P1-01  | P1  | A8  | audit-sandbox basetemp                | 已修复      | R3H-08-R6 | mkdir                 | basetemp pytest 60 passed exit 0                                                                    |
| A8-P1-02  | P1  | A8  | 08B 九源缺测                          | 已修复      | R3H-08-R3 | WAVE2 AC              | `test_r3h08_08b_tierB_*` ×9                                                                         |
| A8-P2-01  | P2  | A8  | ResourceGuard 无测                    | 已修复      | R3H-08-R3 | S08-04                | `test_r3h08_08d_tierC_productLiveGate_resourceGuard`                                                |
| A8-P2-02  | P2  | A8  | silent-fallback 无测                  | 已修复      | R3H-08-R3 | 08C                   | `test_r3h08_08c_livePortFactory_noSilentFallbackToMock`                                             |
| A8-P2-03  | P2  | A8  | probe→service 无 tracer               | 已修复      | R3H-08-R3 | S08-05                | `test_r3h08_05_probeTracer_linksInterfaceProbeServicePath`                                          |
| A8-P2-04  | P2  | A8  | opt-in 弱断言                         | 已修复      | R3H-08-R3 | testing-guidelines    | `is_product_live_fetch_allowed()` in opt-in test                                                    |
| A8-P2-05  | P2  | A8  | 08C reject 无 code                    | 已修复      | R3H-08-R3 | 五字段                | `LIVE_FETCH_REJECTED` on 08C/Tier B/C gate tests                                                    |
| A8-P3-01  | P3  | A8  | test_catalog 空链接                   | 已修复      | R3H-08-R7 | loop_maintain         | `test_catalog.yaml`→ADR-027 + guardrails yaml                                                       |
