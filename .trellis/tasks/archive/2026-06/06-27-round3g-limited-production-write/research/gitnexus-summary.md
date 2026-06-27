# GitNexus Summary — R3G-03（Plan 1b）

## query: limited production clean write

高相关执行流：`rehearsal_runner` 已组合 DataSourceService → ResourceGuard → DbValidationGate → WriteManager → data-health profiles。R3G-03 应 **复用同一编排**，在入口增加 approval/audit/before/rollback 四门，而非新建平行写路径。

## 建议 impact 目标（Execute 改码前必跑）

| 符号                                   | 理由                 |
| -------------------------------------- | -------------------- |
| `run_rehearsal` / `RehearsalRunner`    | 编排复制风险         |
| `write_audit_decision`                 | promote 读取决策形状 |
| `build_production_mutation_proof`      | before/after proof   |
| `data_commands` sandbox-clean-write 组 | CLI 挂载             |

## blast radius（预估 LOW–MEDIUM）

- **直接调用方：** CLI `data_commands.py`、新 `limited_production_entry.py`
- **无影响：** layer1_axes ingestion allowlist（只读）、R3G-01/02 现有 CLI 行为（须保持拒绝生产路径除非 promote）
- **风险点：** 若误将 `DEFAULT_PRODUCTION_DB` 开放给 rehearse/audit → HIGH；须独立路径校验

## 复用决策（ponytail）

| 需求            | 复用                                            | 不新建                     |
| --------------- | ----------------------------------------------- | -------------------------- |
| row count proof | `mutation_proof.key_table_row_counts`           | 全库扫描 helper            |
| 授权 YAML 解析  | 参考 `staged_pilot.validate_authorization` 模式 | 另一套 auth 格式           |
| 门禁链          | `rehearsal_runner` 私有函数提取或镜像           | 第三套 write orchestrator  |
| rollback        | 新 `rollback_plan.py`（小）                     | WriteManager 内置 rollback |

## 测试锚点

已有契约静态测：`tests/test_round3g_limited_production_clean_write.py`（3 项）。Execute 须扩至 runner/CLI 对抗矩阵（活卡 §10）。
