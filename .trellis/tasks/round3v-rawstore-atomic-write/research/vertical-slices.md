# Vertical Slices — Phase 3.5 /to-issues（冻结）

> 工单 ID = STOR-01..05；对应任务卡 B02-STOR-01..05

| ID | 标题 | 建设内容 | 验收标准 | 依赖 | 证据输出 | 测试计划 |
| --- | --- | --- | --- | --- | --- | --- |
| STOR-01 | Atomic helper | `path_compat.write_bytes_atomic`：同目录 `.tmp.*`、flush/fsync、`os.replace`、失败清理 | RED: 无 helper 或直写目标；GREEN: helper 单测绿 | — | `9.1-red.txt` / `9.1-green.txt` | `test_writeBytesAtomic_*` |
| STOR-02 | RawStore wiring | `RawStore.save` 改调 `write_bytes_atomic` | RED: 仍调 `write_bytes`；GREEN: save 落盘绿 | STOR-01 | `9.2-red.txt` / `9.2-green.txt` | 既有 `test_save_*` 回归 |
| STOR-03 | Crash simulation | mock/patch 写中途异常；目标 absent 或 unchanged | RED: 失败留截断文件；GREEN: 断言无半写 | STOR-02 | `9.3-red.txt` / `9.3-green.txt` | `test_save_midWriteFailure_*` |
| STOR-04 | Idempotency | 同 content 重复 save | RED: 第二次破坏文件；GREEN: 字节/路径一致 | STOR-02 | `9.4-red.txt` / `9.4-green.txt` | `test_save_repeatedSameContent_*` |
| STOR-05 | VR-STOR-001 closeout | proposed registry delta + closeout 字段 | RED: 无 delta；GREEN: YAML 完整 | STOR-03..04 | `registry_proposed_delta.yaml` | 主会话 registry |

## 禁止水平合并

不得单 PR 同时改 validation_gate、sync、write 模式或 FileRegistry 语义。
