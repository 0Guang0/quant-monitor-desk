# Research: WAVE0 §5 SSOT ↔ Trellis vertical-slices 对齐

- **Query**: 垂直切片 SSOT `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §5 与 `research/vertical-slices.md` 一致性
- **Scope**: internal
- **Date**: 2026-06-28

## Findings

### SSOT 来源

| 文档 | 仓库位置 | worktree 可见 |
| --- | --- | --- |
| WAVE0 INDEX §5 B3V-C03 | `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/WAVE0_BATCH3V_TO_ISSUES_INDEX.md` | **主仓库有**；`quant-monitor-desk-wt-b3v-stor` **无此文件** |
| Trellis 冻结切片 | `.trellis/tasks/round3v-rawstore-atomic-write/research/vertical-slices.md` | 有 |

### 字段级对照（§5 vs vertical-slices.md）

| 序 | WAVE0 ID | Trellis ID | WAVE0 交付物 | Trellis 建设内容 | WAVE0 依赖 | Trellis 依赖 | WAVE0 证据 | Trellis 证据 | 一致 |
| -- | -------- | ---------- | ------------ | ---------------- | ---------- | ------------ | ---------- | ------------ | ---- |
| 1 | STOR-01 | STOR-01 | `path_compat.write_bytes_atomic` | 同左 + flush/fsync/replace/清理 | — | — | `9.1-red/green.txt` | `9.1-red.txt` / `9.1-green.txt` | Y |
| 2 | STOR-02 | STOR-02 | `save` → atomic | `RawStore.save` 改调 atomic | STOR-01 | STOR-01 | `9.2-red/green.txt` | 同 | Y |
| 3 | STOR-03 | STOR-03 | 无半写文件 | crash mock/patch | STOR-02 | STOR-02 | `9.3-red/green.txt` | 同 | Y |
| 4 | STOR-04 | STOR-04 | 同 content 重复 save | 幂等 | STOR-02 | STOR-02 | `9.4-red/green.txt` | 同 | Y |
| 5 | STOR-05 | STOR-05 | proposed registry delta | VR-STOR-001 closeout YAML | STOR-03..04 | STOR-03..04 | 主会话 | `registry_proposed_delta.yaml` | Y |

### WAVE0 §5 Acceptance criteria ↔ MASTER AC

| WAVE0 AC | MASTER AC | 映射 |
| --- | --- | --- |
| `write_bytes_atomic` 单测绿 | AC-STOR-01 | §9.1 |
| 写中途异常 absent/unchanged | AC-STOR-03 | §9.3 |
| 重复 save 同 hash | AC-STOR-04 | §9.4 |
| 禁止 content_hash 命名变更 | MASTER §3.2 out | — |
| 禁止 Windows POSIX-only dir fsync | MASTER §2.2 · path_compat ponytail 注释 | AC-STOR-01 |

### 任务卡 B02-STOR-01..05 映射

活卡 `B02_03_rawstore_atomic_write.md` §5 使用 `B02-STOR-0x` 前缀；WAVE0/Trellis 使用 `STOR-0x` — 同一竖条，命名空间不同，已在 `original-plan-trace.md` 与 `vertical-slices.md` 注明。

## Caveats / Not Found

- worktree 缺 WAVE0 INDEX 物理文件：对齐基于主仓库 §5 文本与 worktree `vertical-slices.md`  diff，**无内容漂移**。
- 若 Wave 0 协调 checklist §7 要求 INDEX 已 commit 到 master，主会话需确认该文件是否已 merge 到 `fix/round3v-rawstore-atomic-write` 所跟踪的 `master` 尖端。

## 结论

**PASS** — STOR-01..05 竖条与 WAVE0 §5 SSOT 语义一致；Trellis 冻结表为 Execute 可用 SSOT。
