# bucket-OPS align-checklist (Phase A)

Branch: `debt/test-hygiene/bucket-ops-cli`  
Worktree: `quant-monitor-desk-worktrees/bucket-ops-cli`  
Date: 2026-06-24

## 五问汇总（全桶 Y）

| 文件                                  | 用例数 | Q1 对象 | Q2 验证点 | Q3 失败含义 | Q4 无多余行为 | Q5 复用 helper                                                                   |
| ------------------------------------- | ------ | ------- | --------- | ----------- | ------------- | -------------------------------------------------------------------------------- |
| test_ops_db_inspector.py              | 31     | Y       | Y         | Y           | Y             | Y（新增 `_run_qmd_db_inspect_cli`、`_write_files`；保留 subprocess fail-closed） |
| test_ops_interface_probe.py           | 5      | Y       | Y         | Y           | Y             | Y                                                                                |
| test_interface_probe_018c.py          | 7      | Y       | Y         | Y           | Y             | Y                                                                                |
| test_data_cli_contract.py             | 5      | Y       | Y         | Y           | Y             | Y                                                                                |
| test_config.py                        | 5      | Y       | Y         | Y           | Y             | Y（新增 `_reload_config`）                                                       |
| test_config_templates.py              | 2      | Y       | Y         | Y           | Y             | Y                                                                                |
| test_dependency_extras_contract.py    | 3      | Y       | Y         | Y           | Y             | Y（`_pyproject_text` 去重读盘）                                                  |
| test_api_security_contract.py         | 3      | Y       | Y         | Y           | Y             | Y                                                                                |
| test_reference_adoption_guardrails.py | 3      | Y       | Y         | Y           | Y             | Y（contract_gate_support）                                                       |

**合计：** **64 collected → 63 passed, 1 skipped**（symlink 平台 skip）

## Phase A ponytail 改动（价值守恒）

| 改动                                | 说明                                                                             |
| ----------------------------------- | -------------------------------------------------------------------------------- |
| `_run_qmd_db_inspect_cli`           | 统一 qmd_ops db-inspect **子进程**路径；fail-closed 用例仍断言 `returncode != 0` |
| `_parse_cli_json`                   | CLI 成功路径仍校验 returncode 与 JSON 解析                                       |
| `_write_files`                      | 去重子目录/file 种子 setup；parametrize 覆盖不变                                 |
| 移除未用 `monkeypatch` / `tmp_path` | `test_qmdOps_cli_invokesSameInspector`、禁止 flag 用例                           |
| `_reload_config`                    | config 环境变量 reload 模式复用                                                  |
| `_pyproject_text`                   | pyproject 单次读取                                                               |

## 注释冲突

见 `bucket-OPS-comment-conflicts.md` → **none**

## diff 范围

仅 3 文件：`test_ops_db_inspector.py`、`test_config.py`、`test_dependency_extras_contract.py`（均在 allowed 列表）
