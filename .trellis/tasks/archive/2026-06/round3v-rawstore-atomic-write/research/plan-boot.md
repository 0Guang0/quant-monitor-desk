# Plan Boot — B3V-STOR

> Phase P0 complete

## 用户目标

为 `RawStore` 原始证据落盘（json/csv/parquet）增加**原子写**语义：写到一半崩溃或异常时，目标路径不得留下半拉子文件；同 `content_hash` 重复保存保持幂等。

## 依赖

| 依赖                        | 状态         | Plan 策略                                         |
| --------------------------- | ------------ | ------------------------------------------------- |
| post Batch 01 `master` 基线 | 已合并       | worktree `fix/round3v-rawstore-atomic-write`      |
| B3V-DATA schema_hash        | 并行         | 只读；不得改 `validation_gate.py`                 |
| Registry 三件套             | 主会话批闭合 | agent 仅 proposed delta（`VR-STOR-001` closeout） |

## AC 草稿

- `write_bytes_atomic`：同目录临时文件 → flush/fsync → `os.replace`
- `RawStore.save` 对支持类型走原子写
- 写失败：目标不存在或内容不变；临时文件清理
- 同内容重复 `save` 幂等
- `VR-STOR-001` 关闭证据或精确 re-defer

## 原计划已读

- [x] `docs/implementation_tasks/README.md`
- [x] `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3V
- [x] GLOBAL×4
- [x] `ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md`
- [x] `B02_03_rawstore_atomic_write.md`（任务卡）
- [x] `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 + §3.4 + §4
- [x] `BATCH_3V_HARDENING_RULES.md` §1–§7
- [x] `BATCH_3V_TASK_CARD_MANIFEST.md`
- [x] `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md`（`VR-STOR-001` 路由）

## 当前 Round batch map

Batch 3V 协调包 · `B3V-C03` · 正式线 Track A · 合并序 5（playbook §7.2）。

**Phase P0 complete**
