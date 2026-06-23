# Registry Drift Table — R3Y-AUD-06

> 生成：2026-06-23 · 只读反证审计 · 基准：`master` @ `61436a51`（派发计划）

## 图例

| Drift class | 含义 |
|-------------|------|
| **A** | 报告/merge CLOSED，registry 仍 OPEN / 缺行 |
| **B** | registry RESOLVED，secondary docs 仍 OPEN |
| **C** | registry 节内 state 与 RESOLVED/UNRESOLVED 分裂 |
| **OK** | 三方一致 |

## 主表 — post-14 / PROMPT_11–17 关键 ID

| ID | Merge / 报告声称 | AUDIT_DEFERRED | UNRESOLVED | RESOLVED | Drift | 严重度 |
|----|------------------|----------------|------------|----------|-------|--------|
| `R3-PROMPT14-STAGED-01` | CLOSED@Slice2 · `PILOT_PASS_STAGED_RAW` | DEFERRED 节 orphan 行（无 State 列）`:112` | Moved to RESOLVED 注记 `:78` | Closed 2026-06-22 `:18` | **C** | WARN |
| `R3-PROMPT14-AKSHARE-VAL-01` | CLOSED@Slice2（登记 defer） | DEFERRED `:110` | DEFERRED `:76` | — | OK | — |
| `R3-B2.75-REQ2-EM` | 硬约束 · 不得闭合 | DEFERRED `:102` | DEFERRED `:31` | — | OK | — |
| `R3-AUDIT-DEF-03` | CLOSED@Slice3 → RESOLVED | 已移除 DEFERRED | 无 OPEN 行 | Closed 2026-06-22 `:11` | **B**（Plan 索引） | WARN |
| `R2-RISK-3` | CLOSED@Slice4 · UNSUPPORTED_MODES | 已移除 DEFERRED | 无 OPEN 行 | Closed 2026-06-22 `:12` | **B**（Plan 索引 + ROUND2_GAPS） | WARN |
| `R3-PARTIAL-1` | narrative rewrite CLOSED@Slice2 | DEFERRED（ADR 剩余）`:61` | DEFERRED `:33` | — | OK（有意保留 defer） | — |
| `ADV-R3X-*`（PROMPT_15 fixable） | merge_gate OPEN=0 · 73 FIXED/ALREADY_CLOSED | §PROMPT_15 RESOLVED `:135-140` | — | 伞测证据 | OK | — |
| `ADV-R3X-LINEAGE-001` | OUT_OF_SCOPE · Batch 4/5 defer（PROMPT_15） | **缺行** | **缺行** | — | **A** | HIGH |
| `B2.5-O-03` | app-layer closed | DEFERRED 节 · phase=Closed `:92` | Moved to RESOLVED `:68` | Closed 2026-06-21 `:33` | **C** | WARN |
| `R3-B25-DOC-01` / `A08-P1-02` / `R3-B25-HYG-04` | Batch 2.5 closed | — | 无 OPEN | RESOLVED | OK | — |
| `R3-B25-HYG-03` | CI/Batch6 defer | DEFERRED `:104` | DEFERRED `:66` | — | OK | — |
| Bucket B 53 项 | CLOSED@Slice4+4b remaining=0 | — | — | ponytail §11 delta | OK | — |
| `BLOCK-R3-001` / `002` | CLEAR | — | CLEAR `:11-12` | — | OK | — |

## Secondary docs 漂移（registry 已赢、索引未跟）

| ID | RESOLVED 证据 | 仍声称 OPEN 的文件 | 行号 |
|----|---------------|-------------------|------|
| `R3-AUDIT-DEF-03` | `RESOLVED_ISSUES_REGISTRY.md:11` | `UNRESOLVED_ITEM_TASK_COVERAGE.md` | `:27` |
| `R3-AUDIT-DEF-03` | 同上 | `ROUND3_EARLY_CLOSE_PLAN.md` | `:27` |
| `R2-RISK-3` | `RESOLVED_ISSUES_REGISTRY.md:12` | `UNRESOLVED_ITEM_TASK_COVERAGE.md` | `:46` |
| `R2-RISK-3` | 同上 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` Batch 6 表 | `:281`, `:328` |
| `R2-RISK-3` | 同上 | `ROUND2_GAPS_AND_DEVIATIONS.md` §4 | `:146` |
| `R2-RISK-3` | 同上 | `008_implement_write_manager.md` | `:120` |
| `R2-RISK-3` | 同上 | `034_implement_docs_consistency_check.md` | `:125` |

## post-14 报告 ↔ registry 快照

| post-14 finding | 报告状态 | Registry 对齐 | 备注 |
|-----------------|----------|---------------|------|
| ADV-POST14-A-009 | CLOSED@Slice2 | `R3-PROMPT14-AKSHARE-VAL-01` 双 registry | OK |
| ADV-POST14-A-010 | CLOSED@Slice2（cross-ref only） | `R3-B2.75-REQ2-EM` 仍 DEFERRED | OK |
| ADV-POST14-A-016 | CLOSED@Slice2 | RESOLVED + AUDIT_DEFERRED orphan | C |
| ADV-POST14-B-001 | CLOSED@Slice2 | `adversarial_audit_report.md` 历史快照 banner | OK |
| ADV-POST14-B-003 | CLOSED@Slice2 | PONYTAIL SC-05 §10 delta | OK |
| ADV-POST14-B-004 | CLOSED@Slice2 | R3-PARTIAL-1 叙事 | OK |
| ADV-POST14-B-008 | CLOSED@Slice4 | `R2-RISK-3` RESOLVED | B in Plan docs |
| ADV-POST14-B-011 | CLOSED@Slice2 | 同 A-009 | OK |
| Registry/docs drift (hygiene) | CLOSED@hygiene | map checkpoint `4114fcb0` | OK for map header; Batch 6 表见上 |

## pytest 守门覆盖缺口

| 断言域 | `test_round3_audit_registry_alignment` | 本表 Drift |
|--------|----------------------------------------|------------|
| post-14 registry 交叉引用 | 18 tests PASS | — |
| `ADV-R3X-LINEAGE-001` in registry | 未覆盖 | H01 |
| Plan 索引 vs RESOLVED 新鲜度 | 未覆盖 | W01 |
| AUDIT_DEFERRED 节内 RESOLVED 项 | 未覆盖 | W02 |

## 汇总

| 严重度 | 计数 | 阻塞下一批？ |
|--------|------|--------------|
| HIGH | 1 | 否（登记缺失，非错误闭合） |
| WARN | 3 类（Plan 索引、DEFERRED 排版、测试覆盖） | 否 |
| OK | post-14 主路径 + PROMPT_15 fixable set | — |

**总体：** 三 registry 操作面（UNRESOLVED/RESOLVED 分裂 + post-14 关键交叉引用）**可用**；须在下一 registry hygiene slice 修补 LINEAGE defer 登记与 Plan 索引滞后，避免 Plan agent 误读已闭合项或漏读硬排除项。
