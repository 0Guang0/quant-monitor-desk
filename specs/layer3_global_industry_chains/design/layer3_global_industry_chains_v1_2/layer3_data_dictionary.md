# Layer 3 全球产业链资金震动锚点层 v1.1

> 本文件夹是设计文档 Layer 3 的可实现版本。核心思想：第三层不是行业列表，也不是股票池，而是“全球产业链资金震动锚点层”。

## 1. 定位

Layer 3 只追踪能引发产业链资金重定价的锚点，包括：

- 资本开支总开关：决定钱往哪里花、花多少、花多久。
- 全球绝对定价锚：单家公司就能影响全球上下游资金。
- 寡头型资金锚：几家公司共同影响赛道资金。
- 供应链高弹性锚：涨跌幅和主题扩散敏感，但不是绝对龙头。
- 私有事件锚：OpenAI、Anthropic、SpaceX、Unitree 等不能作为普通行情标的，但其融资、产品、订单能影响市场预期。
- 商品/指数锚：铜、油、BDI、锂、铀等通过价格反映供需。
- 区域映射锚：A股/港股/韩股/日股等区域资金映射。

## 2. 文件清单

```text
layer3_global_industry_chain_registry.yaml   # 主配置文件，给程序读取
layer3_anchor_registry.json                  # 扁平化锚点表，给前端/后端快速读取
layer3_data_dictionary.md                    # 字段说明与实现规则
references/source_registry.md                # 官方/权威来源列表
```

## 3. 字段说明

### chain 字段

| 字段                  | 含义                                                             |
| --------------------- | ---------------------------------------------------------------- |
| `chain_id`            | 产业链唯一ID                                                     |
| `chain_name_cn`       | 中文名称                                                         |
| `chain_name_en`       | 英文名称                                                         |
| `chain_priority`      | 产业链优先级：P0_CORE / P1_THEME / P1_GLOBAL_MACRO / P2_OPTIONAL |
| `chain_type`          | demand_side_capex / compute_supply / manufacturing_bottleneck 等 |
| `definition_cn`       | 这条链到底看什么                                                 |
| `frontend_summary_cn` | 前端展示的一句话解释                                             |
| `avoid_confusion_cn`  | 防止误解与跨层污染                                               |
| `key_metrics`         | 前端/后端应优先展示的关键变量                                    |
| `anchors`             | 本链锚点列表                                                     |

### anchor 字段

| 字段                    | 含义                                                                            |
| ----------------------- | ------------------------------------------------------------------------------- |
| `anchor_id`             | 锚点ID                                                                          |
| `display_name_cn`       | 中文名                                                                          |
| `display_name_en`       | 英文名                                                                          |
| `instrument_type`       | public_equity / private_company / future_or_commodity / index / commodity_index |
| `ticker`                | 股票/期货/指数代码；私有公司可为空                                              |
| `exchange`              | 交易所                                                                          |
| `anchor_tier`           | 锚点地位，见下方字典                                                            |
| `anchor_roles`          | 锚点作用，例如 demand_setter / supply_bottleneck / price_proxy                  |
| `frontend_group`        | 前端分组，例如 核心Capex买方、AI服务器、光模块                                  |
| `anchor_priority`       | 锚点监控优先级：P0_CORE / P0_EVENT / P1_ACTIVE / P1_EVENT / P1_PRICE / P2_WATCH |
| `status_explanation_cn` | 地位解释，直接给前端展示                                                        |
| `impact_explanation_cn` | 能造成什么影响，直接给前端展示                                                  |
| `monitor_events`        | 需要监控的事件类型                                                              |
| `layer5_mapping_hint`   | 对应Layer 5 instrument_id的建议                                                 |
| `event_only`            | 是否只做事件锚，不做行情锚                                                      |
| `source_keys`           | 来源索引，见 `references/source_registry.md`                                    |

### root node / edge 字段

第一版为了避免 `industry_chain_node` 为空，每条 chain 至少自动生成一个 root node：

```text
node_id = chain_id + "_ROOT"
node_role = chain_root
node_level = 0
```

后续如需做更细图谱，可逐步把 root node 拆成 Capex 买方、供给瓶颈、制造、扩散、价格锚等子节点，并用 `edges` 表达传导关系。

### source_validation_status

| 值                        | 含义                                     |
| ------------------------- | ---------------------------------------- |
| `verified`                | 已有官方/权威来源键，可进入审计链        |
| `event_only_verified`     | 私有事件锚已有来源键，但不进入普通行情表 |
| `needs_source`            | 需要后续补充来源键，不能作为强证据使用   |
| `event_only_needs_source` | 私有事件锚需要补来源，只能暂作观察       |
| `price_proxy_needs_feed`  | 商品/指数价格锚需要后续确认稳定行情源    |

## 4. `anchor_tier` 字典

| 值                       | 中文解释                                                                                              |
| ------------------------ | ----------------------------------------------------------------------------------------------------- |
| `A_GLOBAL_DOMINANT`      | 全球绝对统治型/定价型锚点。单家公司或变量的财报、产能、路线图、限制政策足以影响全球产业链资金重定价。 |
| `A_CAPEX_SETTER`         | 资本开支总开关。它不是供应商，但决定AI基础设施花多少钱、买多少算力、建多少数据中心。                  |
| `B_OLIGOPOLY_ANCHOR`     | 寡头型资金锚。行业中少数几家公司共同影响资金流向，没有单一绝对统治者。                                |
| `B_SUPPLY_CHAIN_BETA`    | 供应链高弹性锚。对产业链景气度反应快、波动大，适合监控主题扩散。                                      |
| `C_PRIVATE_EVENT_ANCHOR` | 私有公司/不可直接交易事件锚。融资、产品、订单或合作能影响市场，但不是常规行情标的。                   |
| `D_COMMODITY_PROXY`      | 商品/期货/指数价格锚。通过价格或运价直接反映供需约束。                                                |
| `E_REGIONAL_PROXY`       | 区域市场映射锚。主要反映A股、港股、韩股、日股等局部市场弹性，全球统治力不足。                         |

## 5. 前端展示建议

每条链打开后，不要显示几十个同级股票。建议固定五栏：

1. 核心震动锚：通常不超过 3-5 个。
2. 扩散锚：通常不超过 5-10 个。
3. 事件锚：私有公司、监管、政策、融资、订单。
4. 商品/指数代理：期货、商品、运价、ETF/指数。
5. 区域映射：A股、港股、日股、韩股等本地弹性标的。

## 6. 与五层设计的关系

- Layer 3 保存产业链关系、锚点身份、解释字段和事件触发规则。
- Layer 5 保存具体股票、ETF、期货、商品合约的行情、财务和事件。
- Layer 3 页面通过 view / snapshot 从 Layer 5 读取最新价格、成交量、成交额、持仓量和公告事件。
- 私有公司只进入事件系统，不进入普通行情表。

## 7. 第一版主链

本版共设置 14 条主链：

- `L3_AI_CAPEX_COMMAND_CENTER`：AI资本开支总开关（P0_CORE）
- `L3_AI_COMPUTE_ASIC`：AI芯片/加速器/ASIC（P0_CORE）
- `L3_AI_MEMORY_BOTTLENECK`：AI存储瓶颈：HBM/DRAM/NAND（P0_CORE）
- `L3_SEMICONDUCTOR_MANUFACTURING_BOTTLENECK`：半导体制造瓶颈：先进制程/封装/设备/EDA/IP（P0_CORE）
- `L3_AI_INFRASTRUCTURE_EXPANSION`：AI基础设施扩散：服务器/网络/光模块（P0_CORE）
- `L3_AI_POWER_COOLING`：AI电力与冷却链（P0_CORE）
- `L3_MODEL_ENTERPRISE_AI_PLATFORM`：模型层与企业AI平台（P1_THEME）
- `L3_ROBOTICS_EMBODIED_AI`：机器人/具身智能/自动驾驶（P1_THEME）
- `L3_ENERGY_LNG`：油气/LNG/传统能源（P1_GLOBAL_MACRO）
- `L3_CRITICAL_MINERALS_URANIUM`：关键矿产与铀（P1_GLOBAL_MACRO）
- `L3_AEROSPACE_DEFENSE_SPACE`：航空航天/国防/商业航天（P1_GLOBAL_MACRO）
- `L3_SHIPPING_GLOBAL_TRADE`：航运/全球贸易（P1_GLOBAL_MACRO）
- `L3_GLP1_METABOLIC_DRUGS`：GLP-1/肥胖药/代谢药（P1_GLOBAL_MACRO）
- `L3_EV_BATTERY_STORAGE`：新能源车/动力电池/储能（P2_OPTIONAL）

## v1.2：方案B节点与边字段补充

本版本不再只为每条 `chain` 生成 root node，而是为每条链补充功能节点与有向边：

- `layer3_node_registry.json`：扁平化节点表，可直接初始化 `industry_chain_node`。
- `layer3_edge_registry.json`：链内边表，可直接初始化 `industry_chain_edge`。
- `layer3_cross_chain_edge_registry.json`：跨链传导边，尤其用于 AI 主链的“Capex买方 → GPU/ASIC → HBM → 服务器/网络/光模块 → 电力/冷却 → 铜/能源约束”。

新增/强化字段：

| 字段                          | 说明                                                                            | 前端用途                       |
| ----------------------------- | ------------------------------------------------------------------------------- | ------------------------------ |
| `node_role`                   | 节点角色，如 demand_setter、compute_core、memory_bottleneck、power_distribution | 展示节点身份                   |
| `parent_node_id`              | 父节点，root node 为空                                                          | 生成树形结构                   |
| `edge_id`                     | 传导边唯一 ID                                                                   | 关系图绘制                     |
| `from_node_id` / `to_node_id` | 传导边起点/终点                                                                 | 画有向边                       |
| `relation_type`               | 关系类型，如 capex_to_compute_demand、compute_to_memory_bottleneck              | Agent解释关系类型              |
| `transmission_logic_cn`       | 中文传导解释                                                                    | 前端展示“为什么这两个节点相关” |

实现规则：

1. Layer 3 仍然不保存行情历史。
2. 节点和边只说明产业链关系与传导逻辑。
3. 行情、成交额、成交量、持仓量仍从 Layer 5 读取。
4. 私有公司事件锚只进入事件系统，不进入普通行情抓取。
5. P0锚点必须有 `source_keys`，且 `source_validation_status` 不得为 `needs_source`。
