# Agent 04 — 代码质量深度审计

## 1. 独立角色边界

本 agent 只从代码质量角度审计：正确性、可读性、错误处理、边界验证、静态/动态质量门禁、前后端构建与回归质量。不负责设计偏差、性能或数据库专项判断。

## 2. 使用的有效 skill / 工具

| 名称                          | 用途                                                         | 执行命令或依据                                                         | 结果                                       |
| ----------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------- | ------------------------------------------ | ---- | ------------------------------------------- | ---------------------------------------------------- |
| code-review-and-quality skill | 五轴代码评审：正确性、可读性、架构、安全、性能               | 已加载；结合测试、搜索、关键文件读取                                   | 发现质量整体可运行，但有长模块与低覆盖热点 |
| security-and-hardening skill  | 输入/路径/外部数据边界安全审计                               | 已加载；读取 `raw_store.py`, `axis_loader.py`, Layer1 route/fetch 搜索 | 主要路径有校验；未发现直接 adapter 绕过    |
| CodexPro search/read          | 静态审计 TODO/FIXME/pass、直接 adapter factory、关键路径代码 | `search TODO                                                           | FIXME                                      | pass | NotImplemented`; `search create_adapter...` | 仅发现可接受异常吞噬点；Layer1 未直接 create_adapter |
| pytest / pytest-cov           | 动态质量门禁                                                 | 多组 pytest；coverage                                                  | 全量通过；coverage 91.31%                  |
| npm typecheck/test/build      | 前端质量门禁                                                 | `npm run typecheck`, `npm test`, `npm run build`                       | 全通过                                     |

未计入：`ruff check .` 因 safe bash allowlist 拒绝执行，无法作为有效质量工具。

## 3. 执行命令与结果

| 命令                                                                                                                                                  | 结果摘要                                  |
| ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| `pytest -q`                                                                                                                                           | exit 0；收集 589 项；观察到 1 skip        |
| `pytest --cov=backend --cov-fail-under=85 -q`                                                                                                         | exit 0；总覆盖率 91.31%                   |
| `pytest tests/test_write_manager.py tests/test_data_quality_validator.py tests/test_source_conflict_validator.py tests/test_db_validation_gate.py -q` | exit 0                                    |
| `pytest tests/test_module_boundaries.py tests/test_global_execution_rules.py tests/test_documentation_index.py tests/test_manifest_protocol.py -q`    | exit 0                                    |
| `npm run typecheck`                                                                                                                                   | exit 0                                    |
| `npm test` in `frontend`                                                                                                                              | 2 files / 3 tests passed                  |
| `npm run build` in `frontend`                                                                                                                         | exit 0；Vite build 88ms；JS gzip 60.16 kB |

## 4. 质量发现

### 正向证据

- 全量 pytest 通过，coverage gate 通过。
- Route/service/write/validation/conflict 关键套件通过。
- 前端 typecheck/test/build 通过。
- `raw_store.py` 有 segment allowlist、256MB 上限、path containment、content hash。
- `axis_loader.py` 对 spec root 限制在 project root 或系统 temp。

### 问题清单

#### P0

无。

#### P1

| ID        | 问题                                                     | 证据                                                    | 影响                                                | 当前阶段可修复?                  | 修复状态 | 解决方案                                                                           |
| --------- | -------------------------------------------------------- | ------------------------------------------------------- | --------------------------------------------------- | -------------------------------- | -------- | ---------------------------------------------------------------------------------- |
| A04-P1-01 | Python lint/format 质量门禁未能在本环境执行              | `ruff check .` 被 CodexPro safe allowlist 拒绝          | 无法复核 import/order/UP/E/F/I 质量门禁；不能给 95+ | 是，但本轮工具限制且用户禁止变更 | 未修复   | 在 full bash/CI 环境执行 `ruff check .` 与 `ruff format --check .`，修复后重跑全量 |
| A04-P1-02 | `ingestion.py` 过长且混合 runtime/evidence，降低代码质量 | A2 ponytail report：1,516 LOC、evidence/tooling 557 LOC | 高认知负载，后续改动容易引入回归                    | 是，但用户禁止代码变更           | 未修复   | 拆分 runtime service 与 evidence writer，保持测试绿                                |

#### P2

| ID        | 问题                                    | 证据                                                                             | 影响                            | 当前阶段可修复? | 修复状态 | 解决方案                                                           |
| --------- | --------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------- | --------------- | -------- | ------------------------------------------------------------------ |
| A04-P2-01 | 覆盖率低点集中在关键边界模块            | coverage：`observation_mapper.py` 55%，`raw_store.py` 54%，`db_inspector.py` 77% | 单项低覆盖可能隐藏边界异常      | 是              | 未修复   | 为 raw payload 异常、path edge、DB inspector 错误路径补行为测试    |
| A04-P2-02 | 全量测试有 1 skip，报告未定位 skip 原因 | `pytest -q` 进度中出现 `s`; `pytest --collect-only` 共 589 项                    | skip 可能掩盖环境或平台依赖风险 | 是              | 未修复   | 在 CI 输出中记录 skipped test 名称和 skip reason，必要时补替代验证 |

#### P3

| ID        | 问题                                           | 影响                                  | 解决方案                            |
| --------- | ---------------------------------------------- | ------------------------------------- | ----------------------------------- | ----------------------- |
| A04-P3-01 | `except OSError: pass` 存在但上下文可接受      | `resource_guard.py`, `axis_loader.py` | 低；异常被用于 best-effort/路径兼容 | 保持或改为注释说明 why  |
| A04-P3-02 | 工作区存在未跟踪 `=` / `frontend/=` 等异常路径 | `show_changes`                        | 低到中；可能干扰人工 review         | release 前清理/确认来源 |

## 5. 当前未修复原因

本轮用户限制为只产出报告，不能修代码、测试、配置或文档。lint 也因工具 allowlist 不可执行。

## 6. 评分

**91 / 100 — FAIL**

扣分依据：ruff 未验证 -3；长模块/混责 -3；低覆盖热点 -2；skip 未定位 -1。

## 7. 达到 95+ 的最小修复清单

1. 在 CI/full shell 跑通 `ruff check .` 与 `ruff format --check .`。
2. 拆分 `ingestion.py` evidence tooling 或至少提取明显重复块。
3. 给 `observation_mapper.py`、`raw_store.py`、`db_inspector.py` 增加边界测试。
4. 明确 full pytest skip 原因。

## 8. 结论

本维度 **FAIL**。代码质量基础较好、测试回归通过，但未达到 95+ 的严格审计标准。
