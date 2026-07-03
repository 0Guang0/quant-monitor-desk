# DCP-06 并行 Execute Agent 派发协议

> **模型：** `composer-2.5`  
> **铁律：** 与主会话 Execute 一致 + 参考实读门禁

---

## 1. Phase 0 Boot（每 agent）

| #   | 动作                  | 路径                                                                             |
| --- | --------------------- | -------------------------------------------------------------------------------- |
| 0a  | 工程契约              | `agent-toolchain.md` · trellis-execute · reference · principles · project-global |
| 0b  | Bundle                | `00-EXECUTION-ENTRY.md` · `to-issues-slices.md` **本切片** · ADR-029             |
| 0c  | 路由                  | `EXTERNAL-INDEX.md` §A + `implement.jsonl`                                       |
| 0d  | 参考                  | `reference-adoption-dcp06.md` + guardrails.yaml                                  |
| 0e  | impact()              | 本切片 symbol                                                                    |
| 0f  | validate-execute-boot | `task.py validate-execute-boot .trellis/tasks/wave4-r3-dcp-06-five-axis-clean`   |

---

## 2. 参考实读门禁

全 agent 必读 §reference-adoption-dcp06.md §1–2。RED 前落盘 `execute-reference-read-evidence-<suffix>.md`。

---

## 3. 方案 B 分支

| Worktree                                | Branch                     | 切片 | 禁止并发拥有                  |
| --------------------------------------- | -------------------------- | ---- | ----------------------------- |
| `../quant-monitor-desk-wt-dcp06-core`   | `feature/dcp06-s00-core`   | S00  | `clean_observation_reader.py` |
| `../quant-monitor-desk-wt-dcp06-env`    | `feature/dcp06-s01-env`    | S01  | —                             |
| `../quant-monitor-desk-wt-dcp06-credit` | `feature/dcp06-s02-credit` | S02  | —                             |
| `../quant-monitor-desk-wt-dcp06-risk`   | `feature/dcp06-s03-risk`   | S03  | —                             |
| `../quant-monitor-desk-wt-dcp06-liq`    | `feature/dcp06-s04-liq`    | S04  | —                             |
| `../quant-monitor-desk-wt-dcp06-sent`   | `feature/dcp06-s05-sent`   | S05  | —                             |

**Base：** `feature/wave4-r3-dcp-06-five-axis-clean`（含 S00 merge）

**S06：** 主会话 only（集成 + K1 + 台账）

---

## 4. 禁止改

- `backend/app/sync/*` incremental / `clean_write_targets.py`（DCP-05）
- migration DDL

---

## 5. 收尾

```bash
uv run pytest -k "layer1 and clean_e2e" -q
uv run python scripts/loop_maintain.py --fix
```
