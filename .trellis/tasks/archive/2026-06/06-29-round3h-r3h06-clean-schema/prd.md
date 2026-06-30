<!-- thin-index: true -->

# R3H-06 Clean Schema (Wave 1)

> **Execute/Audit SSOT：** `frozen/R3H_06_CLEAN_SCHEMA.md` + `EXECUTION_INDEX.md`（冻结后）

- **目标：** 三域 clean DDL（`security_bar_1d` / `cn_announcement_clean` / `axis_observation` 路由）、OHLCV、cninfo 原生形、PK/upsert 幂等。
- **闭合：** SCHEMA-G3G4 · CNINFO-DISCLOSURE-SHAPE · G6-IDEMPOTENCY（§5.0.1）。
- **波次：** Wave 1 单轨；阻塞 Wave 3 R3H-08。
- **活卡：** `docs/.../R3H_06_CLEAN_SCHEMA.md` · **Trellis：** `.trellis/tasks/06-29-round3h-r3h06-clean-schema/`
- **Plan 状态：** 已冻结；Execute 9.0–9.10 完成；Audit 八路 + Repair 全量闭合中。
- **§5.0.1：** SCHEMA-G3G4 · CNINFO-DISCLOSURE-SHAPE · G6-IDEMPOTENCY → **CLOSED** @ R3H-06。
