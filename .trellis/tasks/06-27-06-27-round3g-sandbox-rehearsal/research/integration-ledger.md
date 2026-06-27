# Integration ledger — R3G-01

| 路径                                 | 类型             | 处理             | for AC        |
| ------------------------------------ | ---------------- | ---------------- | ------------- |
| `sandbox_clean_write_contract.yaml`  | contract         | §3 must-read     | AC-02, AC-05  |
| `reference_adoption_guardrails.yaml` | contract         | §3 must-read     | AC-07–09      |
| `staged_pilot.py`                    | code pattern     | §3 must-read     | AC-03         |
| `fred_sandbox_pilot.py`              | code pattern     | §3 must-read     | AC-06         |
| `data_health_profiles/**`            | code             | §3 must-read     | AC-04         |
| `round3-fred-.../authorization.yaml` | evidence pattern | §3 must-read     | AC-06         |
| `BATCH_3G_COORDINATOR_PLAYBOOK.md`   | playbook         | §3 must-read     | file lock     |
| `production_live_pilot_policy.md`    | policy           | §3 must-read     | 防误宣称 live |
| `staged_acceptance_policy.md`        | policy           | §3 must-read     | 分层验收      |
| 活卡 §4 EasyXT/JQ2PTrade/OpenBB      | reference        | 已内联 frozen §5 | AC-04,07–09   |

## 六类 closure

| 类       | 状态                                    |
| -------- | --------------------------------------- |
| contract | sandbox_clean_write + guardrails 已索引 |
| code     | write/validation/datasource/ops 已索引  |
| test     | round3g + guardrails 在 §2              |
| policy   | live + staged 已索引                    |
| evidence | FRED auth 路径在 frozen §6              |
| playbook | 3G coordinator 已索引                   |
