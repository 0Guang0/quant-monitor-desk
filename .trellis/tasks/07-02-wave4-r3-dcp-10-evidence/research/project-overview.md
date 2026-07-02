# Project Overview — R3-DCP-10 Layer5 Evidence Binding

> GitNexus Phase 1a · 2026-07-02

## Query

Layer5 evidence provenance: fetch bundle → clean bar → foundation/lineage binding.

## 现状（仓内 trace）

| 层 | 组件 | 状态 |
| --- | --- | --- |
| Fetch | `mootdx_port` → `finalize_bundle` | ✅ 产出 `source_fetch_id` / `content_hash` / `schema_hash` |
| Raw | `RawStore.save` + `file_registry` | ✅ content_hash 落盘 |
| Clean | `orchestrator.run_incremental` → `security_bar_1d` | ✅ DCP-05 S08 e2e |
| Normalize | `cn_market.build_cn_market_evidence_bundle` | ✅ schema_version + finalize |
| Bridge | `bundle_layer5_provenance` | ⚠️ 仅 fetch_id + content_hash；**无 schema_hash** |
| Layer5 | `EvidenceFoundationValidator` / `Layer5LineageBuilder` | ✅ 契约完整；测试用 **STAGED** 占位 |
| E2E | `test_layer5_*_clean_e2e` | ❌ **缺失** — 本票 Execute 交付 |

## 数据流（P0 竖切）

```text
SyncJobSpec(source_id=mootdx, data_domain=cn_equity_daily_bar, instrument_id=sh.600519)
  → DataSourceService.fetch_payload
  → cn_market_evidence.json (raw/)
  → staging adapter → security_bar_1d
  → read bundle from raw path OR capture from fetch result
  → SourceProvenance + EvidenceFoundationRecord
  → Layer5LineageEnvelope (snapshot_lineage_contract)
```

## 关键契约

- `specs/contracts/snapshot_lineage_contract.yaml` — `source_fetch_ids` / `source_content_hashes` 必填
- `specs/contracts/sandbox_clean_write_contract.yaml` — evidence 三字段 coverage
- `layer5_instrument_source_plan.yaml` — L5-BS-DAILY-BAR-P0（baostock 为主候选；本票 ponytail 选 mootdx 因 DCP-05 S08 已绿）

## Caveats

- Layer5 **不**写 DB evidence_chain 表（023A foundation slice）；本票验证 **domain record + lineage envelope**
- `schema_hash` 不在 `SourceProvenance` 一等字段；经 `source_dataset_ids` 锚定（ADR-031）
- Live fetch 非 Plan/Execute 默认路径；replay fixture 满足 ACC G5 子集
