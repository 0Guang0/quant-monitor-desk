# Audit A3 — 架构 · R3H-08

| 字段                  | 值                            |
| --------------------- | ----------------------------- |
| 维度                  | A3 架构 · ADR-027 · 无 bypass |
| plan_protocol_version | 4.1                           |
| 日期                  | 2026-06-30                    |

## §维度裁决

**FAIL**

## 计划内问题

| ID       | P   | 标题                                       | 锚点                        | 根因                                     | 修复方案                     | 验证                |
| -------- | --- | ------------------------------------------ | --------------------------- | ---------------------------------------- | ---------------------------- | ------------------- |
| A3-P1-01 | P1  | ProductLiveGate 未实现 ADR-027 完整开关链  | `product_live_gate.py`      | 仅 env；缺 ResourceGuard/registry/staged | gate 模块串联 fail-closed 链 | pytest -k gate      |
| A3-P1-02 | P1  | `live_fetch` 绕过 DataSourceService 金路径 | `data_commands.py` L152–166 | 直连 `port.fetch_payload`                | 改经 `service.fetch`         | pytest -k liveFetch |
| A3-P1-03 | P1  | `live_fetch` 未 fail-closed ResourceGuard  | `data_commands.py` L135–167 | 记录 guard 不阻断                        | 对齐 `sync_plan` guard 检查  | HARD_STOP 负向测    |
| A3-P2-01 | P2  | Tier C port rehearsal smoke 旁路           | `kalshi_port.py` L107–118   | smoke fallback 与 ADR-027 双轨           | 产品路径移除 smoke fallback  | kalshi/poly pytest  |
| A3-P2-02 | P2  | `live_fetch` 未校验 route READY            | `data_commands.py` L133–167 | 执行不检查 `route_status`                | READY 前拒绝 fetch           | 负向测              |

## 计划外发现

| ID       | P   | 标题                                     | 锚点                              | 根因                     | 修复方案                 | 验证                 |
| -------- | --- | ---------------------------------------- | --------------------------------- | ------------------------ | ------------------------ | -------------------- |
| A3-P1-04 | P1  | Tier A/B live port 无 port 级 env gate   | `fred_port.py` 等                 | `use_mock=False` 无 gate | port 入口统一 gate       | 负向测               |
| A3-P2-03 | P2  | datasources→ops 层依赖倒置               | `kalshi_port.py` import ops smoke | L3 port 依赖 E4 ops      | smoke 下沉或注入         | boundary check       |
| A3-P2-04 | P2  | reconcile 未绑定 ProductLiveGate service | `runners.py` L872+                | 可注入未 gated service   | 契约 + 工厂注入          | 对抗测               |
| A3-P3-01 | P3  | authority_graph 未登记 R3H-08 证据       | `authority_graph.yaml`            | 缺 test/ADR 链接         | `loop_maintain.py --fix` | loop_maintain exit 0 |
