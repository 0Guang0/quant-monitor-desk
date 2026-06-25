# PRD — B3F-BR Backfill/Reconcile Parity

## 背景

Batch 3F.4 要求在生产入库前证明坏数据/冲突/回填不会绕过验证。Roadmap `R3F-BR-01..05` 将散落 partial 项收口到 orchestrator parity + registry 链。

## 用户故事

作为数据治理工程师，我需要 backfill/reconcile 行为与 incremental 一样经过 validate+write 或 honest reconcile 路径，并且 orchestrator job 矩阵可机器读取，以便 Batch6 关账。

## 验收标准

1. Backfill 不得再声称跳过 validator（AC-BR-01）
2. Reconcile re-fetch/compare 三条路径有 pytest 锚点（AC-BR-02）
3. `R3-PARTIAL-5` 仅 regression guard，不重开实现（AC-BR-03）
4. Handler registry 覆盖 contract 矩阵（AC-BR-04）
5. ADR-023 与 `R3-PARTIAL-4` registry 链一致（AC-BR-05）
6. Playbook §8.5 命令绿（AC-BR-PLAYBOOK）

## 非目标

- crash-window 新实现
- production clean write
- Layer5 review UI
