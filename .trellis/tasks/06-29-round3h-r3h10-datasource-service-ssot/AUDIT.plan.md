# Audit matrix — R3H-10 DataSourceService SSOT

追溯：`EXECUTION_INDEX.md` §2 AC ↔ `research/00-EXECUTION-ENTRY.md` §1–§5 ↔ `frozen/R3H_10_DATASOURCE_SERVICE_SSOT.md`。

## 1. 维度门禁

| 维度        | 状态 | 说明                                                  |
| ----------- | ---- | ----------------------------------------------------- |
| A1 正确性   | 必做 | 切片 AC 见 `to-issues-slices.md`                      |
| A2 可读性   | 必做 | ENTRY 路由 + consolidation 对照表                     |
| A3 架构     | 必做 | ADR-025 fail-closed · service SSOT                    |
| A4 安全     | 必做 | 旁路守卫 · 无 secrets                                 |
| A5 测试     | 必做 | 每切片 RED→GREEN + 全量 pytest                        |
| A6 性能     | SKIP | 本 Wave 无独立 perf SLO；以全量 pytest 时长为回归哨兵 |
| A7 GitNexus | 必做 | 改 service 前 impact · commit 前 detect_changes       |
| A8 证据     | 必做 | `execute-evidence/9.x-*.txt` + STAGED-PILOT-SSOT 关账 |

## 2. 验收锚点

- **模块：** C2 DataSourceService · E4 staged/live 双轨
- **评级：** `R3_STAGED_FIXTURE_CLOSED` → `R4_SANDBOX_REAL_DATA_OR_REHEARSAL`
- **关账：** S10-CLOSE 后 `validate-plan-freeze` exit 0 · 解锁 R3H-07

无未解析占位符；维度验证见 `audit.jsonl`。
