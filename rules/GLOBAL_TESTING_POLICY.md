# Global Testing Policy

> **权威 skill：** `.cursor/skills/testing-guidelines/SKILL.md`（Agent 写测/审测时 Read；本文为项目策略摘要）

本测试策略来自项目约束与用户上传的测试规范。目标是让测试验证业务行为，而不是验证内部实现细节。

## 1. Mock 边界

允许 mock：

- 数据库连接。
- HTTP 调用。
- 文件系统 I/O。
- 消息队列。
- 第三方 API。
- 邮件、Webhook、桌面通知等外部通知渠道。

不应 mock：

- 纯计算逻辑。
- 条件分支。
- 状态判断函数。
- schema 校验逻辑。
- ResourceGuard 判断逻辑本身。

## 2. 断言要求

每个测试必须至少包含一个对业务语义有意义的断言，例如：

- 返回值是否等于业务预期。
- 状态是否发生正确变化。
- 持久化结果是否包含正确字段。
- 质量标记、错误码、warning 是否符合业务规则。

禁止把 `assertNotNull`、`assertDoesNotThrow` 作为唯一断言。

## 3. 不应断言的内容

除非顺序本身是业务约束，否则不要断言：

- private 方法是否被调用。
- private 方法被调用次数。
- 两个协作方法的内部调用顺序。
- 与业务结果无关的内部实现细节。

## 4. 必测场景

每个模块至少覆盖：

- 正常路径。
- 空值或缺失输入。
- 边界值。
- 异常路径。
- 资源限制路径。
- 数据质量失败路径。
- 不允许动作被拦截路径。

## 5. 测试命名

推荐：

```text
functionName_condition_expectedBehavior
```

例如：

```text
validate_sourceConflict_shouldCreateManualReviewQueue
resourceGuard_lowDisk_shouldPauseBackfill
```

## 6. 覆盖率策略

初期不追求机械 80% 覆盖率。优先覆盖：

- WriteManager。
- ResourceGuard。
- DataQualityValidator。
- SourceConflictValidator。
- Layer 1 / Layer 3 loader。
- Agent / Notification 的 No Action Semantics Guard。

每个 implementation task 必须写清本任务最低测试要求。

## 7. 测试函数 docstring（五字段 · 新增/修改 `test_*` 必填）

**CI 门禁：** `tests/test_docstring_quadruple_coverage.py`

每个 `test_*` 函数 docstring **必须**包含以下五行（通俗中文；第三行标签写 **`目的/目标：`** 或 **`目的：`**）：

| 字段      | 要求                                                                        |
| --------- | --------------------------------------------------------------------------- |
| 覆盖范围  | 本条测哪种业务场景（如拉数成功/失败、坏文件拒绝、合法数据映射、分阶段边界） |
| 测试对象  | 被测函数或行为路径                                                          |
| 目的/目标 | 要证明什么事实（小白能懂）                                                  |
| 验证点    | 关键断言/异常（技术名、错误码可写在此）                                     |
| 失败含义  | 挂了以后业务或审计失去什么保障                                              |

**金样（只读对照）：** `tests/test_layer3_snapshot_builder.py` 首条 `test_layer3Snapshot_buildsFromStagedLoaderAndL5_success`。

### 测试注释模板 1 — 正式提交时拉数失败不得入库

```python
    """覆盖范围：正式提交时底层拉数失败的处理——不得入库
    测试对象：commit_clean_observation_and_snapshots（fetch 被 mock 为失败）
    目的/目标：拉数失败就不能往正式观测表写任何数据，必须报错并中断整个提交
    验证点：抛出 IngestionCommitBlockedError，原因码 OBSERVATION_MAPPING；观测表仍为 0 行
    失败含义：拉数失败仍入库，脏或空数据会进入正式观测表
    """
```

对应实现：`tests/test_layer1_observation_ingestion.py::test_layer1Observation_fetchFailure_blocksCleanWrite`

### 测试注释模板 2 — 只拉原始数据时不写正式观测表

```python
    """覆盖范围：第三阶段「只拉原始数据」时，不得写入正式观测表
    测试对象：micro_fetch_staging
    目的/目标：staging 阶段只记拉取痕迹和 raw 文件，正式观测表（axis_observation）一行都不能多
    验证点：拉数前后观测表行数都是 0
    失败含义：第三阶段小批量拉数就写了正式观测，与第四阶段校验后再入库的设计冲突
    """
```

对应实现：`tests/test_layer1_observation_ingestion.py::test_layer1MicroIngestion_phase3DoesNotWriteCleanAxisObservation`

**禁止：** 用批量脚本生成 docstring；在目的/失败含义里堆 JSON 键名或异常类名而无业务解释。

**新增测试模块：** 在 `tests/` 下新增聚焦的 `test_*.py`；提交前 `uv run pytest -q` 全绿。

## 8. Deterministic / Golden / Time-freeze 基线

所有涉及数据接入、快照、报告、Agent 输出、回测和前端展示的测试，必须默认可复现。

最低要求：

```text
1. 固定随机种子：任何随机抽样、样本打散、fixture 生成都必须设置 seed。
2. 固定时钟：测试不得直接依赖 now()；必须注入 clock/as_of_date，或使用 time-freeze fixture。
3. 固定时区：所有日期时间测试必须声明 timezone，默认使用 UTC 或明确的交易所时区。
4. Golden fixture manifest：跨模块快照、日报、Agent summary、backtest report 必须有 fixture manifest，记录输入文件 hash、as_of、版本号。
5. Contract snapshot regression：API response envelope、Layer snapshot、notification/report JSON、Agent structured output 必须做 contract snapshot 回归。
6. 外部 I/O 全部 mock 或 fixture 化；不得在测试中真实联网。
```

新增推荐测试：

```text
test_goldenFixtureManifest_hashesMatch
test_reportGeneration_frozenClock_isDeterministic
test_agentSummary_sameInput_sameStructuredOutput
test_backtestFrozenDataset_reproducesSameMetrics
```
