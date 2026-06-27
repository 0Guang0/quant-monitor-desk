# Project Overview — R3G-03（Plan 1a · ≤1 页）

## 仓库语境

quant-monitor-desk（QMD）Round 3G 第三批：**有限批准的生产 clean-write**。前两步 R3G-01（sandbox 排练）、R3G-02（对抗审计）已交付 `backend/app/ops/sandbox_clean_write/` 包。

## 相关模块

| 模块              | 路径                                     | R3G-03 角色                                     |
| ----------------- | ---------------------------------------- | ----------------------------------------------- |
| Sandbox rehearsal | `rehearsal_runner.py`                    | 编排样板（改 sandbox→production + approval 门） |
| Adversarial audit | `adversarial_audit.py`                   | 消费 `audit_decision.json`                      |
| Mutation proof    | `mutation_proof.py`                      | before/after row count + hash                   |
| Write path        | `write_manager.py`, `validation_gate.py` | 唯一生产写入口                                  |
| Data health       | `data_health_profiles/*`                 | per-domain 写前校验                             |
| CLI               | `data_commands.py`                       | 挂载 `promote` 子命令                           |
| 契约              | `sandbox_clean_write_contract.yaml`      | `r3g03_limited_entry` block_if                  |

## 数据流（目标）

```text
approval.yaml + audit_decision.json
    → validate_approval_contract()
    → build_before_proof(production_db)
    → build_rollback_plan(dry_run)
    → LimitedProductionEntry.run(dry_run|live)
    → build_after_proof()
    → write promote_report.json
```

## 候选与 caps

仅 `baostock` / `cninfo`(metadata) / 用户授权 `fred`；r3g03 caps：≤10 symbols/series，30–120 天窗口（契约 `candidate_caps`）。

## 关键约束

- `production_mutation_allowed=true` **仅** promote 路径且全部门禁通过
- R3G-01/02 CLI 仍拒绝生产写
- 无 Agent 路径可替代 approval artifact
