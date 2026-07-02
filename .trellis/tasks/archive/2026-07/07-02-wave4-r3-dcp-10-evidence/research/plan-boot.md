# Plan Boot — R3-DCP-10 Layer5 证据绑真源（G5）

> **轨道：** Wave 4f · Plan v4.1  
> **日期：** 2026-07-02  
> **活卡：** `R3_DCP_10_LAYER5_EVIDENCE_BINDING.md`  
> **前置：** R3-DCP-05 ✅ · R3H-08 live fetch 证据 ✅

---

## Phase P0 complete

### 1. 做什么

选 **一条** P0 factual evidence 竖切：Tier A 真 fetch 证据（DCP-05 clean + raw store）→ Layer5 foundation/lineage，pytest 可断言 `source_fetch_id` + `content_hash` + `schema_hash` 与 fetch bundle 一致（非 staged fixture 占位符）。

### 2. 价值

- Wave 4 **G5 绑真源**；承接 `ACC-LAYER-E2E-LIVE-001` **G5 子集**
- 为 Wave 5 `R3H-05-GATE` 提供 Layer5 真源绑定样本

### 3. 约束

| 约束   | 要求                                                                     |
| ------ | ------------------------------------------------------------------------ |
| 金路径 | raw store → clean → Layer5；禁止 bypass WriteManager                     |
| 绑定   | `source_fetch_id` + `content_hash` + `schema_hash` 三者对齐 fetch bundle |
| 真网   | 默认 replay；live 须 env-gate + 隔离库（ADR-027）                        |
| Schema | 无新 migration 除非 ADR                                                  |
| 范围   | **一条** P0 domain/instrument 竖切                                       |
| 参考   | L1/L2/L3 仅 `参考项目/**`                                                |

### 4. P0 竖切定案（Plan 调研后）

| 维度               | 定案                                          |
| ------------------ | --------------------------------------------- |
| **data_domain**    | `cn_equity_daily_bar`                         |
| **source_id**      | `mootdx`（Tier A · DCP-05 S08 replay 先例）   |
| **instrument_id**  | `sh.600519`（mootdx incremental e2e fixture） |
| **clean_table**    | `security_bar_1d`                             |
| **evidence_kind**  | `factual_source` · `price_volume`             |
| **schema_version** | `cn_market_evidence_v1`                       |

**定案理由：** DCP-05 已有 `test_mootdx_incremental_e2e` 金路径；`mootdx_port` + `cn_market` normalizer 已产出含三哈希字段的 evidence bundle；`bundle_layer5_provenance` 已存在但缺 schema_hash 与 clean→Layer5 e2e 接线。

### 5. 架构触点

```text
mootdx fetch (replay/live) → raw metadata + cn_market_evidence.json
        ↓
orchestrator incremental → security_bar_1d (WriteManager)
        ↓
bundle_layer5_provenance (+ schema_hash dataset anchor)
        ↓
EvidenceFoundationRecord + Layer5LineageEnvelope
        ↓
test_layer5_mootdx_bar_clean_e2e.py
```

### 6. 成功标准

活卡 §5 + `validate-plan-freeze` exit 0 + Plan 包齐

### 7. P0 已读清单

- [x] `R3_DCP_10_LAYER5_EVIDENCE_BINDING.md`
- [x] `docs/modules/layer5_security_evidence.md`
- [x] `backend/app/layer5_evidence/{foundation,lineage,models}.py`
- [x] `backend/app/datasources/normalizers/{evidence_bundle,cn_market}.py`
- [x] `backend/app/datasources/fetch_ports/mootdx_port.py`
- [x] `backend/app/ops/mootdx_incremental_run.py`
- [x] `tests/test_layer5_evidence_foundation.py` · `tests/test_raw_store.py`
- [x] `tests/test_mootdx_incremental_e2e.py` · `tests/incremental_mootdx_support.py`
- [x] `.trellis/tasks/wave4-r3-dcp-05-tier-a/research/`（DCP-05 clean 写路径 · 只读）
- [x] `docs/decisions/ADR-027-r3h08-product-live-env-gate.md` · `ADR-028-dcp05-tier-a-clean-domain-extension.md`
- [x] `specs/model_inputs/layer5_instrument_source_plan.yaml`
- [x] `specs/contracts/reference_adoption_guardrails.yaml`
- [x] `docs/quality/待修复清单.md` · `PROJECT_IMPLEMENTATION_ROADMAP.md`（ACC-LAYER-E2E G5）
- [x] 参考项目实读：OpenBB Fetcher · digital-oracle BIS · EasyXT unified_data_interface
- [x] GitNexus query layer5/provenance + impact(`Layer5LineageBuilder`) — LOW
