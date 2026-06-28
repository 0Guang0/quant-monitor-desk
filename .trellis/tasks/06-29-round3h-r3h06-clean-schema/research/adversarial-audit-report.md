# 对抗性审计闭环 — R3H-06 Clean Schema

> **来源：** code-reviewer subagent @ 2026-06-29  
> **主会话复核：** 2026-06-29  
> **裁决：** 全部 BLOCKING 已 **fixed**；NON-BLOCKING 已 **fixed** 或 **waived**

## BLOCKING 闭环

| id  | 描述                             | 状态      | 修复落点                                             |
| --- | -------------------------------- | --------- | ---------------------------------------------------- |
| B01 | frozen 任务卡缺失                | **fixed** | `frozen/R3H_06_CLEAN_SCHEMA.md` @ freeze-task-card   |
| B02 | implement.jsonl 与 INDEX §3 漂移 | **fixed** | `generate-manifests` — 24 条 manifest                |
| B03 | check.jsonl 空壳                 | **fixed** | 本文件同批写入 trace 条目                            |
| B04 | 活卡 VIEW 自相矛盾               | **fixed** | `R3H_06_CLEAN_SCHEMA.md` §1.1 仅「无 VIEW」          |
| B05 | to-issues S7 仍为 PILOT-VIEW     | **fixed** | `to-issues-slices.md` S8=`PILOT-NO-VIEW`             |
| B06 | AC-CNINFO 验收方向错误           | **fixed** | `EXECUTION_INDEX.md` §2 + 活卡 §9.2                  |
| B07 | 三域 staging 未设计              | **fixed** | 活卡 §9.3–9.4；014 OHLCV + `stg_disclosure_smoke`    |
| B08 | G6 与 append_only 冲突           | **fixed** | 活卡 §9.5 `clean_write_targets.py`；9.7 真实 promote |
| B09 | 9.8 rg 门禁不可执行              | **fixed** | 活卡 §9.8.1 + `EXECUTION_INDEX.md` §1.1              |
| B10 | plan.freeze 缺 §3.0b             | **fixed** | `plan.freeze.md` §3.0b 已补                          |

## NON-BLOCKING 闭环

| id   | 描述                          | 状态       | 说明                                                                                |
| ---- | ----------------------------- | ---------- | ----------------------------------------------------------------------------------- |
| NB01 | MANIFEST 缺 R3H-06            | **fixed**  | `BATCH_3H_TASK_CARD_MANIFEST.md` PASS 波次表                                        |
| NB02 | G5 无独立 §5.0.1 ID           | **waived** | `EXECUTION_INDEX.md` §0.1 + `original-plan-trace.md` 已注明由 AC-CNINFO-NO-BAR 覆盖 |
| NB03 | macro_route vs domain_router  | **fixed**  | `spec-driven-development-notes.md` 统一 `-k domain_router`                          |
| NB04 | test_schema_contract 未绑步骤 | **fixed**  | `EXECUTION_INDEX.md` §1 9.1 含 `test_schema_contract.py`                            |
| NB05 | rollback 仅在 research        | **fixed**  | 活卡 §9.9 + `EXECUTION_INDEX.md` AC-DOCS                                            |
| NB06 | adjustment_type 未写 AC       | **fixed**  | `EXECUTION_INDEX.md` §2 AC-SCHEMA-G4-OHLCV                                          |
| NB07 | pdf_file_id 无专测            | **waived** | Execute 9.2 disclosure_ddl 可选 fixture；非 Plan 阻塞                               |
| NB08 | filing_id 归一化              | **fixed**  | 活卡 §9.4 + AC-STG-DISCLOSURE                                                       |
| NB09 | sandbox 仅 cn_announcements   | **waived** | 活卡 §8 pilot 范围注记；三 data_domain 列预留                                       |
| NB10 | context_pack 空               | **fixed**  | `scripts/context_router.py --task` 已刷新                                           |
| NB11 | gitnexus-audit-summary 未建   | **waived** | Execute 完成后 Audit 7.pre 交付                                                     |
| NB12 | INDEX §4 VIEW 摘要            | **fixed**  | `EXECUTION_INDEX.md` §4 已改「无 VIEW」                                             |
| NB13 | brainstorm/overview VIEW 残留 | **fixed**  | 本批修正 L17/L37                                                                    |

## 建议改进采纳

| #   | 建议                     | 采纳                                  |
| --- | ------------------------ | ------------------------------------- |
| 1   | 9.4 拆 macro mapper      | 活卡 9.5b 并入 `-k domain_router`     |
| 2   | disclosure staging 专步  | 活卡 9.4 + 014/013                    |
| 3   | 9.8 文件清单             | 活卡 §9.8.1 后清单                    |
| 4   | 013 范围澄清             | 活卡 9.1/9.2 + MIGRATION_COVERAGE 9.9 |
| 5   | 014 OHLCV migration      | 活卡 9.3                              |
| 6   | cninfo 负向断言          | 活卡 9.6 + AC-CNINFO-NO-BAR           |
| 7   | INDEX forbidden registry | `EXECUTION_INDEX.md` §3.1             |
| 8   | Tier D 主库禁止          | AUDIT A7 + 活卡 §8                    |

**总裁决（Plan 期）：** 对抗项已全部闭环；`validate-plan-freeze` **exit 0** @ 2026-06-29。待用户批准 → `task.py start` Execute。
