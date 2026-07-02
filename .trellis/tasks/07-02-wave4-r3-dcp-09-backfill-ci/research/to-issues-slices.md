# R3-DCP-09 — `/to-issues` 垂直切片

> **SSOT：** 切片 AC 仅本文件 · Plan v4.1  
> **依赖：** R3-DCP-05 ✅ · Wave 3 验收脚本 @ `93b2c82`

---

## 垂直切片规则

1. 每片 tracer-bullet：单一可测交付；独立 pytest 或脚本 exit 0。
2. RED → GREEN：`research/execute-evidence/sNN-red.txt` → `sNN-green.txt`
3. 金路径：CLI → orchestrator → `BackfillShardRunner`；禁止 adapter bypass。
4. CI 默认 PR 仍不跑 network；nightly 才 `--run-network`。

---

## 依赖图

```text
S00 (cap contract + plan_backfill_shards max_shards)
  → S01 (qmd data backfill CLI)
  → S02 (replay backfill e2e)
  → S03 (isolated acceptance --quick) ∥ S04 (nightly workflow)
  → S05 (live acceptance findings gate)
  → S06 (registry 关账 + loop_maintain)
```

---

## 切片总表

| Slice              | What to build                                                                                         | Acceptance criteria                                                                 | Blocked by | 测试 / 证据                                                                 |
| ------------------ | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------- |
| **S00-CAP-CONTRACT** | `bounded_backfill_cap.yaml`；`plan_backfill_shards(..., max_shards=)`；ADR-030                      | 超 cap 日期窗 fail-closed 或 `--truncate-to-cap` 显式截断；默认 shard≤3             | —          | `test_plan_backfill_shards_respects_max_shards` · ADR-030                     |
| **S01-CLI-BACKFILL** | `qmd data backfill --domain --start --end [--max-shards] [--dry-run]` → `run_backfill` + service   | dry-run JSON 可审计；非 dry-run 须 sandbox/live gate；首域 `cn_equity_daily_bar`      | S00        | test_qmd_data_backfill_cli（Execute 新建）                                    |
| **S02-BACKFILL-E2E** | replay e2e：mock/replay fetch → clean upsert；隔离库                                                  | 2+ shards 跑通；`SHARD_COMPLETE` 事件；重复跑幂等                                    | S01        | test_bounded_backfill_cli_e2e（Execute 新建）                                 |
| **S03-ACC-QUICK**  | `wave3_isolated_production_acceptance.py --quick` 跳过 `pytest_full`                                 | quick profile <5min；nightly 无 `--quick` 仍跑全量；`WAVE3-ACC-OPT-01` 关账          | —          | test_wave3_isolated_acceptance_quick_profile（Execute 新建）                  |
| **S04-CI-NIGHTLY** | `.github/workflows/nightly.yml` + `docs/ops/nightly_ci.md`                                           | `pytest -q --run-network -m network tests/test_batch275_live_pilot_gate.py::test_livePilot_phase3RawOnly_threeRequestsLive` 绿；`workflow_dispatch` 可手动触发；`ACC-LIVE-NETWORK-CI-001` · `LIVE-NETWORK-GATE-001` 关账 | S03        | test_nightly_ci_manifest（Execute 新建）                                      |
| **S05-LIVE-GATE**  | `wave3_live_production_acceptance.py --fail-on-severity HIGH,CRITICAL`                               | findings 硬门禁；`EXPECTED_DEFER` 不 fail；`ACC-LIVE-ACCEPT-NIGHTLY-001` 关账        | S04        | test_wave3_live_acceptance_findings_gate（Execute 新建）                     |
| **S06-REGISTRY**    | `待修复清单.md` 关账行 · roadmap 勾选 · `loop_maintain.py`                                            | `WAVE3-ACC-OPT-01` · `ACC-LIVE-NETWORK-CI-001` · `ACC-LIVE-ACCEPT-NIGHTLY-001` · `LIVE-NETWORK-GATE-001` 四 ID 标记承接完成；docs index 更新 | S02,S05    | loop_maintain · registry 测试                                               |

---

## Cap 参数（Execute SSOT 摘要）

| 参数                               | 默认值 | 说明                                      |
| ---------------------------------- | ------ | ----------------------------------------- |
| `ECO_MAX_BACKFILL_DAYS_PER_TASK`   | **31** | 已有；每 shard 最大日历天数               |
| `DEFAULT_MAX_BACKFILL_SHARDS`      | **3**  | 单次 CLI 默认最多执行 shard 数            |
| `ABSOLUTE_MAX_BACKFILL_SHARDS`     | **12** | operator `--max-shards` 硬顶              |
| `--truncate-to-cap`                | off    | 显式开启时截断日期窗至 cap（ponytail 明示） |

---

## Issue 骨架

```markdown
### [S0N] <topic>

**What:** …
**AC:** …
**Blocked by:** S00
**Verify:** pytest / script exit 0
```
