# Project Overview — B3V-STOR

> Plan Phase 1a · GitNexus query

## 模块边界

| 模块           | 路径                                   | 本任务                                  |
| -------------- | -------------------------------------- | --------------------------------------- |
| RawStore       | `backend/app/storage/raw_store.py`     | **独占写**                              |
| path_compat    | `backend/app/storage/path_compat.py`   | **独占写**（新增 `write_bytes_atomic`） |
| FileRegistry   | `backend/app/storage/file_registry.py` | **只读**（除非测试证明必需）            |
| ValidationGate | `backend/app/db/validation_gate.py`    | forbidden                               |
| sync/\*\*      | `backend/app/sync/**`                  | forbidden                               |

## 当前写路径（基线）

`RawStore.save` 在 `mkdir_parents` 后直接调用 `path_compat.write_bytes(dest_path, content)` — 非原子：进程在 `write_bytes` 中途崩溃可能留下截断目标文件。

## 支持类型

`json` / `csv` / `parquet`（`_EXT_MAP`）；`content_hash` 命名 `{sha256}.{ext}` 不变。

## 平台注意

`path_compat` 已有 Windows 长路径 `to_extended_path`；原子写须复用同一前缀逻辑；**不得**让 Windows 行为依赖 POSIX-only 目录 `fsync`。

## authority_graph

`backend/app/storage/` — storage 域；本任务仅触及 raw I/O helper，不扩 FileRegistry 语义。
