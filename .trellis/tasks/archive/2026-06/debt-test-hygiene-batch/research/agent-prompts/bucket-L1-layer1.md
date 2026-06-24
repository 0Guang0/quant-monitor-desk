# Agent 派发 — 桶 L1（Layer1 Ingestion）

> **Worktree：** `debt/test-hygiene/bucket-l1-layer1` from `master`  
> **Bucket ID：** L1

## Allowed files

```
tests/test_layer1_axis_loader.py
tests/test_layer1_interpretation.py
tests/test_layer1_ingestion_gates.py
tests/test_layer1_observation_ingestion.py
tests/test_observation_mapper.py
tests/test_ingestion_validation_migration.py
```

## 特殊注意

- 多个模块共享 DB/fixture 模式；优先复用 `tests/conftest.py` 已有 fixture，勿复制 `apply_migrations` 块
- `test_batch25_production_data_gate.py` 不在本桶（属 G），但 layer1 测试常涉及 staged-only 语义：勿在 layer1 测试里引入 production-live 断言
- Phase B 候选：`test_layer1_observation_ingestion.py`、`test_layer1_ingestion_gates.py` 若 baseline durations Top 30 则标记 perf 机会；**不得**为提速弱化 staged/DB 写路径断言（§1.1）

## 验证命令

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run python -m pytest tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py tests/test_observation_mapper.py tests/test_ingestion_validation_migration.py -q --tb=short
```

## 证据

`.trellis/tasks/debt-test-hygiene-batch/execute-evidence/bucket-L1-*`

## 公共约束

见 `_COMMON.md`。
