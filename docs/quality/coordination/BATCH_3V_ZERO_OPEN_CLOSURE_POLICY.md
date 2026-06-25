# Batch 3V 零遗留闭合策略

> **生效：** 2026-06-25 · 对齐 `BATCH_01_ZERO_OPEN_CLOSURE_POLICY.md`  
> **规则：** 六路分支所有 **BLOCKING** 与 **NON-BLOCKING** OPEN 项必须修复或书面 re-defer（owner、phase、closure test）；**禁止**以「条件可验收」「主会话稍后」留 OPEN。

## 闭合定义

| 类型                  | 闭合条件                                                                                                                                    |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| BLOCKING              | 代码/测试/证据修复 + 复验通过                                                                                                               |
| NON-BLOCKING          | 同上，或 ADR/wont-fix + registry re-defer + 负向测试                                                                                        |
| RECONCILE_STALE       | 审计项已由 post Batch 01 master 关闭 → reconciliation note + registry 更新；**禁止**重复实现                                                |
| HANDOFF_3F            | `VR-SYNC-001` 等范围过大 → Round 3F.4 handoff 含 owner、entrypoints、closure tests                                                          |
| loop/catalog          | `loop_maintain --fix` + **同分支 commit** 生成物                                                                                            |
| manifest 规划 vs Done | **规划期** 允许 `FINAL_AUDIT_REPORT.md` missing 仅当 `DEBT.plan` 有 restore-or-replace 切片；**Done** 要求 `check_manifest_files.py` exit 0 |
| 未 commit             | **BLOCKING** — 闭合前必须 commit 交付物                                                                                                     |

## 跨分支依赖

1. **B3V-OPS** → 先于 **B3V-SYNC** 合并（推荐）— write-mode 契约稳定后再审 crash-window
2. **B3V-REG** / **B3V-L5R** → 可先合并；不得阻塞代码线但 registry 行须主会话统一闭合
3. **Registry** → 主会话 §7.3 批处理；agent 仅 proposed delta
4. **L5R runtime follow-up** → 若核对发现缺口，**新分支**；不得在 reconcile 分支默认改 `layer5_evidence/**`

## 验收

每分支 Done 前：`uv run pytest -q` 全绿 + owned `VR-*` 清单 **0 OPEN** + closure report 九项（父 README §5）。

## Playbook

`docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_COORDINATOR_PLAYBOOK.md`
