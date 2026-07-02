# Audit A5 — AC 完成度 / ACC G5 子集关账 / 独立复验

| 字段     | 值                                                          |
| -------- | ----------------------------------------------------------- |
| 维度     | A5（audit-completion）                                      |
| 任务     | `07-02-wave4-r3-dcp-10-evidence`（R3-DCP-10）               |
| 协议     | `plan_protocol_version: 4.1`                                |
| 分支     | `feature/wave4-r3-dcp-10-evidence`                          |
| 审计日期 | 2026-07-02                                                  |
| 权威     | 代码 + 独立 pytest（不信文档 `[x]` / `s03-green.txt` 自述） |

---

## 维度证据

### AUDIT.plan §2 / frozen §9 对照

| AUDIT 要点 | 验证结论 |
| ---------- | -------- |
| A5：ACC G5 子集 | `ACC-LAYER-E2E-LIVE-001` G5 子集关账证据完整（见 AC #3） |
| A5：全链阶段外置 | L3–L4 全链仍 open，已绑 `R3-DCP-07/08` + `R3H-05-GATE`（见 AC #4） |
| §3 台账：G5 子集关（部分） | 与 `待修复清单.md` §4 / `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 一致 |

### 独立复验（必做 · INDEX §2.1 最弱 2 行）

优先选回归基线 + 全量套件（本票无 Tier 标注；DCP-10 定向测作补充）。

| 原 §2.1 行 | 独立复跑命令 | exit | 与代码行为一致 |
| ---------- | ------------ | ---: | -------------- |
| L1 回归基线 | `uv run pytest tests/test_layer5_evidence_foundation.py tests/test_mootdx_incremental_e2e.py -q` | **0** | 11 passed；foundation/lineage 契约未回归 |
| L2 全量 | `uv run pytest -q` | **0** | ~6 min 全绿（含 4 项 DCP-10 新测） |
| （补充）DCP-10 定向 | `uv run pytest tests/test_layer5_provenance_bridge.py tests/test_layer5_mootdx_bar_clean_e2e.py -q` | **0** | 4 passed；S01+S02 AC 直接证据 |
| L3 loop 维护 | `uv run python scripts/loop_maintain.py` | **1** | `active_master_tasks` 报 `.audit-sandbox/.../MASTER.plan.md` 残留；**非 DCP-10 diff 引入**，见 §计划外 |

**与 Execute 声称对照：** `execute-evidence/s03-green.txt` 声称 `uv run pytest -q → exit 0`；本审计独立复验 **一致**。

### GitNexus（必用）

| 操作 | 目标 | 结果 |
| ---- | ---- | ---- |
| `query` | layer5 provenance / Layer5LineageBuilder | 命中 `Layer5LineageBuilder` · `EvidenceFoundationValidator` · `test_layer5_evidence_foundation.py` |
| `context` | `Layer5LineageBuilder` | incoming: `test_layer5_evidence_foundation.py` · `layer5_evidence/__init__.py` |
| `impact` upstream | `Layer5LineageBuilder` | **LOW** · d=1 仅 `__init__.py` re-export |
| `impact` upstream | `bundle_layer5_provenance` | 索引未收录新签名（Plan `gitnexus-summary.md` 已记）；手工 trace：caller 经 domain wrapper → **additive** `source_dataset_ids`，全量 pytest 绿 |
| `detect_changes` compare master | — | 0 changed symbols（未提交变更不在索引；worktree 手工 diff 见下） |

**Execute 偏差：** 无 silent 扩 scope；`git diff master` 触及文件与 ADR-031 §Consequences 一致。

### git diff 范围核对（vs `master`）

| 文件 | 计划内？ | 说明 |
| ---- | -------- | ---- |
| `backend/app/datasources/normalizers/evidence_bundle.py` | ✅ S01 | 扩展 `bundle_layer5_provenance`：`clean_table` 参数 + `source_dataset_ids`（schema/domain/clean） |
| `backend/app/layer5_evidence/provenance.py`（新） | ✅ S01 | `build_source_provenance_from_bundle` fail-closed |
| `tests/test_layer5_provenance_bridge.py`（新） | ✅ S01 | 3 测 · ADR-031 字段映射 |
| `tests/test_layer5_mootdx_bar_clean_e2e.py`（新） | ✅ S02 | 1 测 · 同 run bundle 绑真源 |
| `docs/decisions/ADR-031-*.md`（新） | ✅ Plan | P0 锚点 + mapping SSOT |
| `docs/quality/待修复清单.md` | ✅ S03 | G5 子集已通登记 |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` | ✅ S03 | DCP-10 G5 ✅ · L3–L4 open |
| `tests/test_catalog.yaml` | ✅ loop | 新测模块 catalog 行（loop 工程约定） |
| `docs/generated/docs_specs_index.generated.md` | ✅ loop | ADR-031 索引刷新 |

**未触及（符合 ENTRY §1 不在范围）：** orchestrator 核心 · evidence_chain DB migration · L3/L4 snapshot writer · live fetch 默认路径。

### AC 评分表（1–5 rubric）

| #     | 范围 | 分 | 追溯链（任务 → 切片 AC → 代码/测试） | 缺口 |
| ----- | ---- | --: | -------------------------------------- | ---- |
| **1** | **S01-PROVENANCE-MAP** | **5** | `to-issues-slices.md` S01 → `bundle_layer5_provenance`（`evidence_bundle.py` L99–125）+ `build_source_provenance_from_bundle`（`provenance.py`）→ `test_layer5_provenance_bridge.py`（3 测）：`source_fetch_id` / `content_hash` / `schema:{hash}@{ver}` / `clean:security_bar_1d@mootdx` / `domain:cn_equity_daily_bar`；缺 fetch_id → `ValueError` | — |
| **2** | **S02-MOOTDX-E2E** | **5** | S02 AC → `test_mootdxBarClean_layer5Provenance_matchesSameRunBundle`：`run_incremental`（mootdx · `sh.600519` · `security_bar_1d`）→ `_load_raw_bundle_from_incremental_run` → `build_source_provenance_from_bundle` → `EvidenceFoundationValidator` + `Layer5LineageBuilder`；断言 `≠ fetch-staged-001`；envelope `source_dataset_ids` 与 provenance 一致 | — |
| **3** | **S03 / `ACC-LAYER-E2E-LIVE-001` G5 子集** | **5** | S03 AC「G5 子集关账 + pytest 全绿」→ `待修复清单.md` §4·§8：`G5 子集已通` + 关闭条件 `test_layer5_mootdx_bar_clean_e2e` 绿；`ROADMAP` §3.5.2 DCP-10 行 `✅ G5 子集 CLOSED`；独立 `uv run pytest -q` exit 0 | — |
| **4** | **L3–L5 全链阶段外置** | **5** | `to-issues-slices.md` 台账表 · ADR-031 §5 · `AUDIT.plan` §3：`L3–L4 全链仍 open` → `R3-DCP-07/08` + `R3H-05-GATE`；`待修复清单` / `ROADMAP` 双登记，无口头 defer | L3–L5 **刻意 open**（符合计划），非缺口 |
| **5** | **P0 竖切边界（replay · 单 instrument）** | **5** | ADR-031 P0 表 · ENTRY §1：`cn_equity_daily_bar` / `mootdx` / `sh.600519` / `security_bar_1d`；e2e 用 replay fixture + tmp_path DB；无 live 默认路径 · 无全 instrument 矩阵 | — |

### S00–S03 切片 ↔ 证据对照

| 切片 | 实现锚点 | 测试 / 台账证据 |
| ---- | -------- | --------------- |
| S00-BOOT | Execute boot 声明 | `frozen` §9.0 `[x]`（文档；本维以代码为准） |
| S01 | `evidence_bundle.py` · `provenance.py` | `test_layer5_provenance_bridge.py`（3） |
| S02 | incremental orch + raw bundle loader | `test_layer5_mootdx_bar_clean_e2e.py`（1） |
| S03 | registry 双登记 | `待修复清单.md` §4·§8 · `ROADMAP` §3.5.2 · 全量 pytest 绿 |

### audit-prod-path

`AUDIT.plan` §1 **未冻结** prod-path；本维 **跳过** `AUDIT_PROD_ROOT` 副本流程。

---

## §维度裁决

**PASS**

**理由：** G5 子集 AC（#1–#3）追溯链完整且独立 pytest 全绿；L3–L5 全链阶段外置双登记合规（#4）；diff 无计划外扩 scope；§计划内/§计划外 findings 均为占位。

---

## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| — | — | 无 | — | — | — | — |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| — | — | 无 | — | — | — | — |

已对抗搜索：`backend/app/layer5_evidence/provenance.py` · `evidence_bundle.bundle_layer5_provenance` · `tests/test_layer5_{provenance_bridge,mootdx_bar_clean_e2e}.py` · `tests/test_layer5_evidence_foundation.py` · `tests/test_mootdx_incremental_e2e.py` · `docs/decisions/ADR-031-dcp10-layer5-evidence-provenance-binding.md` · `待修复清单.md` §4·§8 · `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 · `to-issues-slices.md` S03 台账表 · GitNexus `query`/`impact`/`context` on `Layer5LineageBuilder` · `scripts/loop_maintain.py`（sandbox MASTER 残留仅记维度证据，非 G5 AC 缺口）。

**观察（非 finding）：** `loop_maintain.py` exit 1 因任务目录 `.audit-sandbox/.../MASTER.plan.md` 触发 `active_master_tasks`；建议 A8/loop 维护维清理 sandbox，不阻塞本票 G5 子集关账语义。

---

## pytest exit codes（摘要）

```
uv run pytest tests/test_layer5_provenance_bridge.py \
            tests/test_layer5_mootdx_bar_clean_e2e.py -q  → 0 (4 passed)
uv run pytest tests/test_layer5_evidence_foundation.py \
            tests/test_mootdx_incremental_e2e.py -q       → 0 (11 passed)
uv run pytest -q                                        → 0
uv run python scripts/loop_maintain.py                  → 1 (audit-sandbox MASTER 残留)
```
