# Plan Boot — R3H-03 CN Market Adapters

> **Phase P0 complete** · 2026-06-28

## 批次定位

| 项           | 值                                                                                  |
| ------------ | ----------------------------------------------------------------------------------- |
| Batch        | `ROUND_3_REAL_DATA_PRODUCTION_ENTRY` / Batch 3H                                     |
| Task ID      | `R3H-03`                                                                            |
| Trellis slug | `06-28-round3h-r3h03-cn-market`                                                     |
| 分支         | `feature/round3h-r3h03-cn-market`                                                     |
| Worktree     | `../quant-monitor-desk-wt-r3h03`                                                      |
| 协议         | v4 (`plan_protocol_version: "4"`)                                                   |
| 前置         | R3H-01 CLOSED、R3H-02 CLOSED @ 2026-06-28；Batch 3G CLOSED                          |
| 并行轨       | R3H-04（kalshi/polymarket/web_search）— 禁止互改 source 行                            |
| 禁止提前     | **R3H-05** 全层审计；主库 `quant_monitor.duckdb` 写入（无 gate/ADR）                  |

## 已读 P0 输入

| #   | 文件                                                 | 摘要                                                       |
| --- | ---------------------------------------------------- | ---------------------------------------------------------- |
| 1   | `agent-toolchain.md`                                 | GitNexus impact/query；v4 冻结三件套                       |
| 2   | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                 | 3H 为 Round4 前必经；历史索引                              |
| 3   | `docs/implementation_tasks/README.md`                | Round 3H 执行入口                                          |
| 4   | `TASK_INPUT_CONTEXT_INDEX.md`                        | Plan-only 上下文桥                                         |
| 5   | `GLOBAL_EXECUTION_RULES.md`                          | 全局执行边界                                               |
| 6   | `GLOBAL_TESTING_POLICY.md`                           | TDD 五字段                                                 |
| 7   | `GLOBAL_RESOURCE_LIMITS.md`                          | ResourceGuard / eco-mode                                   |
| 8   | `GLOBAL_TASK_TEMPLATE.md`                            | §9 结构                                                    |
| 9   | `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/README.md`       | 全源 READY 或 ADR                                          |
| 10  | `BATCH_3H_TASK_CARD_MANIFEST.md`                     | R3H-03 十源；并行规则                                      |
| 11  | `BATCH_3H_COORDINATOR_PLAYBOOK.md`                   | 本轨 ownership + registry 合并                             |
| 12  | `BATCH_3H_HARDENING_RULES.md`                        | 禁止微切片 closure                                         |
| 13  | `R3H_03_CN_MARKET_ADAPTERS.md`                       | 活任务卡（已加固 §7–§15）                                  |
| 14  | `PROJECT_IMPLEMENTATION_ROADMAP.md` §5               | G11/G16→R3H-03；当前下一入口                               |
| 15  | `R3G_MASS_REHEARSAL_OPEN_GAPS.md`                    | G11 baostock、G16 cninfo/akshare 开放项                    |
| 16  | `specs/contracts/reference_adoption_guardrails.yaml` | L1/L2/L3 采纳阶梯                                          |
| 17  | `.cursor/skills/trellis-plan/SKILL.md`               | v4 流程                                                    |

## 3G→3H 首切片（G11/G16）

**G11：** baostock 经 3G `--live-wire` 可写 pilot，但无产品化 `baostock_port` + 统一 `cn_market` evidence；DH 仍可能依赖 bridge sidecar。

**G16：** cninfo/akshare 在 3G 为 fixture/validation 样本；无 `cninfo_port`/`akshare_port` L2 产品化边界。

**R3H-03 目标：** 十源各自 fetch port（或 tested authorization-disabled）+ `cn_market` normalizer + `license_gate` + route/replay/evidence；吸收 G11/G16，**不**扩展 R3H-05 全层审计。

## 基线（Plan 1a 摘要）

| 维度              | 当前                                                                 |
| ----------------- | -------------------------------------------------------------------- |
| fetch ports       | 仅 `tdx_pytdx_port.py`（R3FR-03）；其余九源 **无** L2 port          |
| adapters/         | `baostock`/`akshare`/`cninfo`/`qmt_xtdata` 为 **skeleton**           |
| staged pilot      | `ops/staged_pilot_fetch_ports.py` 含 cninfo/baostock staged 逻辑   |
| normalizer        | **无** `cn_market.py`；TDX 有 `normalizers/tdx.py`                 |
| license_gate      | **无** `datasources/auth/license_gate.py`                          |
| 测试              | **无** `test_cn_market_adapters.py`；有 `test_tdx_provider_port.py` |
| registry          | 十源已登记；多数非 `READY_WITH_EVIDENCE` 产品化终态                  |

## 任务边界（一句话）

将中国市场的 10 个 source（baostock…qmt_xqshare）从 skeleton/staged/proposed-disabled 推进到 `READY_WITH_EVIDENCE` 或 `ADR_DISABLED_OUT_OF_SCOPE`；QMT/iFinD/xqshare 默认 authorization-disabled。

## 明确不做

- 写主库 `quant_monitor.duckdb`
- 运行时 import `参考项目/**`
- 修改 R3H-04 拥有的 source（kalshi, polymarket, web_search）
- R3H-05 全层 production-entry audit
- 全市场/全历史/分钟级默认扫描

## GitNexus（Plan 1a/1b）

- `query("CN market baostock cninfo fetch port")` — 命中 `staged_pilot_fetch_ports.CninfoMetadataStagedFetchPort`、`DataSourceService.fetch`、`test_adapter_skeletons`
- `context(tdx_pytdx_port)` — **索引未命中**（worktree 有 `tdx_pytdx_port.py`；Execute boot 可 `node .gitnexus/run.cjs analyze` 刷新）
- 静态：`ops/staged_pilot_fetch_ports.py` 为 baostock/cninfo 迁移源

## context_pack

```bash
uv run python scripts/context_router.py --task .trellis/tasks/06-28-round3h-r3h03-cn-market
```

## Phase 3（grill-me）

- 产出：`research/grill-me-session.md`（**Phase 3 complete**）
- 追溯：`research/original-plan-trace.md`
