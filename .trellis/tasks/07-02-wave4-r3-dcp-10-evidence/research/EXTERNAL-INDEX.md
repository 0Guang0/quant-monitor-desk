# EXTERNAL-INDEX — R3-DCP-10

> 包外必读 · Plan v4.1

---

## §A — 切片开工前必读（外部）

| 路径 | 用途 |
| --- | --- |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_10_LAYER5_EVIDENCE_BINDING.md` | 活卡 §1–§7 |
| `docs/modules/layer5_security_evidence.md` | Layer5 模块权威 |
| `docs/decisions/ADR-031-dcp10-layer5-evidence-provenance-binding.md` | P0 + provenance 映射 |
| `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md` | clean 域 |
| `docs/decisions/ADR-027-r3h08-product-live-env-gate.md` | live 政策 |
| `specs/contracts/reference_adoption_guardrails.yaml` | L 梯铁律 |
| `specs/contracts/snapshot_lineage_contract.yaml` | lineage 字段 |
| `specs/model_inputs/layer5_instrument_source_plan.yaml` | L5 输入计划 |
| `docs/quality/待修复清单.md` | ACC-LAYER-E2E G5 |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` | R3-DCP-10 行 |
| `.trellis/tasks/wave4-r3-dcp-05-tier-a/research/00-EXECUTION-ENTRY.md` | DCP-05 clean 写路径（只读） |

---

## §B — 执行情境路由（外部）

| 情境 | 路径 |
| --- | --- |
| DCP-05 mootdx e2e | `tests/test_mootdx_incremental_e2e.py` |
| Layer5 foundation 先例 | `tests/test_layer5_evidence_foundation.py` |
| raw store lineage | `tests/test_raw_store.py` |
| R3H-08 live gate | `docs/decisions/ADR-027-r3h08-product-live-env-gate.md` |
| Wave 5 GATE | `PROJECT_IMPLEMENTATION_ROADMAP.md` R3H-05 |

---

## §C — 源码/测试字典

| 符号/路径 | 说明 |
| --- | --- |
| `bundle_layer5_provenance` | `backend/app/datasources/normalizers/evidence_bundle.py` |
| `cn_market_bundle_layer5_provenance` | `backend/app/datasources/normalizers/cn_market.py` |
| `Layer5LineageBuilder` | `backend/app/layer5_evidence/lineage.py` |
| `EvidenceFoundationValidator` | `backend/app/layer5_evidence/foundation.py` |
| `SourceProvenance` | `backend/app/layer5_evidence/models.py` |
| `create_mootdx_fetch_port` | `backend/app/datasources/fetch_ports/mootdx_port.py` |
| `run_mootdx_bar_incremental` | `backend/app/ops/mootdx_incremental_run.py` |
| `RawStore` | `backend/app/storage/raw_store.py` |
| `assert_layer5_factual_source_record` | `tests/conftest_layer_smoke.py` |
| `SYMBOL` / `FIXTURE_DATE` | `tests/incremental_mootdx_support.py` |

---

## §8 活卡说明

活卡保留在 `docs/implementation_tasks/.../R3_DCP_10_LAYER5_EVIDENCE_BINDING.md`；冻结薄指针见 `frozen/R3_DCP_10_LAYER5_EVIDENCE_BINDING.md`。
