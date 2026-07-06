# 已知 Pytest Skip 登记

> 运维/CI 排障参考。完整审计上下文见 `docs/quality/待修复清单.md` 与 `docs/RESOLVED_ISSUES_REGISTRY.md`。

| 测试                                                                               | Skip 条件                                 | 平台                 | 缓解措施                                                |
| ---------------------------------------------------------------------------------- | ----------------------------------------- | -------------------- | ------------------------------------------------------- |
| `tests/test_ops_db_inspector.py::test_dbInspect_symlinkOutsideDataRoot_notCounted` | `symlinks not supported on this platform` | Windows（常见）      | 在 Linux CI 上运行；符号链接路径 containment 在那里覆盖 |
| `tests/test_raw_store.py::test_save_windowsLongPath_writesSuccessfully`            | `Windows long-path regression only`       | 非 Windows           | Windows 开发机/agent 覆盖 MAX_PATH                      |
| `tests/test_path_compat.py::*`                                                     | `Windows-only`                            | 非 Windows           | 同上                                                    |
| `tests/test_batch25_production_data_gate.py`（条件性）                             | 缺少本地生产 DB 或 `data/raw`             | 无生产产物的开发环境 | 预期行为；gate 仅测本地就绪状态                         |

**全量套件预期：** `pytest -q` → Windows 上出现 1 个 skip（符号链接测试）属正常。

## 快速 CI 配置

```bash
# 全量套件（本地默认 / nightly）
pytest -q

# 快速配置 — 排除标记为 @pytest.mark.slow 的测试
pytest -q -m "not slow"
```

当前标记为 slow 的测试：`tests/test_layer1_observation_ingestion.py` 中的 phase3/phase4 证据产物测试（见 `test_layer1Ingestion_phase3_taskEvidenceArtifacts`、`test_layer1Ingestion_phase4_taskEvidenceArtifacts`）。

标记注册位置：`pyproject.toml` 的 `[tool.pytest.ini_options].markers`。
