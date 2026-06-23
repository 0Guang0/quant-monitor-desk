# Project overview — 020 Layer3 loader (Plan 1a)

> GitNexus 轻量概览 · ≤1 页

## 模块定位

- **包：** `backend/app/layer3_chains/`（当前仅 `__init__.py` 占位）
- **职责：** 解析 staged fixture 五类 registry → typed dataclasses → contract 硬校验
- **非职责：** snapshot、lineage 写库、Layer5 行情（→ `021`+）

## 019 模式（须复用）

`CrossAssetRegistryLoader`（`sensor_loader.py`）：

- `STAGED_REGISTRY_FIXTURE` 默认路径
- `mode == staged_fixture_only` 门禁
- `CrossAssetRegistryLoadError` fail-fast
- contract 字段枚举 + 唯一性断言

## 契约锚点

`layer3_loader_contract.yaml`：

- 唯一：`chain_id`、`node_id`、`anchor_id`
- 引用：`edge.from/to_node_id`、`anchor.node_id`
- 语义：`event_only` 私有公司；`P0_CORE`/`P0_EVENT` → `source_keys`

## 风险

| 风险 | 缓解 |
| ---- | ---- |
| 全量 registry 过大 | fixture 最小子集 + eco |
| 误读生产 registry | `staged_fixture_only` 拒绝其他 mode |
| scope 漂移到 layer2/4/5 | slice plan forbidden 列表 |

## Blast radius（Plan 预估）

- 新建 `loader.py` + `models.py`；无现有 caller
- 参考只读：`layer2_sensors/sensor_loader.py`
