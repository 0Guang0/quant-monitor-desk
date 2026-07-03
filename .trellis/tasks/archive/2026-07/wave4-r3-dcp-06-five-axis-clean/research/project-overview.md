# Project Overview — R3-DCP-06

> GitNexus Phase 1a · 2026-07-02

## 任务摘要

**R3-DCP-06** 将 Layer1 五轴从 staged fixture 提升到 **Tier A clean 真输入**，闭合 G12 PASS 硬门禁。

## 代码簇（authority_graph `layer1_axes`）

| 区域      | 路径                                     | 职责                              |
| --------- | ---------------------------------------- | --------------------------------- |
| Spec 加载 | `axis_loader.py`, `guardrails.py`        | 五轴 YAML → `AxisLoadResult`      |
| 特征/解释 | `feature_engine.py`, `interpretation.py` | robust_z、state_bucket            |
| 写入桥    | `ingestion*.py`, `observation_*.py`      | Batch 2.5 staged→clean 桥（保留） |
| 血缘      | `lineage.py`                             | snapshot lineage                  |
| 测试      | `tests/test_layer1_*.py`                 | loader/ingestion/interp 覆盖      |

## 上游依赖（已 CLOSED）

| 依赖                   | 证据                                                  |
| ---------------------- | ----------------------------------------------------- |
| R3-DCP-05 Tier A clean | `axis_observation`, `security_bar_1d` incremental e2e |
| R3H-06 clean schema    | migration 013/015                                     |
| Batch 2 Layer1 引擎    | `feature_engine`, `interpretation` staged 绿          |

## 下游

| 消费者             | 关系                     |
| ------------------ | ------------------------ |
| DCP-07 Layer2      | 可读 L1 快照展示；不回写 |
| Wave 5 R3H-05-GATE | 审计五轴 + Layer 绑定    |
| Round4 产品        | 须在 PASS 之后           |

## GitNexus 查询要点

- `layer1 axes clean ingestion feature engine` → `ingestion.py`, `feature_engine.py`, `test_layer1_observation_ingestion.py`
- impact(`Layer1ObservationIngestionService`) → **LOW**，3 直接依赖文件

## 风险触点

- `ingestion.py` 仍硬编码 `FROZEN_STAGED_INDICATOR` / `build_staged_fixture_service` — DCP-06 加 **parallel clean path**，不破坏 staged 桥
- 流动性轴 spec primary = tiingo（非 Tier A）— ADR-029 ponytail 用 alpha_vantage bar
