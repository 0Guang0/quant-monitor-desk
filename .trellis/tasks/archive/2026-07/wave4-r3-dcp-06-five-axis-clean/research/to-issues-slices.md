# R3-DCP-06 — `/to-issues` 垂直切片

> **SSOT：** 切片 AC 仅本文件 · Plan v4.1  
> **依赖：** R3-DCP-05 CLOSED · ADR-029 · 用户五轴 PASS 硬门禁

---

## 垂直切片规则

1. 每片 tracer-bullet：单轴或单共享基础设施；可独立 pytest 绿。
2. RED → GREEN 证据：`research/execute-evidence/sNN-red.txt` → `sNN-green.txt`
3. 共享 `layer1_axes` 读路径：**S00 独占 merge 后** 各轴片只追加轴绑定。
4. K1 whitelist：S06 主会话 merge。

---

## 依赖图

```text
S00 (clean observation reader + bar→Amihud helper + no-fallback guard)
  → S01 (ENVIRONMENT) ∥ S02 (CREDIT_STRESS) ∥ S03 (RISK_APPETITE) ∥ S04 (LIQUIDITY) ∥ S05 (SENTIMENT)
  → S06 (五轴集成 smoke + K1 + A4 ResourceGuard + ACC-LAYER-E2E-LIVE-001 L1 子集)
```

---

## 切片总表

| Slice                 | What to build                                                           | Acceptance criteria                                               | Blocked by  | 测试 / 证据                                            |
| --------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------- | ----------- | ------------------------------------------------------ |
| **S00-CORE-READER**   | `Layer1CleanObservationReader`（macro + bar）；禁止 EasyXT 式 fallback  | clean 有种子 → 返回 `AxisObservation` 序列；无 silent 换源        | —           | test*layer1CleanReader*\*（Execute 新建）              |
| **S01-ENVIRONMENT**   | ENV-E1-DGS10 从 axis_observation replay e2e                             | 非 fixture 读；特征/解释可断言                                    | S00         | test_layer1_environment_clean_e2e                      |
| **S02-CREDIT-STRESS** | CRD.CS1.BAA10Y clean e2e                                                | 同上                                                              | S00         | test_layer1_credit_stress_clean_e2e                    |
| **S03-RISK-APPETITE** | RA.R1.VIXCLS_30D_IMPLIED_VOL clean e2e                                  | 同上                                                              | S00         | test_layer1_risk_appetite_clean_e2e                    |
| **S04-LIQUIDITY**     | LIQ.B-I1.AMIHUD from security_bar_1d（ADR-029 ponytail）                | bar clean 种子 → Amihud 特征绿；文档 tiingo 天花板                | S00         | test_layer1_liquidity_clean_e2e                        |
| **S05-SENTIMENT**     | SEN-S1-COT_LF_NET from cftc axis_observation                            | COT clean e2e 绿                                                  | S00         | test_layer1_sentiment_clean_e2e                        |
| **S06-INTEGRATION**   | 五轴 panel smoke；K1 对齐；台账 L1 子集关账                             | §3.5.1 全 [x]；ACC-LAYER-E2E-LIVE-001 L1 部分；L3–L5 阶段外置登记 | S01–S05     | test_layer1_five_axis_panel_clean_smoke + 全量 pytest  |
| **S07-REPAIR**        | Audit Repair：A3 trust-boundary · A4/A8 测缺口 · A1 追溯 · A5 loop 隔离 | ledger 23/23 已修复；`uv run pytest -q` 连续 2× exit 0            | S06 + Audit | `research/audit-repair-ledger.md` + panel/reader tests |

---

## P0 锚点（ADR-029）

见 `docs/decisions/ADR-029-dcp06-layer1-five-axis-clean-read.md`。

---

## Wave 4 并行 worktree 建议

| Worktree        | Slices | 拥有文件                                         |
| --------------- | ------ | ------------------------------------------------ |
| wt-dcp06-core   | S00    | `clean_observation_reader.py`（新）, 共享 helper |
| wt-dcp06-env    | S01    | env e2e 测                                       |
| wt-dcp06-credit | S02    | credit e2e 测                                    |
| wt-dcp06-risk   | S03    | risk e2e 测                                      |
| wt-dcp06-liq    | S04    | liquidity e2e 测                                 |
| wt-dcp06-sent   | S05    | sentiment e2e 测                                 |

**合并顺序：** S00 → 五轴并行 → S06（主会话）

---

## Issue 骨架

```markdown
### [S0N] <axis> clean read e2e

**What:** read Tier A clean → feature → interpretation per ADR-029
**AC:** replay seed in tmp*path DB; no staged_fixture_only; pytest green
**Blocked by:** S00
**Verify:** Execute 新建 test_layer1*<axis>\_clean_e2e 模块
```
