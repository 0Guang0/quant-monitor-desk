# Project Overview — B3F-SH

> Plan Phase 1a · ≤1 页

## 是什么

Batch 3F.3 将 data health 从 DH2 只读报告升级为 Batch6 **source health 持久化**与 **sync quality runner** 闭包，并在用户授权下完成 FRED live primary 跟踪。

## 关键模块

| 模块 | 路径 | 本任务动作 |
| ---- | ---- | ---------- |
| Data health v2 | `backend/app/ops/data_health.py` | 扩展 persist writer；DH2 profile 仍只读 |
| Sync orchestrator | `backend/app/sync/orchestrator.py` | 实现 `run_revision_audit` / `run_data_quality` |
| Schema | `docs/modules/data_sources.md` | `source_health_snapshot` 列 SSOT |
| Live pilot | `execute-evidence/fred_live_authorization_*.yaml` | SH-06 唯一 live 入口 |

## 并行边界

- **B3F-MIG** 拥有 `migrations/**` 文件锁；SH-01 migration SQL 须协调
- **B3F-HYG** 拥有 ResourceGuard；本任务不修改
- **主会话** 合并 registry RESOLVED 行

## 风险

| 风险 | 缓解 |
| ---- | ---- |
| DH2 路径误建表 | SH-05 边界测试 + §1.5 停损 |
| 无授权 live | SH-06 须 YAML + policy 双门 |
| AkShare false-close | SH-07 registry guard |
