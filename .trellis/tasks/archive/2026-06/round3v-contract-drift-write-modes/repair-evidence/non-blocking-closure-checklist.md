# B3V-OPS 非阻塞项逐项闭合清单

> **策略：** `BATCH_3V_ZERO_OPEN_CLOSURE_POLICY.md` — NON-BLOCKING 不得 plain wont-fix  
> **Repair commit：** post-adversarial hygiene pass  
> **日期：** 2026-06-28

## A1–A8 + 对抗性 逐项核对

| ID                         | 级别         | 发现                               | 原处置         | 闭合动作                                                           | 状态          |
| -------------------------- | ------------ | ---------------------------------- | -------------- | ------------------------------------------------------------------ | ------------- |
| DOUBT-01                   | NON-BLOCKING | 空 key_tables fail-open            | repair 559247e | `_key_tables_from_contract` + 测                                   | ✅            |
| DOUBT-02                   | NON-BLOCKING | deferred 插入序                    | repair 559247e | `items.sort` by item_id                                            | ✅            |
| DOUBT-03 / AA-B3V-ADV-02   | INFO         | enum ∪ 测缺失                      | wont-fix       | `test_writeContract_writeModeEnum_matchesImplementedUnionReserved` | ✅            |
| A2-02..04                  | 建议         | DRY / COUNT 外循环                 | repair         | `tests/db_helpers.py`                                              | ✅            |
| AA-B3V-ADV-01 / PO-01      | INFO         | `FUTURE_PHASE_KEY_TABLES` 硬编码   | wont-fix       | YAML `future_phase_key_tables` + loader + drift 测                 | ✅            |
| AA-B3V-ADV-03 / F2 / PO-02 | INFO         | Write 双 SSOT                      | accepted       | `WriteManager` import-time YAML loader                             | ✅            |
| A4                         | —            | `REQUIRED_TOP_LEVEL_FIELDS` 硬编码 | scope 外       | 从 `required_output_fields` 加载 + drift 测                        | ✅            |
| A8-B3V-04                  | NON-BLOCKING | fresh clone basetemp               | documented     | `conftest` `_ensure_audit_sandbox_pytest_basetemp`                 | ✅            |
| B02-CLOSE-01               | DEFER        | registry 三件套                    | 主会话         | coordinator §7.3                                                   | ⏳ 设计内     |
| A6 NB-1                    | NON-BLOCKING | inspect 21 表串行 SQL              | 备忘           | 非 B3V 引入；perf 切片另开                                         | 📋 主会话登记 |
| A3-PLAN-04/05              | P3           | 路径泄露 / qmd_ops data            | 可接受         | 文档已有 local-only；非本 slice 改码                               | 📋 无代码债   |

## 门控

- [x] 任务域 drift/parity 子集绿
- [x] 全量 `uv run pytest -q` 绿（repair 后）
- [x] registry 三件套未 agent 直接 CLOSED
