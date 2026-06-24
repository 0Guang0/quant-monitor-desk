# Batch 01 Playbook 对抗性审计报告

> **审计对象：** `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`  
> **审计模型：** `composer-2.5`（主会话派发对抗性检查）  
> **主会话处置：** 全部 BLOCKING + NON-BLOCKING 项已写入 playbook 修复（见 playbook §11）  
> **Verdict：** `PASS_AFTER_PLAYBOOK_HARDENING`

---

## 1. 审计方法

对照 Wave C 协调手册、Batch 01 manifest/hardening/audit、五张 forward 任务卡 §3/§11、`023` 任务卡、路线图 Batch 3D.1/3D.3，检查：索引完整性、allowed/forbidden SSOT、合并/registry 门、指令清晰度、ID 映射、worktree 命令。

---

## 2. 发现与处置摘要

| ID             | Sev          | 发现                              | 处置                                               |
| -------------- | ------------ | --------------------------------- | -------------------------------------------------- |
| B01-PB-001     | BLOCKING     | closure report 指向错误 README §5 | playbook §6 修正路径并内联九项                     |
| B01-PB-002     | BLOCKING     | 023 与 Batch 01 merge 包混淆      | playbook §0 范围边界 + §7 双轨合并                 |
| B01-PB-003     | BLOCKING     | LIN 未入 manifest                 | manifest §1.1 增 B01-LIN                           |
| B01-PB-004     | BLOCKING     | Playbook ID 与 manifest ID 无映射 | playbook §3.0 映射表                               |
| B01-PB-005     | BLOCKING     | 缺 per-branch allowed/forbidden   | playbook §2.6                                      |
| B01-PB-006     | BLOCKING     | §8 缺任务卡 §11 命令              | playbook §8.x 增验收命令块                         |
| B01-PB-007     | BLOCKING     | 缺 `/to-issues` 强制              | playbook §2.7                                      |
| B01-PB-008     | BLOCKING     | registry 锁不完整（TDX/SP3）      | playbook §2.5 扩表                                 |
| B01-PB-009     | BLOCKING     | registry 批处理清单不全           | playbook §7 扩 manifest §5 全表                    |
| B01-PB-010     | BLOCKING     | 缺 integration 预合并             | playbook §7.1                                      |
| B01-PB-011     | BLOCKING     | 023 worktree 名与 MAP 不一致      | playbook §3.0 对齐 MAP                             |
| B01-PB-012     | BLOCKING     | 缺 git worktree 模板              | playbook §9.1                                      |
| B01-PB-013–048 | NON-BLOCKING | 索引/质检/金样/追溯等             | 已并入 playbook §2.4、§3.1、§3.9–§3.10、§5、§8、§9 |

**主会话核实：** 2026-06-24 已全部写入 `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` rev.2 与 `BATCH_01_TASK_CARD_MANIFEST.md` §1.1/§4。

---

## 3. 残余风险（执行期监控）

1. **FRED 任务卡 §11 含 `test_ops_data_health.py`** — 与「FRED 不改 data_health 主体」并存；playbook §8.5 限定为**只跑既有测试绿、不得改 `data_health.py`**。
2. **七路 Execute 并行** — registry 行仍须主会话排队；不可假定零冲突。
3. **023 Wave D** — 与 Batch 01 可并行开发，但 merge 轨道分离；不得在同一 PR 混 claim production readiness。

---

_审计日期：2026-06-24 · 主会话修复闭环_
