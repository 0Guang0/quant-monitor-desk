# PERF-AUD — 性能维度只读评估（Phase B3）

> **模板：** `agents/performance-engineer.md`（全文 Read，对抗性权威 Read `agents/audit-adversarial-authority.md`）  
> **分支/工作区：** `debt/test-hygiene/integration` @ `C:\Users\Guang\Desktop\quant-monitor-desk`  
> **模型：** Composer 2.5（禁止 fast）  
> **模式：** 只读评估 — **禁止改码、禁止 git commit**

## 任务

对 audit 桶模块做 **时长 + 内存 + I/O** profiling，产出逐项 ✅/⚠️/❌ 分析报告。

## Allowed 模块（仅分析）

```
tests/test_audit_remediation.py
tests/test_audit_fixes.py
```

注意：`test_audit_remediation.py` import 自 `test_batch_d_orchestration_flow` / `test_sync_orchestrator` — 分析时可引用，**本阶段不改 DS 文件**；跨文件优化写入「MERGE-C 提案」段。

## Baseline（必读）

- `.trellis/tasks/debt-test-hygiene-batch/execute-evidence/phaseB2-pytest-durations.txt`
- `.trellis/tasks/debt-test-hygiene-batch/execute-evidence/phaseB2-analysis.md`
- `.trellis/tasks/debt-test-hygiene-batch/DEBT.plan.md` §1.1

## 必跑命令

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run pytest tests/test_audit_remediation.py tests/test_audit_fixes.py -q --durations=20
```

Top 5 慢测：各测 RSS + tmp DuckDB 观测（命令写入报告）。

## 产出

```
.trellis/tasks/debt-test-hygiene-batch/execute-evidence/perf-AUD-report.md
```

结构同 PERF-DS prompt（Baseline / 耗时 / 资源 / 逐项分析 / ✅ 建议 / ❌ 不可做）。

## 硬约束

- §1.1 价值守恒；不得建议以删 audit 事件断言换速度
- `test_partialSuccess_eachItemWritesAuditEvent` 需 events≥3 — 不可缩分片
