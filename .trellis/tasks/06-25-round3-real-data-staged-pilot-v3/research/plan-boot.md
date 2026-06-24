# Plan Boot — B01-C04 staged pilot v3

## 用户目标摘要

在 PROMPT_14 / v2 staged pilot 证据基础上，按 **B01-WL（`R3D_model_input_whitelist`）** 产出的 `specs/model_inputs/**`，把 baostock、cninfo、akshare 小样本真实数据试跑升级为 **model-driven staged pilot v3**。产出 raw/staging/sandbox 证据与 source readiness 矩阵；**不得** production clean write 或 production-live 声称。

## 原计划已读（ROUND + NNN 任务卡 + GLOBAL）

| 顺序 | 路径 | 要点 |
| ---- | ---- | ---- |
| 1 | `docs/implementation_tasks/README.md` | Round 入口 |
| 2–5 | `GLOBAL_*.md`（4） | 执行/测试/资源/模板 |
| 6 | `ROUND_3_DATA_PRODUCTION_READINESS/README.md` | Batch 01 父包 |
| 7 | `BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_TASK_CARD_MANIFEST.md` | C04 前置 C01 |
| 8 | `BATCH_01_HARDENING_RULES.md` | §1–§10 硬规则 |
| 9 | `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §3.1+§3.6+§2.5–§2.7 | 文件锁与验收 |
| 10 | `R3E_real_data_staged_pilot_v3.md` | 本任务 forward 卡 |
| 11 | `R3D_model_input_whitelist.md` | WL 前置与输出路径 |
| 12 | `R3Y_real_data_staged_pilot_v2.md` + addendum | v2 模式（不得绕过 WL） |
| 13 | `R3X_real_data_staged_pilot.md` | v1 基线 |
| 14 | `018B_production_live_pilot_gate.md` | sandbox 边界 |
| 15 | `docs/quality/prompt14_user_authorization_2026-06-22.md` | 授权语境 |
| 16 | `.trellis/tasks/archive/2026-06/06-24-round3-real-data-staged-pilot-v2/` | v2 证据 SSOT |

## 前置依赖 / Batch 关系

| 前置 | 状态（Plan 时） | 证据 / 处置 |
| ---- | --------------- | ----------- |
| B01-WL `specs/model_inputs/**` | **缺失 — Execute 硬停** | 仅 Plan；Execute 须 WL 合并或只读 rebase |
| v2 staged pilot | merged（master 基线） | `staged_pilot.py` v2 caps/envelopes |
| PROMPT_14 授权 | 有效 | `prompt14_user_authorization_2026-06-22.md` |
| Live 授权（2026-06-24） | 用户已批 | hardening §3 YAML 证据 |
| `R3-B2.75-REQ2-EM` | **DEFERRED** | 不得因 akshare 侧路关闭 |
| Registry 三件套 | 主会话批处理 | 本分支仅 **proposed delta** |

## 预期 AC 草稿（→ MASTER §2）

| AC | 草稿 |
| --- | ---- |
| AC-SP3-01 | WL loader：无白名单/超 cap 拒绝 |
| AC-SP3-02 | baostock 5–20 symbols 扩样 manifest v3 |
| AC-SP3-03 | cninfo metadata-only；拒绝 PDF |
| AC-SP3-04 | akshare validation-only + taxonomy |
| AC-SP3-05 | conflict dry-run summary；无 clean 写 |
| AC-SP3-06 | closeout + readiness matrix + no-mutation |

## Plan Phase 顺序

P0 Boot → 1a → 2a/2b → 3 grill-me → 3.5 vertical-slices → 1b → 4 → 5a/5b → 5c ledger → 5d integration-audit → 冻结

## Phase P0 complete
