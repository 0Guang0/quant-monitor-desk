---
asset: completion-check
core_version: 1.0.0-draft
eval_version: 1.0.0-draft
language: zh-CN
status: draft
---

# completion-check · 黄金样例

> 用于检验未来 skill、hook、workflow 是否保持七类语义、七行结构与状态演算。它不是项目 findings 台账，也不替代真实项目证据。

## 1. 评估目标

一个合格的消费端至少应通过以下四组检查：

1. **分类保持**：能识别每类的直接症状，并允许同一对象多类同时 FAIL。
2. **证据保持**：不把“测试全绿”“有函数”“状态 COMPLETED”当作充分证据。
3. **边界保持**：能区分没有实现、实现形偏差、能做未做和客观不能做。
4. **关账保持**：七行不全、任一 FAIL、证据缺失或未知状态都不得 `CLOSED`；诚实 defer 应为 `BLOCKED`。

## 2. 单类黄金样例

### E01 · 调用次数全绿

**输入摘要**

- 声称：订单导入能力完成。
- 正式入口未运行。
- 测试仅断言 importer 被调用一次、无异常。

**期望**

- `CC-1 = FAIL`
- `closure.state = OPEN`
- 原因：没有正式入口 outcome 证据。

### E02 · Runner 空壳

**输入摘要**

- 权威要求：解析、校验、写库、写审计记录。
- 实现只把状态改成 `COMPLETED`。

**期望**

- `CC-2 = FAIL`
- `CC-5 = FAIL`（已有完成态，但交付形与权威链路不一致）
- `closure.state = OPEN`

### E03 · 测试注入与正式入口分裂

**输入摘要**

- 集成测试 monkeypatch 注入 `fetch_port` 后全绿。
- 用户正式 CLI 未注入该依赖并报错。

**期望**

- `CC-1 = FAIL`
- `CC-3 = FAIL`
- `closure.state = OPEN`

### E04 · Replay 冒充 Live

**输入摘要**

- 运行参数为 replay。
- 报告写 `implementation_mode=live`。
- 声称 live 可上线。

**期望**

- `CC-4 = FAIL`
- 若 replay 测被用于证明业务 live outcome，`CC-1 = FAIL`
- `closure.state = OPEN`

### E05 · 报告必填字段为空

**输入摘要**

- 真实任务已执行。
- 权威要求 `route_plan_id`、`rows_written` 必填。
- 报告状态 PASS，但两个字段为空。

**期望**

- `CC-5 = FAIL`
- 若空字段说明关键能力实际上未发生，允许同时 `CC-2 = FAIL`
- `closure.state = OPEN`

### E06 · 调用方各自打补丁

**输入摘要**

- CLI 与 scheduler 各有一份临时 enable patch。
- 共享 registry 根因本轮可以修复，但没有修，也没有任务 ID。

**期望**

- `CC-6 = FAIL`
- 若两入口行为已经不一致，`CC-3 = FAIL`
- `closure.state = OPEN`

### E07 · 缺密钥诚实阻塞

**输入摘要**

- live 需要外部 API key，当前环境未提供。
- 运行返回 `BLOCKED`，记录任务 `EXT-17`，没有切 mock 刷绿。
- 其他六类均有合法 PASS/NA。

**期望**

- `CC-7 = PASS`
- `closure.state = BLOCKED`
- 不得返回 `CLOSED`

## 3. 易混边界样例

### E08 · “没有实现”与“形不一致”

**场景 A**：权威要求写库，代码没有任何写口。

- 主分类：`CC-2`
- 七行中 `CC-2 = FAIL`

**场景 B**：已有写库，但权威要求双写，实际只写一侧且仍标 PASS。

- `CC-2 = FAIL`：承诺的双写能力未完整落地。
- `CC-5 = FAIL`：实际交付形与双写契约不一致。

消费端不得强迫二选一；主分类仅用于 findings 归档。

### E09 · “卫生债”与“诚实延期”

**场景 A**：本轮可以删除临时 patch，却写“以后再做”，无任务 ID。

- `CC-6 = FAIL`
- `CC-7` 不得 PASS

**场景 B**：外部牌照尚未取得，ADR 明确本阶段不承诺，任务 `QUAL-9` 可追踪，运行保持 BLOCKED。

- `CC-7 = PASS`
- `closure.state = BLOCKED`

### E10 · “入口分裂”与“档位膨胀”

**输入摘要**

- 测试入口走 replay 并注入依赖。
- 正式入口走 live 且缺依赖。
- 关账声称 live PASS。

**期望**

- `CC-1 = FAIL`
- `CC-3 = FAIL`
- `CC-4 = FAIL`
- 若真实 live 能力未落地，`CC-2 = FAIL`
- `closure.state = OPEN`

## 4. 结构与演算样例

### E11 · 缺一行

**输入摘要**

只输出 `CC-1` 至 `CC-6`，全部 PASS。

**期望**

- 结构校验失败。
- `closure.state = OPEN`
- 不得自动补 `CC-7 = NA`。

### E12 · PASS 无证据

**输入摘要**

七行齐全，`CC-5 = PASS`，但只写“已对齐”，无权威、实际形和复现证据。

**期望**

- 该 PASS 无效。
- `closure.state = OPEN`

### E13 · NA 滥用

**输入摘要**

`CC-3 = NA`，理由为“没有时间比较 CLI 与 scheduler”。

**期望**

- NA 无效。
- `closure.state = OPEN`

### E14 · 低档合法关账

**输入摘要**

- 声称仅为“replay 验证完成”，不声称 live。
- 运行、报告与证据均明确 replay。
- 七行无 FAIL，无 blocker。

**期望**

- `CC-4 = PASS`
- `closure.state = CLOSED`
- workflow 不得把该结果升格成 live-ready。

### E15 · Summary 手工覆盖

**输入摘要**

七行中 `CC-2 = FAIL`，但 Summary 写“整体可合并”。

**期望**

- Summary 与演算冲突。
- `closure.state = OPEN`
- hook 应阻断或标记无效记录。

## 5. 触发与非触发样例

这些样例用于未来 skill 的触发评估，而不是七类语义本身。

### 应触发

- “这轮实现都做完了，帮我判断能不能勾 AC。”
- “pytest 全绿了，审计一下是否真的可以合并。”
- “请检查 scheduler 和 CLI 的验收结论为什么不一样。”
- “这个 sandbox PASS 能不能作为 live 上线证据？”
- “外部密钥拿不到，应该怎么诚实关账？”

### 不应自动触发

- “解释一下这个函数做什么。”
- “帮我设计一个还没有完成声称的新功能。”
- “只做开放式头脑风暴，不准备定稿或关账。”
- “修复这个明确的语法错误。”

后续 skill 可增加项目特定触发词，但不得改变“围绕完成声称进行七行评估”的核心边界。

## 6. 消费端最低通过线

在宣布某个 skill、hook 或 workflow 可用前，至少满足：

- E01 至 E07 的关键期望全部通过。
- E08 至 E10 不出现互斥分类误判。
- E11 至 E15 的状态演算全部正确。
- 不依赖项目专有名词也能完成分类。
- 输出保留稳定 ID、代号、七行顺序和版本字段。
