# PRD — B01-DH2 Data Health v2

## 问题

Batch 01 产生 WL/FRED/TDX/SP3 证据后，缺少统一只读体检报告判断证据是否满足 staged/sandbox gate，且 master 上 v1 integration 测因断裂 raw 路径已红。

## 用户故事

作为协调者，我希望对给定 evidence 目录运行 `data_health` profile，得到 PASS/WARN/FAIL/BLOCKED 及 sandbox clean-write 资格陈述，以便决定是否进入 rehearsal，且全程无 fetch、无 DB 写。

## 非目标

- production-live / clean-write 启用
- registry 自动闭合
- `source_health_snapshot` 表

## 成功指标

- 五 profile + rollup 有语义测试
- 基线 integration 绿
- Playbook §8.7 验收命令绿
