# Plan Boot — R3-DCP-05 Tier A incremental + 11/11 clean

> **轨道：** Wave 4a · Plan v4.1  
> **日期：** 2026-07-02  
> **活卡：** `R3_DCP_05_TIER_A_INCREMENTAL.md`  
> **用户裁决：** 11/11 Tier A 必须 clean upsert（ADR-028）

---

## Phase P0 complete

### 1. 做什么

将 Wave 3「水位增量 + 产品 CLI + clean 写入」推广到 **11 个 Tier A 源**；修 baostock sync 硬编码 mock；为 `sec_edgar` / `deribit` 新增 clean 表（migration 015）；扩 `clean_write_targets` 使 **每源 canonical domain → clean upsert e2e 绿**。

### 2. 价值

- Wave 4 DCP-05 路线图硬交付；DCP-06 五轴真 clean 输入前置
- 关 `ACC-BAOSTOCK-NO-LIVE`；东财 SSOT 文档化

### 3. 约束

| 约束   | 要求                                 |
| ------ | ------------------------------------ |
| 金路径 | DataSourceService + run_incremental  |
| 真网   | QMD_ALLOW_LIVE_FETCH + 隔离库        |
| Schema | migration 015（ADR-028）             |
| 11/11  | 每源 watermark + replay e2e clean 写 |
| 参考   | L1/L2/L3 仅 `参考项目/**`            |

### 4. 架构触点

`data_commands` → watermark → incremental service → orchestrator → clean（5 表族）

### 5. 成功标准

活卡 §5 + INDEX §7 + `uv run pytest -q`

### 6. P0 已读清单

- [x] `docs/implementation_tasks/README.md`
- [x] `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5、§3.5.2
- [x] `R3_DCP_TO_ISSUES_INDEX.md` §6、§7（本票新建）
- [x] `R3_DCP_05_TIER_A_INCREMENTAL.md`
- [x] `R3_DCP_01/02` 归档 DEBT.plan + reference-adoption
- [x] `docs/modules/data_sync_orchestrator.md` §13.4.2
- [x] `specs/contracts/reference_adoption_guardrails.yaml`
- [x] `backend/app/sync/watermark.py`, `ops/fred_incremental_*.py`, `data_commands.py`
- [x] `013_clean_domain_tables.sql`
- [x] `待修复清单.md` §4、§8
- [x] 参考项目实读：OpenBB fetcher, digital-oracle bis, EasyXT auto_data_updater + unified_data_interface

### 7. 与 DCP-01/02 差异

| 项            | Wave 3      | DCP-05               |
| ------------- | ----------- | -------------------- |
| 源数量        | 2           | 11                   |
| migration     | 无          | **015**              |
| clean 表      | 已有 3 族   | +2 表 + domain 扩域  |
| baostock live | mock 硬编码 | 接 product live gate |
