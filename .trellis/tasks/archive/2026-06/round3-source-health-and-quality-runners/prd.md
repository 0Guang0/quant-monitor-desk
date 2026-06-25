# PRD — B3F-SH Source Health & Quality Runners

## 背景

Round 3F.3 负责将 read-only data health（DH2）升级为生产前必需的 source health 跟踪与 quality runner 实现，并闭环 `B2.5-O-05` FRED live primary（用户已授权）。

## 用户故事

1. 作为运维，我需要 `source_health_snapshot` 持久化行，以便追踪各 source 健康状态（非 DH2 只读报告）。
2. 作为数据工程师，我需要 `run_revision_audit` / `run_data_quality` 可调用，而非永久 defer。
3. 作为 coordinator，我需要在授权下完成 FRED-only live pilot 并证明无 production mutation。

## 非目标

- production clean write
- ResourceGuard / Layer1 perf（B3F-HYG）
- registry 三件套直接 commit（主会话）
- migration SQL 文件（B3F-MIG，除非主会话协调）

## 成功指标

- `validate-plan-freeze` exit 0
- R3F-SH-01..07 各有 RED/GREEN 证据
- DH2 路径零 `source_health_snapshot` DDL
