# Grill-me session — read-only data health v1

## Q1: 为什么不做完整 Batch6 data health？

**A:** 任务卡 §5.2 明确 out；Wave C 只需 staged evidence gate 输入，非全 DuckDB domain scan。

## Q2: 能否写 source_health_snapshot？

**A:** **禁止** — 任务卡 §5.2、PROMPT_20 §6、playbook §8.1 边界行一致。

## Q3: 坏 fixture 如何证明 meaningful FAIL？

**A:** 每规则切片 §8.3–8.6 至少一条合成坏数据 → `overall_status=FAIL` 且 `checks[].message` 非空。

## Q4: sandbox clean-write rehearsal gate 如何判断？

**A:** 报告字段 `sandbox_clean_write_gate_ready: bool` + `gate_rationale` 文本；基于 lineage + validation + 无 prod mutation 证据，**不**声称 production-live。

## Q5: 与 db-inspect 边界？

**A:** `db-inspect` = presence/metadata；`data health` = domain rules on evidence rows — 不合并进 `db_inspector.py`（设计 doc §3）。

## 开放项（已关闭）

- 无用户阻塞项；`R3-B2.75-REQ2-EM` 保持 DEFERRED 登记即可。
