# AUDIT.plan — M-DATA-03（Plan R2）

> **追溯：** `EXECUTION_INDEX.md` · `research/00-EXECUTION-ENTRY.md`  
> **说明：** Audit 执行产物归档 `archive/audit/`；本文件为 Plan freeze 门禁模板

## §0.1 Trace Authority Set

| 类别         | 文件                                                     |
| ------------ | -------------------------------------------------------- |
| 用户 AC      | `research/plan-revision-r2.md` §2                        |
| 切片 AC      | `research/to-issues-slices.md`                           |
| 规格         | `research/plan-spec.md` · `live_tier_a_evidence_v1.yaml` |
| Execute 入口 | `research/00-EXECUTION-ENTRY.md`                         |
| Plan 5d      | `research/integration-audit.md`                          |

## §1 覆写

- **任务：** M-DATA-03 R2 — 11 源 R4 真网完整验收（无 SKIP）
- **PASS 门槛：** `plan-revision-r2.md` §2 十条 · 11/11 live · pytest 全绿 · 零主库污染

## §2 验证矩阵（R2）

| 维  | 要点                                         |
| --- | -------------------------------------------- |
| A1  | plan-revision-r2 / plan-spec / contract 一致 |
| A2  | 无新 migration；clean 矩阵不变               |
| A3  | 无 `参考项目` runtime import                 |
| A4  | 11 源统一验收层 + manifest                   |
| A5  | F0 四族；**无 SKIP pass**                    |
| A6  | B2 validate_table 11/11                      |
| A7  | dispatch 去重；mootdx matrix                 |
| A8  | CI workflow + `uv run pytest -q`             |

## §3 台账

- Plan R2 文档包：PASS（`integration-audit.md`）
- Execute：待 `task.py start` 后重审
