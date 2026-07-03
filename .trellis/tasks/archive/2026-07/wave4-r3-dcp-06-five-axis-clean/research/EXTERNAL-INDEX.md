# EXTERNAL-INDEX — R3-DCP-06

> 包外必读 · Plan v4.1

---

## §A 切片开工前必读

| 路径                                                                                            | 用途                     |
| ----------------------------------------------------------------------------------------------- | ------------------------ |
| `docs/implementation_tasks/.../R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md`                             | 活卡 §1–§5               |
| `docs/implementation_tasks/.../R3_DCP_TO_ISSUES_INDEX.md` §6.2                                  | Wave 4 DCP-06            |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.1、§3.5.2                                              | 五轴 PASS 清单           |
| `docs/decisions/ADR-029-dcp06-layer1-five-axis-clean-read.md`                                   | P0 锚点                  |
| `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md`                                 | clean 表映射             |
| `docs/modules/layer1_global_regime_panel.md`                                                    | Layer1 模块设计          |
| `specs/layer1_axes/restructured_axes_v1_1/**`                                                   | 五轴 spec                |
| `specs/contracts/layer1_axis_contract.yaml`                                                     | 指标契约                 |
| `specs/model_inputs/layer1_source_whitelist.yaml`                                               | K1                       |
| `specs/contracts/reference_adoption_guardrails.yaml`                                            | 借鉴梯                   |
| `docs/quality/待修复清单.md` §4                                                                 | `ACC-LAYER-E2E-LIVE-001` |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018A_layer1_observation_ingestion_bridge.md` | ingestion 桥             |

### DCP-05 归档（clean 写模板 · 非参考 L 梯）

| 路径                                       | 用途                    |
| ------------------------------------------ | ----------------------- |
| `.trellis/tasks/wave4-r3-dcp-05-tier-a/`   | Tier A incremental 先例 |
| `tests/test_fred_macro_incremental_e2e.py` | macro clean 种子模式    |

---

## §B 情境路由

| 情境          | 路径                                        |
| ------------- | ------------------------------------------- |
| clean 表      | `013_clean_domain_tables.sql`, ADR-028      |
| 特征引擎      | `backend/app/layer1_axes/feature_engine.py` |
| staged 桥     | `backend/app/layer1_axes/ingestion.py`      |
| ResourceGuard | `specs/contracts/resource_limits.yaml`      |

---

## §C 源码 / 测试字典

| 符号                                | 说明                 |
| ----------------------------------- | -------------------- |
| `AxisFeatureEngine`                 | 特征计算             |
| `AxisSpecLoader`                    | YAML 加载            |
| `Layer1ObservationIngestionService` | staged 桥（勿破坏）  |
| `read_observation_date_watermark`   | macro 水位（DCP-05） |
| 新增 `Layer1CleanObservationReader` | S00 交付             |

---

## §D 参考项目实读（L 梯 · 仅 `参考项目/**`）

| 路径                                            | 等级                        |
| ----------------------------------------------- | --------------------------- |
| `OpenBB/.../fetcher.py` L36–85                  | architecture_only / L3 对齐 |
| `OpenBB/.../fred_base.py` L31–75                | L2                          |
| `digital-oracle/.../fear_greed.py` L42–76       | L2 概念                     |
| `EasyXT/.../unified_data_interface.py` L172–244 | forbidden                   |

详见 `research/reference-adoption-dcp06.md`
