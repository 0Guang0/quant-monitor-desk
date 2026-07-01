# AUDIT.plan — R3-DCP-05

> **追溯：** `EXECUTION_INDEX.md` §5 · `research/00-EXECUTION-ENTRY.md`

## §1 覆写

- **任务：** Wave 4 R3-DCP-05 Tier A incremental + 11/11 clean
- **PASS 门槛：** 活卡 §5 全勾 · 11 e2e clean · pytest 全绿 · 无 staging-only Tier A 路径

## §2 验证矩阵（摘要）

| 维  | 要点                                          |
| --- | --------------------------------------------- |
| A1  | 活卡/ENTRY/ADR-028 一致                       |
| A2  | migration 015 + clean_write_targets 矩阵      |
| A3  | 无 `参考项目` runtime import                  |
| A4  | 11 源 e2e 写 clean（非 staging）              |
| A5  | baostock live gate；fred live primary 仍 open |
| A6  | registry 三件套（主会话）                     |
| A7  | 隔离库 / 主库零污染                           |
| A8  | `uv run pytest -q`                            |

## §3 台账

- 关：`ACC-BAOSTOCK-NO-LIVE`
- 文档：`ACC-EASTMONEY-TAXONOMY-001`
- 不关：`B2.5-O-05`
