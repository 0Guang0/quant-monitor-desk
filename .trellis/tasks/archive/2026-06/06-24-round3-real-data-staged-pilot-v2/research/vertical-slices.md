# Vertical Slices — Phase 3.5 /to-issues

> 工单 ID = R3Y-SP2-01..09；Execute 不得合并为单脚本跑通

| ID         | 标题                                 | 建设内容                                                        | 验收标准                                   | 依赖           | 证据输出                              | 测试计划                                         |
| ---------- | ------------------------------------ | --------------------------------------------------------------- | ------------------------------------------ | -------------- | ------------------------------------- | ------------------------------------------------ |
| R3Y-SP2-01 | Pilot v2 plan/caps                   | `PILOT_ID_V2`、caps YAML/JSON、sandbox 路径、批准 envelope 扩样 | caps 与 ResourceGuard 一致；禁止 full scan | PROMPT_14 基线 | `pilot_v2_caps.json`                  | RED: caps 超界拒绝；GREEN: 合法 envelope 通过    |
| R3Y-SP2-02 | baostock expanded                    | 3–5 symbols × 20–60 交易日；raw/staging manifest v2             | content_hash / source_fetch_id / path 齐全 | SP2-01         | `raw_evidence_manifest_v2.json` 等    | RED: 超 cap 拒绝；GREEN: manifest 字段断言       |
| R3Y-SP2-03 | cninfo expanded                      | announcement/filing metadata 小样本                             | 字段结构可验证                             | SP2-01         | `cninfo_schema_notes_v2.md`           | RED/GREEN: schema 必需字段                       |
| R3Y-SP2-04 | akshare retry/re-defer               | validation-only 重试；taxonomy                                  | NETWORK_ERROR/SUCCESS/EMPTY 分类           | SP2-01         | `akshare_validation_taxonomy_v2.json` | RED: 非 validation op 拒绝；GREEN: taxonomy 记录 |
| R3Y-SP2-05 | route matrix v2                      | selected/skipped/disabled/validation-only/auth-required         | 矩阵 JSON 全状态                           | SP2-01..04     | `route_preview_matrix_v2.json`        | 扩展现有 route preview 测试                      |
| R3Y-SP2-06 | validation report v2                 | staging 上跑 validation gate 摘要                               | field/schema/row_count/quality_flags       | SP2-02..03     | `validation_report_v2.json`           | RED: 缺 staging 失败；GREEN: 报告字段            |
| R3Y-SP2-07 | conflict summary v2                  | primary-vs-validation 或 deferred reason                        | conflict JSON                              | SP2-06         | `conflict_check_summary_v2.json`      | 冲突规则对照测试                                 |
| R3Y-SP2-08 | no-mutation proof v2 + MUT-PROOF-001 | DB 存在/缺失；**收紧 proof_status**                             | hash+count gate；`no_mutation_proof_v2.md` | AUD-04         | `no_mutation_proof_v2.md`             | 对抗 mutation fixture 测试                       |
| R3Y-SP2-09 | close/re-defer matrix                | per source/domain 决策                                          | `pilot_v2_closeout.json`                   | SP2-01..08     | `pilot_v2_closeout.json`              | closeout 字段完整性测试                          |
