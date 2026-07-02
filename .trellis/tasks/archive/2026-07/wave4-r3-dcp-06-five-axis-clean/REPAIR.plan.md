# REPAIR.plan — wave4-r3-dcp-06-five-axis-clean

> **源：** `audit.report.md` §4.1（23 findings）· Audit FAIL @ 2026-07-02

## §1 修复行（全量关账，禁止阶段外置除非绑定任务）

| ID            | P   | 修复要点                             | 允许文件                                              |
| ------------- | --- | ------------------------------------ | ----------------------------------------------------- |
| A3-P1-001     | P1  | P0 正源 allowlist；拒 akshare 等     | `clean_observation_reader.py` + tests                 |
| A3-P2-001     | P2  | `source_switched=True` fail-closed   | 同上                                                  |
| A3-P3-001     | P3  | Amihud 路径 forbidden guard          | 同上                                                  |
| A3-P3-002     | P3  | bar staged_fixture pytest            | `test_layer1_clean_reader.py`                         |
| A8-P0-001     | P0  | 全量 pytest 绿（CLI 双测若仍红）     | tests + 最小 CLI 对齐（DEBT 禁止 data_commands 大改） |
| A8-P2-001/002 | P2  | bar empty/forbidden tests            | `test_layer1_clean_reader.py`                         |
| A8-P3-001     | P3  | Amihud empty fail-closed test        | 同上                                                  |
| A8-P3-002     | P3  | 更新 s07-green evidence              | execute-evidence                                      |
| A2-P2-001     | P2  | `seed_cot_lf_net_weekly` 共享        | `layer1_clean_e2e_support.py` + S05/S06               |
| A4-P2-001     | P2  | cap 与 YAML 程序化对账测             | panel or reader tests                                 |
| A4-P2-002     | P2  | bar staged_fixture test              | clean_reader                                          |
| A4-P2-003     | P2  | panel ResourceGuard 接特征链         | panel smoke                                           |
| A4-P3-001/002 | P3  | LIQ/CREDIT boundary_reminder         | axis e2e tests                                        |
| A4-P3-003     | P3  | as_of_end 过滤 test                  | clean_reader                                          |
| A4-P3-004     | P3  | macro_supplementary prefix test      | clean_reader                                          |
| A5-P2-002     | P2  | loop 测试不污染 archive context_pack | `test_loop_engineering_flow.py`                       |
| A5-P2-001     | P2  | 全量 pytest 连续 2 次绿              | 依赖 A8-P0 + A5-P2-002                                |
| A1-P2-01~04   | P2  | Bundle 追溯文档                      | trellis research + INDEX + integration-audit          |
| A1-P3-01      | P3  | GitNexus analyze 或 document         | `gitnexus-audit-summary.md`                           |

## §2 验证

```bash
uv run pytest -q   # 连续 2 次 exit 0
uv run python scripts/loop_maintain.py --fix
```

## §3 禁止

- 改测试 purpose 换绿
- `data_commands.py` 大改（DEBT.plan）；CLI 修优先测/fixture 对齐
