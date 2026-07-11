---
asset: completion-check
contract_version: 1.0.0-draft
language: zh-CN
status: draft
---

# completion-check · 消费契约

> 本文件定义 skill、hook、workflow 与人工审计如何向核心语义提供输入、接收七行输出并计算对象状态。分类语义以 `REFERENCE.md` 为准。

## 1. 输入契约

每个评估对象至少提供：

| 字段                  | 必填     | 含义                                                    |
| --------------------- | -------- | ------------------------------------------------------- |
| `object_id`           | 是       | 稳定对象标识；一个 AC、Slice、任务或交付物一个 ID       |
| `claim`               | 是       | 本次完成声称，例如“实现完成”“可合并”“可上线”            |
| `authority_refs`      | 是       | 计划、设计、契约、决议或用户要求的引用列表              |
| `official_entrypoint` | 条件必填 | 用户实际会走的正式入口；有运行行为时必填                |
| `claimed_mode`        | 条件必填 | 声称对应的 live/replay/dry-run/sandbox/stub 等档位      |
| `runtime_state`       | 是       | `READY / BLOCKED / FAIL_EXTERNAL / DEFERRED / UNKNOWN`  |
| `evidence_sources`    | 是       | 可读取的代码、报告、日志、DB、文件、测试与复现命令      |
| `defer_ref`           | 条件必填 | `runtime_state` 非 `READY` 时的任务 ID、ADR、台账或决议 |

对象、声称或权威不明确时，消费端必须返回 `OPEN`，不得猜测后关账。

## 2. 七行输出契约

每个对象必须按 `CC-1` 至 `CC-7` 顺序输出七条记录。

```yaml
asset_version: 1.0.0-draft
contract_version: 1.0.0-draft
object:
  id: OBJ-001
  claim: 可合并
  authority_refs:
    - task_plan.md#AC-3
  official_entrypoint: app command --run
  claimed_mode: live
  runtime_state: READY
  defer_ref: null
checks:
  - id: CC-1
    code: false-green
    verdict: PASS
    observed: 正式入口运行后报告 rows_written=12
    authority: task_plan.md#AC-3
    evidence:
      - type: command
        ref: app command --run --mode live
        reproduction: 在目标环境执行并保存报告 JSON
      - type: test
        ref: tests/test_acceptance.py::test_live_writes_rows
        reproduction: 运行该测试并核对 rows_written 精确值
    gap: null
  # CC-2 ... CC-7，顺序固定
closure:
  state: CLOSED
  failed_checks: []
  blockers: []
  summary: 七行齐全、无 FAIL、无有效 blocker，允许关账。
```

## 3. 稳定字段

| 字段        | 规则                                             |
| ----------- | ------------------------------------------------ |
| `id`        | 只能是 `CC-1` 至 `CC-7`                          |
| `code`      | 必须与 `REFERENCE.md` 的英文代号一致             |
| `verdict`   | 只能是 `PASS / FAIL / NA`                        |
| `observed`  | 可感知运行或交付事实；不得只写“测试全绿”“已完成” |
| `authority` | 该行对照的权威；无独立权威时引用对象级权威       |
| `evidence`  | 文件、命令、测试、报告、DB 或决议的可复现引用    |
| `gap`       | `FAIL` 时必填；写缺口与影响，不能只写“未通过”    |

## 4. 证据规则

### PASS

`PASS` 必须同时满足：

1. `observed` 非空，描述一条运行或交付事实。
2. `authority` 非空。
3. 至少一条 `evidence` 可独立复现或核对。
4. 证据直接支持本类拷问，不用另一类结论代替。

### FAIL

`FAIL` 必须同时满足：

1. 写明观察到的违反事实。
2. `gap` 写明缺什么、为何影响完成声称。
3. 至少一条证据定位缺口；无法运行时说明限制与替代核对方式。

### NA

`NA` 必须同时满足：

1. `observed` 使用 `NA：<客观原因>`。
2. `evidence` 至少包含一条支持“不适用”的对象边界说明。
3. 未检查、未知、没时间、无环境均不能写成 `NA`。

## 5. 状态演算

按以下顺序计算对象状态：

```text
若缺少 CC-1..CC-7 任一行                         -> OPEN
否则若任一行 FAIL                               -> OPEN
否则若任一 PASS 缺 observed/authority/evidence  -> OPEN
否则若任一 NA 缺客观原因                        -> OPEN
否则若 runtime_state 属于 BLOCKED/FAIL_EXTERNAL/DEFERRED：
    若 CC-7 = PASS 且 defer_ref 可追踪            -> BLOCKED
    否则                                          -> OPEN
否则若 runtime_state = UNKNOWN                    -> OPEN
否则                                              -> CLOSED
```

补充规则：

- `CC-7 PASS` 不覆盖其他类的 `FAIL`。
- 低档运行可以得到对应低档的 `CLOSED`，但不得被 workflow 升格为更高档声称。
- `Summary` 只能由七行和运行状态推导，不得手工覆盖演算结果。

## 6. Markdown 人工记录模板

```markdown
# completion-check

- 核心版本：1.0.0-draft
- 对象：<object_id>
- 声称：<claim>
- 权威：<authority refs>
- 正式入口：<entrypoint | NA>
- 声称档位：<mode | NA>
- 运行状态：<READY | BLOCKED | FAIL_EXTERNAL | DEFERRED | UNKNOWN>
- Defer：<task/ADR/ledger id | NA>

| ID   | 分类                    | 判定         | 观察事实 | 权威 | 证据 | 缺口 |
| ---- | ----------------------- | ------------ | -------- | ---- | ---- | ---- |
| CC-1 | 假绿 false-green        | PASS/FAIL/NA | ...      | ...  | ...  | ...  |
| CC-2 | 半成品 shell-done       | PASS/FAIL/NA | ...      | ...  | ...  | ...  |
| CC-3 | 入口分裂 entry-split    | PASS/FAIL/NA | ...      | ...  | ...  | ...  |
| CC-4 | 档位膨胀 mode-inflation | PASS/FAIL/NA | ...      | ...  | ...  | ...  |
| CC-5 | 交付偏航 delivery-drift | PASS/FAIL/NA | ...      | ...  | ...  | ...  |
| CC-6 | 卫生债 hygiene-debt     | PASS/FAIL/NA | ...      | ...  | ...  | ...  |
| CC-7 | 诚实延期 honest-defer   | PASS/FAIL/NA | ...      | ...  | ...  | ...  |

## Closure

- 状态：CLOSED / OPEN / BLOCKED
- FAIL：<IDs 或无>
- Blocker：<列表或无>
- Summary：<由七行推导的结论>
```

## 7. 消费端职责边界

### Skill

负责：读取语义、收集上下文、生成七行、解释证据缺口。

不得：复制并维护第二套七类定义；用模型自由发挥改写稳定 ID 或代号。

### Hook

负责：结构校验、缺行检查、字段合法性、状态演算和阻断。

不得：仅凭关键词自动判定复杂语义；自动把未知写成 PASS/NA。

### Workflow

负责：定义何时收集输入、何时运行检查、哪个状态允许进入下一阶段。

不得：把角色、文件路径或阶段编排写回语义核心。

### 人工审计

负责：独立复现证据、给出审计七行和状态。

不得：抄执行者表或把执行者结论当证据。

## 8. 兼容与版本

- 增加可选字段：契约小版本升级。
- 改字段含义、状态演算、稳定 ID 或必填规则：契约大版本升级。
- 消费端输出必须记录 `asset_version` 与 `contract_version`。
- 版本不兼容时返回 `OPEN`，不得静默降级。
