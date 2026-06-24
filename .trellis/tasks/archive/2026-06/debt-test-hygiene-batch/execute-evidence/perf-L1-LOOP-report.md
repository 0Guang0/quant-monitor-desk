# PERF-L1-LOOP — 只读评估 + B3 实施（Phase B3）

> 模板：`agents/performance-engineer.md` | 证据：`perf-L1-LOOP-pytest.txt`

## Baseline

```powershell
uv run pytest tests/test_layer1_observation_ingestion.py tests/test_layer1_ingestion_gates.py tests/test_ingestion_validation_migration.py tests/test_loop_engineering_flow.py -q --durations=20
```

- **127 passed**（估）；Top：`contextRouter_cli` 0.90s、`phase4_taskEvidenceArtifacts` 0.74s

## B3 已实施（§1.1 + ponytail）

| 用例/模块                           | 手段                                           | 价值                      |
| ----------------------------------- | ---------------------------------------------- | ------------------------- |
| `test_initDb_runTwice_isIdempotent` | 复用 `validation_module_db`（二次 apply 幂等） | 同库二次 apply + 005 一条 |
| `test_layer1_ingestion_gates.py`    | `@lru_cache _repo_text`                        | gate 文档扫描断言不变     |

## 未做（❌）

- `test_initDb_prodPath` — ConnectionManager 生产路径不可 module 共享
- `contextRouter_cli` / LOOP subprocess — 不可改 import
- `@pytest.mark.slow` evidence 管道 — 不可删步骤
