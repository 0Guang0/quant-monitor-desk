# R2 Tier A Live Acceptance Evidence

> **日期：** 2026-07-03（**rev 4 关账切片 2/2** @ 22:40 UTC+8）  
> **分支：** `feature/m-data-03-tier-a-live`  
> **契约：** `specs/contracts/live_tier_a_evidence_v1.yaml` · ADR-034  
> **核心目标核实：** `M-DATA-03-HANDOFF.md` §2.1 · §5 grill AC

---

## 两层结论

| 层级                   | 含义                                              | 当前状态                                                        |
| ---------------------- | ------------------------------------------------- | --------------------------------------------------------------- |
| **Plan R2 机闸**       | 流水线、契约、pytest、单次/双次 `--report` exit 0 | **[x] 已满足**                                                  |
| **grill 成品核实关账** | 能不能用、入库是否成品形态、可否支撑下轮开主库    | **6/7 AC 可勾选** · AC-4 待 GitHub `workflow_dispatch` 实跑 URL |

**对外表述：** 11 源在**隔离沙箱**内真网验收 **11/11 PASS**（见下关账 run）；**不等于**生产主库就绪（见 ADR-034 §Sandbox boundary · MCR R4）。

---

## grill AC 勾选（§5）

| AC                                 | 状态                 | 证据                                                                                                                |
| ---------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **AC-1** bis/cninfo/sec 调查+修    | **[x]**              | `tier-a-empty-response-investigation.md` · 关账 run 三源均有 clean 行                                               |
| **AC-2** 0 行不得 PASS             | **[x]**              | `classify_source_report_failure` + `test_cleanRowCount_axisObservation_*`                                           |
| **AC-3** 同 sandbox 双跑 exit 0    | **[x]**              | `r2-live-20260703220000` run1+run2 均 exit 0 · 11/11                                                                |
| **AC-4** CI workflow_dispatch 实跑 | **⏸ 合并 master 后** | workflow 文件 + `test_tier_a_live_ci_manifest.py` 绿；**缺** GitHub Actions run URL（用户决定 merge 后再 dispatch） |
| **AC-5** 行情 F0 无 staged-only    | **[x]**              | 关账 run：av/baostock/mootdx 均为 `f0=PASS` · `live_acceptance=True` 跳过 R3G gate                                  |
| **AC-6** 沙箱≠生产文档             | **[x]**              | ADR-034 §Sandbox boundary · MCR 表注（本 rev）                                                                      |
| **AC-7** Tier B/C 三轨             | **[x]**              | 契约+acceptance+CI · sandbox 报告见下                                                                               |

---

## 关账 live run（grill 口径 · SSOT）

| Run              | Sandbox                                                         | Exit  | Summary                                                                                                                                            |
| ---------------- | --------------------------------------------------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **run1**         | `.audit-sandbox/m-data-03/r2-live-20260703220000`               | **0** | 11/11 PASS                                                                                                                                         |
| **run2**（幂等） | 同上 · `tier-a-report-run2.json`                                | **0** | 11/11 PASS                                                                                                                                         |
| **G-07 加厚**    | `.audit-sandbox/m-data-03/r2-thicken-wb-deribit-20260703224024` | **0** | world_bank **axis_observation=2** · deribit **crypto_derivative_clean=2**（分报告 `tier-a-report-world_bank.json` / `tier-a-report-deribit.json`） |

**幂等对比（run1 vs run2 · `r2-live-20260703220000`）：**

| source_id     | run1 class | run2 class | 行数/细节                                                                    |
| ------------- | ---------- | ---------- | ---------------------------------------------------------------------------- |
| alpha_vantage | PASS       | PASS       | security_bar_1d=3 · 一致                                                     |
| baostock      | PASS       | PASS       | security_bar_1d=2 · 一致（`_clamp_bar_incremental_window` 已合入）           |
| bis           | PASS       | PASS       | axis_observation 1→2 · **合法增量**（ADR-034 月频窗追加，非 duplicate 炸库） |
| cftc_cot      | PASS       | PASS       | axis_observation=3 · 一致                                                    |
| cninfo        | PASS       | PASS       | cn_announcement_clean=1 · 一致                                               |
| deribit       | PASS       | PASS       | crypto_derivative_clean=1 · 一致（加厚 run 另证 =2）                         |
| fred          | PASS       | PASS       | axis_observation=3 · 一致                                                    |
| mootdx        | PASS       | PASS       | security_bar_1d=2 · 一致                                                     |
| sec_edgar     | PASS       | PASS       | us_disclosure_clean=2 · 一致                                                 |
| us_treasury   | PASS       | PASS       | axis_observation=3 · 一致                                                    |
| world_bank    | PASS       | PASS       | axis_observation=1 · 一致（加厚 run 另证 =2）                                |

**根因修复（本 rev）：** `baostock` 二次跑 `_clamp_bar_incremental_window` — 跨源共享 `sh.600519` watermark 导致窗超 120 天 cap → 原 `FAILED_FINAL`。

---

## Tier B / Tier C（AC-7）

| 轨     | Sandbox                                    | Exit  | Notes                                                                                                      |
| ------ | ------------------------------------------ | ----- | ---------------------------------------------------------------------------------------------------------- |
| Tier B | `.audit-sandbox/m-data-03/tier-b-closeout` | **0** | 6 PASS · **stooq 路径二已接受**（ADR-034）· **CN 三源条件路径二**（见 `tier-b-network-path2-evidence.md`） |
| Tier C | `.audit-sandbox/m-data-03/tier-c-closeout` | **0** | 3 源真 HTTP · kalshi/polymarket live slug 修复后 PASS                                                      |

Workflow：`.github/workflows/tier-b-live.yml` · `.github/workflows/tier-c-live.yml`

---

## 机闸清单（Plan R2 Execute）

- [x] `live_tier_a_evidence_v1` 11/11 manifest
- [x] acceptance report JSON 11 rows + contract 顶层字段
- [x] E2 inspect 非 FAIL
- [x] B2 `b2_validation_status` 接线
- [x] `failure_artifact` 写出路径
- [x] CI workflow 文件（tier-a/b/c）
- [x] `python -m pytest -q` exit 0（2026-07-03 关账复验）
- [x] staging adapter raw 落盘 → F0 可发现
- [x] 真网双次 `--report` exit 0（关账 sandbox）
- [x] 三源 EMPTY_RESPONSE 根因修复 + 守卫
- [x] F0 方向 B（live 路径无 staged-only）
- [ ] GitHub `workflow_dispatch` 实跑日志（AC-4 · 需 repo secrets + 人工触发）

---

## 命令

```bash
uv run pytest -q
QMD_ALLOW_LIVE_FETCH=1 DATA_ROOT=.audit-sandbox/m-data-03/<run> \
  uv run python scripts/tier_a_live_acceptance.py --report <path>/tier-a-report.json --data-root <path>
# 幂等：同 DATA_ROOT 再跑 --report tier-a-report-run2.json
```

---

## 技术修复记录

| 项                   | 证据                                                                           |
| -------------------- | ------------------------------------------------------------------------------ |
| bis 月频窗           | `bis_incremental_run.py` YYYY-MM 比较                                          |
| cninfo/sec 冷启动    | `cold_start_fallback`（watermark=None）                                        |
| EMPTY 守卫           | `clean_row_count<1` → `FAIL_FIXABLE`                                           |
| F0 方向 B            | `data_health_profiles` `live_acceptance=True`                                  |
| axis 计数            | `_clean_row_count` 按 `source_used`，不回退全表                                |
| baostock 幂等窗      | `_clamp_bar_incremental_window` + 测                                           |
| G-07 world_bank 加厚 | `DEFAULT_COUNTRIES=("US","CN")` · 加厚 run axis_observation=2                  |
| G-07 deribit 加厚    | `_resolve_deribit_live_instruments` 经 `_live_instruments` 取 2 合约 · clean=2 |

---

## 沙箱边界（AC-6 摘要）

- **R4 诚实口径** = 隔离 `DATA_ROOT` 下真网 rehearsal，**非** canonical 主库写权限。
- 过关 ≠ 可开生产主库；主库仍须 R3G promote + Batch05 posture。
- 详见 `docs/decisions/ADR-034-m-data-03-tier-a-live-acceptance.md` §Sandbox boundary。

---

## CI

- Workflow: `.github/workflows/tier-a-live.yml`
- Schedule: `0 7 * * *` → `--quick`
- `workflow_dispatch` → 全量 11/11 — **待实跑 URL（AC-4）**
