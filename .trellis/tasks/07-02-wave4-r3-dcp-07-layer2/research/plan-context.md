# Plan Context — R3-DCP-07

## Context Hierarchy（本任务映射）

| Level | 内容 |
|-------|------|
| L1 | Wave 4 DCP 真数据生产入口 · G2 最小竖切 |
| L2 | Layer2 cross-asset sensor 模块 · Tier A clean 消费 |
| L3 | `layer2_sensors` 源码 · `axis_observation` DDL |
| L4 | 切片 S00–S02 · ADR-032 · to-issues |
| L5 | 当前切片情境路由（§5.3） |

## PROJECT CONTEXT（可复制给 Execute）

```text
任务：R3-DCP-07 Layer2 单传感器真 clean
P0：L2-VIX · VIXCLS · axis_observation（DCP-05 fred）
禁止：staged_fixture 冒充 PASS · EasyXT fallback · 新 migration
必做：TDD · GitNexus impact · reference 实读证据
台账：ACC-LAYER-E2E-LIVE-001 L2 子集（S02）
```

## Level 3 源码表

| 文件 | 切片 | 用途 |
|------|------|------|
| `sensor_loader.py` | S00 | registry mode |
| `clean_observation_reader.py` | S00 | NEW clean read |
| `observation.py` | S00 | source assert |
| `snapshot_builder.py` | S01 | build snapshot |
| `lineage.py` | S01 | VR envelope |
| `tests/test_layer2_sensor_loader.py` | — | staged 契约（勿破坏） |
| `tests/test_fred_macro_incremental_e2e.py` | S01 | 种子模式参考 |

## 开工必读 vs 情境路由

| 时机 | 读什么 |
|------|--------|
| Execute BOOT | ENTRY §5.2 + EXTERNAL §A + ADR-032 + to-issues |
| S00 | plan-spec FR · DCP-06 clean_observation_reader（仓内） |
| S01 | test_layer2_sensor_loader lineage 测 · fred e2e |
| S02 | 待修复清单 §4 ACC-LAYER-E2E |

## 禁止误读

- 不把 `backend/app/layer2_sensors/**` 记入参考 L1/L2/L3
- 不声称关闭 L3–L5 全链 E2E
- 不关 `B2.5-O-05`
