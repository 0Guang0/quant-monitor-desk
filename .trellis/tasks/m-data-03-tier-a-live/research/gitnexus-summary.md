# M-DATA-03 GitNexus Impact Summary（1b）

> **Scope：** M-DATA-03 likely edit surface  
> **Date：** 2026-07-02

---

## 冲击面（改前须 impact）

| 符号 / 区域                                  | 风险           | 说明                                     |
| -------------------------------------------- | -------------- | ---------------------------------------- |
| `gate_live_fetch_port` / `product_live_gate` | **MEDIUM**     | 全 live 切片共用；改闸门影响 24 源政策测 |
| `DataSyncOrchestrator.run_incremental`       | **HIGH**       | 所有源编排；本票应 **避免** 改签名       |
| `build_product_live_service`                 | **MEDIUM**     | live service 工厂                        |
| `fetch_ports/*_port.py`                      | **LOW–MEDIUM** | 按源隔离；并行安全                       |
| `ops/*_incremental_*.py`                     | **LOW**        | 按源隔离                                 |
| `data_commands.py`                           | **MEDIUM**     | S00-INFRA 独占；并行禁止                 |
| `clean_write_targets.py`                     | **LOW**        | ADR-028 封板；本票不扩域                 |
| `source_registry.yaml` 三件套                | **HIGH**       | 仅 S-MERGE coordinator                   |

## 建议修改策略

1. **优先改：** 单源 port + 对应 e2e test + ops runner 的 `use_mock=False` 路径
2. **共享改：** 仅 S00-INFRA（harness）一次
3. **禁止：** orchestrator 公共逻辑重构；无 ADR 新 migration

## detect_changes 提交前

对比 `master`：`fetch_ports/` · `ops/*incremental*` · `tests/test_*incremental*` · `scripts/tier_a_live_acceptance.py`

## Caveats

- `impact('ProductLiveGate')` 符号名未索引；使用 `product_live_gate.gate_live_fetch_port`
