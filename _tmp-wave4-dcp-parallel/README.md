# Wave 4 DCP-07..10 并行协调目录

> **主会话 SSOT** · 2026-07-02  
> **四轨并行：** 0708（DCP-07 ∥ DCP-08）· 0910（DCP-09 ∥ DCP-10）  
> **模型：** `composer-2.5`（**禁止** `composer-2.5-fast`）

## 分支 / worktree

| 轨     | 规划 ID   | 分支                                  | Worktree                         |
| ------ | --------- | ------------------------------------- | -------------------------------- |
| 0708-A | R3-DCP-07 | `feature/wave4-r3-dcp-07-layer2`      | `../quant-monitor-desk-wt-dcp07` |
| 0708-B | R3-DCP-08 | `feature/wave4-r3-dcp-08-layer4`      | `../quant-monitor-desk-wt-dcp08` |
| 0910-A | R3-DCP-09 | `feature/wave4-r3-dcp-09-backfill-ci` | `../quant-monitor-desk-wt-dcp09` |
| 0910-B | R3-DCP-10 | `feature/wave4-r3-dcp-10-evidence`    | `../quant-monitor-desk-wt-dcp10` |

## 每轨流水线（不得跳步）

```text
Plan → Plan 对抗审计 → Plan Repair → Execute → Execute Audit (A1–A8 各一 agent) → Repair → 主会话 merge
```

**工程契约不合格 = 阶段未完成**（ponytail · TDD · 五字段 · GitNexus impact · 参考项目 L 梯分离 · validate-\* gate）。

## Agent 派发

| 阶段       | 提示词                                                        |
| ---------- | ------------------------------------------------------------- |
| 公共       | `agent-prompts/_COMMON.md`                                    |
| Plan       | `agent-prompts/PLAN-DCP-0X.md`                                |
| Plan Audit | `agent-prompts/PLAN-AUDIT-DCP-0X.md`（Plan 完成后主会话生成） |
| Execute    | `agent-prompts/EXECUTE-DCP-0X.md`（Plan freeze 后生成）       |

## 主会话职责

- registry 三件套 **排队 merge**
- 每轨阶段 gate：`validate-plan-freeze` / `validate-execute-handoff`
- 四轨全 CLOSED 后更新 `R3_DCP_TO_ISSUES_INDEX.md` · `待修复清单.md`

**四轨 merge 已完成**（2026-07-02）— master @ `2c5647b5` · 下一入口 **Wave 5 `R3H-05-GATE`**

| 轨     | Plan | Plan Audit | Plan Repair | Execute | Audit | Repair | Merge         |
| ------ | ---- | ---------- | ----------- | ------- | ----- | ------ | ------------- |
| DCP-07 | ✅   | —          | —           | ✅      | ✅    | ✅     | ✅ `3dbf30ea` |
| DCP-08 | ✅   | —          | —           | ✅      | ✅    | ✅     | ✅ `d93483f2` |
| DCP-09 | ✅   | —          | —           | ✅      | ✅    | ✅     | ✅ `5ec88389` |
| DCP-10 | ✅   | —          | —           | ✅      | ✅    | ✅     | ✅ `2c5647b5` |
