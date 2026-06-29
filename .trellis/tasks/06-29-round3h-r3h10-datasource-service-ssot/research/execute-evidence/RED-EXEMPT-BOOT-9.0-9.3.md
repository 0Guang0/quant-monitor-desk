# RED 豁免说明 — S10-BOOT (9.0) · S10-03 (9.3)

> handoff 校验不要求 9.0-red / 9.3-red；本文件为 Audit A7/A8 书面豁免 SSOT。

| 步                | 为何无 RED                                          | 替代证据                                                          |
| ----------------- | --------------------------------------------------- | ----------------------------------------------------------------- |
| **9.0 BOOT**      | 切片交付文档矩阵 + 全量 pytest 基线；无单点行为 RED | `9.0-green.txt` + `bypass-baseline-matrix.md`                     |
| **9.3 rehearsal** | 文档/守卫切片；GREEN 前无 failing 行为测目标        | `9.3-green.txt` + `test_production_live_pilot_policy.py -k r3h10` |

Execute SSOT 证据路径：`research/execute-evidence/`（非任务根 `execute-evidence/`）。
