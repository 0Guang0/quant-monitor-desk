# Plan 对抗性审计 — R3-DCP-03（修订）

> **审计日期：** 2026-06-30  
> **范围：** 活卡 · `DEBT.plan.md` · `reference-adoption-dcp03.md` · `plan-boot.md` · `architecture-dcp03.md` · 原 `plan-adversarial-audit.md`  
> **规则：** **L1/L2/L3 仅用于外部 `参考项目/**`\*\*；仓内代码不得标三等级（用户裁决）

---

## 总裁决

| 轮次                                | 结论                                    |
| ----------------------------------- | --------------------------------------- |
| 初稿（混用仓内 L1）                 | **FAIL**                                |
| 修订后（本文 Fix 已写入 Plan 文件） | **PASS（Plan 闸门）** — 0 BLOCKING 遗留 |

---

## Findings → Fix → 状态

| ID     | 严重度       | Finding                                                                                                                                                                   | Fix                                                                                            | 状态                                     |
| ------ | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------------------------- |
| **F1** | **BLOCKING** | `reference-adoption-dcp03.md` 将 `DbInspector`、`test_*` 等仓内代码标为 L1/L2，**与用户三等级定义冲突**                                                                   | 拆为 §1 仓内复用 + §2 仅参考项目三等级 + §3 本轨绿场                                           | **已修复**                               |
| **F2** | **BLOCKING** | S02 写「从 incremental raw 取 evidence」但未说明 **bundle 格式**；`run_data_health_profile` 需 `raw_evidence_manifest.json`，与 sync raw 布局不一致 → Execute 必 RED 卡死 | `reference-adoption-dcp03.md` §4B + `DEBT.plan` S02 绑定 **fetch_log → 测试 helper 组 bundle** | **已修复**                               |
| **F3** | **BLOCKING** | `DEBT.plan` 写「无 `参考项目/**` 实读门禁」，与 DCP-01 惯例及用户「L2 须复制自外部」相悖                                                                                  | 新增 Execute 必读 `execute-reference-read-evidence.md`；实读 EasyXT 完整性 + JQ2PTrade CLI 段  | **已修复**（模板已建；Execute 填实读行） |
| F4     | medium       | `plan-boot.md` §3 表头「已有（L1）」「缺口（L2）」仍用三等级词                                                                                                            | 改为「仓内已有」「本轨缺口」                                                                   | **已修复**                               |
| F5     | medium       | `DEBT.plan` allowed 未含 `tests/fixtures/data_health/good_bundle`（只读）及可选 `post_write_inspect_support.py`                                                           | allowed 已补                                                                                   | **已修复**                               |
| F6     | medium       | 活卡 AC「L1/L2/L3 表齐」表述易误解                                                                                                                                        | 改为「参考项目三等级表齐 + 仓内复用表齐」                                                      | **已修复**                               |
| F7     | medium       | 初稿 `plan-adversarial-audit.md` 自批 PASS 时 F1/F2/F3 未解决                                                                                                             | 本文件取代；旧稿结论作废                                                                       | **已修复**                               |
| F8     | low          | `architecture-dcp03.md` 步骤 5 暗示 raw 目录即 evidence                                                                                                                   | 改为 fetch_log + helper 组 bundle                                                              | **已修复**                               |
| F9     | low          | 缺 `check.jsonl` / `implement.jsonl` 路由                                                                                                                                 | Execute 开工前由主会话填入 Plan/活卡必读行                                                     | **待 Execute 前**                        |
| F10    | low          | AC 与 DCP-01 `repeatRun_noRowGrowth` 重叠风险                                                                                                                             | S01 明确要求断言 **`DbInspector` 报告**字段，非仅 SQL COUNT                                    | **已写入 DEBT S01**                      |

---

## 修订后核对清单

| 检查                               | 结果              |
| ---------------------------------- | ----------------- |
| 三等级表**仅**含 `参考项目/**` 行  | ✅                |
| 仓内资产单独成表、无 L1/L2/L3 标签 | ✅                |
| S02 evidence bundle 路径可执行     | ✅（helper 策略） |
| forbidden 含 sync/port/migration   | ✅                |
| 参考项目禁止 runtime / 禁止项登记  | ✅                |
| 活卡 AC 可映射 S01–S03             | ✅                |

---

## Execute 放行条件

1. 填完 `research/execute-reference-read-evidence.md`（参考项目实读或 `MISSING_REFERENCE_TREE` + R3D 引用）
2. `task.json` → `in_progress`
3. S01 RED 不得偷用纯 `good_bundle` 代替 incremental 会话（夹具仅格式 SSOT）
