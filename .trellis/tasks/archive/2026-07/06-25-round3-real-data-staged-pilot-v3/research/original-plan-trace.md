# Original Plan Trace — B01-C04 staged pilot v3

> 映射 `docs/implementation_tasks/` 任务卡 → MASTER §2 AC

| 原任务卡                                         | MASTER AC              | §8 切片         |
| ------------------------------------------------ | ---------------------- | --------------- |
| `R3E_real_data_staged_pilot_v3.md` §9 SP3-01..06 | AC-SP3-01..06          | R3E-SP3-01..06  |
| `R3E_real_data_staged_pilot_v3.md` §7 资源 cap   | AC-SP3-01 caps         | R3E-SP3-01      |
| `R3E_real_data_staged_pilot_v3.md` §8 禁止项     | §1.5 停止条件 / §3.3   | 全任务          |
| `R3D_model_input_whitelist.md` 输出路径          | AC-SP3-01 WL trace     | R3E-SP3-01      |
| `R3Y_real_data_staged_pilot_v2.md` v2 模式       | §1.2 前置；不得绕过 WL | 对照 v2 archive |
| `R3Y_staged_pilot_v2_execution_addendum.md`      | §5 TDD / §11 Execute   | 全 §8           |
| `018B_production_live_pilot_gate.md`             | §0 staged-only         | closeout        |
| `BATCH_01_TASK_CARD_MANIFEST.md` §4 C04          | §3 边界表              | 全任务          |
| `BATCH_01_HARDENING_RULES.md` §3–§7              | §0 hardening 摘要      | live/mock       |

## GLOBAL 归并

| GLOBAL                 | MASTER 锚点                       |
| ---------------------- | --------------------------------- |
| GLOBAL_EXECUTION_RULES | §3.3 forbidden；WriteManager only |
| GLOBAL_TESTING_POLICY  | §5 RED/GREEN 语义断言             |
| GLOBAL_RESOURCE_LIMITS | §0 caps                           |
| GLOBAL_TASK_TEMPLATE   | §0 元信息；Red Flags §7           |
