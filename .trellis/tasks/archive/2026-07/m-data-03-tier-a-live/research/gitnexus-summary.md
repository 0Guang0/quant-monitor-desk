# M-DATA-03 GitNexus Impact Summary（Plan R2）

> **Scope：** R2 切片 likely edit surface · **Date：** 2026-07-03

---

## 冲击面（改前须 impact）

| 符号 / 区域                            | 风险       | R2 切片                                |
| -------------------------------------- | ---------- | -------------------------------------- |
| `gate_live_fetch_port`                 | MEDIUM     | 全片                                   |
| `DataSyncOrchestrator.run_incremental` | HIGH       | **避免**改签名；S-R2-DISPATCH 去重包装 |
| `fetch_ports/*_port.py`                | LOW–MEDIUM | 按源（若 port 变更）                   |
| `tier_a_live_incremental_dispatch.py`  | HIGH       | **S-R2-DISPATCH only**                 |
| `tier_a_live_acceptance.py`            | HIGH       | S-R2-EVIDENCE · B2 · F0 · ACCEPT       |
| `data_health` runners                  | MEDIUM     | S-R2-F0                                |
| `DataQualityValidator`                 | MEDIUM     | S-R2-B2                                |
| `platform_source_matrix.yaml`          | MEDIUM     | S-R2-DISPATCH                          |
| `source_registry.yaml` 三件套          | HIGH       | **主会话** merge coordinator           |

## 建议修改策略（R2）

1. **S-R2-EVIDENCE：** manifest 写入 + 契约测
2. **S-R2-F0 / S-R2-B2：** 并行；见 `parallel-dispatch-protocol.md` 文件锁
3. **S-R2-DISPATCH：** 单独 agent；禁止与另一 agent 同改 dispatch
4. **禁止：** orchestrator 公共逻辑无 ADR 重构

## detect_changes 提交前

`fetch_ports/` · `ops/*incremental*` · `tier_a_live_*` · `data_health` · `platform_source_matrix.yaml`
