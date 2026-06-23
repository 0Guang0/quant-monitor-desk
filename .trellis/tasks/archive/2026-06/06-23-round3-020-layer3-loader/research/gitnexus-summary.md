# GitNexus summary — 020 Layer3 loader (Plan 1b)

## Query 摘要

- **概念：** Layer 3 industry chain loader / registry validation
- **参考流：** `019` `CrossAssetRegistryLoader.load` → validate → `CrossAssetLoadResult`
- **目标符号（Execute 将建）：** `IndustryChainLoader`, `IndustryChainLoadResult`

## Impact 预判（改码前 Execute 须 `impact()`）

| 目标                             | 方向   | 风险                     |
| -------------------------------- | ------ | ------------------------ |
| `IndustryChainLoader`            | 新建   | LOW — 无 upstream caller |
| `layer3_chains/models.py`        | 新建   | LOW                      |
| `layer2_sensors/*`               | 禁止改 | —                        |
| `snapshot_lineage_contract.yaml` | 禁止写 | —                        |

## 执行流（Plan 冻结）

```text
fixture paths (YAML/JSON)
  → IndustryChainLoader.load()
  → parse chain/anchor/node/edge/cross_chain
  → _assert_contract_hard_rules()
  → IndustryChainLoadResult
```

## 禁止路径

- production registry 默认路径
- DuckDB clean 写入（本任务 defer；`021` 负责 snapshot WriteManager）
