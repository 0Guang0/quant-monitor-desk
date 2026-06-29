# A1 正确性审计报告 — R3H-08 Live Productization

| 字段                  | 值                                        |
| --------------------- | ----------------------------------------- |
| 维度                  | A1 正确性 · Tier + 24 源                  |
| 任务                  | `06-29-round3h-r3h08-live-productization` |
| plan_protocol_version | 4.1                                       |
| Execute commit        | `2f75a035`                                |
| 审计日期              | 2026-06-30                                |

## 维度证据

- `uv run pytest tests/test_r3h08_live_productization.py -q` → **33 passed** exit 0
- GitNexus `query` 已执行；greenfield 符号索引滞后
- diff 17 files，与 LIVE-PROD-24 scope 一致，无 migration silent 扩大

## §维度裁决

**FAIL**

## 计划内问题

| ID       | P   | 标题                                               | 锚点                             | 根因                                        | 修复方案                                            | 验证                                    |
| -------- | --- | -------------------------------------------------- | -------------------------------- | ------------------------------------------- | --------------------------------------------------- | --------------------------------------- |
| A1-P1-01 | P1  | CLI `live_fetch` 非 dry-run 绕过 DataSourceService | `data_commands.py` L148–166      | `dry_run=False` 直连 port                   | 改经 `build_product_live_service` + `service.fetch` | pytest liveFetch 金路径测               |
| A1-P1-02 | P1  | baostock 产品 live 委托 cn_rehearsal               | `baostock_port.py` L108–116      | 无 replay 时 import rehearsal 模块          | 独立 QMD 网络路径或 replay-only                     | 负向测不得 import cn_rehearsal          |
| A1-P1-03 | P1  | coingecko 工厂缺 `asset_ids`                       | `product_live_ports.py` L242–243 | kwargs 仅 `max_assets` → TypeError          | 补 `asset_ids` 默认                                 | runtime + pytest                        |
| A1-P1-04 | P1  | tdx_pytdx 无产品 live 工厂                         | `product_live_ports.py` L235–252 | 无 `create_tdx_pytdx_fetch_port`            | 新增工厂或排除并文档化                              | `create_product_live_fetch_port` 可构造 |
| A1-P2-01 | P2  | kalshi/polymarket smoke env 旁路                   | `kalshi_port.py` L107–118        | ProductLiveGate 未 opt-in 时 fallback smoke | 产品路径仅 ProductLiveGate                          | 无 env 时 product fetch 拒绝            |

## 计划外发现

| ID       | P   | 标题                              | 锚点                               | 根因               | 修复方案           | 验证           |
| -------- | --- | --------------------------------- | ---------------------------------- | ------------------ | ------------------ | -------------- |
| A1-P2-02 | P2  | BOOT 矩阵 LiveTierRouter 状态过时 | `live-tier-baseline-matrix.md` L51 | 写「未建」但已实现 | S08-CLOSE 更新矩阵 | 矩阵与代码一致 |
