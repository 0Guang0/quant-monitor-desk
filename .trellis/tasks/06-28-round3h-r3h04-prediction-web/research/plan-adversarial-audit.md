# Plan Adversarial Audit — R3H-04（Agent-2 · Plan 5d）

> 2026-06-28 · 对抗性审计 + 直接修复 · 方法：frozen/INDEX/AUDIT/plan.freeze + 活卡 + R3H-02 对标 + BRANCH 边界

---

## 摘要

| 严重度 | 发现数 | 已修复 | 遗留 |
| --- | --- | --- | --- |
| **P0** | 2 | 2 | 0 |
| **P1** | 5 | 5 | 0 |
| **P2** | 2 | 2 | 0 |
| **合计** | **9** | **9** | **0** |

`validate-plan-freeze` / `validate-plan-phase 5e`：修订后 **exit 0**（见文末）。

---

## P0 — Execute 阻断 / AC 缺口

### ADV-P0-1 — frozen 缺 §2.8 Plan vs Execute gates（user_gate 悬空）

| 字段 | 内容 |
| --- | --- |
| **ID** | ADV-P0-1 |
| **声称** | `EXECUTION_INDEX.md` §0 `user_gate` 指向 frozen §2.8，但 Agent-1 frozen 卡无 §2.8；Execute 无法从 SSOT 读取主库禁止、mock-first、web_search 默认 stub |
| **证据** | 对标 R3H-02 frozen §2.8；R3H-04 frozen 仅 §8 决策表 |
| **修复** | 活卡 + frozen 新增 **§2.8 Plan vs Execute gates**（6 条 gate）；INDEX §0 更新引用 |

### ADV-P0-2 — §5.1 schema / 禁止字段未内联（Execute 无法无损执行 probability 路径）

| 字段 | 内容 |
| --- | --- |
| **ID** | ADV-P0-2 |
| **声称** | `spec-driven-development-notes.md` 含 `probability_signal_evidence_v1` / `web_evidence_staging_v1` 字段与禁止字段，但 frozen §5 仅高层列表；INDEX §4 声称已并入 §5.1 但章节不存在 |
| **证据** | v4 §0.0 内联规则；R3H-02 frozen §5.1 完整 spec→test 表 |
| **修复** | frozen **§5.1 Contract schema and spec→test map** 内联；§10.1 三源负例表 |

---

## P1 — 高 misread 风险 / 并行与 TDD

### ADV-P1-1 — §9.6 clean-write 负例在 route 注册前（依赖错序）

| 字段 | 内容 |
| --- | --- |
| **ID** | ADV-P1-1 |
| **声称** | `to-issues` S6 仅依赖 S2–S4；route 未 READY 时 clean-write 负例可能漏测 planner 路径 |
| **修复** | §9 依赖改为 **9.6 须 9.5**；S6 依赖 +S5；INDEX §0.1 同步 |

### ADV-P1-2 — R3H-03 CN 源冲突边界不够 executable

| 字段 | 内容 |
| --- | --- |
| **ID** | ADV-P1-2 |
| **声称** | 「禁止碰 CN market 源」未列 source_id 白名单/黑名单；9.5 manifest 无显式 CN 源枚举 |
| **修复** | §2.8 gate #4 枚举 R3H-03 十源 ID；§4.2 声明无 adapter 重叠 |

### ADV-P1-3 — `resource_guard.py` 活卡 §4 与 §7/BRANCH 矛盾

| 字段 | 内容 |
| --- | --- |
| **ID** | ADV-P1-3 |
| **声称** | 活卡 Target 列 `resource_guard.py` 但 §7 禁止修改；Execute 可能误改共享模块 |
| **修复** | 从 Target 移除；§4 加注「只读参照」；§2.8 gate #5 重申 |

### ADV-P1-4 — §10 缺 per-source 负例 / manual-review 最低用例

| 字段 | 内容 |
| --- | --- |
| **ID** | ADV-P1-4 |
| **声称** | 活卡 §5.4 要求每源 clean-write 负例 + route 测；Plan 仅 §9.6 一步笼统描述 |
| **修复** | frozen **§10.1** 三源负例矩阵（kalshi/polymarket/web_search + `-k resolve`） |

### ADV-P1-5 — AUDIT.plan 缺 A5 完成度倒查 + A4 polymarket 非事实 resolution

| 字段 | 内容 |
| --- | --- |
| **ID** | ADV-P1-5 |
| **声称** | A1/A3/A4 未覆盖 `9.5-manifest` 白名单与 `resolution_source` 非事实；A5 未列入 §1（对标 adversarial-authority A5 职责） |
| **修复** | AUDIT §1 增 **A5 必做**；A3/A4 补充 CN 源与 polymarket 检查 |

---

## P2 — 追溯与索引

### ADV-P2-1 — INDEX §4 指向不存在 frozen 子节（§1.1/§4.2/§10.2）

| 字段 | 内容 |
| --- | --- |
| **ID** | ADV-P2-1 |
| **修复** | 内联章节补齐后 INDEX §4 对照表已对齐 |

### ADV-P2-2 — `_tmp-r3h03-r3h04-parallel/BRANCH-R3H-04.md` worktree 缺失

| 字段 | 内容 |
| --- | --- |
| **ID** | ADV-P2-2 |
| **声称** | INDEX §5 / AUDIT Trace 引用 BRANCH 文件，worktree 无此路径 |
| **修复** | 从主库复制 `BRANCH-R3H-04.md` 至 worktree `_tmp-r3h03-r3h04-parallel/` |

---

## 对抗性重点复核（审计清单 C）

| 检查项 | 结果 |
| --- | --- |
| kalshi/polymarket probability 路径 + schema | ✅ §5.1 + §9.1/9.2/9.3 |
| web_search manual-review staging | ✅ §9.4 + §10.1 |
| 三源 no clean write 负例 | ✅ §9.6 + §10.1 |
| 预测不 resolve 事实 | ✅ §5.1 禁止字段 + `-k resolve` |
| 不与 R3H-03 CN 冲突 | ✅ §2.8 #4 + §4.2 + Red Flag |
| §9 单步 TDD | ✅ 每步 `-k` 过滤 + §9 单步边界说明 |
| AUDIT A6 SKIP | ✅ 有理由（on-demand evidence，无 hot path SLA） |

---

## 修订文件（Agent-2）

- `research/plan-adversarial-audit.md`（本文件）
- `docs/.../R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md`（活卡 §1.1/1.2/2.8/4.x/5.1/9/10）
- `frozen/R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md`（`freeze-task-card` 重冻）
- `EXECUTION_INDEX.md` — §0/§0.1/§4
- `AUDIT.plan.md` — §1 A3/A4/A5
- `research/to-issues-slices.md` — S6 依赖
- `_tmp-r3h03-r3h04-parallel/BRANCH-R3H-04.md`（worktree 补齐）

---

## validate-plan-freeze

```bash
cd C:/Users/Guang/Desktop/quant-monitor-desk-wt-r3h04
python .trellis/scripts/task.py freeze-task-card .trellis/tasks/06-28-round3h-r3h04-prediction-web
python .trellis/scripts/task.py generate-manifests .trellis/tasks/06-28-round3h-r3h04-prediction-web
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-28-round3h-r3h04-prediction-web
python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/06-28-round3h-r3h04-prediction-web 5e
# → Plan freeze validation passed (exit 0)
# → Plan phase 5e validation passed (exit 0)
```

---

## Execute 派发建议

**建议派发 Execute：是**

理由：三件套齐全；frozen 已内联 gates/schema/负例；§9 步可单步 TDD；R3H-03 边界 executable；`validate-plan-freeze` exit 0。Grill-me #1（真实搜索 API）不阻塞 mock-first 默认路径，须 Execute 期间用户 gate 若选 live。
