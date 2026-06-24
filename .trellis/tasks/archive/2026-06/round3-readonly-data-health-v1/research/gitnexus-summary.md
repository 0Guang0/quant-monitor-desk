# GitNexus summary — data health v1 (Plan 1b)

## query: ops data health staged evidence

- **ops cluster:** `db_inspector`, `staged_pilot`, `mutation_proof` — 只读/证据导向
- **validators cluster:** `data_quality`, `source_conflict` — rule_id 权威在 YAML
- **无现有 `data_health` 符号** — 新模块应挂 `backend/app/ops/data_health.py`

## impact 预判（Execute 前必跑）

| 目标符号                     | 预期 callers       | 风险         |
| ---------------------------- | ------------------ | ------------ |
| `DataHealthService`（拟）    | CLI wrapper, tests | LOW — 新文件 |
| `load_evidence_bundle`（拟） | health checks only | LOW          |

## 建议 Execute 路径

1. 先 model + loader（无 DB 写）
2. 规则函数调用 validator 逻辑或内联最小检查（ponytail：不复制整表）
3. CLI 薄包装对齐 `db_inspector` CLI 模式（若存在）

## 禁止触碰（HIGH if touched）

- `staged_evidence.register_staged_file_registry_rows` — β-2 分支
- `layer4_markets/**` — 022 分支
- registry 三件套 — 主会话批处理
