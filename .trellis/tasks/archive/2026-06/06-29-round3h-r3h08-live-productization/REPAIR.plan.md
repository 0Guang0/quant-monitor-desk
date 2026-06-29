# Repair 计划 — R3H-08 Live Productization

> **输入：** `audit.report.md` · `research/audit-repair-ledger.md`（42 项 **待修复**）  
> **原则：** 全部 P1–P3 **必须修根因**；**禁止**阶段外置/defer；禁止 wrapper/改测试目的换绿  
> **工程契约：** ponytail · TDD（正式代码 RED→GREEN）· 五字段 docstring · GitNexus `impact()` 改 symbol 前

## 0. 元信息

| 字段         | 值                                        |
| ------------ | ----------------------------------------- |
| slug         | `06-29-round3h-r3h08-live-productization` |
| Execute base | `2f75a035`                                |
| Audit        | FAIL · A7 PASS only                       |

## 1. 切片（串行 · 一 agent 一片）

### RB-01 后端根因（R1+R2+R4+R5）

**关账 findings：** A1-P1-01..04 · A1-P2-01 · A2-P1-001/002 · A2-P2-001/002/003 · A3-P1-01..04 · A3-P2-01..04 · A4-P1-01..04 · A4-P2-01/03

| 修复                          | 根因动作                                                                                                                                       |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `live_fetch` + CLI            | `main.py` 注册 `live-fetch`；`dry_run=False` 经 `build_product_live_service().fetch`；guard HARD_STOP/PAUSE fail-closed；`route_status==READY` |
| ProductLiveGate ADR-027       | gate 模块或 service 入口串联 env+guard+staged 契约（与 `service.fetch` 对齐）                                                                  |
| port 级 gate                  | `create_*_fetch_port(..., use_mock=False)` 入口 `assert_product_live_allowed`（共享 helper）                                                   |
| `product_live_ports` ponytail | 删 `TIER_*_08x` 双轨；删 `ProductLiveGatedPort` 三重 gate；`SOURCE_LIVE_DEFAULTS`+动态 import；coingecko `asset_ids`；tdx_pytdx 工厂           |
| baostock                      | 禁止 import `cn_rehearsal`；replay-only 或 QMD 网络路径                                                                                        |
| kalshi/poly                   | 产品 `use_mock=False` 路径移除 smoke fallback；smoke 保留 ops 入口                                                                             |
| fetch_ports 简化              | mock-delegate 类内联 factory；CN replay 抽共享 helper                                                                                          |
| reconcile                     | `runners.py` 生产 profile 下 gated service 契约或文档化+检测                                                                                   |
| datasources→ops               | kalshi/poly smoke 逻辑下沉 datasources 或注入，去掉 port→ops import                                                                            |

**允许文件：** `backend/app/datasources/**` · `backend/app/cli/**` · `backend/app/sync/runners.py` · `backend/app/sync/orchestrator.py`（若需）

**验证：** `uv run pytest tests/test_r3h08_live_productization.py -q`（RB-01 后至少不回归）

### RB-02 测试+文档+关账（R3+R6+R7 + 测试侧 A4/A5/A8）

**关账 findings：** A1-P2-02 · A3-P3-01 · A4-P2-02 · A5-_ · A8-_ · A5-P2-02/A8-P1-01 basetemp

| 修复                                           | 根因动作                                                                                                          |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Tier B 九源测                                  | akshare/stooq/coingecko/eastmoney/sina_finance/tdx_pytdx/ths_ifind/qmt_xtdata/qmt_xqshare parametrized gate+fetch |
| ResourceGuard / silent-fallback / probe tracer | 五字段新测；probe 薄守门或 INDEX 链接 `test_interface_probe_018c.py`                                              |
| 弱断言                                         | `LIVE_FETCH_REJECTED` code；opt-in 副作用断言                                                                     |
| Tier C fetch_payload                           | kalshi/poly mock fetch 测                                                                                         |
| `.audit-sandbox/`                              | 任务目录 `mkdir` + `.gitkeep`                                                                                     |
| `EXECUTION_INDEX.md` §2.1                      | Tier A/B/C 复验命令表                                                                                             |
| `live-tier-baseline-matrix.md`                 | LiveTierRouter 已建                                                                                               |
| loop                                           | `loop_maintain.py --fix` · test_catalog 链接 ADR-027                                                              |
| ledger                                         | 42 行 disposition → **已修复** + 证据列                                                                           |
| `audit.report.md` §5                           | Repair 复验 PASS 记录                                                                                             |

**允许文件：** `tests/test_r3h08_live_productization.py` · `.trellis/tasks/06-29-round3h-r3h08-live-productization/**` · `docs/**` · `specs/**` · `tests/test_catalog.yaml` · `docs/generated/*`

**验证：**

```bash
uv run pytest tests/test_r3h08_live_productization.py -q --basetemp=.trellis/tasks/06-29-round3h-r3h08-live-productization/.audit-sandbox/pytest
uv run pytest -q
python .trellis/scripts/task.py validate-repair-close .trellis/tasks/06-29-round3h-r3h08-live-productization
```

## 2. Skill 冻结

| Skill                        | 绑定         |
| ---------------------------- | ------------ |
| `agents/repair-boot-v4.1.md` | Boot         |
| `/test-driven-development`   | 正式代码     |
| `/testing-guidelines`        | 测试五字段   |
| `/karpathy-guidelines`       | 代码风格     |
| GitNexus `impact()`          | 改 symbol 前 |

## 3. Deferred

**无** — 用户要求全部 P0–P3 修复。

## 4. DoD

- [ ] ledger 42 行 **已修复**，无待修复
- [ ] `uv run pytest -q` exit 0
- [ ] `validate-repair-close` exit 0
- [ ] audit.report §5 已更新
