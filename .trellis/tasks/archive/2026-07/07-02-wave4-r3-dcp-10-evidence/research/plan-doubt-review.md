# Plan Doubt Review — R3-DCP-10

## Doubt cycle checklist

### Cycle 1 — P0 源选择：baostock vs mootdx

| Step      | 内容                                                                                                                          |
| --------- | ----------------------------------------------------------------------------------------------------------------------------- |
| CLAIM     | layer5_instrument_source_plan 主候选是 baostock                                                                               |
| EXTRACT   | L5-BS-DAILY-BAR-P0 · baostock primary                                                                                         |
| DOUBT     | 为何 Plan 选 mootdx？                                                                                                         |
| RECONCILE | **actionable** — mootdx DCP-05 S08 e2e 已绿 + cn_market bundle 已有 layer5 helper；baostock 可 Wave 5 扩。ADR-031 冻结 mootdx |
| STOP      | 定案 mootdx / sh.600519                                                                                                       |

### Cycle 2 — schema_hash 存放位置

| Step      | 内容                                                                          |
| --------- | ----------------------------------------------------------------------------- |
| CLAIM     | SourceProvenance 无 schema_hash 字段                                          |
| EXTRACT   | snapshot_lineage_contract 亦无独立列                                          |
| DOUBT     | 如何满足活卡「三者契约对齐」？                                                |
| RECONCILE | **actionable** — encode in `source_dataset_ids` per ADR-031；e2e assert parse |
| STOP      | 不扩 dataclass 除非 Execute 证明 validator 缺口                               |

### Cycle 3 — live vs replay

| Step      | 内容                                                                                                               |
| --------- | ------------------------------------------------------------------------------------------------------------------ |
| CLAIM     | 活卡要求真网                                                                                                       |
| EXTRACT   | ADR-027 env-gate · DCP-05 replay 政策                                                                              |
| DOUBT     | replay 能否关 ACC G5？                                                                                             |
| RECONCILE | **trade-off** — G5 子集 = provenance binding sample，非 production_live 全链；replay bundle 含真 fetch_id 生成逻辑 |
| STOP      | live optional post-S02                                                                                             |

### Cycle 4 — DB evidence_chain 持久化

| Step      | 内容                                                                         |
| --------- | ---------------------------------------------------------------------------- |
| CLAIM     | layer5_security_evidence.md 描述 evidence_chain 表                           |
| EXTRACT   | 023A 仅 foundation validator                                                 |
| DOUBT     | 本票是否写 DB？                                                              |
| RECONCILE | **actionable** — Out of scope；validator + lineage envelope 断言足够 G5 子集 |
| STOP      | 无 migration                                                                 |

### Cycle 5 — 全链 E2E 假关

| Step      | 内容                                                        |
| --------- | ----------------------------------------------------------- |
| CLAIM     | ACC-LAYER-E2E 全链 open                                     |
| EXTRACT   | DCP-06 已关 L1；L2/L4 在 DCP-07/08                          |
| DOUBT     | DCP-10 能否宣称全链 PASS？                                  |
| RECONCILE | **actionable** — 仅 G5 子集；L3–L5 全链阶段外置 Wave 5 GATE |
| STOP      | 台账 S03 精确措辞                                           |

## 分类汇总

| 分类       | 项                                                              |
| ---------- | --------------------------------------------------------------- |
| actionable | mootdx P0 · schema_hash encoding · no DB write · G5 subset only |
| trade-off  | replay vs live                                                  |
| noise      | —                                                               |
