# B3V-STOR — 孤儿 temp 文件运维说明（A7 NB-1）

## 模式

原子写 temp 命名：`.{dest_basename}.tmp.{pid}.{hex}`，与目标文件**同目录**。

示例：`raw/qmt/daily_bar/2026-06-15/.abc123....json.tmp.12345.a1b2c3d4`

## 正常行为

- `os.replace` 成功：temp 消失，仅目标文件存在。
- 任意失败（replace / write）：`write_bytes_atomic` 在 `except` 中 `unlink` temp（`missing_ok=True`）。

## 何时可能残留

- 进程在 `unlink` 前被 `SIGKILL` / 断电。
- 磁盘满导致 unlink 失败（已 swallow `OSError`，temp 可能留下）。

## 运维动作

1. 在 `data_root` 下查找：`find data -name '.*.tmp.*' -type f`（Windows：`Get-ChildItem -Recurse -Filter '.*.tmp.*'`）。
2. 确认对应目标路径无正在写入的进程后删除孤儿 temp。
3. **不要**删除无 `.tmp.` 段的正常 `.{hash}.json` 隐藏文件（若有其他工具创建）。

## 监控建议

周期性 cron / 部署后 smoke：孤儿 temp 计数应为 0 或极低；突增表示写路径异常或机器硬杀。
