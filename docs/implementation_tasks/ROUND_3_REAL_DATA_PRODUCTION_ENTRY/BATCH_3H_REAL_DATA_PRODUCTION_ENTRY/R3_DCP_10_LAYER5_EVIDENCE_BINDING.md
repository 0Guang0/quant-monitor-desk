# R3-DCP-10 — Layer5 证据链绑真源（source_fetch_id / hash）

> **规划 ID：** R3-DCP-10  
> **Wave：** 4f · **并行轨 0910-B**  
> **Trellis：** `.trellis/tasks/07-02-wave4-r3-dcp-10-evidence/` · Plan v4.1 · debt-lite  
> **Module：** G5 Layer5 evidence · A3 storage/evidence  
> **评级：** G5 `R2→R3` · A3 巩固  
> **前置：** R3-DCP-05 ✅ · R3H-08 live fetch 证据 ✅  
> **分支：** `feature/wave4-r3-dcp-10-evidence`  
> **Worktree：** `../quant-monitor-desk-wt-dcp10`  
> **状态：** 🟡 Audit/Repair 阶段 · `task.json` status=`in_progress`

---

## 1. Goal（人话）

Layer5 证据链已有 foundation validator 与 lineage 契约，但 **真网→clean** 路径上 `source_fetch_id` / `content_hash` / `schema_hash` 绑定仍多为 staged。本票选 **一条** P0  factual evidence 竖切，从 **Tier A 真 fetch 证据**（DCP-05 clean + raw store）贯通到 Layer5 lineage，pytest 可断言。

---

## 2. 价值

- Wave 4 主线：G5 绑真源
- 承接 `ACC-LAYER-E2E-LIVE-001` **G5 子集**
- 为 Wave 5 `R3H-05-GATE` 证据审计提供真源绑定样本

---

## 3. 约束

| 约束 | 要求 |
| ---- | ---- |
| 金路径 | raw store → clean → Layer5 foundation/lineage；禁止 bypass WriteManager |
| 绑定 | `source_fetch_id` + `content_hash` + `schema_hash` 三者契约对齐 |
| 真网 | 默认 replay；live env-gate + 隔离库 |
| Schema | 无新 migration 除非 ADR |
| 范围 | **一条** P0 instrument/domain 竖切 |
| 参考项目 | L1/L2/L3 **仅** `参考项目/**` |
| Registry | 主会话排队 merge |

---

## 4. 架构触点

```text
Tier A fetch (R3H-08) → raw metadata / fetch_log
        ↓
clean write (DCP-05)
        ↓
Layer5 foundation.py / lineage.py / evidence_chain.py
        ↓
replay e2e：provenance 含 fetch_id + hashes
```

**设计权威：** `docs/modules/layer5_security_evidence.md` · `backend/app/layer5_evidence/`

---

## 5. Acceptance criteria

- [x] 一条 P0 evidence 路径：真 fetch 证据 → Layer5 lineage 可断言 `source_fetch_id` + hashes
- [x] `tests/test_layer5_*_clean_e2e.py`（或等价）GREEN
- [x] `ACC-LAYER-E2E-LIVE-001` G5 子集关账
- [x] `research/reference-adoption-dcp10.md` 含参考项目 L1/L2/L3
- [x] Plan v4.1 包齐；`validate-plan-freeze` exit 0
- [x] `uv run pytest -q` exit 0

---

## 6. 非目标

- Layer5 全 instrument 矩阵
- web_search 真 API（post-Round4）
- prediction market 写 clean factual
- L3/L4 全链（DCP-07/08）

---

## 7. Trellis 入口

`.trellis/tasks/07-02-wave4-r3-dcp-10-evidence/research/00-EXECUTION-ENTRY.md`（Plan 产出）
