# 执行索引 — R3H-08 Live Productization（Plan v4.1）

> Execute 读 `research/00-EXECUTION-ENTRY.md`

## 0. 冻结元数据

| 字段          | 值                                                            |
| ------------- | ------------------------------------------------------------- |
| slug          | `06-29-round3h-r3h08-live-productization`                     |
| protocol      | `4.1`                                                         |
| execute_entry | `research/00-EXECUTION-ENTRY.md`                              |
| source_card   | `docs/implementation_tasks/.../R3H_08_LIVE_PRODUCTIZATION.md` |
| blocked_by    | R3H-10 + R3H-07 CLOSED                                        |

## 1. 步骤与证据（Execute）

| Step | 切片        | 完成  |
| ---- | ----------- | ----- |
| 9.0  | S08-BOOT    | `[x]` |
| 9.1  | S08-01 08C  | `[x]` |
| 9.2  | S08-02 08A  | `[x]` |
| 9.3  | S08-03 08B  | `[x]` |
| 9.4  | S08-04 08D  | `[x]` |
| 9.5  | S08-05 横切 | `[x]` |

切片 AC SSOT：`research/to-issues-slices.md`

## 2. AC ↔ 测试

| AC                      | 验证                                                                    | 切片       |
| ----------------------- | ----------------------------------------------------------------------- | ---------- |
| LIVE-PROD-24            | registry + pytest                                                       | CLOSE      |
| Tier A/B/C              | per-source 契约测                                                       | S08-01..04 |
| 无 rehearsal 冒充       | policy 测                                                               | 全轨       |
| reconcile/probe service | sync/probe 测                                                           | S08-05     |
| **Execute 双铁律 A+B**  | `execute-parity-contract.md`；主会话同流程 + §7/§D 参考源码 Read + cite | 全切片     |

## 3. 必须读原文

见 `research/EXTERNAL-INDEX.md` §A

## 4. 已并入冻结任务卡

| 来源 | 摘要                       |
| ---- | -------------------------- |
| 活卡 | R3H-08 Wave 2 LIVE-PROD-24 |

## 5. Audit 追溯集

`frozen/R3H_08_LIVE_PRODUCTIZATION.md` · ENTRY · to-issues-slices
