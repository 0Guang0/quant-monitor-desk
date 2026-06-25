# 垂直切片 — B3F-MIG (/to-issues)

| 序 | ID | 交付物（完标准） | 依赖 | AC | 允许文件 |
|----|-----|------------------|------|-----|----------|
| 1 | MIG-01 | 009 CHECK 存在 + 无 013 重复 migration 测试绿 | — | AC-MIG-01 | 测试只读 009 |
| 2 | MIG-02 | ADR-002 priority 段 + 012 MRQ 无 priority CHECK + duckdb 烟测 | MIG-01 | AC-MIG-02 | ADR-002, 012, tests |
| 3 | MIG-03 | 012 显式列重建 fetch_log/MRQ（无 SELECT *） | MIG-01 | AC-MIG-03 | 012, tests |
| 4 | MIG-04 | lifecycle 列 + sync generation/tombstone 测试 | MIG-03 | AC-MIG-04 | 012, source_registry.py, tests |
| 5 | MIG-05 | COVERAGE + 008 PLAN Round 3F 路由段 | MIG-03 | AC-MIG-05 | docs/schema/* |
| 6 | MIG-06 | roadmap R3F-MIG-06 CLOSED B3V 行回归 | — | AC-MIG-06 | ROADMAP 只读 assert |

**不在切片内**: `source_health_snapshot` — B3F-SH；registry 三件套 — B3F-REG。

## 工单要点

### MIG-01（verify-only）
- 不断言新 migration 内容；只 verify 009 含 CHECK 且无 013 文件

### MIG-03
- INSERT 必须列名列表；section 内禁止 `SELECT *`

### MIG-04
- `registry_generation >= 1` after sync；orphan tombstone `removed_from_yaml_at` 非空
