# Grill-me Session — B-19 staged pilot v2

## 质疑与回应

| 质疑 | 回应 / MASTER 吸收 |
| ---- | ------------------ |
| 九切片是否会被合成一个 run 脚本？ | §8 每切片独立 RED/GREEN + evidence 文件 |
| 扩样会否触发 production 写？ | sandbox `QMD_DATA_ROOT`；§1.5 停损 |
| proof_status 仍假安全？ | R3Y-MUT-PROOF-001 纳入 SP2-08 必做 |
| akshare 网络失败怎么算过？ | 明确 re-defer taxonomy；不得当 primary |
| 能否声称 sandbox clean-write 就绪？ | closeout 字段 `sandbox_clean_write_rehearsal` 单独判定 |

## Red Flags → MASTER §7

- 超 cap 无用户批准
- closeout 仅 VERIFIED 无 hash/count
- sync `adapter=` 生产旁路
