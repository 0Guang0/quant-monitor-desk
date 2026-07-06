# ADR-003：任务文档与实现路径映射

> **相关：** 写入热路径复杂度决策见 [ADR-004](ADR-004-write-path-complexity-ceiling.md)。

## 状态

已接受（2026-06-19）

## 背景

早期 Round2 任务文档常写 `backend/sources/*`，实际落地布局为 `backend/app/datasources/*`。若不统一映射，执行者与 agent 会在错误目录找代码。

## 路径映射

| 任务 / 文档中的路径          | 实际代码路径                                 |
| ---------------------------- | -------------------------------------------- |
| `backend/sources/registry`   | `backend/app/datasources/source_registry.py` |
| `backend/sources/adapters/*` | `backend/app/datasources/adapters/*`         |
| `backend/sources/fetch_log`  | `backend/app/datasources/fetch_log.py`       |
| `backend/sync/orchestrator`  | `backend/app/sync/orchestrator.py`           |
| `backend/validators/*`       | `backend/app/validators/*`                   |
| `backend/db/migrations`      | `backend/app/db/migrations`                  |

## 数据库命名说明

| 层级      | 字段                                                                |
| --------- | ------------------------------------------------------------------- |
| YAML      | `allowed_domains`（列表）                                           |
| Python    | `SourceRecord.allowed_domains`（`frozenset`）                       |
| DB        | `allowed_domain`（JSON 数组字符串，列名为单数）                     |
| DB 镜像列 | `allowed_domains_json`（与 `allowed_domain` 同内容，migration 008） |

## 后果

- 新模块须遵循 `backend/app/<layer>/` 布局。
- 任务文档应引用本 ADR，勿再使用遗留的 `backend/sources` 路径。
