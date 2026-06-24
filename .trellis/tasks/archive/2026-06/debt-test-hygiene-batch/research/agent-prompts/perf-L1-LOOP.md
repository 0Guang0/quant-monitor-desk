# PERF-L1-LOOP — 性能维度只读评估（Phase B3）

> **模板：** `agents/performance-engineer.md`（全文 Read，对抗性权威 Read `agents/audit-adversarial-authority.md`）  
> **分支/工作区：** `debt/test-hygiene/integration` @ `C:\Users\Guang\Desktop\quant-monitor-desk`  
> **模型：** Composer 2.5（禁止 fast）  
> **模式：** 只读评估 — **禁止改码、禁止 git commit**

## 任务

对 Layer1 + Loop 相关慢测做 **时长 + 内存 + I/O** profiling。

## Allowed 模块（仅分析）

```
tests/test_layer1_observation_ingestion.py
tests/test_layer1_ingestion_gates.py
tests/test_ingestion_validation_migration.py
tests/test_loop_engineering_flow.py
```

## Baseline（必读）

- `.trellis/tasks/debt-test-hygiene-batch/execute-evidence/phaseB2-pytest-durations.txt`
- `.trellis/tasks/debt-test-hygiene-batch/execute-evidence/phaseB2-analysis.md`
- `.trellis/tasks/debt-test-hygiene-batch/DEBT.plan.md` §1.1

## 必跑命令

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run pytest tests/test_layer1_observation_ingestion.py tests/test_layer1_ingestion_gates.py tests/test_ingestion_validation_migration.py tests/test_loop_engineering_flow.py -q --durations=20
```

Top 5 慢测：RSS + tmp 观测。`test_contextRouter_cli_taskFlag_writesContextPack` 须标注 subprocess 不可 mock。

## 产出

```
.trellis/tasks/debt-test-hygiene-batch/execute-evidence/perf-L1-LOOP-report.md
```

结构同 PERF-DS prompt。

## 硬约束

- `validation_module_db` 已 module-scoped — 评估是否还有 per-test 重复 migrate
- phase3+4 已单 db — 评估 phase4 evidence / slow 标记用例
- §1.1；CLI subprocess 路径不可改 import 直调
