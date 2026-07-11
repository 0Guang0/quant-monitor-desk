# completion-check · project（蒸馏溯源）

> **本文件：** `quant-monitor-desk` **长期蒸馏记录**；**不**复制 [REFERENCE.md](C:/Users/Guang/Desktop/completion-check/REFERENCE.md) 七类正文。  
> **判定权威：** REFERENCE（通用场景 + 关账必问 + 场景边界）。

---

## 列含义

| 列           | 含义                                                                                                                                                                                                                 |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **模式**     | 本仓库内**可复用**的同类问题昵称：比通用问题具体（可用 `AcceptanceReport`、`matrix/binding`、`fetch_port` 等项目词汇），比单次案情抽象（不写票号、不复述一整段案情）。**一行应对准可多次再犯的一类**，不是一事一态。 |
| **分类**     | completion-check 七类；**不等于**模式，**不等于**通用问题。                                                                                                                                                          |
| **通用问题** | **跨项目抽象举例**：`标题 — 症状`；不出现本仓库专有架构词（调度层、信封、`COMPLETED`、matrix/binding 等）。多行**模式**可共享同一通用问题。                                                                          |
| **次数**     | 本仓库内，**同一模式再次被犯下**的次数（见下）；**不是**文件里出现过几次，**不是** grep 命中数，**不是**溯源列列了几条路径。                                                                                         |
| **溯源**     | 曾犯下或审计确认该模式的证据路径（可多条）；**不是**模式名的一部分。                                                                                                                                                 |

### `次数` 怎么 +1

满足**全部**才 +1：

1. 语义上属于表中已有 **模式**（不是「又在某文件里看到类似字眼」）；
2. 在**新一轮实现 / 切片 / 关账声称**中，**再次犯下**该类错误（或修复后**再次引入**），经审计或关账自检确认。

以下**不** +1：仅在 findings/audit 里被**记述**、代码里仍有历史残留但未新犯、同一轮里多文件指向同一次犯错、严格文本匹配到的重复引用。

首犯：`次数 = 1`，记 `首见` / `末见`。再犯：同模式行 `次数 +1`，更新 `末见`，溯源可补**新一次**犯错的锚点。

---

## 维护规则

1. **一行 = 一个项目内模式**（语义去重键；**不等于**分类，**不等于** REFERENCE 某条举例原文）。
2. **新犯错**且语义合于已有模式 → 只 +`次数`、更新 `末见`、溯源补该次锚点。
3. **新犯错**但语义上新类型 → **新起一行**（即使 `通用问题` 与别行相同）。
4. **`通用问题`** 保持跨项目抽象；**模式** 用项目内可复用昵称聚合同类犯法语，不把单次案情或 REFERENCE 举例原文当模式名。
5. 积累够了再从 `通用问题` 池归纳改 REFERENCE 举例；不反向绑死。

---

## 索引（一行一模式）

| 模式                         | 分类               | 次数 | 首见    | 末见       | 溯源                                                                               | 通用问题                                                                                                                |
| ---------------------------- | ------------------ | ---- | ------- | ---------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| G1 call-count 门             | 1 · false-green    | 2    | 2026-03 | 2026-06    | `Findings.txt` §A；`review-commercial-01.txt`                                      | Vacuous outcome — 只断言 True、无异常、非空或调用次数，未核对 DB、报告字段等业务 outcome；底层坏了仍可能全绿。          |
| catalog 元测不跑运行时       | 1 · false-green    | 1    | 2026-03 | 2026-03    | `review-commercial-01.txt`                                                         | Artifact-guard — 测 catalog / 文档措辞 / 源码枚举 / 文件在不在，不测运行时行为；生产回归不会红。                        |
| 测注入正门分裂               | 1 · false-green    | 2    | 2026-03 | 2026-06    | `Findings.txt` §B；`task-02/.../findings.md`                                       | 测专属注入 — 集成或 @live 测靠 monkeypatch 注入依赖，正式入口无同等待遇；测试绿 ≠ 正式命令能跑。                        |
| 调度层合成 PASS 信封         | 1 · false-green    | 1    | 2026-06 | 2026-06    | `task-02/task_plan.md` Slice 2a-0                                                  | 手工拼装通过态 — 子步骤未产出可独立核对的验收结果，父流程仍用手工状态或占位字段使关账 / 套件变绿。                      |
| 放宽断言缩验证               | 1 · false-green    | 1    | 2026-06 | 2026-06    | `task-01.5/.../findings.md`                                                        | 改测试目的缩验证 — 为过关放宽断言、用不等式代替精确值、删失败分支，或占位测永不执行生产路径。                           |
| 质检 runner 空壳             | 2 · shell-done     | 1    | 2026-06 | 2026-06    | `task-02/.../findings.md` F-08/F-09                                                | 成品链路空壳 — 权威要求的校验 / 比对 / 回填 / 写库等完整链路未实现，runner 仅转状态或计数即过关。                       |
| 子报告空壳标完成             | 2 · shell-done     | 1    | 2026-06 | 2026-06    | `task-02/findings.md` V1                                                           | 权威未落地 — plan 要求的能力 / 报告 / 链路仅有壳或占位，却被当作已完成。                                                |
| 决议已关台账仍待实现         | 2 · shell-done     | 3    | 2026-06 | 2026-07-10 | `task-02/findings.md` §6.5；F-15；**F-01/F-03 复核重开**                           | 决议关闭 ≠ 实现完成 — 决议 / OQ / ADR 已拍板纳入后续，台账或口头关账却被当成代码已做完。                                |
| 契约双写单侧                 | 2 · shell-done     | 1    | 2026-07 | 2026-07    | `task-02/task_plan.md` AD-9                                                        | 契约双写缺一 — 权威要求多路落盘，实现只有单侧写口、缺迁移，或两侧不同步。                                               |
| 库内可测正门未接             | 2 · shell-done     | 2    | 2026-03 | 2026-07    | `Findings.txt` §B；`findings.md` F-07/F-14                                         | 库内有正门无 — 能力已在库内可测，用户会走的正式入口未接同一套接线，正门得不到同等能力。                                 |
| matrix / binding 启用双轨    | 3 · entry-split    | 1    | 2026-06 | 2026-06    | `task-02/findings.md` F-07/F-14                                                    | 双入口行为不一致 — 同一能力经不同正式入口行为不同，同参两路结论不一。                                                   |
| 测里 patch enable 源         | 3 · entry-split    | 1    | 2026-06 | 2026-06    | `review-commercial-03.txt`                                                         | 测试配置与生产默认不一致 — 测试里临时打开开关或注入配置后通过，生产默认仍关，同参两路结论不同。                         |
| scheduler 测彩排链           | 3 · entry-split    | 1    | 2026-06 | 2026-06    | `review-commercial-03.txt`                                                         | 彩排链与真链未同测 — 测试只走彩排 / mock 路径，正式运行仍走未覆盖的真链接缝。                                           |
| 并行验收轨分叉               | 3 · entry-split    | 1    | 2026-06 | 2026-06    | `task-01/.../findings.md` Slice 7                                                  | 并行验收缝误判 — 旧 helper / smoke 一路 PASS，权威验收规则或正式入口同能力尚未按同一规则验收。                          |
| replay 轨关账标 live         | 4 · mode-inflation | 1    | 2026-03 | 2026-03    | `Findings.txt` §C；`task-02/findings.md` F-11                                      | 低档运行写入高档关账 — 默认测试 / CI 走低档回放轨，关账声称却为 live-ready 或等价高档。                                 |
| 档位字段与证据分裂           | 4 · mode-inflation | 1    | 2026-06 | 2026-06    | `task-01/findings.md` Phase 17–19                                                  | 关账档位与产出证据不一致 — 报告标高档 PASS，证据字段却含 replay / mock / stub 痕迹。                                    |
| sandbox DONE 标 live primary | 4 · mode-inflation | 1    | 2026-06 | 2026-06    | `task-01.5/findings.md` FIND-C-01                                                  | 隔离环境 DONE 冒充生产主路径 — 隔离 / 彩排环境验收 DONE 被当作生产主路径闭环证据，未标注 rehearsal 或 degraded。        |
| dry_run closure 升 live 授权 | 4 · mode-inflation | 1    | 2026-06 | 2026-06    | `task-01/findings.md` Phase 15                                                     | 彩排 closure 冒充生产授权 — 彩排 / 演练模式下的 PASS 被未标注地用于生产授权关账。                                       |
| 默认 mock 产出标 live        | 4 · mode-inflation | 1    | 2026-06 | 2026-06    | `review-commercial-08.txt`                                                         | 默认低档产出标高档 — 工厂 / CLI 默认 mock 或低档，产出字段仍标 live 或等价高档。                                        |
| 金路径后段缩水               | 5 · delivery-drift | 1    | 2026-06 | 2026-06    | `task-02/task_plan.md`；`findings.md` F-06/F-08                                    | 步骤链缩水 — 权威要求完整步骤链（含后段比对 / 持久化 / 触发等），job 已 COMPLETED，实质仍只走短链，后段无证据。         |
| 可观测必填空值过关           | 5 · delivery-drift | 2    | 2026-03 | 2026-07-10 | `Findings.txt` §B；`PHASE1_PRD.md` R4；**F-03 复核重开**                           | 必填契约项空缺 — 已标 PASS / COMPLETED，但报告 / 信封缺契约必填项，或键在、值为空。                                     |
| 验收信封形偏过关             | 5 · delivery-drift | 1    | 2026-06 | 2026-06    | `task-02/task_plan.md` Slice 2a-0                                                  | 完成态与契约形不一致 — 已有 PASS / COMPLETED，但产出形与契约要求的字段 / 结构不符。                                     |
| 多入口 closure 形分裂        | 5 · delivery-drift | 1    | 2026-06 | 2026-06    | `findings.md` F-07；`review-commercial-02.txt`                                     | 多正式入口产出形分裂 — 同源能力在不同入口走不同规则或产出形状，一处已对齐、另一处仍偏，且无书面变更。                   |
| 勾 AC 形未对齐               | 5 · delivery-drift | 2    | 2026-06 | 2026-07    | `task-02/findings.md` §6.5；`task-01` 未勾 AC                                      | 勾 checkbox 形未对齐 — AC / OQ 已关，实现形仍与清单或契约要求不一致。                                                   |
| sys.path 绕路台账 OPEN       | 6 · hygiene-debt   | 1    | 2026-03 | 2026-03    | `Findings.txt` §E；`AUDIT_DEFERRED_REGISTRY` D7-P2-2                               | 脚本 import 绕路 — 不靠 packaging / 标准入口，手改 import 路径才能跑；台账仍 OPEN 却当已清。                            |
| autouse 放宽 guard 无台账    | 6 · hygiene-debt   | 1    | 2026-06 | 2026-06    | `task-01.5/findings.md` §9                                                         | 临时放宽无删除条件 — 全局 autouse 或临时扩大可选集合过关，无 open 台账、owner 与删除条件。                              |
| enable 接缝调用方补丁        | 6 · hygiene-debt   | 1    | 2026-06 | 2026-06    | `findings.md` F-07/F-14                                                            | 调用方补丁绕过共享根因 — 共享接缝一处未修，各正式入口 / 测试各打一条补丁。                                              |
| registry 多套并行漂移        | 6 · hygiene-debt   | 1    | 2026-06 | 2026-06    | `Findings.txt` §E；`task-01.5/findings.md`                                         | SSOT 多份并行漂移 — 多套枚举或措辞各维护一份，改一处不跟，仍标已对齐。                                                  |
| 假外置无任务 ID              | 6 · hygiene-debt   | 1    | 2026-06 | 2026-06    | `task-01.5/findings.md` FIND-E-01/E-02                                             | 假外置缺任务 ID — 本关能修却写「下阶段 / 后续」，未登记待修复清单或 roadmap 条目。                                      |
| bootstrap 双份接缝           | 6 · hygiene-debt   | 1    | 2026-06 | 2026-06    | `review-commercial-02.txt`                                                         | 双份初始化逻辑并存 — 同一接缝两套启动 / bootstrap 逻辑不合并。                                                          |
| 里程碑代号拖延 rename        | 6 · hygiene-debt   | 1    | 2026-07 | 2026-07-10 | `task-02/task_plan.md`；**AUD-DOUBT-12 已关**                                      | 误导性命名拖延正名 — 正式代码仍用里程碑代号，推迟 rename 叠新功能。                                                     |
| 缺密钥 mock 刷 live          | 7 · honest-defer   | 1    | 2026-06 | 2026-06    | `task-01/findings.md`                                                              | 缺密钥诚实关闸 — 缺必需密钥 / 授权时应 BLOCKED，禁止 mock / replay 把行刷绿。                                           |
| 上游失败 replay 刷绿         | 7 · honest-defer   | 1    | 2026-06 | 2026-06    | `task-01/findings.md`                                                              | 上游客观失败登记延期 — 外部依赖客观失败应 FAIL_EXTERNAL + deferred，禁止 mock / replay 冒充 PASS。                      |
| 资格缺失 stub 刷 PASS        | 7 · honest-defer   | 1    | 2026-06 | 2026-06    | `task-01/findings.md`；ADR-016                                                     | 资格缺失应 defer — 缺本地终端 / 牌照等本阶段未承诺解决的依赖，预期 BLOCKED + deferred，禁止占位刷 PASS。                |
| validation 源升格 Primary    | 7 · honest-defer   | 1    | 2026-06 | 2026-06    | `task-02/findings.md` F-17/AD-10                                                   | validation-only 禁升格 — 只应 degraded / blocked 的源，禁止批量开闸或 staged DONE 顶替生产主路径。                      |
| synthetic PASS 替书面 defer  | 7 · honest-defer   | 1    | 2026-06 | 2026-06    | `task-02/task_plan.md`                                                             | 未承诺阶段书面 defer — plan 未纳入的阶段须 defer 至可追踪任务 ID 并保留阻塞态，禁止 synthetic PASS 或口头等同实现完成。 |
| judgment 字段偏薄            | 5 · delivery-drift | 1    | 2026-06 | 2026-06    | `D:/五层模型数据分析/task-01-.../findings.md`                                      | 可行动字段偏薄 — 产出格式过关，缺可独立核对的判断 / 行动字段。                                                          |
| fallback 参数仅测不接 fetch  | 2 · shell-done     | 1    | 2026-07 | 2026-07    | `completion-check-audit-layer1-modules.md` §9.1；`backend/` 无 `use_fallback=True` | 库内有正门无 — 能力已在库内可测，用户会走的正式入口未接同一套接线，正门得不到同等能力。                                 |

---

## 难例裁决（单行，不堆叠）

| 症状简写                  | 分类   | 非  | 依据                                                 |
| ------------------------- | ------ | --- | ---------------------------------------------------- |
| 合成 PASS 信封            | 2 或 5 | 1   | 无真实能力 → **2**；有 COMPLETED 形不对 → **5**      |
| matrix / binding 启用不一 | 3 或 6 | 2   | 两入口行为不一 → **3**；共享未修、各处 patch → **6** |
| sandbox DONE 写 live 关账 | 4 或 7 | —   | 档位标错 → **4**；validation 应关闸 → **7**          |

---

**Last updated:** 2026-07-10 晚（AUD-DOUBT-12 关账 · task-01.5→task-02 §7 迁入 · F-01/F-03 复核重开）
