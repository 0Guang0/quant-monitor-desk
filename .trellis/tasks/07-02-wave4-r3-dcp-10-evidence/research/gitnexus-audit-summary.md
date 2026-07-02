# GitNexus Audit Summary — R3-DCP-10（7.pre）

> **日期：** 2026-07-02 · Repair A9 · 派发 A1–A8 后刷新  
> **分支：** `feature/wave4-r3-dcp-10-evidence` · worktree `quant-monitor-desk-wt-dcp10`  
> **索引状态：** stale — `build_source_provenance_from_bundle` / `bundle_layer5_provenance` 扩展未 re-index；Repair 后建议 `node .gitnexus/run.cjs analyze`

## query: layer5 evidence provenance bundle mootdx

命中：`Layer5LineageBuilder` · `EvidenceFoundationValidator` · `foundation.py` · `lineage.py` · `test_layer5_evidence_foundation.py`

## context / impact

| 符号 | 结果 | 备注 |
| --- | --- | --- |
| `build_source_provenance_from_bundle` | not found（新文件） | Repair 新增 `layer5_evidence/provenance.py` |
| `bundle_layer5_provenance` | not found（扩展后） | `evidence_bundle.py` additive 扩展 |
| `Layer5LineageBuilder` | found | incoming: tests + `__init__.py` re-export |
| `ConnectionManager` | HIGH upstream | e2e 均 `tmp_path` 隔离 `db_path` |

## detect_changes（worktree uncommitted）

| 项 | 值 |
| --- | --- |
| changed_files | 4+（provenance.py · evidence_bundle · layer5 tests） |
| changed_symbols | 0（索引滞后） |
| risk_level | low |

## 审计焦点符号（Repair 触面）

| 符号/区域 | 用途 |
| --- | --- |
| `build_source_provenance_from_bundle` | S01 ADR-031 bridge |
| `bundle_layer5_provenance` | schema/domain/clean dataset id 编码 |
| `incremental_mootdx_support` | S02 e2e 共享 bootstrap |
| `load_mootdx_raw_bundle_from_fetch_log` | fetch_log 绑真源路径（避免深 glob） |
| `path_compat.read_bytes` | Windows audit basetemp 长路径读 |
