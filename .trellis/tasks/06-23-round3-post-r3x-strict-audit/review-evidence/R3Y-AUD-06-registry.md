# R3Y-AUD-06 — Registry consistency 反证

**Result:** WARN

## 目标与反证假设

验证三份 registry（`AUDIT_DEFERRED` / `UNRESOLVED` / `RESOLVED`）与 post-14 审计报告、PROMPT_11–17 merge gate 是否一致；反证假设：**存在「报告/merge gate 声称 CLOSED，但 registry 或 Plan 索引仍当 OPEN」的静默漂移**。

## 读取文件（含 call path 追溯）

| 类别 | 路径 |
|------|------|
| 派发 / 任务卡 | `.trellis/tasks/06-23-round3-post-r3x-strict-audit/research/parallel-audit-dispatch.md` · `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_post_r3x_strict_adversarial_audit.md` §R3Y-AUD-06 |
| 三 registry SSOT | `docs/AUDIT_DEFERRED_REGISTRY.md` · `docs/UNRESOLVED_ISSUES_REGISTRY.md` · `docs/RESOLVED_ISSUES_REGISTRY.md` |
| post-14 报告 | `docs/quality/adversarial_audit_post14_contract_ponytail_lane.md` · `docs/quality/adversarial_audit_post14_ops_data_lane.md` · `docs/quality/adversarial_audit_post14_master_fix_manifest.md` · `docs/quality/adversarial_audit_report.md` |
| merge evidence | `.trellis/tasks/fix-round3-r3x-residual-open-items-closure/execute-evidence/merge_gate_report.md` · `.trellis/tasks/fix-round3-post14-audit-registry-docs/execute-evidence/slice2-registry-red-green.txt` · `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/merge_gate_report.md` |
| Plan 索引（二次漂移面） | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` · `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md` · `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md` · `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/ROUND2_GAPS_AND_DEVIATIONS.md` |
| 自动化守门 | `tests/test_round3_audit_registry_alignment.py` |

## 核查方法（code trace + pytest 命令与结果）

1. **全文读三 registry** — 核对 post-14 闭合项（`R3-AUDIT-DEF-03`、`R2-RISK-3`、`R3-PROMPT14-STAGED-01`、`R3-PROMPT14-AKSHARE-VAL-01`、`R3-B2.75-REQ2-EM`、PROMPT_15 ADV-R3X 伞测）的 state 与交叉引用。
2. **对照 post-14 merge 报告** — `adversarial_audit_post14_*` 中 `CLOSED@Slice*` 行是否在 registry 有对应行或 RESOLVED 迁移注记。
3. **对照 PROMPT_15 merge_gate** — Master Checklist OPEN=0 与 `AUDIT_DEFERRED` §PROMPT_15 RESOLVED 节是否一致。
4. **Plan 索引反查** — `UNRESOLVED_ITEM_TASK_COVERAGE`、`ROUND3_BATCH_IMPLEMENTATION_MAP` Batch 6、`ROUND3_EARLY_CLOSE_PLAN` 是否仍引用已 RESOLVED 的 ID。
5. **必跑测试**：

```bash
cd quant-monitor-desk-wt-review-r3-post-r3x-strict-audit
uv run pytest tests/test_round3_audit_registry_alignment.py -q
```

**结果：** `18 passed in 0.09s`（exit 0）。日志：`.trellis/tasks/06-23-round3-post-r3x-strict-audit/review-evidence/r3y-aud-06-pytest.log`

## Findings

### HIGH

| ID | 文件:行号 | 描述 |
|----|-----------|------|
| R3Y-AUD-06-H01 | `docs/AUDIT_DEFERRED_REGISTRY.md:106-112` · PROMPT_15 §排除项 | **`ADV-R3X-LINEAGE-001`（L3/L4 完整 snapshot lineage）未在三份 registry 登记。** PROMPT_15 与 `R3X_residual_open_items_closure.md` 明确要求「仅允许文档/registry 登记 defer 至 Batch 4/5」；`adversarial_audit_report.md:422` 仅以叙事提及 `→ Batch 4/5 defer`，无 `AUDIT_DEFERRED` / `UNRESOLVED` 行。Plan agent 无法从 registry SSOT 发现该硬排除项。 |

### WARN

| ID | 文件:行号 | 描述 |
|----|-----------|------|
| R3Y-AUD-06-W01 | `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md:3,27,46` · `ROUND3_EARLY_CLOSE_PLAN.md:27` · `ROUND3_BATCH_IMPLEMENTATION_MAP.md:281,328` · `ROUND2_GAPS_AND_DEVIATIONS.md:146` | **已 RESOLVED 的 `R3-AUDIT-DEF-03`、`R2-RISK-3` 在 Plan 索引层仍当未闭合。** `RESOLVED_ISSUES_REGISTRY.md:11-12` 已 2026-06-22 闭合；`UNRESOLVED_ISSUES_REGISTRY` 无对应 OPEN 行（正确）。但 `UNRESOLVED_ITEM_TASK_COVERAGE`（Last reconciled 2026-06-21）仍要求补齐 scan cap / write_contract matrix；`ROUND3_BATCH_IMPLEMENTATION_MAP` Batch 6 仍列 `R2-RISK-3` 为待办。违反 registry §Resolution policy rule 4「Registry wins on conflict」的操作语义——secondary docs 未同步。 |
| R3Y-AUD-06-W02 | `docs/AUDIT_DEFERRED_REGISTRY.md:90-94,106-112` | **`AUDIT_DEFERRED` 结构漂移：已闭合项仍留在 DEFERRED 节。** `B2.5-O-03`（Resolution phase = Closed via app-layer）仍在 §DEFERRED Batch 2.5 表内，而 `RESOLVED_ISSUES_REGISTRY.md:33` 已迁移；`R3-PROMPT14-STAGED-01` 以 orphan 行挂在 §DEFERRED PROMPT_14 下（无表头、无 State 列），实际状态为 RESOLVED（`RESOLVED_ISSUES_REGISTRY.md:18`）。读者扫 DEFERRED 节可能误判为仍延期。 |
| R3Y-AUD-06-W03 | `tests/test_round3_audit_registry_alignment.py`（全文件） | **自动化守门覆盖 post-14 hygiene，但不覆盖 Plan 索引新鲜度与 LINEAGE defer 登记。** 18 项全绿证明 2026-06-22 post-14 slice 叙事与三 registry 核心交叉引用一致；无法捕获 W01/W02/H01 类 secondary-doc / 缺行漂移。 |

### 反证未成立（PASS 子项）

| 检查项 | 结论 | 证据 |
|--------|------|------|
| post-14 akshare validation re-defer | PASS | `R3-PROMPT14-AKSHARE-VAL-01` 在 `AUDIT_DEFERRED` + `UNRESOLVED` 双登记 DEFERRED；交叉引用 `R3-B2.75-REQ2-EM` |
| staged pilot closeout vs REQ2-EM | PASS | `R3-PROMPT14-STAGED-01` RESOLVED；`R3-B2.75-REQ2-EM` 保持 DEFERRED；merge 与 registry 均注明「不得因 staged pilot 单独闭合」 |
| PROMPT_15 Master Checklist | PASS | merge_gate OPEN=0；`AUDIT_DEFERRED` §PROMPT_15 RESOLVED；`test_r3x_residual_open_items_closure.py` 由 AUD-01 域覆盖 |
| post-14 ponytail / Bucket B | PASS | `PONYTAIL_MODULE_SCAN` §10/§11 delta；`adversarial_audit_post14_contract_ponytail_lane.md` 不再声称 53 项 OPEN |
| R3-PARTIAL-1 陈旧叙事 | PASS | 「skips validator」已从 registry 移除；`ADV-R3X-SYNC-002` 交叉引用保留 |

## 反证结论（修复是否进入 registry SSOT）

- **核心三 registry + post-14 自动化测试：一致。** 不存在「merge gate 声称 FIXED 但 UNRESOLVED 仍 OPEN」的高危漂移（针对 PROMPT_15 fixable set 与 post-14 hygiene slice）。
- **Secondary Plan 索引与 `AUDIT_DEFERRED` 排版：存在可操作的 WARN 漂移**；`ADV-R3X-LINEAGE-001` 缺 registry 行是唯一 HIGH（违反 PROMPT_15 显式 defer 登记要求）。
- **「报告 closed 但 registry 未闭合」反证：对 PROMPT_15/ post-14 主路径不成立；对 Plan 索引反方向成立（registry 已闭合、Plan 文档仍 OPEN）。**

## 阻塞项 / 建议

| 优先级 | 建议 | 归属 |
|--------|------|------|
| P1 | 在 `AUDIT_DEFERRED` + `UNRESOLVED` 新增 `ADV-R3X-LINEAGE-001` DEFERRED 行（Batch 4/5 · tasks 020–022 · closure test = L3/L4 snapshot lineage pytest） | registry/docs hygiene slice（非本审计分支） |
| P2 | 刷新 `UNRESOLVED_ITEM_TASK_COVERAGE.md`、`ROUND3_EARLY_CLOSE_PLAN.md` §Unresolved、移除 `ROUND3_BATCH_IMPLEMENTATION_MAP` Batch 6 中 `R2-RISK-3`；`ROUND2_GAPS` §4 标注 R2-RISK-3 → RESOLVED | 同上 |
| P2 | 将 `B2.5-O-03`、`R3-PROMPT14-STAGED-01` 从 `AUDIT_DEFERRED` DEFERRED 节迁至 RESOLVED 节或加显式「Moved to RESOLVED」注记 | 同上 |
| P3 | 扩展 `test_round3_audit_registry_alignment.py`：断言 `ADV-R3X-LINEAGE-001` 在 registry；或 `UNRESOLVED_ITEM_TASK_COVERAGE` reconciled 日期 ≥ post-14 merge | 测试增强（需新 slice） |

## Verification Story

| 项 | 状态 |
|----|------|
| Tests reviewed | 是 — `test_round3_audit_registry_alignment.py` 18/18；覆盖 post-14 B-001–B-011 / A-009–A-016 等 registry 叙事 |
| Build verified | 否 — 本 issue 只读；仅跑 registry 对齐测试 |
| Security checked | 不适用 |
| Registry 三文件互引 | 主路径一致；`AUDIT_DEFERRED` DEFERRED 节排版见 W02 |
| merge report vs registry | PROMPT_15 / post-14 slice 一致；Plan 索引见 W01 |

---

*Agent: R3Y-AUD-06 · Worktree: `quant-monitor-desk-wt-review-r3-post-r3x-strict-audit` · 基准 master @ 61436a51（派发计划）· 只读 · 未修改 registry/docs*
