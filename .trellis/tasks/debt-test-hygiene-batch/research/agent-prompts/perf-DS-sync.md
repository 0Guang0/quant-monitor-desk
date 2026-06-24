# PERF-DS — 性能维度只读评估（Phase B3）

> **模板：** `agents/performance-engineer.md`（全文 Read，对抗性权威 Read `agents/audit-adversarial-authority.md`）  
> **分支/工作区：** `debt/test-hygiene/integration` @ `C:\Users\Guang\Desktop\quant-monitor-desk`  
> **模型：** Composer 2.5（禁止 fast）  
> **模式：** 只读评估 — **禁止改码、禁止 git commit**

## 任务

对下列模块做 **时长 + 内存 + I/O** profiling，产出逐项 ✅/⚠️/❌ 分析报告。这是 debt-lite Phase B 补测，**无** `AUDIT.plan.md` / `MASTER.plan.md`；权威 = `DEBT.plan.md` §1.1 + `performance-engineer.md` checklist。

## Allowed 模块（仅分析，本阶段不改）

```
tests/test_sync_orchestrator.py
tests/test_batch_d_orchestration_flow.py
tests/test_vendor_fetch_e2e.py
tests/service_path_support.py   # 只读引用；若要改 fixture 仅写提案
```

## Baseline（必读）

- `.trellis/tasks/debt-test-hygiene-batch/execute-evidence/phaseB2-pytest-durations.txt`
- `.trellis/tasks/debt-test-hygiene-batch/execute-evidence/phaseB2-analysis.md`
- `.trellis/tasks/debt-test-hygiene-batch/DEBT.plan.md` §1.1

## 必跑命令（记录完整命令 + 输出摘要）

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run pytest tests/test_sync_orchestrator.py tests/test_batch_d_orchestration_flow.py tests/test_vendor_fetch_e2e.py -q --durations=20
```

对 **Top 5 call 最慢用例** 各跑一次资源快照（任选 psutil / tracemalloc，须在报告中写清命令）：

- 峰值 RSS（MB）
- 若可观测：pytest tmp_path 下 DuckDB 文件数与总字节（setup 阶段 vs call 阶段）

全 suite 注明：**串行** pytest（无 xdist，见 `pytest.ini`）。

## 产出（必交）

```
.trellis/tasks/debt-test-hygiene-batch/execute-evidence/perf-DS-report.md
```

报告结构：

1. Baseline（命令、Python 版本、串行说明）
2. Top 慢测表（call 耗时）
3. Top 5 资源表（RSS + 磁盘/tmp 观测）
4. **逐项深度分析**（每个 Top 15 慢测一行扩展段）：注释验证点、✅/⚠️/❌、ponytail 手段、§1.1 价值是否守恒
5. 建议实施清单（仅 ✅ 项，按收益排序）
6. 明确「不可做」清单（❌ 项及理由）

## 硬约束

- §1.1：不得建议删测、弱 assert、mock 偷换真实 E2E/network/CLI
- 不得建议减 `repeatRun` 次数、减 ≥3 分片 backfill（注释锁死）
- 需要改 `conftest.py`：只写提案段落，不改文件
