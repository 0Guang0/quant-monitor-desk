# 执行索引 — R3H-10 DataSourceService SSOT（Plan v4.1）

> P0i：索引完整 · Execute 读 `research/00-EXECUTION-ENTRY.md`

## 0. 冻结元数据

| 字段          | 值                                                                                                                                   |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| slug          | `06-29-round3h-r3h10-datasource-service-ssot`                                                                                        |
| protocol      | `4.1`                                                                                                                                |
| execute_entry | `research/00-EXECUTION-ENTRY.md`                                                                                                     |
| source_card   | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_10_DATASOURCE_SERVICE_SSOT.md` |
| frozen_card   | `frozen/R3H_10_DATASOURCE_SERVICE_SSOT.md`                                                                                           |

## 1. 步骤与证据（Execute）

| Step | 切片     | RED 命令                    | GREEN 命令 | 证据路径                               |
| ---- | -------- | --------------------------- | ---------- | -------------------------------------- |
| 9.0  | S10-BOOT | 见 `to-issues-slices.md` §2 | 见切片     | `execute-evidence/9.0-{red,green}.txt` |
| 9.1  | S10-01   | 见切片                      | 见切片     | `execute-evidence/9.1-{red,green}.txt` |
| 9.2  | S10-02   | 见切片                      | 见切片     | `execute-evidence/9.2-{red,green}.txt` |
| 9.3  | S10-03   | 见切片                      | 见切片     | `execute-evidence/9.3-{red,green}.txt` |
| 9.4  | S10-04   | 见切片                      | 见切片     | `execute-evidence/9.4-{red,green}.txt` |
| 9.5  | S10-05   | 见切片                      | 见切片     | `execute-evidence/9.5-{red,green}.txt` |

## 2. AC ↔ 测试 / 验收

| AC       | 测试 / 命令                                                             | 通过条件                   |
| -------- | ----------------------------------------------------------------------- | -------------------------- |
| AC-BOOT  | `research/bypass-baseline-matrix.md` + `execute-evidence/9.0-green.txt` | 六类入口矩阵齐全           |
| AC-01    | Sync fail-closed + service 金路径（ADR-025）                            | `uv run pytest` 相关用例绿 |
| AC-02    | `qmd data` 与 `datasource_service_contract.yaml` SSOT                   | 契约升格 + CLI 对齐        |
| AC-03    | Rehearsal vs 产品路径文档硬边界                                         | 文档 + 守卫测试            |
| AC-04    | 旁路负向守卫扩面                                                        | 扩面 pytest 绿             |
| AC-05    | staged/live 双轨收敛 `fetch_ports`                                      | E4 收敛 + 全量 pytest      |
| AC-CLOSE | `validate-plan-freeze` + STAGED-PILOT-SSOT=CLOSED                       | 解锁 R3H-07                |

切片 AC 唯一 SSOT：`research/to-issues-slices.md`

## 3. 必须读原文（manifest · 自动生成 jsonl）

| path                                                                                                                                 | manifest  | audience | extract          | for    |
| ------------------------------------------------------------------------------------------------------------------------------------ | --------- | -------- | ---------------- | ------ |
| `docs/decisions/ADR-025-r3h10-sync-fail-closed-datasource-service.md`                                                                | must-read | execute  | fail-closed 决策 | S10-01 |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_10_DATASOURCE_SERVICE_SSOT.md` | must-read | execute  | 活卡 §1 业务目标 | BOOT   |

> v4.1：slot2 = `research/00-EXECUTION-ENTRY.md`；包内 `research/*` 由 ENTRY §5.2 路由。

## 4. 已并入冻结任务卡

> v4.1：可执行规格在 **Execution Bundle**；本节仅登记 frozen 薄摘要指针。

| 来源 | 并入 | 摘要                        |
| ---- | ---- | --------------------------- |
| 活卡 | 指针 | R3H-10 C2/E4 SSOT · Wave 1a |

## 5. Audit 追溯集

| 类别   | 文件                                       |
| ------ | ------------------------------------------ |
| frozen | `frozen/R3H_10_DATASOURCE_SERVICE_SSOT.md` |
| entry  | `research/00-EXECUTION-ENTRY.md`           |
| slices | `research/to-issues-slices.md`             |
