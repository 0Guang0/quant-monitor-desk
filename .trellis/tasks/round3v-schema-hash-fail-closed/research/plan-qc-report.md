# Plan QC Report — B3V-DATA schema_hash fail-closed

> **Agent:** Plan 质检（B3V-DATA）· **model:** composer-2.5  
> **Worktree:** `../quant-monitor-desk-wt-b3v-data`  
> **输入:** `MASTER.plan.md` · `implement.jsonl`（34 行）· `research/plan-qc-3.10.md`  
> **对照:** Playbook §3.3 · §3.9 · §3.10 · `B02_02_schema_hash_fail_closed.md` · `validate-plan-freeze`

---

## 1. 执行摘要

| 项 | 结果 |
|----|------|
| 初检发现项 | **3**（均为索引/摘要完整性；无计划逻辑缺陷） |
| 阻塞级发现 | **0** |
| 复检遗留（阻塞 Execute） | **0** |
| `validate-plan-freeze` | **exit 0**（本 session 复检） |
| `implement.jsonl` 行数 | **34**（首行 MASTER ✓） |
| **裁决** | **`PASS_FOR_EXECUTE`** |

**派发：** 可派发 Execute；模型 **`composer-2.5`**；禁 `composer-2.5-fast`。

---

## 2. §3.10 权威索引核对（Playbook §3.3 B3V-DATA）

| 路径 | MASTER | implement.jsonl | 摘要一句 | 遗漏风险 |
|------|--------|-----------------|----------|----------|
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 | §0 Source Context | L8 | 共用底座与文件锁 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.3 | §0 Source Context | L8 | B3V-DATA 必读 | 无 |
| `B02_02_schema_hash_fail_closed.md` | §1.6 + trace | L7 | 五切片 AC 权威 | 无 |
| `specs/contracts/data_adapter_contract.md` | §0 §8 DATA-01 | L19 | 结构化 schema_hash | 无 |
| `backend/app/datasources/adapters/skeleton_base.py` | §0 §9.2 | L24 | CSV/Parquet infer | 无 |
| `backend/app/db/validation_gate.py` | §0 §9.3 | L26 | fail-closed gate | 无 |
| `backend/app/datasources/adapters/registry.py` | — | — | adapter 注册邻接 | **F1**（见 §6） |
| `specs/contracts/data_quality_rules.yaml` | §0 §2.4 | L21 | SCHEMA_DRIFT | 无 |
| `specs/contracts/write_contract.yaml` | §2.4 §9.3 | L20 | schema_hash_changed | 无 |
| `specs/contracts/resource_limits.yaml` | §0 §1.4 | L22 | 有界读取 | 无 |
| `tests/test_db_validation_gate.py` | §5.3 | L28 | 缺 hash 负向 | 无 |
| `tests/test_data_adapter_contract.py` | §5.1 | L30 | 契约回归 | 无 |
| `tests/test_data_quality_validator.py` | §6 Tier A+ | L31 | SCHEMA_DRIFT 邻接 | 无 |
| `tests/test_adapter_skeletons.py` | §5.1 §5.3 | L29 | CSV/Parquet/corrupt | 无（B02_02 §6 延伸） |
| `docs/quality/..._v3_INDEX.md` | §0 VR 路由 | L14 | VR-DATA-001 | 无 |
| `docs/modules/data_validation_and_conflict.md` | §0 | L23 | gate 数据流语义 | 无 |
| `BATCH_3V_HARDENING_RULES.md` | §1.4 §1.5 | L10 | 禁 production write | 无 |
| Registry 三件套 | §0 只读标注 | L15 仅 coverage | B02-DATA-05 主会话 | 无（刻意 deferred） |

**§3.3 可执行路径：** 除 `registry.py` 邻接只读外，全部已入 MASTER + implement。

---

## 3. §3.9 追溯规则核对

| 规则 | 检查 | 状态 |
|------|------|------|
| **索引行** | §3.3 主路径均在 MASTER/implement；`registry.py` 缺行 | **F1 非阻塞** |
| **VR 追溯** | `VR-DATA-001` → `B02_02` → AC-DATA-01..05 → §6/§9 验证链 | PASS |
| **负向边界** | MASTER §0 Owns/Must not + §1.4 §1.5 停止条件 | **F2**（缺 playbook §8.2「未改什么」逐字抄录） |
| **切片垂直** | DATA-01..04 各对应 B02-DATA-01..04；无水平跨 VR | PASS |
| **证据路径** | §9 RED/GREEN → `execute-evidence/{step}-red.txt` | PASS |
| **复检** | 本表遗漏风险列：1 项非阻塞 + 2 项摘要缺口 | PASS（无阻塞遗留） |

### VR-DATA-001 三联

| Source ID | AC | Verification |
|-----------|-----|--------------|
| `VR-DATA-001` / `B02_02` | AC-DATA-01..05（05=漂移回归） | §6 Tier A/A+/C + §9 RED/GREEN |
| Registry 闭合 | B02-DATA-05 | **deferred** 主会话；Execute/Audit 不勾选 |

---

## 4. fail-closed 根因核对

Plan 与 `research/plan-boot.md` §当前代码缺口 一致，且与基线代码吻合：

| # | 根因 | 基线证据 | Plan 修复锚点 |
|---|------|----------|---------------|
| 1 | CSV/Parquet 无 `schema_hash` 推导 | `skeleton_base._infer_schema_hash` 对非 JSON 返回 `None` | DATA-02 §9.2 |
| 2 | Gate 在 hash 缺失时 **fail-open** | `_schema_hash_blocks_write`：`current_row[0] is None` 或 `baseline_row[0] is None` → `return False` | DATA-03 §9.3 |
| 3 | 缺负向测试 | JSON infer 有覆盖；CSV/Parquet 缺 hash、corrupt 无 gate 用例 | §5.3 + DATA-04 |

**业务陈述（§1.2）：** 消除「无 schema_hash 绕过 schema drift 检查」— 与审计项 `VR-DATA-001` 一致。**PASS**

---

## 5. DATA-01..04 垂直切片

| 序 | MASTER §8 | 任务卡 | 依赖 | AC | 独立 RED | 状态 |
|----|-----------|--------|------|-----|----------|------|
| 1 | DATA-01 | B02-DATA-01 | — | AC-DATA-01 | §9.1 契约/对照测 | PASS |
| 2 | DATA-02 | B02-DATA-02 | DATA-01 | AC-DATA-02,04（infer） | §9.2 infer tests | PASS |
| 3 | DATA-03 | B02-DATA-03 | DATA-01 | AC-DATA-03,05 | §9.3 missing hash + drift 回归 | PASS |
| 4 | DATA-04 | B02-DATA-04 | DATA-02 | AC-DATA-04（corrupt 负向） | §9.4 corrupt tests | PASS |

- `vertical-slices.md` 与 MASTER §8/§9 **一一对应**。
- DATA-03 同时覆盖 AC-DATA-05（漂移回归）属同一 gate 符号、同一 VR 子 AC，**不视为水平合并**。
- DATA-02 与 DATA-04 对 AC-DATA-04 分工：adapter 行为 vs 负向测试 GREEN，符合 TDD 阶梯。

### B02-DATA-05 / registry 排除

| 检查点 | 证据 | 状态 |
|--------|------|------|
| `original-plan-trace.md` | B02-DATA-05 → **否** Execute | PASS |
| MASTER §1.4 §1.6 §6.1 §10 | registry 闭合不在本任务 | PASS |
| `plan.freeze.md` §4 | B02-DATA-05 不在 Execute 范围 | PASS |
| AUDIT.plan A7 | 零 registry diff | PASS |
| Execute DoD §10 | 不 finish-work · 不 registry 闭合 | PASS |

---

## 6. 专项检查

### 6.1 Forbidden 边界（§2.5 / §2.6 / B02_02 §4）

| 约束 | MASTER 锚点 | 状态 |
|------|-------------|------|
| 禁止全文件扫描 | §0 Must not · §2.5 DuckDB LIMIT 0 | PASS |
| 禁止 production clean write | §0 · §1.5 #2 HARD_STOP | PASS |
| 禁止 RawStore / sync / registry / layer5 | §0 · §1.5 #1 | PASS |
| 禁止 weaken gate（B3V-AUD-05） | §1.5 #4 #6 · §5 负向冻结 | PASS |
| 禁止 db-inspect / WriteManager 模式表改动 | §0 隐含；建议补 §8.2 逐字「未改什么」 | **F2 非阻塞** |
| B02-DATA-05 registry 不写 | 多处 deferred | PASS |

### 6.2 测试与 TDD 纪律

| 检查项 | 结论 |
|--------|------|
| §5.3 具名 `test_*` + RED 命令 | PASS |
| 五字段 docstring 要求 | §0.3b · §5.0 |
| B3V-AUD-05 负向不得削弱 | §5.0 #2 · §1.5 #6 |
| `composer-2.5` only | MASTER §0 |

### 6.3 implement.jsonl 槽位

| 槽位 | 路径 | 状态 |
|------|------|------|
| 1 | `MASTER.plan.md` | PASS |
| 2 | `context_pack.json` | PASS |
| 3+ | trellis-execute · ponytail · ledger · vertical-slices · 契约/接线/测试 | PASS（34 行） |

---

## 7. 发现项清单

| # | 发现 | 严重度 | 阻塞 Execute？ | 建议 |
|---|------|--------|----------------|------|
| F1 | Playbook §3.3 要求 `adapters/registry.py`；`plan-qc-3.10.md` 称已入 implement，**实际未入** MASTER/implement | 低 | 否（只读邻接） | Execute 前可选补 L35 implement + MASTER §0 一行 |
| F2 | Playbook §8.2「未改什么」未逐字写入 MASTER（§0 边界已覆盖实质） | 低 | 否 | 可选在 MASTER §1.4 增「未改什么」子表 |
| F3 | §3.1 部分协调文档（`BATCH_3V_SELF_CHECK.md`、`GLOBAL_TASK_TEMPLATE.md`、`runtime_versions.md`、`ROUND3_HANDOFF.md` 等）未单独入 implement，靠聚合/context_pack | 低 | 否 | 主会话协调包已 PASS_FOR_DISPATCH |

**无计划逻辑、切片、根因或 forbidden 遗漏导致的阻塞项。**

---

## 8. 复检结论

- §3.3 **可执行路径** 已索引（邻接 `registry.py` 除外，非阻塞）
- §3.9 VR 追溯、垂直切片、证据路径：**PASS**
- fail-closed 根因与基线代码：**PASS**
- DATA-01..04 垂直、B02-DATA-05 deferred：**PASS**
- forbidden 边界实质覆盖：**PASS**
- `validate-plan-freeze`：**exit 0**
- `plan-qc-3.10.md` 遗漏风险列：F1 为 false positive，已在本报告纠正

---

## 9. 裁决

### **`PASS_FOR_EXECUTE`**

Execute 可启动；须遵守：

1. Phase 0 **逐行 Read `implement.jsonl`**（34 行）
2. 模型 **`composer-2.5`**；禁 fast
3. **不** 闭合 B02-DATA-05 / registry 三件套
4. GitNexus `impact()` 于 `_infer_schema_hash`、`_schema_hash_blocks_write` 编辑前
5. F1–F3 为可选索引卫生，**不阻碍** 本 session Execute 派发
