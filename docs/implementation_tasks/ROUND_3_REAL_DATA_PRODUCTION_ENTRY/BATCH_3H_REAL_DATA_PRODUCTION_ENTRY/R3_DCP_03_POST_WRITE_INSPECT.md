# R3-DCP-03 — 增量写后抽检（E2 + F0）

> **规划 ID：** R3-DCP-03  
> **Wave：** 3c · **串行收尾轨**  
> **Trellis：** debt-lite · `wave3-r3-dcp-03-post-write-inspect`  
> **Module：** E2 Ops DB inspect · F0 Data health profile  
> **评级：** E2/F0 R3→R4（写后抽检竖切）

---

## 1. Goal（人话）

DCP-01/02 已能「增量拉 + 写隔离库」。本轨补上链路最后一环：**写完之后**，用只读运维工具验「行数没乱涨、`max(trade_date)` 合理、health profile 能跑」——不靠 sync 自说自话。

---

## 2. 价值

- 闭合 Wave 3 路线图句：`读水位 → 只拉新增 → 写库 → **抽检**`
- 把 `MODULE_COMPLETION_RATING` E2「绑 R3H-08 写后检查」落到 **baostock 增量产品路径**（fred 幂等已由 DCP-02 e2e 覆盖；本轨 inspect 以 baostock 为主）
- 为 Wave 4 全 Tier A 扩展提供可复制的「sync 后 inspect」测试模式

---

## 3. 约束

| 约束           | 要求                                                                                                                          |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| 只读           | `DbInspector` / `run_data_health_profile` **不得** mutate DB                                                                  |
| 数据根         | 测试与 smoke 用 `tmp_path` 或 `QMD_DATA_ROOT` 隔离库；**禁止**写 canonical `data/duckdb/`                                     |
| 金路径复用     | `scripts/qmd_ops.py db-inspect` 薄包装 `db_inspector.py`；禁止第二条 inspect 实现                                             |
| Health profile | v1 仅 **`market_bar_p0`** + `market_bar_1d`（已有）；**不**新建 macro profile（fred 本轨非主路径，仅 row_count inspect 可选） |
| Schema         | R3H-06 已封板；**无新 migration**                                                                                             |
| 并行边界       | **禁止**改 DCP-01/02 已交付的 sync/watermark/port 行为（除非 Repair 根因）                                                    |

---

## 4. 架构触点

```text
[DCP-01/02 增量写库完成]
  → DbInspector.inspect(db, data_root)     # E2：key_tables row_count + evidence
  → run_data_health_profile(               # F0：market_bar_p0（baostock 路径）
        profile_id=market_bar_p0,
        domain=market_bar_1d,
        db_path=…,
        evidence_path=…,
     )
  →（可选）qmd_ops.py db-inspect --format json  # CLI smoke
```

**拥有文件组（轨 C）：**

```text
tests/test_incremental_post_write_inspect.py   # 新建：写后抽检集成测
tests/test_ops_db_inspector.py                 # 仅当需共享 helper（优先不复用改）
backend/app/ops/db_inspector.py                # 默认不改；若 AC 需 max(trade_date) 字段才极小扩展；否则测试内 SQL
backend/app/ops/data_health_profiles/**      # 只读消费；不新 profile
scripts/qmd_ops.py                             # 只读；不新子命令
.trellis/tasks/06-30-wave3-r3-dcp-03-post-write-inspect/**
```

**禁止：** 改 `sync/watermark.py`、`baostock_port`、`fred_port`、`orchestrator` 增量语义。

---

## 5. Acceptance criteria

- [x] 重复增量跑后：`DbInspector` 报告 `security_bar_1d.row_count` **稳定**（幂等写后验）
- [x] 写后 `max(trade_date)` 可断言（测试内 read-only SQL 或 inspect 扩展字段）
- [x] `run_data_health_profile(market_bar_p0)` 在 baostock 增量写库后可跑通（PASS/WARN 均可，不得抛未处理异常）
- [x] `qmd_ops.py db-inspect --format json` 对隔离库 exit 0 且含 `security_bar_1d` key_table
- [x] `research/reference-adoption-dcp03.md`：**参考项目**三等级表 + **仓内复用**表齐（仓内代码不得标 L1/L2/L3）
- [x] Audit A1–A8 + Repair ledger 关账（debt-lite）
- [x] `uv run pytest -q` exit 0

---

## 6. Done

**✅ CLOSED @ 2026-06-30** — merge `eff49343` · Audit/Repair PASS · Trellis 归档 `06-30-wave3-r3-dcp-03-post-write-inspect` · **Wave 3 CLOSED**。

---

## 7. 非目标

- 新 macro / fred health profile（Wave 4+）
- `qmd data health` 新产品子命令（已有 data CLI 边界）
- 24 源写后矩阵
- OHLC 域规则扩展（Batch 6 `data_health_cli`）
