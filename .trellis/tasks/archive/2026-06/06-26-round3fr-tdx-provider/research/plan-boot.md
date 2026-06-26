# Plan Boot — R3FR-03 TDX Provider Refactor

> **Phase P0 complete**

## 用户目标

将现有 TDX/pytdx 探针代码重构为 QMD 自有的 **disabled/raw-only provider port**：生命周期、连接尝试、请求上限、错误映射与 raw evidence 输出与 probe 编排分离；完成本批次完整的 disabled/raw-only provider 形态，而非继续「加一个 host / 加一个 status」的微切片。

## 批次与前置

| 项       | 值                                                                                                      |
| -------- | ------------------------------------------------------------------------------------------------------- |
| Batch    | 3F-R — `BATCH_3FR_REFERENCE_ADOPTION_REFACTOR`                                                          |
| Item ID  | `R3FR-03`                                                                                               |
| 建议分支 | `refactor/round3fr-tdx-provider`（Playbook §1）                                                         |
| 前置     | `R3FR-01` 参考治理已归档；`R3FR-02`+`R3FR-06` data health 垂直切片已绿（TDX 输出需喂新 profile checks） |
| 后置     | `R3FR-05`/`R3FR-04` 可并行；`R3FR-07` cleanup 最后                                                      |

## 原计划已读

- [x] `docs/implementation_tasks/README.md`
- [x] `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`（抽样核对 TDX 相关输入）
- [x] `PROJECT_IMPLEMENTATION_ROADMAP.md` — 3F-R 下一轨含 R3FR-03
- [x] `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- [x] `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- [x] `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- [x] `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md`
- [x] `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/README.md`
- [x] `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md`
- [x] `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_03_TDX_PROVIDER_REFACTOR.md`
- [x] `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_COORDINATOR_PLAYBOOK.md`
- [x] `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_TASK_CARD_MANIFEST.md`
- [x] `specs/contracts/reference_adoption_guardrails.yaml`（MIT/EasyXT 采纳红线）
- [x] 既有 Trellis 任务 `round3-tdx-manual-probe` execute-evidence（B01-TDX 历史）

**Round batch map：** 根目录无独立 `ROUND3_BATCH_IMPLEMENTATION_MAP.md` 的 3F-R 专节；以 `BATCH_3FR_*` README + `PROJECT_IMPLEMENTATION_ROADMAP.md` §3F-R 为批次权威。

## 现状摘要（Plan 期代码侦察）

| 模块                                                  | 现状                                                                                                                 | R3FR-03 意图                                |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `interface_probe_fetch_ports.TdxPytdxProbeFetchPort`  | 内联 pytdx 连接 + 仅 equity daily fetch                                                                              | 瘦身为委托新 port；禁止在此增长 downloader  |
| `datasources/adapters/tdx_pytdx.py`                   | skeleton + manifest builder                                                                                          | 保留/扩展为 adapter 边界；normalizer 下沉   |
| `ops/tdx_manual_probe.py`                             | mocked CI + live orchestration                                                                                       | 仅编排；调用 `fetch_ports/tdx_pytdx_port`   |
| `ops/tdx_live_manual_probe_gate.py`                   | fail-closed 授权                                                                                                     | 保持；port 层要求显式 authorization 对象    |
| `fetch_ports/`、`normalizers/`                        | **不存在**                                                                                                           | 新建 QMD 模块边界                           |
| `source_registry` / `source_capabilities` `tdx_pytdx` | disabled/proposed；caps 未完全对齐任务卡                                                                             | 对齐 caps 与 route status 语义              |
| 测试                                                  | `test_tdx_manual_probe.py` · `test_tdx_live_manual_probe_authorization.py` · `test_reference_adoption_guardrails.py` | 扩展/调整 purpose 对齐新 port；禁止弱化门禁 |

## 默认 caps（任务卡 §5）

```yaml
security_list_max_rows: 20
equity_daily_bar_max_symbols: 3
index_daily_bar_max_symbols: 3
max_network_calls: 5
minute_bars_enabled: false
full_market_scan_enabled: false
```

> **Plan 注：** 现行 `tdx_live_manual_probe_gate` 与 `tdx_manual_probe` 部分使用 `max_rows=10`；Execute 须将 registry、gate、port 三处 caps **收敛到任务卡**，并更新测试 purpose（不得删门禁）。

## 禁止（Batch 3F-R 全局 + 任务卡）

- production clean write / 默认 live enablement
- 全市场扫描 / 分钟线默认开启
- runtime import `参考项目/**`
- EasyXT auto-login / account / trading 语义
- silent fallback 到其他源
- 在 `TdxPytdxProbeFetchPort` 继续堆自写 downloader 逻辑

## 验收命令（任务卡 §6）

```bash
uv run pytest tests/test_tdx_manual_probe.py tests/test_tdx_live_manual_probe_authorization.py -q
uv run pytest tests/test_reference_adoption_guardrails.py tests/test_source_capabilities.py -q
```

**Phase P0 complete**
