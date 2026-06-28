# B3V-L5R Vertical Slices — WAVE0 §2 SSOT

> **Manifest:** `B3V-C06` · **活卡:** `B03_01_layer5_model_schema_reconcile.md`  
> **SSOT 索引:** `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §2  
> **Plan 冻结:** `DEBT.plan.md` · **日期:** 2026-06-28

## 铁律

- reconcile-first（`BATCH_3V_HARDENING_RULES.md` §6）
- L5 轨与 MODEL 轨 **分轨**；**禁止**单份水平 reconcile report 同时关 `VR-L5-001` + `VR-MODEL-001` 而无 per-VR 证据
- `backend/app/layer5_evidence/**` **默认只读**
- registry 三件套：**agent 仅 proposed delta**；`L5R-CLOSE` 不交 registry commit

## 竖条表（L5R-BOOT..L5R-CLOSE）

| 序 | ID | VR / 轨 | 垂直切片 | 交付物 | 依赖 | 强制 verification |
| -- | -- | ------- | -------- | ------ | ---- | ----------------- |
| 0 | **L5R-BOOT** | — | post Batch 01 基线证据 | commit `376e30e6` + 现有 Layer5 pytest 绿快照 | — | `execute-evidence/l5r-boot-pytest.txt` |
| 1 | **L5-01** | `VR-L5-001` | Layer5 能力状态矩阵 | `research/l5-reconcile-matrix.md` §2（VR-L5-001） | BOOT | 只读对照 `layer5_evidence/**` |
| 2 | **L5-02** | `VR-L5-001` | Layer5 测试指针核对 | 矩阵每行有 test 名或 follow-up ID | L5-01 | `uv run pytest tests/test_layer5_evidence_chain.py tests/test_layer5_evidence_foundation.py -q` |
| 3 | **MODEL-01** | `VR-MODEL-001` | L3/L4/L5 表三列矩阵 | `research/model-table-matrix.md` + `l5-reconcile-matrix.md` §3 | BOOT | 每表 design_ssot / migration / runtime 列 |
| 4 | **MODEL-02** | `VR-MODEL-001` | 文档 + closure pytest 对齐 | `MIGRATION_COVERAGE.md` L3/L4/L5 段；**TDD** `test_migration_coverage.py` | MODEL-01 | `uv run pytest tests/test_migration_coverage.py -q` + `check_docs_specs_indexed.py` exit 0 |
| 5 | **L5R-CLOSE** | 双 VR | **独立**关账切片：per-VR proposed delta | `research/registry_proposed_delta.yaml` | L5-02 **且** MODEL-02 | 双 mandatory pytest 绿；**不** commit registry |

## 任务卡 ID 交叉引用（legacy B03-*）

| WAVE0 ID | 任务卡 slice | 说明 |
| -------- | ------------ | ---- |
| L5R-BOOT | — | Plan 新增 BOOT 竖条 |
| L5-01 | `B03-L5-01` | 同 AC |
| L5-02 | `B03-L5-02` | 同 AC |
| MODEL-01 | `B03-MODEL-01` | 交付物路径 WAVE0 定为 `model-table-matrix.md` |
| MODEL-02 | `B03-MODEL-02` + `B03-MODEL-03` | docs 对齐 + migration_coverage TDD 合并为一步 |
| L5R-CLOSE | `B03-L5-CLOSE` + `B03-MODEL-CLOSE` + `B03-CLOSE-01`（主会话） | agent 侧仅 proposed delta；registry commit 归主会话 |

## 强制 targeted pytest（playbook §8.6 · 关账前必绿）

```bash
uv sync --locked
uv run pytest tests/test_layer5_evidence_chain.py -q
uv run pytest tests/test_migration_coverage.py -q
uv run python scripts/check_docs_specs_indexed.py
```

| 测试文件 | 切片 | VR | 用途 |
| -------- | ---- | -- | ---- |
| `tests/test_layer5_evidence_chain.py` | L5-02 | `VR-L5-001` | 证据链 staged runtime 回归 |
| `tests/test_layer5_evidence_foundation.py` | L5-02 | `VR-L5-001` | foundation / lineage / agent-text |
| `tests/test_migration_coverage.py` | MODEL-02 | `VR-MODEL-001` | designed 表无 migration 断言；L1 axis 011 DONE |

**禁止：** 仅只读 report 关 `VR-*`；无上述 pytest 绿不得进入 `L5R-CLOSE`。

## 研究产物路径（Plan 预定）

| 路径 | 切片 | 状态 |
| ---- | ---- | ---- |
| `research/l5-reconcile-matrix.md` | L5-01 / L5-02 / L5R-CLOSE | Execute 已落盘 |
| `research/model-table-matrix.md` | MODEL-01 | Plan 预定 SSOT；详表见 `model-schema-table-reconcile.md` |
| `research/registry_proposed_delta.yaml` | L5R-CLOSE | agent 提案；主会话批闭合 |
