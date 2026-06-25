# Batch 3F Playbook 对抗性审计报告

> **审计对象：** `BATCH_3F_COORDINATOR_PLAYBOOK.md`（初稿 51 行）  
> **对照：** `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` · `BATCH_3V_COORDINATOR_PLAYBOOK.md`  
> **审计模型：** `composer-2.5`  
> **Verdict：** `PASS_FOR_DISPATCH`（2026-06-25 rev.1 — 修补已写入 playbook）

---

## 1. 发现与处置（rev.1）

| ID         | Sev          | 发现                                                                | 处置（playbook 章节）                      |
| ---------- | ------------ | ------------------------------------------------------------------- | ------------------------------------------ |
| B3F-PB-001 | BLOCKING     | 缺 §0 范围边界、八分支轨道声明                                      | §0                                         |
| B3F-PB-002 | BLOCKING     | 缺六复杂 + 两精简的 §3.0 派发表（worktree / Trellis / 轨道）        | §3.0                                       |
| B3F-PB-003 | BLOCKING     | 缺 §2.5 核心文件锁（migration、sync、layer3、registry）             | §2.5                                       |
| B3F-PB-004 | BLOCKING     | 缺 §2.6 allowed/forbidden；执行者易越界改 Round4/3G                 | §2.6                                       |
| B3F-PB-005 | BLOCKING     | 缺 complex / debt-lite 双轨道流水线（§4 / §5）                      | §4、§5                                     |
| B3F-PB-006 | BLOCKING     | 缺 §7 合并顺序与 integration 策略                                   | §7                                         |
| B3F-PB-007 | BLOCKING     | 缺 §8 每分支 PASS 命令与负向边界                                    | §8.1–§8.8                                  |
| B3F-PB-008 | BLOCKING     | 3D.3 标 DONE 与 registry OPEN 张力（lineage/L3）                    | §0、§1.1 B3F-LIN、§12                      |
| B3F-PB-009 | BLOCKING     | `R3F-MIG-04` 与 `R3F-HYG-04` 同指 `D2-P3-1` 双 owner 风险           | §2.5、§2.6 B3F-MIG owns migration 列       |
| B3F-PB-010 | HIGH         | `B2.5-O-05` live FRED 与 `R3F-CLI-05` staging E2E 易混为同一授权    | §2.5、§2.6 B3F-SH vs B3F-CLI               |
| B3F-PB-011 | HIGH         | `source_health_snapshot` 表：B3F-SH 与 B3F-MIG migration 须串行锁   | §2.5、§7.2                                 |
| B3F-PB-012 | HIGH         | `R3-PARTIAL-5` / `R2-RISK-3` / `R3-AUDIT-DEF-03` 易被重开实现       | §2.1、§5.1 B3F-REG、manifest §3            |
| B3F-PB-013 | HIGH         | ingestion R2b–R2d 与 live-source 分支禁止同 sprint                  | §2.5 B3F-HYG、hardening §7                 |
| B3F-PB-014 | MEDIUM       | 缺 Plan 质检 §3.8–§3.10、§3.9 追溯规则                              | §3.8–§3.10                                 |
| B3F-PB-015 | MEDIUM       | 缺 §6 Done 九项、§9 开波清单、worktree 模板                         | §6、§9                                     |
| B3F-PB-016 | MEDIUM       | 缺 `composer-2.5-fast` 禁止、GitNexus/codebase-memory 同级核实      | §2.3、§2.4                                 |
| B3F-PB-017 | MEDIUM       | 缺合并后 registry §7.3 与 `ROUND3_HANDOFF` 更新步骤                 | §7.3                                       |
| B3F-PB-018 | NON-BLOCKING | 缺 `BATCH_3F_SELF_CHECK.md`（可后续补；开波前以 §9 checklist 代替） | §9、残余风险 §3                            |
| B3F-PB-019 | NON-BLOCKING | 任务卡未齐（仅 manifest + R3F_verified_audit_ops_perf_hygiene）     | manifest §1；复杂线 Plan 须引用 roadmap 行 |

---

## 2. 垂直切片 / 范围风险（对抗性）

| ID            | 风险                                          | 缓解                                                     |
| ------------- | --------------------------------------------- | -------------------------------------------------------- |
| B3F-AUD-VS-01 | B3F-REG 水平改 registry 三件套                | 主会话批处理；REG 仅 proposed delta + reconcile 测试     |
| B3F-AUD-VS-02 | B3F-MIG 重复实现 migration 009 已关 CHECK     | `R3F-MIG-01` verify-only；§8.1 负向边界                  |
| B3F-AUD-VS-03 | B3F-SH 用 DH2 路径建 `source_health_snapshot` | hardening §2；§2.6 SH owns 表；DH2 只读                  |
| B3F-AUD-VS-04 | B3F-LIN 误关 ADV-R3X 而 staged envelope 未变  | 强制 snapshot lineage pytest + registry row              |
| B3F-AUD-VS-05 | B3F-BR 重开 `R3-PARTIAL-5` crash-window 实现  | `R3F-BR-03` regression guard only                        |
| B3F-AUD-VS-06 | B3F-CI 改 runtime 业务逻辑                    | debt-lite allowed：tests/docs/verification_commands only |
| B3F-AUD-VS-07 | Eastmoney/AkShare 被 sidecar 误关闭           | `R3F-SH-07` registry no-false-close test；hardening §4   |

---

## 3. 残余风险（dispatch 后仍须主会话盯）

1. **八路并行** — registry 三件套仅主会话 + B3F-REG 收口；实现分支禁止直接 RESOLVED 闭合。
2. **`D2-P3-1` 列归属** — migration 列由 B3F-MIG 独占；B3F-HYG 若触达 sync 逻辑不得重复加列。
3. **Live FRED** — `R3F-SH-06` 须用户授权 YAML；sandbox Batch 01 证据不得当作 live primary 关闭。
4. **任务卡缺口** — 复杂线 Plan 冻结前须把 roadmap `R3F-*` 行写入 `MASTER` AC；不得因缺独立 `.md` 卡而缩小范围。
5. **`BATCH_3F_SELF_CHECK.md`** — 建议下一 PR 补齐；当前以 playbook §9 + hardening 为开波门禁。

---

_审计日期：2026-06-25 · rev.1 dispatch-ready_
