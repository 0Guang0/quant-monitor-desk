# Layer 3 配置健康检查

> 文件定位：Layer 3 chain / anchor / node / edge / source 配置的可执行校验文件。  
> 目标：防止产业链配置出现断边、孤儿节点、错误 ticker 类型、私有公司误作行情锚、P0 来源缺失等问题。

---

# 1. 检查对象

```text
specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_global_industry_chain_registry.yaml
specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_anchor_registry.json
specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_node_registry.json
specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_edge_registry.json
specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_cross_chain_edge_registry.json
specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/references/source_registry.md
```

---

# 2. 必须通过的结构检查

```text
chain_id 唯一
anchor_id 唯一
node_id 唯一
edge_id 唯一
cross_chain_edge_id 唯一
每个 anchor.chain_id 存在于 chain registry
每个 anchor.node_id 存在于 node registry
每个 node.chain_id 存在于 chain registry
每个 edge.source_node_id / target_node_id 存在
每个 cross-chain edge 起点和终点存在
```

---

# 3. 字段完整性检查

每个 chain 必须有：

```text
chain_id
chain_name_cn
chain_priority
summary_cn
frontend_group
```

每个 anchor 必须有：

```text
anchor_id
chain_id
node_id
anchor_name
anchor_tier
anchor_roles
anchor_priority
status_explanation_cn
impact_explanation_cn
event_only
source_validation_status
```

---

# 4. source_validation_status 规则

允许值：

```text
verified
needs_source
event_only_verified
price_proxy_needs_feed
```

规则：

```text
P0_CORE anchor 不允许 needs_source
P0_EVENT anchor 必须 event_only_verified
public_equity / adr / etf / futures_proxy 不能 event_only=true
private_company 必须 event_only=true
commodity / index / futures_proxy 如无正式数据源，必须 price_proxy_needs_feed
```

---

# 5. instrument_type 与 ticker 检查

```text
public_equity 必须有 ticker 或 listing_symbol
adr 必须有 ticker
private_company 不要求 ticker，但必须有 event source
commodity / index / futures_proxy 必须有 price_proxy 或 data_feed_hint
regional_proxy 必须标记 region
```

---

# 6. 优先级检查

```text
anchor_priority 不能全部是 P0
chain_priority 与 anchor_priority 不得混用
P2 链上的 anchor 默认不应为 P0，除非有 explicit_override_reason
区域映射股不能与全球定价锚同级，除非有 justification_cn
```

---

# 7. 语义边界检查

禁止：

```text
把私有公司当日度行情锚
把商品指数当股票
把区域映射股当全球绝对定价锚
Layer 3 保存全量历史行情
Layer 3 输出买卖动作
```

---

# 8. 输出报告

```text
reports/system/layer3_config_health_YYYYMMDD.md
```

必须包含：

```text
passed_checks
failed_checks
warning_checks
orphan_nodes
missing_source_keys
p0_source_coverage
private_company_errors
edge_errors
priority_distribution
```

---

# 9. CLI

```bash
python -m quant_monitor.layer3.validate_config --strict
python -m quant_monitor.layer3.validate_config --report reports/system/layer3_config_health_YYYYMMDD.md
```

---

# 10. 验收测试

```text
删除一个 node 后检查能失败
P0 anchor source_keys 为空时检查能失败
private_company event_only=false 时检查能失败
anchor_priority 全 P0 时检查能失败
cross-chain edge 指向不存在节点时检查能失败
正常配置能通过 strict 模式
```
