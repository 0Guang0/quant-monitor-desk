# Project Overview — B01-FRED (Phase 1a)

## 模块邻接

- **Registry：** `source_registry.yaml` / `source_capabilities.yaml` — 当前无独立 `fred` source 行；`macro_supplementary` 为 staged akshare 路由（非 FRED）
- **路由：** `route_planner.py` + `capability_registry.py` — 须增 fred sandbox 路径
- **Pilot 模式：** `staged_pilot.py` + `staged_pilot_fetch_ports.py` — v2 已覆盖 baostock/cninfo/akshare；FRED 为 DEFERRED（`live_pilot_constants.py`）
- **语义债：** `test_fred_staged_semantics.py` — B2.5-O-05 文档/registry 门禁已绿
- **Health：** `data_health.py` — **本任务不改**；DH2 负责 v2 FRED profile

## 风险

1. 任务卡 FRED-05 与 playbook「不改 data_health」冲突 → Plan 纠偏为 `fred_evidence_validator.py`
2. WL 并行 → Execute 须双 SSOT 策略（§3.5）
3. Registry commit 须主会话排队

## GitNexus

Plan 期轻量 query：`fred` / `staged_pilot` / `macro_supplementary` — 无 production FRED fetch 流。
