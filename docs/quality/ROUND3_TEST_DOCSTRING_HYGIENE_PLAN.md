# Round 3 测试 Docstring 卫生计划（五字段 · 仓库持续规范）

> **适用范围：** 全库 `tests/**/test_*.py` 中每个 `test_*`；**新增或修改测试必须遵守**  
> **政策摘要：** `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` §7  
> **Agent skill：** `.cursor/skills/testing-guidelines/SKILL.md` §9.1  
> **CI 门禁：** `tests/test_docstring_quadruple_coverage.py`  
> **唯一金样（只读）：** `tests/test_layer3_snapshot_builder.py` 首条 `test_layer3Snapshot_buildsFromStagedLoaderAndL5_success`

## 五字段模板（缺一不可）

```python
def test_example_condition_expected() -> None:
    """覆盖范围：<业务场景，人话>
    测试对象：<被调函数或行为路径>
    目的/目标：<要证明什么事实（小白能懂）>
    验证点：<具体断言/异常；技术名可在此>
    失败含义：<挂了以后失去什么保障>
    """
```

第三行标签写 **`目的/目标：`** 或 **`目的：`**；五类信息均须齐全。

## 测试注释模板 1 — 正式提交时拉数失败不得入库

```python
    """覆盖范围：正式提交时底层拉数失败的处理——不得入库
    测试对象：commit_clean_observation_and_snapshots（fetch 被 mock 为失败）
    目的/目标：拉数失败就不能往正式观测表写任何数据，必须报错并中断整个提交
    验证点：抛出 IngestionCommitBlockedError，原因码 OBSERVATION_MAPPING；观测表仍为 0 行
    失败含义：拉数失败仍入库，脏或空数据会进入正式观测表
    """
```

**落地用例：** `tests/test_layer1_observation_ingestion.py::test_layer1Observation_fetchFailure_blocksCleanWrite`

## 测试注释模板 2 — 第三阶段只拉原始数据不写正式观测表

```python
    """覆盖范围：第三阶段「只拉原始数据」时，不得写入正式观测表
    测试对象：micro_fetch_staging
    目的/目标：staging 阶段只记拉取痕迹和 raw 文件，正式观测表（axis_observation）一行都不能多
    验证点：拉数前后观测表行数都是 0
    失败含义：第三阶段小批量拉数就写了正式观测，与第四阶段校验后再入库的设计冲突
    """
```

**落地用例：** `tests/test_layer1_observation_ingestion.py::test_layer1MicroIngestion_phase3DoesNotWriteCleanAxisObservation`

### Layer1 / 摄取类 — 覆盖范围应写清的场景

| 场景                   | 覆盖范围应说明              |
| ---------------------- | --------------------------- |
| 拉数成功               | 拉下来后日志、raw、后续步骤 |
| 拉数失败               | 不得入库、如何报错          |
| 原始文件缺失或格式不对 | 如何拒绝                    |
| 合法数据映射           | raw → 可入库观测记录        |
| 分阶段边界             | 只 staging、不写正式观测表  |

## 金样首条（通用场景参考）

```python
def test_layer3Snapshot_buildsFromStagedLoaderAndL5_success() -> None:
    """覆盖范围：用测试用的产业链数据和股价文件，在数据齐全时走正常建快照路径
    测试对象：IndustryChainSnapshotBuilder.build
    目的/目标：证明在合规测试数据下能生成至少一条带价格的行业链日快照，并正确记录 as_of 时间
    验证点：至少一条快照有 latest_price；全部 as_of_timestamp 等于入参；含 MSFT 锚点
    失败含义：正常 staged 路径建不出有价快照，说明 loader+L5 拼接主路径坏了
    """
```

**曾用错误金样：** 仅写「目的：」不写「目的/目标：」→ 批量 agent 漏字段；门禁已加 `test_docstringQuadruple_goldSampleFirstTestComplete` 防回归。

> **禁止：** `scripts/annotate_test_docstrings.py` 及任何批量替换脚本  
> **背景：** 上一轮误将 Layer1 反例当金样，全库写法跑偏；本次 R1–R7 全扫重派。

## 模板（冻结 · 五字段缺一不可）

```python
def test_example_condition_expected() -> None:
    """覆盖范围：<用通俗中文说清测哪块业务/哪条规则/哪种情况>
    测试对象：<被调函数或行为路径>
    目的/目标：<这条测要证明什么事实（小白能懂）>
    验证点：<具体断言/异常，一句；技术名可在此出现>
    失败含义：<挂了以后业务/审计会失去什么保障>
    """
```

**字段名：** 第三行标签**必须写「目的/目标：」**（禁止仅写「目的：」）；五类信息缺一不可。

### Layer1 / 摄取类测试 — 覆盖范围应写清的场景（示例）

改写时按**本条测实际断言**选填，不要套模板空话：

| 场景类型               | 覆盖范围应说明什么（人话）                   |
| ---------------------- | -------------------------------------------- |
| 拉数成功               | 数据能拉下来时，日志/raw 文件/后续步骤应怎样 |
| 拉数失败               | 拉数失败时不得入库、应报什么错               |
| 原始文件缺失或格式不对 | 缺文件、坏 JSON、字段不对时如何拒绝          |
| 合法数据映射           | 合法 raw 如何变成可写入观测表的记录          |
| 分阶段边界             | 例如「只 staging、不写正式观测表」           |

**反例：** 覆盖范围只写「Phase3 micro_fetch」或堆表名/JSON 键，小白仍不知道在测哪种情况。

## 反例（字段齐全仍不合格）

```python
# BAD — 勿模仿
目的：须导出 json/no_clean_write_proof 且 proof 显示 axis_observation 未变、fetch+1
目的：fetch FAILED 须 IngestionCommitBlockedError(OBSERVATION_MAPPING) 且无观测行
验证点：before_obs == after_obs == 0
失败含义：Phase3 Trellis 证据缺 sandbox 证明，无法 sign-off staging
```

**合格：** 目的/失败含义用业务白话；JSON 键、异常类名、pytest.raises 仅出现在验证点。

## 全扫切片 R1–R7（互斥文件 · 一 agent 一批）

| Slice | Owner       | Allowed files     | 状态                   |
| ----- | ----------- | ----------------- | ---------------------- |
| R1–R7 | agent-R1…R7 | 见 git 历史切片表 | **done（2026-06-24）** |

**Excluded：** `test_layer3_snapshot_builder.py`（金样）、`scripts/annotate_test_docstrings.py`

## 执行纪律

1. 逐条读 `test_*` 函数体与断言，再写 docstring；**不得改断言逻辑**。
2. **禁止**批量脚本；**禁止**编辑 allowed files 以外的文件。
3. 每批完成后：`uv run pytest <本批全部文件> -q`

## 验收

```bash
rg "断言/异常语义满足|回归不可被审计|可观察行为符合模块契约|关键业务断言成立" tests/
# 人工：不看函数名能否读懂目的与失败含义
```
