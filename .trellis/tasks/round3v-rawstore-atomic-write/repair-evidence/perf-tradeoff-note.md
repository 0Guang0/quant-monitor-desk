# B3V-STOR — fsync / 原子写性能权衡（A6 NB）

## 结论

`write_bytes_atomic` 对每次写入执行 `flush` + `os.fsync`（文件 fd）。对 RawStore 证据落盘（低频、单文件 ≤256 MiB）可接受。

## 代价

- **延迟**：fsync 强制刷盘，比纯 `write_bytes` 慢一个数量级（取决于磁盘/虚拟化）。
- **吞吐**：高频小文件 burst 时 fsync 成为瓶颈。

## 未做（ponytail 天花板）

- 未对**父目录**做 fsync：极端断电场景下新文件可能不可见（POSIX 目录项耐久性）。
- 全 payload 在内存中缓冲，超大文件受 `MAX_RAW_FILE_BYTES` 约束。

## 复评触发

若未来 sync 路径改为高频小写或批量 micro-fetch，复评是否改为组写、间隔 fsync 或 WAL。
