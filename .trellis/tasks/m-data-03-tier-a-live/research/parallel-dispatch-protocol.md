# M-DATA-03 并行 Execute 派发协议（Plan R2）

> **峰值 2–3 agent** · **合并顺序强制**

---

## 1. R2 切片编制

| 批次 | 角色                  | 切片                  | 串/并                                                       |
| ---- | --------------------- | --------------------- | ----------------------------------------------------------- |
| 1    | Evidence agent ×1     | S-R2-EVIDENCE         | 串行（全员阻塞）                                            |
| 2    | Quality agent ×1–2    | S-R2-F0 ∥ S-R2-B2     | **并行开发**                                                |
| 2    | Infra agent ×1        | S-R2-DISPATCH         | **须在 EVIDENCE merge 后**；可与批次 2 Quality **并行开发** |
| 3    | Close agent（主会话） | S-R2-ACCEPT → S-R2-CI | 串行                                                        |

**禁止：** 11 源 11 agent；两 agent 同时改 `tier_a_live_incremental_dispatch.py`。

## 2. Merge 顺序（强制）

```text
EVIDENCE → (F0 ∥ B2) → DISPATCH → ACCEPT → CI
```

开发可并行，**合并不得跳序**。ACCEPT 前须 F0 + B2 + DISPATCH 均已 merge。

## 3. Boot（每 agent）

1. `00-EXECUTION-ENTRY.md` §1–§4
2. `plan-revision-r2.md` §2
3. `to-issues-slices.md` 本切片
4. GitNexus `impact()`
5. `reference-adoption-m-data-03.md`（若涉借鉴）

## 4. Worktree（建议）

| Worktree              | Branch                          | 切片                |
| --------------------- | ------------------------------- | ------------------- |
| `wt-mdata03-evidence` | `feature/m-data-03-r2-evidence` | S-R2-EVIDENCE       |
| `wt-mdata03-quality`  | `feature/m-data-03-r2-f0-b2`    | S-R2-F0 · S-R2-B2   |
| `wt-mdata03-dispatch` | `feature/m-data-03-r2-dispatch` | S-R2-DISPATCH       |
| main session          | `feature/m-data-03-tier-a-live` | ACCEPT · CI · merge |

## 5. 参考实读

落盘：`research/archive/non-plan/execute/execute-reference-read-evidence-<branch>.md`  
**注意：** 归档内 R1 切片名（S-ACCEPT）已作废；以 S-R2-\* 为准。

## 6. 文件锁表

| 路径                                                                    | 独占切片                        |
| ----------------------------------------------------------------------- | ------------------------------- |
| `scripts/tier_a_live_acceptance.py` · manifest 写入                     | S-R2-EVIDENCE（后 ACCEPT 集成） |
| `backend/app/ops/data_health/*`                                         | S-R2-F0                         |
| `backend/app/validation/data_quality_validator.py` · acceptance B2 接线 | S-R2-B2                         |
| `tier_a_live_incremental_dispatch.py` · `platform_source_matrix.yaml`   | S-R2-DISPATCH                   |
| `.github/workflows/*tier*a*`                                            | S-R2-CI                         |
| `loop_maintain.py` / registry 三件套                                    | **主会话 only**                 |

Registry / `loop_maintain.py`：**主会话**统一跑。
