# GitNexus Summary — R3-DCP-06

> Phase 1b · 2026-07-02

## impact(`Layer1ObservationIngestionService`)

| 字段                  | 值                                                                      |
| --------------------- | ----------------------------------------------------------------------- |
| risk                  | **LOW**                                                                 |
| direct upstream files | `observation_mapper.py`, `ingestion_evidence.py`, `ingestion_commit.py` |
| depth-2               | `observation_writer.py`                                                 |

**结论：** 新增 clean reader 宜 **新模块**（如 `clean_observation_reader.py`）或 `ingestion.py` 内新方法；避免破坏 staged commit 路径。改 `AxisFeatureEngine` / `axis_loader` 风险低。

## impact（Plan 阶段拟改符号）

| 符号                                              | 预期风险 | 备注                      |
| ------------------------------------------------- | -------- | ------------------------- |
| `AxisFeatureEngine`                               | LOW      | 输入源切换为 clean 序列   |
| `Layer1ObservationIngestionService`               | LOW      | 并行入口，不改默认 staged |
| 新增 `read_clean_observations_for_indicator`      | LOW      | 新符号                    |
| `specs/model_inputs/layer1_source_whitelist.yaml` | MED      | registry 协调 merge       |

## 建议 Execute 前复跑

```text
impact(Layer1ObservationIngestionService)
impact(AxisFeatureEngine)
context(AxisFeatureEngine)
detect_changes()  # 提交前
```

## 禁止

- 未 impact 即大范围改 `ingestion_commit.py` 事务语义
- rename 五轴 indicator_id（用 ADR-029 锚点表）
