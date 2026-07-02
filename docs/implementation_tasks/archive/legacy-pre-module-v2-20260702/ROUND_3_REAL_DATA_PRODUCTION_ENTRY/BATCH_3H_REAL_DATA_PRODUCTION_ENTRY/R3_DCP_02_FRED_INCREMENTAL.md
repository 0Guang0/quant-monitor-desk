# R3-DCP-02 — fred 宏观序列增量

> **规划 ID：** R3-DCP-02  
> **Wave：** 3b · **并行轨 B**  
> **Trellis：** debt-lite · `wave3-r3-dcp-02-fred`  
> **Module：** D1 · E1  
> **评级：** D1/E1 R3→R4

---

## 1. Goal（人话）

让 FRED 宏观序列走**产品增量路径**：读库里的最新观测日，只拉新增点，写 macro clean 域，CLI 可重复跑。

---

## 2. 价值

- 与 baostock 并列的 Wave 3 试点，验证宏观序列 watermark 语义
- 承接 R3H-08C fred live port；从「能拉」升级到「能增量产品跑」

---

## 3. 约束

| 约束      | 要求                                                               |
| --------- | ------------------------------------------------------------------ |
| 金路径    | 同 DCP-01                                                          |
| 授权      | `FRED_API_KEY` + `QMD_ALLOW_LIVE_FETCH`；`USER_AUTH_REQUIRED` 负例 |
| 数据根    | 隔离库；禁止 canonical 主库 silent write                           |
| watermark | 序列/观测日语义须与 macro clean PK 对齐（非盲目抄 trade_date）     |
| Registry  | 仅 `fred` 相关行                                                   |

---

## 4. 架构触点

```text
qmd data sync … --source fred
  → watermark 读 macro clean（按契约字段）
  → DataSourceService.fetch(fred)
  → IncrementalJobRunner
```

**拥有文件组（轨 B）：**

```text
backend/app/datasources/fetch_ports/fred_port.py
backend/app/ops/fred_*.py（增量相关切片）
backend/app/sync/**（仅 fred 适配切片；共享 watermark 模块若存在则只读或 PR 协调）
tests/test_*fred* / tests/test_*macro*incremental*
```

**禁止：** 改 `baostock_port`、CN equity clean 域（轨 A）。

---

## 5. Acceptance criteria

- [x] fred watermark 单测（空表 / 有观测 / 多 series）
- [x] replay + env-gated live smoke（隔离库）
- [x] 幂等：重复跑不增行
- [x] `research/reference-adoption-dcp02.md` L1/L2/L3
- [x] Audit + Repair 关账
- [x] `uv run pytest -q` exit 0

---

## 6. Done

**✅ CLOSED @ 2026-06-30** — merge `5d8d7b0f` · P7 post-merge `bb3ce99c` · Trellis 归档 `06-30-wave3-r3-dcp-02-fred`（DCP-03 仅需 01/02 其一 PASS，两轨均已闭合）。

---

## 7. 非目标

- 宏观六源全量增量（Wave 4）
- 新 FRED series 目录 UI
- SEC/CFTC 等其它宏观源
