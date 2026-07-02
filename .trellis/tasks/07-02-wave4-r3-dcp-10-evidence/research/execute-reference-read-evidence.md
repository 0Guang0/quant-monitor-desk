# Execute 参考实读证据 — R3-DCP-10 S01 RED 前

> 对照 `reference-adoption-dcp10.md` §1–§4 · ADR-031

## 实读清单

- [x] `参考项目/OpenBB/.../fetcher.py` L36–85 — **树不在 worktree**；采纳决策已冻结：transform 后读 bundle，不拷贝 Fetcher 类（`reference-adoption-dcp10.md` §2.1）
- [x] `参考项目/digital-oracle/.../bis.py` L54–66 — **树不在 worktree**；hash + fetch_id 必填 fail-closed 对齐 `read_cn_market_evidence_bundle`（§2.2）
- [x] `参考项目/EasyXT/.../unified_data_interface.py` L172–244 — **forbidden**；e2e 禁止 staged 占位 provenance（§2.3）
- [x] 仓内 `evidence_bundle.py` · `cn_market.py` · `test_mootdx_incremental_e2e.py` — P0 replay 金路径已绿

## S01 决策

- 扩展 `bundle_layer5_provenance`：`schema_hash` / `schema_version` / `clean` / `domain` → `source_dataset_ids`
- 新增 `layer5_evidence/provenance.py`：`build_source_provenance_from_bundle`
- 不新增 migration；不改 `SourceProvenance` dataclass 形状（ADR-031）
