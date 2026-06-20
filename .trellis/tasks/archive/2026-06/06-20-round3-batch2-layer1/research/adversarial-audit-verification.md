# 对抗性审计核实与修补记录 — Round 3 Batch 2

> 2026-06-20 · Composer 2.5 Agent1（上下文）+ Agent2（协议）；主会话逐项核实后修补

## Agent 1 上下文项（F-01–F-22）

| ID   | 发现                               | 核实                         | 处置                                                              |
| ---- | ---------------------------------- | ---------------------------- | ----------------------------------------------------------------- |
| F-01 | 五轴 indicator_spec 未入 implement | **确认**                     | implement 追加 5 个 YAML                                          |
| F-02 | engineering_rules 未入 manifest    | **确认**                     | implement 追加 5 个 engineering_rules                             |
| F-03 | SHADOW 三名测试缺失                | **确认**                     | MASTER §8.2 RED + AC-017-6                                        |
| F-04 | module §13 多项未映射              | **确认**                     | 增 AC-017-8,018-5,018-6 等 + §8.2–8.4 测试                        |
| F-05 | lineage 无持久化模型               | **确认**                     | migration `axis_snapshot_lineage` + §3.4                          |
| F-06 | AxisEngineeringGuardrail 缺失      | **确认**                     | `guardrails.py` + AC-017-7                                        |
| F-07 | WriteManager 无 §8 步骤            | **确认**                     | AC-WRIT-1 + §8.5 + validation_gate 入 manifest                    |
| F-08 | ResourceGuard 缺口                 | **确认**                     | AC-RES-1 + resource_guard 入 manifest                             |
| F-09 | AC-018-1 字段过 vague              | **确认**                     | 展开 module §7.1 全字段列表                                       |
| F-10 | user_guide 未入 manifest           | **确认**                     | implement 追加 5 个 user_guide                                    |
| F-11 | module §5.3 超集字段               | **确认**                     | AC-017-2 扩展 + `test_axisSpecLoader_missingQualityRules_rejects` |
| F-12 | lineage 字段列表不完整             | **确认**                     | §3.4 完整复制 contract                                            |
| F-13 | deterministic_rebuild 未测         | **确认**                     | AC-LINEAGE-4 + 测试名                                             |
| F-14 | 017 §5 架构 1-hop 缺失             | **确认**                     | §0.6 + implement 追加 03/04/final_package                         |
| F-15 | 018 输入缺 axis contract           | **确认**                     | §13 注明借用 017 输入                                             |
| F-16 | staged vs Tier B                   | **确认**                     | §10 加注 backend 分层 vs 批次加固                                 |
| F-17 | audit.jsonl 过薄                   | **确认**                     | 扩充至 12+ 条                                                     |
| F-18 | integration-audit 过早 PASS        | **确认**                     | 重写后 closure PASS（修补后）                                     |
| F-19 | 批次范围                           | 核实通过                     | 保持                                                              |
| F-20 | 路径纠偏                           | 核实通过                     | 保持                                                              |
| F-21 | 主契约入 manifest                  | 核实通过                     | 保持                                                              |
| F-22 | lineage 消费者锚点                 | 核实通过；结合 F-05 补持久化 | 已修补                                                            |

## Agent 2 协议项（A2-01–A2-22）

| ID    | 发现                               | 核实       | 处置                                       |
| ----- | ---------------------------------- | ---------- | ------------------------------------------ |
| A2-01 | 缺 adversarial-audit-verification  | **确认**   | 本文件                                     |
| A2-02 | AUDIT §2 不完整                    | **确认**   | 补 A5 prod-path + 证据抽检 + A6/A7/A8 双行 |
| A2-03 | A6 无命令                          | **确认**   | §2 填 fixture 500 perf 命令                |
| A2-04 | to-issues 无产出                   | **确认**   | `research/vertical-slices.md`              |
| A2-05 | 五轴 YAML manifest                 | 同 F-01    | 已修补                                     |
| A2-06 | §13 未映射                         | 同 F-04    | 已修补                                     |
| A2-07 | plan.freeze 压缩                   | **确认**   | 补 §3.0/§3.0a/§3.7 对抗轮次                |
| A2-08 | §12 verification-before-completion | **确认**   | 改「不用」；仅 Audit A5                    |
| A2-09 | 缺 \*-tests.md                     | **确认**   | 三份 research 测试设计                     |
| A2-10 | AC-018-1 vague                     | 同 F-09    | 已修补                                     |
| A2-11 | WriteManager 模糊                  | 同 F-07    | AC-WRIT-1                                  |
| A2-12 | predecessor_tasks 缺               | **确认**   | task.json 追加                             |
| A2-13 | R2.6 gate pointer                  | **确认**   | implement 追加两 gate audit.report         |
| A2-14 | staged_acceptance 未入 manifest    | **确认**   | implement 追加                             |
| A2-15 | 017 §5 架构未追溯                  | 同 F-14    | 已修补                                     |
| A2-16 | audit.jsonl 薄                     | 同 F-17    | 已扩充                                     |
| A2-17 | plan-manifest-audit stub           | **确认**   | 扩充                                       |
| A2-18 | ResourceGuard                      | 同 F-08    | AC-RES-1                                   |
| A2-19 | 用户批准未勾                       | **已闭合** | plan.freeze §5 已勾选；`task.py start`     |
| A2-20 | 薄索引合格                         | 通过       | 保持                                       |
| A2-21 | DECISIONS 不存在                   | 可接受     | original-plan-trace 保持                   |
| A2-22 | Tier C N/A                         | 可接受     | AUDIT A5 prod-path 覆盖 data 副本          |

## 验证

修补后：`python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-20-round3-batch2-layer1` → 须 exit 0。
