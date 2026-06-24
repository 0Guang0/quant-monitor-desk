# Grill-me Session — B01-C04 staged pilot v3

## CLAIM → DOUBT → RECONCILE

| # | CLAIM | DOUBT | RECONCILE（Plan 冻结） |
| --- | ----- | ----- | ---------------------- |
| 1 | v3 可在 WL 未合并时先写 pilot 逻辑 | 任务卡 §3 硬停；会发明 symbol scope | Execute Boot 检查 `specs/model_inputs/**`；缺失即 STOP |
| 2 | 复用 v2 envelope 扩 symbol 即可 | 违反 model-driven；对抗审计 B01-AUD | SP3-01 必须 WL loader；v2 envelope 仅回归对照 |
| 3 | agent 可直接改 registry 闭合 AKSHARE | playbook §2.1 主会话批处理 | 分支产出 `registry_proposed_delta_v3.yaml` + evidence |
| 4 | akshare 成功可关 EM 债 | `R3-B2.75-REQ2-EM` 不可侧路关闭 | closeout 显式 re-defer + taxonomy |
| 5 | live 已授权可全市场拉取 | hardening §6 + 任务卡 §7 | caps：50 calls / 2k rows；ResourceGuard 停损 |
| 6 | cninfo 可顺带下 PDF | 任务卡 §7/§8 禁止 | SP3-03 RED 测 PDF 路径拒绝 |

**结论：** Plan 可冻结；Execute 依赖 WL 合并；无 WL 不得 start。
