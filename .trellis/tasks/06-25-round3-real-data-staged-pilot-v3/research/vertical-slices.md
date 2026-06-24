# Vertical Slices — Phase 3.5 /to-issues

> 工单 ID = R3E-SP3-01..07；Execute 不得合并为单脚本跑通

| ID | 标题 | 建设内容 | 验收标准 | 依赖 | 证据输出 | 测试计划 |
| --- | --- | --- | --- | --- | --- | --- |
| R3E-SP3-01 | Whitelist input loader | 从 `specs/model_inputs/**` 加载 baostock/cninfo/akshare 子集；cap 校验；whitelist hash 写入 caps | 无 WL 拒绝；超 symbol/row 拒绝 | **B01-WL 已合并** | `pilot_v3_caps.json` + `whitelist_ref.json` | RED: 缺 WL FAIL；GREEN: fixture WL 通过 cap |
| R3E-SP3-02 | baostock daily expansion | 5–20 WL symbols × 30–120 日；raw/staging manifest v3 | source_fetch_id/content_hash/as_of 齐全 | SP3-01 | `raw_evidence_manifest_v3_baostock.json` 等 | RED: 超 cap；GREEN: manifest 字段 |
| R3E-SP3-03 | cninfo metadata expansion | WL issuers/symbols；metadata-only；拒绝 PDF/full-text | 无 bulk PDF 路径 | SP3-01 | `cninfo_schema_notes_v3.md` | RED: PDF op 拒绝；GREEN: metadata manifest |
| R3E-SP3-04 | akshare validation-only | validation op only；failure taxonomy；不得 Primary | `R3-PROMPT14-AKSHARE-VAL-01` 证据或 re-defer | SP3-01 | `akshare_validation_taxonomy_v3.json` | RED: primary 路由拒绝；GREEN: taxonomy |
| R3E-SP3-05 | conflict dry-run summary | baostock vs akshare mismatch → summary；无 clean 覆盖 | conflict JSON；dry-run only | SP3-02,04 | `conflict_check_summary_v3.json` | RED: clean write 尝试失败；GREEN: summary |
| R3E-SP3-06 | closeout / readiness matrix | per source/domain 决策；no-mutation；registry proposed delta | 无 production-live 声称 | SP3-01..05 | `pilot_v3_closeout.json`, `source_readiness_matrix_v3.md`, `no_mutation_proof_v3.md` | RED: 缺证据字段；GREEN: closeout 完整 |
| R3E-SP3-07 | merge gate regression | playbook §8.6 五命令 + Tier A/B/C | 全 AC 回归绿 | SP3-01..06 | `9.7-green.txt` | RED: 任一步回归红；GREEN: 全库 pytest + ruff + compileall |
