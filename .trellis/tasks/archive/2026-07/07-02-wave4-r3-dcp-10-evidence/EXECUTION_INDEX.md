# 执行索引 — R3-DCP-10 Layer5 证据绑真源（Plan v4.1）

> Execute 首读：`research/00-EXECUTION-ENTRY.md`

## 0. 冻结元数据

| 字段          | 值                                                                   |
| ------------- | -------------------------------------------------------------------- |
| slug          | `wave4-r3-dcp-10-evidence`                                           |
| protocol      | `4.1`                                                                |
| execute_entry | `research/00-EXECUTION-ENTRY.md`                                     |
| source_card   | `docs/implementation_tasks/.../R3_DCP_10_LAYER5_EVIDENCE_BINDING.md` |
| frozen_card   | `frozen/R3_DCP_10_LAYER5_EVIDENCE_BINDING.md`                        |

## 1. 步骤与证据（Execute）

| Step  | 切片     | 证据路径                               |
| ----- | -------- | -------------------------------------- |
| [x] 1 | S00-BOOT | boot 声明                              |
| [x] 2 | S01      | `execute-evidence/s01-{red,green}.txt` |
| [x] 3 | S02      | `execute-evidence/s02-{red,green}.txt` |
| [x] 4 | S03      | `execute-evidence/s03-green.txt`       |
| 5     | Audit    | `research/audit-a*-report.md`          |

切片 AC SSOT：`research/to-issues-slices.md`

## 2.1 复验命令（Repair / Audit 关账）

```bash
uv run pytest tests/test_layer5_evidence_foundation.py tests/test_mootdx_incremental_e2e.py -q
uv run pytest -q
uv run python scripts/loop_maintain.py --fix
```

## 2. AC ↔ 测试

| AC              | 验证                                                                            |
| --------------- | ------------------------------------------------------------------------------- |
| provenance 映射 | S01 Execute 新建 test_layer5_provenance_bridge 模块                             |
| mootdx e2e      | S02 Execute 新建 test_layer5_mootdx_bar_clean_e2e 模块                          |
| 回归基线        | tests/test_layer5_evidence_foundation.py · tests/test_mootdx_incremental_e2e.py |
| ACC G5 子集     | S03 台账 + pytest 全绿                                                          |

## 3. 必须读原文（manifest）

| path                                                                 | manifest  | for              |
| -------------------------------------------------------------------- | --------- | ---------------- |
| `docs/decisions/ADR-031-dcp10-layer5-evidence-provenance-binding.md` | must-read | both · S01+      |
| `docs/modules/layer5_security_evidence.md`                           | must-read | both · S01+      |
| `scripts/loop_maintain.py`                                           | must-read | both · loop 维护 |

## 4. 已并入冻结任务卡

v4.1 薄指针 — 规格在 Execution Bundle。

## 5. Audit 追溯集

| 类别   | 文件                                          |
| ------ | --------------------------------------------- |
| frozen | `frozen/R3_DCP_10_LAYER5_EVIDENCE_BINDING.md` |
| entry  | `research/00-EXECUTION-ENTRY.md`              |
| index  | 本文件                                        |
| slices | `research/to-issues-slices.md`                |
