# Integration Audit — R3FR-03 (Phase 5d / doubt-driven-development)

## 1. doc-gap

| 检查                                               | 结果                                                  |
| -------------------------------------------------- | ----------------------------------------------------- |
| 任务卡 §4 目标文件 → `EXECUTION_INDEX` §0.1 / §1   | PASS                                                  |
| 任务卡 §5 caps → `plan-boot.md` + frozen §7        | PASS（注：现行代码 10→3 须在 Execute 对齐）           |
| 任务卡 §6 验收 → `EXECUTION_INDEX` §2 / §2.1       | PASS                                                  |
| Batch README 执行顺序（R3FR-03 after data health） | PASS（前置 R3FR-02/06 已归档绿）                      |
| Playbook 文件锁 → `integration-ledger.md`          | PASS                                                  |
| `context_pack.json` 空 modules                     | **WARN** — Execute Boot 依赖 §3 manifest；非阻塞 Plan |

## 2. 六类关键信息

| 类别         | ledger/implement                   | frozen/索引归并 | 缺口           |
| ------------ | ---------------------------------- | --------------- | -------------- |
| decision     | Batch 3F-R posture                 | frozen §8       | 无             |
| contract     | fetch_port, guardrails, registry   | §3 manifest     | 无             |
| business     | R3FR-03 任务卡                     | frozen §1–§2    | 无             |
| architecture | fetch_ports/normalizers 新边界     | frozen §5       | Execute 待建   |
| rule         | GLOBAL, reference guardrails       | §3              | 无             |
| wiring       | tdx_manual_probe, gate, probe port | §9 步骤         | Execute 待实现 |

## 3. adversarial

| 攻击面                                        | 处置                                              |
| --------------------------------------------- | ------------------------------------------------- |
| 在 `TdxPytdxProbeFetchPort` 继续堆 downloader | §9.5 编排瘦身 + forbidden 语义                    |
| 无授权 live 联网                              | §9.4 + `test_tdx_live_manual_probe_authorization` |
| 参考项目 runtime import                       | §9.7 + `test_reference_adoption_guardrails`       |
| 单 PR 水平实现七切片                          | `vertical-slices.md` TDX-R3FR-01..07 逐步         |
| scope creep 到 data health                    | grill Q5 + ledger OUT                             |
| caps 弱化测试目的通过                         | 只改数值不改 purpose（integration-audit D3）      |

## 4. closure

**integration-audit: PASS**（对抗性 Plan 审计 2026-06-26；ADV-01..25 主会话已闭合）

## 5. plan-manifest-audit

| 检查                 | implement                                        | audit                | check  |
| -------------------- | ------------------------------------------------ | -------------------- | ------ |
| §3 manifest 路径     | 已扩 §3 + regenerate                             | Trace Authority 完整 | 已生成 |
| validate-plan-freeze | exit 0（修复后复验）                             | —                    | —      |
| adversarial audit    | `research/adversarial-plan-audit.report.md` PASS | —                    | —      |
