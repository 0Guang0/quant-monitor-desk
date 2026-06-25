# Vertical slices — B3V-OPS (`/to-issues`)

> 每切片一个 VR 或子 AC；禁止水平合并。Registry 闭合不在本列表。

| 切片 ID | VR / AC | 交付物（完标准） | 依赖 | 证据 |
| ------- | ------- | ---------------- | ---- | ---- |
| **OPS-01** | VR-OPS-001 | `db_inspector` 从 `ops_db_inspect_contract.yaml` 加载 `key_tables` + `deferred_item_mapping`；删除重复常量 | — | `9.1-red/green.txt` |
| **OPS-02** | VR-OPS-001 | `test_contract_drift_ops_write` 断言 YAML↔运行时 key_tables + deferred 全量一致；改 YAML 无代码则 RED | OPS-01 | `9.2-red/green.txt` |
| **WRITE-01** | VR-WRITE-001 | `write_contract.yaml` 增加 `implemented_modes` / `reserved_modes`；`write_request.write_mode` 引用二者并集 | — | `9.3-red/green.txt` |
| **WRITE-02** | VR-WRITE-001 | 漂移测：`implemented_modes == WriteManager.SUPPORTED_MODES` | WRITE-01 | `9.4-red/green.txt` |
| **WRITE-03** | VR-WRITE-001 | 漂移测：每个 `reserved_modes` 调用 `write()` 稳定 `ValueError` 且行数为 0 | WRITE-01 | `9.5-red/green.txt` |

## 禁止切片

| 任务卡切片 | 原因 |
| ---------- | ---- |
| B02-CLOSE-01 | Plan 门禁：禁止 registry 闭合；VR 证据由 §10 验收，registry 主会话 |
