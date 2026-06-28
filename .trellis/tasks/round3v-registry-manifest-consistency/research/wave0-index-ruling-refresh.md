# Research: WAVE0 INDEX 2026-06-28 裁决刷新

- **Query**: 对照 `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §0.2 / §1 刷新 B3V-REG debt-lite Plan 切片粒度
- **Scope**: internal（主仓库 INDEX vs worktree DEBT.plan / research）
- **Date**: 2026-06-28

## Findings

### 裁决摘要（§0.2）

| 卡 | 裁决 | GitHub issue 数 |
| -- | ---- | --------------- |
| **B3V-C05 REG** | 整卡 **1 个 issue**；REG + DOC 竖条内用 checklist，**不再拆 DOC-01/02/03 三票** | **1** |

### DEBT.plan 刷新对照

| 旧 Plan（2026-06-25） | 新 SSOT（2026-06-28） | 处置 |
| --------------------- | --------------------- | ---- |
| REG-01 / REG-02 | REG-**BOOT** / REG-01 / REG-02 | 新增 BOOT 基线切片；01/02 语义不变 |
| DOC-01 / DOC-02 / DOC-03 三行 | **DOC-ALL** 单行 + 票内 checklist | 合并为单竖条；证据文件保留原名 |
| 无 GitHub issue 表 | **REG-ISSUE-1** 整卡 1 票 | 写入 DEBT.plan + `research/vertical-slices.md` |
| Blocker: `check_docs_specs_indexed` exit 1 | worktree 实测 **exit 0**（2026-06-28） | 移除 Plan 阻塞；保留 merge gate 命令 |

### 证据路径映射（Execute 已完成 → 新切片）

| 新切片 | 已有证据 |
| ------ | -------- |
| REG-BOOT | `research/migration-009-coverage-matrix.md` |
| REG-01 | `execute-evidence/REG-01-matrix.txt` |
| REG-02 | `execute-evidence/REG-02-proposed-registry-delta.md`、`repair-evidence/registry-ready-for-coordinator.md` |
| DOC-ALL | `execute-evidence/DOC-01-restore.txt`、`DOC-02-doc-sync.txt`、`DOC-03-red.txt`、`DOC-03-green.txt` |

### Playbook §2.6 allowed/forbidden（抄录）

| Owns（可写） | Must not own |
| ------------ | ------------ |
| migration 009 覆盖矩阵、manifest/doc/registry 对齐 | 无证明重写 migration 009；伪造 `FINAL_AUDIT_REPORT` |

完整边界见 DEBT.plan Boundary 表（任务卡 §4 + manifest §3 C05）。

### Related Specs

- `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.6、§5.1、§2.5/§2.6
- `complex-task-planning-protocol.md` Phase 8D §8D.3
- `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §1（C05）

## Caveats / Not Found

- worktree 分支在刷新前**无** `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` 文件（仅主仓库 `master` 有）；本次 Plan 将 INDEX 同步入 `docs/implementation_tasks/.../BATCH_3V_VERIFIED_AUDIT_CLEANUP/`。
- Execute / repair 证据已存在；本刷新为 **Plan SSOT 对齐**，不改变已落地业务 diff 语义。
